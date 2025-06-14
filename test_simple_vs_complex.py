#!/usr/bin/env python3
"""
Test to compare simple vs complex prompts for calculator
"""

import subprocess
import time
import json
from pathlib import Path
from simple_prompts import get_simple_prompt

def test_simple_research():
    """Test simple research prompt"""
    prompt = get_simple_prompt("research", "Basic arithmetic operations")
    
    start = time.time()
    
    # Run with simple prompt
    result = subprocess.run([
        "claude", "-p", prompt,
        "--output-format", "json",
        "--max-turns", "10",
        "--dangerously-skip-permissions"
    ], capture_output=True, text=True, cwd="/home/brian/autocoder2_cc/test_calculator")
    
    duration = time.time() - start
    
    print(f"Simple research took: {duration:.1f} seconds")
    
    if result.returncode == 0:
        data = json.loads(result.stdout)
        print(f"Session ID: {data.get('session_id', 'unknown')}")
        print(f"Cost: ${data.get('cost_usd', 0):.4f}")
    else:
        print(f"Error: {result.stderr}")

if __name__ == "__main__":
    print("Testing simple prompts for calculator...")
    test_simple_research()