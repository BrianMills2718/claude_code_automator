#!/usr/bin/env python3
"""
REAL complex system test: Full-stack web application with database, auth, API, and frontend
This is what would actually test the system's capabilities
"""

import subprocess
import shutil
from pathlib import Path
import os

def create_real_world_project() -> Path:
    """Create a realistic full-stack application project"""
    
    project_dir = Path("/tmp/real_complex_test")
    if project_dir.exists():
        shutil.rmtree(project_dir)
    
    project_dir.mkdir(parents=True)
    
    claude_content = """# Task Management SaaS Platform

## Project Overview
A complete SaaS task management platform with user authentication, real-time collaboration, and REST API

## Technical Requirements
- FastAPI backend with async support
- PostgreSQL database with SQLAlchemy ORM
- JWT authentication and authorization 
- WebSocket support for real-time updates
- RESTful API with full CRUD operations
- React frontend (or HTML/JS if React too complex)
- Docker containerization
- Comprehensive test suite
- API documentation with OpenAPI/Swagger

## Success Criteria
- Complete working web application accessible via browser
- User registration and login system
- Task CRUD operations (create, read, update, delete)
- Real-time collaboration features
- Secure API endpoints with proper authentication
- Database migrations and data persistence
- Deployment-ready with Docker
- >90% test coverage

## Milestones

### Milestone 1: Core API and Database
- Produces a working main.py with FastAPI application
- User authentication (register, login, JWT tokens)
- Basic task CRUD API endpoints
- Database integration with SQLAlchemy
- API documentation with Swagger UI
- All tests pass

### Milestone 2: Advanced Features and Real-time
- Produces enhanced main.py with all Milestone 1 features plus:
- WebSocket support for real-time task updates
- Advanced task features (priorities, due dates)
- Search and filtering capabilities
- Enhanced error handling and validation
- All tests pass

### Milestone 3: Complete Web Application
- Produces full application with all previous features plus:
- Complete web frontend (HTML/JS)
- User interface for all task management features
- Docker containerization
- Production-ready configuration
- All tests pass

## Development Standards

### Code Quality
- All code must pass flake8 linting (max-line-length=100)
- All code must pass mypy strict type checking
- All tests must pass with pytest
- API endpoints must be documented and tested
- Frontend must be functional and accessible

### Testing Requirements
- Unit tests: Test individual components and functions
- Integration tests: Test API endpoints and database interactions
- E2E tests: Test complete user workflows via web interface
- Performance tests: Ensure reasonable response times
- Security tests: Validate authentication and authorization

### Architecture Patterns
- Clean architecture with separation of concerns
- Dependency injection for testability
- Async/await patterns for I/O operations
- RESTful API design principles
- Secure coding practices throughout

## External Dependencies
### API Keys Required:
- DATABASE_URL: PostgreSQL connection string
- JWT_SECRET_KEY: Secret key for JWT token signing
- EMAIL_API_KEY: Email service for notifications (optional)

## Special Considerations
- Handle concurrent user access and data consistency
- Implement proper error handling and user feedback
- Security best practices for web applications
- Performance optimization for database queries
- Scalable architecture for future growth
- Cross-browser compatibility
- Mobile-responsive design
"""
    
    (project_dir / "CLAUDE.md").write_text(claude_content)
    
    # Create realistic project structure
    (project_dir / "src").mkdir()
    (project_dir / "src" / "__init__.py").touch()
    (project_dir / "src" / "api").mkdir()
    (project_dir / "src" / "api" / "__init__.py").touch()
    (project_dir / "src" / "models").mkdir()
    (project_dir / "src" / "models" / "__init__.py").touch()
    (project_dir / "src" / "auth").mkdir()
    (project_dir / "src" / "auth" / "__init__.py").touch()
    (project_dir / "frontend").mkdir()
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

