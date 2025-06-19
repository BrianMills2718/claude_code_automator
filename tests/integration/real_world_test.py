#!/usr/bin/env python3
"""
Real-world comprehensive test: Multi-milestone calculator project
Tests the FULL CC_AUTOMATOR4 system as a user would experience it
"""

import subprocess
import shutil
from pathlib import Path
import os

def create_real_calculator_project() -> Path:
    """Create a realistic 3-milestone calculator project"""
    
    project_dir = Path("/tmp/real_calculator_test")
    if project_dir.exists():
        shutil.rmtree(project_dir)
    
    project_dir.mkdir(parents=True)
    
    claude_content = """# Advanced Calculator Application

## Project Overview
A comprehensive command-line calculator with advanced mathematical functions

## Technical Requirements
- Python 3.8+
- Command line interface
- Expression parsing and evaluation
- Advanced mathematical functions

## Success Criteria
- Working main.py that performs calculations
- All functionality implemented and tested
- Clean code passing linting and type checking

## Milestones

### Milestone 1: Basic arithmetic operations (add, subtract, multiply, divide)
- Produces a working main.py with this functionality
- Handles command line arguments like "python main.py 2+2"
- All tests pass

### Milestone 2: Advanced operations (sin, cos, sqrt, power, parentheses)
- Produces a working main.py with this functionality
- Supports expressions like "sin(pi/2)" and "(2+3)*4"
- All tests pass

### Milestone 3: Professional interface and error handling
- Produces a working main.py with this functionality
- Complete CLI with help system and error messages
- All tests pass

## Development Standards

### Code Quality
- All code must pass flake8 linting (max-line-length=100)
- All code must pass mypy strict type checking
- All tests must pass with pytest
- main.py must run successfully as the entry point
- Code coverage should be >90%

### Testing Requirements
- Unit tests: Test individual components in isolation
- Integration tests: Test component interactions
- E2E tests: Test complete workflows via main.py
- Performance tests: Ensure reasonable response times
- Error handling tests: Verify graceful failure modes

### Architecture Patterns
- Use dependency injection for testability
- Separate concerns between parsing, evaluation, and UI
- Plugin architecture for extensibility
- Clear module organization with proper abstractions
- Type hints throughout for maintainability

## External Dependencies
None required - uses only Python standard library for core functionality
Optional: Enhanced libraries for advanced mathematical functions

## Special Considerations
- Handle floating point precision issues
- Support for very large numbers
- Graceful degradation when optional features unavailable
- Cross-platform compatibility
- Memory efficient for complex calculations
- Security considerations for expression evaluation
"""
    
    (project_dir / "CLAUDE.md").write_text(claude_content)
    
    # Create proper project structure
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
    
    # Initialize git
    subprocess.run(["git", "init"], cwd=str(project_dir), capture_output=True)
    subprocess.run(["git", "config", "user.email", "test@example.com"], cwd=str(project_dir), capture_output=True)
    subprocess.run(["git", "config", "user.name", "Test User"], cwd=str(project_dir), capture_output=True)
    
    return project_dir

def run_full_calculator_test(project_dir: Path) -> dict:
    """Run CC_AUTOMATOR4 on the full 3-milestone calculator project"""
    
    env = os.environ.copy()
    env["FORCE_NON_INTERACTIVE"] = "true"
    env["AUTO_SELECT_CLAUDE"] = "true"
    
    cmd = [
        "python", "/home/brian/cc_automator4/run.py",
        "--project", str(project_dir),
        "--force-sonnet",  # Cost-effective for testing
        "--verbose"        # Get full details
    ]
    
    print(f"🚀 Running FULL 3-milestone calculator project...")
    print(f"Command: {' '.join(cmd)}")
    print(f"Project: {project_dir}")
    print()
    
    try:
        result = subprocess.run(
            cmd,
            cwd=str(project_dir),
            text=True,
            timeout=3600,  # 1 hour max for full project
            env=env
        )
        
        return {
            "success": result.returncode == 0,
            "returncode": result.returncode,
            "completed": True
        }
        
    except subprocess.TimeoutExpired:
        print("⏰ Process timed out after 1 hour")
        return {
            "success": False,
            "returncode": -1,
            "completed": False,
            "error": "timeout"
        }
    except Exception as e:
        print(f"💥 Process failed: {e}")
        return {
            "success": False,
            "returncode": -2,
            "completed": False,
            "error": str(e)
        }

