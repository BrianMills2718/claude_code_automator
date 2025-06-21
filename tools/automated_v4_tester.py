#!/usr/bin/env python3
"""
Automated V4 Testing and Monitoring Script

Runs V4 tests continuously without user intervention, tracking progress
and automatically handling errors. Provides real-time status updates
and detailed logging of execution attempts.
"""

import os
import sys
import time
import json
import subprocess
import signal
import threading
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Any
import argparse

# Add project root to path
sys.path.append(str(Path(__file__).parent.parent))

class V4AutomatedTester:
    """Automated tester for V4 meta-agent system."""
    
    def __init__(self, project_path: str, config: Dict[str, Any] = None):
        self.project_path = Path(project_path).resolve()
        self.config = config or {}
        
        # Test configuration
        self.max_attempts = self.config.get('max_attempts', 10)
        self.retry_delay = self.config.get('retry_delay', 30)  # seconds
        self.timeout_per_attempt = self.config.get('timeout', 3600)  # 1 hour per attempt
        self.continuous = self.config.get('continuous', True)
        
        # Monitoring
        self.start_time = datetime.now()
        self.attempt_number = 0
        self.results_log = []
        self.current_process = None
        self.is_running = True
        
        # Logging
        self.log_dir = Path("logs/automated_v4_testing")
        self.log_dir.mkdir(parents=True, exist_ok=True)
        self.session_id = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # Setup signal handlers for graceful shutdown
        signal.signal(signal.SIGINT, self._signal_handler)
        signal.signal(signal.SIGTERM, self._signal_handler)
    
    def run(self):
        """Run automated testing loop."""
        print("🤖 Starting Automated V4 Testing")
        print(f"📁 Project: {self.project_path}")
        print(f"🎯 Max attempts: {self.max_attempts}")
        print(f"⏱️  Timeout per attempt: {self.timeout_per_attempt}s")
        print(f"🔄 Continuous mode: {self.continuous}")
        print("=" * 60)
        
        while self.is_running and (self.continuous or self.attempt_number < self.max_attempts):
            self.attempt_number += 1
            attempt_start = datetime.now()
            
            print(f"\n🚀 Attempt {self.attempt_number} started at {attempt_start.strftime('%H:%M:%S')}")
            
            try:
                result = self._run_single_attempt()
                self._record_result(result, attempt_start)
                
                if result['success']:
                    print(f"✅ Attempt {self.attempt_number} SUCCEEDED!")
                    self._log_success(result)
                    
                    if not self.continuous:
                        print("🎉 Success achieved, stopping (not in continuous mode)")
                        break
                else:
                    print(f"❌ Attempt {self.attempt_number} failed: {result.get('error', 'Unknown error')}")
                    self._log_failure(result)
                
            except KeyboardInterrupt:
                print("\n⏹️  Testing interrupted by user")
                break
            except Exception as e:
                print(f"💥 Unexpected error in attempt {self.attempt_number}: {str(e)}")
                self._record_result({'success': False, 'error': f'Unexpected: {str(e)}'}, attempt_start)
            
            # Wait before next attempt (unless this was the last attempt)
            if self.is_running and (self.continuous or self.attempt_number < self.max_attempts):
                print(f"⏳ Waiting {self.retry_delay}s before next attempt...")
                self._wait_with_status(self.retry_delay)
        
        self._generate_final_report()
    
    def _run_single_attempt(self) -> Dict[str, Any]:
        """Run a single V4 test attempt."""
        # Clean up any previous state
        self._cleanup_previous_state()
        
        # Build command
        cmd = [
            sys.executable, "cli.py",
            "--project", str(self.project_path),
            "--v4",
            "--explain"
        ]
        
        # Add force sonnet if configured
        if os.environ.get('FORCE_SONNET') == 'true':
            cmd.append("--force-sonnet")
        
        print(f"🔧 Command: {' '.join(cmd)}")
        
        try:
            # Run with timeout
            start_time = time.time()
            
            result = subprocess.run(
                cmd,
                cwd=Path(__file__).parent.parent,  # cc_automator4 root
                capture_output=True,
                text=True,
                timeout=self.timeout_per_attempt
            )
            
            execution_time = time.time() - start_time
            
            # Parse output for insights
            output_analysis = self._analyze_output(result.stdout, result.stderr)
            
            return {
                'success': result.returncode == 0,
                'returncode': result.returncode,
                'execution_time': execution_time,
                'stdout': result.stdout,
                'stderr': result.stderr,
                'analysis': output_analysis,
                'error': output_analysis.get('primary_error', 'Process failed') if result.returncode != 0 else None
            }
            
        except subprocess.TimeoutExpired:
            return {
                'success': False,
                'error': f'Timeout after {self.timeout_per_attempt}s',
                'execution_time': self.timeout_per_attempt,
                'stdout': '',
                'stderr': '',
                'analysis': {'timeout': True}
            }
    
    def _analyze_output(self, stdout: str, stderr: str) -> Dict[str, Any]:
        """Analyze command output to extract key information."""
        analysis = {
            'phases_attempted': [],
            'milestones_attempted': 0,
            'errors': [],
            'strategy_selections': 0,
            'context_analysis_completed': False,
            'v3_execution_started': False,
            'async_error': False
        }
        
        combined_output = stdout + "\n" + stderr
        lines = combined_output.split('\n')
        
        for line in lines:
            line = line.strip()
            
            # Track strategy selections
            if "🎯 Strategy Selection:" in line:
                analysis['strategy_selections'] += 1
            
            # Track context analysis
            if "🔍 Project Context Analysis:" in line:
                analysis['context_analysis_completed'] = True
            
            # Track V3 execution start
            if "CC_AUTOMATOR4 - Autonomous Code Generation" in line:
                analysis['v3_execution_started'] = True
            
            # Track milestones
            if "Milestone" in line and ("starting" in line.lower() or "#" in line):
                analysis['milestones_attempted'] += 1
            
            # Track phases
            if "Starting" in line and "phase" in line:
                phase_name = self._extract_phase_name(line)
                if phase_name:
                    analysis['phases_attempted'].append(phase_name)
            
            # Track specific errors
            if "Already running asyncio in this thread" in line:
                analysis['async_error'] = True
                analysis['primary_error'] = "AsyncIO conflict - V4 trying to run async inside async"
            
            if "❌" in line or "failed" in line.lower():
                analysis['errors'].append(line)
        
        # Determine primary issue
        if analysis['async_error']:
            analysis['primary_error'] = "AsyncIO nesting issue"
        elif analysis['strategy_selections'] > 3:
            analysis['primary_error'] = "Strategy selection loop"
        elif not analysis['v3_execution_started']:
            analysis['primary_error'] = "V3 execution never started"
        elif not analysis['phases_attempted']:
            analysis['primary_error'] = "No phases executed"
        
        return analysis
    
    def _extract_phase_name(self, line: str) -> Optional[str]:
        """Extract phase name from log line."""
        # Look for patterns like "Starting research phase" or "[1/11] Starting research phase"
        parts = line.lower().split()
        if 'starting' in parts:
            try:
                start_idx = parts.index('starting')
                if start_idx + 1 < len(parts):
                    phase = parts[start_idx + 1]
                    if phase.endswith('...'):
                        phase = phase[:-3]
                    return phase
            except:
                pass
        return None
    
    def _cleanup_previous_state(self):
        """Clean up any state from previous runs."""
        cc_automator_dir = self.project_path / '.cc_automator'
        if cc_automator_dir.exists():
            try:
                # Remove session files that might cause conflicts
                session_files = cc_automator_dir.glob('session_*.json')
                for f in session_files:
                    f.unlink(missing_ok=True)
                
                # Clear any lock files
                lock_files = cc_automator_dir.glob('*.lock')
                for f in lock_files:
                    f.unlink(missing_ok=True)
                    
            except Exception as e:
                print(f"⚠️  Warning: Could not clean up state: {e}")
    
    def _record_result(self, result: Dict[str, Any], start_time: datetime):
        """Record result of an attempt."""
        record = {
            'attempt': self.attempt_number,
            'start_time': start_time.isoformat(),
            'end_time': datetime.now().isoformat(),
            'success': result['success'],
            'execution_time': result.get('execution_time', 0),
            'error': result.get('error'),
            'analysis': result.get('analysis', {}),
            'returncode': result.get('returncode')
        }
        
        self.results_log.append(record)
        
        # Save to file
        log_file = self.log_dir / f"session_{self.session_id}_results.json"
        with open(log_file, 'w') as f:
            json.dump({
                'session_id': self.session_id,
                'project_path': str(self.project_path),
                'config': self.config,
                'start_time': self.start_time.isoformat(),
                'results': self.results_log
            }, f, indent=2)
    
    def _log_success(self, result: Dict[str, Any]):
        """Log successful attempt details."""
        print(f"⏱️  Execution time: {result.get('execution_time', 0):.1f}s")
        analysis = result.get('analysis', {})
        print(f"📊 Milestones attempted: {analysis.get('milestones_attempted', 0)}")
        print(f"📊 Phases completed: {len(analysis.get('phases_attempted', []))}")
    
    def _log_failure(self, result: Dict[str, Any]):
        """Log failure details."""
        analysis = result.get('analysis', {})
        print(f"🔍 Primary issue: {analysis.get('primary_error', 'Unknown')}")
        print(f"📊 Strategy selections: {analysis.get('strategy_selections', 0)}")
        print(f"📊 V3 execution started: {analysis.get('v3_execution_started', False)}")
        print(f"📊 Phases attempted: {analysis.get('phases_attempted', [])}")
        
        if analysis.get('async_error'):
            print("🚨 AsyncIO nesting detected - this is the main issue to fix")
    
    def _wait_with_status(self, seconds: int):
        """Wait with live countdown status."""
        for remaining in range(seconds, 0, -1):
            if not self.is_running:
                break
            print(f"\r⏳ Next attempt in {remaining}s...", end='', flush=True)
            time.sleep(1)
        print()  # New line after countdown
    
    def _signal_handler(self, signum, frame):
        """Handle shutdown signals gracefully."""
        print(f"\n📶 Received signal {signum}, shutting down gracefully...")
        self.is_running = False
        if self.current_process:
            self.current_process.terminate()
    
    def _generate_final_report(self):
        """Generate final testing report."""
        total_time = datetime.now() - self.start_time
        successful_attempts = sum(1 for r in self.results_log if r['success'])
        
        print("\n" + "=" * 60)
        print("📊 FINAL AUTOMATED TESTING REPORT")
        print("=" * 60)
        print(f"🕐 Total testing time: {total_time}")
        print(f"🔢 Total attempts: {len(self.results_log)}")
        print(f"✅ Successful attempts: {successful_attempts}")
        print(f"❌ Failed attempts: {len(self.results_log) - successful_attempts}")
        
        if successful_attempts > 0:
            print(f"🎯 Success rate: {(successful_attempts/len(self.results_log)*100):.1f}%")
        
        # Common issues analysis
        issues = {}
        for result in self.results_log:
            error = result.get('analysis', {}).get('primary_error', 'Unknown')
            issues[error] = issues.get(error, 0) + 1
        
        if issues:
            print("\n🔍 Common Issues:")
            for issue, count in sorted(issues.items(), key=lambda x: x[1], reverse=True):
                print(f"  • {issue}: {count} times")
        
        # Save final report
        report_file = self.log_dir / f"session_{self.session_id}_final_report.json"
        with open(report_file, 'w') as f:
            json.dump({
                'session_summary': {
                    'session_id': self.session_id,
                    'total_time': str(total_time),
                    'total_attempts': len(self.results_log),
                    'successful_attempts': successful_attempts,
                    'success_rate': successful_attempts/len(self.results_log) if self.results_log else 0,
                    'common_issues': issues
                },
                'detailed_results': self.results_log
            }, f, indent=2)
        
        print(f"\n📄 Full report saved to: {report_file}")


