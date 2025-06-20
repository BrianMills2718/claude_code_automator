# CC_AUTOMATOR V4 Planning Document

**Status**: Planning Phase - No implementation started  
**Purpose**: Capture insights from LLM analysis for future development

## Executive Summary

This document captures the analysis and recommendations for CC_AUTOMATOR V4, based on feedback from three different LLMs about meta-agent architecture and system improvements. These ideas align with cc_automator4's core philosophy of evidence-based validation while adding intelligence and efficiency.

## Most Valuable Ideas (Aligned with Philosophy)

### 1. Lightweight Meta-Agent as Event Monitor (Not Controller)

- Start with read-only telemetry collection across phases
- Track patterns like "architecture phase times out after complex implementations"
- Generate insights without changing execution flow
- This preserves the evidence-based validation while adding intelligence

**Key Principle**: Observer, not controller - maintains anti-cheating philosophy

### 2. Structured Event Bus

```python
# Simple implementation in src/telemetry.py
class PhaseEvent:
    phase: str
    status: str
    duration_s: float
    evidence_path: Optional[Path]
    error_details: Optional[dict]
```

This gives meta-agent clean data without coupling to implementation details.

**Implementation Example**:
```python
# In phase_orchestrator.py
async def _execute_phase():
    start_time = time.time()
    try:
        result = await self._run_phase_logic()
        self.telemetry.emit(PhaseEvent(
            phase=self.phase_name,
            status="success",
            duration_s=time.time() - start_time
        ))
    except Exception as e:
        self.telemetry.emit(PhaseEvent(
            phase=self.phase_name, 
            status="failure",
            error_details={"type": type(e).__name__, "message": str(e)}
        ))
```

### 3. Phase Parallelization via DAG

The Phase-DAG concept is excellent. We already do file-level parallelization, but could extend to phase-level:

**Current Sequential Flow** (inefficient):
```
implement (30s) → architecture (10s) → lint (20s) → typecheck (25s) → test (15s)
Total: 100s
```

**DAG-Based Parallel Flow**:
```
implement (30s) → architecture (10s) → {lint, typecheck} → test (15s)
                                         (parallel: 25s)
Total: 80s (20% faster)
```

**Safe Parallelization Opportunities**:

1. **lint + typecheck** (obvious win)
   - Both are read-only analysis
   - No shared state
   - Already have independent validation

2. **research + preflight** (if we add preflight)
   - Research explores external resources
   - Preflight validates local environment
   - No dependencies between them

3. **unit + integration tests** (with care)
   - If tests are properly isolated
   - Would need to ensure no resource conflicts

**Implementation Approach**:
```python
# src/phase_dag.py
class PhaseDependencyGraph:
    def __init__(self):
        self.dependencies = {
            'research': [],
            'planning': ['research'],
            'implement': ['planning'],
            'architecture': ['implement'],
            'lint': ['architecture'],
            'typecheck': ['architecture'],
            'test': ['lint', 'typecheck'],  # Wait for both
            'integration': ['test'],
            'e2e': ['integration'],
            'validate': ['e2e'],
            'commit': ['validate']
        }
    
    def get_ready_phases(self, completed_phases: Set[str]) -> Set[str]:
        """Return phases whose dependencies are all satisfied."""
        ready = set()
        for phase, deps in self.dependencies.items():
            if phase not in completed_phases and all(d in completed_phases for d in deps):
                ready.add(phase)
        return ready
```

**Benefits**:
- 20-30% time savings on mechanical phases
- Better resource utilization
- Cost efficiency (same total API work)

**Risks to Manage**:
- Debugging complexity
- Race conditions in evidence handling
- Resource limits on parallel Claude calls

### 4. Configurable Architecture Thresholds

Moving hardcoded limits to config makes sense:

```yaml
# architecture_config.yml
limits:
  function_lines: 50  # default, adjustable per project type
  class_methods: 20
  file_lines: 1000
  complexity: 10
  nesting_depth: 4
```

## Ideas to Approach Cautiously

### 1. Active Meta-Agent Interventions
- The "rollback to phase X" automation could create unpredictable loops
- Better: Meta-agent suggests interventions, human approves
- Aligns with "never trust agent claims" philosophy

### 2. Relaxing Testing Philosophy
- The "real testing" requirement is core anti-cheating mechanism
- Mocking external dependencies could enable fake success claims
- Keep strict validation, but maybe add "mock allowed" project types

### 3. Too Much Abstraction
- LLM3's "think harder" skepticism is correct
- Keep instructions explicit and verifiable
- Abstract concepts enable Claude to claim understanding without proof

## Implementation Priority

### Phase 1 (High Priority)
1. **Basic telemetry event system** - Foundation for all improvements
2. **Better E2E validation** - Replace nohup with deterministic status files
3. **Simple phase parallelization** - Start with lint + typecheck

### Phase 2 (Medium Priority)
1. **Configurable architecture thresholds** - Via YAML config
2. **Read-only meta-agent** - Pattern analysis without control
3. **Phase dependency graph** - Enable more parallelization

### Phase 3 (Low Priority)
1. **Human checkpoints** - Optional --pause-at-milestone flag
2. **Extended parallelization** - More phase combinations
3. **Advanced telemetry analysis** - Cost optimization insights

## Better E2E Validation Design

Replace nohup approach with deterministic markers:

```python
# Create deterministic success marker
(test_dir / ".e2e_complete").write_text(json.dumps({
    "status": "success",
    "timestamp": time.time(),
    "output_hash": hashlib.sha256(output).hexdigest()
}))
```

## LLM Analysis Summary

**Best advice came from LLM1** because:
- Concrete and actionable (imperative verbs, specific details)
- Risk-aware (shadow-mode validation, bounded control laws)
- Technically grounded (structured events, FSM, proper telemetry)
- Incremental approach (prioritized implementation)

LLM2 was comprehensive but tried to boil the ocean. LLM3 had good strategic thinking but was less actionable.

## Key Principles for V4

1. **Maintain Evidence-Based Validation** - Core anti-cheating mechanism
2. **Observer Before Controller** - Meta-agent watches, doesn't intervene
3. **Incremental Parallelization** - Start simple, expand carefully
4. **Explicit Over Abstract** - Clear, verifiable instructions
5. **Human Escalation** - Keep humans in the loop for critical decisions

## Next Steps

When ready to implement V4:
1. Start with telemetry foundation
2. Add simplest parallelization (lint + typecheck)
3. Build read-only meta-agent
4. Gradually expand based on telemetry insights
5. Always maintain backward compatibility with V3

---

**Note**: This document is for planning purposes only. No implementation should begin until V3 is fully stable and tested.