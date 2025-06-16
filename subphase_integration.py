"""Example of how to integrate sub-phases into existing phase_orchestrator.py"""

# Add to phase_orchestrator.py after PHASE_CONFIGS

RESEARCH_SUBPHASES = [
    ("analyze_requirements", """Read PROJECT_DESCRIPTION.md and create requirements.txt 
     listing key features and success criteria.""", 5),
    ("explore_solutions", """Read requirements.txt and create solutions.txt with 
     technical approaches and algorithm choices.""", 5),
    ("write_research", """Read requirements.txt and solutions.txt, then create 
     comprehensive research.md.""", 5),
]

IMPLEMENT_SUBPHASES = [
    ("create_structure", """Create project structure with __init__.py files and 
     basic module organization.""", 10),
    ("implement_core", """Implement the core algorithms and data structures 
     based on plan.md.""", 10),
    ("add_interfaces", """Add user-facing interfaces (CLI/API) to interact 
     with core functionality.""", 10),
    ("add_helpers", """Add utility functions, error handling, and logging.""", 10),
    ("final_integration", """Ensure all components work together and main.py 
     runs successfully.""", 10),
]

# Modified _execute_phase method
async def _execute_phase_with_subphases(self, phase: Phase, prompt: str, 
                                       max_attempts: int = 3) -> PhaseResult:
    """Execute a phase, potentially broken into sub-phases."""
    
    # Determine if this phase should use sub-phases
    subphases = None
    if phase.name == "research" and hasattr(self, 'use_subphases') and self.use_subphases:
        subphases = RESEARCH_SUBPHASES
    elif phase.name == "implement" and hasattr(self, 'use_subphases') and self.use_subphases:
        subphases = IMPLEMENT_SUBPHASES
        
    if not subphases:
        # Execute normally without sub-phases
        return await self._execute_phase(phase, prompt, max_attempts)
        
    # Execute with sub-phases
    print(f"\nExecuting {phase.name} phase with {len(subphases)} sub-phases")
    
    combined_output = []
    all_success = True
    total_cost = 0.0
    
    for i, (sub_name, sub_prompt_template, sub_max_turns) in enumerate(subphases):
        print(f"\n[{i+1}/{len(subphases)}] Running sub-phase: {sub_name}")
        
        # Build sub-phase prompt with context
        sub_prompt = f"""You are in the {phase.name} phase, sub-phase: {sub_name}

Working directory: {self.working_dir.name}
Milestone: {getattr(self, 'current_milestone_name', 'Milestone 1')}

Current task: {sub_prompt_template}

Previous sub-phase outputs are available in:
- .cc_automator/milestones/milestone_1/requirements.txt
- .cc_automator/milestones/milestone_1/solutions.txt

Important: Do NOT use WebSearch. Focus on the specific task above.
Complete this sub-phase efficiently."""
        
        # Execute sub-phase
        try:
            result = await self._execute_with_sdk(
                phase=phase,
                prompt=sub_prompt,
                max_turns_override=sub_max_turns
            )
            
            combined_output.append(f"=== Sub-phase: {sub_name} ===\n{result.output}")
            total_cost += result.cost_usd
            
            if not result.success:
                print(f"Sub-phase {sub_name} failed")
                all_success = False
                break  # Stop on first failure
                
        except Exception as e:
            print(f"Sub-phase {sub_name} error: {e}")
            all_success = False
            break
            
    # Validate the complete phase output
    if all_success:
        all_success = self._validate_phase_outputs(phase)
        
    return PhaseResult(
        success=all_success,
        output="\n\n".join(combined_output),
        cost_usd=total_cost,
        should_retry=not all_success,
        retry_reason=f"{phase.name} sub-phases incomplete" if not all_success else None
    )

# Add option to CLI
def add_subphase_argument(parser):
    """Add --subphases flag to enable sub-phase execution."""
    parser.add_argument(
        '--subphases',
        action='store_true',
        help='Break complex phases into smaller sub-phases to avoid timeouts'
    )

# Usage in orchestrator.py
def __init__(self, ..., use_subphases: bool = False):
    self.use_subphases = use_subphases
    # ... rest of init