# CC_AUTOMATOR4 Implementation Guide

**FOR CLAUDE CODE AGENTS**: This document contains everything needed to implement robust cc_automator4 features. Follow these patterns and principles exactly.

## WORKING NOTES (REMOVE WHEN COMPLETE)
<!-- Archive to: docs/implementation_strategies.md when done -->

### CURRENT PRIORITY: Fix SDK TaskGroup Errors ✅ ROOT CAUSE IDENTIFIED
**GOAL**: Make SDK work consistently without CLI fallbacks
**STRATEGY**: Fix async cleanup race conditions in Claude Code SDK
**STATUS**: 🔍 DIAGNOSED - Root cause in SDK subprocess transport layer

**Root Cause Identified**: TaskGroup errors are async cleanup race conditions in:
- **File**: `/lib/python3.10/site-packages/claude_code_sdk/_internal/transport/subprocess_cli.py`
- **Issue**: `tg.cancel_scope.cancel()` called while `read_stderr` task still running
- **Impact**: Work completes successfully, but cleanup fails with "unhandled errors"

**Key File Locations**:
- **Main orchestrator**: `src/orchestrator.py:635`
- **Phase execution**: `src/phase_orchestrator.py:156-188`  
- **SDK wrapper**: `src/claude_code_sdk_fixed_v2.py`
- **Error handling**: `src/phase_orchestrator.py:799-816`

**Evidence**:
- ✅ No resource leaks (memory +0.8MB only, no file/thread leaks)
- ✅ 100% work completion rate (even "failed" calls complete successfully)
- ❌ 20% TaskGroup cleanup errors during normal operation
- ❌ CLI fallback masks issue and loses SDK features

**Fix Strategy**:
1. **Improve error classification** - Distinguish cleanup errors from real failures
2. **Fix SDK TaskGroup cleanup** - Remove forced cancellation in finally block
3. **Add timeout handling** - For long-running WebSearch operations
4. **Keep CLI fallback minimal** - Only for actual SDK failures, not cleanup noise

<!-- Remove this entire section when SDK issues are resolved -->

## File Organization & Navigation

**CC_AUTOMATOR4 uses a clean, organized directory structure:**

### 📁 Root Directory (Essential Files Only)
```
cc_automator4/
├── CLAUDE.md              # This file - main instructions
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
├── claude_code_sdk_fixed_v2.py # SDK wrapper with bug fixes
├── session_manager.py         # Session tracking
├── progress_tracker.py        # Progress and cost tracking
├── milestone_decomposer.py    # Milestone parsing
├── phase_prompt_generator.py  # Dynamic prompt generation
├── file_parallel_executor.py  # Parallel file processing
├── preflight_validator.py     # Environment validation
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

### 🎯 Quick Navigation for Claude Agents

**When debugging or implementing:**
- **Main entry point**: `cli.py` 
- **Core logic**: `src/orchestrator.py`
- **Phase execution**: `src/phase_orchestrator.py`
- **SDK issues**: `src/claude_code_sdk_fixed_v2.py`
- **Tests**: `tests/` (organized by type)
- **Documentation**: `docs/` (organized by purpose)

**File Creation Guidelines:**
- ✅ **Core system files**: Add to `src/` with relative imports
- ✅ **Tests**: Add to appropriate `tests/` subdirectory
- ✅ **Documentation**: Add to appropriate `docs/` subdirectory  
- ✅ **Utilities**: Add to appropriate `tools/` subdirectory
- ❌ **Never**: Create files in root directory (except essential config)

## 📋 Detailed File Creation & Reference Rules

### 🎯 **FOR CLAUDE AGENTS: Follow These Rules Exactly**

#### **1. When Creating New Files**

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

**✅ Documentation Files** (Add to `docs/`)
```markdown
<!-- NEW FILE: docs/implementation/new_feature_guide.md -->
# New Feature Implementation Guide
...
```

**✅ Debug/Analysis Tools** (Add to `tools/`)
```python
# NEW FILE: tools/debug/debug_new_issue.py
from pathlib import Path
import sys
sys.path.append(str(Path(__file__).parent.parent))
from src.component import Component
```

#### **2. When Referencing Existing Files**

**✅ Use Relative Paths from Project Root**
- ✅ `src/orchestrator.py` 
- ✅ `tests/unit/test_component.py`
- ✅ `docs/implementation/guide.md`
- ❌ `/home/brian/cc_automator4/src/orchestrator.py` (absolute paths)

**✅ Include Line Numbers for Debugging**
- ✅ `src/phase_orchestrator.py:156` (specific function)
- ✅ `src/orchestrator.py:635-642` (code block)

#### **3. Import Statement Rules**

**Within `src/` directory - USE RELATIVE IMPORTS:**
```python
# ✅ CORRECT: Relative imports within src/
from .phase_orchestrator import PhaseOrchestrator
from .session_manager import SessionManager
from .progress_tracker import ProgressTracker

