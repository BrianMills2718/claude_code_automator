"""
Recovery Effectiveness Analyzer for CC_AUTOMATOR4 Phase 3
Measures and analyzes the effectiveness of recovery mechanisms
"""

import time
import json
import statistics
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass, field
from enum import Enum
import logging

logger = logging.getLogger(__name__)

class RecoveryMetric(Enum):
    """Types of recovery effectiveness metrics"""
    SUCCESS_RATE = "success_rate"
    RECOVERY_TIME = "recovery_time"
    RESOURCE_CLEANUP = "resource_cleanup"
    ERROR_PREVENTION = "error_prevention"
    USER_EXPERIENCE = "user_experience"
    SYSTEM_STABILITY = "system_stability"

@dataclass
class RecoveryPerformanceData:
    """Performance data for a recovery mechanism"""
    mechanism_name: str
    test_runs: int
    successful_recoveries: int
    failed_recoveries: int
    recovery_times: List[float]
    resource_leaks_detected: int
    errors_prevented: int
    user_impact_scores: List[float]  # 0-10 scale
    stability_metrics: Dict[str, Any] = field(default_factory=dict)

@dataclass
class RecoveryEffectivenessReport:
    """Comprehensive effectiveness analysis report"""
    overall_effectiveness_score: float  # 0-100 scale
    mechanism_rankings: List[Tuple[str, float]]  # (name, score) pairs
    performance_summary: Dict[str, RecoveryPerformanceData]
    recommendations: List[str]
    improvement_areas: List[str]
    verified_capabilities: List[str]

