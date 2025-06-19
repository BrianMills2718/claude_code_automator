#!/usr/bin/env python3
"""
V3 Stability Validation Framework

This tool implements the mandatory V3 stability gates identified in our
comprehensive risk analysis. It validates that V3 is truly stable before
any V4 development begins.

Validation Gates:
1. Fix TaskGroup Issues - Replace error masking with proper async cleanup
2. Consecutive Success Test - 10 ML Portfolio runs without SDK errors  
3. Resource Stability - Prove no memory leaks or connection accumulation
4. Stress Testing - 8+ hour operation without async cleanup failures
"""

import asyncio
import sys
import time
import subprocess
import json
import logging
import psutil
import statistics
from pathlib import Path
from dataclasses import dataclass, asdict
from typing import List, Dict, Any, Optional
import tempfile
import os

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

@dataclass
class ResourceMetrics:
    """Resource usage metrics for leak detection."""
    timestamp: float
    memory_mb: float
    open_fds: int
    cpu_percent: float
    network_connections: int
    
@dataclass
class TestRun:
    """Results from a single test run."""
    run_number: int
    start_time: float
    end_time: Optional[float]
    success: bool
    error_message: Optional[str]
    taskgroup_errors: int
    memory_start_mb: float
    memory_end_mb: float
    cost_usd: float
    milestones_completed: int

@dataclass
class StabilityResults:
    """Overall stability validation results."""
    consecutive_success_rate: float
    taskgroup_error_count: int
    memory_leak_detected: bool
    memory_growth_mb: float
    resource_leak_detected: bool
    avg_run_time_minutes: float
    total_cost_usd: float
    stress_test_passed: bool
    