def main():
    """Main entry point for automated testing."""
    parser = argparse.ArgumentParser(
        description="Automated V4 Testing and Monitoring",
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    
    parser.add_argument("--project", type=str, 
                       default="example_projects/ml_portfolio_analyzer",
                       help="Project to test (default: ml_portfolio_analyzer)")
    parser.add_argument("--max-attempts", type=int, default=10,
                       help="Maximum attempts before stopping (default: 10)")
    parser.add_argument("--timeout", type=int, default=3600,
                       help="Timeout per attempt in seconds (default: 3600)")
    parser.add_argument("--retry-delay", type=int, default=30,
                       help="Delay between attempts in seconds (default: 30)")
    parser.add_argument("--continuous", action="store_true",
                       help="Run continuously even after success")
    parser.add_argument("--one-shot", action="store_true",
                       help="Run only one attempt")
    
    args = parser.parse_args()
    
    # Set force sonnet for cost efficiency
    os.environ['FORCE_SONNET'] = 'true'
    
    config = {
        'max_attempts': 1 if args.one_shot else args.max_attempts,
        'timeout': args.timeout,
        'retry_delay': args.retry_delay,
        'continuous': args.continuous and not args.one_shot
    }
    
    tester = V4AutomatedTester(args.project, config)
    tester.run()


if __name__ == "__main__":
    main()