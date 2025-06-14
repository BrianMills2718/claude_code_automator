#!/usr/bin/env python3
"""
Phase Prompt Generator for CC_AUTOMATOR3
Generates detailed prompts for each phase with evidence requirements
"""

from pathlib import Path
from typing import Dict, Optional
from milestone_decomposer import Milestone


class PhasePromptGenerator:
    """Generates detailed prompts for each phase type"""
    
    def __init__(self, project_dir: Path):
        self.project_dir = Path(project_dir)
        self.evidence_dir = self.project_dir / ".cc_automator" / "evidence"
        self.milestone_dir = self.project_dir / ".cc_automator" / "milestones"
        
        # Initialize context manager
        try:
            from context_manager import ContextManager
            self.context_manager = ContextManager(project_dir)
        except ImportError:
            self.context_manager = None
        
    def generate_prompt(self, phase_type: str, milestone: Milestone, 
                       previous_phase_output: Optional[str] = None) -> str:
        """Generate a detailed prompt for a specific phase"""
        
        # Get base prompt
        prompt = self._get_base_prompt(phase_type, milestone)
        
        # Use context manager if available for smarter context
        if self.context_manager:
            context = self.context_manager.get_phase_context(
                phase_type, previous_phase_output, milestone.number
            )
            if context:
                prompt = f"{context}\n\n{prompt}"
                # Save the output for future reference
                if previous_phase_output:
                    prev_phase = self._get_previous_phase_type(phase_type)
                    if prev_phase:
                        self.context_manager.save_phase_output(
                            prev_phase, milestone.number, previous_phase_output
                        )
        else:
            # Fallback to old method
            if previous_phase_output:
                prompt = self._add_previous_context(prompt, phase_type, previous_phase_output)
            
        # Add evidence requirements
        prompt = self._add_evidence_requirements(prompt, phase_type, milestone)
        
        # Add self-healing patterns reminder for implementation
        if phase_type in ["implement", "test", "integration"]:
            prompt = self._add_self_healing_reminder(prompt)
            
        return prompt
    
    def _get_previous_phase_type(self, current_phase: str) -> Optional[str]:
        """Get the previous phase type in the sequence"""
        phase_sequence = [
            "research", "planning", "implement", "lint", 
            "typecheck", "test", "integration", "e2e", "commit"
        ]
        
        try:
            idx = phase_sequence.index(current_phase)
            if idx > 0:
                return phase_sequence[idx - 1]
        except ValueError:
            pass
        
        return None
        
    def _get_base_prompt(self, phase_type: str, milestone: Milestone) -> str:
        """Get the base prompt for a phase type"""
        
        milestone_context = f"""
## Current Milestone: {milestone.number} - {milestone.name}

### Success Criteria:
{chr(10).join(f"- {criterion}" for criterion in milestone.success_criteria)}
"""
        
        prompts = {
            "research": f"""Research requirements for: {milestone.name}

Create file: .cc_automator/milestones/milestone_{milestone.number}/research.md

Include:
- What components to build
- Design approach
- Potential challenges
- Implementation strategy

Keep it concise but thorough.""",

            "planning": f"""
{milestone_context}

## Planning Phase

Based on the research findings, create a detailed implementation plan.

### Tasks:
1. Define the exact file structure to create/modify
2. Specify all functions/classes with signatures
3. Detail the data flow and interactions
4. List all test cases to implement
5. Create implementation steps in order

### Output Required:
Create a detailed plan including:
- File structure with purpose of each file
- Function/class specifications with type hints
- Pseudocode for complex logic
- Test case specifications
- Step-by-step implementation order

Save your COMPLETE plan to: .cc_automator/milestones/milestone_{milestone.number}/plan.md

This plan will be used by the implementation phase, so make it comprehensive and clear.
""",

            "implement": f"""
{milestone_context}

## Implementation Phase

Implement the functionality according to the plan for Milestone {milestone.number}.

### Requirements:
1. Follow the implementation plan exactly
2. Ensure main.py demonstrates this milestone's features
3. Use type hints for all functions
4. Add docstrings to all functions/classes
5. Follow the self-healing patterns from CLAUDE.md

### Key Features to Implement:
{chr(10).join(f"- {criterion}" for criterion in milestone.success_criteria)}

### Verification:
After implementation, run:
```bash
python main.py
```

The program must run without errors and demonstrate all required functionality.

### Output Required:
Save a summary of what you implemented to: .cc_automator/milestones/milestone_{milestone.number}/implement.md
Include:
- List of files created/modified
- Key functions/classes implemented
- How to run and test the implementation
""",

            "lint": """Run flake8 and fix F errors only:

1. flake8 --select=F --exclude=venv,__pycache__,.git
2. Fix each F error (syntax, undefined names, etc.)
3. Re-run flake8 --select=F to verify clean output

Evidence: Show final flake8 --select=F output with zero F errors.""",

            "typecheck": """Run mypy and fix all type errors:

1. mypy --strict .
2. Add missing type hints
3. Fix type inconsistencies
4. Re-run mypy to verify clean output

Evidence: Show final mypy output with "Success: no issues found".""",

            "test": f"""
## Unit Test Phase

Create and run unit tests for Milestone {milestone.number}.

### Tasks:
1. Check if tests/unit directory has test files
2. If no tests exist, create comprehensive unit tests for the implemented functionality
3. Run: `pytest tests/unit -xvs`
4. Fix any failing tests
5. Ensure good test coverage for milestone features

### What to Test:
Based on the implementation, create tests for:
- All public functions/methods
- Edge cases (empty inputs, zero values, etc.)
- Error conditions (invalid inputs, exceptions)
- Return values and types

### Test Structure:
```python
# tests/unit/test_[module_name].py
import pytest
from main import function_name  # or from src.module import function

def test_function_normal_case():
    assert function_name(input) == expected_output

def test_function_edge_case():
    # Test edge cases

def test_function_error_case():
    with pytest.raises(ExpectedException):
        function_name(invalid_input)
```

### Evidence Required:
1. Show created test files
2. Show pytest output with all tests passing
""",

            "integration": f"""
## Integration Test Phase

Create and run integration tests for Milestone {milestone.number}.

### Tasks:
1. Check if tests/integration directory has test files
2. If no tests exist, create integration tests for component interactions
3. Run: `pytest tests/integration -xvs`
4. Fix any failing tests
5. Use minimal mocking (only external services like APIs, databases)

### What to Test:
- How components work together
- Data flow between modules
- Error propagation across components
- Integration with the CLI interface

### Integration Test Example:
```python
# tests/integration/test_calculator_cli.py
import subprocess
from pathlib import Path

def test_calculator_workflow():
    # Test the complete workflow
    result = subprocess.run(['python', 'main.py'], 
                          input='1\\n5\\n10\\n5\\n', 
                          capture_output=True, text=True)
    assert 'Result:' in result.stdout
    assert '15' in result.stdout  # 5 + 10
```

### Evidence Required:
1. Show created integration test files
2. Show pytest output with all tests passing
""",

            "e2e": f"""
## End-to-End Test Phase

Verify main.py works correctly for Milestone {milestone.number}.

### Tasks:
1. Run: `python main.py`
2. Test all features for this milestone
3. Verify success criteria are met
4. Ensure user-friendly interface
5. Test error handling with invalid inputs

### Success Criteria to Verify:
{chr(10).join(f"- {criterion}" for criterion in milestone.success_criteria)}

### Evidence Required:
1. Show main.py running successfully
2. Demonstrate each success criterion working
3. Include example inputs and outputs
4. Save full session log to: .cc_automator/milestones/milestone_{milestone.number}/e2e_evidence.log

Remember: NO mocking in E2E tests - must be real functionality!
""",

            "commit": f"""
## Commit Phase

Create a git commit for Milestone {milestone.number}.

### Tasks:
1. Stage all changes: `git add -A`
2. Create descriptive commit message
3. Commit with conventional format

### Commit Message Format:
```
feat: Complete Milestone {milestone.number} - {milestone.name}

Implemented:
{chr(10).join(f"- {criterion}" for criterion in milestone.success_criteria)}

- All tests passing
- Type checking passes
- Linting passes
- E2E tests verified
```

### Evidence Required:
Show the git commit hash and message.
"""
        }
        
        return prompts.get(phase_type, f"Execute {phase_type} phase for milestone {milestone.number}")
        
    def _add_previous_context(self, prompt: str, phase_type: str, previous_output: str) -> str:
        """Add context from previous phase"""
        
        context_intros = {
            "planning": "## Previous Phase: Research\n\nBased on the research findings:",
            "implement": "## Previous Phase: Planning\n\nFollowing the implementation plan:",
            "lint": "## Previous Phase: Implementation\n\nNow cleaning up the code:",
            "typecheck": "## Previous Phase: Linting\n\nNow adding type safety:",
            "test": "## Previous Phase: Implementation\n\nBased on what was implemented, create tests:",
            "integration": "## Previous Phase: Unit Tests\n\nNow test component interactions:",
            "e2e": "## Previous Phase: Integration Tests\n\nFinally, verify the complete system:",
        }
        
        if phase_type in context_intros:
            prompt = f"{context_intros[phase_type]}\n\n{previous_output}\n\n{prompt}"
            
        return prompt
        
    def _add_evidence_requirements(self, prompt: str, phase_type: str, milestone: Milestone) -> str:
        """Add specific evidence requirements"""
        
        evidence_section = """

## Evidence Requirements

You MUST provide clear evidence that this phase completed successfully:

1. Show exact command outputs (not paraphrased)
2. Include relevant file contents if created/modified  
3. Demonstrate the success criteria are met
4. Save any logs or outputs as specified

**Remember: "Show, don't tell" - provide actual evidence, not just claims.**
"""
        
        return prompt + evidence_section
        
    def _add_self_healing_reminder(self, prompt: str) -> str:
        """Add reminder about self-healing patterns"""
        
        reminder = """

## Self-Healing Patterns Reminder

Follow these patterns for robust code:
- Use relative imports (from ..module import func)
- Test behavior, not implementation
- Handle missing dependencies gracefully  
- Use pathlib for all file operations
- Write descriptive error messages
- Avoid hardcoded paths
"""
        
        return prompt + reminder
        
    def create_phase_specific_claude_md(self, phase_type: str, milestone: Milestone,
                                       phase_name: str) -> Path:
        """Create a phase-specific CLAUDE.md file"""
        
        # Create milestone directory
        milestone_path = self.milestone_dir / f"milestone_{milestone.number}"
        milestone_path.mkdir(parents=True, exist_ok=True)
        
        # Generate prompt
        prompt = self.generate_prompt(phase_type, milestone)
        
        # Create phase-specific CLAUDE.md
        phase_claude_md = milestone_path / f"{phase_name}_CLAUDE.md"
        
        content = f"""# Phase: {phase_name}

## Milestone {milestone.number}: {milestone.name}

{prompt}

## Working Directory
{self.project_dir}

## Important Files
- CLAUDE.md - Main project specification
- main.py - Entry point that must work
- .cc_automator/milestones/milestone_{milestone.number}/ - Milestone outputs
"""
        
        with open(phase_claude_md, 'w') as f:
            f.write(content)
            
        return phase_claude_md