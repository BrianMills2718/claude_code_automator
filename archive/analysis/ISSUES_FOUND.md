# CC_AUTOMATOR3 Issues Found

## 1. Missing Output Requirements (FIXED)
**Issue**: The implement phase prompt was missing the instruction to save output to `.cc_automator/milestones/milestone_{milestone.number}/implement.md`
**Location**: `phase_prompt_generator.py` lines 152-159
**Status**: FIXED - Added output requirement

## 2. Test Phase Assumptions
**Issue**: The test phase prompt assumes tests might not exist and says "If no tests exist for the new functionality, create them" but doesn't provide enough guidance on WHERE to create them or WHAT structure to follow.
**Location**: `phase_prompt_generator.py` lines 178-217
**Problem**: 
- Line 184: "If no tests exist, create comprehensive unit tests"
- Provides example structure but doesn't specify the exact file paths
- Should be more explicit: `tests/unit/test_[module_name].py`

## 3. Context Passing for Test Phase
**Issue**: The test phase gets NO context about what was implemented
**Location**: 
- `context_manager.py` line 60-64: test phase has `needs_previous_output=False`
- `run.py` lines 536-562: Only research, planning, and implement phases capture output for next phase
**Problem**: Test phase doesn't know what functions were implemented, making it harder to write appropriate tests

## 4. Integration Test Phase Context
**Issue**: Same as test phase - integration tests get no context about implementation
**Location**: `context_manager.py` lines 66-70
**Problem**: Integration tests need to know about the components to test their interactions

## 5. E2E Evidence Saving
**Issue**: The e2e phase prompt tells Claude to save evidence but the phase orchestrator might not handle this properly
**Location**: 
- `phase_prompt_generator.py` line 276: Instructs to save to `.cc_automator/milestones/milestone_{milestone.number}/e2e_evidence.log`
- `phase_orchestrator.py` lines 414-456: Only saves evidence for research, planning, implement phases

## 6. Hardcoded Phase Evidence Saving
**Issue**: `phase_orchestrator.py` only saves evidence for specific phases
**Location**: `phase_orchestrator.py` lines 414-415
```python
if phase.name not in ["research", "planning", "implement"]:
    return
```
**Problem**: This prevents e2e evidence from being saved even though the prompt asks for it

## 7. Missing Error Handling for Output Files
**Issue**: When phases are expected to create output files but don't, the system falls back to reading source code but doesn't inform subsequent phases
**Location**: `run.py` lines 346-372 and 537-561
**Problem**: If implement phase doesn't create implement.md, the next phase gets raw source code without context about what was intended

## 8. Commit Phase Gets Limited Context
**Issue**: Commit phase uses `needs_summary_only=True` but might need more details
**Location**: `context_manager.py` lines 78-82
**Problem**: Commit message might be too generic without full implementation details

## 9. Phase Prompts Don't Enforce Output Creation
**Issue**: While prompts say "Save your plan to X" or "Create file Y", there's no verification or enforcement
**Location**: Throughout `phase_prompt_generator.py`
**Problem**: Claude might complete the task but forget to save the output file

## 10. Test Directory Structure Not Enforced (PARTIAL)
**Issue**: Test phases assume `tests/unit`, `tests/integration`, `tests/e2e` directories exist
**Location**: Various prompts in `phase_prompt_generator.py`
**Status**: PARTIALLY ADDRESSED - `setup.py` creates these directories (lines 216-218) but only during initial setup
**Problem**: If directories are deleted or setup wasn't run, tests might fail or be created in wrong locations

## 11. File Parallel Executor Only Handles F-errors for Flake8
**Issue**: The file parallel executor filters to only F-errors but the main lint prompt doesn't specify this
**Location**: 
- `file_parallel_executor.py` line 58: `if error_code.startswith('F'):`
- `phase_prompt_generator.py` line 161: Says "Run flake8 and fix F errors only"
**Status**: Consistent but could be clearer

## 12. No Verification of Phase Success
**Issue**: Phases can claim success without verification that the actual task was completed
**Example**: Lint phase could run without actually fixing all F-errors
**Problem**: No post-execution verification that flake8/mypy/pytest actually pass

## Recommendations:
1. Make test and integration phases receive implementation context
2. Add verification that required output files are created
3. Extend evidence saving to all phases that produce outputs
4. Be more explicit about file paths and directory structures
5. Add fallback handling when expected outputs are missing
6. Add post-phase verification for mechanical phases (lint, typecheck, test)
7. Ensure test directories exist before test phases run