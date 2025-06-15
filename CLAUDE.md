# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

# CC_AUTOMATOR3 Implementation Guide

## Commands

### Building and Running
```bash
# Run the automator on a project
python run.py --project /path/to/project

# Resume from last checkpoint
python run.py --project /path/to/project --resume

# Run specific milestone only
python run.py --project /path/to/project --milestone 2

# Run with Docker isolation (Phase 4)
python run.py --project /path/to/project --docker

# Disable parallel execution
python run.py --project /path/to/project --no-parallel

# Run setup for a new project
python setup.py --project /path/to/project

# Create example project
python setup.py --project /path/to/project --example calculator
```

### Testing
```bash
# Run all tests
pytest tests/ -xvs

# Test specific component
python test_orchestrator.py --phase research

# Test with real project
python setup.py --project test_calculator --example calculator
python run.py --project test_calculator
```

### Linting and Type Checking
```bash
# Run linting (F-errors only for production)
flake8 --select=F --exclude=venv,__pycache__,.git

# Run type checking
mypy --strict .
```

## High-Level Architecture

CC_AUTOMATOR3 is an autonomous code generation system that orchestrates Claude Code CLI through isolated phase executions to build complete software projects without human intervention.

### Core Design Principles

1. **Isolated Phase Execution**: Each of 9 phases runs in a separate Claude Code instance with fresh context
2. **Completion Markers**: Bypasses subprocess timeout limits using file-based completion tracking
3. **Evidence-Based Validation**: Every phase must provide verifiable proof of success
4. **Vertical Slice Milestones**: Each milestone produces a runnable main.py
5. **Smart Context Management**: Phases receive only relevant context from previous phases

### Key Components

#### Phase Orchestrator (`phase_orchestrator.py`)
- Manages isolated Claude Code CLI invocations
- Implements async execution with completion markers for long-running phases
- Handles streaming JSON output for real-time monitoring
- Tracks session IDs for precise debugging

#### Run System (`run.py`)
- Main entry point that coordinates the entire process
- Manages milestone execution sequentially
- Supports resume from checkpoint
- Integrates Phase 4 features (parallel, Docker, visual)

#### Phase Prompt Generator (`phase_prompt_generator.py`)
- Creates phase-specific prompts with evidence requirements
- Manages context flow between phases
- Enforces self-healing patterns
- Creates phase-specific CLAUDE.md files

#### Milestone Decomposer (`milestone_decomposer.py`)
- Parses CLAUDE.md to extract milestones
- Validates milestones are vertical slices
- Generates phase sequence for each milestone

### Phase Execution Flow

```
For each milestone:
  1. Research    → Analyze requirements (Write tool needed)
  2. Planning    → Create implementation plan
  3. Implement   → Build the solution
  4. Lint        → Fix F-errors only (fast, mechanical)
  5. Typecheck   → Add type hints (fast, mechanical)  
  6. Test        → Create/fix unit tests
  7. Integration → Test component interactions
  8. E2E         → Verify main.py works
  9. Commit      → Create git commit
```

### Completion Marker System

To handle phases that may run longer than subprocess timeouts:

```python
# Phase creates marker when done
completion_marker = f".cc_automator/phase_{phase_name}_complete"
# Write "PHASE_COMPLETE" to marker file

# Orchestrator polls for marker instead of waiting for process exit
```

### Think Modes Strategy

Research and planning phases benefit from deeper analysis:
- Research: Basic analysis mode
- Planning: Thoughtful planning mode
- Other phases: Standard execution

### Self-Healing Patterns

All implementation includes these patterns automatically:
- Relative imports (not absolute)
- Behavior testing (not implementation)
- Graceful dependency handling
- Pathlib for file operations
- Descriptive error messages

## Phase 4 Advanced Features

### Parallel Execution
- Lint and typecheck can run in parallel
- Test and integration can run in parallel
- Uses git worktrees for true isolation
- File-level parallelization for mechanical fixes

### Docker Integration
- Mechanical phases run in containers
- Consistent environment across systems
- Better resource isolation

### Visual Progress Display
- Real-time phase status
- Cost and duration tracking
- Session ID display
- Error reporting

## Important Notes

1. **For Claude Max users**: Costs shown are informational only (no actual charges)
2. **Timeout handling**: 10-minute default, phases create completion markers for async
3. **E2E tests**: Run with `nohup` to avoid timeout, NO mocking allowed
4. **Evidence validation**: All phases must provide proof, not just claims
5. **Context limits**: Each phase gets targeted context, not full history

## Development Guidelines

1. Each component should be testable in isolation
2. Use type hints throughout (mypy --strict must pass)
3. Handle subprocess timeouts gracefully
4. Always validate evidence from Claude
5. Log all phase outputs for debugging
6. Prefer file-based communication over process exit codes

## Debugging

Check these locations for troubleshooting:
- `.cc_automator/logs/` - Phase execution logs
- `.cc_automator/checkpoints/` - Phase completion status
- `.cc_automator/milestones/` - Phase outputs
- `.cc_automator/progress.json` - Overall execution state