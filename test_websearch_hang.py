#!/usr/bin/env python3
"""Test if WebSearch hangs by using it in isolation."""

import asyncio
import time
from claude_code_sdk import query, ClaudeCodeOptions

async def test_websearch_hang():
    """Test WebSearch with a simple query to see if it hangs."""
    
    print("Testing WebSearch hang behavior...")
    print("This test will timeout after 60 seconds if WebSearch hangs")
    
    prompt = """Use WebSearch to find the current version of FastAPI.
Just search for "FastAPI current version 2024" and report what you find.
This should take less than 30 seconds."""
    
    start_time = time.time()
    
    try:
        message_count = 0
        async for message in query(
            prompt=prompt,
            options=ClaudeCodeOptions(
                max_turns=5,
                permission_mode='bypassPermissions'
            )
        ):
            message_count += 1
            elapsed = time.time() - start_time
            print(f"Message {message_count} at {elapsed:.1f}s: {type(message).__name__}")
            
            # Log WebSearch tool usage
            if hasattr(message, 'content') and isinstance(message.content, list):
                for item in message.content:
                    if hasattr(item, 'name') and item.name == 'WebSearch':
                        print(f"🔍 WebSearch detected: {item.input}")
                        
            # Safety timeout
            if elapsed > 60:
                print("❌ Test timeout after 60 seconds - WebSearch likely hung")
                return False
                
        duration = time.time() - start_time
        print(f"✅ WebSearch completed in {duration:.1f}s")
        return True
        
    except Exception as e:
        duration = time.time() - start_time
        print(f"❌ Error after {duration:.1f}s: {e}")
        return False

async def main():
    print("WebSearch Hang Test")
    print("=" * 40)
    
    # Test if WebSearch hangs
    success = await test_websearch_hang()
    
    if success:
        print("\n✅ WebSearch works properly - not the cause of timeouts")
    else:
        print("\n❌ WebSearch hangs - this explains the 10+ minute timeouts")
        print("   Solution: Either fix WebSearch or disable it for research phase")

if __name__ == "__main__":
    asyncio.run(main())