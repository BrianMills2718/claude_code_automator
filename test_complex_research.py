#!/usr/bin/env python3
"""Test WebSearch with complex research that requires current library info."""

import asyncio
import time
from pathlib import Path
from claude_code_sdk import query, ClaudeCodeOptions
import shutil

async def test_complex_research():
    """Test research that legitimately needs WebSearch for current library syntax."""
    
    # Clean up and create test directory
    test_dir = Path("test_complex_research")
    if test_dir.exists():
        shutil.rmtree(test_dir)
    test_dir.mkdir()
    
    # Create FastAPI project structure like the one that was hanging
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
    
    req_txt = test_dir / "requirements.txt"
    req_txt.write_text("# Core dependencies\n# (will be populated by cc_automator)")
    
    milestone_dir = test_dir / ".cc_automator/milestones/milestone_1"
    milestone_dir.mkdir(parents=True, exist_ok=True)
    
    # Create CLAUDE.md with complex requirements that need current info
    claude_md = test_dir / "CLAUDE.md"
    claude_md.write_text("""# FastAPI CRUD API

## Technical Requirements
- FastAPI with async/await patterns
- SQLAlchemy 2.0 with async support (NEW SYNTAX)
- Pydantic v2 for data validation (NEW API)
- JWT authentication with python-jose
- Modern async database patterns

## Milestone 1: Basic CRUD API with User model
- Set up FastAPI application structure with current best practices
- Create User model with SQLAlchemy 2.0 async (need current syntax)
- Implement CRUD endpoints using latest FastAPI patterns
- Use Pydantic v2 for request/response schemas (need current API)
- Modern async database setup

This requires current 2024 library syntax and patterns.""")
    
    # Research prompt that SHOULD use WebSearch for current info
    prompt = f"""Research requirements for: Basic CRUD API with User model

This is a FastAPI project using modern libraries that have changed significantly:
- SQLAlchemy 2.0 async (major syntax changes from 1.x)
- Pydantic v2 (breaking changes from v1)
- FastAPI latest patterns (2024)

1. Check what exists in main.py, requirements.txt, and CLAUDE.md
2. Use WebSearch to find CURRENT syntax for:
   - SQLAlchemy 2.0 async session setup
   - Pydantic v2 model definitions
   - FastAPI dependency injection patterns
   - Current library versions (2024)

3. Write findings to: {milestone_dir}/research.md

The research.md must include:
- Current library versions and syntax
- Working code examples with 2024 syntax
- Any breaking changes from older versions

IMPORTANT: Use WebSearch to get current information - these libraries have changed significantly and outdated syntax won't work."""
    
    print("Testing complex research that REQUIRES WebSearch...")
    print("This should trigger WebSearch for current library syntax")
    
    start_time = time.time()
    websearch_count = 0
    last_activity = start_time
    
    try:
        message_count = 0
        last_websearch_time = None
        
        async for message in query(
            prompt=prompt,
            options=ClaudeCodeOptions(
                max_turns=25,
                permission_mode='bypassPermissions',
                cwd=str(test_dir.absolute())
            )
        ):
            message_count += 1
            elapsed = time.time() - start_time
            activity_gap = time.time() - last_activity
            last_activity = time.time()
            
            print(f"[{elapsed:6.1f}s] Message {message_count} (+{activity_gap:.1f}s): {type(message).__name__}")
            
            # Track WebSearch usage in detail
            if hasattr(message, 'content') and isinstance(message.content, list):
                for item in message.content:
                    if hasattr(item, 'name') and item.name == 'WebSearch':
                        websearch_count += 1
                        query_text = getattr(item, 'input', {}).get('query', 'unknown')
                        print(f"    🔍 WebSearch #{websearch_count}: '{query_text}'")
                        last_websearch_time = time.time()
                        
            # Check for WebSearch hanging
            if last_websearch_time and (time.time() - last_websearch_time) > 120:
                print(f"    ❌ WebSearch appears to be hanging (>{120}s since request)")
                return False, websearch_count, elapsed
                
            # Check for long gaps between messages
            if activity_gap > 90:
                print(f"    ⚠️  Very long gap: {activity_gap:.1f}s since last message")
                
            # Safety timeout - but longer for complex research
            if elapsed > 600:  # 10 minutes
                print(f"    ❌ Test timeout after 10 minutes")
                return False, websearch_count, elapsed
                
        duration = time.time() - start_time
        print(f"\n✅ Complex research completed in {duration:.1f}s")
        print(f"   WebSearch queries made: {websearch_count}")
        
        # Check results
        research_file = milestone_dir / "research.md"
        if research_file.exists():
            content = research_file.read_text()
            print(f"   ✅ research.md created ({len(content)} chars)")
            
            # Check if it has current info (indicates WebSearch was used)
            if "2024" in content or "current" in content.lower():
                print(f"   ✅ Contains current/2024 information")
            else:
                print(f"   ⚠️  May not have current information")
        else:
            print(f"   ❌ research.md not created")
            
        return True, websearch_count, duration
        
    except Exception as e:
        duration = time.time() - start_time
        print(f"❌ Error after {duration:.1f}s: {e}")
        if "TaskGroup" in str(e):
            print("   This looks like the TaskGroup error we've been seeing!")
        return False, websearch_count, duration

async def main():
    print("Complex Research WebSearch Test")
    print("=" * 50)
    print("Testing research that REQUIRES WebSearch for current library syntax")
    print("This should reproduce the hanging behavior if it exists.")
    print()
    
    success, websearch_count, duration = await test_complex_research()
    
    print(f"\nResults:")
    print(f"- Success: {'✅' if success else '❌'}")
    print(f"- Duration: {duration:.1f}s")
    print(f"- WebSearch queries: {websearch_count}")
    
    if not success:
        print("\n❌ Found the hanging issue!")
        print("   The problem is complex research that requires multiple WebSearch queries")
    elif websearch_count == 0:
        print("\n🤔 Claude didn't use WebSearch even when explicitly asked")
        print("   This suggests WebSearch might be disabled or avoided")
    else:
        print(f"\n✅ Complex research with WebSearch works fine")
        print("   The hanging issue might be context-specific or intermittent")

if __name__ == "__main__":
    asyncio.run(main())