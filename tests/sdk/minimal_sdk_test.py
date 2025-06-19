#!/usr/bin/env python3
"""
Minimal SDK test to isolate the hanging issue
"""

import asyncio
import signal
import sys

def timeout_handler(signum, frame):
    print("TIMEOUT: SDK call took too long")
    sys.exit(1)

async def minimal_test():
    print("Testing minimal SDK call...")
    
    # Set a timeout
    signal.signal(signal.SIGALRM, timeout_handler)
    signal.alarm(10)  # 10 second timeout
    
    try:
        from claude_code_sdk import query, ClaudeCodeOptions
        
        # Absolutely minimal options
        options = ClaudeCodeOptions()
        
        print("Starting query...")
        msg_count = 0
        
        async for message in query(prompt="Hello", options=options):
            msg_count += 1
            print(f"Message {msg_count}: {type(message).__name__}")
            
            if msg_count >= 3:  # Stop early
                break
                
        signal.alarm(0)  # Cancel timeout
        print(f"✅ Success: {msg_count} messages")
        return True
        
    except Exception as e:
        signal.alarm(0)
        print(f"❌ Error: {type(e).__name__}: {e}")
        return False

if __name__ == "__main__":
    success = asyncio.run(minimal_test())
    print(f"Result: {'SUCCESS' if success else 'FAILED'}")