# ❌ WRONG: Absolute imports within src/
from phase_orchestrator import PhaseOrchestrator
from session_manager import SessionManager
```

**From outside `src/` directory - USE MODULE IMPORTS:**
```python
# ✅ CORRECT: From cli.py or tests
from src.orchestrator import CCAutomatorOrchestrator
from src.phase_orchestrator import Phase

# ❌ WRONG: Direct imports
from orchestrator import CCAutomatorOrchestrator
```

#### **4. File Organization Decision Tree**

**🤔 Where should I put this file?**

```
Is it core system logic?
├─ YES → src/
│   ├─ Main orchestration? → src/orchestrator.py or src/phase_orchestrator.py
│   ├─ Data management? → src/session_manager.py, src/progress_tracker.py
│   └─ Utilities? → src/[utility_name].py
│
├─ Is it a test?
│   ├─ Tests one component? → tests/unit/
│   ├─ Tests interaction between components? → tests/integration/
│   ├─ Tests SDK functionality? → tests/sdk/
│   └─ End-to-end scenario? → tests/scenarios/
│
├─ Is it documentation?
│   ├─ Technical specification? → docs/specifications/
│   ├─ Implementation guide? → docs/implementation/
│   └─ Troubleshooting guide? → docs/troubleshooting/
│
└─ Is it a utility or tool?
    ├─ Setup/installation? → tools/setup/
    ├─ Debugging tool? → tools/debug/
    └─ Analysis tool? → tools/analysis/
```

#### **5. File Naming Conventions**

**✅ Python Files:**
- `snake_case.py` for all Python files
- Descriptive names: `phase_orchestrator.py` not `orchestrator2.py`
- Test files: `test_[component_name].py`

**✅ Documentation Files:**
- `UPPERCASE.md` for specifications: `REQUIREMENTS.md`
- `lowercase_with_underscores.md` for guides: `implementation_guide.md`

**✅ Directories:**
- `lowercase` for all directories
- Plural when containing multiple items: `tests/`, `docs/`, `tools/`

#### **6. Evidence File Creation (Critical for Anti-Cheating)**

**When implementing phases, ALWAYS create evidence files:**

```python
# ✅ CORRECT: Create evidence in milestone directory
milestone_dir = Path(".cc_automator/milestones/milestone_1")
evidence_file = milestone_dir / "research.md"
evidence_file.write_text("# Research Evidence\n\n...")

# ✅ CORRECT: Reference evidence files
evidence_path = "milestone_1/research.md"  # Relative to .cc_automator/milestones/
```

#### **7. Common Anti-Patterns to Avoid**

```python
# ❌ WRONG: Creating files in root directory
with open("temp_debug.py", "w") as f:
    f.write("...")

# ✅ CORRECT: Put debug files in tools/debug/
with open("tools/debug/temp_debug.py", "w") as f:
    f.write("...")

# ❌ WRONG: Hardcoded absolute paths
import sys
sys.path.append("/home/brian/cc_automator4/src")

# ✅ CORRECT: Relative imports or module imports
from src.component import Component

# ❌ WRONG: Vague file references in documentation
"Update the orchestrator file"

