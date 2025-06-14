# CC_AUTOMATOR3 Next Steps Plan

## Current Status (Dec 13, 2024)

### What's Working ✅
1. **Context passing between phases** - Implementation gets full plan
2. **Cleaner output** - Verbose details hidden by default
3. **File-level parallelization** - Implemented but not tested
4. **Git worktree parallelization** - Working for lint/typecheck
5. **Initial implementation phases** - Research, planning, implement succeed

### What's Failing ❌
1. **Test phases hitting 30 turn limit** - Root cause identified
2. **Missing evidence files** - implement.md not being saved
3. **Test phase context mismatch** - Tests expect different architecture than implemented

## Root Cause Analysis

The test phases fail because:
1. Implementation phase doesn't save `implement.md` to document what was built
2. Test phase only sees the plan, not the actual implementation
3. Test phase tries to test based on plan (Calculator class) but implementation did something different (standalone functions)
4. This mismatch causes 30 turns of confusion

## Planned Improvements

### 1. Parallel Assessment Agent (Priority: HIGH)
**Why**: Current hardcoded turn limits and pattern detection are pre-LLM thinking. An LLM can intelligently assess progress.

**Implementation**:
```python
class ParallelAssessmentAgent:
    def spawn_monitor(self, phase_name: str, check_interval: int = 60):
        """Spawn parallel agent to monitor main agent progress"""
        # Runs every 60 seconds without interrupting main agent
        # Reviews recent outputs and assesses:
        # - Is progress being made?
        # - What specific blockers exist?
        # - Should we intervene?
```

**Logic**: 
- No hardcoded patterns needed
- LLM understands context and can identify real issues
- Non-intrusive (runs in parallel)
- Can provide specific guidance for retry

### 2. Evidence File Saving (Priority: CRITICAL)
**Why**: Phases need to save their outputs for next phases to see

**Implementation**:
- Ensure all phases save their primary output to `.cc_automator/milestones/milestone_X/{phase}.md`
- Implementation phase must save what it actually built
- Test phases need to see actual implementation, not just plan

**Fix location**: `phase_orchestrator.py` - add automatic evidence saving

### 3. Research Phase Parallelization (Priority: HIGH)
**Why**: Library research tasks are independent and can run simultaneously

**Implementation**:
```python
def generate_parallel_research_tasks(milestone):
    # Extract all libraries/APIs to verify
    # Create independent research tasks
    # Run in parallel with focused prompts
```

**Focus**: Research should verify current library APIs, not learn general concepts
- "Verify pytest current API for fixtures"
- "Check mypy --strict current flags"
- NOT "Learn testing best practices"

### 4. Incremental Test-Driven Development (Priority: MEDIUM)
**Why**: Enforces TDD best practices, prevents "implement everything then hope" problem

**Implementation**:
```python
# New flow:
1. Implement one function
2. Immediately create its unit test
3. Run test to verify
4. Fix if needed
5. Repeat for next function
```

**Benefits**: 
- Faster feedback loops
- Catches issues immediately
- Enforces best practices humans skip

### 5. Enhanced Progress Monitoring (Priority: MEDIUM)
**Why**: Current "Phase running... (15s elapsed)" gives no insight

**Implementation**:
- Default: Clean terminal + detailed log file
- `--verbose`: Show more progress in terminal
- `--very-verbose`: Show Claude's actual outputs
- Log everything to `.cc_automator/logs/session_[timestamp].log`

**Real-time updates**:
- "Creating src/calculator.py..."
- "Writing function add()..."
- "Running pytest..."

### 6. Smart Context Inclusion (Priority: HIGH)
**Why**: Prevent future failures from outdated knowledge

**Implementation**:
- When phase fails, include failure history in retry
- Show previous attempts and specific errors
- But use assessment agent to decide when to do this

## Implementation Order

### Phase 1: Critical Fixes (Do First)
1. **Fix evidence file saving** - Ensure implement.md is saved
2. **Fix test phase context** - Test phase must see actual implementation
3. **Test with calculator project** - Verify fixes work

### Phase 2: Intelligence Layer (Do Second)
1. **Implement parallel assessment agent** - Monitor and guide stuck phases
2. **Add smart retry context** - Include failure history when retrying
3. **Test assessment agent** - Verify it catches common issues

### Phase 3: Performance Optimizations (Do Third)
1. **Research parallelization** - Run library verifications in parallel
2. **Test file-level parallelization** - Verify it works as expected
3. **Add progress streaming** - Real-time visibility

### Phase 4: Best Practices (Do Fourth)
1. **Incremental TDD flow** - Function-by-function implementation
2. **Enhanced logging** - Multiple verbosity levels
3. **Checkpoint improvements** - Better resume capabilities

## Key Insights

### 1. LLM-Native Thinking
- Use LLMs to assess LLMs (parallel assessment agent)
- No hardcoded patterns or turn limits
- Let intelligence handle intelligence

### 2. Library Verification Focus
- Research phase should verify APIs, not learn concepts
- "What you think you know that ain't so" is the killer
- Always verify current library state

### 3. Evidence Chain
- Each phase must document what it actually did
- Next phase needs to see reality, not just plans
- Broken evidence chain = phase failures

### 4. Enforce Best Practices
- System can enforce TDD, proper testing, etc.
- Humans skip these due to impatience
- System has infinite patience

## Success Metrics

1. **Calculator project completes all 3 milestones** without failures
2. **Test phases complete in <2 minutes** (not 30 turns)
3. **Parallel assessment catches issues** before 30 turns
4. **Research verifies all library APIs** used
5. **Clear progress visibility** throughout execution

## Recovery Plan

If implementation is interrupted:
1. This plan is saved in `NEXT_STEPS_PLAN.md`
2. Current code is committed to git
3. Start with Phase 1 critical fixes
4. Test each improvement before moving to next

## Notes

- Cost is not a concern (user has Claude Max subscription)
- Robustness > Speed (but both are important)
- System should be smarter, not just faster
- Evidence and context flow are critical