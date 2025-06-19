#!/usr/bin/env python3
"""
Implementation Validator for CC_AUTOMATOR4
Ensures all functionality is real, not mocked or stubbed
"""

import ast
import subprocess
from pathlib import Path
from typing import List, Tuple, Dict


class ImplementationValidator:
    """Validates that implementations are real, not mocked"""
    
    def __init__(self, project_dir: Path):
        self.project_dir = Path(project_dir)
        self.issues = []
        
    def validate_all(self) -> Tuple[bool, List[str]]:
        """Run all validation checks"""
        self.issues = []
        
        # Check for mock/stub patterns in main code
        self._check_for_mocks()
        
        # Check for hardcoded fake responses
        self._check_for_fake_responses()
        
        # Check that API calls are real
        self._check_api_implementations()
        
        # Run main.py with real inputs
        self._test_real_execution()
        
        return len(self.issues) == 0, self.issues
    
    def _check_for_mocks(self):
        """Check main code for mock/stub usage"""
        # Exclude test files
        for py_file in self.project_dir.rglob("*.py"):
            if "test" in str(py_file) or "__pycache__" in str(py_file):
                continue
                
            try:
                content = py_file.read_text()
                
                # Check for mock indicators
                mock_patterns = [
                    "from unittest.mock import",
                    "from unittest import mock",
                    "import mock",
                    "@mock.",
                    "Mock(",
                    "MagicMock(",
                    "TODO:",
                    "FIXME:",
                    "NotImplementedError",
                    "raise NotImplemented",
                    "pass  # TODO",
                    "return None  # TODO",
                    "return []  # TODO",
                    "return {}  # TODO",
                    "return ''  # TODO",
                    "return 0  # TODO"
                ]
                
                for pattern in mock_patterns:
                    if pattern in content:
                        self.issues.append(
                            f"Found potential mock/stub in {py_file.relative_to(self.project_dir)}: '{pattern}'"
                        )
                        
            except Exception as e:
                continue
    
    def _check_for_fake_responses(self):
        """Check for hardcoded fake responses"""
        fake_patterns = [
            # Fake API responses
            ('return {"fake":', "Hardcoded fake response"),
            ('return {"test":', "Possible test data in production code"),
            ('return {"mock":', "Mock response in production code"),
            ('return "TODO"', "Unimplemented functionality"),
            ('return "Not implemented"', "Unimplemented functionality"),
            # Fake data
            ('example.com', "Using example domain instead of real API"),
            ('test@example', "Using test email in production code"),
            ('12345', "Possible test/fake ID"),
            ('Lorem ipsum', "Placeholder text in production"),
        ]
        
        for py_file in self.project_dir.rglob("*.py"):
            if "test" in str(py_file) or "__pycache__" in str(py_file):
                continue
                
            try:
                content = py_file.read_text()
                for pattern, description in fake_patterns:
                    if pattern.lower() in content.lower():
                        self.issues.append(
                            f"{description} in {py_file.relative_to(self.project_dir)}"
                        )
            except Exception:
                continue
    
    def _check_api_implementations(self):
        """Check that API calls are real implementations"""
        # Look for common API patterns
        api_indicators = [
            "requests.",
            "httpx.",
            "aiohttp.",
            "urllib.",
            "fetch(",
            "axios."
        ]
        
        for py_file in self.project_dir.rglob("*.py"):
            if "test" in str(py_file) or "__pycache__" in str(py_file):
                continue
                
            try:
                content = py_file.read_text()
                
                # Check if file has API indicators but might be mocked
                has_api = any(ind in content for ind in api_indicators)
                if has_api:
                    # Look for signs of real implementation
                    real_signs = [
                        "timeout=",
                        "headers=",
                        "auth=",
                        ".status_code",
                        ".json()",
                        "try:",  # Error handling
                        "except requests.",
                        "except httpx.",
                    ]
                    
                    has_real_impl = any(sign in content for sign in real_signs)
                    if not has_real_impl:
                        self.issues.append(
                            f"API usage in {py_file.relative_to(self.project_dir)} may not be fully implemented"
                        )
                        
            except Exception:
                continue
    
    def _test_real_execution(self):
        """Test that main.py actually works with real inputs"""
        main_py = self.project_dir / "main.py"
        
        if not main_py.exists():
            self.issues.append("main.py not found")
            return
            
        try:
            # Try running main.py
            result = subprocess.run(
                ["python", "main.py"],
                input="0\n",  # Exit command
                capture_output=True,
                text=True,
                timeout=5,
                cwd=str(self.project_dir)
            )
            
            if result.returncode != 0:
                self.issues.append(f"main.py failed to run: {result.stderr}")
            elif "not implemented" in result.stdout.lower():
                self.issues.append("main.py contains 'not implemented' messages")
            elif "todo" in result.stdout.lower():
                self.issues.append("main.py contains TODO messages")
                
        except subprocess.TimeoutExpired:
            # This might be OK if it's an interactive app
            pass
        except Exception as e:
            self.issues.append(f"Failed to test main.py: {e}")


def create_validation_phase_prompt(milestone) -> str:
    """Create prompt for validation phase"""
    return f"""
## Implementation Validation Phase

Thoroughly validate that ALL functionality for {milestone.name} is REAL and working.

### Critical Checks:

1. **No Mocks in Production Code**
   - Run: `grep -r "mock\\|Mock\\|TODO\\|FIXME\\|NotImplemented" --include="*.py" --exclude-dir=tests .`
   - Ensure NO mocks/stubs in main code (only in tests)

2. **Real API Implementations**
   - If the code makes API calls, verify they're real
   - Check for actual error handling
   - No hardcoded fake responses

3. **All Features Actually Work**
   - Test EVERY feature mentioned in success criteria
   - Use real inputs, not test data
   - Verify actual functionality, not just that it runs

4. **Integration Test**
   - Run the application end-to-end
   - Try edge cases and error scenarios
   - Ensure graceful error handling

### Success Criteria to Validate:
{chr(10).join(f"- {criterion}" for criterion in milestone.success_criteria)}

### Evidence Required:
1. Show grep results proving no mocks in production
2. Demonstrate each feature working with real data
3. Show error handling with invalid inputs
4. Create validation_report.md with:
   - List of all features tested
   - Real examples of each feature working
   - Confirmation that NO functionality is mocked

IMPORTANT: If you find ANY mocked/stubbed functionality, you must fix it to use real implementations before marking this phase complete.
"""


if __name__ == "__main__":
    # Example usage
    validator = ImplementationValidator(Path("."))
    is_valid, issues = validator.validate_all()
    
    if is_valid:
        print("✓ All implementations appear to be real")
    else:
        print("✗ Found potential mock/stub implementations:")
        for issue in issues:
            print(f"  - {issue}")