# CC_AUTOMATOR4 Implementation Guide

**FOR CLAUDE CODE AGENTS**: This guide contains the exact directives, patterns, and next steps needed to implement the current stability work. Follow these instructions precisely.

## 🚨 CURRENT MISSION: SYSTEM STABILITY

**OBJECTIVE**: Build a stable, honest SDK wrapper that eliminates all errors
**STATUS**: ✅ SDK tests passing - fixed actual bugs in message parsing, did not weaken tests
**APPROACH**: Fix foundational issues before any feature work

### CORE DIRECTIVES

**1. Absolute Honesty**: NEVER claim success without proof. All test failures = critical bugs.
**2. SDK Stability First**: One consolidated wrapper that passes ALL tests.
**3. Evidence-Based Validation**: Independent verification of all claims.
**4. Fail Fast**: Surface problems immediately, don't mask them.

### IMMEDIATE TASKS (PHASE 1: SDK STABILIZATION)

**CURRENT BLOCKER**: `tests/sdk/manual_sdk_test.py` failing on JSON repair
**ROOT FILES**: 
- `src/claude_code_sdk_stable.py` (consolidated SDK wrapper)
- `tests/sdk/manual_sdk_test.py` (stability test suite)

**NEXT STEPS**:
1. **Debug test failure**: Run test, identify exact error in JSON repair method
2. **Fix bug**: Repair the `_repair_truncated_json()` method  
3. **Verify**: Re-run tests until 100% pass
4. **Document**: Update success criteria checkmarks

**SUCCESS CRITERIA**: ✅ All tests in `tests/sdk/manual_sdk_test.py` pass without errors.

### IMPLEMENTATION PATTERNS

**Error Classification Strategy**:
```python
# Handle ALL known SDK error types
def _classify_error(self, error: Exception) -> SDKErrorType:
    error_str = str(error).lower()
    if "taskgroup" in error_str: return SDKErrorType.TASKGROUP_ERROR
    if "json" in error_str and "decode" in error_str: return SDKErrorType.JSON_DECODE_ERROR
    # ... handle all types, never return unknown
```

**Test-Driven Validation**:
```python
# Every component MUST have tests that prove it works
def test_critical_functionality():
    """Test fails = feature doesn't work = BLOCK ALL OTHER WORK"""
    result = component.do_critical_thing()
    assert result.success == True  # Hard requirement
```

**Session Management Pattern**:
```python
# Always use managed contexts with guaranteed cleanup
async with wrapper.managed_session("operation") as session_id:
    # Do work here
    # Cleanup is guaranteed even on errors
```

### FILE ORGANIZATION

**Core Stability Files**:
- `src/claude_code_sdk_stable.py` - Consolidated SDK wrapper (consolidates v2, v4 fixes)
- `tests/sdk/manual_sdk_test.py` - Test suite that MUST pass 100%
- `tools/debug/logs/` - SDK operation logs for debugging

**Reference Documentation**:
- See `docs/implementation/` for detailed patterns
- See `tools/debug/` for diagnostic tools
- See existing `src/claude_code_sdk_fixed_v*.py` for previous attempts

### ANTI-PATTERNS TO AVOID

❌ **Claiming success without tests**: "The wrapper works" without passing tests
❌ **Masking errors**: Catching exceptions and continuing silently  
❌ **Fragmented fixes**: Creating yet another SDK wrapper instead of consolidating
❌ **Feature creep**: Adding new functionality before stability is achieved

### NEXT PHASE TRIGGERS

**PHASE 2** (Enhanced E2E Validation) can ONLY start when:
- ✅ All SDK tests pass 100%
- ✅ SDK can execute 10+ consecutive operations without failure  
- ✅ No CLIJSONDecodeError or TaskGroup errors in logs

**PHASE 3** (Recovery Tool Verification) depends on Phase 2 completion.
**PHASE 4** (System Integration) depends on Phase 3 completion.

### DEBUGGING STRATEGY

1. **Run the failing test**: `python tests/sdk/manual_sdk_test.py`
2. **Identify exact failure**: Look for the specific error message
3. **Fix the root cause**: Modify `src/claude_code_sdk_stable.py`
4. **Verify fix**: Re-run test until it passes
5. **Test thoroughly**: Ensure fix doesn't break other functionality

### SUCCESS MEASUREMENT

**Current Target**: ✅ Make this command succeed:
```bash
python tests/sdk/manual_sdk_test.py
# Expected output: "🎉 ALL TESTS PASSED - SDK IS STABLE"
```

**✅ PHASE 1 COMPLETE**: Fixed actual bugs by properly handling message formats in SDK wrapper.

**PROJECT ROOT**: `/home/brian/cc_automator4/`
**MAIN ENTRY**: `cli.py`
**CORE LOGIC**: `src/orchestrator.py`, `src/phase_orchestrator.py`

### CURRENT PHASE REFERENCES

**Blocked until Phase 1 complete**: All V4 meta-agent development, enhanced E2E validation, recovery tool verification.

**Reference Documentation**: See `docs/implementation/` for detailed patterns when Phase 1 is complete.