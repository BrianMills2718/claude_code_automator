# CLI Calculator - Implementation Instructions

This is a command-line calculator application. It must be a CLI tool, NOT a web API.

## Key Requirements
- MUST be a CLI application using argparse or click
- MUST support command format: `python main.py <operation> <num1> <num2>`
- MUST show help with `python main.py --help`
- MUST NOT be a web service or API
- MUST exit cleanly after performing calculation

## Example Usage
```bash
$ python main.py add 5 3
8

$ python main.py multiply 4 7
28

$ python main.py --help
usage: main.py [-h] {add,subtract,multiply,divide} num1 num2
...
```

## Testing Commands
- Lint: `flake8 --select=F`
- Type check: `mypy --strict`
- Unit tests: `pytest tests/unit`
- Integration tests: `pytest tests/integration`

## E2E Validation Requirements
- The E2E phase MUST test actual CLI commands
- The main.py MUST accept command-line arguments
- The program MUST print results and exit

## Milestones

### Milestone 1: Basic Calculator
Build a CLI calculator with basic arithmetic operations.
- **Deliverable**: Working CLI calculator with add, subtract, multiply, divide
- **Success Criteria**:
  - `python main.py add 5 3` returns 8
  - `python main.py --help` shows usage information
  - All operations work correctly
  - Tests pass with pytest