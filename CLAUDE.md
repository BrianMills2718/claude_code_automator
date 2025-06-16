# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

# CC_AUTOMATOR4: SDK Integration Complete ✅

## Current State - SDK Migration COMPLETE

**IMPORTANT**: The migration from Claude Code CLI to Claude Code SDK is now complete and working! The context preservation bug that caused "write file → error → retry" loops is fixed.

### Migration Status
- [x] Phase 1: Core SDK integration in phase_orchestrator.py ✅
- [x] Phase 2: Basic async support added ✅
- [ ] Phase 3: Remove completion markers (cosmetic, low priority)
- [x] Phase 4: Session management working ✅
- [x] Phase 5: Evidence-based validation enforced ✅
- [ ] Phase 6: Delete old CLI code (can keep as fallback)

### Key Findings
1. **No API Key Required** - Claude Code SDK works with Claude Max subscription
2. **Context Bug Fixed** - SDK maintains conversation history between attempts
3. **Validation Active** - Each phase output is independently verified
4. **Cost Tracking** - Accurate per-phase cost information

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
  1. Research    → Analyze requirements 
  2. Planning    → Create implementation plan (gets smart context from research)
  3. Implement   → Build the solution (gets plan context)
  4. Lint        → Fix F-errors only
  5. Typecheck   → Add type hints
  6. Test        → Create/fix unit tests
  7. Integration → Test component interactions
  8. E2E         → Verify main.py works (NO MOCKING)
  9. Commit      → Create git commit
```

### Smart Context Management

Instead of passing entire outputs between phases:
```python
# Extract only relevant information
research_output = get_phase_output("research")
planning_context = extract_key_findings(research_output)
# Only pass: existing files found, missing functionality, key decisions
```

## Usage

```bash
# SDK is now the default mode (uses Claude Max subscription)
python cli.py --project /path/to/project

# Resume from last checkpoint
python cli.py --project /path/to/project --resume

# Run specific milestone only
python cli.py --project /path/to/project --milestone 2

# Force old CLI mode (if needed)
export USE_CLAUDE_SDK=false
python cli.py --project /path/to/project
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

## Development Guidelines

1. **Type hints** for all new functions
2. **Test each phase** in isolation
3. **Preserve validation logic** - this is our key differentiator
4. **Document failures** - log why validation failed
5. **Keep evidence** - save all phase outputs

## Known Issues & Solutions

### Issue: "File has not been read yet" errors
**Status**: FIXED ✅
**Solution**: SDK maintains conversation context between attempts

### Issue: Completion markers in prompts
**Status**: Cosmetic issue only
**Solution**: SDK ignores these markers. Can be removed later.

### Issue: Validation too strict
**Status**: By design
**Solution**: Adjust validation thresholds if needed, but never disable

## Testing

```bash
# Test basic SDK functionality
python test_sdk_simple.py

# Test with real project
cd test_example/
python ../cli.py --project . --verbose

# Check logs for context preservation
cat .cc_automator/logs/research_*.log
```

## Key Benefits of SDK Integration

1. **Context Preservation** ✅ - No more infinite retry loops
2. **Better Performance** ✅ - No subprocess overhead  
3. **Accurate Costs** ✅ - Per-phase cost tracking
4. **Session Management** ✅ - Resume/continue support
5. **No API Key Required** ✅ - Uses Claude Max subscription

## Important Notes

- SDK mode is now default (USE_CLAUDE_SDK=true)
- Validation may catch more failures - this is good!
- Each phase has specific output requirements
- Logs are saved in .cc_automator/logs/
- Sessions can be resumed using --resume

## Files Modified for SDK

Key files updated:
1. `phase_orchestrator.py` - Core SDK integration ✅
2. `orchestrator.py` - Basic async support ✅
3. Validation added to ensure outputs meet requirements ✅

## For Claude Code Agents

When working on this codebase:
1. **Always validate outputs** - Don't trust claims, verify with subprocess
2. **Create required files** - Each phase has specific file requirements
3. **Show evidence** - Include command outputs that prove success
4. **Handle errors gracefully** - Read files before writing
5. **Use absolute paths** - Avoid relative path issues