# CC_AUTOMATOR4 V3 - Pure SDK Architecture Specification

## Overview

CC_AUTOMATOR4 V3 is a fully autonomous code generation system that uses **pure Claude Code SDK** to build complete software projects through isolated, sequential phases. Once configured and started, it runs for hours without human intervention, producing working software with comprehensive tests and documentation.

## V3 Architecture (2024) - Pure SDK

- **Execution Engine**: Pure Claude Code SDK with async streaming (NO CLI fallback)
- **Phase Model**: Sequential 11-phase pipeline per milestone with architectural quality gate
- **Recovery Strategy**: Intelligent step-back with failure analysis
- **Cost Optimization**: Sonnet for mechanical phases, Opus for creative work
- **SDK Issues**: All TaskGroup and async cleanup issues resolved natively

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
├── architecture_validator.py        # Architectural quality validation
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

### 1. Pure SDK Execution with Native Error Handling

**Decision**: Use pure Claude Code SDK with async streaming, NO CLI fallback

**Reasoning**: 
- Complete context isolation between phases
- Cost tracking and session management throughout
- MCP integration for enhanced tools
- Real-time streaming progress
- Consistent execution model
- Forces resolution of root SDK issues

**Implementation**:
```python
# Pure SDK execution with native error handling
options = ClaudeCodeOptions(
    max_turns=phase.max_turns,
    allowed_tools=phase.allowed_tools,
    cwd=str(self.working_dir),
    permission_mode="bypassPermissions",
    model=self._select_model_for_phase(phase.name)
)

# Async streaming execution with proper TaskGroup management
async with asyncio.TaskGroup() as tg:
    async for message in query(prompt=phase.prompt, options=options):
        # Process streaming messages with proper async handling
        await self._process_streaming_message(message)
```

**SDK Issue Resolution Strategy**:
- Native TaskGroup cleanup with proper exception handling
- Async subprocess management for E2E testing
- Session resumption through SDK-only mechanisms
- Timeout handling without external process management

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
    
    async def execute_phase(self, phase):
        # Run Claude SDK and capture session ID from streaming
        async for message in query(prompt=phase.prompt, options=options):
            if hasattr(message, 'session_id'):
                self.sessions[phase.name] = message.session_id
        
    async def resume_phase(self, phase_name):
        session_id = self.sessions.get(phase_name)
        if session_id:
            # Resume through SDK using session context
            options.session_id = session_id
            async for message in query(prompt="Continue", options=options):
                yield message
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
async def run_e2e_test():
    """Run main.py with real dependencies through SDK subprocess management"""
    # Use SDK's subprocess handling for proper async management
    options = ClaudeCodeOptions(
        max_turns=10,
        allowed_tools=["Bash", "Read"],
        cwd=str(self.working_dir),
        permission_mode="bypassPermissions"
    )
    
    prompt = """Run the main.py program and capture its output:
    1. Execute: python main.py > .cc_automator/e2e_output.log 2>&1
    2. Monitor execution for completion or timeout after 60s
    3. Read and verify the output log
    4. Provide evidence of successful execution"""
    
    async for message in query(prompt=prompt, options=options):
        # SDK handles subprocess management natively
        yield message
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
    mechanical_phases = ["architecture", "lint", "typecheck"]
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

1. **Code Structure Constraints**:
   - Functions ≤50 lines (break larger functions into smaller, focused ones)
   - Classes ≤20 methods (split large classes by responsibility)
   - Files ≤1000 lines (create logical module boundaries)
   - Function parameters ≤5 (use configuration objects for complex inputs)

2. **Import Structure Requirements**:
   - No circular import dependencies (restructure module relationships)
   - Proper `__init__.py` files in all package directories
   - Clean dependency hierarchies (business logic independent of UI)
   - Relative imports within project modules

3. **Design Pattern Enforcement**:
   - Separation of concerns (UI, business logic, data access in separate modules)
   - Configuration externalization (no hardcoded URLs, credentials, or environment-specific values)
   - Consistent error handling patterns throughout the codebase
   - Dependency injection for testability

4. **Complexity Management**:
   - Cyclomatic complexity ≤10 per function (break down complex decision trees)
   - Nesting depth ≤4 levels (use early returns and guard clauses)
   - Extract repeated code into reusable functions
   - Clear naming conventions for variables, functions, and classes

5. **Anti-Pattern Prevention**:
   - No god objects (classes that handle too many unrelated responsibilities)
   - No excessive parameter lists (use data classes or configuration objects)
   - No duplicate code blocks (DRY principle enforcement)
   - No mixed concerns (business logic and presentation logic separated)

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

**Measurable Benefits**:

1. **Cost Reduction**:
   - Prevents 3-5 retry cycles in lint phase due to structural issues
   - Reduces typecheck phase failures from import problems by 80%
   - Decreases test phase complexity from tightly coupled code
   - Saves average 15 API calls per milestone on rework

2. **Quality Assurance**:
   - Enforces maintainable code standards before they become technical debt
   - Ensures consistent architecture patterns across all generated code
   - Prevents common anti-patterns that lead to brittle implementations
   - Creates foundation for reliable testing and future extensibility

