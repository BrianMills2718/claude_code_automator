#!/usr/bin/env python3
"""Simplified test to check if sub-phases can work."""

import asyncio
from pathlib import Path
from claude_code_sdk import query, ClaudeCodeOptions

async def test_simple_subphase():
    """Test a single simple sub-phase that should complete quickly."""
    
    test_dir = Path("test_simple_subphase")
    test_dir.mkdir(exist_ok=True)
    
    # Create a simple input file
    input_file = test_dir / "input.txt"
    input_file.write_text("Prime numbers: 2, 3, 5, 7, 11")
    
    # Simple focused prompt
    prompt = f"""Working directory: {test_dir.absolute()}

Read input.txt and create output.txt with the sum of all numbers found.
This is a simple focused task - just read, calculate sum, and write."""
    
    print("Starting simple sub-phase test...")
    start_time = asyncio.get_event_loop().time()
    
    try:
        message_count = 0
        async for message in query(
            prompt=prompt,
            options=ClaudeCodeOptions(max_turns=10)
        ):
            message_count += 1
            print(f"Message {message_count}: {type(message).__name__}")
            
        duration = asyncio.get_event_loop().time() - start_time
        print(f"\nCompleted in {duration:.1f}s with {message_count} messages")
        
        # Check output
        output_file = test_dir / "output.txt"
        if output_file.exists():
            print(f"✓ Output created: {output_file.read_text()}")
            return True
        else:
            print("✗ Output file not created")
            return False
            
    except Exception as e:
        print(f"Error: {e}")
        return False

async def test_with_tools_approved():
    """Test with pre-approved tools."""
    test_dir = Path("test_approved_tools")
    test_dir.mkdir(exist_ok=True)
    
    prompt = f"""Working directory: {test_dir.absolute()}

Create a file called test.txt with content 'Hello from sub-phase!'

You have permission to use these tools: Read, Write, Bash"""
    
    print("\nTesting with approved tools...")
    
    try:
        async for message in query(
            prompt=prompt,
            options=ClaudeCodeOptions(
                max_turns=5,
                approved_tools=["Read", "Write", "Bash"]  # Pre-approve tools
            )
        ):
            if hasattr(message, 'content'):
                print(f"Claude: {str(message.content)[:100]}...")
                
        # Check result
        test_file = test_dir / "test.txt"
        if test_file.exists():
            print(f"✓ File created: {test_file.read_text()}")
            return True
        else:
            print("✗ File not created")
            return False
            
    except Exception as e:
        print(f"Error: {e}")
        # Check if approved_tools is not supported
        if "approved_tools" in str(e):
            print("Note: approved_tools parameter not supported in SDK")
        return False

async def main():
    print("Testing sub-phase approach for timeout avoidance\n")
    
    # Test 1: Simple task
    result1 = await test_simple_subphase()
    
    # Test 2: With tool approval
    result2 = await test_with_tools_approved()
    
    print(f"\nResults:")
    print(f"Simple sub-phase: {'PASSED' if result1 else 'FAILED'}")
    print(f"Approved tools: {'PASSED' if result2 else 'FAILED'}")

if __name__ == "__main__":
    asyncio.run(main())