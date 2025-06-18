# GraphRAG System

## Project Overview
**User Intent:** graphrag system for analyzing research papers
**Project Type:** Graph-Based Retrieval Augmented Generation System

## Technical Requirements
- Python 3.9+
- Proper async/await patterns
- Comprehensive error handling
- Full test coverage

## Success Criteria
- Working main.py with CLI interface
- All functionality implemented and tested
- Clean code passing linting and type checking
- Complete documentation

## Milestones

### Milestone 1: Core Graph Construction
**Produces a working main.py that can:**
- Document processing and knowledge graph building
- Pass all tests for this milestone
- Demonstrate progress toward final goal

## Development Standards

### Code Quality
- All code must pass flake8 linting (max-line-length=100)
- All code must pass mypy strict type checking
- All tests must pass with pytest
- main.py must run successfully as the entry point

### Testing Requirements
- Unit tests: Test individual components in isolation
- Integration tests: Test component interactions
- E2E tests: Test complete workflows via main.py

### Architecture Patterns
- Use dependency injection for testability
- Implement proper async patterns for I/O operations
- Use dataclasses/Pydantic for data models
- Separate concerns between components

## External Dependencies
### API Keys Required:
- OPENAI_GPT4_API_KEY: OpenAI GPT-4 for document analysis

## Special Considerations
- Handle errors gracefully with informative messages
- Use async patterns for I/O-bound operations
- Consider memory usage and performance
- Implement proper logging and monitoring