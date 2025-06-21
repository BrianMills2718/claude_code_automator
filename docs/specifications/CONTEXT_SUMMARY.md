# CC_AUTOMATOR3 Context Summary

## Current Status

### What's Built
1. **Main System (run.py)**
   - Full orchestration with 9 phases
   - Progress tracking and resume capability
   - Parallel execution support (disabled for debugging)
   - Session management and logging

2. **Hybrid Approach (hybrid_orchestrator.py)**
   - Clean markdown templates in `.claude/commands/`
   - Template-based prompts with argument substitution
   - Not yet integrated with main run.py

3. **Simple Test (simple_run.py)**
   - Minimal complexity version
   - Successfully completed in 90 seconds
   - Proves the concept works with simple prompts

### Current Problems

1. **Main System Gets Stuck**
   - Research phase: ~200+ seconds (was using "think harder" mode)
   - Planning phase: ~300+ seconds, often times out
   - Never successfully completed a full milestone

2. **Root Causes Identified**
   - Overly verbose prompts asking for too much analysis
   - Claude uses TodoWrite tool (8 times in research phase alone)
   - Think modes were enabled (now removed)
   - Async execution with completion markers adds complexity
   - Turn limits too low (10) for phases that create files

3. **Testing Issues**
   - test_calculator directory was "polluted" with existing code
   - System correctly found existing implementation but still tried to plan
   - This scenario (partial implementation without progress tracking) won't happen in real use

## Design Decisions Made

### 1. Removed Think Modes
- **Change**: Set all think modes to None in PHASE_CONFIGS
- **Why**: "think harder" was causing massive delays
- **Result**: Reduced time but still getting stuck

### 2. Increased Turn Limits
- **Change**: Research 10→15, Planning 10→10, Implement 60→30
- **Why**: Need enough turns to create output files
- **Concern**: Arbitrary limits aren't intelligent

### 3. Added "Don't Use TodoWrite" Instructions
- **Change**: Added to phase-specific CLAUDE.md files
- **Why**: TodoWrite wastes turns on task tracking
- **Result**: Claude still uses it sometimes

### 4. Created Hybrid Orchestrator
- **Change**: Markdown templates with {{args}} substitution
- **Why**: Cleaner separation of prompts from code
- **Status**: Built but not integrated

## Rejected Alternatives

1. **Skip Logic for Existing Code**
   - **Idea**: If research finds code exists, skip to testing
   - **Rejected**: Would mask problems in 99% use case (fresh builds)
   - **Brian's insight**: System should handle normal case well first

2. **Hardcoded Time Limits Instead of Turns**
   - **Idea**: 5-minute timeout instead of turn count
   - **Rejected**: No more intelligent than turn limits
   - **Better idea**: Dynamic monitoring

## Key Insights from Discussion

1. **99% Use Case**: Building from scratch or resuming with --resume
   - Current test scenario (polluted directory) is artificial
   - Should test with fresh directory

2. **Phase Ordering Problem**
   - Current: Research → Planning → Implement
   - Better: Pre-Planning (architecture) → Research (libraries) → Detailed Planning → Implement
   - Research should discover HOW to build what was planned

3. **Intelligent Monitoring Ideas**
   - Parallel monitor agent checking progress
   - Self-aware checkpoints in prompts
   - Progress metrics instead of hard limits

## Prompt Simplification Needed

### Research Phase
**Current**: Multiple subagent calls, comprehensive analysis
**Should be**: "Understand requirements and identify needed components"

### Planning Phase  
**Current**: Detailed specs, pseudocode, test cases (300+ lines)
**Should be**: "List files to create and key functions with signatures"

### Implementation Phase
**Current**: Verbose instructions about patterns
**Should be**: "Implement according to plan"

## Path Forward

### Immediate Actions
1. Test with fresh directory (test_calculator2) to see real behavior
2. Simplify prompts to match simple_run.py success
3. Consider reordering phases: Plan → Research → Detailed Plan → Implement

### Longer Term
1. Implement intelligent monitoring instead of hard limits
2. Integrate hybrid_orchestrator.py approach
3. Add pre-planning phase for architecture design
4. Remove async complexity if it's not adding value

### Critical Questions to Resolve
1. Should we add pre-planning phase before research?
2. How to implement intelligent monitoring of phases?
3. Is async execution with completion markers worth the complexity?
4. Should phases be able to self-terminate when complete?

## Test Commands

```bash
# Create fresh test
cd /home/brian/autocoder2_cc
mkdir test_calculator2
cd test_calculator2
cp ../test_calculator/CLAUDE.md .
git init

# Run simple version (works)
python ../cc_automator4/simple_run.py

# Run main version (currently gets stuck)
python ../cc_automator4/run.py --project . --milestone 1 --no-parallel --no-file-parallel

# Run with resume
python ../cc_automator4/run.py --project . --resume
```

## Key Files Modified
- phase_orchestrator.py: Removed think modes, adjusted turn limits
- phase_prompt_generator.py: Added "don't use TodoWrite" instructions
- Created: hybrid_orchestrator.py, simple_run.py, test templates

## Brian's Key Points
- Don't optimize for edge cases (polluted directories)
- Focus on 99% use case (fresh builds)
- Complex systems need disciplined framework
- Intelligent monitoring > hardcoded limits
- Phase ordering matters for complex projects