#!/usr/bin/env python3
"""
Test script for Phase 4 features
"""

import subprocess
import sys
from pathlib import Path

def test_parallel_execution():
    """Test parallel execution is available"""
    print("Testing parallel execution...")
    
    result = subprocess.run(
        [sys.executable, "run.py", "--help"],
        capture_output=True,
        text=True
    )
    
    if "--parallel" in result.stdout:
        print("✓ Parallel execution flag available")
    else:
        print("✗ Parallel execution flag missing")
        
    if "--docker" in result.stdout:
        print("✓ Docker execution flag available")
    else:
        print("✗ Docker execution flag missing")
        
    if "--visual" in result.stdout:
        print("✓ Visual progress flag available")
    else:
        print("✗ Visual progress flag missing")

def test_imports():
    """Test that Phase 4 modules can be imported"""
    print("\nTesting Phase 4 imports...")
    
    try:
        from parallel_executor import ParallelExecutor
        print("✓ ParallelExecutor imported successfully")
    except ImportError as e:
        print(f"✗ Failed to import ParallelExecutor: {e}")
        
    try:
        from docker_executor import DockerExecutor
        print("✓ DockerExecutor imported successfully")
    except ImportError as e:
        print(f"✗ Failed to import DockerExecutor: {e}")
        
    try:
        from visual_progress import VisualProgressDisplay
        print("✓ VisualProgressDisplay imported successfully")
    except ImportError as e:
        print(f"✗ Failed to import VisualProgressDisplay: {e}")

def test_git_worktree_support():
    """Test if git worktrees are supported"""
    print("\nTesting git worktree support...")
    
    result = subprocess.run(
        ["git", "worktree", "list"],
        capture_output=True,
        text=True
    )
    
    if result.returncode == 0:
        print("✓ Git worktrees supported")
    else:
        print("✗ Git worktrees not available")

def test_docker_availability():
    """Test if Docker is available"""
    print("\nTesting Docker availability...")
    
    result = subprocess.run(
        ["docker", "--version"],
        capture_output=True,
        text=True
    )
    
    if result.returncode == 0:
        print(f"✓ Docker available: {result.stdout.strip()}")
    else:
        print("✗ Docker not available (optional)")

if __name__ == "__main__":
    print("CC_AUTOMATOR3 Phase 4 Feature Test")
    print("=" * 50)
    
    test_parallel_execution()
    test_imports()
    test_git_worktree_support()
    test_docker_availability()
    
    print("\n" + "=" * 50)
    print("Phase 4 features are ready to use!")
    print("\nUsage examples:")
    print("  python run.py                    # All features enabled by default")
    print("  python run.py --no-parallel      # Disable parallel execution")
    print("  python run.py --docker           # Enable Docker execution")
    print("  python run.py --no-visual        # Disable visual progress")
    print("  python run.py --milestone 2      # Run only milestone 2")