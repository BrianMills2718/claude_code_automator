#!/usr/bin/env python3
"""
Test script to demonstrate adaptive polling behavior
"""

import subprocess
import time
import threading
from pathlib import Path

def monitor_completion_markers(project_dir):
    """Monitor for completion markers and print when found"""
    markers_dir = project_dir / ".cc_automator"
    
    print("\nMonitoring for completion markers...")
    start_time = time.time()
    
    while True:
        # Check for any completion markers
        markers = list(markers_dir.glob("phase_*_complete"))
        if markers:
            for marker in markers:
                elapsed = time.time() - start_time
                print(f"\n✓ Found {marker.name} after {elapsed:.1f}s")
                return
        time.sleep(1)

def run_test():
    """Run test to show adaptive polling"""
    project_dir = Path("test_adaptive")
    
    # Start monitoring in background thread
    monitor_thread = threading.Thread(target=monitor_completion_markers, args=(project_dir,))
    monitor_thread.daemon = True
    monitor_thread.start()
    
    # Run the automator
    print("Starting CC_AUTOMATOR3 with verbose output...")
    print("Watch for adaptive polling intervals (5s → 7.5s → 11.25s → ... → 30s max)")
    print("-" * 60)
    
    cmd = [
        "python", "cli.py",
        "--project", "test_adaptive",
        "--milestone", "1",
        "--verbose",
        "--no-parallel"
    ]
    
    process = subprocess.Popen(
        cmd,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        bufsize=1
    )
    
    # Stream output
    for line in process.stdout:
        print(line, end='')
        
        # Highlight polling messages
        if "Phase research running..." in line:
            # Extract the elapsed time from the message
            try:
                elapsed_part = line.split("(")[1].split("s")[0]
                elapsed = int(elapsed_part)
                print(f"  → Polling interval will be: {min(elapsed * 1.5, 30):.1f}s", end='')
            except:
                pass
    
    process.wait()

if __name__ == "__main__":
    run_test()