class RecoveryEffectivenessAnalyzer:
    """Analyzes the effectiveness of recovery mechanisms"""
    
    def __init__(self, working_dir: Path):
        self.working_dir = working_dir
        self.performance_data: Dict[str, RecoveryPerformanceData] = {}
        
    def record_recovery_attempt(self, 
                               mechanism_name: str,
                               success: bool,
                               recovery_time: float,
                               resource_leaks: int = 0,
                               errors_prevented: int = 0,
                               user_impact_score: float = 5.0):
        """Record a recovery attempt for analysis"""
        
        if mechanism_name not in self.performance_data:
            self.performance_data[mechanism_name] = RecoveryPerformanceData(
                mechanism_name=mechanism_name,
                test_runs=0,
                successful_recoveries=0,
                failed_recoveries=0,
                recovery_times=[],
                resource_leaks_detected=0,
                errors_prevented=0,
                user_impact_scores=[]
            )
        
        data = self.performance_data[mechanism_name]
        data.test_runs += 1
        
        if success:
            data.successful_recoveries += 1
        else:
            data.failed_recoveries += 1
            
        data.recovery_times.append(recovery_time)
        data.resource_leaks_detected += resource_leaks
        data.errors_prevented += errors_prevented
        data.user_impact_scores.append(user_impact_score)
        
        logger.debug(f"Recorded recovery attempt: {mechanism_name} - {'SUCCESS' if success else 'FAILED'} ({recovery_time:.2f}s)")
    
    def calculate_mechanism_effectiveness(self, data: RecoveryPerformanceData) -> float:
        """Calculate effectiveness score for a single mechanism (0-100)"""
        
        if data.test_runs == 0:
            return 0.0
        
        # Success rate component (0-40 points)
        success_rate = data.successful_recoveries / data.test_runs
        success_score = success_rate * 40
        
        # Recovery time component (0-20 points) - faster is better
        if data.recovery_times:
            avg_recovery_time = statistics.mean(data.recovery_times)
            # Score decreases as recovery time increases (5s = max score, 30s = min score)
            time_score = max(0, 20 * (1 - (avg_recovery_time - 5) / 25))
        else:
            time_score = 0
        
        # Resource cleanup component (0-15 points)
        if data.test_runs > 0:
            leak_rate = data.resource_leaks_detected / data.test_runs
            cleanup_score = max(0, 15 * (1 - leak_rate))
        else:
            cleanup_score = 0
        
        # Error prevention component (0-15 points)
        prevention_score = min(15, data.errors_prevented * 3)
        
        # User experience component (0-10 points)
        if data.user_impact_scores:
            avg_user_score = statistics.mean(data.user_impact_scores)
            user_score = (avg_user_score / 10) * 10
        else:
            user_score = 5
        
        total_score = success_score + time_score + cleanup_score + prevention_score + user_score
        
        return min(100.0, max(0.0, total_score))
    
    def analyze_recovery_patterns(self) -> Dict[str, Any]:
        """Analyze patterns in recovery performance"""
        
        patterns = {
            "total_mechanisms_tested": len(self.performance_data),
            "total_recovery_attempts": sum(data.test_runs for data in self.performance_data.values()),
            "overall_success_rate": 0.0,
            "fastest_recovery_mechanism": None,
            "most_reliable_mechanism": None,
            "best_user_experience": None,
            "performance_trends": {}
        }
        
        if not self.performance_data:
            return patterns
        
        # Calculate overall success rate
        total_attempts = sum(data.test_runs for data in self.performance_data.values())
        total_successes = sum(data.successful_recoveries for data in self.performance_data.values())
        
        if total_attempts > 0:
            patterns["overall_success_rate"] = total_successes / total_attempts
        
        # Find best performing mechanisms
        mechanism_scores = []
        for name, data in self.performance_data.items():
            if data.test_runs > 0:
                effectiveness = self.calculate_mechanism_effectiveness(data)
                mechanism_scores.append((name, effectiveness, data))
        
        if mechanism_scores:
            # Sort by effectiveness score
            mechanism_scores.sort(key=lambda x: x[1], reverse=True)
            
            # Best overall
            patterns["most_reliable_mechanism"] = mechanism_scores[0][0]
            
            # Fastest recovery
            fastest_mechanism = None
            fastest_time = float('inf')
            
            for name, score, data in mechanism_scores:
                if data.recovery_times:
                    avg_time = statistics.mean(data.recovery_times)
                    if avg_time < fastest_time:
                        fastest_time = avg_time
                        fastest_mechanism = name
            
            patterns["fastest_recovery_mechanism"] = fastest_mechanism
            
            # Best user experience
            best_ux_mechanism = None
            best_ux_score = 0
            
            for name, score, data in mechanism_scores:
                if data.user_impact_scores:
                    avg_ux = statistics.mean(data.user_impact_scores)
                    if avg_ux > best_ux_score:
                        best_ux_score = avg_ux
                        best_ux_mechanism = name
            
            patterns["best_user_experience"] = best_ux_mechanism
        
        return patterns
    
    def generate_recommendations(self, patterns: Dict[str, Any]) -> List[str]:
        """Generate recommendations for improving recovery effectiveness"""
        
        recommendations = []
        
        # Overall success rate recommendations
        overall_success = patterns.get("overall_success_rate", 0)
        if overall_success < 0.7:
            recommendations.append(
                f"Overall recovery success rate is {overall_success:.1%}. "
                "Consider implementing additional fallback mechanisms."
            )
        elif overall_success > 0.9:
            recommendations.append(
                f"Excellent overall recovery success rate of {overall_success:.1%}. "
                "Focus on optimizing recovery times and user experience."
            )
        
        # Individual mechanism recommendations
        for name, data in self.performance_data.items():
            effectiveness = self.calculate_mechanism_effectiveness(data)
            
            if effectiveness < 50:
                recommendations.append(
                    f"{name}: Low effectiveness score ({effectiveness:.1f}/100). "
                    "Consider redesigning or replacing this recovery mechanism."
                )
            elif effectiveness > 80:
                recommendations.append(
                    f"{name}: High effectiveness score ({effectiveness:.1f}/100). "
                    "Consider using this as a model for other recovery mechanisms."
                )
            
            # Recovery time recommendations
            if data.recovery_times:
                avg_time = statistics.mean(data.recovery_times)
                if avg_time > 10:
                    recommendations.append(
                        f"{name}: Average recovery time is {avg_time:.1f}s. "
                        "Consider optimizing for faster recovery."
                    )
            
            # Resource leak recommendations  
            if data.resource_leaks_detected > 0:
                leak_rate = data.resource_leaks_detected / data.test_runs
                recommendations.append(
                    f"{name}: Resource leaks detected in {leak_rate:.1%} of cases. "
                    "Improve resource cleanup mechanisms."
                )
        
        return recommendations
    
    def identify_improvement_areas(self, patterns: Dict[str, Any]) -> List[str]:
        """Identify specific areas for improvement"""
        
        improvement_areas = []
        
        # Check for missing recovery mechanisms
        tested_mechanisms = set(self.performance_data.keys())
        expected_mechanisms = {
            "JSON Repair Recovery",
            "Session Cleanup Recovery", 
            "TaskGroup Recovery",
            "Network Timeout Recovery",
            "Interactive Program Recovery",
            "CLI Fallback Recovery",
            "Memory Exhaustion Recovery",
            "Process Orphan Recovery"
        }
        
        missing_mechanisms = expected_mechanisms - tested_mechanisms
        if missing_mechanisms:
            improvement_areas.append(
                f"Missing recovery mechanisms: {', '.join(missing_mechanisms)}"
            )
        
        # Check for low-performing mechanisms
        low_performers = []
        for name, data in self.performance_data.items():
            effectiveness = self.calculate_mechanism_effectiveness(data)
            if effectiveness < 60:
                low_performers.append(name)
        
        if low_performers:
            improvement_areas.append(
                f"Low-performing mechanisms needing improvement: {', '.join(low_performers)}"
            )
        
        # Check for slow recovery times
        slow_mechanisms = []
        for name, data in self.performance_data.items():
            if data.recovery_times:
                avg_time = statistics.mean(data.recovery_times)
                if avg_time > 15:
                    slow_mechanisms.append(f"{name} ({avg_time:.1f}s)")
        
        if slow_mechanisms:
            improvement_areas.append(
                f"Slow recovery mechanisms: {', '.join(slow_mechanisms)}"
            )
        
        # Check for resource management issues
        leaky_mechanisms = []
        for name, data in self.performance_data.items():
            if data.resource_leaks_detected > 0:
                leak_rate = data.resource_leaks_detected / data.test_runs
                if leak_rate > 0.1:  # More than 10% leak rate
                    leaky_mechanisms.append(f"{name} ({leak_rate:.1%} leak rate)")
        
        if leaky_mechanisms:
            improvement_areas.append(
                f"Resource leak issues: {', '.join(leaky_mechanisms)}"
            )
        
        return improvement_areas
    
    def identify_verified_capabilities(self) -> List[str]:
        """Identify recovery capabilities that are working well"""
        
        verified_capabilities = []
        
        for name, data in self.performance_data.items():
            effectiveness = self.calculate_mechanism_effectiveness(data)
            success_rate = data.successful_recoveries / data.test_runs if data.test_runs > 0 else 0
            
            if effectiveness >= 70 and success_rate >= 0.8:
                capabilities = []
                
                # Recovery success
                capabilities.append(f"reliable recovery ({success_rate:.1%} success rate)")
                
                # Fast recovery
                if data.recovery_times:
                    avg_time = statistics.mean(data.recovery_times)
                    if avg_time <= 5:
                        capabilities.append(f"fast recovery ({avg_time:.1f}s average)")
                
                # Good resource management
                if data.resource_leaks_detected == 0:
                    capabilities.append("clean resource management")
                
                # Error prevention
                if data.errors_prevented > 0:
                    capabilities.append(f"error prevention ({data.errors_prevented} errors prevented)")
                
                # Good user experience
                if data.user_impact_scores:
                    avg_ux = statistics.mean(data.user_impact_scores)
                    if avg_ux >= 7:
                        capabilities.append(f"good user experience ({avg_ux:.1f}/10)")
                
                if capabilities:
                    verified_capabilities.append(f"{name}: {', '.join(capabilities)}")
        
        return verified_capabilities
    
    def generate_effectiveness_report(self) -> RecoveryEffectivenessReport:
        """Generate comprehensive effectiveness analysis report"""
        
        # Calculate individual mechanism scores
        mechanism_rankings = []
        for name, data in self.performance_data.items():
            effectiveness = self.calculate_mechanism_effectiveness(data)
            mechanism_rankings.append((name, effectiveness))
        
        # Sort by effectiveness score
        mechanism_rankings.sort(key=lambda x: x[1], reverse=True)
        
        # Calculate overall effectiveness score
        if mechanism_rankings:
            overall_score = statistics.mean([score for _, score in mechanism_rankings])
        else:
            overall_score = 0.0
        
        # Analyze patterns
        patterns = self.analyze_recovery_patterns()
        
        # Generate recommendations and improvements
        recommendations = self.generate_recommendations(patterns)
        improvement_areas = self.identify_improvement_areas(patterns)
        verified_capabilities = self.identify_verified_capabilities()
        
        return RecoveryEffectivenessReport(
            overall_effectiveness_score=overall_score,
            mechanism_rankings=mechanism_rankings,
            performance_summary=self.performance_data.copy(),
            recommendations=recommendations,
            improvement_areas=improvement_areas,
            verified_capabilities=verified_capabilities
        )
    
    def export_effectiveness_data(self, output_path: Path):
        """Export effectiveness data for further analysis"""
        
        export_data = {
            "timestamp": time.time(),
            "performance_data": {},
            "analysis_patterns": self.analyze_recovery_patterns()
        }
        
        # Convert performance data to JSON-serializable format
        for name, data in self.performance_data.items():
            export_data["performance_data"][name] = {
                "mechanism_name": data.mechanism_name,
                "test_runs": data.test_runs,
                "successful_recoveries": data.successful_recoveries,
                "failed_recoveries": data.failed_recoveries,
                "recovery_times": data.recovery_times,
                "resource_leaks_detected": data.resource_leaks_detected,
                "errors_prevented": data.errors_prevented,
                "user_impact_scores": data.user_impact_scores,
                "effectiveness_score": self.calculate_mechanism_effectiveness(data),
                "success_rate": data.successful_recoveries / data.test_runs if data.test_runs > 0 else 0,
                "average_recovery_time": statistics.mean(data.recovery_times) if data.recovery_times else 0
            }
        
        with open(output_path, 'w') as f:
            json.dump(export_data, f, indent=2)
        
        logger.info(f"📊 Recovery effectiveness data exported to: {output_path}")
    
    def generate_effectiveness_report_text(self, report: RecoveryEffectivenessReport) -> str:
        """Generate human-readable effectiveness report"""
        
        lines = [
            "# Recovery Effectiveness Analysis Report",
            "",
            f"**Overall Effectiveness Score**: {report.overall_effectiveness_score:.1f}/100",
            "",
            f"**Mechanisms Tested**: {len(report.mechanism_rankings)}",
            f"**Total Recovery Attempts**: {sum(data.test_runs for data in report.performance_summary.values())}",
            ""
        ]
        
        # Mechanism rankings
        if report.mechanism_rankings:
            lines.extend([
                "## 📊 Recovery Mechanism Rankings",
                ""
            ])
            
            for i, (name, score) in enumerate(report.mechanism_rankings, 1):
                status = "🥇" if i == 1 else "🥈" if i == 2 else "🥉" if i == 3 else "📍"
                lines.append(f"{i}. {status} **{name}**: {score:.1f}/100")
            
            lines.append("")
        
        # Verified capabilities
        if report.verified_capabilities:
            lines.extend([
                "## ✅ Verified Recovery Capabilities",
                ""
            ])
            
            for capability in report.verified_capabilities:
                lines.append(f"- {capability}")
            
            lines.append("")
        
        # Recommendations
        if report.recommendations:
            lines.extend([
                "## 💡 Recommendations",
                ""
            ])
            
            for recommendation in report.recommendations:
                lines.append(f"- {recommendation}")
            
            lines.append("")
        
        # Improvement areas
        if report.improvement_areas:
            lines.extend([
                "## 🔧 Areas for Improvement",
                ""
            ])
            
            for area in report.improvement_areas:
                lines.append(f"- {area}")
            
            lines.append("")
        
        # Detailed performance data
        lines.extend([
            "## 📈 Detailed Performance Data",
            ""
        ])
        
        for name, data in report.performance_summary.items():
            success_rate = data.successful_recoveries / data.test_runs if data.test_runs > 0 else 0
            avg_time = statistics.mean(data.recovery_times) if data.recovery_times else 0
            effectiveness = self.calculate_mechanism_effectiveness(data)
            
            lines.extend([
                f"### {name}",
                f"- **Effectiveness Score**: {effectiveness:.1f}/100",
                f"- **Success Rate**: {success_rate:.1%} ({data.successful_recoveries}/{data.test_runs})",
                f"- **Average Recovery Time**: {avg_time:.2f}s",
                f"- **Resource Leaks**: {data.resource_leaks_detected}",
                f"- **Errors Prevented**: {data.errors_prevented}",
                ""
            ])
        
        return "\n".join(lines)