#!/usr/bin/env python3
"""Test sub-phase approach for research phase to avoid timeouts."""

import asyncio
from pathlib import Path
from claude_code_sdk import query, ClaudeCodeOptions
import shutil

class SubPhaseResearchTest:
    def __init__(self, project_dir: Path):
        self.project_dir = project_dir
        self.milestone_dir = project_dir / ".cc_automator/milestones/milestone_1"
        self.milestone_dir.mkdir(parents=True, exist_ok=True)
        
    async def run_subphase(self, name: str, prompt: str, max_turns: int = 5) -> dict:
        """Run a single sub-phase with focused prompt."""
        print(f"\n{'='*60}")
        print(f"Running sub-phase: {name}")
        print(f"{'='*60}")
        
        start_time = asyncio.get_event_loop().time()
        messages = []
        success = False
        
        try:
            async for message in query(
                prompt=prompt,
                options=ClaudeCodeOptions(
                    max_turns=max_turns
                )
            ):
                if hasattr(message, 'content'):
                    content_str = str(message.content)
                    print(f"Claude: {content_str[:200]}...")
                    messages.append(content_str)
                elif hasattr(message, 'text'):
                    print(f"Tool result: {message.text[:200]}...")
                else:
                    print(f"Other message type: {type(message)}")
                    
            success = True
        except Exception as e:
            print(f"Sub-phase {name} failed: {e}")
            
        duration = asyncio.get_event_loop().time() - start_time
        print(f"\nSub-phase {name} completed in {duration:.1f}s")
        
        return {
            "name": name,
            "success": success,
            "duration": duration,
            "output": "\n".join(messages)
        }
        
    async def test_research_with_subphases(self):
        """Test breaking research into 3 focused sub-phases."""
        
        # Create project description
        desc_file = self.project_dir / "PROJECT_DESCRIPTION.md"
        desc_file.write_text("""# Number Analysis Tools
Create a Python package with:
1. is_prime(n) - Check if number is prime
2. fibonacci(n) - Get nth Fibonacci number
3. factorial(n) - Calculate factorial
Include comprehensive tests and documentation.
""")
        
        # Sub-phase 1: Analyze requirements
        result1 = await self.run_subphase(
            "research_requirements",
            f"""You are in the research phase of a software project.
            
Working directory: {self.project_dir}

Read PROJECT_DESCRIPTION.md and analyze the requirements.
Create a file at .cc_automator/milestones/milestone_1/requirements.txt listing:
- Key features required
- Success criteria
- Technical constraints

Be concise and focused. Do NOT use WebSearch."""
        )
        
        # Sub-phase 2: Explore solutions (only if phase 1 succeeded)
        if result1["success"]:
            result2 = await self.run_subphase(
                "research_solutions", 
                f"""Continue the research phase.

Working directory: {self.project_dir}

Read .cc_automator/milestones/milestone_1/requirements.txt
Research technical approaches for implementing these requirements.
Create .cc_automator/milestones/milestone_1/solutions.txt with:
- Algorithm choices
- Testing strategies  
- Code structure recommendations

Focus on practical solutions. Do NOT use WebSearch."""
            )
        else:
            result2 = {"success": False, "name": "research_solutions", "duration": 0}
            
        # Sub-phase 3: Write research.md (only if phase 2 succeeded)
        if result2["success"]:
            result3 = await self.run_subphase(
                "research_document",
                f"""Complete the research phase.

Working directory: {self.project_dir}

Read both:
- .cc_automator/milestones/milestone_1/requirements.txt
- .cc_automator/milestones/milestone_1/solutions.txt

Create .cc_automator/milestones/milestone_1/research.md with:
# Research Summary
## Requirements Analysis
## Technical Approach  
## Implementation Plan

This completes the research phase. Do NOT use WebSearch."""
            )
        else:
            result3 = {"success": False, "name": "research_document", "duration": 0}
            
        # Summary
        print(f"\n{'='*60}")
        print("RESEARCH PHASE SUMMARY")
        print(f"{'='*60}")
        
        total_duration = sum(r["duration"] for r in [result1, result2, result3])
        success_count = sum(1 for r in [result1, result2, result3] if r["success"])
        
        print(f"Total duration: {total_duration:.1f}s")
        print(f"Sub-phases completed: {success_count}/3")
        
        for result in [result1, result2, result3]:
            status = "✓" if result["success"] else "✗"
            print(f"  {status} {result['name']}: {result['duration']:.1f}s")
            
        # Check final output
        research_file = self.milestone_dir / "research.md"
        if research_file.exists():
            print(f"\n✓ research.md created ({len(research_file.read_text())} chars)")
        else:
            print("\n✗ research.md NOT created")
            
        return success_count == 3

async def main():
    # Clean test directory
    test_dir = Path("test_subphase")
    if test_dir.exists():
        shutil.rmtree(test_dir)
    test_dir.mkdir()
    
    # Run test
    tester = SubPhaseResearchTest(test_dir)
    success = await tester.test_research_with_subphases()
    
    print(f"\nOverall test: {'PASSED' if success else 'FAILED'}")

if __name__ == "__main__":
    asyncio.run(main())