#!/usr/bin/env python3
"""
Comprehensive analysis of when TaskGroup errors occur
"""

import asyncio
import time
from claude_code_sdk_fixed import query, ClaudeCodeOptions
from pathlib import Path

async def test_taskgroup_conditions():
    """Test different conditions that might trigger TaskGroup errors"""
    
    print("TASKGROUP ERROR CONDITION ANALYSIS")
    print("=" * 60)
    
    test_cases = [
        ("minimal", "Write 'test' to test1.txt", 1, ["Write"]),
        ("normal", "Create a Python hello world script", 3, ["Write", "Read"]),
        ("complex", "Create and test a calculator with error handling", 5, ["Write", "Read", "Bash"]),
        ("multi_tool", "Research Python best practices and create a README", 5, ["Write", "Read", "WebSearch"])
    ]
    
    results = {}
    
    for test_name, prompt, max_turns, tools in test_cases:
        print(f"\nTesting: {test_name}")
        print(f"  Prompt: {prompt[:50]}...")
        print(f"  Max turns: {max_turns}, Tools: {tools}")
        
        try:
            options = ClaudeCodeOptions(
                max_turns=max_turns,
                allowed_tools=tools,
                permission_mode="bypassPermissions",
                cwd=str(Path.cwd())
            )
            
            start_time = time.time()
            messages = []
            work_done = False
            
            async for message in query(prompt=prompt, options=options):
                messages.append(type(message).__name__)
                if hasattr(message, 'total_cost_usd'):
                    work_done = True
            
            duration = time.time() - start_time
            
            results[test_name] = {
                'success': True,
                'messages': len(messages),
                'work_done': work_done,
                'duration': duration,
                'error': None,
                'error_type': None
            }
            
            print(f"  ✅ Success: {len(messages)} msgs, {duration:.1f}s")
            
        except Exception as e:
            duration = time.time() - start_time
            error_type = type(e).__name__
            
            results[test_name] = {
                'success': False,
                'messages': len(messages),
                'work_done': work_done,
                'duration': duration,
                'error': str(e)[:200],
                'error_type': error_type
            }
            
            print(f"  ❌ Failed: {error_type} after {len(messages)} msgs")
            
            # Analyze error type
            if "TaskGroup" in str(e) or "cancel scope" in str(e):
                print(f"    🔍 TaskGroup/async cleanup error")
            elif "JSONDecodeError" in str(e):
                print(f"    🔍 JSON parsing error")
            elif "cost_usd" in str(e):
                print(f"    🔍 Cost field error (should be fixed!)")
            else:
                print(f"    🔍 Other error: {str(e)[:50]}...")
    
    # Analysis
    print(f"\n" + "=" * 60)
    print("PATTERN ANALYSIS")
    print("=" * 60)
    
    successful = [name for name, result in results.items() if result['success']]
    failed = [name for name, result in results.items() if not result['success']]
    
    print(f"Successful: {successful}")
    print(f"Failed: {failed}")
    
    if failed:
        print(f"\nFailure patterns:")
        for name in failed:
            result = results[name]
            print(f"  {name}: {result['error_type']} after {result['messages']} messages")
            print(f"    Work done before error: {result['work_done']}")
    
    # TaskGroup specific analysis
    taskgroup_errors = [
        name for name, result in results.items() 
        if result['error'] and ("TaskGroup" in result['error'] or "cancel scope" in result['error'])
    ]
    
    if taskgroup_errors:
        print(f"\nTaskGroup errors in: {taskgroup_errors}")
        print(f"Pattern: These typically happen during async cleanup")
        
        for name in taskgroup_errors:
            result = results[name]
            print(f"  {name}: Work completed = {result['work_done']}")
    else:
        print(f"\n✅ No TaskGroup errors observed in this run")
        print(f"   (They may be intermittent or timing-dependent)")
    
    return results

if __name__ == "__main__":
    results = asyncio.run(test_taskgroup_conditions())
    
    # Summary
    print(f"\n" + "=" * 60)
    print("SUMMARY")
    print("=" * 60)
    
    total_tests = len(results)
    successful_tests = sum(1 for r in results.values() if r['success'])
    work_completed_despite_errors = sum(
        1 for r in results.values() 
        if not r['success'] and r['work_done']
    )
    
    print(f"Total tests: {total_tests}")
    print(f"Successful: {successful_tests}")
    print(f"Work done despite errors: {work_completed_despite_errors}")
    
    if work_completed_despite_errors > 0:
        print(f"\n🎯 KEY FINDING: Work completed even when cleanup failed")
        print(f"   This confirms TaskGroup errors are nuisance cleanup issues")
    
    if successful_tests == total_tests:
        print(f"\n🎉 All tests passed - SDK is working reliably!")
    elif successful_tests > 0:
        print(f"\n⚖️  Mixed results - SDK works but has intermittent cleanup issues")