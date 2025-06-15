#!/usr/bin/env python3
"""Test async execution with completion markers"""

import subprocess
import time
from pathlib import Path

# Setup
marker_dir = Path(".cc_automator")
marker_dir.mkdir(exist_ok=True)
completion_marker = marker_dir / "test_complete"
completion_marker.unlink(missing_ok=True)

# Simple prompt
prompt = f"""Create a file called hello.txt with content 'Hello World'.

When done, create file: {completion_marker}
Write to it: PHASE_COMPLETE"""

# Run Claude
cmd = [
    "claude", "-p", prompt,
    "--dangerously-skip-permissions",
    "--output-format", "json",
    "--max-turns", "10"
]

print("Starting Claude...")
process = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)

# Poll for completion
for i in range(20):  # 20 seconds max
    time.sleep(1)
    
    if process.poll() is not None:
        stdout, stderr = process.communicate()
        print(f"\nProcess exited with code {process.returncode}")
        print(f"STDOUT: {stdout}")
        print(f"STDERR: {stderr}")
        break
        
    if completion_marker.exists():
        print(f"\n✓ Completion marker found after {i+1} seconds!")
        process.terminate()
        break
        
    print(".", end="", flush=True)
else:
    print("\n✗ Timeout!")
    process.terminate()

# Check results
if Path("hello.txt").exists():
    print("✓ hello.txt created")
else:
    print("✗ hello.txt not created")
    
if completion_marker.exists():
    print(f"✓ Marker content: {completion_marker.read_text()}")
else:
    print("✗ Completion marker not created")