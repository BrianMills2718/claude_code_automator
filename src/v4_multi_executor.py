"""
V4 Multi-Strategy Executor
Executes multiple strategies in parallel when beneficial.
"""

import asyncio
import logging
import time
import psutil
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, field
from pathlib import Path
from contextlib import asynccontextmanager
import resource

from .orchestrator import CCAutomatorOrchestrator

logger = logging.getLogger(__name__)


@dataclass
class ResourceLimits:
    """Resource limits for parallel execution."""
    max_concurrent: int = 2
    memory_limit_gb: float = 4.0
    cpu_percent_limit: float = 80.0
    timeout_seconds: int = 3600  # 1 hour per strategy


@dataclass
class ExecutionMetrics:
    """Metrics collected during execution."""
    start_time: float
    end_time: float = 0.0
    peak_memory_mb: float = 0.0
    avg_cpu_percent: float = 0.0
    api_calls: int = 0
    errors: List[str] = field(default_factory=list)
    
    @property
    def duration(self) -> float:
        return self.end_time - self.start_time if self.end_time > 0 else 0.0


class ResourceMonitor:
    """
    Monitors system resources during parallel execution.
    """
    
    def __init__(self, limits: ResourceLimits):
        self.limits = limits
        self.monitoring = False
        self.metrics = []
        self.process = psutil.Process()
    
    async def start_monitoring(self):
        """Start resource monitoring in background."""
        self.monitoring = True
        asyncio.create_task(self._monitor_loop())
    
    async def stop_monitoring(self):
        """Stop resource monitoring."""
        self.monitoring = False
        await asyncio.sleep(0.1)  # Let monitor loop finish
    
    async def _monitor_loop(self):
        """Background monitoring loop."""
        while self.monitoring:
            try:
                # Check memory
                memory_info = self.process.memory_info()
                memory_gb = memory_info.rss / (1024 * 1024 * 1024)
                
                # Check CPU
                cpu_percent = self.process.cpu_percent(interval=0.1)
                
                self.metrics.append({
                    'timestamp': time.time(),
                    'memory_gb': memory_gb,
                    'cpu_percent': cpu_percent
                })
                
                # Check limits
                if memory_gb > self.limits.memory_limit_gb:
                    logger.warning(f"Memory limit exceeded: {memory_gb:.2f}GB > {self.limits.memory_limit_gb}GB")
                
                if cpu_percent > self.limits.cpu_percent_limit:
                    logger.warning(f"CPU limit exceeded: {cpu_percent:.1f}% > {self.limits.cpu_percent_limit}%")
                
            except Exception as e:
                logger.error(f"Resource monitoring error: {e}")
            
            await asyncio.sleep(5)  # Check every 5 seconds
    
    def get_metrics_summary(self) -> Dict[str, float]:
        """Get summary of collected metrics."""
        if not self.metrics:
            return {'peak_memory_gb': 0.0, 'avg_cpu_percent': 0.0}
        
        memories = [m['memory_gb'] for m in self.metrics]
        cpus = [m['cpu_percent'] for m in self.metrics]
        
        return {
            'peak_memory_gb': max(memories) if memories else 0.0,
            'avg_cpu_percent': sum(cpus) / len(cpus) if cpus else 0.0
        }