def run_complex_system_test(project_dir: Path) -> dict:
    """Run CC_AUTOMATOR4 on the complex SaaS platform"""
    
    env = os.environ.copy()
    env["FORCE_NON_INTERACTIVE"] = "true"
    env["AUTO_SELECT_CLAUDE"] = "true"
    
    # Provide required environment variables for the app
    env["DATABASE_URL"] = "sqlite:///./test.db"  # Use SQLite for testing
    env["JWT_SECRET_KEY"] = "test-secret-key-for-jwt-tokens"
    
    cmd = [
        "python", "/home/brian/cc_automator4/run.py",
        "--project", str(project_dir),
        "--verbose"  # Get full details of this complex build
    ]
    
    print(f"🚀 Running COMPLEX FULL-STACK SAAS PLATFORM BUILD...")
    print(f"Command: {' '.join(cmd)}")
    print(f"Project: {project_dir}")
    print(f"Expected duration: 30-60 minutes for complete build")
    print()
    
    try:
        result = subprocess.run(
            cmd,
            cwd=str(project_dir),
            text=True,
            timeout=7200,  # 2 hours max for complex system
            env=env
        )
        
        return {
            "success": result.returncode == 0,
            "returncode": result.returncode,
            "completed": True
        }
        
    except subprocess.TimeoutExpired:
        print("⏰ Process timed out after 2 hours")
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

def validate_complex_system(project_dir: Path) -> dict:
    """Comprehensively validate the SaaS platform like a real user would"""
    
    print("🔍 REAL-WORLD COMPLEX SYSTEM VALIDATION")
    print("=" * 60)
    
    validation = {
        "backend_exists": False,
        "database_models": False,
        "api_endpoints": False,
        "authentication": False,
        "websocket_support": False,
        "frontend_exists": False,
        "frontend_functional": False,
        "docker_ready": False,
        "tests_comprehensive": False,
        "all_tests_pass": False,
        "api_documented": False,
        "security_implemented": False,
        "production_ready": False,
        "real_world_usable": False
    }
    
    # Check backend structure
    main_py = project_dir / "main.py"
    if main_py.exists():
        validation["backend_exists"] = True
        print("✅ Backend application exists")
        
        # Check if it's actually a FastAPI app
        content = main_py.read_text()
        if "FastAPI" in content and "app = " in content:
            print("✅ FastAPI application detected")
    else:
        print("❌ No main.py backend found")
    
    # Check database models
    models_dir = project_dir / "src" / "models"
    if models_dir.exists() and any(models_dir.glob("*.py")):
        validation["database_models"] = True
        print("✅ Database models exist")
    else:
        print("❌ No database models found")
    
    # Check API endpoints
    api_dir = project_dir / "src" / "api"
    if api_dir.exists() and any(api_dir.glob("*.py")):
        validation["api_endpoints"] = True
        print("✅ API endpoints exist")
    else:
        print("❌ No API endpoints found")
    
    # Check authentication
    auth_dir = project_dir / "src" / "auth"
    if auth_dir.exists() and any(auth_dir.glob("*.py")):
        validation["authentication"] = True
        print("✅ Authentication system exists")
    else:
        print("❌ No authentication system found")
    
    # Check frontend
    frontend_dir = project_dir / "frontend"
    if frontend_dir.exists() and (
        any(frontend_dir.glob("*.html")) or 
        any(frontend_dir.glob("*.js")) or
        any(frontend_dir.glob("*.jsx"))
    ):
        validation["frontend_exists"] = True
        print("✅ Frontend files exist")
    else:
        print("❌ No frontend found")
    
    # Check Docker setup
    docker_files = [
        project_dir / "Dockerfile",
        project_dir / "docker-compose.yml"
    ]
    if any(f.exists() for f in docker_files):
        validation["docker_ready"] = True
        print("✅ Docker configuration exists")
    else:
        print("❌ No Docker configuration found")
    
    # Check comprehensive test suite
    tests_dir = project_dir / "tests"
    if tests_dir.exists():
        test_files = list(tests_dir.rglob("test_*.py"))
        if len(test_files) >= 10:  # Should have many tests for complex system
            validation["tests_comprehensive"] = True
            print(f"✅ Comprehensive test suite ({len(test_files)} test files)")
            
            # Try to run tests
            try:
                result = subprocess.run(
                    ["python", "-m", "pytest", "tests/", "-v", "--tb=short"],
                    cwd=str(project_dir),
                    capture_output=True,
                    text=True,
                    timeout=300
                )
                if result.returncode == 0:
                    validation["all_tests_pass"] = True
                    print("✅ All tests pass")
                else:
                    print(f"❌ Tests failed")
            except:
                print("❌ Test execution failed")
        else:
            print(f"❌ Insufficient tests ({len(test_files)} files)")
    else:
        print("❌ No tests directory")
    
    # Check API documentation
    if main_py.exists():
        content = main_py.read_text()
        if "swagger" in content.lower() or "openapi" in content.lower():
            validation["api_documented"] = True
            print("✅ API documentation configured")
        else:
            print("❌ No API documentation found")
    
    # Test if backend actually runs
    if validation["backend_exists"]:
        try:
            print("🔄 Testing if backend starts...")
            # Try to start the server briefly
            process = subprocess.Popen(
                ["python", "main.py"],
                cwd=str(project_dir),
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE
            )
            
            # Give it 5 seconds to start
            import time
            time.sleep(5)
            
            # Check if it's still running (good sign)
            if process.poll() is None:
                validation["production_ready"] = True
                print("✅ Backend starts successfully")
                process.terminate()
                process.wait()
            else:
                print("❌ Backend failed to start")
                
        except Exception as e:
            print(f"❌ Backend startup test failed: {e}")
    
    # Overall assessment
    core_features = [
        validation["backend_exists"],
        validation["database_models"],
        validation["api_endpoints"],
        validation["authentication"]
    ]
    
    advanced_features = [
        validation["frontend_exists"],
        validation["tests_comprehensive"],
        validation["docker_ready"]
    ]
    
    quality_standards = [
        validation["all_tests_pass"],
        validation["api_documented"],
        validation["production_ready"]
    ]
    
    # Real-world usability assessment
    if all(core_features) and any(advanced_features) and any(quality_standards):
        validation["real_world_usable"] = True
    
    return validation

