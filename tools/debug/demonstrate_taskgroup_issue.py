#!/usr/bin/env python3
"""
Demonstrate that TaskGroup error doesn't affect actual results
"""

import asyncio
from claude_code_sdk_fixed import query, ClaudeCodeOptions
from pathlib import Path

async def capture_work_vs_cleanup():
    """Show that work succeeds before cleanup fails"""
    
    print("DEMONSTRATING TASKGROUP ISSUE")
    print("=" * 50)
    
    options = ClaudeCodeOptions(
        max_turns=2,
        allowed_tools=["Write"],
        permission_mode="bypassPermissions", 
        cwd=str(Path.cwd())
    )
    
    # Track what happens during execution vs cleanup
    messages_received = []
    work_completed = False
    cleanup_error = None
    
    try:
        print("Starting SDK query...")
        
        async for message in query(prompt="Write 'success' to demo.txt", options=options):
            msg_type = type(message).__name__
            messages_received.append(msg_type)
            print(f"  ✅ Received: {msg_type}")
            
            # Check for completion
            if hasattr(message, 'total_cost_usd'):
                work_completed = True
                print(f"  ✅ Work completed with cost: ${message.total_cost_usd:.4f}")
        
        print("  ✅ All messages processed successfully")
        
    except Exception as e:
        # This is where we catch the cleanup error
        cleanup_error = str(e)
        print(f"  ❌ Exception during cleanup: {type(e).__name__}")
        
        if "TaskGroup" in str(e):
            print("  🔍 This is the TaskGroup cleanup error")
        elif "cancel scope" in str(e):
            print("  🔍 This is the async context cleanup error")
    
    # Check if actual work was done despite the error
    demo_file = Path("demo.txt")
    file_created = demo_file.exists()
    file_content = ""
    
    if file_created:
        file_content = demo_file.read_text().strip()
        demo_file.unlink()  # cleanup
    
    # Results
    print("\n" + "=" * 50)
    print("RESULTS ANALYSIS")
    print("=" * 50)
    
    print(f"Messages received: {len(messages_received)}")
    for i, msg_type in enumerate(messages_received, 1):
        print(f"  {i}. {msg_type}")
    
    print(f"\nWork completed: {'✅ YES' if work_completed else '❌ NO'}")
    print(f"File created: {'✅ YES' if file_created else '❌ NO'}")
    if file_created:
        print(f"File content: '{file_content}'")
    
    print(f"Cleanup error: {'❌ YES' if cleanup_error else '✅ NO'}")
    if cleanup_error:
        print(f"  Error type: {cleanup_error[:100]}...")
    
    # The key insight
    print(f"\n" + "=" * 50)
    print("KEY INSIGHT")
    print("=" * 50)
    
    if work_completed and file_created and cleanup_error:
        print("🎯 WORK SUCCEEDED BUT CLEANUP FAILED")
        print("   - All messages were processed")
        print("   - File was created correctly")
        print("   - Cost was tracked")
        print("   - Only the cleanup phase had an error")
        print("   - This proves the TaskGroup error is a nuisance")
    elif not cleanup_error:
        print("✅ NO CLEANUP ERROR - SDK worked perfectly")
    else:
        print("❌ REAL FAILURE - work didn't complete")

if __name__ == "__main__":
    asyncio.run(capture_work_vs_cleanup())