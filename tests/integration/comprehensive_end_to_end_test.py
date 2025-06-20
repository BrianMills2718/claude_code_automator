#!/usr/bin/env python3
"""
Comprehensive End-to-End Test of CC_AUTOMATOR4 System
Simulates full user workflow without requiring interactive input
"""

import asyncio
import subprocess
import tempfile
import shutil
from pathlib import Path
import os

def create_test_project(project_name: str, project_type: str) -> Path:
    """Create a test project with CLAUDE.md configuration"""
    
    project_dir = Path(f"/tmp/cc_test_{project_name}")
    if project_dir.exists():
        shutil.rmtree(project_dir)
    
    project_dir.mkdir(parents=True)
    
    if project_type == "chatbot":
        claude_content = """# Customer Service Chatbot

## Project Overview
**User Intent:** Customer service chatbot that can handle support tickets and FAQs
**Project Type:** Conversational AI Assistant

## Technical Requirements
- Python 3.9+
- OpenAI integration for natural language processing
- Proper async/await patterns
- Comprehensive error handling
- Full test coverage

## Success Criteria
- Working main.py with CLI interface
- All functionality implemented and tested
- Clean code passing linting and type checking
- Complete documentation

## Milestones

### Milestone 1: Basic Chat Interface
**Produces a working main.py that can:**
- Accept user questions via command line
- Generate helpful responses using OpenAI API
- Handle common customer service scenarios
- Pass all tests for this milestone
- Demonstrate progress toward final goal

## Development Standards

### Code Quality
- All code must pass flake8 linting (max-line-length=100)
- All code must pass mypy strict type checking
- All tests must pass with pytest
- main.py must run successfully as the entry point

### Testing Requirements
- Unit tests: Test individual components in isolation
- Integration tests: Test component interactions
- E2E tests: Test complete workflows via main.py

### Architecture Patterns
- Use dependency injection for testability
- Implement proper async patterns for I/O operations
- Use dataclasses/Pydantic for data models
- Separate concerns between components

## External Dependencies
### API Keys Required:
- OPENAI_API_KEY: OpenAI Chat Completions API

## Special Considerations
- Handle errors gracefully with informative messages
- Use async patterns for I/O-bound operations
- Consider memory usage and performance
- Implement proper logging and monitoring
"""
    
    elif project_type == "calculator":
        claude_content = """# Python Calculator

## Project Overview
**User Intent:** A simple calculator application
**Project Type:** CLI Application

## Technical Requirements
- Python 3.9+
- Command line interface
- Basic arithmetic operations
- Error handling for invalid input

## Success Criteria
- Working main.py that performs calculations
- All functionality implemented and tested
- Clean code passing linting and type checking

## Milestones

### Milestone 1: Basic Calculator
**Produces a working main.py that can:**
- Perform basic arithmetic (add, subtract, multiply, divide)
- Handle user input from command line
- Display results clearly
- Handle errors gracefully
- Pass all tests for this milestone

### Milestone 2: Advanced Features
**Produces enhanced functionality:**
- Support for parentheses and order of operations
- Memory functions (store/recall)
- Scientific calculator functions
- Expression parsing and evaluation

### Milestone 3: User Interface Polish
**Produces a polished user experience:**
- Enhanced error messages
- Input validation
- Help system
- Command history

## Development Standards

### Code Quality
- All code must pass flake8 linting (max-line-length=100)
- All code must pass mypy strict type checking
- All tests must pass with pytest
- main.py must run successfully as the entry point

### Testing Requirements
- Unit tests: Test individual components in isolation
- Integration tests: Test component interactions
- E2E tests: Test complete workflows via main.py

### Architecture Patterns
- Use dependency injection for testability
- Separate concerns between components
- Clear module organization

## External Dependencies
None required - uses only Python standard library

## Special Considerations
- Handle division by zero gracefully
- Support floating point arithmetic
- Clear error messages for invalid expressions
"""
    
    (project_dir / "CLAUDE.md").write_text(claude_content)
    
    # Create basic project structure
    (project_dir / "src").mkdir()
    (project_dir / "src" / "__init__.py").touch()
    (project_dir / "tests").mkdir()
    (project_dir / "tests" / "__init__.py").touch()
    (project_dir / "tests" / "unit").mkdir()
    (project_dir / "tests" / "unit" / "__init__.py").touch()
    (project_dir / "tests" / "integration").mkdir()
    (project_dir / "tests" / "integration" / "__init__.py").touch()
    (project_dir / "tests" / "e2e").mkdir()
    (project_dir / "tests" / "e2e" / "__init__.py").touch()
    
    return project_dir

