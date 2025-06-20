"""
User Journey Validator for CC_AUTOMATOR4
Ensures generated systems pass realistic user workflow tests
"""

import subprocess
import json
import re
from pathlib import Path
from typing import List, Dict, Tuple, Optional
from dataclasses import field
from dataclasses import dataclass
import logging

logger = logging.getLogger(__name__)

@dataclass
class StateValidation:
    """Defines how to validate state persistence between commands"""
    check_type: str  # 'file_exists', 'file_contains', 'database_has', 'api_responds'
    target: str      # File path, database query, API endpoint, etc.
    expected_value: Optional[str] = None  # Expected content or response
    description: str = ""  # Human-readable description

@dataclass
class UserJourney:
    """Represents a user journey test scenario"""
    name: str
    description: str
    commands: List[str]
    expected_patterns: List[str]  # Regex patterns that should appear in output
    forbidden_patterns: List[str]  # Patterns that indicate failure
    requires_persistence: bool = False  # Whether journey needs data persistence between commands
    state_validations: List[StateValidation] = field(default_factory=list)  # State checks between commands

@dataclass
class JourneyResult:
    """Result of a user journey test"""
    journey: UserJourney
    success: bool
    outputs: List[str]
    errors: List[str]
    matched_patterns: Dict[str, bool]
    state_validation_results: Dict[str, bool] = field(default_factory=dict)  # Results of state validations

