# CC_AUTOMATOR4 Implementation Guide

**FOR CLAUDE CODE AGENTS**: This document contains everything needed to implement robust cc_automator4 features. Follow these patterns and principles exactly.

## 🚨 CRITICAL SYSTEM STABILITY WORK (HIGHEST PRIORITY)

**PRIMARY GOAL**: Build a stable, honest, and verifiable automation system
**CURRENT STATUS**: ❌ SYSTEM IS UNSTABLE - SDK errors causing constant failures
**APPROACH**: Stop all feature development until foundational stability is achieved

### STABILITY CRISIS ANALYSIS

**Root Cause**: The underlying SDK is fundamentally unstable, causing:
- CLIJSONDecodeError: Failed to decode JSON (current primary failure)
- TaskGroup unhandled errors (partially addressed but not eliminated)
- System claiming success when it actually failed (anti-pattern)
- Recovery tools themselves failing (meta-failure)

**Impact**: The system cannot be trusted because:
1. It lies about completion status
2. Evidence files may be fabricated or incomplete  
3. Recovery mechanisms are unreliable
4. Users get broken implementations marked as "successful"

### NEW DIRECTIVES (NON-NEGOTIABLE)

**Directive 1: Absolute Honesty**
- NEVER claim success without verifiable proof
- Treat ALL errors as critical failures requiring fixes
- Embrace failure as data - don't hide problems

**Directive 2: SDK Stability First**  
- Build one consolidated `claude_code_sdk_stable.py` 
- Create rigorous test suite in `tests/sdk/`
- NO SDK wrapper is "done" until it passes ALL stability tests
- Eliminate ALL CLIJSONDecodeError and TaskGroup errors

**Directive 3: Evidence-Based Validation**
- Complete `src/enhanced_e2e_validator.py` (remove NotImplementedError)
- Enforce strict evidence logs with actual command outputs
- Implement user journey integration tests
- Make validation impossible to deceive

**Directive 4: Verify Recovery Tools**
- Create tests for ALL recovery mechanisms
- Prove tools work before claiming they're functional
- Fix manual phase completion tool (currently failing)

### IMPLEMENTATION PRIORITY ORDER

**PHASE 1: SDK STABILIZATION** (BLOCKING ALL OTHER WORK)
1. ❌ Fix JSON repair bug in `src/claude_code_sdk_stable.py`
2. ❌ Make ALL tests in `tests/sdk/manual_sdk_test.py` pass
3. ❌ Eliminate CLIJSONDecodeError completely
4. ❌ Prove SDK can execute 10 consecutive operations without failure

**PHASE 2: VALIDATION SYSTEM** (AFTER SDK IS STABLE)
1. ❌ Complete `src/enhanced_e2e_validator.py`
2. ❌ Implement strict evidence logging
3. ❌ Add user journey testing capability
4. ❌ Prove validator cannot be deceived

**PHASE 3: RECOVERY VERIFICATION** (AFTER VALIDATION WORKS)
1. ❌ Fix manual phase completion tool
2. ❌ Create tests for all recovery mechanisms
3. ❌ Verify each tool actually works

**PHASE 4: SYSTEM INTEGRATION** (AFTER ALL COMPONENTS STABLE)
1. ❌ Integrate stable SDK into phase orchestrator
2. ❌ Replace all unstable SDK wrappers
3. ❌ Run full system test with enhanced validation

### SUCCESS CRITERIA (MEASURABLE)

The system is considered stable when:
- [ ] `tests/sdk/manual_sdk_test.py` passes 100%
- [ ] Enhanced E2E validator detects all failure scenarios
- [ ] Recovery tools pass their own test suites
- [ ] 5 consecutive full project runs complete without SDK errors
- [ ] Evidence logs contain actual command outputs and statuses

### BLOCKED ACTIVITIES

Until stability is achieved, the following are FORBIDDEN:
- ❌ Any V4 meta-agent development
- ❌ New feature additions
- ❌ Performance optimizations
- ❌ Documentation updates (except this stability work)

