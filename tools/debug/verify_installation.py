#!/usr/bin/env python3
"""
Verification script for CC_AUTOMATOR4 installation
"""

import os
import sys
from pathlib import Path

def verify_installation():
    """Verify CC_AUTOMATOR4 is properly set up"""
    
    print("CC_AUTOMATOR4 Installation Verification")
    print("=" * 50)
    
    # Check current directory
    current_dir = Path.cwd()
    print(f"✓ Current directory: {current_dir}")
    
    # Check critical files exist
    critical_files = [
        "run.py",
        "phase_orchestrator.py", 
        "phase_prompt_generator.py",
        "milestone_decomposer.py",
        "preflight_validator.py",
        "templates/CLAUDE_TEMPLATE.md",
        "HANDOFF.md",
        "README.md"
    ]
    
    all_good = True
    for file in critical_files:
        if Path(file).exists():
            print(f"✓ {file} exists")
        else:
            print(f"✗ {file} MISSING")
            all_good = False
            
    # Check no references to cc_automator3
    print("\nChecking for outdated references...")
    import subprocess
    result = subprocess.run(
        ["grep", "-r", "cc_automator3", ".", "--include=*.md", "--include=*.py", "--exclude-dir=archive", "--exclude=verify_installation.py"],
        capture_output=True, text=True
    )
    
    if result.stdout:
        print("✗ Found outdated cc_automator3 references:")
        print(result.stdout[:200])
        all_good = False
    else:
        print("✓ No outdated references found")
        
    # Check Python version
    print(f"\n✓ Python version: {sys.version.split()[0]}")
    
    # Summary
    print("\n" + "=" * 50)
    if all_good:
        print("✓ CC_AUTOMATOR4 is ready for use!")
        print("\nNext steps:")
        print("1. Move to home directory: cp -r . ~/cc_automator4")
        print("2. Test with: python run.py --project ../test_calculator_fresh --milestone 1")
    else:
        print("✗ Some issues found - please fix before proceeding")
        
    return all_good

if __name__ == "__main__":
    verify_installation()