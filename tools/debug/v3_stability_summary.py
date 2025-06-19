#!/usr/bin/env python3
"""
V3 Stability Summary Tool

Generate a quick stability summary of the current V3 system based on:
- TaskGroup error logs
- Resource usage patterns  
- Current ML Portfolio test status
- Overall stability assessment

This provides immediate visibility into V3 stability without running full validation.
"""

import json
import time
import sys
from pathlib import Path
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

class V3StabilitySummary:
    """Generate quick stability summary for V3 system."""
    
    def __init__(self, project_path: str = "example_projects/ml_portfolio_analyzer"):
        self.project_path = Path(project_path)
        self.stability_logs_dir = self.project_path / ".cc_automator" / "stability_logs"
        self.progress_file = self.project_path / ".cc_automator" / "progress.json"
        
    def get_taskgroup_error_summary(self) -> Dict[str, Any]:
        """Analyze TaskGroup errors from stability logs."""
        taskgroup_log = self.stability_logs_dir / "taskgroup_errors.jsonl"
        
        if not taskgroup_log.exists():
            return {"status": "no_taskgroup_logs", "total_errors": 0}
        
        try:
            errors = []
            with open(taskgroup_log) as f:
                for line in f:
                    try:
                        errors.append(json.loads(line.strip()))
                    except json.JSONDecodeError:
                        continue
            
            if not errors:
                return {"status": "no_errors", "total_errors": 0}
            
            # Analyze error patterns
            now = time.time()
            recent_errors = [e for e in errors if now - e["timestamp"] < 3600]  # Last hour
            
            error_types = {}
            severity_counts = {"low": 0, "medium": 0, "high": 0}
            
            for error in errors:
                analysis = error.get("error_analysis", {})
                error_type = analysis.get("specific_type", "unknown")
                severity = analysis.get("severity", "medium")
                
                error_types[error_type] = error_types.get(error_type, 0) + 1
                severity_counts[severity] += 1
            
            return {
                "status": "errors_found",
                "total_errors": len(errors),
                "recent_errors": len(recent_errors),
                "error_types": error_types,
                "severity_distribution": severity_counts,
                "most_common": max(error_types.items(), key=lambda x: x[1])[0] if error_types else None,
                "last_error": max(e["timestamp"] for e in errors),
                "error_rate_per_hour": len(recent_errors) if recent_errors else 0
            }
            
        except Exception as e:
            return {"status": "analysis_error", "error": str(e)}
    
    def get_resource_usage_summary(self) -> Dict[str, Any]:
        """Analyze resource usage from stability logs."""
        resource_log = self.stability_logs_dir / "resource_metrics.jsonl"
        
        if not resource_log.exists():
            return {"status": "no_resource_logs"}
        
        try:
            metrics = []
            with open(resource_log) as f:
                for line in f:
                    try:
                        metrics.append(json.loads(line.strip()))
                    except json.JSONDecodeError:
                        continue
            
            if len(metrics) < 2:
                return {"status": "insufficient_data", "sample_count": len(metrics)}
            
            # Analyze resource trends
            memory_values = [m["process_memory_mb"] for m in metrics if "process_memory_mb" in m]
            fd_values = [m["open_file_descriptors"] for m in metrics if "open_file_descriptors" in m and m["open_file_descriptors"] > 0]
            connection_values = [m["network_connections"] for m in metrics if "network_connections" in m]
            
            if not memory_values:
                return {"status": "no_memory_data"}
            
            initial_memory = memory_values[0]
            current_memory = memory_values[-1]
            max_memory = max(memory_values)
            avg_memory = sum(memory_values) / len(memory_values)
            
            memory_growth = current_memory - initial_memory
            
            # Recent trend (last 20 samples)
            recent_memory = memory_values[-20:] if len(memory_values) >= 20 else memory_values
            recent_trend = recent_memory[-1] - recent_memory[0] if len(recent_memory) > 1 else 0
            
            return {
                "status": "analyzed",
                "sample_count": len(metrics),
                "memory_analysis": {
                    "initial_mb": initial_memory,
                    "current_mb": current_memory,
                    "max_mb": max_memory,
                    "average_mb": avg_memory,
                    "total_growth_mb": memory_growth,
                    "recent_trend_mb": recent_trend,
                    "leak_suspected": memory_growth > 100 or recent_trend > 50
                },
                "file_descriptors": {
                    "max_fds": max(fd_values) if fd_values else 0,
                    "leak_suspected": max(fd_values) > 100 if fd_values else False
                },
                "network_connections": {
                    "max_connections": max(connection_values) if connection_values else 0,
                    "leak_suspected": max(connection_values) > 20 if connection_values else False
                },
                "duration_hours": (metrics[-1]["timestamp"] - metrics[0]["timestamp"]) / 3600
            }
            
        except Exception as e:
            return {"status": "analysis_error", "error": str(e)}
    
    def get_ml_portfolio_status(self) -> Dict[str, Any]:
        """Get current ML Portfolio test status."""
        if not self.progress_file.exists():
            return {"status": "no_test_running"}
        
        try:
            with open(self.progress_file) as f:
                progress = json.load(f)
            
            current_milestone = progress.get("current_milestone", "Unknown")
            total_cost = progress.get("total_cost", 0)
            start_time = progress.get("start_time")
            
            # Count completed milestones
            milestones = progress.get("milestones", {})
            completed_milestones = 0
            current_milestone_progress = None
            
            for milestone_name, milestone_data in milestones.items():
                completed_phases = milestone_data.get("completed_phases", 0)
                total_phases = milestone_data.get("total_phases", 11)
                
                if completed_phases >= total_phases:
                    completed_milestones += 1
                elif milestone_data.get("current_phase"):
                    current_milestone_progress = {
                        "name": milestone_name,
                        "completed_phases": completed_phases,
                        "total_phases": total_phases,
                        "current_phase": milestone_data.get("current_phase"),
                        "progress_percent": (completed_phases / total_phases) * 100
                    }
            
            # Calculate runtime
            runtime_hours = 0
            if start_time:
                try:
                    from datetime import datetime
                    start_dt = datetime.fromisoformat(start_time.replace('Z', '+00:00'))
                    runtime_hours = (datetime.now().astimezone() - start_dt).total_seconds() / 3600
                except:
                    pass
            
            return {
                "status": "test_running",
                "current_milestone": current_milestone,
                "completed_milestones": completed_milestones,
                "total_milestones": len(milestones),
                "current_progress": current_milestone_progress,
                "total_cost": total_cost,
                "runtime_hours": runtime_hours
            }
            
        except Exception as e:
            return {"status": "analysis_error", "error": str(e)}
    
    def assess_overall_stability(self, taskgroup_summary: Dict, resource_summary: Dict, test_status: Dict) -> Dict[str, Any]:
        """Provide overall stability assessment."""
        
        # Calculate stability score (0-100)
        stability_score = 100
        issues = []
        
        # TaskGroup error assessment
        if taskgroup_summary.get("status") == "errors_found":
            total_errors = taskgroup_summary.get("total_errors", 0)
            recent_errors = taskgroup_summary.get("recent_errors", 0)
            
            if total_errors > 50:
                stability_score -= 30
                issues.append(f"High TaskGroup error count: {total_errors} total")
            elif total_errors > 10:
                stability_score -= 15
                issues.append(f"Moderate TaskGroup error count: {total_errors} total")
            
            if recent_errors > 5:
                stability_score -= 20
                issues.append(f"Recent TaskGroup errors: {recent_errors} in last hour")
        
        # Resource leak assessment
        if resource_summary.get("status") == "analyzed":
            memory_analysis = resource_summary.get("memory_analysis", {})
            
            if memory_analysis.get("leak_suspected"):
                stability_score -= 25
                growth = memory_analysis.get("total_growth_mb", 0)
                issues.append(f"Memory leak suspected: {growth:.1f}MB growth")
            
            if resource_summary.get("file_descriptors", {}).get("leak_suspected"):
                stability_score -= 15
                issues.append("File descriptor leak suspected")
            
            if resource_summary.get("network_connections", {}).get("leak_suspected"):
                stability_score -= 15
                issues.append("Network connection leak suspected")
        
        # Test progress assessment
        if test_status.get("status") == "test_running":
            cost = test_status.get("total_cost", 0)
            if cost > 50:  # High cost may indicate inefficiency
                stability_score -= 10
                issues.append(f"High test cost: ${cost:.2f}")
        
        # Determine stability level
        if stability_score >= 90:
            stability_level = "excellent"
        elif stability_score >= 75:
            stability_level = "good"
        elif stability_score >= 60:
            stability_level = "acceptable"
        elif stability_score >= 40:
            stability_level = "concerning"
        else:
            stability_level = "poor"
        
        return {
            "stability_score": max(0, stability_score),
            "stability_level": stability_level,
            "issues": issues,
            "ready_for_v4": stability_score >= 75 and len(issues) == 0,
            "recommendation": self._get_stability_recommendation(stability_level, issues)
        }
    
    def _get_stability_recommendation(self, level: str, issues: List[str]) -> str:
        """Get recommendation based on stability level."""
        if level == "excellent":
            return "V3 is stable and ready for V4 development"
        elif level == "good":
            return "V3 is mostly stable, monitor for issues before V4"
        elif level == "acceptable":
            return "V3 has minor issues, address before V4 development"
        elif level == "concerning":
            return "V3 has significant issues, stability work required"
        else:
            return "V3 is unstable, immediate stability work required"
    
    def generate_summary_report(self) -> Dict[str, Any]:
        """Generate complete stability summary report."""
        
        print("🔍 Analyzing V3 Stability...")
        
        taskgroup_summary = self.get_taskgroup_error_summary()
        resource_summary = self.get_resource_usage_summary()
        test_status = self.get_ml_portfolio_status()
        overall_assessment = self.assess_overall_stability(taskgroup_summary, resource_summary, test_status)
        
        return {
            "timestamp": time.time(),
            "iso_timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "taskgroup_errors": taskgroup_summary,
            "resource_usage": resource_summary,
            "ml_portfolio_test": test_status,
            "overall_stability": overall_assessment
        }
    
    def print_summary_report(self, report: Dict[str, Any]):
        """Print formatted summary report."""
        
        print("\n" + "=" * 70)
        print("V3 STABILITY SUMMARY REPORT")
        print("=" * 70)
        print(f"Generated: {report['iso_timestamp']}")
        
        # Overall Assessment
        overall = report["overall_stability"]
        score = overall["stability_score"]
        level = overall["stability_level"].upper()
        
        print(f"\n🎯 OVERALL STABILITY: {level} ({score}/100)")
        print(f"📋 Ready for V4: {'✅ YES' if overall['ready_for_v4'] else '❌ NO'}")
        print(f"💡 Recommendation: {overall['recommendation']}")
        
        if overall["issues"]:
            print(f"\n⚠️  ISSUES FOUND:")
            for issue in overall["issues"]:
                print(f"   • {issue}")
        
        # TaskGroup Errors
        taskgroup = report["taskgroup_errors"]
        print(f"\n🔧 TASKGROUP ERRORS:")
        
        if taskgroup["status"] == "no_taskgroup_logs":
            print("   📊 No TaskGroup error logs found")
        elif taskgroup["status"] == "no_errors":
            print("   ✅ No TaskGroup errors recorded")
        elif taskgroup["status"] == "errors_found":
            print(f"   📊 Total errors: {taskgroup['total_errors']}")
            print(f"   ⏰ Recent errors (1h): {taskgroup['recent_errors']}")
            print(f"   🔝 Most common: {taskgroup['most_common']}")
            
            if taskgroup["recent_errors"] > 0:
                print(f"   ⚠️  Active error rate: {taskgroup['error_rate_per_hour']}/hour")
        
        # Resource Usage
        resource = report["resource_usage"]
        print(f"\n💻 RESOURCE USAGE:")
        
        if resource["status"] == "no_resource_logs":
            print("   📊 No resource usage logs found")
        elif resource["status"] == "analyzed":
            memory = resource["memory_analysis"]
            print(f"   📊 Monitoring duration: {resource['duration_hours']:.1f} hours")
            print(f"   🧠 Memory: {memory['current_mb']:.1f}MB (growth: {memory['total_growth_mb']:+.1f}MB)")
            print(f"   📁 Max file descriptors: {resource['file_descriptors']['max_fds']}")
            print(f"   🌐 Max connections: {resource['network_connections']['max_connections']}")
            
            if memory["leak_suspected"]:
                print("   ⚠️  Memory leak suspected!")
            if resource["file_descriptors"]["leak_suspected"]:
                print("   ⚠️  File descriptor leak suspected!")
            if resource["network_connections"]["leak_suspected"]:
                print("   ⚠️  Network connection leak suspected!")
        
        # ML Portfolio Test
        test = report["ml_portfolio_test"]
        print(f"\n🧪 ML PORTFOLIO TEST:")
        
        if test["status"] == "no_test_running":
            print("   📊 No test currently running")
        elif test["status"] == "test_running":
            print(f"   📊 Status: {test['current_milestone']}")
            print(f"   ✅ Completed milestones: {test['completed_milestones']}/{test['total_milestones']}")
            print(f"   💰 Cost: ${test['total_cost']:.2f}")
            print(f"   ⏱️  Runtime: {test['runtime_hours']:.1f} hours")
            
            if test["current_progress"]:
                progress = test["current_progress"]
                print(f"   🔄 Current: {progress['name']} - {progress['completed_phases']}/{progress['total_phases']} phases ({progress['progress_percent']:.1f}%)")
        
        print("\n" + "=" * 70)


def main():
    """Main entry point."""
    import argparse
    
    parser = argparse.ArgumentParser(description="V3 Stability Summary")
    parser.add_argument("--project", default="example_projects/ml_portfolio_analyzer",
                       help="Project path to analyze")
    parser.add_argument("--json", action="store_true",
                       help="Output raw JSON instead of formatted report")
    
    args = parser.parse_args()
    
    try:
        summary = V3StabilitySummary(args.project)
        report = summary.generate_summary_report()
        
        if args.json:
            print(json.dumps(report, indent=2))
        else:
            summary.print_summary_report(report)
            
    except Exception as e:
        print(f"❌ Failed to generate stability summary: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()