#!/usr/bin/env python3
"""
Test if Claude Code subagents can run in parallel
"""

import time
import subprocess
import json

# Create a test prompt that uses multiple Task tools in one response
test_prompt = """
Use the Task tool to launch 3 subagents simultaneously:

1. Task 1: Count from 1 to 5 slowly (sleep 1 second between each number)
2. Task 2: List all files in /tmp 
3. Task 3: Calculate 2+2

Launch all three tasks in a single response to test parallel execution.
"""

print("Testing parallel subagent execution...")
start = time.time()

result = subprocess.run([
    "claude", "-p", test_prompt,
    "--output-format", "json",
    "--dangerously-skip-permissions"
], capture_output=True, text=True, cwd="/tmp")

duration = time.time() - start

if result.returncode == 0:
    print(f"✓ Completed in {duration:.1f} seconds")
    
    # If tasks ran in parallel, total time should be ~5 seconds (dominated by Task 1)
    # If sequential, total time would be much longer
    
    if duration < 10:
        print("→ Likely PARALLEL execution (fast completion)")
    else:
        print("→ Likely SEQUENTIAL execution (slow completion)")
        
    # Parse and show the output
    data = json.loads(result.stdout)
    print(f"\nSession: {data.get('session_id', 'unknown')}")
else:
    print(f"✗ Failed: {result.stderr}")

print(f"\nTotal duration: {duration:.1f}s")