class UserJourneyValidator:
    """Validates user journeys for generated systems"""
    
    def __init__(self, project_dir: Path):
        self.project_dir = project_dir
        self.main_py = project_dir / "main.py"
        
    def get_milestone_journeys(self, milestone_num: int, project_type: str) -> List[UserJourney]:
        """Get user journeys for specific milestone and project type"""
        
        # ML Portfolio Analyzer specific journeys
        if "portfolio" in project_type.lower() and "ml" in project_type.lower():
            if milestone_num == 1:
                return [
                    UserJourney(
                        name="fetch_then_analyze",
                        description="User fetches data then analyzes it",
                        commands=[
                            "python main.py fetch AAPL",
                            "python main.py analyze AAPL"
                        ],
                        expected_patterns=[
                            r"Market Data for AAPL",  # Fetch should show data
                            r"\d+\.\d+",  # Should see some numbers
                        ],
                        forbidden_patterns=[
                            r"No data found",  # Analyze should not fail after fetch
                            r"Error:",
                            r"Traceback"
                        ],
                        requires_persistence=True,
                        state_validations=[
                            StateValidation(
                                check_type="file_exists",
                                target="data/AAPL.json",
                                description="Verify AAPL data file created by fetch command"
                            ),
                            StateValidation(
                                check_type="file_contains",
                                target="data/AAPL.json",
                                expected_value="AAPL",
                                description="Verify AAPL data file contains symbol data"
                            )
                        ]
                    ),
                    UserJourney(
                        name="search_then_fetch",
                        description="User searches for symbol then fetches it",
                        commands=[
                            "python main.py search apple",
                            "python main.py fetch AAPL"
                        ],
                        expected_patterns=[
                            r"Search Results",
                            r"AAPL|Apple",  # Should find Apple
                            r"Market Data for AAPL"
                        ],
                        forbidden_patterns=[
                            r"No results found",
                            r"Error:",
                            r"Traceback"
                        ]
                    ),
                    UserJourney(
                        name="help_navigation",
                        description="User explores help and available commands",
                        commands=[
                            "python main.py --help",
                            "python main.py fetch --help"
                        ],
                        expected_patterns=[
                            r"fetch.*Fetch market data",
                            r"search.*Search for",
                            r"analyze.*analysis",
                            r"--help.*Show this message"
                        ],
                        forbidden_patterns=[
                            r"Error:",
                            r"Traceback"
                        ]
                    )
                ]
                
        # Add more project-specific journeys here
        
        # Generic journeys for any project
        return [
            UserJourney(
                name="basic_startup",
                description="Program starts and shows help",
                commands=["python main.py --help"],
                expected_patterns=[r"Usage:", r"Commands:"],
                forbidden_patterns=[r"Error:", r"Traceback"]
            )
        ]
    
    def validate_state_persistence(self, validations: List[StateValidation]) -> Tuple[Dict[str, bool], List[str]]:
        """Validate state persistence between commands"""
        results = {}
        errors = []
        
        if not validations:
            return {}, []
            
        for validation in validations:
            try:
                if validation.check_type == "file_exists":
                    file_path = self.project_dir / validation.target
                    results[validation.description] = file_path.exists()
                    if not file_path.exists():
                        errors.append(f"State validation failed: {validation.description} - File {validation.target} does not exist")
                        
                elif validation.check_type == "file_contains":
                    file_path = self.project_dir / validation.target
                    if file_path.exists():
                        content = file_path.read_text()
                        contains_expected = validation.expected_value in content if validation.expected_value else True
                        results[validation.description] = contains_expected
                        if not contains_expected:
                            errors.append(f"State validation failed: {validation.description} - File {validation.target} does not contain '{validation.expected_value}'")
                    else:
                        results[validation.description] = False
                        errors.append(f"State validation failed: {validation.description} - File {validation.target} does not exist")
                        
                elif validation.check_type == "database_has":
                    # Future: implement database checks
                    results[validation.description] = True
                    logger.warning(f"Database validation not yet implemented: {validation.description}")
                    
                elif validation.check_type == "api_responds":
                    # Future: implement API checks  
                    results[validation.description] = True
                    logger.warning(f"API validation not yet implemented: {validation.description}")
                    
                else:
                    results[validation.description] = False
                    errors.append(f"Unknown state validation type: {validation.check_type}")
                    
            except Exception as e:
                results[validation.description] = False
                errors.append(f"State validation error for {validation.description}: {str(e)}")
                
        return results, errors
    
    def validate_journey(self, journey: UserJourney, timeout: int = 30) -> JourneyResult:
        """Execute and validate a single user journey"""
        outputs = []
        errors = []
        matched_patterns = {pattern: False for pattern in journey.expected_patterns}
        state_validation_results = {}
        
        for i, command in enumerate(journey.commands):
            logger.info(f"Executing journey '{journey.name}' step {i+1}: {command}")
            
            try:
                # Execute command
                result = subprocess.run(
                    command.split(),
                    capture_output=True,
                    text=True,
                    timeout=timeout,
                    cwd=self.project_dir
                )
                
                output = result.stdout + result.stderr
                outputs.append(output)
                
                # Check for forbidden patterns
                for pattern in journey.forbidden_patterns:
                    if re.search(pattern, output, re.MULTILINE | re.IGNORECASE):
                        errors.append(f"Step {i+1}: Found forbidden pattern '{pattern}'")
                        
                # Check expected patterns
                for pattern in journey.expected_patterns:
                    if re.search(pattern, output, re.MULTILINE | re.IGNORECASE):
                        matched_patterns[pattern] = True
                        
                # Validate state persistence after each command if required
                if journey.requires_persistence and journey.state_validations and i == 0:
                    # After first command, check if state is properly persisted
                    state_results, state_errors = self.validate_state_persistence(journey.state_validations)
                    state_validation_results.update(state_results)
                    errors.extend(state_errors)
                        
            except subprocess.TimeoutExpired:
                errors.append(f"Step {i+1}: Command timed out after {timeout}s")
            except Exception as e:
                errors.append(f"Step {i+1}: Error executing command: {str(e)}")
                
        # Check if all expected patterns were found
        for pattern, found in matched_patterns.items():
            if not found:
                errors.append(f"Expected pattern '{pattern}' not found in any output")
                
        success = len(errors) == 0 and all(matched_patterns.values())
        
        return JourneyResult(
            journey=journey,
            success=success,
            outputs=outputs,
            errors=errors,
            matched_patterns=matched_patterns,
            state_validation_results=state_validation_results
        )
    
    def validate_all_journeys(self, milestone_num: int, project_type: str) -> Tuple[bool, List[JourneyResult]]:
        """Validate all user journeys for a milestone"""
        journeys = self.get_milestone_journeys(milestone_num, project_type)
        results = []
        all_success = True
        
        for journey in journeys:
            result = self.validate_journey(journey)
            results.append(result)
            if not result.success:
                all_success = False
                logger.error(f"Journey '{journey.name}' failed: {result.errors}")
        
        return all_success, results
    
    def generate_journey_report(self, results: List[JourneyResult]) -> str:
        """Generate a detailed report of journey validation results"""
        report = ["# User Journey Validation Report\n"]
        
        total = len(results)
        passed = sum(1 for r in results if r.success)
        
        report.append(f"**Total Journeys**: {total}")
        report.append(f"**Passed**: {passed}")
        report.append(f"**Failed**: {total - passed}\n")
        
        for result in results:
            status = "✅ PASSED" if result.success else "❌ FAILED"
            report.append(f"## {result.journey.name} - {status}")
            report.append(f"**Description**: {result.journey.description}")
            report.append(f"**Commands**:")
            for cmd in result.journey.commands:
                report.append(f"  - `{cmd}`")
                
            if result.errors:
                report.append(f"**Errors**:")
                for error in result.errors:
                    report.append(f"  - {error}")
                    
            report.append("")
            
        return "\n".join(report)