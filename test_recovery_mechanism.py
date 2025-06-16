#!/usr/bin/env python3
"""Test the new TaskGroup recovery mechanism."""

import asyncio
import time
from pathlib import Path
import shutil
import sys
import os

# Add the current directory to path so we can import the orchestrator
sys.path.insert(0, '/home/brian/cc_automator4')

from phase_orchestrator import PhaseOrchestrator, Phase, PhaseStatus
from milestone_decomposer import Milestone

async def test_recovery_mechanism():
    """Test that TaskGroup recovery works by reproducing the complex research scenario."""
    
    # Clean up and create test directory
    test_dir = Path("/home/brian/cc_automator4/test_recovery_dir")
    if test_dir.exists():
        shutil.rmtree(test_dir)
    test_dir.mkdir()
    
    # Create FastAPI project that should trigger WebSearch and TaskGroup error
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
    
    claude_md = test_dir / "CLAUDE.md"
    claude_md.write_text("""# FastAPI CRUD API

## Technical Requirements
- FastAPI with async/await patterns
- SQLAlchemy 2.0 with async support (NEED CURRENT SYNTAX)
- Pydantic v2 for data validation (BREAKING CHANGES FROM V1)
- JWT authentication with python-jose
- Current library versions and patterns (2024)

## Milestone 1: Basic CRUD API with User model
- Set up FastAPI application structure with latest patterns
- Create User model with SQLAlchemy 2.0 async (current syntax required)
- Implement CRUD endpoints using 2024 FastAPI best practices
- Use Pydantic v2 for request/response schemas (v2 API required)

This requires current library syntax that has changed significantly.""")
    
    # Create milestone for testing
    milestone = Milestone(
        number=1,
        name="Basic CRUD API with User model",
        description="FastAPI CRUD with current library syntax",
        success_criteria=[
            "FastAPI app with async SQLAlchemy 2.0",
            "Pydantic v2 models",
            "Current 2024 syntax"
        ]
    )
    
    # Create phase orchestrator
    orchestrator = PhaseOrchestrator(
        working_dir=test_dir,
        project_name="FastAPI Recovery Test",
        verbose=True
    )
    
    # Create research phase that should trigger WebSearch and fail
    research_phase = Phase(
        name="research",
        description="Research requirements with current library syntax",
        prompt=f"""Research requirements for: {milestone.name}

This FastAPI project requires CURRENT library syntax:
- SQLAlchemy 2.0 async (major changes from 1.x)
- Pydantic v2 (breaking changes from v1)
- FastAPI latest patterns (2024)

1. Check existing files: main.py, requirements.txt, CLAUDE.md
2. Use WebSearch to find CURRENT syntax for modern libraries
3. Create comprehensive research.md with up-to-date information

IMPORTANT: Use WebSearch to get current library syntax - these have changed significantly.""",
        timeout_seconds=600,
        allowed_tools=["Read", "Write", "Edit", "WebSearch", "Bash"],
        max_turns=25
    )
    
    print("Testing TaskGroup recovery mechanism...")
    print("This should trigger WebSearch TaskGroup error, then recover")
    
    start_time = time.time()
    
    try:
        # Disable sub-phases to force direct SDK execution and trigger TaskGroup error
        os.environ['USE_SUBPHASES'] = 'false'
        
        # Execute the research phase (should fail with TaskGroup, then recover)
        result = await orchestrator._execute_with_sdk(research_phase)
        duration = time.time() - start_time
        
        print(f"\nTest completed in {duration:.1f}s")
        print(f"Phase status: {research_phase.status}")
        print(f"Phase error: {research_phase.error}")
        
        # Check if research.md was created (indicates recovery worked)
        research_file = test_dir / ".cc_automator/milestones/milestone_1/research.md"
        if research_file.exists():
            content = research_file.read_text()
            print(f"✅ research.md created: {len(content)} chars")
            
            # Check if it has reasonable content
            if len(content) > 500 and "FastAPI" in content:
                print("✅ Research content looks comprehensive")
                return True
            else:
                print("⚠️  Research content seems minimal")
                return False
        else:
            print("❌ research.md not created")
            return False
            
    except Exception as e:
        duration = time.time() - start_time
        print(f"❌ Test failed after {duration:.1f}s: {e}")
        return False

async def main():
    print("TaskGroup Recovery Mechanism Test")
    print("=" * 50)
    print("Testing that complex research can recover from WebSearch TaskGroup errors")
    print()
    
    success = await test_recovery_mechanism()
    
    if success:
        print("\n✅ Recovery mechanism works!")
        print("   Complex research with WebSearch failures now completes successfully")
    else:
        print("\n❌ Recovery mechanism needs improvement")
        print("   TaskGroup errors still prevent phase completion")

if __name__ == "__main__":
    asyncio.run(main())