def validate_full_calculator(project_dir: Path) -> dict:
    """Comprehensively validate the completed calculator project"""
    
    print("🔍 COMPREHENSIVE VALIDATION")
    print("=" * 50)
    
    validation = {
        "main_py_exists": False,
        "main_py_functional": False,
        "basic_math_works": False,
        "advanced_math_works": False,
        "cli_interface_works": False,
        "tests_exist": False,
        "all_tests_pass": False,
        "lint_clean": False,
        "type_check_clean": False,
        "milestones_completed": [],
        "package_structure": False,
        "setup_py_exists": False,
        "installable": False
    }
    
    # Check main.py exists and basic functionality
    main_py = project_dir / "main.py"
    if main_py.exists():
        validation["main_py_exists"] = True
        print("✅ main.py exists")
        
        # Test basic functionality
        try:
            # Test help
            result = subprocess.run(
                ["python", "main.py", "--help"],
                cwd=str(project_dir),
                capture_output=True,
                text=True,
                timeout=10
            )
            if result.returncode == 0:
                validation["main_py_functional"] = True
                validation["cli_interface_works"] = True
                print("✅ CLI interface functional")
        except:
            print("❌ CLI interface failed")
        
        # Test basic math
        try:
            result = subprocess.run(
                ["python", "main.py", "2+2"],
                cwd=str(project_dir),
                capture_output=True,
                text=True,
                timeout=10
            )
            if result.returncode == 0 and "4" in result.stdout:
                validation["basic_math_works"] = True
                print("✅ Basic math works")
        except:
            print("❌ Basic math failed")
        
        # Test advanced math
        try:
            result = subprocess.run(
                ["python", "main.py", "sin(0)"],
                cwd=str(project_dir),
                capture_output=True,
                text=True,
                timeout=10
            )
            if result.returncode == 0:
                validation["advanced_math_works"] = True
                print("✅ Advanced math works")
        except:
            print("❌ Advanced math failed")
    else:
        print("❌ main.py missing")
    
    # Check comprehensive test suite
    tests_dir = project_dir / "tests"
    if tests_dir.exists():
        test_files = list(tests_dir.rglob("test_*.py"))
        if len(test_files) >= 3:  # Should have unit, integration, e2e tests
            validation["tests_exist"] = True
            print(f"✅ Test suite exists ({len(test_files)} test files)")
            
            # Run full test suite
            try:
                result = subprocess.run(
                    ["python", "-m", "pytest", "tests/", "-v", "--tb=short"],
                    cwd=str(project_dir),
                    capture_output=True,
                    text=True,
                    timeout=120
                )
                if result.returncode == 0:
                    validation["all_tests_pass"] = True
                    print("✅ All tests pass")
                else:
                    print(f"❌ Tests failed: {result.stdout[-200:]}")
            except:
                print("❌ Test execution failed")
        else:
            print(f"❌ Insufficient tests ({len(test_files)} files)")
    else:
        print("❌ No tests directory")
    
    # Check code quality
    try:
        result = subprocess.run(
            ["flake8", "--select=F", "."],
            cwd=str(project_dir),
            capture_output=True,
            text=True,
            timeout=30
        )
        if result.returncode == 0:
            validation["lint_clean"] = True
            print("✅ Lint clean")
        else:
            print(f"❌ Lint errors: {result.stdout[:100]}")
    except:
        print("❌ Lint check failed")
    
    # Check type checking
    try:
        result = subprocess.run(
            ["mypy", "--strict", "src/"],
            cwd=str(project_dir),
            capture_output=True,
            text=True,
            timeout=30
        )
        if result.returncode == 0:
            validation["type_check_clean"] = True
            print("✅ Type checking clean")
        else:
            print(f"❌ Type errors: {result.stdout[:100]}")
    except:
        print("❌ Type check failed")
    
    # Check milestone completion
    milestone_dirs = list(project_dir.glob(".cc_automator/milestones/milestone_*"))
    for milestone_dir in milestone_dirs:
        evidence_file = milestone_dir / "e2e_evidence.log"
        if evidence_file.exists():
            milestone_num = int(milestone_dir.name.split("_")[1])
            validation["milestones_completed"].append(milestone_num)
    
    print(f"✅ Milestones completed: {validation['milestones_completed']}")
    
    # Check package structure
    setup_py = project_dir / "setup.py"
    if setup_py.exists():
        validation["setup_py_exists"] = True
        print("✅ setup.py exists")
        
        # Test if package is installable
        try:
            result = subprocess.run(
                ["python", "setup.py", "check"],
                cwd=str(project_dir),
                capture_output=True,
                text=True,
                timeout=30
            )
            if result.returncode == 0:
                validation["installable"] = True
                print("✅ Package is installable")
        except:
            print("❌ Package installation check failed")
    else:
        print("❌ setup.py missing")
    
    # Check overall package structure
    if (project_dir / "src").exists() and (project_dir / "README.md").exists():
        validation["package_structure"] = True
        print("✅ Professional package structure")
    else:
        print("❌ Missing package structure elements")
    
    return validation