**REMEMBER**: A broken system that claims to work is worse than a system that honestly admits its limitations.

## V4 Meta-Agent Development Guide

### Meta-Agent Architecture Overview

**Core Principle**: Build an intelligent orchestrator that can adapt strategies based on project context, failure patterns, and evidence-based learning while preserving V3's anti-cheating validation system.

#### Key Components to Implement

**1. Strategy Manager** (`src/v4_strategy_manager.py`)
- **Purpose**: Select and coordinate different orchestration strategies
- **Responsibilities**: 
  - Analyze project type and complexity
  - Choose appropriate strategy (simple pipeline, iterative refinement, parallel exploration)
  - Switch strategies based on failure patterns
- **Integration**: Uses V3 phase pipeline as one available strategy

**2. Failure Pattern Analyzer** (`src/v4_failure_analyzer.py`)
- **Purpose**: Learn from V3 validation failures to improve decision-making
- **Responsibilities**:
  - Track phase failure patterns across projects
  - Identify common failure modes (infinite loops, validation failures, resource issues)
  - Suggest strategy adaptations based on historical data
- **Data Sources**: V3 validation logs, phase execution metrics, evidence files

**3. Multi-Strategy Executor** (`src/v4_multi_executor.py`)
- **Purpose**: Run multiple strategies in parallel when beneficial
- **Responsibilities**:
  - Execute competing approaches simultaneously
  - Select best result based on evidence quality
  - Manage resource allocation across strategies
- **Integration**: Uses V3's evidence-based validation to compare strategy outcomes

**4. Context Analyzer** (`src/v4_context_analyzer.py`)
- **Purpose**: Understand project characteristics to inform strategy selection
- **Responsibilities**:
  - Analyze codebase size, complexity, technology stack
  - Identify project patterns (web app, CLI tool, library, etc.)
  - Assess test coverage and architectural quality
- **Output**: Context profile used by Strategy Manager

#### Implementation Strategy

**Phase 1: Foundation** (Week 1)
1. Create basic meta-agent skeleton that wraps V3 orchestrator
2. Implement simple strategy selection (default to V3 pipeline)
3. Add failure tracking and basic pattern recognition
4. Preserve all V3 validation and evidence systems

**Phase 2: Intelligence** (Week 2) 
1. Build context analyzer for project type detection
2. Implement multiple orchestration strategies
3. Add failure pattern learning from V3 execution logs
4. Create strategy switching based on failure analysis

**Phase 3: Optimization** (Week 3)
1. Add parallel strategy execution
2. Implement intelligent resource management
3. Build comprehensive strategy performance tracking
4. Create adaptive parameter tuning

#### Technical Requirements

**Preserve V3 Guarantees**:
- ✅ Evidence-based validation (no trusting agent claims)
- ✅ Independent verification of all phase outputs
- ✅ Anti-cheating system prevents false completions
- ✅ All existing file creation and validation rules

**Add V4 Intelligence**:
- 🔄 **Strategy Adaptation**: Learn from failures and adapt approaches
- 🔄 **Context Awareness**: Different strategies for different project types  
- 🔄 **Parallel Exploration**: Run multiple approaches when beneficial
- 🔄 **Failure Recovery**: Intelligent retry and pivot strategies

**File Structure for V4**:
```
src/
├─ v4_meta_orchestrator.py      # Main V4 entry point
├─ v4_strategy_manager.py       # Strategy selection and coordination
├─ v4_failure_analyzer.py       # Failure pattern recognition
├─ v4_multi_executor.py         # Parallel strategy execution
├─ v4_context_analyzer.py       # Project context analysis
└─ strategies/                  # Individual strategy implementations
   ├─ v3_pipeline_strategy.py   # Wrap existing V3 pipeline
   ├─ iterative_strategy.py     # Iterative refinement approach
   └─ parallel_strategy.py      # Parallel exploration approach
```

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
- **architecture**: `milestone_N/architecture_review.md` AND zero violations from ArchitectureValidator
- **lint**: Zero F-errors from `flake8 --select=F`
- **typecheck**: Clean output from `mypy --strict`
- **test**: `pytest tests/unit` passes
- **integration**: `pytest tests/integration` passes
- **e2e**: `milestone_N/e2e_evidence.log` AND `python main.py` succeeds AND user journeys validated
- **commit**: Git commit created

