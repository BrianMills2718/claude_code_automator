#!/usr/bin/env python3
"""
Phase Prompt Generator for CC_AUTOMATOR3
Generates detailed prompts for each phase with evidence requirements
"""

from pathlib import Path
from typing import Dict, Optional
from .milestone_decomposer import Milestone


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
        
        # Create phase-specific CLAUDE.md if needed
        self._create_phase_claude_md(phase_type, milestone)
        
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
            elif previous_phase_output:
                # If context manager returns empty but we have previous output, use fallback
                prompt = self._add_previous_context(prompt, phase_type, previous_phase_output)
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

**IMPORTANT: Do NOT use TodoWrite tool - just research and write directly.**

1. Check what exists in main.py and requirements.txt
2. Review the project structure and requirements in CLAUDE.md
3. Write your research findings to: .cc_automator/milestones/milestone_{milestone.number}/research.md

The research.md file must contain:
# Research Findings for {milestone.name}

## What Exists
- Summary of main.py (if it exists)
- Current requirements.txt status
- Current project structure

## Requirements Analysis
- What functionality needs to be implemented for this milestone
- What libraries/dependencies are needed (if any)
- Implementation approach based on project type

## Implementation Approach
- Basic code structure needed
- Key functions/classes to implement
- User interface approach (CLI, web, etc.)

## Testing Strategy
- What types of tests are needed
- Test scenarios for this milestone

RESEARCH APPROACH:
1. First, read CLAUDE.md to understand the project type and requirements
2. Check existing code to see what's already implemented
3. Use your knowledge of Python best practices for this type of project
4. Only use WebSearch if you need very specific information about libraries
5. Focus on creating actionable research that guides implementation""",

            "planning": f"""
{milestone_context}

## Planning Phase

**IMPORTANT: Do NOT use TodoWrite tool - just plan and write directly.**

Based on research, create implementation plan.

If research shows functionality is already complete:
1. Document that in plan.md
2. List any minor fixes needed (lint, types)
3. Exit early - no need for detailed planning

Otherwise, create brief plan with:
- Files to create/modify
- Key functions needed
- Basic test approach

Save to: .cc_automator/milestones/milestone_{milestone.number}/plan.md
""",

            "implement": f"""
{milestone_context}

## Implementation Phase

Create the implementation based on the plan.

**IMPORTANT: Do NOT use TodoWrite tool - just implement directly.**

### Tasks:
1. Read the plan.md file to understand requirements
2. Create main.py with the specified functionality
3. Create requirements.txt (usually empty for basic projects)
4. Test that main.py runs without errors
5. Save a brief summary to: .cc_automator/milestones/milestone_{milestone.number}/implement.md

### Implementation Guidelines:
- Follow the exact specifications in plan.md
- Use proper type hints for all functions
- Include error handling as specified
- Keep code simple and readable
- Ensure main.py is the entry point

### Verification:
After implementation, test with: python main.py
""",

            "architecture": f"""
## Architecture Review Phase

Review the implementation for {milestone.name} to ensure good architectural quality BEFORE proceeding to mechanical phases.

### CRITICAL MISSION: Prevent Wasted Cycles

Your goal is to catch architectural issues that would cause lint/typecheck/test phases to waste time and API costs. Fix structural problems NOW, not later.

### Architecture Standards to Enforce:

#### 1. **Code Structure**
- Functions ≤ 50 lines (break down larger ones)
- Classes ≤ 20 methods (split responsibilities)  
- Files ≤ 1000 lines (create modules)
- Nesting depth ≤ 4 levels (flatten complex logic)
- Function parameters ≤ 5 (use data classes/configs)

#### 2. **Import Structure**
- Add missing `__init__.py` files in src/ directories
- Fix circular imports (restructure if needed)
- Use relative imports within project modules
- Group imports: stdlib, third-party, local

#### 3. **Design Patterns**
- Separate UI code from business logic (except main.py)
- Extract hardcoded values to constants/config
- Implement proper error handling patterns
- Use dependency injection for testability

#### 4. **Complexity Management**
- Cyclomatic complexity ≤ 10 per function
- Break down complex conditionals
- Extract repeated code into functions
- Use early returns to reduce nesting

