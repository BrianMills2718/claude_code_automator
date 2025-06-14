# CC_AUTOMATOR3 Improvement Plan

## Quick Fixes Needed (Priority 1)

### 1. Fix Test Phase Context Chain
**Problem**: Test/integration phases don't know what was implemented
**Solution**: Pass implementation output to test phases
```python
# In run.py, extend context passing:
if phase_type in ["research", "planning", "implement"]:
    # Save output for next phase
```

### 2. Fix Test Phase Prompts
**Problem**: Prompts say "Fix failing tests" but no tests exist yet
**Solution**: Change prompts to handle both scenarios:
- "Create tests if none exist, then ensure all pass"
- Check if test directories are empty first

### 3. Better Error Detection
**Problem**: Phases hit 30 turns because pytest fails on empty directories
**Solution**: Add pre-check - if no test files exist, create them first

## Major Improvements (Priority 2)

### 1. File-Level Parallelization for Mechanical Fixes
**Status**: High confidence this will work
**Implementation**:
```python
# Instead of:
# All files → Claude → Fix all errors

# Do:
# Run flake8 → Parse output → Spawn parallel workers per file
# Worker 1: Fix errors in main.py only
# Worker 2: Fix errors in src/calc.py only
# etc.
```
**Benefits**: 
- Massive token reduction (each worker only sees one file)
- True parallel fixing (N files = N workers)
- More focused context

### 2. Better Terminal Output
**Problem**: Too verbose for humans, not informative enough about progress
**Solutions**:
a) **Filter agent instructions** - Don't show "Evidence Requirements" section to humans
b) **Add real-time progress** - Stream what's actually happening:
   ```
   Creating main.py...
   Writing function 'add'...
   Running flake8...
   Found 3 errors in main.py
   Fixing undefined variable on line 42...
   ```
c) **Progress bars** for long operations
d) **Summary mode** vs **Verbose mode** options

### 3. Meta-Agent for Dynamic Turn Limits
**Status**: Good idea, medium complexity
**Implementation**:
```python
class TurnLimitWatcher:
    def evaluate_after_turns(self, turns=10):
        # Spawn evaluator to check:
        # - Is Claude stuck in a loop?
        # - Is there a missing file/import?
        # - Should we provide hints or abort?
        # - Can we identify the specific blocker?
```
**Benefits**: Smarter than hardcoded limits, can provide targeted help

### 4. Test Structure Verification
**Status**: High confidence
**Implementation**:
```python
class TestVerifier:
    def verify_tests_complete(self, test_dir):
        # Check for:
        # - Actual test files (not just __init__.py)
        # - Tests import the main code
        # - Tests have assertions
        # - Basic coverage metrics
```

### 5. Smart Recovery from Failures
**Status**: Medium complexity but valuable
**Implementation**:
- Analyze failure type (timeout, file not found, import error)
- Save partial progress
- Provide specific recovery hints
- Resume from last good state

### 6. Pre-Implementation Validation
**Status**: Simple and effective
**Implementation**:
```python
def validate_before_implement(plan_file):
    # Check plan contains:
    # - Specific file names
    # - Function signatures
    # - Not just high-level descriptions
```

## Uncertainties/Questions

### 1. Context Passing Depth
- How much context is too much? 
- Should test phase see ALL of main.py or just function signatures?
- Trade-off: Complete context vs token usage

### 2. Parallel Worker Coordination
- How to handle interdependent files?
- What if two files need to import each other?
- How to merge changes cleanly?

### 3. Meta-Agent Complexity
- How smart should the evaluator be?
- Risk of meta-agent also getting stuck?
- How to make decisions actionable?

### 4. Test Creation Strategy
- Should we generate all tests at once or incrementally?
- How to ensure tests actually test the implementation?
- Balance between thorough testing and execution time

## Implementation Order

### Phase 1: Quick Fixes (1-2 hours)
1. Fix test phase context chain - pass implementation details
2. Update test prompts to handle "create vs fix"  
3. Add pre-checks for empty test directories

### Phase 2: Core Improvements (3-4 hours)
1. File-level parallelization for mechanical fixes
2. Terminal output improvements (filter + real-time progress)
3. Test structure verification

### Phase 3: Advanced Features (2-3 hours)
1. Meta-agent for turn limit management
2. Smart recovery from failures
3. Pre-implementation validation

## Expected Outcomes

### After Quick Fixes:
- Test phases will complete successfully
- Full milestone execution working end-to-end
- ~50% reduction in test phase time

### After Core Improvements:
- 70-80% faster mechanical phases (lint/typecheck)
- Much better visibility into progress
- Higher success rate on complex projects

### After Advanced Features:
- Self-recovering from common failures
- Adaptive to project complexity
- Production-ready robustness

## Notes for Power Loss Recovery
- All code changes are committed to git
- This plan saved in `/home/brian/autocoder2_cc/cc_automator3/IMPROVEMENT_PLAN.md`
- Current state: Context passing fixed, test phases need work
- Next step: Implement quick fixes for test phase context