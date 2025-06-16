"""Sub-phase configurations to break complex phases into smaller chunks."""

# Research phase broken into 3 focused sub-phases
RESEARCH_SUBPHASES = [
    {
        "name": "analyze_requirements",
        "max_turns": 5,
        "prompt_template": """You are in the research phase, focusing on requirements analysis.

Working directory: {working_dir}

Read PROJECT_DESCRIPTION.md and create .cc_automator/milestones/milestone_{milestone_num}/requirements.txt with:
- Key features required
- Success criteria  
- Technical constraints
- Dependencies and prerequisites

Be concise and focused. Do NOT use WebSearch."""
    },
    {
        "name": "explore_solutions",
        "max_turns": 5,
        "prompt_template": """Continue the research phase, focusing on technical solutions.

Working directory: {working_dir}

Read .cc_automator/milestones/milestone_{milestone_num}/requirements.txt and create 
.cc_automator/milestones/milestone_{milestone_num}/solutions.txt with:
- Algorithm choices for each feature
- Design patterns to use
- Testing strategies
- Code structure recommendations

Do NOT use WebSearch."""
    },
    {
        "name": "document_research",
        "max_turns": 5,
        "prompt_template": """Complete the research phase by creating the final documentation.

Working directory: {working_dir}

Read both:
- .cc_automator/milestones/milestone_{milestone_num}/requirements.txt
- .cc_automator/milestones/milestone_{milestone_num}/solutions.txt

Create a file named research.md at the path:
.cc_automator/milestones/milestone_{milestone_num}/research.md

The file should contain:
# Research Summary
## Requirements Analysis
## Technical Approach  
## Implementation Plan
## Risk Assessment

Important: The file must be named exactly 'research.md' (not research_CLAUDE.md or anything else).
This completes the research phase."""
    }
]

# Implementation phase broken into 5 focused sub-phases
IMPLEMENT_SUBPHASES = [
    {
        "name": "create_structure",
        "max_turns": 10,
        "prompt_template": """You are in the implementation phase, creating project structure.

Working directory: {working_dir}

Based on the plan in .cc_automator/milestones/milestone_{milestone_num}/plan.md:
1. Create the basic project structure (directories, __init__.py files)
2. Set up the main module structure
3. Create placeholder files for all planned components

Focus only on structure creation, not implementation."""
    },
    {
        "name": "implement_core", 
        "max_turns": 10,
        "prompt_template": """Continue implementation, focusing on core functionality.

Working directory: {working_dir}

Implement the core algorithms and data structures based on the plan.
This includes the main business logic but not interfaces or helpers.
Focus on getting the core functionality working correctly."""
    },
    {
        "name": "add_interfaces",
        "max_turns": 10,
        "prompt_template": """Continue implementation, adding user interfaces.

Working directory: {working_dir}

Add user-facing interfaces (CLI, API endpoints, or main.py) to interact 
with the core functionality you've implemented. Ensure users can access
all features through these interfaces."""
    },
    {
        "name": "add_helpers",
        "max_turns": 10,
        "prompt_template": """Continue implementation, adding support code.

Working directory: {working_dir}

Add utility functions, error handling, input validation, and logging.
Ensure the code is robust and handles edge cases properly."""
    },
    {
        "name": "final_integration",
        "max_turns": 10,
        "prompt_template": """Complete the implementation phase.

Working directory: {working_dir}

1. Ensure all components work together properly
2. Add any missing imports or connections
3. Verify main.py (or equivalent) runs successfully
4. Add basic documentation/docstrings

The implementation should be complete and functional after this step."""
    }
]

# Planning phase could also be broken down if needed
PLANNING_SUBPHASES = [
    {
        "name": "design_architecture",
        "max_turns": 7,
        "prompt_template": """You are in the planning phase, focusing on system architecture.

Working directory: {working_dir}

Read .cc_automator/milestones/milestone_{milestone_num}/research.md and create
.cc_automator/milestones/milestone_{milestone_num}/architecture.txt with:
- High-level system design
- Component breakdown
- Data flow between components
- Key design decisions"""
    },
    {
        "name": "plan_implementation",
        "max_turns": 7,
        "prompt_template": """Continue planning, focusing on implementation details.

Working directory: {working_dir}

Read .cc_automator/milestones/milestone_{milestone_num}/architecture.txt and create
.cc_automator/milestones/milestone_{milestone_num}/implementation_tasks.txt with:
- Detailed task breakdown
- Implementation order
- File structure
- Function/class signatures"""
    },
    {
        "name": "finalize_plan",
        "max_turns": 6,
        "prompt_template": """Complete the planning phase.

Working directory: {working_dir}

Read both:
- .cc_automator/milestones/milestone_{milestone_num}/architecture.txt
- .cc_automator/milestones/milestone_{milestone_num}/implementation_tasks.txt

Then create a file named plan.md at the path:
.cc_automator/milestones/milestone_{milestone_num}/plan.md

The file should contain a comprehensive plan including:
- Project structure
- Implementation steps
- Testing strategy
- Success criteria"""
    }
]

def get_subphases(phase_name: str) -> list:
    """Get sub-phase configuration for a given phase."""
    configs = {
        "research": RESEARCH_SUBPHASES,
        "planning": PLANNING_SUBPHASES,
        "implement": IMPLEMENT_SUBPHASES,
    }
    return configs.get(phase_name, [])