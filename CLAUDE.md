# CC_AUTOMATOR4 Implementation Guide

**FOR CLAUDE CODE AGENTS**: This document contains everything needed to implement robust cc_automator4 features. Follow these patterns and principles exactly.

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

### Evidence-Based Validation Philosophy

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

### Required Output Files by Phase

1. **research**: `milestone_N/research.md` (>100 chars)
2. **planning**: `milestone_N/plan.md` (>50 chars)  
3. **implement**: `main.py` OR `src/*.py` files
4. **lint**: Zero F-errors from `flake8 --select=F`
5. **typecheck**: Clean output from `mypy --strict`
6. **test**: `pytest tests/unit` passes
7. **integration**: `pytest tests/integration` passes
8. **e2e**: `milestone_N/e2e_evidence.log` AND `python main.py` succeeds
9. **commit**: Git commit created

## Critical Implementation Patterns

### 1. Interactive Program Detection (E2E Phase)

**PROBLEM**: Interactive programs hang during e2e validation without input.

**GENERALIST SOLUTION**:
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

def test_interactive_program(file_path: Path, working_dir: Path) -> bool:
    """Test interactive program with multiple input patterns."""
    if not detect_interactive_program(file_path):
        # Non-interactive, run directly
        result = subprocess.run(["python", file_path.name], 
                              cwd=working_dir, timeout=10)
        return result.returncode == 0
    
    # Try different exit patterns
    for test_input in get_common_exit_inputs():
        try:
            result = subprocess.run(
                ["python", file_path.name],
                input=test_input,
                capture_output=True,
                text=True,
                cwd=working_dir,
                timeout=10
            )
            if result.returncode == 0:
                return True
        except subprocess.TimeoutExpired:
            continue  # Try next pattern
    
    return False  # No exit pattern worked
```

**DO NOT** hardcode program-specific input sequences. Always use generalist patterns.

### 2. SDK Bug Handling

**KNOWN ISSUE**: TaskGroup errors with "error_during_execution" and "is_error": false

**SOLUTION**: Check if work was actually completed despite SDK errors:
```python
if "TaskGroup" in str(error) and phase.status == PhaseStatus.RUNNING:
    # Check if outputs exist despite SDK crash
    if self._validate_phase_outputs(phase):
        phase.status = PhaseStatus.COMPLETED
        return success
    else:
        # Fall back to CLI execution
        return self._execute_cli_fallback(phase)
```

### 3. Model Selection for Cost Optimization

**MECHANICAL PHASES** (use Sonnet - 90% cost savings):
- lint, typecheck

**COMPLEX PHASES** (use Opus - better reasoning):  
- research, planning, implement, test, integration, e2e, validate, commit

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

### 4. File Parallel Execution (Lint/Typecheck)

**PRINCIPLE**: Process multiple files concurrently for 11x speed improvement.

```python
# ✅ CORRECT: True parallel execution
with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
    future_to_file = {
        executor.submit(self.fix_file_errors, file_path, errors): file_path
        for file_path, errors in errors_by_file.items()
    }
    
    for future in as_completed(future_to_file):
        result = future.result()

# ❌ WRONG: Sequential processing
for file_path, errors in errors_by_file.items():
    self.fix_file_errors(file_path, errors)
```

### 5. Iteration Until Success

**PRINCIPLE**: Don't give up after one attempt. Iterate until clean or max attempts.

```python
max_iterations = 5
iteration = 0

while iteration < max_iterations:
    iteration += 1
    
    # Run validation
    errors = self.find_errors()
    if not errors:
        return success  # Clean!
    
    # Fix errors in parallel
    self.fix_errors_parallel(errors)
    
    if iteration == max_iterations:
        return failure  # Give up
```

## Testing Strategy

### Unit Tests
- Test individual functions/classes
- Mock external dependencies 
- Focus on logic correctness

### Integration Tests  
- Test component interactions
- Minimal mocking
- Test file I/O, subprocess calls

### E2E Tests
- NO mocking whatsoever
- Test via main.py entry point
- Must work like real user interaction

## Error Recovery Patterns

### 1. Graceful Degradation
```python
try:
    result = advanced_operation()
