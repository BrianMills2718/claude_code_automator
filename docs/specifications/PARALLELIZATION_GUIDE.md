# CC_AUTOMATOR3 Parallelization Strategy Guide

## Overview

CC_AUTOMATOR3 supports three parallelization strategies to optimize execution time. This guide helps you choose the right strategy for your use case.

## Available Strategies

### 1. File-Level Parallelization (Default)

**What it does**: Splits mechanical fixes (lint, typecheck) across multiple files simultaneously.

**When to use**:
- Large codebases with many lint/type errors
- Mechanical fixes that don't require cross-file context
- When you want the fastest fix time for style issues

**How to enable**: Enabled by default, or use `--file-parallel`

**Example scenario**:
```
Project has 50 Python files with lint errors
→ Splits into 4 workers, each fixing ~12 files
→ 4x speedup for lint phase
```

**Limitations**:
- Only works for lint and typecheck phases
- Requires files to be independent

### 2. Git Worktrees (Advanced)

**What it does**: Creates separate working directories for truly parallel development.

**When to use**:
- Building independent features simultaneously
- Large refactoring of separate modules
- When changes don't overlap between tasks

**How to use**:
```bash
# Create worktrees for parallel features
git worktree add ../feature-auth -b auth-feature
git worktree add ../feature-ui -b ui-feature

# Run Claude in each worktree
cd ../feature-auth && python /path/to/cc_automator4/cli.py
cd ../feature-ui && python /path/to/cc_automator4/cli.py  # In another terminal
```

**Example scenario**:
```
Building an authentication system AND a UI dashboard
→ Two Claude instances work completely independently
→ No merge conflicts during development
→ Merge both branches when complete
```

**Requirements**:
- Git expertise
- Sufficient system resources for multiple Claude instances
- Clear feature boundaries

### 3. Phase-Level Parallelization (Future)

**What it does**: Runs compatible phases simultaneously (e.g., lint + typecheck).

**When to use**:
- Small to medium projects
- When phases don't modify the same files
- Limited system resources

**Status**: Available with `--parallel` flag (experimental)

## Strategy Selection Guide

### For Most Users: File-Level (Default)

This provides the best balance of:
- ✅ Simplicity
- ✅ Performance gains
- ✅ No Git complexity
- ✅ Works out of the box

### For Power Users: Git Worktrees

When you need:
- ✅ True isolation between features
- ✅ Maximum parallelism
- ✅ Working on multiple milestones
- ⚠️ Requires Git expertise

### Decision Matrix

| Scenario | Recommended Strategy |
|----------|---------------------|
| Fix all lint errors | File-level (default) |
| Fix all type errors | File-level (default) |
| Build auth + UI simultaneously | Git worktrees |
| Small project (<20 files) | Sequential (no parallel) |
| Running tests | Sequential |
| Complex implementation | Sequential |

## Future: LLM-Driven Strategy Selection

In future versions, CC_AUTOMATOR3 will use AI to automatically choose the optimal strategy:

```python
# Future capability
strategy = orchestrator_llm.analyze_and_choose_strategy(
    milestone_description,
    codebase_size,
    file_dependencies,
    team_git_expertise
)
```

## Performance Expectations

### File-Level Parallelization
- **Speedup**: 2-4x for mechanical fixes
- **Overhead**: Minimal
- **Scaling**: Linear with worker count

### Git Worktrees
- **Speedup**: Nx for N independent features
- **Overhead**: Repository size × N
- **Scaling**: Limited by system resources

## Common Issues and Solutions

### File-Level Issues

**Problem**: "Some files failed to fix"
**Solution**: Check individual file errors in logs, may need manual intervention

**Problem**: High API costs
**Solution**: Reduce worker count or batch smaller groups

### Git Worktree Issues

**Problem**: "fatal: already has a worktree"
**Solution**: Remove old worktree: `git worktree remove ../old-worktree`

**Problem**: IDE shows wrong files
**Solution**: Open each worktree in separate IDE window

## Best Practices

1. **Start Simple**: Use default file-level parallelization
2. **Monitor Costs**: Parallel execution increases API usage
3. **Clean Up**: Remove worktrees when done
4. **Feature Boundaries**: Ensure truly independent work for worktrees
5. **Resource Management**: Don't overload your system

## Examples

### Example 1: Fixing a Large Legacy Codebase
```bash
# Default file-level works great
python cli.py --project /path/to/legacy-app

# CC_AUTOMATOR3 automatically parallelizes lint and typecheck phases
```

### Example 2: Building Multiple Features
```bash
# Terminal 1: Authentication feature
git worktree add ../auth-feature -b feature/auth
cd ../auth-feature
python /path/to/cc_automator4/cli.py --milestone 1

# Terminal 2: Payment feature  
git worktree add ../payment-feature -b feature/payment
cd ../payment-feature
python /path/to/cc_automator4/cli.py --milestone 2
```

### Example 3: Quick Style Fixes
```bash
# Just fix lint/type errors quickly
python cli.py --no-parallel  # Disable if project is small
python cli.py               # Use default for larger projects
```

## Conclusion

For most users, the default file-level parallelization provides the best results. Git worktrees are powerful for advanced users with clear feature boundaries. Future versions will use AI to make these decisions automatically.