### Common Validation Commands
- **Lint**: `flake8 --select=F`
- **Typecheck**: `mypy --strict`
- **Unit tests**: `pytest tests/unit`
- **Integration tests**: `pytest tests/integration`
- **E2E test**: `python main.py` (with input handling)

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
        return "claude-sonnet-4-20250514"
    
    # Mechanical phases use cost-effective Sonnet
    mechanical_phases = ["architecture", "lint", "typecheck"]
    if phase_name in mechanical_phases:
        return "claude-sonnet-4-20250514"  # Cost-effective for pattern recognition
    return None  # Use default (Opus) for creative work
```

### 4. User Journey Validation (E2E Phase)

```python
def validate_user_journeys(cli_commands: List[str]) -> Dict[str, bool]:
    """Test realistic user workflows beyond basic smoke tests."""
    journeys = {
        "fetch_then_analyze": ["fetch AAPL", "analyze AAPL"],
        "search_then_view": ["search tech", "view MSFT"],
        "crud_operations": ["create", "list", "update 1", "delete 1"]
    }
    
    results = {}
    for journey_name, commands in journeys.items():
        success = test_command_sequence(commands)
        results[journey_name] = success
    return results

def test_command_sequence(commands: List[str]) -> bool:
    """Execute commands in sequence and validate outputs."""
    for i, cmd in enumerate(commands):
        result = run_command(f"python main.py {cmd}")
        if not validate_output(result, cmd, previous_commands=commands[:i]):
            return False
    return True
```

### 5. Integration Consistency Validation

```python
def validate_integration_consistency(commands: Dict[str, CommandInfo]) -> List[Issue]:
    """Ensure related commands have consistent behavior."""
    issues = []
    
    # Check state dependencies
    if "fetch" in commands and "analyze" in commands:
        if commands["fetch"].saves_to_db and not commands["analyze"].reads_from_db:
            issues.append("fetch saves data but analyze doesn't use it")
    
    # Check error handling consistency
    for cmd_pair in get_related_command_pairs(commands):
        if not have_consistent_error_handling(cmd_pair):
            issues.append(f"Inconsistent error handling: {cmd_pair}")
    
    return issues
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

#### 3. Design Pattern Enforcement
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

### Measurable Benefits

#### Cost Reduction
- Prevents 3-5 retry cycles in lint phase due to structural issues
- Reduces typecheck phase failures from import problems by 80%
- Decreases test phase complexity from tightly coupled code
- Saves average 15 API calls per milestone on rework

#### Quality Assurance
- Enforces maintainable code standards before they become technical debt
- Ensures consistent architecture patterns across all generated code
- Prevents common anti-patterns that lead to brittle implementations
- Creates foundation for reliable testing and future extensibility

#### Downstream Phase Optimization
Without Architecture Phase vs. With Architecture Phase:

| Phase | Without Architecture | With Architecture |
|-------|---------------------|------------------|
| **Lint** | 5 turns fixing monolithic functions | Clean pass, functions already properly sized |
| **Typecheck** | Import resolution failures | Clean imports, no circular dependencies |
| **Test** | Struggling with tightly coupled code | Easily testable, well-structured components |
| **Integration** | Complex debugging sessions | Clear interfaces, predictable behavior |

### Integration with Pipeline

**Input**: Implementation artifacts from previous phase  
**Context**: Full Python codebase for structural analysis  
**Tools**: ArchitectureValidator with AST analysis capabilities  
**Model**: Sonnet (cost-effective for pattern recognition tasks)  
**Output**: `architecture_review.md` with validation results  
**Success Criteria**: Zero architecture violations before proceeding

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
- [ ] Does it follow the eleven-phase pipeline with architecture quality gate?
- [ ] Does it support parallel execution where beneficial?
- [ ] Does it iterate until success or max attempts?
- [ ] Does it validate user workflows, not just individual commands?
- [ ] Does it check integration consistency between related features?

