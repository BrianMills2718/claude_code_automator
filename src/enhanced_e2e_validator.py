"""
Enhanced E2E Validator that includes user journey testing
"""

import subprocess
import json
from pathlib import Path
from typing import Dict, List, Tuple, Optional
import logging
try:
    from .user_journey_validator import UserJourneyValidator, JourneyResult
except ImportError:
    from user_journey_validator import UserJourneyValidator, JourneyResult

logger = logging.getLogger(__name__)

class EnhancedE2EValidator:
    """Enhanced E2E validation that includes both basic tests and user journeys"""
    
    def __init__(self, working_dir: Path, milestone_num: int, verbose: bool = False):
        self.working_dir = working_dir
        self.milestone_num = milestone_num
        self.verbose = verbose
        self.milestone_dir = working_dir / ".cc_automator/milestones" / f"milestone_{milestone_num}"
        
    def validate_basic_requirements(self) -> Tuple[bool, List[str]]:
        """Validate basic E2E requirements (evidence log, main.py exists)"""
        errors = []
        
        # Check evidence log
        e2e_files = list(self.milestone_dir.glob("*e2e*.log")) + list(self.milestone_dir.glob("*evidence*.log"))
        if not e2e_files:
            errors.append("No E2E evidence log found")
            return False, errors
            
        # Check main.py exists
        main_py = self.working_dir / "main.py"
        if not main_py.exists():
            errors.append("main.py not found")
            return False, errors
            
        return True, errors
    
    def validate_main_py_execution(self) -> Tuple[bool, List[str]]:
        """Validate that main.py runs without errors"""
        errors = []
        main_py = self.working_dir / "main.py"
        
        # Check if interactive
        content = main_py.read_text()
        is_interactive = 'input(' in content or 'raw_input(' in content
        
        try:
            if is_interactive:
                # Try common exit patterns
                exit_patterns = ["q\n", "exit\n", "8\n", "0\n", "\n"]
                success = False
                
                for test_input in exit_patterns:
                    try:
                        result = subprocess.run(
                            ["python", "main.py"],
                            input=test_input,
                            capture_output=True,
                            text=True,
                            cwd=str(self.working_dir),
                            timeout=10
                        )
                        if result.returncode == 0:
                            success = True
                            break
                    except subprocess.TimeoutExpired:
                        continue
                        
                if not success:
                    errors.append("Interactive main.py doesn't exit cleanly")
                    return False, errors
                    
            else:
                # Non-interactive
                result = subprocess.run(
                    ["python", "main.py"],
                    capture_output=True,
                    text=True,
                    cwd=str(self.working_dir),
                    timeout=10
                )
                if result.returncode != 0:
                    errors.append(f"main.py exited with code {result.returncode}")
                    return False, errors
                    
        except Exception as e:
            errors.append(f"Error running main.py: {str(e)}")
            return False, errors
            
        return True, errors
    
    def validate_user_journeys(self) -> Tuple[bool, List[JourneyResult]]:
        """Validate user journeys for the project"""
        # Detect project type from CLAUDE.md or project structure
        project_type = self._detect_project_type()
        
        # Create journey validator
        validator = UserJourneyValidator(self.working_dir)
        
        # Validate all journeys
        success, results = validator.validate_all_journeys(self.milestone_num, project_type)
        
        # Save journey report
        report = validator.generate_journey_report(results)
        report_path = self.milestone_dir / "user_journey_report.md"
        report_path.write_text(report)
        
        return success, results
    
    def _detect_project_type(self) -> str:
        """Detect the type of project from CLAUDE.md or structure"""
        claude_md = self.working_dir / "CLAUDE.md"
        if claude_md.exists():
            content = claude_md.read_text().lower()
            if "portfolio" in content and "ml" in content:
                return "ml_portfolio_analyzer"
            elif "task" in content:
                return "task_tracker"
            elif "crud" in content and "api" in content:
                return "fastapi_crud"
                
        # Default
        return "generic"
    
    def validate_all(self) -> Tuple[bool, Dict[str, any]]:
        """Run all E2E validations"""
        results = {
            "basic_requirements": {"success": False, "errors": []},
            "main_py_execution": {"success": False, "errors": []},
            "user_journeys": {"success": False, "results": []}
        }
        
        # Basic requirements
        success, errors = self.validate_basic_requirements()
        results["basic_requirements"]["success"] = success
        results["basic_requirements"]["errors"] = errors
        
        if not success:
            return False, results
            
        # Main.py execution
        success, errors = self.validate_main_py_execution()
        results["main_py_execution"]["success"] = success
        results["main_py_execution"]["errors"] = errors
        
        # User journeys (even if main.py basic test fails, we want to see journey results)
        journey_success, journey_results = self.validate_user_journeys()
        results["user_journeys"]["success"] = journey_success
        results["user_journeys"]["results"] = [
            {
                "name": r.journey.name,
                "success": r.success,
                "errors": r.errors
            }
            for r in journey_results
        ]
        
        # Overall success requires all validations to pass
        overall_success = all([
            results["basic_requirements"]["success"],
            results["main_py_execution"]["success"],
            results["user_journeys"]["success"]
        ])
        
        return overall_success, results