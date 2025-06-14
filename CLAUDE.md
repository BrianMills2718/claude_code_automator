# CC_AUTOMATOR3 Implementation Guide

## Current Status
Building CC_AUTOMATOR3 - an autonomous code generation system using isolated Claude Code CLI invocations.

## Implementation Plan

### Phase 1: Core Foundation (CURRENT)
- [x] Basic phase orchestrator with streaming JSON output
- [x] Session management with ID tracking
- [x] Preflight validation system
- [x] Progress tracking and checkpointing

### Phase 2: Templates & Setup
- [x] Create CLAUDE_TEMPLATE.md with project placeholders
- [x] Create CLAUDE_TEMPLATE_QA.md for interactive setup
- [x] Build setup.py for one-time configuration
- [x] Milestone validation (vertical slices)

### Phase 3: Phase Implementations
- [ ] Create phase prompt templates for all 9 phases
- [ ] Integrate think modes per phase
- [ ] Add self-healing patterns to prompts
- [ ] Implement evidence validation

### Phase 4: Advanced Features
- [ ] Git worktree parallelization for mechanical fixes
- [ ] Docker environment integration
- [ ] Full checkpoint/resume system
- [ ] Rich visual progress display

## Key Technical Decisions

### CLI Invocation Pattern
```python
# Streaming JSON for real-time monitoring
process = subprocess.Popen([
    "claude", "-p", phase_prompt,
    "--output-format", "stream-json",
    "--max-turns", "10",
    "--allowedTools", "Read,Write,Edit,MultiEdit,Bash"
], stdout=subprocess.PIPE, text=True, timeout=600)
```

### Phase Sequence
```python
PHASES = [
    ("research",     "Analyze requirements and explore solutions"),
    ("planning",     "Create detailed implementation plan"),
    ("implement",    "Build the solution"),
    ("lint",         "Fix code style issues (flake8)"),
    ("typecheck",    "Fix type errors (mypy --strict)"),
    ("test",         "Fix unit tests (pytest)"),
    ("integration",  "Fix integration tests"),
    ("e2e",          "Verify main.py runs successfully"),
    ("commit",       "Create git commit with changes")
]
```

### Think Modes by Phase
```python
PHASE_THINK_MODES = {
    "research": "think harder",
    "planning": "think hard",
    "implement": "think",
    "lint": None,
    "typecheck": None,
    "test": "think",
    "integration": "think",
    "e2e": "think hard",
    "commit": None
}
```

### Self-Healing Patterns
Always include in implementation prompts:
1. Use relative imports (not absolute)
2. Test behavior (not implementation)
3. Handle missing dependencies gracefully
4. Use pathlib for file operations
5. Write descriptive error messages

## Project Structure
```
cc_automator3/
├── CLAUDE.md                    # This file
├── CC_AUTOMATOR_SPECIFICATION.md # Full specification
├── phase_orchestrator.py        # Main orchestration engine
├── session_manager.py           # Track Claude sessions
├── preflight_validator.py       # Pre-execution checks
├── progress_tracker.py          # Progress and checkpointing
├── setup.py                     # Interactive setup
├── templates/
│   ├── CLAUDE_TEMPLATE.md      # Project template
│   ├── CLAUDE_TEMPLATE_QA.md   # Setup guide
│   └── phase_prompts/          # Per-phase prompts
└── tests/
    └── test_orchestrator.py    # Test the system
```

## Testing Commands
```bash
# Test basic phase execution
python test_orchestrator.py --phase research

# Test full milestone
python test_orchestrator.py --milestone 1

# Test with real project
python setup.py --project test_calculator
python run.py
```

## Key Requirements
- Python 3.8+
- Claude Code CLI authenticated (Claude Max subscription)
- Git repository initialized
- Docker (for phase 4)
- flake8, mypy, pytest installed

## Development Guidelines
1. Each component should be testable in isolation
2. Use type hints throughout
3. Handle subprocess timeouts gracefully
4. Always validate evidence from Claude
5. Log all phase outputs for debugging

## Current Focus
Start with phase_orchestrator.py implementing:
1. Streaming JSON processing
2. Session ID capture and storage
3. Timeout handling
4. Basic error recovery

## Notes
- For Claude Max users, costs shown are informational only
- 10-minute timeout per phase (configurable)
- E2E tests run async to avoid timeout limits
- Git worktrees will be used for parallel fixes (Phase 4)