## Documentation Archive

When implementation is complete, move working notes to:
- `docs/implementation_strategies.md` - Problem-solving approaches used
- `docs/debugging_history.md` - What was tried and failed
- `docs/decision_rationale.md` - Why certain approaches were chosen

**Remember**: The goal is a robust, generalist system that prevents Claude from taking shortcuts while optimizing for speed and cost.

## E2E Enhancement Implementation Guide

### Required Files to Implement Enhanced E2E Testing

The following files must be created to implement the enhanced E2E testing that prevents integration failures like the fetch→analyze bug:

#### 1. Create `src/user_journey_validator.py`

```python
from typing import List, Dict, Optional, NamedTuple
import subprocess
import re
from pathlib import Path
import logging

class UserJourney(NamedTuple):
    name: str
    commands: List[str]
    forbidden_patterns: List[str]
    required_patterns: Optional[List[str]] = None

class JourneyResult(NamedTuple):
    success: bool
    command: str
    output: str
    error: Optional[str] = None

class UserJourneyValidator:
    """Validates realistic user workflows beyond basic smoke tests."""
    
    def __init__(self, project_root: Path):
        self.project_root = project_root
        self.logger = logging.getLogger(__name__)
    
    def get_default_journeys(self) -> List[UserJourney]:
        """Return common user journey patterns to test."""
        return [
            UserJourney(
                name="fetch_then_analyze",
                commands=["python main.py fetch AAPL", "python main.py analyze AAPL"],
                forbidden_patterns=[r"No data found", r"Error:", r"Traceback", r"failed"]
            ),
            UserJourney(
                name="crud_operations",
                commands=["python main.py create item1", "python main.py list", "python main.py update item1", "python main.py delete item1"],
                forbidden_patterns=[r"Error:", r"Traceback", r"not found", r"failed"]
            ),
            UserJourney(
                name="search_then_view",
                commands=["python main.py search tech", "python main.py view MSFT"],
                forbidden_patterns=[r"Error:", r"Traceback", r"not found", r"failed"]
            ),
            UserJourney(
                name="config_then_run",
                commands=["python main.py config set key=value", "python main.py run"],
                forbidden_patterns=[r"Error:", r"Traceback", r"not configured", r"failed"]
            )
        ]
    
    def detect_available_commands(self) -> List[str]:
        """Detect available commands by running help."""
        try:
            result = subprocess.run(
                ["python", "main.py", "--help"],
                cwd=self.project_root,
                capture_output=True,
                text=True,
                timeout=30
            )
            
            # Extract command names from help output
            commands = []
            for line in result.stdout.split('\n'):
                # Look for command patterns in help output
                if 'Commands:' in line or 'Usage:' in line:
                    continue
                # Simple heuristic: lines with alphanumeric words that could be commands
                words = line.strip().split()
                if words and words[0].isalpha() and len(words[0]) > 2:
                    commands.append(words[0])
            
            return commands[:10]  # Limit to reasonable number
        except Exception as e:
            self.logger.warning(f"Could not detect commands: {e}")
            return []
    
    def generate_adaptive_journeys(self) -> List[UserJourney]:
        """Generate journeys based on detected commands."""
        commands = self.detect_available_commands()
        journeys = []
        
        # Generate simple sequential patterns
        if len(commands) >= 2:
            for i in range(min(3, len(commands) - 1)):
                journeys.append(UserJourney(
                    name=f"sequence_{commands[i]}_{commands[i+1]}",
                    commands=[f"python main.py {commands[i]}", f"python main.py {commands[i+1]}"],
                    forbidden_patterns=[r"Error:", r"Traceback", r"failed", r"not found"]
                ))
        
        return journeys
    
    def validate_journey(self, journey: UserJourney) -> List[JourneyResult]:
        """Execute a user journey and validate outputs."""
        results = []
        
        for i, command in enumerate(journey.commands):
            try:
                result = subprocess.run(
                    command.split(),
                    cwd=self.project_root,
                    capture_output=True,
                    text=True,
                    timeout=60,
                    input="\n" * 10  # Provide default inputs for interactive programs
                )
                
                output = result.stdout + result.stderr
                success = self._validate_output(output, journey, command, i)
                
                results.append(JourneyResult(
                    success=success,
                    command=command,
                    output=output,
                    error=None if success else f"Command failed validation"
                ))
                
                # Stop on first failure
                if not success:
                    break
                    
            except subprocess.TimeoutExpired:
                results.append(JourneyResult(
                    success=False,
                    command=command,
                    output="",
                    error="Command timed out"
                ))
                break
            except Exception as e:
                results.append(JourneyResult(
                    success=False,
                    command=command,
                    output="",
                    error=str(e)
                ))
                break
        
        return results
    
    def _validate_output(self, output: str, journey: UserJourney, command: str, command_index: int) -> bool:
        """Validate command output against journey requirements."""
        # Check forbidden patterns
        for pattern in journey.forbidden_patterns:
            if re.search(pattern, output, re.IGNORECASE):
                self.logger.warning(f"Found forbidden pattern '{pattern}' in output: {output[:200]}")
                return False
        
        # Check required patterns if specified
        if journey.required_patterns:
            for pattern in journey.required_patterns:
                if not re.search(pattern, output, re.IGNORECASE):
                    self.logger.warning(f"Missing required pattern '{pattern}' in output")
                    return False
        
        # Command-specific validation
        if "fetch" in command and command_index == 0:
            # First fetch should show some data
            if len(output.strip()) < 10:
                self.logger.warning("Fetch command produced minimal output")
                return False
        
        return True
    
    def validate_all_journeys(self) -> Dict[str, bool]:
        """Validate all user journeys."""
        all_journeys = self.get_default_journeys() + self.generate_adaptive_journeys()
        results = {}
        
        for journey in all_journeys:
            journey_results = self.validate_journey(journey)
            overall_success = all(r.success for r in journey_results)
            results[journey.name] = overall_success
            
            if not overall_success:
                self.logger.error(f"Journey '{journey.name}' failed:")
                for result in journey_results:
                    if not result.success:
                        self.logger.error(f"  Command: {result.command}")
                        self.logger.error(f"  Error: {result.error}")
                        self.logger.error(f"  Output: {result.output[:200]}")
        
        return results
```