class V4MultiStrategyExecutor:
    """
    Executes multiple strategies in parallel with resource management.
    
    Key capabilities:
    - Resource-limited parallel execution
    - Evidence-based result comparison
    - Automatic fallback on resource exhaustion
    - Comprehensive metrics collection
    """
    
    def __init__(self, v3_orchestrator: CCAutomatorOrchestrator):
        self.v3_orchestrator = v3_orchestrator
        self.default_limits = ResourceLimits()
        self.execution_metrics = {}
        
        logger.info("Multi-Strategy Executor initialized")
    
    async def execute_parallel_strategies(
        self,
        strategies: List['Strategy'],
        milestone_num: int,
        milestone: str,
        limits: Optional[ResourceLimits] = None
    ) -> List['ExecutionResult']:
        """
        Execute multiple strategies in parallel with resource management.
        
        Returns list of results from all strategies that completed.
        """
        limits = limits or self.default_limits
        
        logger.info(f"Executing {len(strategies)} strategies in parallel "
                   f"(max concurrent: {limits.max_concurrent})")
        
        # Start resource monitoring
        monitor = ResourceMonitor(limits)
        await monitor.start_monitoring()
        
        try:
            # Create execution tasks with resource limits
            tasks = []
            semaphore = asyncio.Semaphore(limits.max_concurrent)
            
            for i, strategy in enumerate(strategies):
                task = self._execute_strategy_with_limits(
                    strategy,
                    milestone_num,
                    milestone,
                    semaphore,
                    limits,
                    strategy_index=i
                )
                tasks.append(task)
            
            # Execute with timeout
            try:
                results = await asyncio.wait_for(
                    asyncio.gather(*tasks, return_exceptions=True),
                    timeout=limits.timeout_seconds
                )
            except asyncio.TimeoutError:
                logger.error(f"Parallel execution timeout after {limits.timeout_seconds}s")
                results = []
            
            # Stop monitoring
            await monitor.stop_monitoring()
            
            # Collect metrics
            resource_summary = monitor.get_metrics_summary()
            logger.info(f"Resource usage - Peak memory: {resource_summary['peak_memory_gb']:.2f}GB, "
                       f"Avg CPU: {resource_summary['avg_cpu_percent']:.1f}%")
            
            # Filter successful results
            valid_results = []
            for i, result in enumerate(results):
                if isinstance(result, Exception):
                    logger.error(f"Strategy {i} failed: {result}")
                elif result is not None:
                    valid_results.append(result)
            
            return valid_results
            
        except Exception as e:
            logger.error(f"Parallel execution error: {e}")
            await monitor.stop_monitoring()
            return []
    
    async def _execute_strategy_with_limits(
        self,
        strategy: 'Strategy',
        milestone_num: int,
        milestone: str,
        semaphore: asyncio.Semaphore,
        limits: ResourceLimits,
        strategy_index: int
    ) -> Optional['ExecutionResult']:
        """
        Execute a single strategy with resource limits.
        """
        async with semaphore:  # Limit concurrent executions
            logger.info(f"Starting strategy {strategy_index}: {strategy.name}")
            
            metrics = ExecutionMetrics(start_time=time.time())
            
            try:
                # Create isolated execution environment
                async with self._create_isolated_environment(strategy_index) as env:
                    # Execute strategy
                    result = await strategy.execute(
                        milestone_num,
                        milestone,
                        failure_callback=self._create_failure_callback(strategy_index)
                    )
                    
                    # Collect metrics
                    metrics.end_time = time.time()
                    metrics.api_calls = self._estimate_api_calls(result)
                    
                    # Add metrics to result
                    result.execution_time = metrics.duration
                    result.resource_usage = {
                        'duration_seconds': metrics.duration,
                        'api_calls': metrics.api_calls
                    }
                    
                    # Validate result has required evidence
                    if self._validate_result_evidence(result):
                        logger.info(f"Strategy {strategy_index} completed successfully "
                                   f"in {metrics.duration:.1f}s")
                        return result
                    else:
                        logger.warning(f"Strategy {strategy_index} completed but failed validation")
                        return None
                        
            except Exception as e:
                logger.error(f"Strategy {strategy_index} execution error: {e}")
                metrics.errors.append(str(e))
                metrics.end_time = time.time()
                
                # Record metrics even for failures
                self.execution_metrics[strategy_index] = metrics
                return None
    
    @asynccontextmanager
    async def _create_isolated_environment(self, strategy_index: int):
        """
        Create isolated environment for strategy execution.
        """
        # Create strategy-specific working directory
        strategy_dir = self.v3_orchestrator.working_dir / f'.cc_automator/strategies/strategy_{strategy_index}'
        strategy_dir.mkdir(parents=True, exist_ok=True)
        
        original_cwd = Path.cwd()
        
        try:
            # Could implement more isolation here (Docker, etc.)
            yield {
                'working_dir': strategy_dir,
                'strategy_index': strategy_index
            }
        finally:
            # Cleanup if needed
            pass
    
    def _create_failure_callback(self, strategy_index: int):
        """
        Create failure callback for a specific strategy.
        """
        def callback(phase_name: str, error: Exception, context: Dict[str, Any]):
            logger.warning(f"Strategy {strategy_index} - Phase {phase_name} failed: {error}")
            # Could implement strategy-specific failure handling here
            return None
        
        return callback
    
    def _validate_result_evidence(self, result: 'ExecutionResult') -> bool:
        """
        Validate that result has required evidence files.
        
        This ensures parallel strategies can't cheat by claiming success
        without producing concrete evidence.
        """
        if not result.evidence_files:
            return False
        
        # Check for required evidence types
        evidence_names = {f.name for f in result.evidence_files if f.exists()}
        
        required_evidence = {
            'research.md',
            'plan.md',
            'main.py',  # Or other implementation files
            'test_results.log',
            'e2e_evidence.log'
        }
        
        # Need at least 3 of the required evidence types
        found_evidence = evidence_names & required_evidence
        
        if len(found_evidence) < 3:
            logger.warning(f"Insufficient evidence: only found {found_evidence}")
            return False
        
        # Check evidence files are non-empty
        for evidence_file in result.evidence_files:
            if evidence_file.exists() and evidence_file.stat().st_size == 0:
                logger.warning(f"Empty evidence file: {evidence_file}")
                return False
        
        return True
    
    def _estimate_api_calls(self, result: 'ExecutionResult') -> int:
        """
        Estimate API calls made during execution.
        """
        # This is a rough estimate based on phases completed
        phase_estimates = {
            'research': 5,
            'planning': 8,
            'implement': 15,
            'architecture': 10,
            'lint': 5,
            'typecheck': 5,
            'test': 10,
            'integration': 8,
            'e2e': 5,
            'validate': 3,
            'commit': 2
        }
        
        # Count based on evidence produced
        total_calls = 0
        evidence_to_phase = {
            'research.md': 'research',
            'plan.md': 'planning',
            'architecture_review.md': 'architecture',
            'test_results.log': 'test',
            'e2e_evidence.log': 'e2e'
        }
        
        for evidence_file in result.evidence_files:
            phase = evidence_to_phase.get(evidence_file.name)
            if phase:
                total_calls += phase_estimates.get(phase, 5)
        
        return total_calls
    
    async def compare_strategy_results(
        self,
        results: List['ExecutionResult']
    ) -> Dict[str, Any]:
        """
        Compare results from different strategies.
        
        Returns detailed comparison for decision making.
        """
        if not results:
            return {'error': 'No results to compare'}
        
        comparison = {
            'strategy_count': len(results),
            'strategies': []
        }
        
        for result in results:
            strategy_analysis = {
                'name': result.strategy_name,
                'success': result.success,
                'execution_time': result.execution_time,
                'evidence_score': self._score_evidence_quality(result.evidence_files),
                'test_coverage': self._estimate_test_coverage(result),
                'architecture_quality': self._assess_architecture_quality(result),
                'resource_efficiency': self._calculate_resource_efficiency(result)
            }
            
            # Calculate overall score
            strategy_analysis['overall_score'] = self._calculate_overall_score(strategy_analysis)
            
            comparison['strategies'].append(strategy_analysis)
        
        # Sort by overall score
        comparison['strategies'].sort(key=lambda x: x['overall_score'], reverse=True)
        
        # Identify best strategy
        comparison['recommended_strategy'] = comparison['strategies'][0]['name']
        comparison['recommendation_confidence'] = self._calculate_recommendation_confidence(
            comparison['strategies']
        )
        
        return comparison
    
    def _score_evidence_quality(self, evidence_files: List[Path]) -> float:
        """
        Score the quality and completeness of evidence.
        """
        if not evidence_files:
            return 0.0
        
        score = 0.0
        max_score = 0.0
        
        # Evidence type weights
        evidence_weights = {
            'research.md': 0.15,
            'plan.md': 0.15,
            'architecture_review.md': 0.2,
            'test_results.log': 0.2,
            'e2e_evidence.log': 0.2,
            'validation_report.md': 0.1
        }
        
        for evidence_type, weight in evidence_weights.items():
            max_score += weight
            
            # Find matching evidence file
            for evidence_file in evidence_files:
                if evidence_file.name == evidence_type and evidence_file.exists():
                    # Check file size (quality proxy)
                    size = evidence_file.stat().st_size
                    if size > 100:  # More than 100 bytes
                        score += weight
                        if size > 1000:  # Substantial content
                            score += weight * 0.2  # Bonus
                    break
        
        return min(score / max_score, 1.0) if max_score > 0 else 0.0
    
    def _estimate_test_coverage(self, result: 'ExecutionResult') -> float:
        """
        Estimate test coverage from result evidence.
        """
        # Look for test results
        test_evidence = None
        for evidence_file in result.evidence_files:
            if 'test' in evidence_file.name and evidence_file.exists():
                test_evidence = evidence_file
                break
        
        if not test_evidence:
            return 0.0
        
        try:
            content = test_evidence.read_text()
            
            # Look for pytest coverage output
            if 'coverage' in content.lower():
                # Try to extract percentage
                import re
                match = re.search(r'(\d+)%', content)
                if match:
                    return float(match.group(1)) / 100
            
            # Look for test counts
            if 'passed' in content:
                # Rough estimate based on test count
                match = re.search(r'(\d+) passed', content)
                if match:
                    test_count = int(match.group(1))
                    # Assume decent coverage if many tests
                    return min(test_count / 20, 1.0) * 0.8
            
            return 0.5  # Default if tests exist but no coverage info
            
        except Exception:
            return 0.3  # Error reading test evidence
    
    def _assess_architecture_quality(self, result: 'ExecutionResult') -> float:
        """
        Assess architecture quality from evidence.
        """
        # Look for architecture review
        arch_evidence = None
        for evidence_file in result.evidence_files:
            if 'architecture' in evidence_file.name and evidence_file.exists():
                arch_evidence = evidence_file
                break
        
        if not arch_evidence:
            return 0.3  # No architecture review
        
        try:
            content = arch_evidence.read_text().lower()
            
            # Perfect architecture validation
            if 'zero violations' in content or 'no issues found' in content:
                return 1.0
            
            # Check for specific issue counts
            import re
            violations = re.findall(r'(\d+)\s*violations?', content)
            if violations:
                violation_count = int(violations[0])
                # Score based on violation count
                if violation_count == 0:
                    return 1.0
                elif violation_count <= 3:
                    return 0.8
                elif violation_count <= 10:
                    return 0.6
                else:
                    return 0.4
            
            # Check for positive indicators
            if 'well-structured' in content or 'good design' in content:
                return 0.8
            
            return 0.5  # Default if review exists
            
        except Exception:
            return 0.3
    
    def _calculate_resource_efficiency(self, result: 'ExecutionResult') -> float:
        """
        Calculate resource efficiency score.
        """
        if not result.resource_usage:
            return 0.5  # No data
        
        efficiency = 1.0
        
        # Time efficiency (faster is better)
        duration = result.resource_usage.get('duration_seconds', 0)
        if duration > 0:
            # Normalize to 30 minutes as baseline
            time_score = min(1800 / duration, 2.0) / 2.0
            efficiency *= time_score
        
        # API call efficiency (fewer is better)
        api_calls = result.resource_usage.get('api_calls', 0)
        if api_calls > 0:
            # Normalize to 50 calls as baseline
            api_score = min(50 / api_calls, 2.0) / 2.0
            efficiency *= api_score
        
        return efficiency
    
    def _calculate_overall_score(self, analysis: Dict[str, Any]) -> float:
        """
        Calculate overall score for a strategy result.
        """
        # Weighted scoring
        weights = {
            'evidence_score': 0.25,
            'test_coverage': 0.2,
            'architecture_quality': 0.25,
            'resource_efficiency': 0.15,
            'success': 0.15  # Binary success indicator
        }
        
        score = 0.0
        for metric, weight in weights.items():
            if metric in analysis:
                value = 1.0 if (metric == 'success' and analysis[metric]) else analysis.get(metric, 0)
                score += value * weight
        
        return score
    
    def _calculate_recommendation_confidence(self, strategies: List[Dict[str, Any]]) -> float:
        """
        Calculate confidence in the recommendation.
        """
        if len(strategies) < 2:
            return 0.5  # Only one option
        
        # Check score differences
        best_score = strategies[0]['overall_score']
        second_score = strategies[1]['overall_score']
        
        score_diff = best_score - second_score
        
        # Confidence based on score separation
        if score_diff > 0.3:
            return 0.9  # Clear winner
        elif score_diff > 0.15:
            return 0.7  # Good separation
        elif score_diff > 0.05:
            return 0.5  # Marginal difference
        else:
            return 0.3  # Too close to call