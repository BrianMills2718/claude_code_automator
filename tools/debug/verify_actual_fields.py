#!/usr/bin/env python3
"""
Verify what fields are actually returned by Claude CLI
"""

import subprocess
import json

# Create a test file first
with open('temp_test.txt', 'w') as f:
    f.write('exists')

# Run Claude CLI directly and capture result message
cmd = [
    "claude", 
    "-p", "Read temp_test.txt",
    "--output-format", "json",
    "--max-turns", "2",
    "--dangerously-skip-permissions"
]

print("Running Claude CLI to capture actual field names...")
result = subprocess.run(cmd, capture_output=True, text=True)

if result.returncode == 0:
    try:
        data = json.loads(result.stdout)
        print("\nActual fields in result:")
        for key in sorted(data.keys()):
            print(f"  - {key}: {type(data[key]).__name__}")
        
        # Check for cost fields
        cost_fields = [k for k in data.keys() if 'cost' in k.lower()]
        print(f"\nCost fields present: {cost_fields}")
        
        # Show the exact values
        if 'cost_usd' in data:
            print(f"  cost_usd: {data['cost_usd']}")
        if 'total_cost_usd' in data:
            print(f"  total_cost_usd: {data['total_cost_usd']}")
        if 'total_cost' in data:
            print(f"  total_cost: {data['total_cost']}")
            
    except json.JSONDecodeError as e:
        print(f"Failed to parse JSON: {e}")
else:
    print(f"Command failed: {result.stderr}")

# Clean up
import os
os.remove('temp_test.txt')