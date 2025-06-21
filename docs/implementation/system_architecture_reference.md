# CC_AUTOMATOR4 System Architecture Reference

This document contains detailed implementation patterns, phase requirements, and architectural guidelines that were moved from CLAUDE.md to keep the main implementation guide focused.

## Core System Architecture

### Eleven-Phase Pipeline
```
research → planning → implement → architecture → lint → typecheck → test → integration → e2e → validate → commit
```

**Architecture Quality Gate**: The architecture phase serves as a critical quality gate between creative implementation and mechanical validation phases, preventing structural issues that would waste cycles in downstream phases.

**Each phase MUST:**
1. Create specific output files for validation
2. Pass independent validation commands 
3. Build on previous phase outputs
4. Handle errors gracefully with evidence
5. **NEVER be marked complete without concrete proof**

## Phase-Specific Requirements

### Research Phase
- **MUST use WebSearch** for current information, API docs, best practices
- **MUST read existing codebase** to understand current state
- Output: `milestone_N/research.md` (>100 chars)

### Planning Phase  
- **MUST read existing codebase** before planning
- **MUST reference research findings** from previous phase
- Output: `milestone_N/plan.md` (>50 chars)

### Implementation Phase
- **Full tool access** - use whatever tools needed
- Output: `main.py` OR `src/*.py` files

### Architecture Phase
- **MUST enforce structural standards**: Functions ≤50 lines, classes ≤20 methods, files ≤1000 lines
- **MUST validate import structure**: No circular imports, proper `__init__.py` files
- **MUST check design patterns**: Separation of concerns, externalized configuration
- **MUST prevent anti-patterns**: God objects, excessive nesting, hardcoded values
- Output: `milestone_N/architecture_review.md` with zero violations
- **COST OPTIMIZATION**: Uses Sonnet model for pattern recognition efficiency

### Lint Phase
- **MUST achieve zero F-errors**: `flake8 --select=F` returns 0
- Use parallel file processing for speed

### Typecheck Phase
- **MUST pass strict typing**: `mypy --strict` returns clean
- Use parallel file processing for speed

### Test Phase
- **MUST pass unit tests**: `pytest tests/unit` succeeds
- Generate specific error feedback for retries

### Integration Phase
- **MUST pass integration tests**: `pytest tests/integration` succeeds

### E2E Phase
- **MUST create evidence log**: `milestone_N/e2e_evidence.log`
- **MUST test main.py execution** with interactive program detection
- **MUST validate user journeys**: Test realistic command sequences (e.g., fetch→analyze)
- **MUST check integration consistency**: Verify related commands work together properly
- **MUST detect state dependencies**: Ensure commands handle missing prerequisites gracefully

### Commit Phase
- **MUST create git commit** with proper message format

## File Organization & Navigation

**CC_AUTOMATOR4 uses a clean, organized directory structure:**

### 📁 Root Directory (Essential Files Only)
```
cc_automator4/
├── CLAUDE.md              # Main implementation guide
├── README.md              # User documentation  
├── cli.py                 # Main CLI entry point
├── run.py                 # Legacy entry point
├── requirements.txt       # Python dependencies
└── example_projects/      # Test projects
```

### 📁 Core System (`src/`)
```
src/
├── orchestrator.py            # Main orchestration logic
├── phase_orchestrator.py      # Phase execution engine  
├── claude_code_sdk_stable.py  # Consolidated SDK wrapper
├── session_manager.py         # Session tracking
├── progress_tracker.py        # Progress and cost tracking
├── milestone_decomposer.py    # Milestone parsing
├── phase_prompt_generator.py  # Dynamic prompt generation
├── file_parallel_executor.py  # Parallel file processing
├── preflight_validator.py     # Environment validation
├── architecture_validator.py  # Architectural quality validation
└── ...                        # Other core modules
```

### 📁 Tests (`tests/`)
```
tests/
├── unit/          # Unit tests for individual components
├── integration/   # Integration tests for phase interactions  
├── sdk/          # SDK-specific tests and debugging
└── scenarios/    # End-to-end test scenarios
```

### 📁 Documentation (`docs/`)
```
docs/
├── specifications/    # Requirements and specifications
├── implementation/    # Technical implementation guides
└── troubleshooting/   # Debug guides and known issues
```

### 📁 Tools (`tools/`)
```
tools/
├── setup/     # Installation and setup scripts
├── debug/     # Debugging and diagnostic tools
└── analysis/  # Analysis and research tools
```

## File Creation & Reference Rules

### When Creating New Files

**✅ Core System Components** (Add to `src/`)
```python
# NEW FILE: src/new_component.py
from .existing_component import ExistingClass
from .phase_orchestrator import Phase

class NewComponent:
    def __init__(self):
        # Use relative imports within src/
        pass
```

**✅ Test Files** (Add to appropriate `tests/` subdirectory)
```python
# NEW FILE: tests/unit/test_new_component.py
import pytest
from src.new_component import NewComponent

def test_new_component():
    pass
```

### Import Statement Rules