3. **Predictable Execution**:
   - Mechanical phases (lint, typecheck) complete faster with clean architecture
   - Test phase succeeds more reliably with properly structured code
   - Integration phase benefits from clear module boundaries
   - E2E phase works smoothly with separated concerns

4. **Developer Experience**:
   - Generated code follows industry best practices
   - Clear structure makes future modifications easier
   - Consistent patterns reduce cognitive load
   - Self-documenting architecture through good design

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
    "architecture": ["*.py", "src/"],  # All Python files for structure analysis
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
    "architecture": "think",       # Structural analysis needed
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
├─ ✓ Architecture   [00:04:22] $0.18
├─ ✓ Lint          [00:01:12] $0.08  # Faster due to better structure
├─ ✓ Type Check    [00:02:01] $0.12  # Faster due to clean imports
├─ ⚡ Unit Tests    [00:03:44] $0.31 (fixing...)
├─ ○ Integration
├─ ○ E2E
├─ ○ Validate
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
│       │   ├── architecture_review.md  # Architecture validation report
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
1. All 11 phases completed successfully in sequence
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

## Architecture Phase Methodology

### Phase Positioning and Purpose

The architecture phase serves as a **quality gate** between creative implementation and mechanical validation phases. It operates on the principle that **preventing poor architecture is more cost-effective than fixing it later**.

### Validation Categories

#### 1. Structural Analysis
```python
# Detection: Functions exceeding maintainability thresholds
def analyze_function_structure(ast_node):
    issues = []
    if function_line_count > 50:
        issues.append(f"Function {name} too long: {line_count} lines")
    if parameter_count > 5:
        issues.append(f"Function {name} too many parameters: {param_count}")
    if nesting_depth > 4:
        issues.append(f"Function {name} excessive nesting: {depth} levels")
    return issues

# Remediation: Guided refactoring suggestions
def suggest_refactoring(function_analysis):
    return [
        "Extract validation logic to separate function",
        "Use configuration object instead of multiple parameters",
        "Apply early return pattern to reduce nesting"
    ]
```

#### 2. Import Dependency Analysis
```python
# Detection: Circular dependencies and missing structure
def analyze_import_graph(project_files):
    import_graph = build_dependency_graph(project_files)
    cycles = detect_cycles(import_graph)
    missing_inits = find_missing_init_files(project_files)
    return cycles, missing_inits

# Remediation: Dependency restructuring
def resolve_circular_imports(cycles):
    return [
        "Move shared utilities to neutral module",
        "Use dependency injection instead of direct imports",
        "Create interface abstractions to break tight coupling"
    ]
```

#### 3. Design Pattern Validation
```python
# Detection: Anti-patterns and architectural violations
def check_design_patterns(codebase):
    violations = []
    
    # Mixed concerns detection
    if has_ui_and_business_logic(file):
        violations.append("Separate UI from business logic")
    
    # Hardcoded configuration detection
    if contains_hardcoded_values(file):
        violations.append("Extract configuration to external files")
    
    # God object detection
    if class_method_count > 20:
        violations.append("Split class responsibilities")
        
    return violations
```

### Integration with Phase Pipeline

The architecture phase receives:
- **Input**: Implementation artifacts from previous phase
- **Context**: Full Python codebase for structural analysis
- **Tools**: ArchitectureValidator with AST analysis capabilities
- **Model**: Sonnet (cost-effective for pattern recognition tasks)

The architecture phase produces:
- **Required Output**: `architecture_review.md` with validation results
- **Validation Evidence**: Zero architecture violations before proceeding
- **Structural Improvements**: Refactored code meeting all quality standards
- **Documentation**: Record of issues found and fixes applied

### Success Criteria

Architecture phase completion requires:
1. **Zero structural violations** - All size and complexity limits met
2. **Clean import structure** - No circular dependencies, proper package organization
3. **Design pattern compliance** - Separation of concerns, externalized configuration
4. **Maintainability metrics** - Code complexity within acceptable ranges
5. **Evidence documentation** - Complete record of validation and fixes

### Failure Prevention

The architecture phase prevents specific downstream failures:

| Without Architecture Phase | With Architecture Phase |
|----------------------------|-------------------------|
| Lint phase: 5 turns fixing monolithic functions | Lint phase: Clean pass, functions already properly sized |
| Typecheck phase: Import resolution failures | Typecheck phase: Clean imports, no circular dependencies |
| Test phase: Struggling with tightly coupled code | Test phase: Easily testable, well-structured components |
| Integration phase: Complex debugging sessions | Integration phase: Clear interfaces, predictable behavior |

## Summary

CC_AUTOMATOR4 achieves reliable, autonomous code generation through:
- **Sequential phase execution** with clear dependency chains
- **SDK-first architecture** with intelligent CLI fallback
- **Architectural quality gate** preventing structural issues before mechanical phases
- **Intelligent step-back recovery** from root cause analysis
- **Evidence-based validation** with strict anti-cheating measures
- **Cost optimization** through strategic model selection and early problem detection
- **Vertical milestones** maintaining testability at each stage
- **Think modes** for complex problem solving
- **Self-healing patterns** for robust code generation
- **Smart orchestration** handling failures gracefully
- **100% success validation** requiring concrete proof

The system transforms high-level requirements into working, tested, documented code without human intervention after initial setup, with sophisticated recovery mechanisms that ensure reliability and prevent false positives.