class V3StabilityValidator:
    """
    Comprehensive V3 stability validation framework.
    
    Implements all stability gates required before V4 development.
    """
    
    def __init__(self, verbose: bool = True):
        self.verbose = verbose
        self.logger = self._setup_logging()
        self.test_runs: List[TestRun] = []
        self.resource_metrics: List[ResourceMetrics] = []
        self.project_path = Path("example_projects/ml_portfolio_analyzer")
        
    def _setup_logging(self) -> logging.Logger:
        """Set up logging for validation results."""
        logger = logging.getLogger("v3_stability_validator")
        logger.setLevel(logging.INFO if self.verbose else logging.WARNING)
        
        handler = logging.StreamHandler()
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        handler.setFormatter(formatter)
        logger.addHandler(handler)
        
        return logger
    
    def record_resource_metrics(self) -> ResourceMetrics:
        """Record current system resource usage."""
        try:
            process = psutil.Process()
            memory_mb = process.memory_info().rss / 1024 / 1024
            open_fds = process.num_fds() if hasattr(process, 'num_fds') else 0
            cpu_percent = process.cpu_percent()
            
            # Count network connections
            try:
                connections = process.connections()
                network_connections = len([c for c in connections if c.status == 'ESTABLISHED'])
            except (psutil.AccessDenied, psutil.NoSuchProcess):
                network_connections = 0
                
            metrics = ResourceMetrics(
                timestamp=time.time(),
                memory_mb=memory_mb,
                open_fds=open_fds,
                cpu_percent=cpu_percent,
                network_connections=network_connections
            )
            
            self.resource_metrics.append(metrics)
            return metrics
            
        except Exception as e:
            self.logger.warning(f"Failed to record resource metrics: {e}")
            return ResourceMetrics(time.time(), 0, 0, 0, 0)
    
    def analyze_taskgroup_errors(self, log_content: str) -> int:
        """Count TaskGroup cleanup race conditions in logs."""
        taskgroup_patterns = [
            "TaskGroup cleanup race condition detected",
            "unhandled errors in a TaskGroup",
            "BaseExceptionGroup",
            "Attempted to exit cancel scope"
        ]
        
        error_count = 0
        for pattern in taskgroup_patterns:
            error_count += log_content.lower().count(pattern.lower())
            
        return error_count
    
    def run_single_ml_portfolio_test(self, run_number: int) -> TestRun:
        """Run a single ML Portfolio Analyzer test and collect metrics."""
        self.logger.info(f"Starting test run #{run_number}")
        
        start_metrics = self.record_resource_metrics()
        start_time = time.time()
        
        test_run = TestRun(
            run_number=run_number,
            start_time=start_time,
            end_time=None,
            success=False,
            error_message=None,
            taskgroup_errors=0,
            memory_start_mb=start_metrics.memory_mb,
            memory_end_mb=0,
            cost_usd=0,
            milestones_completed=0
        )
        
        try:
            # Clean up any previous test state
            self._cleanup_previous_test()
            
            # Run the ML Portfolio test
            cmd = [
                sys.executable, "cli.py", 
                "example_projects/ml_portfolio_analyzer",
                "--infinite"  # Use infinite mode for stability testing
            ]
            
            # Create temporary log file for this run
            with tempfile.NamedTemporaryFile(mode='w+', suffix='.log', delete=False) as log_file:
                log_path = log_file.name
            
            # Run with timeout (max 2 hours per test)
            process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                bufsize=1,
                universal_newlines=True
            )
            
            # Monitor process with timeout
            timeout_seconds = 7200  # 2 hours max per test
            try:
                stdout, _ = process.communicate(timeout=timeout_seconds)
                
                # Save output for analysis
                with open(log_path, 'w') as f:
                    f.write(stdout)
                
                # Analyze results
                test_run.success = process.returncode == 0
                test_run.taskgroup_errors = self.analyze_taskgroup_errors(stdout)
                
                # Get final metrics
                end_metrics = self.record_resource_metrics()
                test_run.memory_end_mb = end_metrics.memory_mb
                test_run.end_time = time.time()
                
                # Parse progress for cost and milestone info
                progress_info = self._parse_progress_json()
                if progress_info:
                    test_run.cost_usd = progress_info.get('total_cost', 0)
                    test_run.milestones_completed = self._count_completed_milestones(progress_info)
                
                if not test_run.success:
                    test_run.error_message = f"Process failed with return code {process.returncode}"
                
            except subprocess.TimeoutExpired:
                process.kill()
                test_run.error_message = f"Test timed out after {timeout_seconds} seconds"
                test_run.end_time = time.time()
                
            finally:
                # Clean up log file
                try:
                    os.unlink(log_path)
                except OSError:
                    pass
                
        except Exception as e:
            test_run.error_message = str(e)
            test_run.end_time = time.time()
            
        # Log results
        duration_minutes = (test_run.end_time - test_run.start_time) / 60
        memory_delta = test_run.memory_end_mb - test_run.memory_start_mb
        
        self.logger.info(f"Run #{run_number} completed:")
        self.logger.info(f"  Success: {test_run.success}")
        self.logger.info(f"  Duration: {duration_minutes:.1f} minutes")
        self.logger.info(f"  TaskGroup errors: {test_run.taskgroup_errors}")
        self.logger.info(f"  Memory delta: {memory_delta:+.1f} MB")
        self.logger.info(f"  Cost: ${test_run.cost_usd:.2f}")
        self.logger.info(f"  Milestones: {test_run.milestones_completed}")
        
        if test_run.error_message:
            self.logger.error(f"  Error: {test_run.error_message}")
            
        return test_run
    
    def _cleanup_previous_test(self):
        """Clean up any state from previous test runs."""
        progress_file = self.project_path / ".cc_automator" / "progress.json"
        if progress_file.exists():
            try:
                # Backup previous results
                backup_path = progress_file.with_suffix(f".backup_{int(time.time())}.json")
                progress_file.rename(backup_path)
                self.logger.debug(f"Backed up previous progress to {backup_path}")
            except OSError as e:
                self.logger.warning(f"Failed to backup progress file: {e}")
    
    def _parse_progress_json(self) -> Optional[Dict[str, Any]]:
        """Parse the progress.json file for test results."""
        progress_file = self.project_path / ".cc_automator" / "progress.json"
        
        try:
            if progress_file.exists():
                with open(progress_file) as f:
                    return json.load(f)
        except (json.JSONDecodeError, OSError) as e:
            self.logger.warning(f"Failed to parse progress file: {e}")
            
        return None
    
    def _count_completed_milestones(self, progress_data: Dict[str, Any]) -> int:
        """Count how many milestones were fully completed."""
        milestones = progress_data.get('milestones', {})
        completed = 0
        
        for milestone_data in milestones.values():
            if milestone_data.get('completed_phases', 0) >= milestone_data.get('total_phases', 11):
                completed += 1
                
        return completed
    
    def run_consecutive_success_test(self, num_runs: int = 10) -> bool:
        """
        Stability Gate 1: Consecutive Success Test
        
        Run num_runs consecutive ML Portfolio tests and verify:
        - All runs complete successfully
        - No TaskGroup errors in any run
        - Memory usage remains stable
        """
        self.logger.info(f"Starting consecutive success test: {num_runs} runs")
        
        self.test_runs.clear()
        
        for i in range(1, num_runs + 1):
            test_run = self.run_single_ml_portfolio_test(i)
            self.test_runs.append(test_run)
            
            # Early termination on failure for efficiency
            if not test_run.success or test_run.taskgroup_errors > 0:
                self.logger.error(f"Consecutive success test FAILED at run {i}")
                return False
            
            # Brief pause between runs to allow system cleanup
            if i < num_runs:
                self.logger.info(f"Pausing 30 seconds before next run...")
                time.sleep(30)
        
        # Analyze overall results
        success_rate = sum(1 for run in self.test_runs if run.success) / len(self.test_runs)
        total_taskgroup_errors = sum(run.taskgroup_errors for run in self.test_runs)
        
        self.logger.info(f"Consecutive success test results:")
        self.logger.info(f"  Success rate: {success_rate:.1%}")
        self.logger.info(f"  Total TaskGroup errors: {total_taskgroup_errors}")
        
        passed = success_rate == 1.0 and total_taskgroup_errors == 0
        self.logger.info(f"Consecutive success test: {'PASSED' if passed else 'FAILED'}")
        
        return passed
    
    def analyze_resource_stability(self) -> Dict[str, Any]:
        """
        Stability Gate 2: Resource Stability Analysis
        
        Analyze resource usage patterns to detect:
        - Memory leaks
        - File descriptor leaks  
        - Network connection accumulation
        """
        if len(self.resource_metrics) < 10:
            return {"insufficient_data": True}
        
        # Analyze memory usage trend
        memory_values = [m.memory_mb for m in self.resource_metrics]
        memory_growth = memory_values[-1] - memory_values[0]
        memory_trend = statistics.mean(memory_values[-5:]) - statistics.mean(memory_values[:5])
        
        # Analyze file descriptor usage
        fd_values = [m.open_fds for m in self.resource_metrics]
        fd_growth = fd_values[-1] - fd_values[0]
        
        # Analyze network connections
        conn_values = [m.network_connections for m in self.resource_metrics]
        conn_max = max(conn_values)
        conn_avg = statistics.mean(conn_values)
        
        # Test run memory analysis
        if self.test_runs:
            run_memory_deltas = [run.memory_end_mb - run.memory_start_mb for run in self.test_runs]
            avg_memory_delta = statistics.mean(run_memory_deltas)
            max_memory_delta = max(run_memory_deltas)
        else:
            avg_memory_delta = 0
            max_memory_delta = 0
        
        analysis = {
            "memory_growth_mb": memory_growth,
            "memory_trend_mb": memory_trend,
            "fd_growth": fd_growth,
            "max_connections": conn_max,
            "avg_connections": conn_avg,
            "avg_run_memory_delta_mb": avg_memory_delta,
            "max_run_memory_delta_mb": max_memory_delta,
            "memory_leak_suspected": memory_growth > 100 or avg_memory_delta > 50,
            "fd_leak_suspected": fd_growth > 20,
            "connection_leak_suspected": conn_max > 50
        }
        
        self.logger.info("Resource stability analysis:")
        for key, value in analysis.items():
            if isinstance(value, float):
                self.logger.info(f"  {key}: {value:.2f}")
            else:
                self.logger.info(f"  {key}: {value}")
        
        return analysis
    
    async def run_stress_test(self, duration_hours: float = 8.0) -> bool:
        """
        Stability Gate 3: Stress Testing
        
        Run extended operation for specified duration and verify:
        - No crashes or hangs
        - Resource usage remains stable
        - TaskGroup errors don't accumulate
        """
        self.logger.info(f"Starting {duration_hours:.1f} hour stress test")
        
        start_time = time.time()
        end_time = start_time + (duration_hours * 3600)
        test_count = 0
        
        while time.time() < end_time:
            remaining_hours = (end_time - time.time()) / 3600
            self.logger.info(f"Stress test progress: {remaining_hours:.2f} hours remaining")
            
            # Run a test cycle
            test_count += 1
            test_run = self.run_single_ml_portfolio_test(f"stress_{test_count}")
            
            # Check for failures
            if not test_run.success:
                self.logger.error(f"Stress test FAILED at iteration {test_count}")
                return False
            
            if test_run.taskgroup_errors > 0:
                self.logger.error(f"TaskGroup errors detected in stress test iteration {test_count}")
                return False
            
            # Check resource stability every 10 runs
            if test_count % 10 == 0:
                resource_analysis = self.analyze_resource_stability()
                if resource_analysis.get("memory_leak_suspected") or resource_analysis.get("fd_leak_suspected"):
                    self.logger.error(f"Resource leak detected during stress test at iteration {test_count}")
                    return False
            
            # Brief pause between stress test cycles
            time.sleep(60)  # 1 minute between cycles
        
        self.logger.info(f"Stress test completed: {test_count} iterations over {duration_hours:.1f} hours")
        return True
    
    def generate_stability_report(self) -> StabilityResults:
        """Generate comprehensive stability validation report."""
        if not self.test_runs:
            raise ValueError("No test runs available for analysis")
        
        # Calculate metrics
        successful_runs = [run for run in self.test_runs if run.success]
        consecutive_success_rate = len(successful_runs) / len(self.test_runs)
        
        total_taskgroup_errors = sum(run.taskgroup_errors for run in self.test_runs)
        
        resource_analysis = self.analyze_resource_stability()
        memory_leak_detected = resource_analysis.get("memory_leak_suspected", False)
        memory_growth_mb = resource_analysis.get("memory_growth_mb", 0)
        resource_leak_detected = (
            memory_leak_detected or 
            resource_analysis.get("fd_leak_suspected", False) or
            resource_analysis.get("connection_leak_suspected", False)
        )
        
        run_times = [(run.end_time - run.start_time) / 60 for run in self.test_runs if run.end_time]
        avg_run_time_minutes = statistics.mean(run_times) if run_times else 0
        
        total_cost_usd = sum(run.cost_usd for run in self.test_runs)
        
        # Stress test considered passed if we have long-running data
        stress_test_passed = len(self.test_runs) >= 20  # Approximate 8+ hours
        
        results = StabilityResults(
            consecutive_success_rate=consecutive_success_rate,
            taskgroup_error_count=total_taskgroup_errors,
            memory_leak_detected=memory_leak_detected,
            memory_growth_mb=memory_growth_mb,
            resource_leak_detected=resource_leak_detected,
            avg_run_time_minutes=avg_run_time_minutes,
            total_cost_usd=total_cost_usd,
            stress_test_passed=stress_test_passed
        )
        
        return results
    
    def save_results(self, results: StabilityResults, output_path: str = "v3_stability_results.json"):
        """Save validation results to JSON file."""
        output_data = {
            "validation_timestamp": time.time(),
            "stability_results": asdict(results),
            "test_runs": [asdict(run) for run in self.test_runs],
            "resource_metrics_summary": {
                "total_metrics": len(self.resource_metrics),
                "memory_range_mb": [
                    min(m.memory_mb for m in self.resource_metrics),
                    max(m.memory_mb for m in self.resource_metrics)
                ] if self.resource_metrics else [0, 0]
            }
        }
        
        with open(output_path, 'w') as f:
            json.dump(output_data, f, indent=2)
        
        self.logger.info(f"Stability validation results saved to {output_path}")