except AdvancedError:
    result = fallback_operation()  # Simpler approach
```

### 2. Evidence Collection
```python
def attempt_phase(phase):
    try:
        execute_phase(phase)
    except Exception as e:
        # Always check if work was actually done
        if outputs_exist(phase):
            return success_with_warning(e)
        else:
            return failure(e)
```

### 3. Intelligent Validation Feedback & Retry
```python
def validate_with_feedback(phase):
    if basic_validation_passes(phase):
        return {"success": True}
    
    # Generate specific feedback about what failed
    feedback = generate_specific_feedback(phase)
    
    # Attempt retry with targeted feedback
    retry_success = retry_phase_with_feedback(phase, feedback)
    
    return {"success": retry_success, "feedback": feedback}

def generate_specific_feedback(phase):
    if phase.name == "e2e":
        if missing_evidence_log():
            return "Missing required evidence log file. You must create: milestone_N/e2e_evidence.log"
        elif main_py_execution_failed():
            return "Evidence log exists but main.py execution test failed"
    # ... specific feedback for each phase type
```

### 4. The Feedback Loop That Was Missing
The original system had a critical gap:
1. ✅ Detect validation failure
2. ❌ **NO specific feedback about what was wrong**
3. ❌ **NO retry with targeted guidance**  
4. ❌ **NO learning from the failure**

The enhanced system now:
1. ✅ Detect validation failure
2. ✅ **Generate specific feedback about missing files/outputs**
3. ✅ **Retry with targeted prompt explaining exactly what to fix**
4. ✅ **Re-validate after retry to confirm fix**

## Prompt Engineering Principles

### 1. Be Specific About Outputs
```python
# ✅ GOOD: Specific file requirements
prompt = f"""
Create research.md in {milestone_dir}/research.md with:
- Current codebase analysis (what exists)
- Requirements for {milestone.description}  
- Implementation approach
- Testing strategy

File must be >100 characters.
"""

# ❌ BAD: Vague requirements  
prompt = "Research the requirements and create documentation."
```

### 2. Provide Context Flow
```python
prompt = f"""
PREVIOUS PHASES:
Research: {research_summary}
Planning: {plan_summary}

YOUR TASK: Implement {milestone.description}
Focus on the plan above and research findings.
"""
```

### 3. Include Validation Criteria
```python
prompt = f"""
SUCCESS CRITERIA:
- All flake8 F-errors fixed: `flake8 --select=F` returns 0
- Files must be syntactically valid Python
- Don't break existing functionality

CURRENT ERRORS:
{error_list}
"""
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

### ❌ Complex Validation Logic
```python
# WRONG: Parsing complex outputs
def validate_tests():
    output = run_tests()
    parsed = parse_pytest_output(output)  # Complex!
    return analyze_test_results(parsed)   # Fragile!

# RIGHT: Simple validation
def validate_tests():
    result = subprocess.run(["pytest", "tests/unit"])
    return result.returncode == 0  # Simple!
```

### ❌ Disabling Features Due to Bugs
```python
# WRONG: Remove functionality
def execute_phase(phase):
    # Disable WebSearch due to SDK bug
    phase.allowed_tools.remove("WebSearch")

# RIGHT: Work around bugs  
def execute_phase(phase):
    try:
        return execute_with_websearch(phase)
    except SDKBug:
        return execute_without_websearch(phase)
```

## Key Success Metrics

1. **Validation Independence**: Each phase validated by external tools
2. **Evidence Collection**: Concrete proof files created  
3. **Cost Efficiency**: Sonnet for mechanical, Opus for complex
4. **Speed Optimization**: Parallel execution where beneficial
5. **Error Recovery**: Continue despite SDK bugs
6. **Generalist Design**: Works across different project types

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

**Remember**: The goal is a robust, generalist system that prevents Claude from taking shortcuts while optimizing for speed and cost.