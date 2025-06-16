#!/usr/bin/env python3
"""Minimal test to reproduce TaskGroup error with WebSearch"""

import asyncio
from claude_code_sdk import query, ClaudeCodeOptions

async def test_websearch():
    """Test WebSearch to see if it causes TaskGroup errors"""
    
    prompt = """Use WebSearch to find information about Python asyncio TaskGroup errors.
    
    After searching, write a summary to websearch_test.md"""
    
    print("Starting WebSearch test...")
    
    try:
        message_count = 0
        async for message in query(
            prompt=prompt,
            options=ClaudeCodeOptions(max_turns=5)
        ):
            message_count += 1
            print(f"Message {message_count}: {type(message).__name__}")
            
            if hasattr(message, 'content'):
                content_str = str(message.content)[:200]
                print(f"  Content: {content_str}...")
            elif hasattr(message, 'text'):
                print(f"  Text: {message.text[:200]}...")
                
        print(f"\nCompleted successfully with {message_count} messages")
        
    except Exception as e:
        print(f"\nError occurred: {type(e).__name__}: {e}")
        
        # Check for TaskGroup in error
        if "TaskGroup" in str(e):
            print("\n*** This is the TaskGroup error we're looking for! ***")
            print(f"Full error: {e}")

if __name__ == "__main__":
    asyncio.run(test_websearch())