def run_cc_automator(project_dir: Path, with_api_key: bool = False) -> dict:
    """Run CC_AUTOMATOR4 on a project and capture results"""
    
    env = os.environ.copy()
    if with_api_key:
        env["OPENAI_API_KEY"] = "YOUR_OPENAI_API_KEY_HERE"
    
    # Force non-interactive mode and auto-select Claude for LLM dependencies
    env["FORCE_NON_INTERACTIVE"] = "true"
    env["AUTO_SELECT_CLAUDE"] = "true"
    
    cmd = [
        "python", "/home/brian/cc_automator4/run.py", 
        "--project", str(project_dir),
        "--force-sonnet",  # Use cost-effective model for testing
        "--no-visual"      # Disable visual progress for cleaner output
    ]
    
    print(f"Running: {' '.join(cmd)}")
    print(f"Working directory: {project_dir}")
    
    try:
        result = subprocess.run(
            cmd,
            cwd=str(project_dir),
            capture_output=True,
            text=True,
            timeout=1800,  # 30 minutes max
            env=env
        )
        
        return {
            "success": result.returncode == 0,
            "returncode": result.returncode,
            "stdout": result.stdout,
            "stderr": result.stderr,
            "duration": "completed"
        }
        
    except subprocess.TimeoutExpired:
        return {
            "success": False,
            "returncode": -1,
            "stdout": "",
            "stderr": "Timeout after 30 minutes",
            "duration": "timeout"
        }
    except Exception as e:
        return {
            "success": False,
            "returncode": -2,
            "stdout": "",
            "stderr": str(e),
            "duration": "error"
        }

def validate_project_outputs(project_dir: Path) -> dict:
    """Validate that the project was built correctly"""
    
    results = {
        "main_py_exists": False,
        "main_py_runnable": False,
        "tests_exist": False,
        "tests_pass": False,
        "lint_clean": False,
        "type_check_clean": False,
        "milestones_completed": []
    }
    
    # Check main.py exists
    main_py = project_dir / "main.py"
    if main_py.exists():
        results["main_py_exists"] = True
        
        # Test if main.py runs
        try:
            test_result = subprocess.run(
                ["python", "main.py", "--help"],
                cwd=str(project_dir),
                capture_output=True,
                text=True,
                timeout=10
            )
            results["main_py_runnable"] = test_result.returncode == 0
        except:
            results["main_py_runnable"] = False
    
    # Check tests exist
    tests_dir = project_dir / "tests"
    if tests_dir.exists() and any(tests_dir.rglob("test_*.py")):
        results["tests_exist"] = True
        
        # Run tests
        try:
            test_result = subprocess.run(
                ["python", "-m", "pytest", "tests/", "-v"],
                cwd=str(project_dir),
                capture_output=True,
                text=True,
                timeout=60
            )
            results["tests_pass"] = test_result.returncode == 0
        except:
            results["tests_pass"] = False
    
    # Check lint
    try:
        lint_result = subprocess.run(
            ["flake8", "--select=F", "."],
            cwd=str(project_dir),
            capture_output=True,
            text=True,
            timeout=30
        )
        results["lint_clean"] = lint_result.returncode == 0
    except:
        results["lint_clean"] = False
    
    # Check type checking
    try:
        mypy_result = subprocess.run(
            ["mypy", "--strict", "src/"],
            cwd=str(project_dir),
            capture_output=True,
            text=True,
            timeout=30
        )
        results["type_check_clean"] = mypy_result.returncode == 0
    except:
        results["type_check_clean"] = False
    
    # Check milestone completion
    for milestone_dir in project_dir.glob("milestone_*"):
        if (milestone_dir / "e2e_evidence.log").exists():
            milestone_num = milestone_dir.name.split("_")[1]
            results["milestones_completed"].append(int(milestone_num))
    
    return results

