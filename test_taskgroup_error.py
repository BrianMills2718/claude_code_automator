#!/usr/bin/env python3
"""
Test script to reproduce the TaskGroup error during explore_solutions sub-phase
"""

import asyncio
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))

from phase_orchestrator import PhaseOrchestrator, Phase
import os

async def test_research_phase():
    """Test the research phase with WebSearch to reproduce TaskGroup error"""
    
    # Create test directory
    test_dir = Path("test_taskgroup")
    test_dir.mkdir(exist_ok=True)
    
    # Create basic project files
    (test_dir / "main.py").write_text("# Test project")
    
    # Initialize orchestrator
    orchestrator = PhaseOrchestrator(
        project_name="test_taskgroup",
        working_dir=str(test_dir),
        verbose=True
    )
    
    # Create research phase that uses WebSearch
    research_phase = Phase(
        name="research",
        description="Research phase with WebSearch",
        prompt="""You are researching a simple calculator project.

Please research the following:
1. Best practices for Python calculator design
2. Error handling patterns
3. Testing strategies

Use WebSearch to find current best practices.

Write your findings to .cc_automator/milestones/milestone_1/research.md

Important: Create comprehensive research documentation.""",
        allowed_tools=["Read", "Write", "Edit", "LS", "WebSearch"],
        max_turns=10
    )
    
    # Set milestone context
    orchestrator.current_milestone = type('obj', (object,), {
        'number': 1,
        'name': 'Basic Calculator',
        'description': 'Create a simple calculator'
    })
    
    print("Starting research phase with WebSearch...")
    
    try:
        result = orchestrator.execute_phase(research_phase)
        print(f"\nPhase result: {result}")
    except Exception as e:
        print(f"\nError occurred: {type(e).__name__}: {e}")
        
        # Check if logs were created
        log_dir = test_dir / ".cc_automator" / "logs"
        if log_dir.exists():
            log_files = list(log_dir.glob("research_*.log"))
            if log_files:
                print(f"\nFound log file: {log_files[-1]}")
                print("\nLog contents:")
                print(log_files[-1].read_text())

if __name__ == "__main__":
    asyncio.run(test_research_phase())