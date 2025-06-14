# CC_AUTOMATOR3 - Complete Specification and Architecture

## Overview

CC_AUTOMATOR3 is a fully autonomous code generation system that uses Claude Code to build complete software projects through isolated, sequential phases. Once configured and started, it runs for hours without human intervention, producing working software with comprehensive tests and documentation.

## Core Philosophy

1. **Complete Autonomy**: After initial setup, zero human intervention required
2. **Evidence-Based Validation**: Every claim must be proven with actual output
3. **Vertical Slice Milestones**: Each milestone produces a working, testable program
4. **Isolated Phases**: Each phase runs in a separate Claude Code instance for clean context
5. **Real Testing**: E2E tests must use actual implementations, no mocking

## Architecture

### System Components

```
cc_automator3/
├── CC_AUTOMATOR_SPECIFICATION.md    # This file
├── CLAUDE_TEMPLATE.md               # Template filled for each project
├── CLAUDE_TEMPLATE_QA.md            # Interactive template filling guide
├── phase_orchestrator.py            # Main orchestration engine
├── preflight_validator.py           # Pre-execution validation
├── dependency_analyzer.py           # Build dependency graphs
├── progress_tracker.py              # Track and visualize progress
├── docker/
│   ├── Dockerfile                   # Isolated execution environment
│   └── docker-compose.yml           # Service configuration
└── templates/
    └── phase_prompts/               # Per-phase prompt templates
```

### Execution Flow

1. **Initial Setup** (One-time human interaction)
   - Run template Q&A to fill in project details
   - Validate all dependencies available
   - Create project structure

2. **Autonomous Execution** (No human interaction)
   - For each milestone:
     - For each phase:
       - Execute in isolated Claude Code instance
       - Validate success with evidence
       - Save checkpoint
       - Continue to next phase

### Phase Structure

Each milestone goes through these phases sequentially:

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

## Key Design Decisions

### 1. CLI-Based Isolation with Streaming

**Decision**: Use `claude -p "prompt" --output-format stream-json` for each phase

**Reasoning**: 
- Complete context isolation between phases
- No context accumulation or confusion
- Clear cost tracking per phase
- Easy to resume from failures
- Real-time progress monitoring

**Implementation**:
```python
# For monitoring progress in real-time
process = subprocess.Popen([
    "claude", "-p", phase_prompt,
    "--output-format", "stream-json",
    "--max-turns", "10",
    "--allowedTools", "Read,Write,Edit,Bash"
], stdout=subprocess.PIPE, text=True)

# Process streaming output
for line in process.stdout:
    if line.strip():
        event = json.loads(line)
        # Handle different event types
```

### 2. Smart Session Management

**Decision**: Track and resume specific sessions using session IDs

**Reasoning**:
- Precise session tracking across phases
- Better debugging and recovery
- Essential for parallel execution
- More reliable than "most recent" session

**Implementation**:
```python
class SessionManager:
    def __init__(self):
        self.sessions = {}  # phase_name -> session_id
    
    def execute_phase(self, phase):
        # Run Claude and capture session ID
        result = json.loads(output)
        self.sessions[phase.name] = result.get("session_id")
        
    def resume_phase(self, phase_name):
        session_id = self.sessions.get(phase_name)
        if session_id:
            cmd = ["claude", "--resume", session_id, "-p", "Continue"]
```

### 3. Docker Environment

**Decision**: Run all code execution inside Docker containers

**Reasoning**:
- Consistent environment across different host systems
- Isolation from host system
- Easy dependency management
- Reproducible builds

**Implementation**:
```yaml
services:
  cc_automator:
    build: .
    volumes:
      - .:/app  # Mount for live editing
    environment:
      - PYTHONPATH=/app
```

### 4. Vertical Slice Milestones

**Decision**: Each milestone must produce a runnable main.py

**Reasoning**:
- Enables E2E testing at each milestone
- Provides tangible progress
- Catches integration issues early
- Mirrors real-world iterative development

**Validation**:
```python
def validate_milestone_is_vertical_slice(milestone):
    """Ensure milestone produces testable functionality"""
    return all([
        "produces runnable main.py" in milestone.description,
        "user-visible functionality" in milestone.description,
        "can be tested end-to-end" in milestone.description
    ])
```

### 5. Testing Strategy

**Decision**: Three levels of testing with different mocking policies

**Reasoning**:
- Unit tests (mocking OK): Fast, focused on logic
- Integration tests (minimal mocking): Component interaction
- E2E tests (NO mocking): Real user experience

