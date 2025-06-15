# Context Management Design

## Overview

Each phase receives EXACTLY the context it needs - no more, no less. This improves focus, reduces confusion, and maintains robustness.

## Phase Context Requirements

### Research Phase
- **Gets**: CLAUDE.md, README.md, requirements.txt
- **Why**: Needs project specs, not implementation details
- **Result**: Focused analysis without distraction

### Planning Phase  
- **Gets**: Research SUMMARY + CLAUDE.md
- **Why**: Needs conclusions, not detailed analysis
- **Result**: Clear plan based on key findings

### Implementation Phase
- **Gets**: Full planning output
- **Why**: Needs complete implementation details
- **Result**: Accurate implementation following the plan

### Lint Phase
- **Gets**: Python files + lint guidelines
- **Why**: Only needs code to check, not why it was written
- **Result**: Fast, focused F-error fixes

### Typecheck Phase
- **Gets**: Python files + type guidelines  
- **Why**: Only needs code structure, not business logic
- **Result**: Efficient type annotation fixes

### Test Phase
- **Gets**: Source + unit test files
- **Why**: Needs implementation to test, not how it was developed
- **Result**: Focused test execution

### Integration Phase
- **Gets**: Source + integration test files
- **Why**: Needs component interfaces, not unit test details
- **Result**: Proper integration testing

### E2E Phase
- **Gets**: main.py + README + e2e tests
- **Why**: Needs entry points and usage, not internals
- **Result**: Real user workflow validation

### Commit Phase
- **Gets**: Summary of all phases
- **Why**: Needs what changed, not how it was changed
- **Result**: Clean, informative commit message

## Benefits

1. **Improved Focus**: Each phase sees only relevant information
2. **Faster Execution**: Less context to process = quicker responses
3. **Better Quality**: No confusion from irrelevant details
4. **Maintains Robustness**: Still provides all necessary information

## Implementation

The `ContextManager` class:
- Extracts summaries from verbose outputs
- Loads only specified files
- Adds phase-specific guidelines
- Saves outputs for cross-milestone reference

## Example Impact

Before (Lint Phase):
- 5000+ tokens of implementation details, research, planning
- Claude has to figure out what's relevant
- Slower, potentially confused

After (Lint Phase):
- ~1000 tokens of just Python files + lint rules
- Claude knows exactly what to do
- Faster, focused, accurate