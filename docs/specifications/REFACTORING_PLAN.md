# CC_AUTOMATOR3 MVP Refactoring Plan

## Current State (Commit: d0deaa7)

### What Works Well
- Core orchestration logic is solid
- Isolated phase execution prevents context pollution  
- Completion markers cleverly bypass timeout limits
- Git worktrees provide true parallel isolation
- System is battle-tested at Anthropic

### Issues to Address

#### 1. Parallelization Complexity
- **Problem**: Three strategies (file_parallel_executor.py, parallel_executor.py, git worktrees) confuse users
- **Solution**: Default to file-level for MVP, document others for power users
- **Future**: LLM-driven strategy selection

#### 2. Performance Issues
- **Problem**: Fixed 15-second polling intervals waste time
- **Solution**: Adaptive polling (5s → 30s exponential backoff)
- **Future**: Event-driven architecture if needed

#### 3. Architecture Debt  
- **Problem**: run.py is 694 lines doing everything
- **Solution**: Split into cli.py, orchestrator.py, progress_display.py
- **Future**: Plugin architecture for custom phases

#### 4. Production Gaps
- **Problem**: Poor error messages, broken cost tracking
- **Solution**: Clear error messages, fix session ID and cost display
- **Future**: Structured logging, observability

## MVP Implementation Plan

### Phase 1: Light Architecture Refactor
```
run.py (694 lines) → 
  ├── cli.py (~100 lines) - CLI entry point and arg parsing
  ├── orchestrator.py (~300 lines) - Core orchestration logic  
  └── progress_display.py (~150 lines) - UI and progress tracking
```

### Phase 2: Performance Quick Wins
```python
# Change from:
time.sleep(15)  # Fixed interval

# To:
poll_interval = 5
while not complete:
    time.sleep(poll_interval)
    poll_interval = min(poll_interval * 1.5, 30)
```

### Phase 3: Fix Obvious Bugs
- Session ID capture in async mode
- Cost tracking display
- Error message clarity

### Phase 4: Documentation
- Strategy selection guide
- LLM prompt templates for future
- CONTRIBUTING.md for developers

## Rollback Instructions

To revert to current state:
```bash
git checkout d0deaa7
```

## Success Criteria

MVP is complete when:
1. run.py is split into logical components
2. Adaptive polling is implemented
3. Cost and session tracking work
4. Error messages are helpful
5. Documentation explains all strategies

## Future Vision

After MVP, the system will support:
```python
# LLM-driven orchestration
strategy = orchestrator_llm.choose_strategy(context)
execution_plan = orchestrator_llm.create_plan(milestone)
```

This preserves all current functionality while making the system more maintainable and setting up for intelligent orchestration.

## Next Steps

1. Create feature branch: `git checkout -b mvp-refactor`
2. Implement light refactor of run.py
3. Add adaptive polling
4. Fix tracking bugs
5. Update documentation
6. Test with example project
7. Merge back to master

The goal is a simpler, clearer system that works today and can become intelligent tomorrow.