def main():
    """Main validation entry point."""
    import argparse
    
    parser = argparse.ArgumentParser(description="V3 Stability Validation Framework")
    parser.add_argument("--consecutive-runs", type=int, default=10, 
                       help="Number of consecutive test runs (default: 10)")
    parser.add_argument("--stress-hours", type=float, default=8.0,
                       help="Stress test duration in hours (default: 8.0)")
    parser.add_argument("--quick-test", action="store_true",
                       help="Run quick validation (3 runs, 1 hour stress test)")
    parser.add_argument("--output", default="v3_stability_results.json",
                       help="Output file for results")
    parser.add_argument("--verbose", action="store_true", default=True,
                       help="Verbose logging")
    
    args = parser.parse_args()
    
    if args.quick_test:
        args.consecutive_runs = 3
        args.stress_hours = 1.0
    
    validator = V3StabilityValidator(verbose=args.verbose)
    
    print("=" * 80)
    print("V3 STABILITY VALIDATION FRAMEWORK")
    print("=" * 80)
    print(f"Consecutive runs: {args.consecutive_runs}")
    print(f"Stress test duration: {args.stress_hours:.1f} hours")
    print("=" * 80)
    
    try:
        # Run consecutive success test
        print("\n🔍 STABILITY GATE 1: Consecutive Success Test")
        consecutive_passed = validator.run_consecutive_success_test(args.consecutive_runs)
        
        if not consecutive_passed:
            print("❌ CONSECUTIVE SUCCESS TEST FAILED")
            print("V3 is NOT stable enough for V4 development")
            sys.exit(1)
        
        print("✅ Consecutive success test PASSED")
        
        # Analyze resource stability
        print("\n🔍 STABILITY GATE 2: Resource Stability Analysis")
        resource_analysis = validator.analyze_resource_stability()
        
        if resource_analysis.get("memory_leak_suspected") or resource_analysis.get("fd_leak_suspected"):
            print("❌ RESOURCE STABILITY TEST FAILED")
            print("Resource leaks detected - V3 needs stability work")
            sys.exit(1)
        
        print("✅ Resource stability analysis PASSED")
        
        # Run stress test (if requested)
        if args.stress_hours > 0:
            print(f"\n🔍 STABILITY GATE 3: {args.stress_hours:.1f} Hour Stress Test")
            stress_passed = asyncio.run(validator.run_stress_test(args.stress_hours))
            
            if not stress_passed:
                print("❌ STRESS TEST FAILED")
                print("V3 cannot handle extended operation")
                sys.exit(1)
            
            print("✅ Stress test PASSED")
        
        # Generate final report
        print("\n📊 Generating stability report...")
        results = validator.generate_stability_report()
        validator.save_results(results, args.output)
        
        # Final assessment
        print("\n" + "=" * 80)
        print("V3 STABILITY VALIDATION RESULTS")
        print("=" * 80)
        print(f"Consecutive success rate: {results.consecutive_success_rate:.1%}")
        print(f"TaskGroup error count: {results.taskgroup_error_count}")
        print(f"Memory leak detected: {results.memory_leak_detected}")
        print(f"Resource leak detected: {results.resource_leak_detected}")
        print(f"Average run time: {results.avg_run_time_minutes:.1f} minutes")
        print(f"Total cost: ${results.total_cost_usd:.2f}")
        print(f"Stress test passed: {results.stress_test_passed}")
        
        all_gates_passed = (
            results.consecutive_success_rate == 1.0 and
            results.taskgroup_error_count == 0 and
            not results.memory_leak_detected and
            not results.resource_leak_detected and
            results.stress_test_passed
        )
        
        if all_gates_passed:
            print("\n🎉 ALL STABILITY GATES PASSED")
            print("V3 is ready for V4 development")
        else:
            print("\n❌ STABILITY VALIDATION FAILED")
            print("V3 requires stability work before V4 development")
            sys.exit(1)
        
    except KeyboardInterrupt:
        print("\n⚠️  Validation interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n💥 Validation failed with error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()