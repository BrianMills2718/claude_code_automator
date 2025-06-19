#!/usr/bin/env python3
"""
Resume State Validator for CC_AUTOMATOR V3
Provides comprehensive validation for resume operations to ensure system stability
"""

import json
from pathlib import Path
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass
from enum import Enum


class ValidationLevel(Enum):
    """Validation strictness levels"""
    BASIC = "basic"      # Essential checks only
    STANDARD = "standard"  # Recommended checks
    STRICT = "strict"    # All possible checks


@dataclass
class ValidationResult:
    """Result of a validation check"""
    is_valid: bool
    message: str
    severity: str = "info"  # info, warning, error
    recommendation: Optional[str] = None


class ResumeStateValidator:
    """Validates project state before resuming execution"""
    
    def __init__(self, project_dir: Path, validation_level: ValidationLevel = ValidationLevel.STANDARD):
        self.project_dir = Path(project_dir)
        self.validation_level = validation_level
        self.cc_automator_dir = self.project_dir / ".cc_automator"
        
    def validate_resume_state(self) -> Tuple[bool, List[ValidationResult]]:
        """
        Comprehensive validation of project state for resume operations.
        Returns: (can_resume, validation_results)
        """
        results = []
        
        # Essential validations (always run)
        results.extend(self._validate_project_structure())
        results.extend(self._validate_progress_consistency())
        results.extend(self._validate_milestone_integrity())
        
        # Standard validations
        if self.validation_level in [ValidationLevel.STANDARD, ValidationLevel.STRICT]:
            results.extend(self._validate_session_state())
            results.extend(self._validate_evidence_files())
            results.extend(self._validate_time_consistency())
            
        # Strict validations  
        if self.validation_level == ValidationLevel.STRICT:
            results.extend(self._validate_file_system_state())
            results.extend(self._validate_dependency_consistency())
            
        # Determine if we can resume based on errors
        errors = [r for r in results if r.severity == "error"]
        can_resume = len(errors) == 0
        
        return can_resume, results
        
    def _validate_project_structure(self) -> List[ValidationResult]:
        """Validate essential project structure exists"""
        results = []
        
        # Check .cc_automator directory
        if not self.cc_automator_dir.exists():
            results.append(ValidationResult(
                is_valid=False,
                message="Missing .cc_automator directory",
                severity="error",
                recommendation="Run a fresh execution instead of resume"
            ))
            return results
            
        # Check essential files
        essential_files = {
            "progress.json": "Progress tracking data",
            "sessions.json": "Session management data",
            "milestones": "Milestone directory"
        }
        
        for file_name, description in essential_files.items():
            file_path = self.cc_automator_dir / file_name
            if not file_path.exists():
                results.append(ValidationResult(
                    is_valid=False,
                    message=f"Missing {description} ({file_name})",
                    severity="error",
                    recommendation=f"Regenerate {file_name} or start fresh"
                ))
            else:
                results.append(ValidationResult(
                    is_valid=True,
                    message=f"Found {description}",
                    severity="info"
                ))
                
        return results
        
    def _validate_progress_consistency(self) -> List[ValidationResult]:
        """Validate progress data consistency"""
        results = []
        
        progress_file = self.cc_automator_dir / "progress.json"
        if not progress_file.exists():
            return [ValidationResult(
                is_valid=False,
                message="Progress file missing",
                severity="error"
            )]
            
        try:
            with open(progress_file) as f:
                progress_data = json.load(f)
                
            # Validate required fields
            required_fields = ["project_name", "start_time", "milestones"]
            for field in required_fields:
                if field not in progress_data:
                    results.append(ValidationResult(
                        is_valid=False,
                        message=f"Progress data missing field: {field}",
                        severity="error",
                        recommendation="Regenerate progress data"
                    ))
                    
            # Validate milestone data structure
            milestones = progress_data.get("milestones", {})
            for milestone_name, milestone_data in milestones.items():
                required_milestone_fields = ["name", "total_phases", "completed_phases"]
                for field in required_milestone_fields:
                    if field not in milestone_data:
                        results.append(ValidationResult(
                            is_valid=False,
                            message=f"Milestone {milestone_name} missing field: {field}",
                            severity="warning",
                            recommendation="Regenerate milestone progress"
                        ))
                        
                # Validate phase counts
                total = milestone_data.get("total_phases", 0)
                completed = milestone_data.get("completed_phases", 0)
                if completed > total:
                    results.append(ValidationResult(
                        is_valid=False,
                        message=f"Milestone {milestone_name}: completed_phases ({completed}) > total_phases ({total})",
                        severity="error",
                        recommendation="Fix progress data corruption"
                    ))
                    
            if not results or all(r.is_valid for r in results):
                results.append(ValidationResult(
                    is_valid=True,
                    message="Progress data structure is valid",
                    severity="info"
                ))
                
        except json.JSONDecodeError as e:
            results.append(ValidationResult(
                is_valid=False,
                message=f"Progress file corrupted: {e}",
                severity="error",
                recommendation="Delete progress.json and start fresh"
            ))
        except Exception as e:
            results.append(ValidationResult(
                is_valid=False,
                message=f"Error reading progress: {e}",
                severity="error"
            ))
            
        return results
        
    def _validate_milestone_integrity(self) -> List[ValidationResult]:
        """Validate milestone directory structure and evidence files"""
        results = []
        
        milestones_dir = self.cc_automator_dir / "milestones"
        if not milestones_dir.exists():
            return [ValidationResult(
                is_valid=False,
                message="Milestones directory missing",
                severity="error",
                recommendation="Start fresh execution"
            )]
            
        # Check milestone directories exist
        milestone_dirs = [d for d in milestones_dir.iterdir() if d.is_dir()]
        
        if not milestone_dirs:
            results.append(ValidationResult(
                is_valid=False,
                message="No milestone directories found",
                severity="warning",
                recommendation="May be starting from beginning"
            ))
            return results
            
        # Validate each milestone directory
        for milestone_dir in milestone_dirs:
            milestone_name = milestone_dir.name
            
            # Check for evidence files
            evidence_files = list(milestone_dir.glob("*.md"))
            if evidence_files:
                results.append(ValidationResult(
                    is_valid=True,
                    message=f"Found {len(evidence_files)} evidence files in {milestone_name}",
                    severity="info"
                ))
            else:
                results.append(ValidationResult(
                    is_valid=False,
                    message=f"No evidence files in {milestone_name}",
                    severity="warning",
                    recommendation="May need to repeat milestone phases"
                ))
                
        return results
        
    def _validate_session_state(self) -> List[ValidationResult]:
        """Validate session management state"""
        results = []
        
        sessions_file = self.cc_automator_dir / "sessions.json"
        if not sessions_file.exists():
            return [ValidationResult(
                is_valid=False,
                message="Sessions file missing",
                severity="warning",
                recommendation="Session tracking will restart"
            )]
            
        try:
            with open(sessions_file) as f:
                sessions_data = json.load(f)
                
            session_count = len(sessions_data)
            if session_count > 0:
                results.append(ValidationResult(
                    is_valid=True,
                    message=f"Found {session_count} tracked sessions",
                    severity="info"
                ))
                
                # Check for recent sessions
                recent_count = 0
                cutoff_time = datetime.now() - timedelta(hours=24)
                
                for phase, session_info in sessions_data.items():
                    timestamp_str = session_info.get("timestamp")
                    if timestamp_str:
                        try:
                            session_time = datetime.fromisoformat(timestamp_str)
                            if session_time > cutoff_time:
                                recent_count += 1
                        except ValueError:
                            pass
                            
                if recent_count > 0:
                    results.append(ValidationResult(
                        is_valid=True,
                        message=f"Found {recent_count} recent sessions (within 24h)",
                        severity="info"
                    ))
                else:
                    results.append(ValidationResult(
                        is_valid=True,
                        message="No recent sessions found",
                        severity="warning",
                        recommendation="Previous sessions may be stale"
                    ))
            else:
                results.append(ValidationResult(
                    is_valid=True,
                    message="No sessions tracked yet",
                    severity="info"
                ))
                
        except json.JSONDecodeError:
            results.append(ValidationResult(
                is_valid=False,
                message="Sessions file corrupted",
                severity="warning",
                recommendation="Delete sessions.json - will restart session tracking"
            ))
        except Exception as e:
            results.append(ValidationResult(
                is_valid=False,
                message=f"Error reading sessions: {e}",
                severity="warning"
            ))
            
        return results
        
    def _validate_evidence_files(self) -> List[ValidationResult]:
        """Validate evidence files are not corrupted"""
        results = []
        
        milestones_dir = self.cc_automator_dir / "milestones"
        if not milestones_dir.exists():
            return []
            
        evidence_files = list(milestones_dir.glob("*/*.md"))
        
        corrupted_files = []
        empty_files = []
        valid_files = []
        
        for evidence_file in evidence_files:
            try:
                content = evidence_file.read_text()
                if not content.strip():
                    empty_files.append(evidence_file.name)
                elif len(content) < 10:  # Suspiciously short
                    corrupted_files.append(evidence_file.name)
                else:
                    valid_files.append(evidence_file.name)
            except Exception:
                corrupted_files.append(evidence_file.name)
                
        if valid_files:
            results.append(ValidationResult(
                is_valid=True,
                message=f"Found {len(valid_files)} valid evidence files",
                severity="info"
            ))
            
        if empty_files:
            results.append(ValidationResult(
                is_valid=False,
                message=f"Found {len(empty_files)} empty evidence files",
                severity="warning",
                recommendation="May need to regenerate affected phases"
            ))
            
        if corrupted_files:
            results.append(ValidationResult(
                is_valid=False,
                message=f"Found {len(corrupted_files)} corrupted evidence files",
                severity="error",
                recommendation="Regenerate affected phases"
            ))
            
        return results
        
    def _validate_time_consistency(self) -> List[ValidationResult]:
        """Validate timestamp consistency"""
        results = []
        
        progress_file = self.cc_automator_dir / "progress.json"
        if not progress_file.exists():
            return []
            
        try:
            with open(progress_file) as f:
                progress_data = json.load(f)
                
            start_time_str = progress_data.get("start_time")
            if start_time_str:
                try:
                    start_time = datetime.fromisoformat(start_time_str)
                    now = datetime.now()
                    
                    # Check for reasonable time bounds
                    if start_time > now:
                        results.append(ValidationResult(
                            is_valid=False,
                            message="Start time is in the future",
                            severity="error",
                            recommendation="Fix system clock or regenerate progress"
                        ))
                    elif (now - start_time).days > 30:
                        results.append(ValidationResult(
                            is_valid=False,
                            message=f"Start time is {(now - start_time).days} days ago",
                            severity="warning",
                            recommendation="Consider starting fresh for very old projects"
                        ))
                    else:
                        results.append(ValidationResult(
                            is_valid=True,
                            message=f"Start time is reasonable ({(now - start_time).days} days ago)",
                            severity="info"
                        ))
                except ValueError:
                    results.append(ValidationResult(
                        is_valid=False,
                        message="Invalid start time format",
                        severity="warning",
                        recommendation="Regenerate progress data"
                    ))
        except Exception:
            pass  # Already handled by progress validation
            
        return results
        
    def _validate_file_system_state(self) -> List[ValidationResult]:
        """Validate file system state (strict mode only)"""
        results = []
        
        # Check for common problematic files
        problematic_patterns = [
            "*.tmp",
            "*.lock",
            ".*.swp",
            "core.*"
        ]
        
        found_issues = []
        for pattern in problematic_patterns:
            matches = list(self.project_dir.glob(pattern))
            if matches:
                found_issues.extend([m.name for m in matches])
                
        if found_issues:
            results.append(ValidationResult(
                is_valid=False,
                message=f"Found problematic files: {', '.join(found_issues[:3])}{'...' if len(found_issues) > 3 else ''}",
                severity="warning",
                recommendation="Clean up temporary files before resume"
            ))
        else:
            results.append(ValidationResult(
                is_valid=True,
                message="No problematic files detected",
                severity="info"
            ))
            
        return results
        
    def _validate_dependency_consistency(self) -> List[ValidationResult]:
        """Validate dependency files haven't changed (strict mode only)"""
        results = []
        
        # Check common dependency files
        dependency_files = [
            "requirements.txt",
            "package.json", 
            "Cargo.toml",
            "go.mod"
        ]
        
        changed_deps = []
        for dep_file in dependency_files:
            dep_path = self.project_dir / dep_file
            if dep_path.exists():
                # Simple check: if modified in last hour, flag as potentially changed
                import os
                stat_info = os.stat(dep_path)
                modified_time = datetime.fromtimestamp(stat_info.st_mtime)
                if (datetime.now() - modified_time).total_seconds() < 3600:
                    changed_deps.append(dep_file)
                    
        if changed_deps:
            results.append(ValidationResult(
                is_valid=False,
                message=f"Recently modified dependency files: {', '.join(changed_deps)}",
                severity="warning",
                recommendation="Verify dependencies haven't broken existing implementation"
            ))
        else:
            results.append(ValidationResult(
                is_valid=True,
                message="Dependency files appear stable",
                severity="info"
            ))
            
        return results
        
    def generate_resume_report(self, results: List[ValidationResult]) -> str:
        """Generate a detailed resume validation report"""
        report = []
        report.append("# Resume State Validation Report")
        report.append(f"\n**Project**: {self.project_dir.name}")
        report.append(f"**Validation Level**: {self.validation_level.value.upper()}")
        report.append(f"**Timestamp**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        
        # Summary
        errors = [r for r in results if r.severity == "error"]
        warnings = [r for r in results if r.severity == "warning"]
        info = [r for r in results if r.severity == "info"]
        
        can_resume = len(errors) == 0
        status = "✅ CAN RESUME" if can_resume else "❌ CANNOT RESUME"
        
        report.append(f"\n## Status: {status}")
        report.append(f"- **Errors**: {len(errors)} (blocking)")
        report.append(f"- **Warnings**: {len(warnings)} (non-blocking)")
        report.append(f"- **Info**: {len(info)} (informational)")
        
        # Details by severity
        for severity_name, severity_results in [("Errors", errors), ("Warnings", warnings), ("Info", info)]:
            if severity_results:
                report.append(f"\n## {severity_name}")
                for result in severity_results:
                    icon = "❌" if result.severity == "error" else "⚠️" if result.severity == "warning" else "ℹ️"
                    report.append(f"\n{icon} **{result.message}**")
                    if result.recommendation:
                        report.append(f"   - *Recommendation*: {result.recommendation}")
                        
        return "\n".join(report)


def validate_project_for_resume(project_dir: Path, 
                               validation_level: ValidationLevel = ValidationLevel.STANDARD,
                               save_report: bool = True) -> Tuple[bool, str]:
    """
    Convenience function to validate a project for resume.
    Returns: (can_resume, report_text)
    """
    validator = ResumeStateValidator(project_dir, validation_level)
    can_resume, results = validator.validate_resume_state()
    report = validator.generate_resume_report(results)
    
    if save_report:
        report_file = project_dir / ".cc_automator" / "resume_validation.md"
        report_file.parent.mkdir(parents=True, exist_ok=True)
        report_file.write_text(report)
        
    return can_resume, report


if __name__ == "__main__":
    # Example usage
    import sys
    
    project_path = Path(sys.argv[1]) if len(sys.argv) > 1 else Path(".")
    can_resume, report = validate_project_for_resume(project_path, ValidationLevel.STANDARD)
    
    print(report)
    print(f"\n{'='*60}")
    print(f"RESUME STATUS: {'✅ SAFE TO RESUME' if can_resume else '❌ DO NOT RESUME'}")