"""
User Journey Validator for CC_AUTOMATOR4
Ensures generated systems pass realistic user workflow tests
"""

import subprocess
import json
import re
from pathlib import Path
from typing import List, Dict, Tuple, Optional
from dataclasses import dataclass
import logging

logger = logging.getLogger(__name__)

@dataclass
class UserJourney:
    """Represents a user journey test scenario"""
    name: str
    description: str
    commands: List[str]
    expected_patterns: List[str]  # Regex patterns that should appear in output
    forbidden_patterns: List[str]  # Patterns that indicate failure
    requires_persistence: bool = False  # Whether journey needs data persistence between commands

@dataclass
class JourneyResult:
    """Result of a user journey test"""
    journey: UserJourney
    success: bool
    outputs: List[str]
    errors: List[str]
    matched_patterns: Dict[str, bool]

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
                        requires_persistence=True
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
    
    def validate_journey(self, journey: UserJourney, timeout: int = 30) -> JourneyResult:
        """Execute and validate a single user journey"""
        outputs = []
        errors = []
        matched_patterns = {pattern: False for pattern in journey.expected_patterns}
        
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
            matched_patterns=matched_patterns
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