**E2E Enforcement**:
```python
def run_e2e_test():
    """Run main.py with real dependencies"""
    # Start in background to avoid timeout
    subprocess.Popen([
        "nohup", "python", "main.py", 
        ">", ".cc_automator/e2e_output.log", "2>&1", "&"
    ])
    # Monitor output for completion
```

### 6. Evidence-Based Validation

**Decision**: "Show, don't tell" - require proof for all claims

**Reasoning**:
- Prevents false positives
- Catches subtle failures
- Builds trust in the system
- Enables debugging

**Example Prompt**:
```markdown
Run the tests and provide evidence:
1. Quote the exact pytest output showing all tests passed
2. Include the summary line (e.g., "5 passed in 1.23s")
3. If any test fails, quote the full error
4. No paraphrasing - exact output only
```

### 7. Sequential Implementation, Parallel Mechanical Fixes

**Decision**: Implementation phase is sequential, mechanical fixes use git worktrees for parallelism

**Reasoning**:
- Creative work (implementation) needs coherent design
- Mechanical fixes can be safely parallelized
- Git worktrees provide true isolation
- Easier merging of small, focused changes

**Git Worktree Strategy**:
```python
# Create isolated worktrees for parallel fixes
def create_worktrees_for_parallel_fixes(fix_type, num_workers):
    worktrees = []
    for i in range(num_workers):
        worktree_path = f"../worktree-{fix_type}-{i}"
        subprocess.run(["git", "worktree", "add", worktree_path, "main"])
        worktrees.append(worktree_path)
    return worktrees

# After fixes complete, merge back
def merge_worktree_changes(worktree_path, branch_name):
    subprocess.run(["git", "checkout", "main"])
    subprocess.run(["git", "merge", f"worktree-{branch_name}"])
    subprocess.run(["git", "worktree", "remove", worktree_path])
```

**Parallelizable with Worktrees**:
- Lint fixes (by file)
- Type fixes (by file) 
- Test fixes (by test file)
- Research tasks (read-only, no worktrees needed)

**Merge Strategy**: After each phase completes, before next phase

### 8. Iterative Fix Phases

**Decision**: Keep running fix phases until clean (max 5 iterations)

**Reasoning**:
- First pass rarely fixes all issues
- Each iteration makes progress
- Timeout prevents infinite loops
- Matches human debugging patterns

**Implementation**:
```python
for iteration in range(MAX_ITERATIONS):
    result = run_tool()  # flake8, mypy, pytest
    if result.returncode == 0:
        break
    fix_with_claude(result.stderr)
```

### 9. Pre-flight Validation

**Decision**: Validate environment before starting

**Reasoning**:
- Catches missing dependencies early
- Saves API costs on doomed runs
- Better user experience
- Clear error messages

**Checks**:
- Git repository clean
- Required tools installed (flake8, mypy, pytest)
- Docker available
- Sufficient disk space
- Claude Code authenticated

### 10. One-Time Human Setup

**Decision**: All human interaction happens at the beginning

**Reasoning**:
- Core value prop: start and walk away
- Gather all requirements upfront
- No blocking on human input mid-execution
- True automation

**Setup Captures**:
- Project requirements
- API keys needed
- External service configs
- Success criteria
- Special considerations

### 11. Smart Context Management

**Decision**: Each phase gets only relevant files as context

**Reasoning**:
- Reduces token usage
- Improves focus
- Faster execution
- Prevents confusion

**Example**:
```python
context_map = {
    "research": ["README.md", "requirements.txt"],
    "implement": ["research_output.md", "plan.md"],
    "lint": ["*.py"],  # Only Python files
    "test": ["src/", "tests/"],
    "e2e": ["main.py", "README.md"]
}
```

## Prompt Engineering Strategies

### 1. Explicit Success Criteria

Every prompt includes:
- What to do
- How to verify it worked
- What output to provide as evidence
- What NOT to do

### 2. Forbidden Practices

Explicitly state what to avoid:
- "NO mocking in E2E tests"
- "NO stub implementations"
- "NO assumed success - verify everything"
- "NO style-only linting issues"

### 3. Evidence Requirements

- Quote exact tool output
- Show file contents created
- Include timestamps
- Capture return codes

### 4. Context From Previous Phases

Each phase can access:
- Previous phase outputs
- Accumulated knowledge
- But NOT previous phase's full context

### 5. Think Modes for Complex Tasks

**Strategy**: Use Claude's think triggers for phases requiring deep analysis

