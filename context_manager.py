#!/usr/bin/env python3
"""
Context Manager for CC_AUTOMATOR3
Provides exactly the right context for each phase to improve focus and robustness
"""

from typing import Dict, List, Optional, Tuple
from pathlib import Path
import json
from dataclasses import dataclass

@dataclass
class PhaseContext:
    """Defines what context a phase needs"""
    needs_previous_output: bool = True
    needs_files: List[str] = None
    needs_summary_only: bool = False
    max_file_size: int = 10000  # Max chars per file
    
    def __post_init__(self):
        if self.needs_files is None:
            self.needs_files = []


class ContextManager:
    """Manages context for each phase to ensure focused execution"""
    
    # Define what each phase actually needs
    PHASE_CONTEXTS = {
        "research": PhaseContext(
            needs_previous_output=False,
            needs_files=["CLAUDE.md", "README.md", "requirements.txt"],
            needs_summary_only=False
        ),
        
        "planning": PhaseContext(
            needs_previous_output=True,  # Needs research output
            needs_files=["CLAUDE.md"],  # For success criteria
            needs_summary_only=True  # Just research summary, not full details
        ),
        
        "implement": PhaseContext(
            needs_previous_output=True,  # Needs the plan
            needs_files=[],  # Plan should contain all needed info
            needs_summary_only=False  # Need full plan details
        ),
        
        "lint": PhaseContext(
            needs_previous_output=False,  # Doesn't need implementation details
            needs_files=["*.py"],  # Just Python files to lint
            needs_summary_only=False
        ),
        
        "typecheck": PhaseContext(
            needs_previous_output=False,  # Doesn't need lint details
            needs_files=["*.py", "py.typed"],  # Python files + type markers
            needs_summary_only=False
        ),
        
        "test": PhaseContext(
            needs_previous_output=False,  # Doesn't need typecheck details
            needs_files=["src/**/*.py", "tests/unit/**/*.py"],  # Source and unit tests
            needs_summary_only=False
        ),
        
        "integration": PhaseContext(
            needs_previous_output=False,  # Doesn't need unit test details
            needs_files=["src/**/*.py", "tests/integration/**/*.py"],
            needs_summary_only=False
        ),
        
        "e2e": PhaseContext(
            needs_previous_output=False,  # Doesn't need integration details
            needs_files=["main.py", "README.md", "tests/e2e/**/*.py"],
            needs_summary_only=False
        ),
        
        "commit": PhaseContext(
            needs_previous_output=True,  # Needs to know what was done
            needs_files=[],  # Git will show the changes
            needs_summary_only=True  # Just a summary of all phases
        )
    }
    
    def __init__(self, project_dir: Path):
        self.project_dir = Path(project_dir)
        self.phase_outputs_dir = self.project_dir / ".cc_automator" / "phase_outputs"
        self.phase_outputs_dir.mkdir(exist_ok=True, parents=True)
    
    def get_phase_context(self, phase_type: str, previous_output: Optional[str] = None,
                         milestone_number: int = 1) -> str:
        """Get the appropriate context for a phase"""
        
        context_parts = []
        phase_ctx = self.PHASE_CONTEXTS.get(phase_type, PhaseContext())
        
        # Add previous phase output if needed
        if phase_ctx.needs_previous_output and previous_output:
            if phase_ctx.needs_summary_only:
                summary = self._extract_summary(previous_output)
                context_parts.append(f"## Previous Phase Summary\n\n{summary}")
            else:
                context_parts.append(f"## Previous Phase Output\n\n{previous_output}")
        
        # Add required files
        if phase_ctx.needs_files:
            file_contents = self._get_file_contents(phase_ctx.needs_files, phase_ctx.max_file_size)
            if file_contents:
                context_parts.append(f"## Relevant Files\n\n{file_contents}")
        
        # Add phase-specific context
        specific_context = self._get_phase_specific_context(phase_type, milestone_number)
        if specific_context:
            context_parts.append(specific_context)
        
        return "\n\n".join(context_parts)
    
    def _extract_summary(self, text: str) -> str:
        """Extract summary from phase output"""
        
        # Look for summary sections
        summary_markers = [
            "## Summary", "## Conclusion", "## Results", 
            "## Key Findings", "## Overview", "## Outcome"
        ]
        
        lines = text.split('\n')
        summary_lines = []
        in_summary = False
        
        for line in lines:
            # Check if we're entering a summary section
            if any(marker in line for marker in summary_markers):
                in_summary = True
                summary_lines.append(line)
                continue
            
            # If in summary, collect lines until next section
            if in_summary:
                if line.startswith('#') and not any(marker in line for marker in summary_markers):
                    break
                summary_lines.append(line)
        
        # If no summary found, extract key points
        if not summary_lines:
            # Extract lines with key indicators
            key_indicators = ['complete', 'success', 'implement', 'creat', 'add', 'fix', 'test', 'pass']
            for line in lines:
                if any(indicator in line.lower() for indicator in key_indicators):
                    summary_lines.append(line)
                    if len(summary_lines) > 10:
                        break
        
        return '\n'.join(summary_lines) if summary_lines else text[:500] + "..."
    
    def _get_file_contents(self, patterns: List[str], max_size: int) -> str:
        """Get contents of files matching patterns"""
        
        contents = []
        
        for pattern in patterns:
            if pattern.endswith("**/*.py"):
                # Handle recursive patterns
                base_path = self.project_dir / pattern.split('**')[0]
                if base_path.exists():
                    for py_file in base_path.rglob("*.py"):
                        if py_file.is_file():
                            content = self._read_file_safely(py_file, max_size)
                            if content:
                                contents.append(f"### {py_file.relative_to(self.project_dir)}\n```python\n{content}\n```")
            
            elif pattern == "*.py":
                # Handle root Python files
                for py_file in self.project_dir.glob("*.py"):
                    if py_file.is_file():
                        content = self._read_file_safely(py_file, max_size)
                        if content:
                            contents.append(f"### {py_file.name}\n```python\n{content}\n```")
            
            else:
                # Handle specific files
                file_path = self.project_dir / pattern
                if file_path.exists() and file_path.is_file():
                    content = self._read_file_safely(file_path, max_size)
                    if content:
                        contents.append(f"### {pattern}\n```\n{content}\n```")
        
        return '\n\n'.join(contents)
    
    def _read_file_safely(self, file_path: Path, max_size: int) -> Optional[str]:
        """Read file with size limit"""
        try:
            content = file_path.read_text()
            if len(content) > max_size:
                return content[:max_size] + f"\n... (truncated, {len(content) - max_size} chars omitted)"
            return content
        except Exception:
            return None
    
    def _get_phase_specific_context(self, phase_type: str, milestone_number: int) -> Optional[str]:
        """Get phase-specific context additions"""
        
        specific_contexts = {
            "lint": """## Lint Guidelines
- Only fix F-errors (flake8 --select=F)
- F401: unused imports
- F841: unused variables
- F821: undefined names
- Ignore style issues (E/W codes)""",
            
            "typecheck": """## Type Check Guidelines
- Use mypy --strict
- All functions need type hints
- Use Optional[] for nullable types
- Import types from typing module""",
            
            "test": """## Unit Test Guidelines
- Test each function in isolation
- Mock external dependencies
- Test edge cases
- Aim for high coverage""",
            
            "integration": """## Integration Test Guidelines
- Test component interactions
- Minimal mocking (only external services)
- Test data flow between modules""",
            
            "e2e": """## E2E Test Guidelines
- NO mocking allowed
- Test through main.py only
- Simulate real user workflows
- Verify actual outputs""",
            
            "commit": f"""## Commit Guidelines
- Summarize Milestone {milestone_number} changes
- Use conventional commit format
- Include all changed files
- Reference completed tests"""
        }
        
        return specific_contexts.get(phase_type)
    
    def save_phase_output(self, phase_type: str, milestone_number: int, output: str):
        """Save phase output for future reference"""
        
        output_file = self.phase_outputs_dir / f"milestone_{milestone_number}_{phase_type}.md"
        output_file.write_text(output)
    
    def get_milestone_summary(self, milestone_number: int) -> str:
        """Get summary of all phases for a milestone"""
        
        phase_types = ["research", "planning", "implement", "lint", "typecheck", "test", "integration", "e2e"]
        summaries = []
        
        for phase in phase_types:
            output_file = self.phase_outputs_dir / f"milestone_{milestone_number}_{phase}.md"
            if output_file.exists():
                output = output_file.read_text()
                summary = self._extract_summary(output)
                summaries.append(f"### {phase.title()} Phase\n{summary}")
        
        return "\n\n".join(summaries) if summaries else "No phase outputs found"