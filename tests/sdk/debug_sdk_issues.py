#!/usr/bin/env python3
"""
Systematic debugging of additional SDK issues
Let's identify and fix each one
"""

import asyncio
import json
import subprocess
import time
from pathlib import Path
from claude_code_sdk_fixed import query, ClaudeCodeOptions

async def test_json_parsing_issue():
    """Test what causes JSON parsing errors"""
    print("=" * 80)
    print("DEBUGGING JSON PARSING ISSUES")
    print("=" * 80)
    
    # Test different prompt complexities to find the trigger
    test_cases = [
        ("simple", "Write 'hello' to simple.txt"),
        ("medium", "Create a Python script that prints hello world, then read it back"),
        ("complex", """Create a complete Python calculator with:
1. Basic arithmetic operations (+, -, *, /)
2. Error handling for division by zero
3. A main loop for user input
4. Comments explaining each function
Then test it by running a few calculations."""),
        ("very_complex", """Research and implement a complete web scraper that:
1. Uses requests to fetch HTML
2. Uses BeautifulSoup to parse content
3. Handles rate limiting and retries
4. Saves data to JSON files
5. Has proper error handling
6. Includes unit tests
Create all necessary files and run the tests.""")
    ]
    
    results = {}
    
    for test_name, prompt in test_cases:
        print(f"\nTesting {test_name} prompt...")
        print(f"Length: {len(prompt)} chars")
        
        options = ClaudeCodeOptions(
            max_turns=5,
            allowed_tools=["Write", "Read", "Bash"],
            permission_mode="bypassPermissions",
            cwd=str(Path.cwd())
        )
        
        try:
            start_time = time.time()
            message_count = 0
            last_message_type = None
            
            async for message in query(prompt=prompt, options=options):
                message_count += 1
                last_message_type = type(message).__name__
                
                # Stop after reasonable number to avoid long tests
                if message_count > 20:
                    break
                    
            duration = time.time() - start_time
            results[test_name] = {
                'success': True,
                'messages': message_count,
                'duration': duration,
                'last_type': last_message_type,
                'error': None
            }
            print(f"  ✅ Success: {message_count} messages in {duration:.1f}s")
            
        except Exception as e:
            duration = time.time() - start_time
            error_type = type(e).__name__
            error_msg = str(e)
            
            results[test_name] = {
                'success': False,
                'messages': message_count,
                'duration': duration,
                'last_type': last_message_type,
                'error': f"{error_type}: {error_msg}"
            }
            
            print(f"  ❌ Failed: {error_type}")
            
            # Categorize the error
            if "JSONDecodeError" in error_type:
                print(f"    JSON parsing issue at message {message_count}")
            elif "TaskGroup" in error_msg:
                print(f"    Async cleanup issue at message {message_count}")
            elif "timeout" in error_msg.lower():
                print(f"    Timeout issue after {duration:.1f}s")
            else:
                print(f"    Unknown issue: {error_msg[:100]}...")
    
    return results

async def test_subprocess_output():
    """Test if the issue is in subprocess communication"""
    print("\n" + "=" * 80)
    print("DEBUGGING SUBPROCESS COMMUNICATION")
    print("=" * 80)
    
    # Run Claude CLI directly and capture raw output
    cmd = [
        "claude", 
        "-p", "Create a simple Python script with error handling",
        "--output-format", "stream-json",
        "--max-turns", "3",
        "--dangerously-skip-permissions"
    ]
    
    print("Running Claude CLI directly...")
    print(f"Command: {' '.join(cmd)}")
    
    try:
        process = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )
        
        lines_captured = []
        json_errors = []
        valid_json_count = 0
        
        # Read output line by line like the SDK does
        for line_num, line in enumerate(process.stdout, 1):
            line = line.strip()
            if line:
                lines_captured.append((line_num, line))
                
                # Try to parse each line as JSON
                try:
                    data = json.loads(line)
                    valid_json_count += 1
                except json.JSONDecodeError as e:
                    json_errors.append({
                        'line': line_num,
                        'error': str(e),
                        'content': line[:200] + "..." if len(line) > 200 else line
                    })
        
        process.wait()
        
        print(f"\nResults:")
        print(f"  Total lines: {len(lines_captured)}")
        print(f"  Valid JSON lines: {valid_json_count}")
        print(f"  JSON errors: {len(json_errors)}")
        print(f"  Exit code: {process.returncode}")
        
        if json_errors:
            print(f"\nJSON parsing errors:")
            for error in json_errors[:3]:  # Show first 3 errors
                print(f"  Line {error['line']}: {error['error']}")
                print(f"    Content: {error['content']}")
                
        return {
            'total_lines': len(lines_captured),
            'valid_json': valid_json_count,
            'json_errors': len(json_errors),
            'exit_code': process.returncode,
            'first_errors': json_errors[:3]
        }
        
    except Exception as e:
        print(f"Subprocess test failed: {e}")
        return None