**Within `src/` directory - USE RELATIVE IMPORTS:**
```python
# ✅ CORRECT: Relative imports within src/
from .phase_orchestrator import PhaseOrchestrator
from .session_manager import SessionManager

# ❌ WRONG: Absolute imports within src/
from phase_orchestrator import PhaseOrchestrator
```

**From outside `src/` directory - USE MODULE IMPORTS:**
```python
# ✅ CORRECT: From cli.py or tests
from src.orchestrator import CCAutomatorOrchestrator

# ❌ WRONG: Direct imports
from orchestrator import CCAutomatorOrchestrator
```

## Evidence-Based Validation Philosophy

**NEVER TRUST AGENT CLAIMS** - Always verify with independent validation:

```python
# ✅ CORRECT: Independent validation
def _validate_lint_phase():
    result = subprocess.run(["flake8", "--select=F"], capture_output=True)
    return result.returncode == 0

# ❌ WRONG: Trust agent claims
def _validate_lint_phase():
    return "lint phase completed successfully" in agent_response
```

## Critical Implementation Patterns

### 1. Interactive Program Detection (E2E Phase)

```python
def detect_interactive_program(file_path: Path) -> bool:
    """Detect if a Python program requires user input."""
    content = file_path.read_text()
    return 'input(' in content or 'raw_input(' in content

def get_common_exit_inputs() -> List[str]:
    """Return common exit input patterns to try."""
    return [
        "q\n",           # Quit
        "exit\n",        # Exit command  
        "0\n",           # Zero (common exit option)
        "\n" * 5,       # Multiple enters
        "quit\n",       # Quit command
        "bye\n",        # Goodbye
    ]
```

### 2. File Parallel Execution (Lint/Typecheck)

```python
# ✅ CORRECT: True parallel execution
with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
    future_to_file = {
        executor.submit(self.fix_file_errors, file_path, errors): file_path
        for file_path, errors in errors_by_file.items()
    }
    
    for future in as_completed(future_to_file):
        result = future.result()
```

### 3. Model Selection for Cost Optimization

```python
def _select_model_for_phase(phase_name: str) -> Optional[str]:
    # Check environment overrides first
    if os.environ.get('FORCE_SONNET') == 'true':
        return "claude-sonnet-4-20250514"
    
    # Mechanical phases use cost-effective Sonnet
    mechanical_phases = ["architecture", "lint", "typecheck"]
    if phase_name in mechanical_phases:
        return "claude-sonnet-4-20250514"  # Cost-effective for pattern recognition
    return None  # Use default (Opus) for creative work
```

## Architecture Phase Methodology

### The Quality Gate Principle

The architecture phase operates on the principle that **preventing poor architecture is more cost-effective than fixing it later**. It serves as a quality gate between creative implementation and mechanical validation phases.

### Validation Categories

#### 1. Code Structure Validation
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
```

#### 2. Import Dependency Analysis
```python
# Detection: Circular dependencies and missing structure
def analyze_import_graph(project_files):
    import_graph = build_dependency_graph(project_files)
    cycles = detect_cycles(import_graph)
    missing_inits = find_missing_init_files(project_files)
    return cycles, missing_inits
```

### Architecture Standards Enforced

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

## Common Error Patterns

### Integration Failures Between Commands
- **Symptom**: Individual commands work but fail when used in sequence (e.g., fetch→analyze)
- **Root Cause**: E2E phase only does smoke testing, not workflow validation
- **Solution**: Implement user journey testing for common command sequences
- **Detection**: Test sequential commands with dependency relationships
- **Prevention**: Validate state persistence and graceful degradation

### "TaskGroup" SDK Errors
- **Symptom**: TaskGroup error with partial completion
- **Current Issue**: Happening frequently, masking root problems
- **Debug Action**: Disable CLI fallback, capture full error context
- **Root Cause**: SDK wrapper incomplete - needs comprehensive TaskGroup handling
- **Goal**: Fix SDK wrapper to eliminate TaskGroup errors entirely

### Interactive Program Hangs
- **Symptom**: E2E phase hangs on `input()` calls
- **Diagnosis**: Detect interactive programs with content analysis
- **Action**: Use generalist exit patterns (`q\n`, `exit\n`, `0\n`, etc.)

## Enhanced E2E Validation Implementation

The enhanced E2E validation system includes:

1. **User Journey Validation**: Test realistic command sequences
2. **Integration Consistency**: Verify related commands work together
3. **State Dependency Detection**: Ensure graceful handling of missing prerequisites

Key files to implement (when Phase 1 is complete):
- `src/user_journey_validator.py`
- `src/integration_consistency_validator.py` 
- `src/enhanced_e2e_validator.py`

## Implementation Checklist

When implementing any cc_automator4 feature:

- [ ] Does it work for ANY project type? (not just current one)
- [ ] Does it have independent validation? (not trust agent claims)  
- [ ] Does it handle SDK bugs gracefully?
- [ ] Does it optimize costs appropriately?
- [ ] Does it collect concrete evidence?
- [ ] Does it follow the eleven-phase pipeline with architecture quality gate?
- [ ] Does it support parallel execution where beneficial?
- [ ] Does it iterate until success or max attempts?
- [ ] Does it validate user workflows, not just individual commands?
- [ ] Does it check integration consistency between related features?