#### 5. **Anti-Pattern Prevention**
- No god objects (classes with too many responsibilities)
- No long parameter lists
- No duplicate code blocks
- No mixed concerns (business logic + UI in same module)

### Required Actions:
1. **Run Architecture Validation**:
```python
from src.architecture_validator import ArchitectureValidator
from pathlib import Path
validator = ArchitectureValidator(Path('.'))
is_valid, issues = validator.validate_all()
print('ARCHITECTURE VALIDATION RESULTS:')
if is_valid:
    print('✓ All architecture checks passed')
else:
    print('✗ Architecture issues found:')
    for issue in issues:
        print(f'  - {{issue}}')
```

2. **Fix ALL Issues Found** - No compromises allowed
3. **Re-run validation** to confirm zero issues
4. **Create architecture_review.md** in milestone directory with:
   - List of issues found and fixed
   - Final validation showing all checks passed
   - Brief explanation of any major restructuring

### SUCCESS CRITERIA:
- Zero architecture violations
- Well-structured, maintainable code
- Clean import structure
- Appropriate complexity levels
- Evidence of thorough review

### FAILURE CONSEQUENCES:
If you skip this review, subsequent phases will waste cycles:
- **Lint phase**: Breaking down monolithic functions
- **Typecheck phase**: Fixing import structure issues  
- **Test phase**: Working around tightly coupled code
- **Integration phase**: Debugging complex interactions

Save results to: .cc_automator/milestones/milestone_{milestone.number}/architecture_review.md

REMEMBER: This phase prevents wasted API costs in later phases. Be thorough!
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

### Quick Check:
1. Look at existing test structure if any
2. Follow existing patterns

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

### IMPORTANT: Verify Before Completing
Before marking this phase complete, run:
`pytest tests/unit -xvs`

All tests must pass. If any fail or pytest can't find tests:
- Check test directory location
- Fix failing tests
- Ensure tests are in tests/unit/

Only complete when all unit tests pass.
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

### IMPORTANT: Verify Before Completing
Before marking this phase complete, run:
`pytest tests/integration -xvs`

If it fails (e.g., directory not found), fix the issue:
- Create missing directories
- Move test files if needed
- Ensure tests are in the correct location

Only complete this phase when pytest runs successfully.
""",

            "e2e": f"""
## End-to-End Test Phase

Verify main.py works correctly for Milestone {milestone.number}.

### Testing Strategy:

**If main.py is interactive (waits for user input):**
- Use echo to provide input: `echo "2 + 3\nquit" | python main.py`
- Or test with timeout: `timeout 5s python main.py` 
- Or test importing: `python -c "import main; print('Import successful')"`

**If main.py is non-interactive:**
- Run directly: `python main.py`

### Tasks:
1. First check if main.py is interactive by looking at the code
2. Test main.py using appropriate method (with input if interactive)
3. Test all features for this milestone  
4. Verify success criteria are met
5. Test error handling with invalid inputs
6. Ensure program exits cleanly

### Success Criteria to Verify:
{chr(10).join(f"- {criterion}" for criterion in milestone.success_criteria)}

### Example for interactive calculator:
```bash
# Test basic operations
echo "2 + 3" | python main.py
echo "10 / 2" | python main.py  
echo "quit" | python main.py

# Test error handling
echo "abc + def" | python main.py
echo "5 / 0" | python main.py
```

### CRITICAL REQUIREMENT - CREATE EVIDENCE LOG:

**YOU MUST CREATE THIS FILE OR THE PHASE WILL FAIL:**
`.cc_automator/milestones/milestone_{milestone.number}/e2e_evidence.log`

Steps to create evidence log:
1. Run all your e2e tests and capture the outputs
2. Use the Write tool to create the evidence log file
3. Include in the log:
   - All command outputs from testing main.py
   - Success/failure status for each test
   - Verification of each success criterion
   - Any error messages encountered

Example evidence log content:
```
E2E Testing Session for Milestone {milestone.number}
===========================================

Test 1: Basic functionality
$ python main.py
[include actual output here]
Status: ✓ PASSED

Test 2: Error handling  
$ python main.py
[include actual output here]
Status: ✓ PASSED

SUCCESS CRITERIA VERIFICATION:
- Criterion 1: ✓ VERIFIED
- Criterion 2: ✓ VERIFIED

CONCLUSION: All tests passed successfully.
```

