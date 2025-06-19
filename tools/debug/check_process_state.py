#!/usr/bin/env python3
"""
Simple check of process state after SDK usage
"""

import psutil
import os
import asyncio
from claude_code_sdk_fixed import query, ClaudeCodeOptions
from pathlib import Path

def show_process_info(label):
    """Show current process information"""
    process = psutil.Process(os.getpid())
    
    print(f"{label}:")
    print(f"  Memory: {process.memory_info().rss / 1024 / 1024:.1f} MB")
    print(f"  Open files: {len(process.open_files())}")
    print(f"  Threads: {process.num_threads()}")
    
    # Show child processes
    children = process.children(recursive=True)
    if children:
        print(f"  Child processes: {len(children)}")
        for child in children[:3]:  # Show first 3
            try:
                print(f"    - PID {child.pid}: {child.name()}")
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                print(f"    - PID {child.pid}: <terminated>")
    else:
        print(f"  Child processes: 0")

async def test_single_call():
    """Test one SDK call and check process state"""
    
    print("PROCESS STATE TEST")
    print("=" * 40)
    
    show_process_info("Before SDK call")
    
    try:
        options = ClaudeCodeOptions(
            max_turns=1,
            allowed_tools=["Write"],
            permission_mode="bypassPermissions",
            cwd=str(Path.cwd())
        )
        
        print("\nMaking SDK call...")
        async for message in query(prompt="Write 'test' to state_test.txt", options=options):
            pass
            
        print("SDK call completed")
        
    except Exception as e:
        print(f"SDK call failed: {type(e).__name__}")
    
    print()
    show_process_info("After SDK call")
    
    # Check if test file was created
    test_file = Path("state_test.txt")
    if test_file.exists():
        print(f"\n✅ File created successfully")
        test_file.unlink()
    else:
        print(f"\n❌ File not created")

if __name__ == "__main__":
    asyncio.run(test_single_call())