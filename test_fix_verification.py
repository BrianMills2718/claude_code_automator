#!/usr/bin/env python3
"""Verify the context bug fix is working"""

import subprocess
import time
from pathlib import Path

def run_test_phases():
    """Run research and planning phases to verify no infinite loops"""
    
    print("Testing context bug fix...")
    print("=" * 60)
    
    # Run research phase
    print("\n1. Running RESEARCH phase...")
    start_time = time.time()
    
    result = subprocess.run([
        "python", "../cli.py", 
        "--project", ".",
        "--milestone", "1"
    ], 
    cwd="test_example",
    capture_output=True,
    text=True,
    timeout=300  # 5 minute timeout
    )
    
    duration = time.time() - start_time
    
    # Check for the error in logs
    research_logs = list(Path("test_example/.cc_automator/logs").glob("research_*.log"))
    planning_logs = list(Path("test_example/.cc_automator/logs").glob("planning_*.log"))
    
    error_count = 0
    for log_file in research_logs + planning_logs:
        content = log_file.read_text()
        error_count += content.count("File has not been read yet")
    
    print(f"\nResults:")
    print(f"- Duration: {duration:.1f}s")
    print(f"- 'File has not been read yet' errors: {error_count}")
    print(f"- Research phase files: {len(research_logs)}")
    print(f"- Planning phase files: {len(planning_logs)}")
    
    # Check milestone files
    milestone_dir = Path("test_example/.cc_automator/milestones/milestone_1")
    if milestone_dir.exists():
        files = list(milestone_dir.glob("*.md"))
        print(f"- Milestone files created: {len(files)}")
        for f in files:
            print(f"  - {f.name}: {f.stat().st_size} bytes")
    
    if error_count == 0:
        print("\n✅ SUCCESS: No 'File has not been read yet' errors!")
        print("The context bug fix is working correctly.")
    else:
        print(f"\n❌ FAILURE: Found {error_count} errors")
        print("The bug may not be fully fixed.")
    
    return error_count == 0

if __name__ == "__main__":
    success = run_test_phases()
    exit(0 if success else 1)