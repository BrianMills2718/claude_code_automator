# CC_AUTOMATOR4 - Complete Specification and Architecture

## Overview

CC_AUTOMATOR4 is a fully autonomous code generation system that uses Claude Code SDK to build complete software projects through isolated, sequential phases. Once configured and started, it runs for hours without human intervention, producing working software with comprehensive tests and documentation.

## Current Architecture (2024)

- **Execution Engine**: Claude Code SDK with async streaming
- **Phase Model**: Sequential 10-phase pipeline per milestone
- **Recovery Strategy**: Intelligent step-back with failure analysis
- **Cost Optimization**: Sonnet for mechanical phases, Opus for creative work
- **Fallback Strategy**: CLI only for TaskGroup async cleanup errors

## Core Philosophy

1. **Complete Autonomy**: After initial setup, zero human intervention required
2. **Evidence-Based Validation**: Every claim must be proven with actual output
3. **Vertical Slice Milestones**: Each milestone produces a working, testable program
4. **Isolated Phases**: Each phase runs in a separate Claude Code instance for clean context
5. **Real Testing**: E2E tests must use actual implementations, no mocking

## Architecture

### System Components

```
cc_automator4/
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
    ("architecture", "Review implementation architecture before mechanical phases"),
    ("lint",         "Fix code style issues (flake8)"),
    ("typecheck",    "Fix type errors (mypy --strict)"),
    ("test",         "Fix unit tests (pytest)"),
    ("integration",  "Fix integration tests"),
    ("e2e",          "Verify main.py runs successfully"),
    ("validate",     "Validate all functionality is real, not mocked"),
    ("commit",       "Create git commit with changes")
]
```

## Phase Dependencies

```
research → planning → implement → architecture → lint → typecheck → test → integration → e2e → validate → commit
```

- **Strict Sequential Execution**: Each phase must complete before next begins
- **Step-back Capability**: Failure can trigger intelligent return to earlier phase
- **Evidence-based Validation**: Each phase requires concrete proof of success
- **No Parallelism**: All phases execute sequentially for reliability

## Key Design Decisions

### 1. SDK-First Execution with CLI Fallback

**Decision**: Use Claude Code SDK with async streaming, CLI only for TaskGroup errors

**Reasoning**: 
- Complete context isolation between phases
- Cost tracking and session management
- MCP integration for enhanced tools
- Real-time streaming progress
- Superior error handling and recovery

**Implementation**:
```python
# SDK-first execution with streaming
options = ClaudeCodeOptions(
    max_turns=phase.max_turns,
    allowed_tools=phase.allowed_tools,
    cwd=str(self.working_dir),
    permission_mode="bypassPermissions",
    model=self._select_model_for_phase(phase.name)
)

# Async streaming execution
async for message in query(prompt=phase.prompt, options=options):
    # Process streaming messages
    self._process_streaming_message(message)
```

**CLI Fallback Strategy**:
- Only triggered by TaskGroup async cleanup errors
- Automatic detection of partial completion
- Immediate fallback without retries for known SDK bugs

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

### 7. Sequential Phase Execution with Cost Optimization

**Decision**: All phases execute sequentially, mechanical phases use Sonnet for cost efficiency

**Reasoning**:
- Sequential execution ensures reliability and clear dependency chains
- Cost optimization through model selection for different phase types
- Simpler debugging and state management
- Eliminates merge conflicts and coordination complexity

**Model Selection Strategy**:
```python
def _select_model_for_phase(phase_name: str) -> Optional[str]:
    # Check environment overrides first
    if os.environ.get('FORCE_SONNET') == 'true':
        return "claude-3-5-sonnet-20241022"
    
    # Mechanical phases use cost-effective Sonnet
    mechanical_phases = ["lint", "typecheck"]
    if phase_name in mechanical_phases:
        return "claude-3-5-sonnet-20241022"
    
    # Creative phases use default model (Opus)
    return None
```

**Sequential Benefits**:
- Each phase builds on previous phase outputs
- Clear error propagation and debugging
- Predictable resource usage
- No complex merge strategies needed

### 8. Intelligent Step-Back Recovery

**Decision**: When phases fail, analyze root cause and step back to appropriate earlier phase

**Reasoning**:
- Early phase errors (research, planning) often cause later phase failures
- Intelligent analysis determines optimal step-back target
- Avoids wasted cycles on doomed implementations
- Provides failure context to prevent repeating mistakes

