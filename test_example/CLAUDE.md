# Python Calculator

## Project Overview
A command-line calculator with basic arithmetic operations

## Technical Requirements
- Python 3.8+
- No external dependencies for core functionality

## Success Criteria
- All arithmetic operations work correctly
- Proper error handling
- User-friendly interface

## Milestones

### Milestone 1: Basic arithmetic operations (add, subtract, multiply, divide)
- Produces a working main.py with this functionality
- All tests pass

### Milestone 2: Advanced operations (power, sqrt, modulo)
- Produces a working main.py with this functionality
- All tests pass

### Milestone 3: Expression parser for complex calculations
- Produces a working main.py with this functionality
- All tests pass



## Additional Documentation
See @README.md for general project information.

## CC_AUTOMATOR3 Instructions
- Each phase will receive its own CLAUDE.md with specific instructions
- Use subagents when prompted for verification and exploration
- Save outputs to specified milestone directories
- Follow the phase-specific guidance carefully

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
Python Calculator/
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
None required

## External Dependencies
None

## Special Considerations
- Focus on code clarity and good error messages