#### 2. Create `src/integration_consistency_validator.py`

```python
from typing import List, Dict, NamedTuple, Set
import ast
import re
from pathlib import Path
import logging

class CommandDependencies(NamedTuple):
    name: str
    reads_from_db: bool
    writes_to_db: bool
    requires_auth: bool
    requires_config: bool
    file_path: str

class DependencyInconsistency(NamedTuple):
    command1: str
    command2: str
    issue: str
    severity: str

class IntegrationConsistencyValidator:
    """Ensures related commands have consistent behavior and dependencies."""
    
    def __init__(self, project_root: Path):
        self.project_root = project_root
        self.logger = logging.getLogger(__name__)
    
    def analyze_command_dependencies(self) -> Dict[str, CommandDependencies]:
        """Analyze all commands to understand their dependencies."""
        dependencies = {}
        
        # Find command files
        command_files = list(self.project_root.rglob("**/commands.py")) + \
                      list(self.project_root.rglob("**/cli.py")) + \
                      list(self.project_root.rglob("main.py"))
        
        for file_path in command_files:
            try:
                file_deps = self._analyze_file_dependencies(file_path)
                dependencies.update(file_deps)
            except Exception as e:
                self.logger.warning(f"Could not analyze {file_path}: {e}")
        
        return dependencies
    
    def _analyze_file_dependencies(self, file_path: Path) -> Dict[str, CommandDependencies]:
        """Analyze a single file for command dependencies."""
        dependencies = {}
        
        try:
            content = file_path.read_text()
            tree = ast.parse(content)
            
            # Find command functions
            for node in ast.walk(tree):
                if isinstance(node, ast.FunctionDef):
                    cmd_deps = self._analyze_function_dependencies(node, content, str(file_path))
                    if cmd_deps:
                        dependencies[node.name] = cmd_deps
                
        except Exception as e:
            self.logger.warning(f"Could not parse {file_path}: {e}")
        
        return dependencies
    
    def _analyze_function_dependencies(self, func_node: ast.FunctionDef, content: str, file_path: str) -> Optional[CommandDependencies]:
        """Analyze a function to determine its dependencies."""
        func_source = ast.get_source_segment(content, func_node) or ""
        
        # Skip if not a command function
        if not self._is_command_function(func_node, func_source):
            return None
        
        reads_from_db = any(pattern in func_source for pattern in [
            ".get(", ".query(", ".filter(", "SELECT", "session.get"
        ])
        
        writes_to_db = any(pattern in func_source for pattern in [
            ".save(", ".create(", ".update(", ".delete(", "INSERT", "UPDATE", "session.add"
        ])
        
        requires_auth = any(pattern in func_source for pattern in [
            "auth", "login", "token", "authenticate", "permission"
        ])
        
        requires_config = any(pattern in func_source for pattern in [
            "config", "settings", "environment", "API_KEY", "SECRET"
        ])
        
        return CommandDependencies(
            name=func_node.name,
            reads_from_db=reads_from_db,
            writes_to_db=writes_to_db,
            requires_auth=requires_auth,
            requires_config=requires_config,
            file_path=file_path
        )
    
    def _is_command_function(self, func_node: ast.FunctionDef, func_source: str) -> bool:
        """Determine if a function is a CLI command."""
        # Check for CLI decorators
        for decorator in func_node.decorator_list:
            if isinstance(decorator, ast.Name) and decorator.id in ["command", "click_command"]:
                return True
            if isinstance(decorator, ast.Attribute) and decorator.attr == "command":
                return True
        
        # Check for CLI framework patterns
        cli_patterns = ["@app.command", "@click.command", "def main", "def cli"]
        return any(pattern in func_source for pattern in cli_patterns)
    
    def find_inconsistencies(self, dependencies: Dict[str, CommandDependencies]) -> List[DependencyInconsistency]:
        """Find dependency inconsistencies between related commands."""
        inconsistencies = []
        
        # Group related commands
        command_groups = self._group_related_commands(dependencies)
        
        for group_name, commands in command_groups.items():
            group_inconsistencies = self._check_group_consistency(commands)
            inconsistencies.extend(group_inconsistencies)
        
        return inconsistencies
    
    def _group_related_commands(self, dependencies: Dict[str, CommandDependencies]) -> Dict[str, List[CommandDependencies]]:
        """Group commands that are likely related."""
        groups = {
            "data_operations": [],
            "auth_operations": [],
            "config_operations": [],
            "analysis_operations": []
        }
        
        for cmd_name, cmd_deps in dependencies.items():
            # Data operations
            if any(keyword in cmd_name.lower() for keyword in ["fetch", "get", "load", "save", "store", "analyze", "process"]):
                groups["data_operations"].append(cmd_deps)
            
            # Auth operations
            if any(keyword in cmd_name.lower() for keyword in ["login", "auth", "user", "register"]):
                groups["auth_operations"].append(cmd_deps)
            
            # Config operations
            if any(keyword in cmd_name.lower() for keyword in ["config", "setup", "init", "configure"]):
                groups["config_operations"].append(cmd_deps)
            
            # Analysis operations
            if any(keyword in cmd_name.lower() for keyword in ["analyze", "report", "calculate", "predict"]):
                groups["analysis_operations"].append(cmd_deps)
        
        # Remove empty groups
        return {k: v for k, v in groups.items() if v}
    
    def _check_group_consistency(self, commands: List[CommandDependencies]) -> List[DependencyInconsistency]:
        """Check consistency within a group of related commands."""
        inconsistencies = []
        
        if len(commands) < 2:
            return inconsistencies
        
        # Check data persistence consistency
        writers = [cmd for cmd in commands if cmd.writes_to_db]
        readers = [cmd for cmd in commands if cmd.reads_from_db]
        
        if writers and readers:
            # Check if readers can actually read what writers write
            for writer in writers:
                for reader in readers:
                    if self._are_related_commands(writer.name, reader.name):
                        # They should have consistent DB access patterns
                        if writer.writes_to_db and not reader.reads_from_db:
                            inconsistencies.append(DependencyInconsistency(
                                command1=writer.name,
                                command2=reader.name,
                                issue=f"{writer.name} saves data but {reader.name} doesn't read from DB",
                                severity="high"
                            ))
        
        # Check configuration consistency
        config_users = [cmd for cmd in commands if cmd.requires_config]
        if len(config_users) > 1:
            # All should handle missing config consistently
            for i, cmd1 in enumerate(config_users):
                for cmd2 in config_users[i+1:]:
                    if not self._have_consistent_config_handling(cmd1, cmd2):
                        inconsistencies.append(DependencyInconsistency(
                            command1=cmd1.name,
                            command2=cmd2.name,
                            issue="Inconsistent configuration handling",
                            severity="medium"
                        ))
        
        return inconsistencies
    
    def _are_related_commands(self, cmd1: str, cmd2: str) -> bool:
        """Check if two commands are related (e.g., fetch/analyze)."""
        related_pairs = [
            ("fetch", "analyze"), ("get", "analyze"), ("load", "process"),
            ("create", "list"), ("add", "show"), ("save", "load"),
            ("search", "view"), ("find", "show")
        ]
        
        for pair in related_pairs:
            if (pair[0] in cmd1.lower() and pair[1] in cmd2.lower()) or \
               (pair[1] in cmd1.lower() and pair[0] in cmd2.lower()):
                return True
        
        return False
    
    def _have_consistent_config_handling(self, cmd1: CommandDependencies, cmd2: CommandDependencies) -> bool:
        """Check if two commands handle configuration consistently."""
        # This is a simplified check - in reality, you'd analyze the actual error handling
        return cmd1.requires_config == cmd2.requires_config
    
    def validate_consistency(self) -> Dict[str, any]:
        """Validate integration consistency across the project."""
        dependencies = self.analyze_command_dependencies()
        inconsistencies = self.find_inconsistencies(dependencies)
        
        return {
            "total_commands": len(dependencies),
            "inconsistencies": len(inconsistencies),
            "issues": [
                {
                    "command1": inc.command1,
                    "command2": inc.command2,
                    "issue": inc.issue,
                    "severity": inc.severity
                }
                for inc in inconsistencies
            ],
            "success": len(inconsistencies) == 0
        }
```

