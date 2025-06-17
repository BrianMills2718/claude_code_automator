# Advanced Calculator Project

## Project Overview
A comprehensive calculator application with basic operations, advanced functions, and expression parsing.

## Technical Requirements
- Python 3.8+
- Clean architecture with proper separation of concerns
- Comprehensive testing
- Type hints throughout

## Success Criteria
- All operations work correctly
- Proper error handling
- User-friendly CLI interface
- Full test coverage

## Milestones

### Milestone 1: Basic arithmetic operations (add, subtract, multiply, divide)
- Produces a working main.py with basic calculator functionality
- Calculator class with add, subtract, multiply, divide methods
- Interactive CLI menu for operation selection
- Proper error handling for division by zero
- All tests pass

### Milestone 2: Advanced operations (power, sqrt, modulo, factorial)
- Produces a working main.py with advanced calculator functions
- Extended Calculator class with power, sqrt, modulo, factorial operations
- Enhanced CLI with scientific calculator mode
- All basic and advanced operations work correctly
- All tests pass

### Milestone 3: Expression parser for complex calculations
- Produces a working main.py with full expression parsing
- Expression parser supporting "2 + 3 * 4", parentheses, operator precedence
- CLI mode for entering mathematical expressions
- Complete calculator with all features working
- All tests pass

## Development Standards

### Code Quality
- All code must pass flake8 linting (max-line-length=100)
- All code must pass mypy strict type checking
- All tests must pass with pytest
- main.py must run successfully as the entry point

### Testing Requirements
- Unit tests: Test individual functions
- Integration tests: Test component interactions
- E2E tests: Test via main.py interface

## Project Structure
```
Advanced Calculator/
├── main.py              # Entry point (required)
├── requirements.txt     # Python dependencies
├── src/
│   ├── calculator.py    # Calculator class
│   ├── parser.py        # Expression parser (milestone 3)
│   └── cli.py          # CLI interface
├── tests/
│   ├── unit/           # Unit tests
│   ├── integration/    # Integration tests
│   └── e2e/            # End-to-end tests
└── README.md           # Project documentation
```