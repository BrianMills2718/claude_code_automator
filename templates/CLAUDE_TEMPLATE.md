# {{PROJECT_NAME}}

## Project Overview
{{PROJECT_DESCRIPTION}}

## Technical Requirements
{{TECHNICAL_REQUIREMENTS}}

## Success Criteria
{{SUCCESS_CRITERIA}}

## Milestones

{{MILESTONES}}

## Development Standards

### Code Quality
- All code must pass flake8 linting (max-line-length=100)
- All code must pass mypy strict type checking
- All tests must pass with pytest
- main.py must run successfully as the entry point

### Testing Requirements
- Unit tests: Mocking allowed for external dependencies
- Integration tests: Minimal mocking, test component interactions
- E2E tests: NO mocking, must use real implementations via main.py

### Self-Healing Patterns
When implementing code, always follow these patterns for robustness:

1. **Use relative imports instead of absolute**
   ```python
   # Good: from ..utils import helper
   # Bad: from src.utils import helper
   ```

2. **Test behavior, not implementation**
   ```python
   # Good: assert calculator.add(2, 3) == 5
   # Bad: assert calculator._internal_state == 5
   ```

3. **Handle missing dependencies gracefully**
   ```python
   try:
       import optional_library
   except ImportError:
       optional_library = None
   ```

4. **Use pathlib for file operations**
   ```python
   # Good: Path(__file__).parent / "data"
   # Bad: "/absolute/path/to/data"
   ```

5. **Write descriptive error messages**
   ```python
   # Good: raise ValueError(f"Expected positive number, got {value}")
   # Bad: raise ValueError("Invalid input")
   ```

## Project Structure
```
{{PROJECT_NAME}}/
├── main.py              # Entry point (required)
├── requirements.txt     # Python dependencies
├── src/                 # Source code
├── tests/
│   ├── unit/           # Unit tests
│   ├── integration/    # Integration tests
│   └── e2e/            # End-to-end tests
└── README.md           # Project documentation
```

## Environment Variables
{{ENV_VARIABLES}}

## External Dependencies
{{EXTERNAL_DEPENDENCIES}}

## Special Considerations
{{SPECIAL_CONSIDERATIONS}}