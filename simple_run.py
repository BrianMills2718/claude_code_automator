#!/usr/bin/env python3
"""
Simplified runner for CC_AUTOMATOR3 - direct execution without complexity
"""

import subprocess
import json
import time
from pathlib import Path

def run_phase(phase_name: str, prompt: str, project_dir: Path):
    """Run a single phase with minimal overhead"""
    print(f"\n{'='*60}")
    print(f"Running {phase_name} phase...")
    print(f"{'='*60}")
    
    start = time.time()
    
    cmd = [
        "claude", "-p", prompt,
        "--output-format", "json",
        "--max-turns", "5",
        "--dangerously-skip-permissions"
    ]
    
    result = subprocess.run(
        cmd,
        capture_output=True,
        text=True,
        cwd=project_dir,
        timeout=120  # 2 minute timeout
    )
    
    duration = time.time() - start
    
    if result.returncode == 0:
        data = json.loads(result.stdout)
        print(f"✓ Completed in {duration:.1f}s")
        print(f"  Cost: ${data.get('cost_usd', 0):.4f}")
        return True
    else:
        print(f"✗ Failed: {result.stderr[:200]}")
        return False

def main():
    """Run milestone 1 with extremely simple prompts"""
    
    project_dir = Path("/home/brian/autocoder2_cc/test_calculator")
    
    # Clean up
    subprocess.run(["rm", "-rf", ".cc_automator"], cwd=project_dir)
    
    print("CC_AUTOMATOR3 - Simple Mode")
    print("="*60)
    
    # Phase 1: Research
    research_prompt = """Check if add, subtract, multiply, divide functions exist in this project.
Write findings to: .cc_automator/milestones/milestone_1/research.md"""
    
    if not run_phase("research", research_prompt, project_dir):
        return 1
        
    # Phase 2: Planning  
    planning_prompt = """Based on research, create a brief plan for implementing calculator.
Write to: .cc_automator/milestones/milestone_1/plan.md"""
    
    if not run_phase("planning", planning_prompt, project_dir):
        return 1
        
    # Phase 3: Implement
    implement_prompt = """Implement add, subtract, multiply, divide functions if needed.
Create main.py that demonstrates these operations."""
    
    if not run_phase("implement", implement_prompt, project_dir):
        return 1
        
    # Phase 4: Test
    test_prompt = """Run: pytest tests/unit -v
If no tests exist, create basic tests for the 4 operations."""
    
    if not run_phase("test", test_prompt, project_dir):
        return 1
        
    print("\n✓ Milestone 1 completed!")
    return 0

if __name__ == "__main__":
    exit(main())