#### 3. Create `src/enhanced_e2e_validator.py`

```python
from typing import Dict, Tuple, List
from pathlib import Path
import logging
from .user_journey_validator import UserJourneyValidator
from .integration_consistency_validator import IntegrationConsistencyValidator

class EnhancedE2EValidator:
    """Enhanced E2E validator that combines basic tests with user journey validation."""
    
    def __init__(self, project_root: Path):
        self.project_root = project_root
        self.logger = logging.getLogger(__name__)
        self.journey_validator = UserJourneyValidator(project_root)
        self.consistency_validator = IntegrationConsistencyValidator(project_root)
    
    def validate_basic_requirements(self) -> Dict[str, bool]:
        """Validate basic E2E requirements (evidence log, main.py execution)."""
        results = {}
        
        # Check for evidence log
        evidence_files = list(self.project_root.rglob("**/*e2e_evidence.log"))
        results["evidence_log_exists"] = len(evidence_files) > 0
        
        # Check main.py exists and is executable
        main_py = self.project_root / "main.py"
        results["main_py_exists"] = main_py.exists()
        
        if main_py.exists():
            try:
                import subprocess
                result = subprocess.run(
                    ["python", "main.py", "--help"],
                    cwd=self.project_root,
                    capture_output=True,
                    timeout=30
                )
                results["main_py_executable"] = result.returncode == 0
            except Exception:
                results["main_py_executable"] = False
        else:
            results["main_py_executable"] = False
        
        return results
    
    def validate_user_journeys(self) -> Dict[str, bool]:
        """Validate user journey workflows."""
        return self.journey_validator.validate_all_journeys()
    
    def validate_integration_consistency(self) -> Dict[str, any]:
        """Validate integration consistency between commands."""
        return self.consistency_validator.validate_consistency()
    
    def validate_all(self) -> Tuple[bool, Dict[str, any]]:
        """Perform comprehensive E2E validation."""
        # Basic requirements
        basic_results = self.validate_basic_requirements()
        basic_success = all(basic_results.values())
        
        # User journey validation
        journey_results = self.validate_user_journeys()
        journey_success = all(journey_results.values())
        
        # Integration consistency validation
        consistency_results = self.validate_integration_consistency()
        consistency_success = consistency_results.get("success", False)
        
        # Overall success
        overall_success = basic_success and journey_success and consistency_success
        
        # Detailed results
        detailed_results = {
            "overall_success": overall_success,
            "basic_requirements": {
                "success": basic_success,
                "details": basic_results
            },
            "user_journeys": {
                "success": journey_success,
                "details": journey_results
            },
            "integration_consistency": {
                "success": consistency_success,
                "details": consistency_results
            }
        }
        
        # Log results
        if not overall_success:
            self.logger.error("Enhanced E2E validation failed:")
            if not basic_success:
                self.logger.error(f"  Basic requirements: {basic_results}")
            if not journey_success:
                failed_journeys = [k for k, v in journey_results.items() if not v]
                self.logger.error(f"  Failed journeys: {failed_journeys}")
            if not consistency_success:
                self.logger.error(f"  Consistency issues: {consistency_results.get('inconsistencies', 0)}")
        
        return overall_success, detailed_results
```

