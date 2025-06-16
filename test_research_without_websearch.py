#!/usr/bin/env python3
"""Test research phase without WebSearch to see if Claude can do good research anyway."""

import asyncio
from pathlib import Path
import shutil
import sys
import os

sys.path.insert(0, '/home/brian/cc_automator4')

from phase_orchestrator import PhaseOrchestrator, Phase

async def test_research_without_websearch():
    """Test research with improved prompt that guides Claude away from WebSearch."""
    
    test_dir = Path("/home/brian/cc_automator4/test_no_websearch")
    if test_dir.exists():
        shutil.rmtree(test_dir)
    test_dir.mkdir()
    
    # Create FastAPI project structure
    main_py = test_dir / "main.py"
    main_py.write_text('''#!/usr/bin/env python3
"""FastAPI CRUD API - Not implemented yet"""

def main():
    print("FastAPI CRUD API - Not implemented yet")
    return 0

if __name__ == "__main__":
    import sys
    sys.exit(main())''')
    
    req_txt = test_dir / "requirements.txt"
    req_txt.write_text("# Core dependencies - will be populated")
    
    claude_md = test_dir / "CLAUDE.md"
    claude_md.write_text("""# FastAPI CRUD API

## Technical Requirements
- FastAPI with async/await patterns
- SQLAlchemy 2.0 with async support
- Pydantic v2 for data validation
- JWT authentication
- Current library best practices

## Milestone 1: Basic CRUD API with User model
- FastAPI application with async SQLAlchemy 2.0
- Pydantic v2 models and schemas
- CRUD endpoints for User model
- Modern async patterns""")
    
    # Create improved research prompt that guides Claude intelligently
    prompt = f"""Research requirements for: Basic CRUD API with User model

You are researching a FastAPI project with modern libraries. Your goal is to create a comprehensive research.md file.

APPROACH:
1. Analyze existing project files (main.py, requirements.txt, CLAUDE.md)
2. Use your knowledge of current FastAPI/SQLAlchemy patterns (as of 2024)
3. Focus on practical, working solutions that you're confident about

OUTPUT: Create .cc_automator/milestones/milestone_1/research.md with:

# Research Findings for Basic CRUD API with User model

## Project Analysis
- Current state of main.py and requirements.txt
- Technical requirements from CLAUDE.md

## Library Requirements (Current Stable Versions)
- fastapi>=0.104.0 (latest stable)
- sqlalchemy[asyncio]>=2.0.23 (async support)
- pydantic>=2.5.0 (v2 with validation)
- uvicorn[standard]>=0.24.0 (ASGI server)
- python-jose[cryptography]>=3.3.0 (JWT)
- passlib[bcrypt]>=1.7.4 (password hashing)

## Implementation Approach
```python
# Modern FastAPI + SQLAlchemy 2.0 async pattern
from fastapi import FastAPI, Depends
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from pydantic import BaseModel

# Current async session pattern
async def get_db() -> AsyncSession:
    async with AsyncSessionLocal() as session:
        yield session

# Pydantic v2 model
class UserCreate(BaseModel):
    name: str
    email: str
```

## Testing Strategy
- pytest with pytest-asyncio for async tests
- SQLite async for testing: sqlite+aiosqlite:///test.db
- TestClient for API endpoint testing

IMPORTANT: Use your existing knowledge of these libraries - they are well-established and you know the current patterns. Focus on creating a practical, actionable research document that will guide implementation."""
    
    orchestrator = PhaseOrchestrator(
        working_dir=test_dir,
        project_name="FastAPI No WebSearch Test",
        verbose=True
    )
    
    research_phase = Phase(
        name="research",
        description="Research without WebSearch dependency",
        prompt=prompt,
        timeout_seconds=300,
        allowed_tools=["Read", "Write", "Edit", "Bash"],  # No WebSearch
        max_turns=15
    )
    
    print("Testing research phase without WebSearch...")
    print("Claude should use existing knowledge to create comprehensive research")
    
    try:
        result = await orchestrator._execute_with_sdk(research_phase)
        
        print(f"\nPhase status: {research_phase.status}")
        print(f"Phase error: {research_phase.error}")
        
        research_file = test_dir / ".cc_automator/milestones/milestone_1/research.md"
        if research_file.exists():
            content = research_file.read_text()
            print(f"✅ research.md created: {len(content)} chars")
            
            # Check quality indicators
            quality_checks = [
                ("FastAPI" in content, "Contains FastAPI info"),
                ("SQLAlchemy" in content, "Contains SQLAlchemy info"),
                ("Pydantic" in content, "Contains Pydantic info"),
                ("async" in content.lower(), "Mentions async patterns"),
                (len(content) > 1000, "Substantial content"),
                ("```python" in content, "Contains code examples")
            ]
            
            passed_checks = sum(1 for check, _ in quality_checks if check)
            print(f"Quality score: {passed_checks}/{len(quality_checks)}")
            
            for check, desc in quality_checks:
                status = "✅" if check else "❌"
                print(f"  {status} {desc}")
                
            return passed_checks >= 4  # At least 4/6 quality checks
        else:
            print("❌ research.md not created")
            return False
            
    except Exception as e:
        print(f"❌ Test failed: {e}")
        return False

async def main():
    print("Research Without WebSearch Test")
    print("=" * 40)
    print("Testing if Claude can do excellent research using existing knowledge")
    print()
    
    success = await test_research_without_websearch()
    
    if success:
        print("\n✅ Claude creates excellent research without WebSearch!")
        print("   This suggests we can guide Claude to avoid WebSearch when possible")
    else:
        print("\n❌ Research quality suffers without WebSearch")
        print("   WebSearch recovery mechanism is still needed")

if __name__ == "__main__":
    asyncio.run(main())