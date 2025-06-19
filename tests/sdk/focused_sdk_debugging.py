#!/usr/bin/env python3
"""
Focused debugging of specific SDK issues observed
"""

import asyncio
import sys
from claude_code_sdk_fixed import query, ClaudeCodeOptions
from pathlib import Path

async def test_specific_issues():
    """Test specific SDK issues we've identified"""
    
    print("FOCUSED SDK ISSUE DEBUGGING")
    print("=" * 50)
    
    issues_tested = {
        'cost_tracking': False,
        'basic_functionality': False,
        'json_parsing': True,  # Assume this will fail
        'task_group_cleanup': True  # Assume this will fail
    }
    
    # Test 1: Basic functionality (this should work with our fix)
    print("\n1. Testing basic functionality...")
    try:
        options = ClaudeCodeOptions(
            max_turns=3,
            allowed_tools=["Write"],
            permission_mode="bypassPermissions",
            cwd=str(Path.cwd())
        )
        
        message_count = 0
        cost_received = False
        
        async for message in query(
            prompt="Create a file called basic_test.txt with content 'Basic test works'",
            options=options
        ):
            message_count += 1
            if hasattr(message, 'total_cost_usd') and message.total_cost_usd > 0:
                cost_received = True
                issues_tested['cost_tracking'] = True
                print(f"   ✅ Cost tracked: ${message.total_cost_usd:.4f}")
        
        if message_count > 0:
            issues_tested['basic_functionality'] = True
            print(f"   ✅ Basic functionality: {message_count} messages")
        
        # Check file creation
        test_file = Path("basic_test.txt")
        if test_file.exists():
            print(f"   ✅ File created successfully")
            test_file.unlink()  # cleanup
            issues_tested['json_parsing'] = False  # If we got here, JSON parsing worked
            
    except Exception as e:
        print(f"   ❌ Basic test failed: {type(e).__name__}: {str(e)[:100]}")
        
        # Categorize the error
        if "JSONDecodeError" in str(e):
            print("   🔍 JSON parsing issue confirmed")
        elif "TaskGroup" in str(e):
            print("   🔍 TaskGroup cleanup issue confirmed")
            issues_tested['task_group_cleanup'] = False
    
    # Test 2: Simple prompt that should minimize issues
    print("\n2. Testing minimal prompt...")
    try:
        options = ClaudeCodeOptions(
            max_turns=1,  # Minimal turns
            allowed_tools=["Write"],  # Single tool
            permission_mode="bypassPermissions",
            cwd=str(Path.cwd())
        )
        
        msg_count = 0
        async for message in query(prompt="Write 'minimal' to min.txt", options=options):
            msg_count += 1
            if msg_count >= 5:  # Prevent infinite loops
                break
                
        print(f"   ✅ Minimal test: {msg_count} messages")
        
        min_file = Path("min.txt")
        if min_file.exists():
            print(f"   ✅ Minimal file created")
            min_file.unlink()
            
    except Exception as e:
        print(f"   ❌ Minimal test failed: {type(e).__name__}")
    
    # Summary
    print("\n" + "=" * 50)
    print("ISSUE STATUS SUMMARY")
    print("=" * 50)
    
    for issue, resolved in issues_tested.items():
        status = "✅ RESOLVED" if resolved else "❌ UNRESOLVED"
        print(f"{status}: {issue}")
    
    # Specific recommendations
    print(f"\nRECOMMENDATIONS:")
    
    unresolved = [issue for issue, resolved in issues_tested.items() if not resolved]
    
    if not unresolved:
        print("🎉 ALL ISSUES RESOLVED - SDK IS FULLY FUNCTIONAL")
        print("   Ready for full CC_AUTOMATOR4 integration")
    else:
        print(f"Issues to address: {unresolved}")
        
        if 'json_parsing' in unresolved:
            print("   1. JSON parsing: SDK stream parser needs buffer fix")
            print("      - Likely in subprocess_cli.py receive_messages()")
        
        if 'task_group_cleanup' in unresolved:
            print("   2. TaskGroup cleanup: Async context issue")
            print("      - Likely in anyio task group management")
        
        if 'cost_tracking' in unresolved:
            print("   3. Cost tracking: Field mapping issue")
            print("      - Should be fixed by our wrapper")
        
        if 'basic_functionality' in unresolved:
            print("   4. Basic functionality: Core SDK broken")
            print("      - May need CLI fallback for now")
    
    return issues_tested

if __name__ == "__main__":
    results = asyncio.run(test_specific_issues())
    
    # Exit with success if cost tracking and basic functionality work
    critical_issues = ['cost_tracking', 'basic_functionality']
    success = all(results.get(issue, False) for issue in critical_issues)
    
    print(f"\nCRITICAL ISSUES STATUS: {'✅ RESOLVED' if success else '❌ UNRESOLVED'}")
    sys.exit(0 if success else 1)