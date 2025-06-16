#!/usr/bin/env python3
"""Test sub-phases by letting Claude Code work naturally without programmatic parsing."""

import asyncio
from pathlib import Path
from claude_code_sdk import query, ClaudeCodeOptions
import shutil

async def run_research_subphases(project_dir: Path):
    """Run research phase as 3 natural sub-phases."""
    
    milestone_dir = project_dir / ".cc_automator/milestones/milestone_1"
    milestone_dir.mkdir(parents=True, exist_ok=True)
    
    # Create project description
    desc_file = project_dir / "PROJECT_DESCRIPTION.md"
    desc_file.write_text("""# Number Analysis Tools
Create a Python package with:
1. is_prime(n) - Check if number is prime
2. fibonacci(n) - Get nth Fibonacci number  
3. factorial(n) - Calculate factorial
Include comprehensive tests and documentation.
""")
    
    print("Running Research Phase with 3 Sub-phases\n")
    
    # Sub-phase 1: Analyze requirements (5 turns max)
    print("="*60)
    print("Sub-phase 1/3: Analyze Requirements")
    print("="*60)
    
    prompt1 = f"""You are in the research phase, focusing on requirements analysis.

Working directory: {project_dir}

Read PROJECT_DESCRIPTION.md and create .cc_automator/milestones/milestone_1/requirements.txt with:
- Key features required
- Success criteria  
- Technical constraints

Be concise and focused. Do NOT use WebSearch."""

    async for message in query(
        prompt=prompt1,
        options=ClaudeCodeOptions(
            max_turns=5,
            permission_mode='bypassPermissions'
        )
    ):
        pass  # Just let Claude work, don't parse messages
        
    # Check if sub-phase 1 succeeded
    req_file = milestone_dir / "requirements.txt"
    if not req_file.exists():
        print("✗ Sub-phase 1 failed: requirements.txt not created")
        return False
        
    print("✓ Sub-phase 1 complete: requirements.txt created\n")
    
    # Sub-phase 2: Explore solutions (5 turns max)
    print("="*60)
    print("Sub-phase 2/3: Explore Solutions")
    print("="*60)
    
    prompt2 = f"""Continue the research phase, focusing on technical solutions.

Working directory: {project_dir}

Read .cc_automator/milestones/milestone_1/requirements.txt and create 
.cc_automator/milestones/milestone_1/solutions.txt with:
- Algorithm choices for each function
- Testing strategies
- Code structure recommendations

Do NOT use WebSearch."""

    async for message in query(
        prompt=prompt2,
        options=ClaudeCodeOptions(
            max_turns=5,
            permission_mode='bypassPermissions'
        )
    ):
        pass
        
    sol_file = milestone_dir / "solutions.txt"
    if not sol_file.exists():
        print("✗ Sub-phase 2 failed: solutions.txt not created")
        return False
        
    print("✓ Sub-phase 2 complete: solutions.txt created\n")
    
    # Sub-phase 3: Write research.md (5 turns max)
    print("="*60)
    print("Sub-phase 3/3: Document Research")
    print("="*60)
    
    prompt3 = f"""Complete the research phase by creating the final documentation.

Working directory: {project_dir}

Read both:
- .cc_automator/milestones/milestone_1/requirements.txt
- .cc_automator/milestones/milestone_1/solutions.txt

Create .cc_automator/milestones/milestone_1/research.md with:
# Research Summary
## Requirements Analysis
## Technical Approach
## Implementation Plan

This completes the research phase."""

    async for message in query(
        prompt=prompt3,
        options=ClaudeCodeOptions(
            max_turns=5,
            permission_mode='bypassPermissions'
        )
    ):
        pass
        
    research_file = milestone_dir / "research.md"
    if not research_file.exists():
        print("✗ Sub-phase 3 failed: research.md not created")
        return False
        
    print("✓ Sub-phase 3 complete: research.md created")
    print(f"  File size: {len(research_file.read_text())} chars\n")
    
    return True

async def main():
    # Clean test directory
    test_dir = Path("test_subphase_natural")
    if test_dir.exists():
        shutil.rmtree(test_dir)
    test_dir.mkdir()
    
    # Run test
    start_time = asyncio.get_event_loop().time()
    success = await run_research_subphases(test_dir)
    total_time = asyncio.get_event_loop().time() - start_time
    
    print("="*60)
    print(f"Research Phase: {'PASSED' if success else 'FAILED'}")
    print(f"Total time: {total_time:.1f}s")
    print(f"Average per sub-phase: {total_time/3:.1f}s")
    
    if success:
        print("\nThis demonstrates that breaking phases into focused sub-phases:")
        print("- Avoids the 10-minute timeout")
        print("- Maintains clear progress")
        print("- Allows natural Claude Code execution")

if __name__ == "__main__":
    asyncio.run(main())