**Implementation**:
```python
PHASE_THINK_MODES = {
    "research": "think harder",    # Deep analysis needed
    "planning": "think hard",      # Careful planning required
    "implement": "think",          # Standard thinking
    "lint": None,                  # No thinking needed
    "typecheck": None,             # Mechanical task
    "test": "think",               # May need problem solving
    "integration": "think",        # Complex interactions
    "e2e": "think hard",          # Full system understanding
    "commit": None                 # Simple task
}

# In prompt generation
if think_mode := PHASE_THINK_MODES.get(phase_name):
    prompt = f"{think_mode} about this problem: {prompt}"
```

### 6. Self-Healing Patterns

**Strategy**: Build resilience into generated code from the start

**Prompts Include**:
```python
self_healing_patterns = """
When implementing code, follow these patterns for robustness:

1. Use relative imports instead of absolute:
   # Good: from ..utils import helper
   # Bad: from src.utils import helper

2. Test behavior, not implementation:
   # Good: assert calculator.add(2, 3) == 5
   # Bad: assert calculator._internal_state == 5

3. Handle missing dependencies gracefully:
   try:
       import optional_library
   except ImportError:
       optional_library = None

4. Use pathlib for file operations:
   # Good: Path(__file__).parent / "data"
   # Bad: "/absolute/path/to/data"

5. Write descriptive error messages:
   # Good: raise ValueError(f"Expected positive number, got {value}")
   # Bad: raise ValueError("Invalid input")
"""
```

## Progress Tracking

### Visual Display
```
Project: AI Assistant
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Milestone 1: Basic CLI Interface [████████░░] 80%
├─ ✓ Research       [00:05:23] $0.24
├─ ✓ Planning       [00:03:12] $0.18  
├─ ✓ Implementation [00:15:45] $0.89
├─ ✓ Lint          [00:02:33] $0.15
├─ ✓ Type Check    [00:04:11] $0.22
├─ ⚡ Unit Tests    [00:03:44] $0.31 (fixing...)
├─ ○ Integration
├─ ○ E2E
└─ ○ Commit

Total: 00:34:48 | $1.99 | Errors Fixed: 47
```

### Checkpoint System

After each phase:
- Save current state
- Record what changed
- Enable resume from failure
- Track success metrics

## Error Handling

### Timeout Strategy
- 10-minute timeout per phase
- Timeout = failure (not assumed success)
- E2E tests run async to avoid timeout

### Retry Logic
- Max 2 retries per phase
- Different approach on retry
- Skip to next milestone if phase repeatedly fails

### Rollback Capability
- Git stash before risky changes
- Restore on failure
- Commit only on full milestone success

## Directory Structure Per Project

```
project/
├── CLAUDE.md                    # Filled template with project spec
├── main.py                      # Required entry point
├── requirements.txt             # Python dependencies
├── .env.example                 # Required environment variables
├── src/                         # Source code
├── tests/
│   ├── unit/                   # Unit tests (mocking OK)
│   ├── integration/            # Integration tests
│   └── e2e/                    # End-to-end tests (no mocking)
├── .cc_automator/
│   ├── checkpoints/            # Phase completion records
│   ├── evidence/               # Test output logs
│   ├── progress.json           # Current status
│   └── milestones/
│       ├── milestone_1/
│       │   ├── research.md     # Research findings
│       │   ├── plan.md         # Implementation plan
│       │   └── evidence.log    # Proof of success
│       └── milestone_2/
```

## Usage

### Initial Setup
```bash
cd my_project
python cc_automator3/setup.py

# Interactive Q&A fills template
# Validates environment
# Creates initial structure
```

### Run
```bash
python cc_automator3/run.py

# Runs autonomously for hours
# Check progress.json for status
# Review evidence/ for validation
```

### Resume After Failure
```bash
python cc_automator3/run.py --resume

# Picks up from last checkpoint
# Skips completed phases
```

## Success Metrics

A milestone is complete when:
1. All phases completed successfully
2. main.py runs without errors
3. All tests pass (unit, integration, E2E)
4. Evidence logs prove real execution
5. Git commit created

## Future Enhancements (Not in V1)

1. Web dashboard for progress monitoring
2. Slack/email notifications
3. Cost optimization with model selection
4. Parallel milestone execution
5. Learning from past projects

## Summary

CC_AUTOMATOR3 achieves reliable, autonomous code generation through:
- **Isolated phases** preventing context pollution
- **Real-time monitoring** via streaming JSON output
- **Smart session tracking** with precise ID management
- **True parallelism** using git worktrees for mechanical fixes
- **Evidence-based validation** ensuring real functionality  
- **Vertical milestones** maintaining testability
- **Think modes** for complex problem solving
- **Self-healing patterns** for robust code generation
- **Smart orchestration** handling failures gracefully
- **Clear specifications** leaving no ambiguity

The system transforms high-level requirements into working, tested, documented code without human intervention after initial setup.