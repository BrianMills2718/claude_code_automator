#!/usr/bin/env python3
"""Test SDK directly without orchestrator to diagnose issues."""

import asyncio
from pathlib import Path
from claude_code_sdk import query, ClaudeCodeOptions

async def test_simple_file_creation():
    """Test if SDK can create a simple file."""
    
    test_dir = Path("test_sdk_direct")
    test_dir.mkdir(exist_ok=True)
    
    prompt = f"""Working directory: {test_dir.absolute()}

Create a simple main.py file with:
```python
def hello():
    return "Hello from SDK test"

if __name__ == "__main__":
    print(hello())
```

Just create the file, nothing else."""
    
    print("Testing SDK file creation...")
    
    try:
        options = ClaudeCodeOptions(
            max_turns=5,
            permission_mode='bypassPermissions',
            cwd=str(test_dir.absolute())
        )
        
        async for message in query(prompt=prompt, options=options):
            if hasattr(message, 'content'):
                print(f"Claude: {str(message.content)[:100]}...")
            if hasattr(message, '__dict__'):
                msg_dict = message.__dict__
                if msg_dict.get('type') == 'result':
                    print(f"Result: success={not msg_dict.get('is_error')}")
                    
        # Check if file was created
        main_py = test_dir / "main.py"
        if main_py.exists():
            print(f"✓ File created successfully!")
            print(f"Contents:\n{main_py.read_text()}")
            return True
        else:
            print("✗ File not created")
            return False
            
    except Exception as e:
        print(f"Error: {e}")
        return False

if __name__ == "__main__":
    success = asyncio.run(test_simple_file_creation())
    print(f"\nTest {'PASSED' if success else 'FAILED'}")