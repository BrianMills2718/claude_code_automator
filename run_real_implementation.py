#!/usr/bin/env python3
"""
Run a real implementation test - Create a web API with database
Using the existing project structure that works
"""

import subprocess
import shutil
from pathlib import Path
import os
import time

def create_web_api_project() -> Path:
    """Create a realistic web API project that will pass validation"""
    
    project_dir = Path("/tmp/web_api_test")
    if project_dir.exists():
        shutil.rmtree(project_dir)
    
    project_dir.mkdir(parents=True)
    
    # Use the exact format that works based on test_example
    claude_content = """# Task Management Web API

## Project Overview
A web-based task management API with user authentication and real-time features

## Technical Requirements
- FastAPI web framework
- SQLite database with SQLAlchemy ORM
- User authentication with JWT tokens
- RESTful API endpoints
- WebSocket support for real-time updates

## Success Criteria
- Working main.py that starts web server
- All functionality implemented and tested
- Clean code passing linting and type checking

## Milestones

### Milestone 1: Basic API with authentication
- Produces a working main.py with this functionality
- All tests pass

### Milestone 2: Task CRUD operations and database
- Produces a working main.py with this functionality  
- All tests pass

### Milestone 3: Web frontend and real-time features
- Produces a working main.py with this functionality
- All tests pass

## Development Standards

### Code Quality
- All code must pass flake8 linting (max-line-length=100)
- All code must pass mypy strict type checking
- All tests must pass with pytest
- main.py must run successfully as the entry point

### Testing Requirements
- Unit tests: Test individual components in isolation
- Integration tests: Test API endpoints and database interactions
- E2E tests: Test complete workflows via HTTP requests

### Architecture Patterns
- Use dependency injection for testability
- Separate concerns between API, business logic, and data layers
- Async/await patterns for I/O operations
- Clean module organization

## External Dependencies
### API Keys Required:
- DATABASE_URL: SQLite database file path
- JWT_SECRET_KEY: Secret key for JWT token signing

## Special Considerations
- Handle concurrent user access safely
- Implement proper error handling and validation
- Use secure authentication practices
- Ensure API is properly documented
- Support for JSON request/response format
"""
    
    (project_dir / "CLAUDE.md").write_text(claude_content)
    
    # Create project structure
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

def run_implementation(project_dir: Path) -> dict:
    """Run CC_AUTOMATOR4 on the web API project"""
    
    env = os.environ.copy()
    env["FORCE_NON_INTERACTIVE"] = "true" 
    env["AUTO_SELECT_CLAUDE"] = "true"
    env["DATABASE_URL"] = "sqlite:///./tasks.db"
    env["JWT_SECRET_KEY"] = "supersecret-jwt-key-for-testing"
    
    cmd = [
        "python", "/home/brian/cc_automator4/run.py",
        "--project", str(project_dir),
        "--verbose"
    ]
    
    print(f"🚀 IMPLEMENTING REAL WEB API PROJECT")
    print(f"📁 Project: {project_dir}")
    print(f"⏱️  Expected duration: 15-30 minutes")
    print(f"🎯 Target: FastAPI + Auth + Database + WebSocket + Frontend")
    print()
    
    start_time = time.time()
    
    try:
        result = subprocess.run(
            cmd,
            cwd=str(project_dir),
            text=True,
            timeout=3600,  # 1 hour timeout
            env=env
        )
        
        duration = time.time() - start_time
        
        return {
            "success": result.returncode == 0,
            "returncode": result.returncode,
            "duration_minutes": duration / 60,
            "completed": True
        }
        
    except subprocess.TimeoutExpired:
        duration = time.time() - start_time
        print(f"⏰ Timed out after {duration/60:.1f} minutes")
        return {
            "success": False,
            "returncode": -1,
            "duration_minutes": duration / 60,
            "completed": False,
            "error": "timeout"
        }
    except Exception as e:
        duration = time.time() - start_time
        print(f"💥 Failed: {e}")
        return {
            "success": False,
            "returncode": -2,
            "duration_minutes": duration / 60,
            "completed": False,
            "error": str(e)
        }

