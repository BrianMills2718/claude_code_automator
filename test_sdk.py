#!/usr/bin/env python3
"""Simple test to verify SDK file writing works"""

import asyncio
from pathlib import Path
from claude_code_sdk import query, ClaudeCodeOptions

async def test_sdk_write():
    """Test if SDK can write a simple file"""
    
    # Clean test directory
    test_dir = Path("test_sdk_output")
    if test_dir.exists():
        import shutil
        shutil.rmtree(test_dir)
    test_dir.mkdir()
    
    # Simple prompt to write a file
    prompt = """Please write a file called test.md in the test_sdk_output directory with the content:
# Test File
This is a test file created by the SDK.
"""
    
    options = ClaudeCodeOptions(
        max_turns=5,
        allowed_tools=["Write"],
        cwd=str(Path.cwd()),
        permission_mode="bypassPermissions"
    )
    
    print("Starting SDK test...")
    messages = []
    
    try:
        async for message in query(prompt=prompt, options=options):
            messages.append(message)
            print(f"Received message type: {type(message)}")
        
        print(f"\nTotal messages: {len(messages)}")
        
        # Check if file was created
        test_file = test_dir / "test.md"
        if test_file.exists():
            print(f"✓ Success! File created: {test_file}")
            print(f"Content: {test_file.read_text()}")
        else:
            print("✗ Failed - file not created")
            
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_sdk_write())