def main():
    """Run comprehensive real-world test"""
    
    print("🧪 REAL-WORLD CC_AUTOMATOR4 TEST")
    print("🎯 Multi-milestone advanced calculator project")
    print("=" * 60)
    
    # Create realistic project
    project_dir = create_real_calculator_project()
    print(f"📁 Created project: {project_dir}")
    
    # Run full CC_AUTOMATOR4 execution
    print("\n🚀 RUNNING FULL CC_AUTOMATOR4...")
    run_result = run_full_calculator_test(project_dir)
    
    if run_result["success"]:
        print("✅ CC_AUTOMATOR4 completed successfully!")
    else:
        print(f"❌ CC_AUTOMATOR4 failed: {run_result.get('error', 'Unknown error')}")
        return False
    
    # Comprehensive validation
    print("\n🔍 COMPREHENSIVE VALIDATION...")
    validation = validate_full_calculator(project_dir)
    
    # Calculate success metrics
    core_functionality = (
        validation["main_py_exists"] and
        validation["main_py_functional"] and 
        validation["basic_math_works"]
    )
    
    advanced_features = (
        validation["advanced_math_works"] and
        validation["cli_interface_works"]
    )
    
    quality_standards = (
        validation["tests_exist"] and
        validation["all_tests_pass"] and
        validation["lint_clean"] and
        validation["type_check_clean"]
    )
    
    professional_package = (
        validation["package_structure"] and
        validation["setup_py_exists"] and
        validation["installable"]
    )
    
    milestone_completion = len(validation["milestones_completed"]) >= 3
    
    # Final verdict
    print("\n" + "=" * 60)
    print("🎯 REAL-WORLD TEST RESULTS")
    print("=" * 60)
    
    print(f"Core Functionality: {'✅ PASS' if core_functionality else '❌ FAIL'}")
    print(f"Advanced Features: {'✅ PASS' if advanced_features else '❌ FAIL'}")
    print(f"Quality Standards: {'✅ PASS' if quality_standards else '❌ FAIL'}")
    print(f"Professional Package: {'✅ PASS' if professional_package else '❌ FAIL'}")
    print(f"Milestone Completion: {'✅ PASS' if milestone_completion else '❌ FAIL'}")
    
    overall_success = (
        core_functionality and
        advanced_features and
        quality_standards and
        milestone_completion
    )
    
    if overall_success:
        print(f"\n🎉 REAL-WORLD TEST: COMPLETE SUCCESS!")
        print(f"   CC_AUTOMATOR4 built a fully functional, professional")
        print(f"   multi-milestone application that works as expected.")
        return True
    else:
        print(f"\n💥 REAL-WORLD TEST: FAILED")
        print(f"   System did not meet real-world user expectations.")
        return False

if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)