#### 4. Integration Instructions for `src/phase_orchestrator.py`

Add this import at the top of `src/phase_orchestrator.py`:

```python
from .enhanced_e2e_validator import EnhancedE2EValidator
```

Replace the existing E2E validation logic (around line 400-450) with:

```python
elif phase.name == "e2e":
    # Enhanced E2E validation with user journey testing
    validator = EnhancedE2EValidator(Path.cwd())
    success, detailed_results = validator.validate_all()
    
    if success:
        self.logger.info("Enhanced E2E validation passed")
        phase.status = "completed"
    else:
        error_msg = "Enhanced E2E validation failed:\n"
        if not detailed_results["basic_requirements"]["success"]:
            error_msg += f"Basic requirements: {detailed_results['basic_requirements']['details']}\n"
        if not detailed_results["user_journeys"]["success"]:
            failed_journeys = [k for k, v in detailed_results['user_journeys']['details'].items() if not v]
            error_msg += f"Failed user journeys: {failed_journeys}\n"
        if not detailed_results["integration_consistency"]["success"]:
            issues = detailed_results['integration_consistency']['details'].get('issues', [])
            error_msg += f"Integration issues: {[issue['issue'] for issue in issues]}\n"
        
        phase.status = "failed"
        phase.error = error_msg
        self.logger.error(error_msg)
```

#### 5. Implementation Checklist

To implement these enhancements:

1. **Create the three new validator files** in `src/` directory
2. **Update `src/phase_orchestrator.py`** with the new E2E validation logic
3. **Test the implementation** by running a project through the E2E phase
4. **Verify** that user journeys are tested and integration inconsistencies are caught

This implementation will catch integration failures like the fetch→analyze bug during the E2E phase rather than leaving them for users to discover.