# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

# CC_AUTOMATOR4: SDK Integration Complete with Bug Fix ✅

## Current State - Context Bug FIXED!

**IMPORTANT**: The SDK integration is complete and the root cause of the "write file → error → retry" loop has been identified and fixed!

### Migration Status
- [x] Phase 1: Core SDK integration in phase_orchestrator.py ✅
- [x] Phase 2: Basic async support added ✅
- [ ] Phase 3: Remove completion markers (cosmetic, low priority)
- [x] Phase 4: Session management working ✅
- [x] Phase 5: Evidence-based validation enforced ✅
- [x] Phase 6: Bug fix - Auto-cleanup milestone directories ✅

### Root Cause & Fix
**THE BUG**: When milestone files exist from previous runs, Claude tries to Write to them, gets "File has not been read yet" error, and retries infinitely.

**THE FIX**: Automatically clean up milestone directories when starting fresh (not resuming). This ensures Claude always writes to new files.

```python
# In orchestrator.py line 269
if self.current_phase_idx == 0:  # Starting fresh
    milestone_dir = self.project_dir / ".cc_automator" / "milestones" / f"milestone_{milestone.number}"
    if milestone_dir.exists():
        shutil.rmtree(milestone_dir)
```

## High-Level Architecture

CC_AUTOMATOR4 orchestrates multiple Claude Code SDK instances through isolated phase executions to build complete software projects without human intervention.

### Core Design Principle: Separation of Concerns

**THE MAIN PROBLEM WE'RE SOLVING**: Claude Code often claims success without actually meeting specifications. By separating execution from validation, we ensure each agent only does one job and can't self-validate.

Example:
- Research agent: Only researches, doesn't know about next phases
- Planning agent: Only plans based on research output
- Implementation agent: Only implements based on plan
- **External validation**: No agent validates their own work

### SDK Architecture (WORKING)

```python
# SDK phase execution with validation
async def _execute_with_sdk(self, phase: Phase) -> Dict[str, Any]:
    options = ClaudeCodeOptions(
        max_turns=phase.max_turns,
        allowed_tools=phase.allowed_tools,
        cwd=str(self.working_dir)
    )
    
    messages = []
    async for message in query(prompt=phase.prompt, options=options):
        messages.append(message)
        # Process streaming messages
        
    # CRITICAL: Independent validation
    if phase.status == PhaseStatus.COMPLETED:
        if not self._validate_phase_outputs(phase):
            phase.status = PhaseStatus.FAILED
            phase.error = "Phase validation failed - outputs do not meet requirements"
```

### Phase Execution Flow

```
For each milestone:
  1. Research    → Analyze requirements (creates research.md)
  2. Planning    → Create implementation plan (creates plan.md)
  3. Implement   → Build the solution (creates/modifies code files)
  4. Lint        → Fix F-errors only
  5. Typecheck   → Add type hints
  6. Test        → Create/fix unit tests
  7. Integration → Test component interactions
  8. E2E         → Verify main.py works (NO MOCKING)
  9. Commit      → Create git commit
```

## Usage

```bash
# SDK is now the default mode (uses Claude Max subscription)
python cli.py --project /path/to/project

# Resume from last checkpoint
python cli.py --project /path/to/project --resume

# Run specific milestone only
python cli.py --project /path/to/project --milestone 2

# Verbose mode to see details
python cli.py --project /path/to/project --verbose
```

## Critical Validation Requirements

**NEVER TRUST CLAUDE'S CLAIMS WITHOUT VERIFICATION**

Every phase MUST provide evidence and pass independent validation:

1. **Lint**: `flake8 --select=F` must return zero errors
2. **Typecheck**: `mypy --strict` must pass
3. **Test**: `pytest tests/unit` must pass
4. **Integration**: `pytest tests/integration` must pass  
5. **Research**: Must create research.md with >100 chars
6. **Planning**: Must create plan.md with >50 chars
7. **Implement**: Must create main.py or src/*.py files
8. **E2E**: Must create e2e_evidence.log
9. **Commit**: Must create actual git commit

The `_validate_phase_outputs()` method enforces these requirements.

## Known Issues & Solutions

### Issue: "File has not been read yet" errors
**Status**: FIXED ✅
**Solution**: Automatic cleanup of milestone directories prevents writing to existing files

### Issue: Async cleanup errors after phase completion
**Status**: FIXED ✅
**Solution**: Ignore TaskGroup errors if phase already completed successfully

### Issue: Phase turn limits too low for SDK
**Status**: FIXED ✅
**Solution**: Increased limits (research: 30, planning: 20, implement: 50)

## Next Steps for Further Improvement

1. **Add Edit tool to allowed_tools** for phases that might modify existing files
2. **Update prompts** to hint about checking file existence
3. **Consider persistent context** between phases for better continuity
4. **Remove completion markers** from prompts (cosmetic improvement)

## Testing

```bash
# Test with example project
cd test_example/
python ../cli.py --project . --verbose

# Check logs for any errors
cat .cc_automator/logs/*.log | grep "error"

# Verify milestone files created
ls -la .cc_automator/milestones/milestone_1/
```

## Key Benefits of Current Implementation

1. **Context Preservation** ✅ - SDK maintains conversation history
2. **No Infinite Loops** ✅ - Cleanup prevents write errors
3. **Accurate Costs** ✅ - Per-phase cost tracking  
4. **Session Management** ✅ - Resume/continue support
5. **No API Key Required** ✅ - Uses Claude Max subscription
6. **Validation Enforcement** ✅ - Catches false success claims

## Important Notes

- SDK mode is default (USE_CLAUDE_SDK=true)
- Milestone directories cleaned on fresh starts
- Validation may catch failures - this is good!
- Each phase has specific output requirements
- Logs saved in .cc_automator/logs/

## For Claude Code Agents

When working on this codebase:
1. **Always validate outputs** - Don't trust claims, verify with subprocess
2. **Create required files** - Each phase has specific file requirements
3. **Show evidence** - Include command outputs that prove success
4. **Handle existing files** - Check if files exist before writing
5. **Use absolute paths** - Avoid relative path issues
6. **Remember context** - Previous phases create files you might need

## File Write/Edit Guidelines

**IMPORTANT**: Claude Code has a safety feature:
- **Write tool**: Only for NEW files (or after reading existing ones)
- **Edit tool**: For modifying EXISTING files
- If you get "File has not been read yet", either:
  1. Read the file first, then Write
  2. Use Edit instead of Write
  3. Check if the file should be deleted first

This prevents accidental data loss but can cause confusion if not understood.