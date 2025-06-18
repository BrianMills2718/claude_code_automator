# GraphRAG System

## Project Overview
A Graph-based Retrieval Augmented Generation (GraphRAG) system that combines knowledge graphs with language models for enhanced information retrieval and generation.

## Technical Requirements
- Python 3.9+
- FastAPI for web API
- NetworkX for graph operations
- LangChain for LLM integration
- Vector database (in-memory for simplicity)
- Proper async/await patterns

## Success Criteria
- RESTful API for document ingestion and querying
- Knowledge graph construction from documents
- Vector embeddings for semantic search
- Graph traversal for enhanced retrieval
- LLM integration for response generation
- Comprehensive error handling
- Full test coverage

## Milestones

### Milestone 1: Core Graph Infrastructure
**Produces a working main.py that can:**
- Ingest documents from text files
- Extract entities and relationships
- Build and visualize knowledge graphs
- Store/retrieve graph data
- Provide CLI commands for graph operations
- Show basic graph statistics and traversal

### Milestone 2: Vector Integration & Search
**Produces a working main.py that can:**
- Generate embeddings for document chunks
- Perform vector similarity search
- Execute hybrid retrieval (graph + vector)
- Process complex queries
- Show search results with scores
- Demonstrate improved retrieval over Milestone 1

### Milestone 3: LLM Integration & API
**Produces a working main.py that can:**
- Start FastAPI server
- Handle REST API requests
- Generate responses using LLM + retrieved context
- Serve complete GraphRAG pipeline
- Provide web interface endpoints
- Demonstrate end-to-end RAG functionality

## Development Standards

### Code Quality
- All code must pass flake8 linting (max-line-length=100)
- All code must pass mypy strict type checking
- All tests must pass with pytest
- main.py must run successfully as the entry point

### Testing Requirements
- Unit tests: Test individual components in isolation
- Integration tests: Test component interactions
- E2E tests: Test complete workflows via main.py/API

### Architecture Patterns
- Use dependency injection for testability
- Implement proper async patterns for I/O operations
- Use dataclasses/Pydantic for data models
- Separate concerns: parsing, graph ops, retrieval, generation

## Project Structure
```
GraphRAG System/
├── main.py              # Entry point (CLI + server)
├── requirements.txt     # Python dependencies
├── src/
│   ├── __init__.py
│   ├── models.py        # Data models
│   ├── graph/
│   │   ├── __init__.py
│   │   ├── builder.py   # Graph construction
│   │   └── storage.py   # Graph storage/retrieval
│   ├── retrieval/
│   │   ├── __init__.py
│   │   ├── embeddings.py # Vector operations
│   │   └── hybrid.py    # Hybrid retrieval
│   ├── llm/
│   │   ├── __init__.py
│   │   └── integration.py # LLM integration
│   └── api/
│       ├── __init__.py
│       └── server.py    # FastAPI server
├── tests/
│   ├── unit/           # Unit tests
│   ├── integration/    # Integration tests
│   └── e2e/            # End-to-end tests
└── README.md           # Project documentation
```

## External Dependencies
- fastapi: Web framework
- uvicorn: ASGI server
- networkx: Graph operations
- langchain: LLM integration
- sentence-transformers: Embeddings
- numpy: Numerical operations
- pydantic: Data validation

## Special Considerations
- Handle large documents efficiently
- Implement proper error handling for LLM API calls
- Use async patterns for I/O-bound operations
- Consider memory usage for large graphs
- Implement rate limiting for API endpoints