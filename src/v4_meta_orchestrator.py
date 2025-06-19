"""
CC_AUTOMATOR4 V4 Meta-Orchestrator
Main entry point for V4's intelligent orchestration system.
Wraps V3 orchestrator with adaptive intelligence while preserving evidence-based validation.
"""

import asyncio
import json
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any
from datetime import datetime
import logging

from .orchestrator import CCAutomatorOrchestrator
from .v4_strategy_manager import V4StrategyManager
from .v4_failure_analyzer import V4FailureAnalyzer
from .v4_context_analyzer import V4ContextAnalyzer
from .v4_multi_executor import V4MultiStrategyExecutor
from .progress_tracker import ProgressTracker
from .session_manager import SessionManager
from .milestone_decomposer import MilestoneDecomposer

logger = logging.getLogger(__name__)


class V4MetaOrchestrator:
    """
    Intelligent meta-orchestrator that adds adaptive strategies to V3's proven foundation.
    
    Key Principles:
    - Preserves all V3 evidence-based validation
    - Adds contextual intelligence for strategy selection
    - Learns from failures to prevent infinite loops
    - Supports multi-strategy exploration when beneficial
    """
    
    def __init__(self, project_path: Path, config: Optional[Dict[str, Any]] = None):
        """Initialize V4 meta-orchestrator with V3 foundation."""
        self.project_path = Path(project_path)
        self.config = config or {}
        
        # Core V3 components (preserved)
        self.v3_orchestrator = CCAutomatorOrchestrator(project_path)
        self.progress_tracker = ProgressTracker(project_path, project_path.name)
        self.session_manager = SessionManager(project_path)
        
        # V4 intelligent components
        self.strategy_manager = V4StrategyManager(self.v3_orchestrator)
        self.failure_analyzer = V4FailureAnalyzer(project_path)
        self.context_analyzer = V4ContextAnalyzer(project_path)
        self.multi_executor = V4MultiStrategyExecutor(self.v3_orchestrator)
        
        # Learning and history
        self.failure_history = self._load_failure_history()
        self.strategy_performance = self._load_strategy_performance()
        self.learning_enabled = config.get('learning_enabled', True)
        
        # V4 feature flags
        self.enable_parallel_strategies = config.get('parallel_strategies', False)
        self.enable_adaptive_parameters = config.get('adaptive_parameters', True)
        self.enable_intelligent_stepback = config.get('intelligent_stepback', True)
        self.explain_decisions = config.get('explain_decisions', False)
        
        logger.info(f"V4 Meta-Orchestrator initialized with features: "
                   f"parallel={self.enable_parallel_strategies}, "
                   f"adaptive={self.enable_adaptive_parameters}, "
                   f"intelligent_stepback={self.enable_intelligent_stepback}")
    
    async def run(self) -> bool:
        """
        Run the complete project with intelligent orchestration.
        Returns True if all milestones completed successfully.
        """
        try:
            # Analyze project context
            logger.info("Analyzing project context...")
            project_context = await self.context_analyzer.analyze_project()
            
            if self.explain_decisions:
                self._explain_context_analysis(project_context)
            
            # Load milestones
            milestones = MilestoneDecomposer.extract_milestones()
            logger.info(f"Found {len(milestones)} milestones to complete")
            
            # Process each milestone with intelligent orchestration
            for milestone_num, milestone in enumerate(milestones, 1):
                success = await self._orchestrate_milestone(
                    milestone_num, 
                    milestone, 
                    project_context
                )
                
                if not success:
                    logger.error(f"Milestone {milestone_num} failed after all attempts")
                    return False
                    
                logger.info(f"Milestone {milestone_num} completed successfully")
            
            # Save learning data for future runs
            if self.learning_enabled:
                self._save_learning_data()
            
            return True
            
        except Exception as e:
            logger.error(f"V4 orchestration failed: {str(e)}")
            return False
    
    async def _orchestrate_milestone(
        self, 
        milestone_num: int, 
        milestone: str, 
        project_context: 'ProjectContext'
    ) -> bool:
        """
        Orchestrate a single milestone with intelligent strategy selection.
        """
        logger.info(f"Starting milestone {milestone_num}: {milestone}")
        
        # Select initial strategy based on context and history
        strategy = self.strategy_manager.select_strategy(
            project_context,
            self.failure_history,
            milestone
        )
        
        if self.explain_decisions:
            self._explain_strategy_selection(strategy, project_context)
        
        # Execute with intelligent monitoring and adaptation
        max_strategy_switches = 3
        strategy_switches = 0
        
        while strategy_switches < max_strategy_switches:
            try:
                # Execute strategy with failure monitoring
                result = await self._execute_strategy_with_monitoring(
                    strategy,
                    milestone_num,
                    milestone,
                    project_context
                )
                
                # Validate result using V3's evidence-based system
                if self._validate_milestone_completion(result):
                    # Record successful strategy for learning
                    if self.learning_enabled:
                        self._record_strategy_success(
                            strategy, 
                            project_context, 
                            result
                        )
                    return True
                else:
                    raise ValueError("Strategy completed but failed evidence validation")
                    
            except Exception as e:
                logger.warning(f"Strategy {strategy.name} failed: {str(e)}")
                
                # Analyze failure and potentially switch strategies
                failure_analysis = await self.failure_analyzer.analyze_failure(
                    strategy,
                    e,
                    self._get_execution_context(milestone_num)
                )
                
                if self.explain_decisions:
                    self._explain_failure_analysis(failure_analysis)
                
                # Determine if we should switch strategies
                if failure_analysis.suggests_strategy_switch():
                    new_strategy = self.strategy_manager.select_alternative_strategy(
                        strategy,
                        failure_analysis,
                        project_context
                    )
                    
                    if new_strategy != strategy:
                        logger.info(f"Switching from {strategy.name} to {new_strategy.name}")
                        strategy = new_strategy
                        strategy_switches += 1
                        continue
                
                # If no strategy switch, break and fail
                break
        
        logger.error(f"Milestone {milestone_num} failed after {strategy_switches} strategy switches")
        return False
    
    async def _execute_strategy_with_monitoring(
        self,
        strategy: 'Strategy',
        milestone_num: int,
        milestone: str,
        project_context: 'ProjectContext'
    ) -> 'ExecutionResult':
        """
        Execute a strategy with intelligent monitoring and potential parallel exploration.
        """
        # Check if parallel exploration would be beneficial
        if (self.enable_parallel_strategies and 
            self._should_use_parallel_exploration(project_context, self.failure_history)):
            
            logger.info("Using parallel strategy exploration")
            return await self._execute_parallel_strategies(
                strategy,
                milestone_num,
                milestone,
                project_context
            )
        else:
            # Single strategy execution with monitoring
            return await strategy.execute(
                milestone_num,
                milestone,
                failure_callback=self._handle_phase_failure
            )
    
    async def _execute_parallel_strategies(
        self,
        primary_strategy: 'Strategy',
        milestone_num: int,
        milestone: str,
        project_context: 'ProjectContext'
    ) -> 'ExecutionResult':
        """
        Execute multiple strategies in parallel and select the best result.
        """
        # Generate alternative strategies
        strategies = self.strategy_manager.generate_exploration_strategies(
            primary_strategy,
            project_context,
            max_strategies=3
        )
        
        logger.info(f"Exploring {len(strategies)} strategies in parallel")
        
        # Execute in parallel with resource management
        results = await self.multi_executor.execute_parallel_strategies(
            strategies,
            milestone_num,
            milestone
        )
        
        # Validate all results and select best
        validated_results = []
        for result in results:
            if self._validate_milestone_completion(result):
                validated_results.append(result)
        
        if not validated_results:
            raise ValueError("No parallel strategies produced valid results")
        
        # Select best result based on evidence quality
        best_result = self._select_best_result(validated_results)
        
        if self.explain_decisions:
            self._explain_result_selection(results, best_result)
        
        return best_result
    
    async def _handle_phase_failure(
        self,
        phase_name: str,
        error: Exception,
        context: Dict[str, Any]
    ) -> Optional[Dict[str, Any]]:
        """
        Intelligent phase failure handling with learning.
        """
        # Record failure for pattern analysis
        self.failure_analyzer.record_phase_failure(
            phase_name,
            error,
            context
        )
        
        # Check for infinite loop patterns
        if self.failure_analyzer.detect_infinite_loop(phase_name, context):
            logger.warning(f"Infinite loop detected in phase {phase_name}")
            
            if self.enable_intelligent_stepback:
                # Generate constraints to break the loop
                constraints = self.failure_analyzer.generate_loop_breaking_constraints(
                    phase_name,
                    context
                )
                
                return {
                    'action': 'step_back_with_constraints',
                    'target_phase': self._determine_stepback_target(phase_name, context),
                    'constraints': constraints
                }
        
        # Check if we should adapt parameters
        if self.enable_adaptive_parameters:
            adapted_params = self._adapt_phase_parameters(
                phase_name,
                error,
                context
            )
            
            if adapted_params:
                return {
                    'action': 'retry_with_adaptation',
                    'parameters': adapted_params
                }
        
        # Default to V3 behavior
        return None
    
    def _validate_milestone_completion(self, result: 'ExecutionResult') -> bool:
        """
        Validate milestone completion using V3's evidence-based system.
        CRITICAL: This ensures meta-agent cannot lie about success.
        """
        try:
            # Use V3's validation system
            validation_result = self.v3_orchestrator.validate_milestone_evidence(
                result.milestone_num,
                result.evidence_files
            )
            
            if not validation_result['valid']:
                logger.warning(f"Evidence validation failed: {validation_result['reason']}")
                return False
            
            # Additional V4 validation for learning data
            if self.learning_enabled and hasattr(result, 'learning_data'):
                learning_validation = self._validate_learning_evidence(
                    result.learning_data
                )
                if not learning_validation:
                    logger.warning("Learning data validation failed")
                    # Don't fail milestone, but don't save learning data
                    result.learning_data = None
            
            return True
            
        except Exception as e:
            logger.error(f"Validation error: {str(e)}")
            return False
    
    def _should_use_parallel_exploration(
        self,
        context: 'ProjectContext',
        history: 'FailureHistory'
    ) -> bool:
        """
        Determine if parallel strategy exploration would be beneficial.
        """
        # Don't use parallel for simple projects
        if context.complexity_score < 0.5:
            return False
        
        # Use parallel if we've had repeated failures
        if history.get_failure_count_for_project_type(context.project_type) > 5:
            return True
        
        # Use parallel for ambiguous requirements
        if context.requirement_clarity < 0.3:
            return True
        
        return False
    
    def _determine_stepback_target(
        self,
        failed_phase: str,
        context: Dict[str, Any]
    ) -> str:
        """
        Intelligently determine which phase to step back to.
        """
        # Analyze failure patterns to find root cause
        root_cause_analysis = self.failure_analyzer.trace_failure_root_cause(
            failed_phase,
            context
        )
        
        # Map common patterns to stepback targets
        stepback_mapping = {
            'architecture_loops': 'planning',  # Bad planning causes architecture issues
            'test_failures': 'implement',      # Implementation issues cause test failures
            'integration_issues': 'architecture',  # Poor architecture causes integration issues
            'missing_requirements': 'research'  # Incomplete research causes downstream issues
        }
        
        pattern = root_cause_analysis.get('pattern', 'unknown')
        return stepback_mapping.get(pattern, 'planning')  # Default to planning
    
    def _adapt_phase_parameters(
        self,
        phase_name: str,
        error: Exception,
        context: Dict[str, Any]
    ) -> Optional[Dict[str, Any]]:
        """
        Adapt phase parameters based on failure patterns.
        """
        # Get failure history for this phase
        phase_failures = self.failure_history.get_phase_failures(phase_name)
        
        if len(phase_failures) < 2:
            return None  # Not enough data to adapt
        
        # Analyze patterns and suggest adaptations
        adaptations = {}
        
        # Increase turns for timeout patterns
        if any('timeout' in str(f.error) for f in phase_failures[-3:]):
            current_turns = context.get('max_turns', 30)
            adaptations['max_turns'] = int(current_turns * 1.5)
            adaptations['think_mode'] = 'think harder'
        
        # Add more context for confusion patterns
        if any('unclear' in str(f.error) or 'ambiguous' in str(f.error) 
               for f in phase_failures[-3:]):
            adaptations['additional_context'] = self._gather_clarifying_context(
                phase_name,
                context
            )
        
        return adaptations if adaptations else None
    
    def _gather_clarifying_context(
        self,
        phase_name: str,
        context: Dict[str, Any]
    ) -> str:
        """
        Gather additional context to clarify ambiguous situations.
        """
        clarifications = []
        
        # Add examples from successful similar projects
        similar_successes = self.strategy_performance.get_similar_successes(
            context.get('project_type'),
            phase_name
        )
        
        if similar_successes:
            clarifications.append(
                f"Similar successful {context.get('project_type')} projects "
                f"handled {phase_name} by: {similar_successes[0].approach_summary}"
            )
        
        # Add specific constraints based on failure patterns
        if phase_name == 'architecture':
            clarifications.append(
                "Focus on modular design with clear separation of concerns. "
                "Ensure no circular dependencies and maintain consistent patterns."
            )
        
        return "\n".join(clarifications)
    
    def _select_best_result(
        self,
        results: List['ExecutionResult']
    ) -> 'ExecutionResult':
        """
        Select the best result from multiple parallel executions.
        """
        # Score each result based on multiple criteria
        scored_results = []
        
        for result in results:
            score = 0
            
            # Evidence completeness
            score += len(result.evidence_files) * 10
            
            # Test coverage
            if hasattr(result, 'test_coverage'):
                score += result.test_coverage * 100
            
            # Execution time (prefer faster)
            if hasattr(result, 'execution_time'):
                score += (1.0 / (1 + result.execution_time)) * 50
            
            # Architecture quality
            if hasattr(result, 'architecture_score'):
                score += result.architecture_score * 100
            
            scored_results.append((score, result))
        
        # Return highest scoring result
        scored_results.sort(key=lambda x: x[0], reverse=True)
        return scored_results[0][1]
    
    def _record_strategy_success(
        self,
        strategy: 'Strategy',
        context: 'ProjectContext',
        result: 'ExecutionResult'
    ):
        """
        Record successful strategy execution for future learning.
        """
        self.strategy_performance.record_success({
            'strategy': strategy.name,
            'project_type': context.project_type,
            'complexity': context.complexity_score,
            'execution_time': result.execution_time,
            'resource_usage': result.resource_usage,
            'evidence_quality': self._score_evidence_quality(result.evidence_files),
            'timestamp': datetime.now().isoformat()
        })
    
    def _score_evidence_quality(self, evidence_files: List[Path]) -> float:
        """
        Score the quality of evidence files (0.0 to 1.0).
        """
        if not evidence_files:
            return 0.0
        
        score = 0.0
        
        # Check for required evidence types
        evidence_types = {f.name for f in evidence_files}
        
        required_evidence = {
            'research.md': 0.1,
            'plan.md': 0.1,
            'architecture_review.md': 0.2,
            'test_results.log': 0.2,
            'e2e_evidence.log': 0.2,
            'validation_report.md': 0.2
        }
        
        for required, weight in required_evidence.items():
            if any(required in f for f in evidence_types):
                score += weight
        
        return min(score, 1.0)
    
    def _load_failure_history(self) -> 'FailureHistory':
        """Load historical failure data for learning."""
        history_file = self.project_path / '.cc_automator' / 'v4_failure_history.json'
        if history_file.exists():
            with open(history_file) as f:
                data = json.load(f)
                return FailureHistory.from_dict(data)
        return FailureHistory()
    
    def _load_strategy_performance(self) -> 'StrategyPerformance':
        """Load historical strategy performance data."""
        perf_file = self.project_path / '.cc_automator' / 'v4_strategy_performance.json'
        if perf_file.exists():
            with open(perf_file) as f:
                data = json.load(f)
                return StrategyPerformance.from_dict(data)
        return StrategyPerformance()
    
    def _save_learning_data(self):
        """Save learning data for future runs."""
        learning_dir = self.project_path / '.cc_automator'
        learning_dir.mkdir(exist_ok=True)
        
        # Save failure history
        history_file = learning_dir / 'v4_failure_history.json'
        with open(history_file, 'w') as f:
            json.dump(self.failure_history.to_dict(), f, indent=2)
        
        # Save strategy performance
        perf_file = learning_dir / 'v4_strategy_performance.json'
        with open(perf_file, 'w') as f:
            json.dump(self.strategy_performance.to_dict(), f, indent=2)
    
    def _get_execution_context(self, milestone_num: int) -> Dict[str, Any]:
        """Get current execution context for analysis."""
        return {
            'milestone_num': milestone_num,
            'project_path': str(self.project_path),
            'session_data': self.session_manager.get_all_sessions(),
            'progress': self.progress_tracker.get_current_progress(),
            'timestamp': datetime.now().isoformat()
        }
    
    # Explanation methods for transparency
    def _explain_context_analysis(self, context: 'ProjectContext'):
        """Explain project context analysis to user."""
        print("\n🔍 Project Context Analysis:")
        print(f"  - Project Type: {context.project_type}")
        print(f"  - Complexity Score: {context.complexity_score:.2f}/1.0")
        print(f"  - Technology Stack: {', '.join(context.technology_stack)}")
        print(f"  - Requirement Clarity: {context.requirement_clarity:.2f}/1.0")
        print(f"  - Similar Past Projects: {len(context.similar_projects)}")
    
    def _explain_strategy_selection(self, strategy: 'Strategy', context: 'ProjectContext'):
        """Explain why a particular strategy was selected."""
        print(f"\n🎯 Strategy Selection: {strategy.name}")
        print(f"  - Reason: {strategy.selection_reason}")
        print(f"  - Best for: {strategy.best_for_description}")
        print(f"  - Expected phases: {len(strategy.get_phases())}")
    
    def _explain_failure_analysis(self, analysis: 'FailureAnalysis'):
        """Explain failure analysis results."""
        print(f"\n❌ Failure Analysis:")
        print(f"  - Type: {analysis.failure_type}")
        print(f"  - Root Cause: {analysis.root_cause}")
        print(f"  - Pattern: {analysis.pattern_name}")
        print(f"  - Suggested Action: {analysis.suggested_action}")
    
    def _explain_result_selection(self, results: List['ExecutionResult'], best: 'ExecutionResult'):
        """Explain why a particular result was selected from parallel execution."""
        print(f"\n✅ Result Selection from {len(results)} parallel executions:")
        for i, result in enumerate(results):
            score = self._score_evidence_quality(result.evidence_files)
            print(f"  - Strategy {i+1}: {result.strategy_name} (score: {score:.2f})")
        print(f"  - Selected: {best.strategy_name} (best evidence quality)")


# Support classes referenced above
class FailureHistory:
    """Tracks historical failures for pattern recognition."""
    
    def __init__(self):
        self.failures = []
    
    def get_failure_count_for_project_type(self, project_type: str) -> int:
        return sum(1 for f in self.failures if f.get('project_type') == project_type)
    
    def get_phase_failures(self, phase_name: str) -> List[Dict[str, Any]]:
        return [f for f in self.failures if f.get('phase') == phase_name]
    
    def to_dict(self) -> Dict[str, Any]:
        return {'failures': self.failures}
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'FailureHistory':
        history = cls()
        history.failures = data.get('failures', [])
        return history


class StrategyPerformance:
    """Tracks strategy performance metrics."""
    
    def __init__(self):
        self.performances = []
    
    def record_success(self, performance_data: Dict[str, Any]):
        self.performances.append(performance_data)
    
    def get_similar_successes(self, project_type: str, phase_name: str) -> List[Dict[str, Any]]:
        return [
            p for p in self.performances 
            if p.get('project_type') == project_type and p.get('phase') == phase_name
        ]
    
    def to_dict(self) -> Dict[str, Any]:
        return {'performances': self.performances}
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'StrategyPerformance':
        perf = cls()
        perf.performances = data.get('performances', [])
        return perf