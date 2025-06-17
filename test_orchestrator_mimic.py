#!/usr/bin/env python3
"""Mimic what the orchestrator does to diagnose TaskGroup errors."""

import asyncio
from pathlib import Path
from claude_code_sdk import query, ClaudeCodeOptions

async def test_with_orchestrator_style():
    """Test with a prompt similar to what orchestrator generates."""
    
    test_dir = Path("test_example")
    
    # Test with context from previous phase
    prompt = """Working directory: test_example

## Previous Phase: Planning

Following the implementation plan:

# Implementation Plan - Milestone 1: Basic Arithmetic Operations

Create main.py with Calculator class containing add, subtract, multiply, divide methods.
Include CLI interface with menu system. Handle division by zero.
Create src/calculator.py with the Calculator class.
Create empty requirements.txt.

## Implementation Phase

Create the implementation based on the plan above.

**IMPORTANT: Do NOT use TodoWrite tool - just implement directly.**"""
    
    print("Testing with simplified prompt...")
    
    try:
        options = ClaudeCodeOptions(
            max_turns=50,  # Same as implement phase
            allowed_tools=["Read", "Write", "Edit", "MultiEdit"],  # No Bash tool
            permission_mode='bypassPermissions',
            cwd=str(test_dir.absolute())
        )
        
        message_count = 0
        async for message in query(prompt=prompt, options=options):
            message_count += 1
            if message_count <= 5:  # Only print first few messages
                if hasattr(message, 'content'):
                    print(f"Message {message_count}: {str(message.content)[:100]}...")
            
            # Check for errors
            if hasattr(message, '__dict__'):
                msg_dict = message.__dict__
                if msg_dict.get('type') == 'result' and msg_dict.get('is_error'):
                    print(f"Error detected: {msg_dict}")
                    
        print(f"\nTotal messages: {message_count}")
        
        # Check if main.py was created
        main_py = test_dir / "main.py"
        if main_py.exists():
            print(f"✓ main.py created!")
            return True
        else:
            print("✗ main.py not created")
            return False
            
    except Exception as e:
        print(f"Exception: {type(e).__name__}: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = asyncio.run(test_with_orchestrator_style())
    print(f"\nTest {'PASSED' if success else 'FAILED'}")