def main():
    """Run comprehensive end-to-end tests"""
    
    print("=" * 80)
    print("🧪 COMPREHENSIVE END-TO-END CC_AUTOMATOR4 TEST")
    print("=" * 80)
    
    test_cases = [
        ("calculator", "calculator", False),  # No API key needed
        ("chatbot", "chatbot", True),         # Requires OpenAI API key
    ]
    
    results = {}
    
    for test_name, project_type, needs_api_key in test_cases:
        print(f"\n📋 Testing: {test_name.upper()}")
        print("-" * 60)
        
        # Create test project
        print(f"Creating test project...")
        project_dir = create_test_project(test_name, project_type)
        print(f"Project created: {project_dir}")
        
        # Run CC_AUTOMATOR4
        print(f"Running CC_AUTOMATOR4...")
        run_result = run_cc_automator(project_dir, with_api_key=needs_api_key)
        
        # Validate outputs
        print(f"Validating outputs...")
        validation_result = validate_project_outputs(project_dir)
        
        results[test_name] = {
            "run_result": run_result,
            "validation": validation_result,
            "project_dir": str(project_dir)
        }
        
        # Print immediate results
        if run_result["success"]:
            print(f"✅ CC_AUTOMATOR4 completed successfully")
        else:
            print(f"❌ CC_AUTOMATOR4 failed: {run_result['stderr'][:200]}...")
        
        print(f"📊 Validation results:")
        print(f"  - main.py exists: {validation_result['main_py_exists']}")
        print(f"  - main.py runnable: {validation_result['main_py_runnable']}")
        print(f"  - tests exist: {validation_result['tests_exist']}")
        print(f"  - tests pass: {validation_result['tests_pass']}")
        print(f"  - lint clean: {validation_result['lint_clean']}")
        print(f"  - type check clean: {validation_result['type_check_clean']}")
        print(f"  - milestones completed: {validation_result['milestones_completed']}")
    
    # Final summary
    print("\n" + "=" * 80)
    print("🎯 FINAL TEST RESULTS")
    print("=" * 80)
    
    total_tests = len(test_cases)
    successful_runs = sum(1 for r in results.values() if r["run_result"]["success"])
    working_outputs = sum(1 for r in results.values() 
                         if r["validation"]["main_py_exists"] and 
                            r["validation"]["main_py_runnable"])
    
    print(f"Total tests: {total_tests}")
    print(f"Successful runs: {successful_runs}/{total_tests}")
    print(f"Working outputs: {working_outputs}/{total_tests}")
    
    for test_name, result in results.items():
        status = "✅ PASS" if result["run_result"]["success"] else "❌ FAIL"
        print(f"  {test_name}: {status}")
        if not result["run_result"]["success"]:
            print(f"    Error: {result['run_result']['stderr'][:100]}...")
    
    # Overall verdict
    if successful_runs == total_tests and working_outputs == total_tests:
        print(f"\n🎉 ALL TESTS PASSED - CC_AUTOMATOR4 IS FULLY FUNCTIONAL")
        return True
    elif successful_runs > 0:
        print(f"\n⚠️  PARTIAL SUCCESS - {successful_runs}/{total_tests} tests passed")
        return False
    else:
        print(f"\n💥 ALL TESTS FAILED - System has critical issues")
        return False

if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)