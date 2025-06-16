#!/usr/bin/env python3
"""Test WebSearch behavior in research-like context to find why it hangs."""

import asyncio
import time
from pathlib import Path
from claude_code_sdk import query, ClaudeCodeOptions

async def test_research_websearch():
    """Test WebSearch in a research context similar to what causes hangs."""
    
    # Create a test directory with FastAPI-like setup
    test_dir = Path("test_websearch_research")
    test_dir.mkdir(exist_ok=True)
    
    # Create main.py like FastAPI project
    main_py = test_dir / "main.py"
    main_py.write_text('''#!/usr/bin/env python3
"""
Main entry point for the FastAPI CRUD application
"""

def main():
    """Main function"""
    print("FastAPI CRUD API - Not implemented yet")
    # TODO: Implement FastAPI application
    return 0

if __name__ == "__main__":
    import sys
    sys.exit(main())''')
    
    # Create requirements.txt
    req_txt = test_dir / "requirements.txt"
    req_txt.write_text("# Core dependencies\n# (will be populated by cc_automator)")
    
    # Create milestone directory
    milestone_dir = test_dir / ".cc_automator/milestones/milestone_1"
    milestone_dir.mkdir(parents=True, exist_ok=True)
    
    # Use the EXACT research prompt that was causing hangs
    prompt = f"""Research requirements for: Basic CRUD API with User model

1. Check what exists in main.py and requirements.txt

2. Write your research findings to: {milestone_dir}/research.md

The research.md file must contain:
# Research Findings for Basic CRUD API with User model

## What Exists
- Summary of main.py 
- Current requirements.txt status

## Libraries Needed
- fastapi>=0.104.0
- sqlalchemy[asyncio]>=2.0.0
- pydantic>=2.0.0
- uvicorn[standard]>=0.24.0

## Basic CRUD Pattern
```python
# Example async CRUD pattern
from sqlalchemy.ext.asyncio import AsyncSession

async def create_user(db: AsyncSession, user_data: dict):
    # Basic pattern here
```

## Testing Approach
- pytest with async support
- Test database with SQLite

You may use WebSearch if needed for current information, but don't let it block progress. If WebSearch times out or fails, continue without it and use your existing knowledge."""
    
    print("Testing WebSearch in research context...")
    print(f"Working directory: {test_dir.absolute()}")
    print("This reproduces the exact scenario that caused hangs")
    
    start_time = time.time()
    websearch_count = 0
    last_activity = start_time
    
    try:
        message_count = 0
        async for message in query(
            prompt=prompt,
            options=ClaudeCodeOptions(
                max_turns=20,  # Allow more turns like research phase
                permission_mode='bypassPermissions',
                cwd=str(test_dir.absolute())
            )
        ):
            message_count += 1
            elapsed = time.time() - start_time
            activity_gap = time.time() - last_activity
            last_activity = time.time()
            
            print(f"[{elapsed:6.1f}s] Message {message_count} (+{activity_gap:.1f}s): {type(message).__name__}")
            
            # Track WebSearch usage
            if hasattr(message, 'content') and isinstance(message.content, list):
                for item in message.content:
                    if hasattr(item, 'name') and item.name == 'WebSearch':
                        websearch_count += 1
                        query_text = getattr(item, 'input', {}).get('query', 'unknown')
                        print(f"    🔍 WebSearch #{websearch_count}: {query_text}")
                        
            # Check for long gaps (potential hangs)
            if activity_gap > 60:
                print(f"    ⚠️  Long gap detected: {activity_gap:.1f}s since last message")
                
            # Safety timeout
            if elapsed > 300:  # 5 minutes
                print(f"    ❌ Test timeout after 5 minutes")
                return False, websearch_count, elapsed
                
        duration = time.time() - start_time
        print(f"\n✅ Research completed successfully in {duration:.1f}s")
        print(f"   WebSearch queries made: {websearch_count}")
        
        # Check if research.md was created
        research_file = milestone_dir / "research.md"
        if research_file.exists():
            print(f"   ✅ research.md created ({len(research_file.read_text())} chars)")
        else:
            print(f"   ❌ research.md not created")
            
        return True, websearch_count, duration
        
    except Exception as e:
        duration = time.time() - start_time
        print(f"❌ Error after {duration:.1f}s: {e}")
        return False, websearch_count, duration

async def main():
    print("WebSearch Research Context Test")
    print("=" * 50)
    print("This test reproduces the exact research scenario that caused hangs")
    print("to identify why WebSearch works in isolation but hangs in research.")
    print()
    
    success, websearch_count, duration = await test_research_websearch()
    
    print(f"\nResults:")
    print(f"- Success: {'✅' if success else '❌'}")
    print(f"- Duration: {duration:.1f}s")
    print(f"- WebSearch queries: {websearch_count}")
    
    if success:
        print("\n✅ Research with WebSearch works - may be a different issue")
    else:
        print("\n❌ Research with WebSearch hangs - this is the root cause")
        print("   Next steps: Analyze what specifically about research context causes hangs")

if __name__ == "__main__":
    asyncio.run(main())