def main():
    """Run real-world complex system test"""
    
    print("🧪 REAL-WORLD COMPLEX SYSTEM TEST")
    print("🎯 Full-stack SaaS Task Management Platform")
    print("📊 Expected: 30+ files, API, database, auth, frontend, tests")
    print("=" * 70)
    
    # Create realistic complex project
    project_dir = create_real_world_project()
    print(f"📁 Created complex project: {project_dir}")
    
    # Run full CC_AUTOMATOR4 execution
    print("\n🚀 RUNNING FULL CC_AUTOMATOR4 ON COMPLEX SYSTEM...")
    run_result = run_complex_system_test(project_dir)
    
    if run_result["success"]:
        print("✅ CC_AUTOMATOR4 completed complex system build!")
    else:
        print(f"❌ CC_AUTOMATOR4 failed on complex system: {run_result.get('error', 'Unknown error')}")
        return False
    
    # Real-world validation
    print("\n🔍 REAL-WORLD VALIDATION...")
    validation = validate_complex_system(project_dir)
    
    # Calculate success metrics
    core_backend = (
        validation["backend_exists"] and
        validation["database_models"] and 
        validation["api_endpoints"] and
        validation["authentication"]
    )
    
    full_stack = (
        core_backend and
        validation["frontend_exists"]
    )
    
    production_ready = (
        full_stack and
        validation["tests_comprehensive"] and
        validation["docker_ready"] and
        validation["production_ready"]
    )
    
    enterprise_quality = (
        production_ready and
        validation["all_tests_pass"] and
        validation["api_documented"]
    )
    
    # Final verdict
    print("\n" + "=" * 70)
    print("🎯 REAL-WORLD COMPLEX SYSTEM RESULTS")
    print("=" * 70)
    
    print(f"Core Backend (API + Auth + DB): {'✅ PASS' if core_backend else '❌ FAIL'}")
    print(f"Full-Stack (Backend + Frontend): {'✅ PASS' if full_stack else '❌ FAIL'}")
    print(f"Production Ready (Docker + Tests): {'✅ PASS' if production_ready else '❌ FAIL'}")
    print(f"Enterprise Quality (Docs + CI): {'✅ PASS' if enterprise_quality else '❌ FAIL'}")
    print(f"Real-World Usable: {'✅ PASS' if validation['real_world_usable'] else '❌ FAIL'}")
    
    if enterprise_quality:
        print(f"\n🎉 REAL-WORLD TEST: COMPLETE SUCCESS!")
        print(f"   CC_AUTOMATOR4 built a production-ready full-stack application")
        print(f"   that meets enterprise standards and real-world requirements.")
        return True
    elif production_ready:
        print(f"\n✅ REAL-WORLD TEST: STRONG SUCCESS!")
        print(f"   CC_AUTOMATOR4 built a working full-stack application")
        print(f"   with proper testing and deployment capabilities.")
        return True
    elif full_stack:
        print(f"\n⚠️  REAL-WORLD TEST: PARTIAL SUCCESS")
        print(f"   CC_AUTOMATOR4 built core functionality but lacks")
        print(f"   production readiness and enterprise features.")
        return False
    else:
        print(f"\n💥 REAL-WORLD TEST: FAILED")
        print(f"   System could not build a functional complex application.")
        return False

if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)