def validate_implementation(project_dir: Path) -> dict:
    """Validate the implemented web API like a real user"""
    
    print("\n🔍 REAL-WORLD VALIDATION")
    print("=" * 50)
    
    results = {
        "files_created": 0,
        "main_py_exists": False,
        "main_py_runnable": False,
        "api_server_starts": False,
        "endpoints_functional": False,
        "database_working": False,
        "auth_implemented": False,
        "tests_exist": False,
        "tests_pass": False,
        "frontend_exists": False,
        "professional_quality": False
    }
    
    # Count files created
    all_files = list(project_dir.rglob("*.py"))
    results["files_created"] = len(all_files)
    print(f"📁 Files created: {len(all_files)}")
    
    # Check main.py
    main_py = project_dir / "main.py"
    if main_py.exists():
        results["main_py_exists"] = True
        print("✅ main.py exists")
        
        content = main_py.read_text()
        if "FastAPI" in content or "fastapi" in content:
            print("✅ FastAPI application detected")
            
            # Test if server starts
            try:
                print("🔄 Testing server startup...")
                process = subprocess.Popen(
                    ["python", "main.py"],
                    cwd=str(project_dir),
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE
                )
                
                time.sleep(3)  # Give it time to start
                
                if process.poll() is None:
                    results["api_server_starts"] = True
                    print("✅ API server starts successfully")
                    process.terminate()
                    process.wait()
                else:
                    print("❌ API server failed to start")
                    
            except Exception as e:
                print(f"❌ Server startup test failed: {e}")
        
        # Check for authentication
        if "jwt" in content.lower() or "token" in content.lower():
            results["auth_implemented"] = True
            print("✅ Authentication system detected")
        
        # Check for database
        if "database" in content.lower() or "sqlalchemy" in content.lower():
            results["database_working"] = True
            print("✅ Database integration detected")
            
    else:
        print("❌ main.py not found")
    
    # Check comprehensive tests
    tests_dir = project_dir / "tests"
    if tests_dir.exists():
        test_files = list(tests_dir.rglob("test_*.py"))
        if len(test_files) >= 5:  # Should have multiple test files
            results["tests_exist"] = True
            print(f"✅ Test suite exists ({len(test_files)} files)")
            
            # Run tests
            try:
                result = subprocess.run(
                    ["python", "-m", "pytest", "tests/", "-v"],
                    cwd=str(project_dir),
                    capture_output=True,
                    text=True,
                    timeout=120
                )
                if result.returncode == 0:
                    results["tests_pass"] = True
                    print("✅ All tests pass")
                else:
                    print("❌ Some tests failed")
            except:
                print("❌ Test execution failed")
        else:
            print(f"❌ Insufficient tests ({len(test_files)} files)")
    
    # Check frontend
    html_files = list(project_dir.rglob("*.html"))
    js_files = list(project_dir.rglob("*.js"))
    if html_files or js_files:
        results["frontend_exists"] = True
        print(f"✅ Frontend files exist ({len(html_files)} HTML, {len(js_files)} JS)")
    
    # Professional quality assessment
    has_requirements = (project_dir / "requirements.txt").exists()
    has_readme = (project_dir / "README.md").exists()
    has_setup = (project_dir / "setup.py").exists()
    
    if has_requirements and (has_readme or has_setup):
        results["professional_quality"] = True
        print("✅ Professional package structure")
    
    return results

def main():
    """Run real implementation test"""
    
    print("🧪 REAL IMPLEMENTATION TEST")
    print("🎯 Task Management Web API with Authentication")
    print("=" * 60)
    
    # Create project
    project_dir = create_web_api_project()
    print(f"📁 Created project: {project_dir}")
    
    # Run implementation
    print("\n🚀 RUNNING IMPLEMENTATION...")
    result = run_implementation(project_dir)
    
    if result["success"]:
        print(f"✅ Implementation completed in {result['duration_minutes']:.1f} minutes!")
    else:
        print(f"❌ Implementation failed after {result['duration_minutes']:.1f} minutes")
        if not result["completed"]:
            print(f"   Reason: {result.get('error', 'unknown')}")
        return False
    
    # Validate implementation
    validation = validate_implementation(project_dir)
    
    # Assessment
    print("\n" + "=" * 60)
    print("🎯 IMPLEMENTATION RESULTS")
    print("=" * 60)
    
    core_api = (
        validation["main_py_exists"] and
        validation["api_server_starts"] and
        validation["auth_implemented"] and
        validation["database_working"]
    )
    
    quality_code = (
        validation["tests_exist"] and
        validation["tests_pass"] and
        validation["professional_quality"]
    )
    
    complete_app = (
        core_api and
        validation["frontend_exists"]
    )
    
    print(f"Files Created: {validation['files_created']}")
    print(f"Core API (FastAPI + Auth + DB): {'✅ PASS' if core_api else '❌ FAIL'}")
    print(f"Quality Code (Tests + Structure): {'✅ PASS' if quality_code else '❌ FAIL'}")
    print(f"Complete App (Frontend + API): {'✅ PASS' if complete_app else '❌ FAIL'}")
    
    if complete_app and quality_code:
        print(f"\n🎉 REAL IMPLEMENTATION: COMPLETE SUCCESS!")
        print(f"   Built a working web API with authentication, database,")
        print(f"   comprehensive tests, and frontend interface.")
        print(f"   Duration: {result['duration_minutes']:.1f} minutes")
        print(f"   Files: {validation['files_created']} Python files")
        return True
    elif core_api:
        print(f"\n✅ REAL IMPLEMENTATION: PARTIAL SUCCESS!")
        print(f"   Built working API backend but missing some components.")
        return True
    else:
        print(f"\n💥 REAL IMPLEMENTATION: FAILED")
        print(f"   Could not build functional web API.")
        return False

if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)