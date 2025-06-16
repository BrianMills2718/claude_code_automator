#\!/usr/bin/env python3
"""Test if context7 MCP is working"""

import asyncio
from claude_code_sdk import query, ClaudeCodeOptions

async def test_context7():
    """Test context7 MCP functionality"""
    prompt = """Use the mcp__context7__resolve-library-id tool to find the library ID for FastAPI."""
    
    options = ClaudeCodeOptions(
        max_turns=3,
        allowed_tools=["mcp__context7__resolve-library-id"],
        cwd="."
    )
    
    print("Testing context7 MCP...")
    
    try:
        tool_calls = []
        async for message in query(prompt=prompt, options=options):
            if hasattr(message, '__dict__'):
                msg_dict = message.__dict__
            elif isinstance(message, dict):
                msg_dict = message
            else:
                continue
                
            # Track tool usage
            if msg_dict.get("type") == "tool_use":
                tool_name = msg_dict.get("name", "")
                print(f"Tool called: {tool_name}")
                if "context7" in tool_name:
                    tool_calls.append(tool_name)
                    
        if tool_calls:
            print(f"\n✓ Success\! Context7 tools were called")
        else:
            print("\n✗ No context7 tools were called")
            
    except Exception as e:
        print(f"\n✗ Error: {e}")

if __name__ == "__main__":
    asyncio.run(test_context7())
EOF < /dev/null