# ✅ CORRECT: Specific file references  
"Update `src/orchestrator.py:156-162`"
```

### 🎯 **Quick Reference for File Operations**

**Creating Files:**
- Core logic → `src/[name].py` with relative imports
- Tests → `tests/[category]/test_[name].py`
- Docs → `docs/[category]/[name].md`
- Tools → `tools/[category]/[name].py`

**Referencing Files:**
- Always use relative paths from project root
- Include line numbers for debugging: `:156` or `:156-162`
- Use consistent path separators: `/` not `\`

**Importing Code:**
- Within src/: Use relative imports (`.component`)
- From outside src/: Use module imports (`src.component`)

## Core Philosophy

**Purpose**: Prevent Claude from claiming task completion without concrete proof
**Method**: Evidence-based validation with independent verification  
**Strategy**: Optimize for speed (parallel) and cost (model selection) while maintaining quality

## THE FUNDAMENTAL PURPOSE

**CC_AUTOMATOR4 EXISTS TO SOLVE ONE CRITICAL PROBLEM:**

Claude Code agents routinely **LIE** about task completion. They claim "successfully implemented feature X" when they actually did nothing, created broken code, or only did part of the work. This happens constantly and is the core problem this system prevents.

### The Anti-Cheating Philosophy

**CARDINAL RULE: NEVER TRUST AGENT CLAIMS WITHOUT CONCRETE PROOF**

Every single validation MUST be:
- ✅ **Independent**: External tools verify success
- ✅ **Concrete**: Specific files/outputs required
- ✅ **Strict**: No "close enough" or "probably works"
- ❌ **Never**: Trust what Claude says it did

## Core System Architecture

### Nine-Phase Pipeline
```
research → planning → implement → lint → typecheck → test → integration → e2e → commit
```

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

### Commit Phase
- **MUST create git commit** with proper message format

## Tool Usage Philosophy

- **No artificial tool restrictions per phase** - use what's needed
- Phase-specific requirements above are minimums, not maximums
- Leverage Claude's intelligence for tool selection
- **Full tool access** unless specifically constrained

## Execution Strategy

- **Always use SDK** - Streaming, cost tracking, MCP integration
- **DEBUGGING MODE**: Disable CLI fallback to surface SDK issues
- CLI fallback = SDK failure (should be eliminated, not masked)
- **Use parallel processing** for lint/typecheck phases by default

### SDK Debug Priority
- **Current State**: TaskGroup errors causing frequent CLI fallbacks
- **Required Action**: Fix SDK wrapper to handle all error scenarios
- **Temporary Strategy**: Fail hard instead of fallback to debug root causes

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

# ❌ ABSOLUTELY WRONG: Accept "close enough"
def _validate_e2e_phase():
    if evidence_log_missing:
        return main_py_runs_without_crash()  # THIS IS CHEATING!
```

## Quick Reference

### Phase Outputs Required
- **research**: `milestone_N/research.md` (>100 chars)
- **planning**: `milestone_N/plan.md` (>50 chars)  
- **implement**: `main.py` OR `src/*.py` files
- **lint**: Zero F-errors from `flake8 --select=F`
- **typecheck**: Clean output from `mypy --strict`
- **test**: `pytest tests/unit` passes
- **integration**: `pytest tests/integration` passes
- **e2e**: `milestone_N/e2e_evidence.log` AND `python main.py` succeeds
- **commit**: Git commit created

### Common Validation Commands
- **Lint**: `flake8 --select=F`
- **Typecheck**: `mypy --strict`
- **Unit tests**: `pytest tests/unit`
- **Integration tests**: `pytest tests/integration`
- **E2E test**: `python main.py` (with input handling)

## Common Error Patterns

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

### Turn Limit Issues
- **Symptom**: Phase fails due to insufficient turns
- **Solution**: Research=30, Planning=50, Validate=50 turns minimum

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
        return "claude-3-5-sonnet-20241022"
    
    # Default logic
    if phase_name in ["lint", "typecheck"]:
        return "claude-3-5-sonnet-20241022"  # Cost-effective
    return None  # Use default (Opus)
```

## Common Anti-Patterns to Avoid

### ❌ The DEADLY Sin: Accepting "Close Enough"
```python
# ABSOLUTELY FORBIDDEN: Weakening validation requirements
def validate_e2e():
    required_files = find_evidence_logs()
    if not required_files:
        # ❌ NEVER DO THIS - this is exactly what Claude wants!
        return test_main_py_directly()  # This defeats the entire purpose!
    return True

# ✅ CORRECT: Strict validation only
def validate_e2e():
    required_files = find_evidence_logs()
    return len(required_files) > 0  # Evidence required, no exceptions
```

### ❌ Trusting Agent Claims
```python
# WRONG: Believing what Claude says
if "successfully completed" in response:
    return success
```

### ❌ Hardcoded Solutions  
```python
# WRONG: Project-specific logic
if "calculator" in project_name:
    test_input = "1\n10\n5\n8\n"
```

## Implementation Checklist

When implementing any cc_automator4 feature:

- [ ] Does it work for ANY project type? (not just current one)
- [ ] Does it have independent validation? (not trust agent claims)  
- [ ] Does it handle SDK bugs gracefully?
- [ ] Does it optimize costs appropriately?
- [ ] Does it collect concrete evidence?
- [ ] Does it follow the nine-phase pipeline?
- [ ] Does it support parallel execution where beneficial?
- [ ] Does it iterate until success or max attempts?

## Documentation Archive

When implementation is complete, move working notes to:
- `docs/implementation_strategies.md` - Problem-solving approaches used
- `docs/debugging_history.md` - What was tried and failed
- `docs/decision_rationale.md` - Why certain approaches were chosen

**Remember**: The goal is a robust, generalist system that prevents Claude from taking shortcuts while optimizing for speed and cost.