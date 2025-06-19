#!/usr/bin/env python3
"""
Debug test run to see exactly what's happening
"""

import subprocess
import os
from pathlib import Path

def debug_run():
    # Create simple test project 
    test_dir = Path("/tmp/cc_debug_test")
    test_dir.mkdir(exist_ok=True)
    
    claude_md = """# Simple Test Project

## Project Overview
**User Intent:** A simple test application
**Project Type:** CLI Application

## Milestones

### Milestone 1: Hello World
**Produces a working main.py that can:**
- Print "Hello World" when run
- Pass all tests for this milestone

## Development Standards
- All code must pass flake8 linting (max-line-length=100)
- All code must pass mypy strict type checking
- All tests must pass with pytest
- main.py must run successfully as the entry point

## External Dependencies
None required - uses only Python standard library
"""
    
    (test_dir / "CLAUDE.md").write_text(claude_md)
    
    # Create basic structure
    (test_dir / "src").mkdir(exist_ok=True)
    (test_dir / "src" / "__init__.py").touch()
    (test_dir / "tests").mkdir(exist_ok=True)
    (test_dir / "tests" / "__init__.py").touch()
    (test_dir / "tests" / "unit").mkdir(exist_ok=True)
    (test_dir / "tests" / "unit" / "__init__.py").touch()
    (test_dir / "tests" / "integration").mkdir(exist_ok=True)
    (test_dir / "tests" / "integration" / "__init__.py").touch()
    (test_dir / "tests" / "e2e").mkdir(exist_ok=True)
    (test_dir / "tests" / "e2e" / "__init__.py").touch()
    
    # Initialize git repo
    subprocess.run(["git", "init"], cwd=str(test_dir), capture_output=True)
    subprocess.run(["git", "config", "user.email", "test@example.com"], cwd=str(test_dir), capture_output=True)
    subprocess.run(["git", "config", "user.name", "Test User"], cwd=str(test_dir), capture_output=True)
    
    env = os.environ.copy()
    env["FORCE_NON_INTERACTIVE"] = "true"
    env["AUTO_SELECT_CLAUDE"] = "true"
    
    cmd = [
        "python", "/home/brian/cc_automator4/run.py",
        "--project", str(test_dir),
        "--force-sonnet",
        "--no-visual",
        "--verbose"
    ]
    
    print(f"Running: {' '.join(cmd)}")
    print(f"Environment additions:")
    print(f"  FORCE_NON_INTERACTIVE=true")
    print(f"  AUTO_SELECT_CLAUDE=true")
    print()
    
    try:
        result = subprocess.run(
            cmd,
            cwd=str(test_dir),
            text=True,
            timeout=300,  # 5 minutes
            env=env
        )
        
        print(f"Return code: {result.returncode}")
        return result.returncode == 0
        
    except subprocess.TimeoutExpired:
        print("❌ Timeout after 5 minutes")
        return False
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

if __name__ == "__main__":
    success = debug_run()
    print(f"\nResult: {'SUCCESS' if success else 'FAILURE'}")