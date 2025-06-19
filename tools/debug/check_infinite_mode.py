#!/usr/bin/env python3
"""
Check Infinite Mode Implementation
Validates that --infinite flag properly removes all limits
"""

import re
import sys
from pathlib import Path

def check_file_for_limits(file_path: Path) -> list:
    """Check a file for hardcoded limits that might not respect infinite mode"""
    issues = []
    
    with open(file_path, 'r') as f:
        lines = f.readlines()
    
    for line_num, line in enumerate(lines, 1):
        # Check for hardcoded numeric limits
        if re.search(r'max_\w+\s*=\s*\d+', line) and 'infinite_mode' not in line:
            issues.append(f"{file_path}:{line_num} - Hardcoded limit: {line.strip()}")
        
        # Check for while loops with numeric comparisons
        if re.search(r'while\s+\w+\s*<\s*\d+', line) and 'infinite_mode' not in line:
            issues.append(f"{file_path}:{line_num} - Hardcoded loop limit: {line.strip()}")
        
        # Check for range with hardcoded values
        if re.search(r'for\s+\w+\s+in\s+range\(\d+\)', line):
            issues.append(f"{file_path}:{line_num} - Hardcoded range: {line.strip()}")
        
        # Check for timeout values
        if re.search(r'timeout\w*\s*=\s*\d+', line, re.IGNORECASE) and 'infinite_mode' not in line:
            issues.append(f"{file_path}:{line_num} - Hardcoded timeout: {line.strip()}")
        
        # Check for retry/attempt limits
        if re.search(r'(retry|attempt)\w*\s*[<>=]+\s*\d+', line, re.IGNORECASE) and 'infinite_mode' not in line:
            issues.append(f"{file_path}:{line_num} - Hardcoded retry limit: {line.strip()}")
    
    return issues

def check_infinite_mode_propagation(src_dir: Path) -> list:
    """Check that infinite_mode is properly propagated through the system"""
    issues = []
    
    # Files that should accept infinite_mode parameter
    files_should_accept = [
        'orchestrator.py',
        'phase_orchestrator.py', 
        'file_parallel_executor.py'
    ]
    
    for file_name in files_should_accept:
        file_path = src_dir / file_name
        if file_path.exists():
            with open(file_path, 'r') as f:
                content = f.read()
            
            # Check __init__ accepts infinite_mode
            if not re.search(r'def __init__.*infinite_mode', content):
                issues.append(f"{file_path} - __init__ doesn't accept infinite_mode parameter")
            
            # Check it's stored as instance variable
            if not re.search(r'self\.infinite_mode\s*=', content):
                issues.append(f"{file_path} - infinite_mode not stored as instance variable")
    
    return issues

def check_phase_configs(src_dir: Path) -> list:
    """Check PHASE_CONFIGS for hardcoded turn limits"""
    issues = []
    
    phase_orchestrator = src_dir / 'phase_orchestrator.py'
    if phase_orchestrator.exists():
        with open(phase_orchestrator, 'r') as f:
            content = f.read()
        
        # Find PHASE_CONFIGS definition
        phase_configs_match = re.search(r'PHASE_CONFIGS\s*=\s*\[(.*?)\]', content, re.DOTALL)
        if phase_configs_match:
            configs = phase_configs_match.group(1)
            # Each config line has format: ("phase_name", "desc", [...], None, TURN_LIMIT)
            for match in re.finditer(r'\("(\w+)".*?,\s*(\d+)\s*\)', configs):
                phase_name = match.group(1)
                turn_limit = match.group(2)
                issues.append(f"PHASE_CONFIGS - {phase_name} has hardcoded {turn_limit} turn limit")
    
    return issues

def main():
    """Main checking function"""
    project_root = Path(__file__).parent.parent.parent
    src_dir = project_root / 'src'
    
    print("Checking Infinite Mode Implementation...")
    print("=" * 60)
    
    all_issues = []
    
    # Check propagation
    print("\n1. Checking infinite_mode parameter propagation:")
    propagation_issues = check_infinite_mode_propagation(src_dir)
    if propagation_issues:
        for issue in propagation_issues:
            print(f"  ❌ {issue}")
        all_issues.extend(propagation_issues)
    else:
        print("  ✅ All key files accept and store infinite_mode")
    
    # Check PHASE_CONFIGS
    print("\n2. Checking PHASE_CONFIGS for hardcoded limits:")
    config_issues = check_phase_configs(src_dir)
    if config_issues:
        for issue in config_issues:
            print(f"  ❌ {issue}")
        all_issues.extend(config_issues)
    else:
        print("  ✅ No hardcoded limits in PHASE_CONFIGS")
    
    # Check all Python files for potential limit issues
    print("\n3. Checking all files for hardcoded limits:")
    file_issues = []
    for py_file in src_dir.glob('*.py'):
        issues = check_file_for_limits(py_file)
        file_issues.extend(issues)
    
    if file_issues:
        # Filter out known OK patterns
        filtered_issues = []
        for issue in file_issues:
            # Skip if it's already handling infinite_mode nearby
            if 'infinite_mode' in issue:
                continue
            # Skip test configurations and constants
            if 'test' in issue.lower() or 'TEST' in issue:
                continue
            filtered_issues.append(issue)
        
        if filtered_issues:
            for issue in filtered_issues[:10]:  # Show first 10
                print(f"  ⚠️  {issue}")
            if len(filtered_issues) > 10:
                print(f"  ... and {len(filtered_issues) - 10} more")
            all_issues.extend(filtered_issues)
        else:
            print("  ✅ No concerning hardcoded limits found")
    else:
        print("  ✅ No hardcoded limits found")
    
    # Summary
    print("\n" + "=" * 60)
    if all_issues:
        print(f"❌ Found {len(all_issues)} potential issues with infinite mode implementation")
        print("\nRecommendation: Review infinite_mode_gaps.md for detailed fixes")
        return 1
    else:
        print("✅ Infinite mode appears to be properly implemented!")
        return 0

if __name__ == "__main__":
    sys.exit(main())