async def main():
    """Run all debugging tests"""
    print("COMPREHENSIVE SDK ISSUE DEBUGGING")
    print("This will help us identify and fix all SDK issues")
    print()
    
    # Test 1: JSON parsing with different complexities
    json_results = await test_json_parsing_issue()
    
    # Test 2: Direct subprocess communication
    subprocess_results = await test_subprocess_output()
    
    # Analysis
    print("\n" + "=" * 80)
    print("ANALYSIS")
    print("=" * 80)
    
    print("\nJSON Parsing Test Results:")
    for test_name, result in json_results.items():
        status = "✅" if result['success'] else "❌"
        print(f"  {status} {test_name}: {result['messages']} msgs, {result['duration']:.1f}s")
        if not result['success']:
            print(f"      Error: {result['error']}")
    
    if subprocess_results:
        print(f"\nSubprocess Communication:")
        print(f"  Lines captured: {subprocess_results['total_lines']}")
        print(f"  Valid JSON: {subprocess_results['valid_json']}")
        print(f"  JSON errors: {subprocess_results['json_errors']}")
        
        if subprocess_results['json_errors'] > 0:
            print(f"  ⚠️  JSON parsing issues detected at CLI level")
        else:
            print(f"  ✅ CLI output is valid JSON")
    
    # Determine root causes
    print(f"\nROOT CAUSE ANALYSIS:")
    
    # Pattern analysis
    failed_tests = [name for name, result in json_results.items() if not result['success']]
    
    if failed_tests:
        print(f"  Failed complexity levels: {failed_tests}")
        
        # Check if it's complexity-related
        if 'simple' in failed_tests:
            print(f"  🔍 Issue occurs even with simple prompts - likely core SDK bug")
        elif 'complex' in failed_tests or 'very_complex' in failed_tests:
            print(f"  🔍 Issue occurs with complex prompts - likely buffer/stream issue")
        
        # Check error patterns
        error_types = []
        for result in json_results.values():
            if result['error']:
                if "JSONDecodeError" in result['error']:
                    error_types.append("JSON parsing")
                elif "TaskGroup" in result['error']:
                    error_types.append("Async cleanup")
                elif "timeout" in result['error'].lower():
                    error_types.append("Timeout")
        
        if error_types:
            print(f"  📊 Error patterns: {set(error_types)}")
    else:
        print(f"  ✅ All tests passed - SDK might be working correctly")
    
    # Next steps
    print(f"\nNEXT STEPS FOR DEBUGGING:")
    if subprocess_results and subprocess_results['json_errors'] > 0:
        print(f"  1. Fix CLI output parsing (buffer issues)")
        print(f"  2. Improve JSON stream handling in SDK")
    
    if 'Async cleanup' in str(json_results):
        print(f"  3. Fix TaskGroup async cleanup issues")
    
    if failed_tests:
        print(f"  4. Test each fix incrementally")
    else:
        print(f"  4. SDK appears functional - ready for full CC_AUTOMATOR4 test")

if __name__ == "__main__":
    asyncio.run(main())