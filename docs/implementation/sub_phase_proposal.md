# Sub-Phase Proposal for CC_AUTOMATOR4

## Problem
- SDK has a 10-minute (600 second) timeout limit
- Complex phases like "implement" (50 turns) often timeout
- Large prompts with many instructions take too long to process

## Solution: Break Phases into Focused Sub-Phases

### 1. Research Phase → 3 Sub-phases
```python
("research_analyze", "Analyze project requirements", 5),
("research_explore", "Explore technical solutions", 5),  
("research_document", "Write research.md summary", 5),
```

### 2. Planning Phase → 3 Sub-phases
```python
("plan_architecture", "Design system architecture", 7),
("plan_tasks", "Break down implementation tasks", 7),
("plan_document", "Write detailed plan.md", 6),
```

### 3. Implementation Phase → 5 Sub-phases
```python
("implement_core", "Create core data structures/models", 10),
("implement_api", "Build API endpoints/interfaces", 10),
("implement_logic", "Implement business logic", 10),
("implement_ui", "Create UI/CLI interface", 10),
("implement_integrate", "Connect all components", 10),
```

### 4. Test Phases → Keep as-is but reduce turns
```python
("lint", "Fix code style issues", 10),  # Down from 20
("typecheck", "Fix type errors", 10),   # Down from 20
("test", "Fix unit tests", 15),         # Down from 25
("integration", "Fix integration tests", 15),  # Down from 25
```

### 5. E2E Phase → 2 Sub-phases
```python
("e2e_setup", "Set up test environment and data", 10),
("e2e_run", "Run end-to-end tests and document", 10),
```

## Benefits

1. **Avoid Timeouts**: Each sub-phase completes in <5 minutes
2. **Better Progress Tracking**: More granular status updates
3. **Easier Recovery**: If one sub-phase fails, others still complete
4. **Focused Prompts**: Each sub-phase has a single clear goal
5. **Reduced Context**: Smaller prompts = faster processing

## Implementation Strategy

### Option 1: Minimal Changes (Recommended)
- Keep existing phase structure
- Add sub-phase execution within each phase
- Aggregate results before validation

```python
async def execute_phase_with_subphases(phase, subphases):
    combined_output = ""
    for subphase_name, subphase_prompt, max_turns in subphases:
        result = await execute_subphase(subphase_name, subphase_prompt, max_turns)
        combined_output += result.output
        if result.failed:
            return PhaseResult(failed=True, output=combined_output)
    return PhaseResult(success=True, output=combined_output)
```

### Option 2: Full Refactor
- Treat each sub-phase as a full phase
- Update validation logic for each sub-phase
- More complex but more flexible

## Example: Research Phase Refactor

Instead of one big prompt:
```python
# OLD: Single monolithic prompt
"Research this project thoroughly. Analyze requirements, explore solutions, 
consider trade-offs, investigate libraries, write comprehensive research.md..."
```

Use focused sub-phases:
```python
# NEW: Sub-phase 1
"Analyze the project requirements in PROJECT_DESCRIPTION.md. 
List the key features and success criteria. Write to requirements.txt."

# NEW: Sub-phase 2  
"Based on requirements.txt, explore technical solutions.
Research relevant libraries and patterns. Write to solutions.txt."

# NEW: Sub-phase 3
"Using requirements.txt and solutions.txt, create research.md 
with a comprehensive analysis and recommendations."
```

## Quick Test

We could test this approach with just the research phase:
```python
# In phase_orchestrator.py, modify research execution
if phase.name == "research":
    # Execute as sub-phases
    sub_results = []
    for sub_prompt in RESEARCH_SUB_PROMPTS:
        result = await self._execute_with_sdk(sub_prompt, max_turns=5)
        sub_results.append(result)
        if not result.success:
            break
    # Combine results
    combined = "\n".join([r.output for r in sub_results])
    return PhaseResult(success=all(r.success for r in sub_results), output=combined)
```