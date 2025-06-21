# Todo List REST API - Project Instructions

This is a simple REST API project for managing todo lists. Follow standard REST conventions and clean architecture principles.

## Project Structure
```
test_v4_todo/
├── src/
│   ├── api/          # FastAPI routes
│   ├── models/       # Data models
│   ├── services/     # Business logic
│   └── auth/         # Authentication
├── tests/
│   ├── unit/         # Unit tests
│   └── integration/  # Integration tests
├── main.py           # Application entry point
└── requirements.txt  # Dependencies
```

## Key Requirements
- Use FastAPI for the web framework
- Implement proper error handling
- Add comprehensive tests
- Follow REST best practices
- Use type hints throughout

## Testing Commands
- Lint: `flake8 --select=F`
- Type check: `mypy --strict`
- Unit tests: `pytest tests/unit`
- Integration tests: `pytest tests/integration`

## Anti-Cheating Requirements
- All tests must actually run and pass
- E2E evidence must show real command execution
- No placeholder or fake implementations

## Milestones

### Milestone 1: Core Data Infrastructure
Build a REST API with basic CRUD operations for todo items.
- **Deliverable**: Working FastAPI server with endpoints for create, read, update, delete todos
- **Success Criteria**: 
  - `python main.py` starts the server
  - All CRUD endpoints return proper JSON responses
  - All tests pass with `pytest`

### Milestone 2: User Authentication  
Add token-based authentication to the working API from Milestone 1.
- **Deliverable**: JWT authentication integrated into existing todo API
- **Success Criteria**:
  - User registration endpoint creates new users
  - Login endpoint returns valid JWT tokens
  - Todo endpoints from Milestone 1 now require authentication
  - `python main.py` runs the enhanced server

### Milestone 3: Advanced Features
Enhance the authenticated API from Milestone 2 with advanced features.
- **Deliverable**: Enhanced API with due dates, priorities, and search
- **Success Criteria**:
  - Can filter todos by priority and due date
  - Search endpoint finds todos by text
  - Bulk operations work correctly
  - `python main.py` runs with all features

### Milestone 4: Production Readiness
Finalize the full-featured API from Milestone 3 for production.
- **Deliverable**: Production-ready API with logging and monitoring
- **Success Criteria**:
  - Structured logging implemented
  - Health check endpoint available
  - Docker deployment ready
  - `python main.py` runs production server