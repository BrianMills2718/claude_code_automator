#!/usr/bin/env python3
"""
ML Portfolio Test Monitor

Monitor the currently running ML Portfolio test for:
- Progress updates
- Resource usage
- TaskGroup errors
- Stability metrics

This provides real-time data about V3 stability while the test runs.
"""

import time
import json
import psutil
import subprocess
import sys
from pathlib import Path
from datetime import datetime
from typing import Optional, Dict, Any

class MLPortfolioTestMonitor:
    """Monitor ongoing ML Portfolio test for stability metrics."""
    
    def __init__(self):
        self.project_path = Path("example_projects/ml_portfolio_analyzer")
        self.progress_file = self.project_path / ".cc_automator" / "progress.json"
        self.start_time = time.time()
        self.last_progress = None
        self.resource_samples = []
        
    def get_current_progress(self) -> Optional[Dict[str, Any]]:
        """Get current test progress from progress.json."""
        try:
            if self.progress_file.exists():
                with open(self.progress_file) as f:
                    return json.load(f)
        except (json.JSONDecodeError, OSError) as e:
            print(f"Warning: Failed to read progress file: {e}")
        return None
    
    def get_resource_usage(self) -> Dict[str, Any]:
        """Get current system resource usage."""
        try:
            process = psutil.Process()
            memory_mb = process.memory_info().rss / 1024 / 1024
            cpu_percent = process.cpu_percent()
            
            # Get system-wide stats
            system_memory = psutil.virtual_memory()
            system_cpu = psutil.cpu_percent(interval=1)
            
            return {
                "timestamp": time.time(),
                "process_memory_mb": memory_mb,
                "process_cpu_percent": cpu_percent,
                "system_memory_percent": system_memory.percent,
                "system_cpu_percent": system_cpu,
                "available_memory_gb": system_memory.available / 1024 / 1024 / 1024
            }
        except Exception as e:
            print(f"Warning: Failed to get resource usage: {e}")
            return {"timestamp": time.time()}
    
    def check_for_taskgroup_errors(self) -> int:
        """Check recent logs for TaskGroup errors."""
        try:
            # Look for recent log files
            log_dir = self.project_path / ".cc_automator" / "logs"
            if not log_dir.exists():
                return 0
            
            recent_logs = sorted(log_dir.glob("*.log"), key=lambda p: p.stat().st_mtime)[-5:]
            
            error_count = 0
            taskgroup_patterns = [
                "TaskGroup cleanup race condition detected",
                "unhandled errors in a TaskGroup",
                "BaseExceptionGroup"
            ]
            
            for log_file in recent_logs:
                try:
                    content = log_file.read_text()
                    for pattern in taskgroup_patterns:
                        error_count += content.lower().count(pattern.lower())
                except OSError:
                    continue
            
            return error_count
            
        except Exception as e:
            print(f"Warning: Failed to check TaskGroup errors: {e}")
            return 0
    
    def format_duration(self, seconds: float) -> str:
        """Format duration in human-readable format."""
        hours = int(seconds // 3600)
        minutes = int((seconds % 3600) // 60)
        secs = int(seconds % 60)
        
        if hours > 0:
            return f"{hours}h {minutes}m {secs}s"
        elif minutes > 0:
            return f"{minutes}m {secs}s"
        else:
            return f"{secs}s"
    
    def print_progress_summary(self, progress: Dict[str, Any]):
        """Print a summary of current test progress."""
        current_milestone = progress.get("current_milestone", "Unknown")
        total_cost = progress.get("total_cost", 0)
        
        print(f"\n📊 ML Portfolio Test Progress:")
        print(f"Current Milestone: {current_milestone}")
        print(f"Total Cost: ${total_cost:.2f}")
        
        milestones = progress.get("milestones", {})
        for milestone_name, milestone_data in milestones.items():
            completed = milestone_data.get("completed_phases", 0)
            total = milestone_data.get("total_phases", 11)
            current_phase = milestone_data.get("current_phase")
            
            status = "✅" if completed == total else "🔄" if current_phase else "⭕"
            print(f"  {status} {milestone_name}: {completed}/{total} phases")
            if current_phase:
                print(f"     Currently: {current_phase}")
    
    def monitor_loop(self, check_interval: int = 30):
        """Main monitoring loop."""
        print("🔍 ML Portfolio Test Monitor Started")
        print(f"Monitoring: {self.project_path}")
        print(f"Check interval: {check_interval} seconds")
        print("Press Ctrl+C to stop monitoring")
        print("=" * 60)
        
        try:
            while True:
                # Get current progress
                progress = self.get_current_progress()
                if not progress:
                    print("⚠️  No progress file found - test may not be running")
                    time.sleep(check_interval)
                    continue
                
                # Get resource usage
                resources = self.get_resource_usage()
                self.resource_samples.append(resources)
                
                # Check for TaskGroup errors
                taskgroup_errors = self.check_for_taskgroup_errors()
                
                # Calculate elapsed time
                elapsed = time.time() - self.start_time
                
                # Print status update
                timestamp = datetime.now().strftime("%H:%M:%S")
                print(f"\n[{timestamp}] Status Update (Running {self.format_duration(elapsed)})")
                
                self.print_progress_summary(progress)
                
                print(f"\n💻 Resource Usage:")
                if "process_memory_mb" in resources:
                    print(f"  Memory: {resources['process_memory_mb']:.1f} MB")
                if "system_memory_percent" in resources:
                    print(f"  System Memory: {resources['system_memory_percent']:.1f}%")
                if "system_cpu_percent" in resources:
                    print(f"  System CPU: {resources['system_cpu_percent']:.1f}%")
                
                print(f"\n⚠️  Stability Metrics:")
                print(f"  TaskGroup Errors (recent): {taskgroup_errors}")
                
                # Check for significant changes
                if self.last_progress:
                    old_cost = self.last_progress.get("total_cost", 0)
                    new_cost = progress.get("total_cost", 0)
                    cost_delta = new_cost - old_cost
                    
                    if cost_delta > 0:
                        print(f"  💰 Cost increased by ${cost_delta:.2f}")
                
                # Resource trend analysis
                if len(self.resource_samples) >= 5:
                    recent_memory = [s.get("process_memory_mb", 0) for s in self.resource_samples[-5:]]
                    memory_trend = recent_memory[-1] - recent_memory[0] if recent_memory else 0
                    
                    if abs(memory_trend) > 10:  # 10MB change
                        direction = "↗️" if memory_trend > 0 else "↘️"
                        print(f"  {direction} Memory trend: {memory_trend:+.1f} MB over last 5 samples")
                
                self.last_progress = progress
                print("=" * 60)
                
                # Wait for next check
                time.sleep(check_interval)
                
        except KeyboardInterrupt:
            print("\n\n🛑 Monitoring stopped by user")
            self.print_final_summary()
        except Exception as e:
            print(f"\n💥 Monitoring error: {e}")
            self.print_final_summary()
    
    def print_final_summary(self):
        """Print final monitoring summary."""
        total_time = time.time() - self.start_time
        
        print(f"\n📈 Final Monitoring Summary:")
        print(f"Total monitoring time: {self.format_duration(total_time)}")
        print(f"Resource samples collected: {len(self.resource_samples)}")
        
        if len(self.resource_samples) >= 2:
            initial_memory = self.resource_samples[0].get("process_memory_mb", 0)
            final_memory = self.resource_samples[-1].get("process_memory_mb", 0)
            memory_delta = final_memory - initial_memory
            
            print(f"Memory change: {memory_delta:+.1f} MB")
            
            if abs(memory_delta) > 50:
                print("⚠️  Significant memory change detected!")
        
        if self.last_progress:
            final_cost = self.last_progress.get("total_cost", 0)
            print(f"Final cost: ${final_cost:.2f}")
            
            milestones = self.last_progress.get("milestones", {})
            completed_milestones = sum(
                1 for m in milestones.values() 
                if m.get("completed_phases", 0) >= m.get("total_phases", 11)
            )
            print(f"Completed milestones: {completed_milestones}/{len(milestones)}")


def main():
    """Main entry point."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Monitor ML Portfolio Test")
    parser.add_argument("--interval", type=int, default=30,
                       help="Check interval in seconds (default: 30)")
    
    args = parser.parse_args()
    
    monitor = MLPortfolioTestMonitor()
    monitor.monitor_loop(args.interval)


if __name__ == "__main__":
    main()