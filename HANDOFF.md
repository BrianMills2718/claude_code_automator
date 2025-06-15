# CC_AUTOMATOR4 Handoff Document

## Current State
- **Status**: Functional but needs optimization
- **Location**: `/home/brian/autocoder2_cc/cc_automator4` (ready to move to `~/cc_automator4`)
- **Key Issue**: Research/Planning phases take too long due to verbose prompts
- **Documentation**: All references updated to cc_automator4

## What Works
1. All core components are built and integrated
2. Preflight validation ✓
3. Progress tracking and resume ✓
4. Session management ✓
5. Simple version (`archive/experimental/simple_run.py`) completes in 90 seconds

## What Needs Fixing

### 1. Prompt Optimization (PRIORITY)
- Research phase: Remove subagent calls, simplify to core requirements
- Planning phase: Reduce from 300+ line plans to simple file/function lists
- All phases: Remove TodoWrite usage (wastes turns)

### 2. Testing
Create fresh test directory:
```bash
# Option 1: Use existing test_calculator_fresh
cd ~/autocoder2_cc/test_calculator_fresh
python ../cc_automator4/run.py --milestone 1

# Option 2: After moving to home directory
cd ~/cc_automator4
mkdir -p test_projects/calculator_fresh
cd test_projects/calculator_fresh
cp ~/autocoder2_cc/test_calculator/CLAUDE.md .
git init
python ../../run.py --milestone 1
```

### 3. Consider Phase Reordering
Current: Research → Planning → Implement
Better: Pre-Planning → Research → Detailed Planning → Implement

## Quick Start Commands

```bash
# Move to final location
cp -r ~/autocoder2_cc/cc_automator4 ~/cc_automator4
cd ~/cc_automator4

# Run on existing project
cd ~/my_project
cp -r ~/cc_automator4 ./cc_automator
python cc_automator/run.py

# Resume interrupted run
python cc_automator/run.py --resume

# Run specific milestone
python cc_automator/run.py --milestone 1
```

## File Organization

### Core Files
- `run.py` - Main entry point
- `phase_orchestrator.py` - Executes phases
- `phase_prompt_generator.py` - Generates prompts (needs simplification)
- `milestone_decomposer.py` - Extracts milestones from CLAUDE.md

### Experimental (in archive/)
- `simple_run.py` - Proof that simple prompts work
- `hybrid_orchestrator.py` - Template-based approach (not integrated)
- `kiss_orchestrator.py` - Minimal version

### Configuration
- Think modes: Disabled (removed from PHASE_CONFIGS)
- Turn limits: Research=15, Planning=10, Implement=30
- Max timeout: 600 seconds per phase

## Next Steps

1. **Simplify prompts** in phase_prompt_generator.py
2. **Test with fresh directory** (no existing code)
3. **Consider integrating hybrid_orchestrator.py** for cleaner prompts
4. **Add intelligent monitoring** instead of turn limits

## Key Insights from Development

1. **Simple prompts work better** - The 90-second simple_run proves this
2. **TodoWrite is harmful** - Wastes turns on unnecessary task tracking
3. **Fresh directories only** - Don't test with polluted directories
4. **Focus on 99% use case** - Building from scratch, not partial implementations

## Contact
Original context and detailed analysis in CONTEXT_SUMMARY.md