**Implementation**:
```python
async def _execute_intelligent_step_back(self, current_phase, original_feedback):
    # Analyze failure to determine step-back target
    step_back_to_phase = await self._analyze_failure_for_step_back(
        current_phase, original_feedback
    )
    
    # Create failure history for context
    failure_history = {
        "failed_phase": current_phase.name,
        "original_feedback": original_feedback,
        "analysis_insights": failure_insights,
        "step_back_count": self.step_back_count
    }
    
    # Re-execute with failure insights
    success = await self._re_execute_phase_with_insights(
        step_back_to_phase, failure_history
    )
    
    if success:
        # Re-execute all subsequent phases
        return await self._re_execute_subsequent_phases(
            step_back_to_phase, current_phase.name, failure_history
        )
```

**Step-Back Limits**:
- Normal mode: Maximum 3 step-backs per milestone
- Infinite mode: Unlimited step-backs until success
- Failure logs saved for debugging and analysis

### 9. Architectural Quality Gate

**Decision**: Insert architecture review phase between implement and mechanical phases

**Reasoning**:
- Catches structural issues before they waste cycles in lint/typecheck/test phases
- Prevents "polishing a turd" scenario where poor architecture gets mechanically fixed
- Enforces quality standards early when fixes are cheaper
- Aligns with anti-cheating philosophy of preventing false progress

**Architecture Standards Enforced**:
- **Code Structure**: Functions ≤50 lines, classes ≤20 methods, files ≤1000 lines
- **Import Structure**: No circular imports, proper `__init__.py` files, clean dependencies
- **Design Patterns**: Separation of concerns, no hardcoded values, proper error handling
- **Complexity Limits**: Cyclomatic complexity ≤10, nesting depth ≤4 levels
- **Anti-Pattern Prevention**: No god objects, duplicate code, or mixed concerns

**Implementation**:
```python
class ArchitectureValidator:
    def validate_all(self) -> Tuple[bool, List[str]]:
        self._check_code_structure()
        self._check_import_structure() 
        self._check_design_patterns()
        self._check_complexity_metrics()
        self._check_antipatterns()
        return len(self.issues) == 0, self.issues
```

**Benefits**:
- **Prevents Wasted Cycles**: Structural issues caught before mechanical phases
- **Cost Optimization**: Fewer retry cycles in expensive phases
- **Quality Assurance**: Enforces maintainable code standards
- **Early Detection**: Problems found when fixes are simpler

### 10. Iterative Fix Phases

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

### Multi-Level Retry Strategy

**Decision**: Hierarchical retry system with escalating intervention

**Implementation**:
1. **Level 1**: Direct retry with enhanced feedback
2. **Level 2**: Enhanced retry with detailed error analysis  
3. **Level 3**: Intelligent step-back to root cause phase
4. **Level 4**: Skip milestone if all recovery attempts fail

**Step-Back Triggers**:
- Test failures that indicate architectural issues
- Type errors suggesting design flaws
- Integration failures pointing to planning problems
- E2E failures indicating research gaps

**Infinite Mode**: Continue step-backs indefinitely until success (for debugging)

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
python cc_automator4/setup.py

# Interactive Q&A fills template
# Validates environment
# Creates initial structure
```

### Run
```bash
python cc_automator4/run.py

# Runs autonomously for hours
# Check progress.json for status
# Review evidence/ for validation
```

### Resume After Failure
```bash
python cc_automator4/run.py --resume

# Picks up from last checkpoint
# Skips completed phases
```

## Success Metrics

A milestone is complete when:
1. All 10 phases completed successfully in sequence
2. main.py runs without errors and produces expected output
3. **100% test passage**: Zero failures, zero errors (strict validation)
4. Evidence logs prove real execution with concrete proof
5. Validation phase confirms no mocked implementations
6. Git commit created with proper message format

**Anti-Cheating Validation**:
- Test count parsing with regex to prevent partial success
- Implementation validator checks for mocks/stubs in production code
- E2E evidence logs required for completion
- Independent validation commands verify all claims

## Future Enhancements (Not in V1)

1. Web dashboard for progress monitoring
2. Slack/email notifications
3. Cost optimization with model selection
4. Parallel milestone execution
5. Learning from past projects

## Summary

CC_AUTOMATOR4 achieves reliable, autonomous code generation through:
- **Sequential phase execution** with clear dependency chains
- **SDK-first architecture** with intelligent CLI fallback
- **Intelligent step-back recovery** from root cause analysis
- **Evidence-based validation** with strict anti-cheating measures
- **Cost optimization** through strategic model selection
- **Vertical milestones** maintaining testability at each stage
- **Think modes** for complex problem solving
- **Self-healing patterns** for robust code generation
- **Smart orchestration** handling failures gracefully
- **100% success validation** requiring concrete proof

The system transforms high-level requirements into working, tested, documented code without human intervention after initial setup, with sophisticated recovery mechanisms that ensure reliability and prevent false positives.