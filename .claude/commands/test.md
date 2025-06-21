# Unit Test Phase: {{milestone_name}}

## Implementation Summary
{{implement_output}}

## Tasks
1. Check if tests/unit directory has test files
2. If no tests exist, create comprehensive unit tests for Milestone {{milestone_number}} functionality
3. Run: `pytest tests/unit -xvs`
4. Fix any failing tests
5. Ensure good test coverage for milestone features

## What to Test
Based on the implementation, create tests for:
- All public functions/methods
- Edge cases (empty inputs, zero values, etc.)
- Error conditions (invalid inputs, exceptions)
- Return values and types

## Test Structure
```python
# tests/unit/test_[module_name].py
import pytest
from main import function_name  # or from src.module import function

def test_function_normal_case():
    assert function_name(input) == expected_output

def test_function_edge_case():
    # Test edge cases

def test_function_error_case():
    with pytest.raises(ExpectedException):
        function_name(invalid_input)
```

## Evidence Required
Show pytest output with all tests passing.