**VALIDATION WILL FAIL WITHOUT THIS FILE** - the system requires concrete proof of testing!

**IMPORTANT:** Never run interactive programs without providing input - they will hang forever!

Remember: NO mocking in E2E tests - must be real functionality!
""",

            "validate": f"""
## Implementation Validation Phase

Thoroughly validate that ALL functionality for {milestone.name} is REAL and working.

### Critical Checks:

1. **No Mocks in Production Code**
   - Run: `grep -r "mock\\|Mock\\|TODO\\|FIXME\\|NotImplemented" --include="*.py" --exclude-dir=tests .`
   - Ensure NO mocks/stubs in main code (only in tests)

2. **Real Implementations**
   - Check main.py and src/ files for actual implementations
   - No placeholder returns like 'return None # TODO'
   - No hardcoded fake responses

3. **Test ALL Features**
   - Run main.py and test EVERY feature for this milestone
   - Use real inputs, not test data
   - Verify actual functionality works as expected

### Success Criteria to Validate:
{chr(10).join(f"- {criterion}" for criterion in milestone.success_criteria)}

### Required Actions:
1. Run grep to check for mocks/stubs
2. Test each feature with real examples
3. Fix ANY mocked/stubbed code you find
4. Create validation report: .cc_automator/milestones/milestone_{milestone.number}/validation_report.md

The report must confirm:
- No mocks/stubs in production code
- All features tested and working
- Real examples of each feature

IMPORTANT: If you find ANY mocked functionality, you MUST implement it for real before completing this phase.

### FINAL VERIFICATION
Before completing, run these checks:
1. `grep -r "mock\|Mock\|TODO\|FIXME\|NotImplemented" --include="*.py" --exclude-dir=tests .`
   - Must return NO matches in production code
2. `python main.py` with test inputs
   - Must run without errors

Only complete when ALL checks pass.
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
        
    def _create_phase_claude_md(self, phase_type: str, milestone: Milestone) -> None:
        """Create a phase-specific CLAUDE.md file with targeted instructions"""
        
        # Create milestone directory
        milestone_path = self.milestone_dir / f"milestone_{milestone.number}"
        milestone_path.mkdir(parents=True, exist_ok=True)
        
        # Phase-specific CLAUDE.md content
        phase_instructions = {
            "research": f"""# Research Phase Instructions
- Focus on understanding what needs to be built for {milestone.name}
- Check if any functionality already exists
- Identify potential challenges early
- Keep findings concise and actionable
- DO NOT use TodoWrite tool - just do the work directly
- Create completion marker when done
""",
            "planning": f"""# Planning Phase Instructions  
- Create a detailed but not overly verbose plan
- Focus on WHAT to build, not HOW to code it
- Keep the plan under 300 lines for simple features
- Include clear success criteria
- DO NOT use TodoWrite tool - just do the work directly
""",
            "implement": f"""# Implementation Phase Instructions
- Follow the plan exactly - don't add extra features
- Only implement what's needed for Milestone {milestone.number}
- Use subagents to verify your work
- Keep code simple and readable
""",
            "test": f"""# Test Phase Instructions
- Use subagents to find existing test patterns
- Follow the project's test conventions
- Test edge cases and error conditions
- Keep tests focused and fast
""",
            "lint": """# Lint Phase Instructions
- Only fix F-errors (syntax, undefined names)
- Don't fix style issues unless they're F-errors
- Run flake8 with --select=F flag
- DO NOT use TodoWrite tool - just fix the errors
""",
            "typecheck": """# Type Check Phase Instructions
- Add all missing type hints
- Use Union types where appropriate
- Run mypy with --strict flag
- Fix all type errors
"""
        }
        
        if phase_type in phase_instructions:
            phase_claude_md = milestone_path / f"{phase_type}_CLAUDE.md"
            content = phase_instructions[phase_type]
            
            # Add milestone-specific context
            if phase_type in ["implement", "test"]:
                content += f"\n## Milestone {milestone.number} Success Criteria:\n"
                for criterion in milestone.success_criteria:
                    content += f"- {criterion}\n"
            
            with open(phase_claude_md, 'w') as f:
                f.write(content)
        
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