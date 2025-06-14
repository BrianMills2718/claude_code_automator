#!/usr/bin/env python3
"""
Milestone Decomposer for CC_AUTOMATOR3
Extracts and manages milestones from CLAUDE.md
"""

import re
from pathlib import Path
from typing import List, Dict, Optional, Tuple
from dataclasses import dataclass


@dataclass
class Milestone:
    """Represents a project milestone"""
    number: int
    name: str
    description: str
    success_criteria: List[str]
    
    def is_vertical_slice(self) -> bool:
        """Check if milestone produces runnable software"""
        keywords = ["main.py", "runnable", "working", "executable", "can be tested"]
        full_text = f"{self.name} {self.description} {' '.join(self.success_criteria)}".lower()
        return any(keyword in full_text for keyword in keywords)


class MilestoneDecomposer:
    """Decomposes project into executable milestones"""
    
    def __init__(self, project_dir: Path):
        self.project_dir = Path(project_dir)
        self.claude_md = self.project_dir / "CLAUDE.md"
        self.milestones: List[Milestone] = []
        
    def extract_milestones(self) -> List[Milestone]:
        """Extract milestones from CLAUDE.md"""
        if not self.claude_md.exists():
            raise FileNotFoundError(f"CLAUDE.md not found in {self.project_dir}")
            
        with open(self.claude_md) as f:
            content = f.read()
            
        self.milestones = self._parse_milestones(content)
        return self.milestones
        
    def _parse_milestones(self, content: str) -> List[Milestone]:
        """Parse milestone sections from markdown content"""
        milestones = []
        
        # Look for Milestones section
        milestones_section = self._extract_section(content, "Milestones")
        if not milestones_section:
            print("Warning: No Milestones section found in CLAUDE.md")
            return []
            
        # Find individual milestones (### Milestone N: Title)
        milestone_pattern = r'###\s+Milestone\s+(\d+):\s*(.+?)(?=###\s+Milestone|\Z)'
        matches = re.findall(milestone_pattern, milestones_section, re.DOTALL)
        
        for match in matches:
            number = int(match[0])
            rest = match[1].strip()
            
            # Extract title and content
            lines = rest.split('\n')
            name = lines[0].strip()
            
            # Extract description and criteria
            description = ""
            criteria = []
            
            for line in lines[1:]:
                line = line.strip()
                if line.startswith('- '):
                    criteria.append(line[2:])
                elif line and not line.startswith('#'):
                    if description:
                        description += " " + line
                    else:
                        description = line
                        
            milestone = Milestone(
                number=number,
                name=name,
                description=description,
                success_criteria=criteria
            )
            
            milestones.append(milestone)
            
        return sorted(milestones, key=lambda m: m.number)
        
    def _extract_section(self, content: str, section_name: str) -> Optional[str]:
        """Extract a specific section from markdown content"""
        # Look for ## Section Name
        pattern = rf'##\s+{re.escape(section_name)}\s*\n(.*?)(?=\n##\s+|\Z)'
        match = re.search(pattern, content, re.DOTALL)
        
        if match:
            return match.group(1).strip()
        return None
        
    def validate_milestones(self) -> Tuple[bool, List[str]]:
        """Validate that milestones are proper vertical slices"""
        if not self.milestones:
            return False, ["No milestones found"]
            
        issues = []
        
        for milestone in self.milestones:
            if not milestone.is_vertical_slice():
                issues.append(
                    f"Milestone {milestone.number} '{milestone.name}' may not produce runnable software"
                )
                
            if not milestone.success_criteria:
                issues.append(
                    f"Milestone {milestone.number} '{milestone.name}' has no success criteria"
                )
                
        return len(issues) == 0, issues
        
    def get_milestone_phases(self, milestone: Milestone) -> List[Dict[str, str]]:
        """Get all phases for a specific milestone"""
        phases = []
        
        # Standard phases from specification
        phase_configs = [
            ("research", f"Research requirements for: {milestone.name}"),
            ("planning", f"Create implementation plan for: {milestone.name}"),
            ("implement", f"Implement: {milestone.name}"),
            ("lint", "Fix all flake8 issues"),
            ("typecheck", "Fix all mypy type errors"),
            ("test", "Fix all failing unit tests"),
            ("integration", "Fix all integration test failures"),
            ("e2e", "Ensure main.py runs successfully for this milestone's features"),
            ("commit", f"Commit milestone {milestone.number}: {milestone.name}")
        ]
        
        for phase_name, phase_desc in phase_configs:
            phases.append({
                "name": f"milestone_{milestone.number}_{phase_name}",
                "type": phase_name,
                "description": phase_desc,
                "milestone": milestone.number,
                "milestone_name": milestone.name
            })
            
        return phases
        
    def get_all_phases(self) -> List[Dict[str, str]]:
        """Get all phases for all milestones"""
        all_phases = []
        
        for milestone in self.milestones:
            all_phases.extend(self.get_milestone_phases(milestone))
            
        return all_phases
        
    def create_milestone_context(self, milestone: Milestone) -> str:
        """Create context information for a milestone"""
        context = f"""# Milestone {milestone.number}: {milestone.name}

## Description
{milestone.description}

## Success Criteria
"""
        for criterion in milestone.success_criteria:
            context += f"- {criterion}\n"
            
        # Add context from previous milestones
        if milestone.number > 1:
            context += "\n## Previous Milestones Completed\n"
            for prev in self.milestones:
                if prev.number < milestone.number:
                    context += f"- Milestone {prev.number}: {prev.name}\n"
                    
        return context
        
    def create_phase_prompt(self, phase: Dict[str, str], milestone: Milestone) -> str:
        """Create a detailed prompt for a specific phase"""
        phase_type = phase["type"]
        milestone_context = self.create_milestone_context(milestone)
        
        prompts = {
            "research": f"""
{milestone_context}

Analyze the requirements for this milestone and research the best approach.
Consider:
1. What components need to be built
2. How they should interact
3. What patterns to use
4. Potential challenges

Save your findings to: .cc_automator/milestones/milestone_{milestone.number}/research.md
""",
            
            "planning": f"""
{milestone_context}

Based on the research findings, create a detailed implementation plan.
Include:
1. File structure to create/modify
2. Key functions and their signatures  
3. Data flow between components
4. Test cases to implement

Save your plan to: .cc_automator/milestones/milestone_{milestone.number}/plan.md
""",
            
            "implement": f"""
{milestone_context}

Implement the functionality according to the plan.
Remember:
- Follow the self-healing patterns from CLAUDE.md
- Ensure main.py works for this milestone's features
- Write clean, documented code

After implementation, run: python main.py
to verify it works.
""",
            
            "lint": """
Run flake8 with: flake8 --max-line-length=100

Fix ALL issues reported. Focus on real code problems, not just style.
Run flake8 again to verify all issues are resolved.
""",
            
            "typecheck": """
Run mypy with: mypy --strict .

Fix ALL type errors reported.
Add type hints where missing.
Run mypy again to verify all issues are resolved.
""",
            
            "test": """
Run pytest with: pytest tests/unit -xvs

Fix any failing tests. 
If no tests exist for the new functionality, create them.
Ensure all tests pass.
""",
            
            "integration": """
Run integration tests with: pytest tests/integration -xvs

Fix any failing integration tests.
Ensure components work together correctly.
All tests must pass.
""",
            
            "e2e": f"""
Run the application with: python main.py

Verify that all features for Milestone {milestone.number} work correctly:
{chr(10).join(f"- {criterion}" for criterion in milestone.success_criteria)}

The application must run without errors and demonstrate the required functionality.
Save evidence of successful execution to: .cc_automator/milestones/milestone_{milestone.number}/e2e_evidence.log
""",
            
            "commit": f"""
Create a git commit for this milestone with:

git add -A
git commit -m "feat: Complete Milestone {milestone.number} - {milestone.name}

{milestone.description}

Completed:
{chr(10).join(f"- {criterion}" for criterion in milestone.success_criteria)}
"

Ensure all changes are committed successfully.
"""
        }
        
        return prompts.get(phase_type, f"Execute {phase_type} phase for milestone {milestone.number}")


if __name__ == "__main__":
    # Test the decomposer
    import sys
    
    project_dir = Path(sys.argv[1]) if len(sys.argv) > 1 else Path.cwd()
    
    decomposer = MilestoneDecomposer(project_dir)
    
    try:
        milestones = decomposer.extract_milestones()
        
        print(f"Found {len(milestones)} milestones:\n")
        
        for milestone in milestones:
            print(f"Milestone {milestone.number}: {milestone.name}")
            print(f"  Description: {milestone.description}")
            print(f"  Vertical Slice: {'✓' if milestone.is_vertical_slice() else '✗'}")
            print(f"  Success Criteria:")
            for criterion in milestone.success_criteria:
                print(f"    - {criterion}")
            print()
            
        # Validate
        valid, issues = decomposer.validate_milestones()
        if not valid:
            print("Validation issues:")
            for issue in issues:
                print(f"  - {issue}")
        else:
            print("✓ All milestones validated successfully")
            
        # Show phases
        print(f"\nTotal phases to execute: {len(decomposer.get_all_phases())}")
        
    except FileNotFoundError as e:
        print(f"Error: {e}")
        sys.exit(1)