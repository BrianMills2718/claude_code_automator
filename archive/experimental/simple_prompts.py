#!/usr/bin/env python3
"""
Simplified prompt templates for CC_AUTOMATOR3
Focus on speed and pragmatism over exhaustive planning
"""

SIMPLE_PROMPTS = {
    "research": """Check if {milestone_name} is already implemented.
If yes: document that in research.md and we're done.
If no: briefly note what needs to be built.
This should take < 30 seconds.""",
    
    "planning": """Based on research:
If already complete: write "Already implemented" in plan.md
Otherwise: write a brief plan (< 50 lines) with key functions needed.""",
    
    "implement": """Based on plan:
If already complete: verify with 'python main.py' and document
Otherwise: implement the required functionality efficiently.""",
    
    "lint": """Run: flake8 --max-line-length=100
Fix any errors. Show clean output.""",
    
    "typecheck": """Run: mypy --strict .
Fix any errors. Show clean output.""",
    
    "test": """Run: pytest tests/unit -v
If tests exist and pass: document success
If tests missing: create minimal tests for the milestone
Fix any failures.""",
    
    "integration": """Run: pytest tests/integration -v
Fix any failures or create minimal integration tests if missing.""",
    
    "e2e": """Run: python main.py
Verify it works for the milestone functionality.""",
    
    "commit": """Create a git commit with the changes for this milestone."""
}

def get_simple_prompt(phase: str, milestone_name: str) -> str:
    """Get a simplified prompt for a phase"""
    template = SIMPLE_PROMPTS.get(phase, "Complete the {phase} phase")
    return template.format(milestone_name=milestone_name, phase=phase)