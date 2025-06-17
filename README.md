# 🤖 CC_AUTOMATOR4 - Autonomous Code Generation

**Intelligent multi-milestone project automation using Claude Code with advanced error recovery and validation.**

## ✨ What It Does

CC_AUTOMATOR4 orchestrates multiple Claude Code instances through a sophisticated 9-phase pipeline to build complete, production-ready software projects autonomously. Unlike simple AI coding tools, it enforces evidence-based validation and prevents Claude from taking shortcuts or mocking implementations.

### 🎯 Key Features

- **Multi-Milestone Projects**: Automatically breaks complex projects into achievable milestones
- **9-Phase Pipeline**: Research → Planning → Implementation → Lint → Typecheck → Test → Integration → E2E → Commit
- **Evidence-Based Validation**: Requires concrete proof of success (passing tests, clean code, working executables)
- **Advanced Error Recovery**: CLI fallback system handles SDK TaskGroup bugs automatically  
- **MCP Integration**: Uses Model Context Protocol for enhanced tool access
- **Cost Tracking**: Per-phase token usage monitoring
- **Resume Support**: Checkpoint system for long-running projects

## 🚀 Quick Start

### Prerequisites

- Python 3.8+
- Claude Code installed and authenticated (`claude auth login`)
- Git repository initialized

### Installation

```bash
git clone https://github.com/BrianMills2718/claude_code_automator.git
cd claude_code_automator
```

### Basic Usage

1. **Create your project directory:**
```bash
mkdir my_project && cd my_project
```

2. **Create CLAUDE.md with your project specification:**
```markdown
# My Project

## Project Overview
Brief description of what you're building

## Milestones

### Milestone 1: Core functionality
- Produces a working main.py with basic features
- Unit tests for all functions
- All tests pass

### Milestone 2: Advanced features  
- Produces a working main.py with extended functionality
- Integration tests
- All tests pass
```

3. **Run the automator:**
```bash
python /path/to/cc_automator4/cli.py --project . --verbose
```

## 🏗️ How It Works

### The Problem CC_AUTOMATOR4 Solves

When you ask Claude Code to build something complex, it often:
- Claims success without actually completing the task
- Implements partial solutions that don't meet specifications  
- Creates code that doesn't run or pass tests
- Loses context between different parts of the implementation

### The Intelligent Solution

CC_AUTOMATOR4 prevents these issues by:

1. **Milestone Decomposition**: Breaking complex projects into achievable chunks
2. **Enforced Validation**: Each phase must produce concrete evidence (files, passing tests)
3. **Context Preservation**: Each phase builds on previous phase outputs
4. **Error Recovery**: Automatic CLI fallback when SDK issues occur
5. **No Cheating**: Validation catches false success claims

### Nine-Phase Pipeline

```
Research → Planning → Implementation → Lint → Typecheck → Test → Integration → E2E → Commit
```

Each phase has specific requirements and validation:
- **Research**: Must create research.md with >100 characters
- **Planning**: Must create plan.md with implementation strategy  
- **Implementation**: Must create working main.py and/or src/ files
- **Lint**: Must pass flake8 with zero F-errors
- **Typecheck**: Must pass mypy --strict
- **Test**: Must pass pytest tests/unit
- **Integration**: Must pass pytest tests/integration
- **E2E**: Must demonstrate main.py runs successfully
- **Commit**: Must create actual git commit

## 📊 Example Results

Our 3-milestone advanced calculator test:

```
✓ Milestone 1: Basic arithmetic (8m 32s, $2.41) - COMPLETE
✓ Milestone 2: Advanced operations (4m 28s, $0.26) - IN PROGRESS  
○ Milestone 3: Expression parser - PENDING

Total: Working calculator with proper CLI, tests, and error handling
```

## 🔧 Advanced Usage

### Environment Variables

```bash
export USE_SUBPHASES=false      # More stable (recommended)
export DISABLE_MCP=false        # Enable MCP servers
export USE_CLAUDE_SDK=true      # Use SDK by default
```

### Command Options

```bash
# Resume from last checkpoint
python cli.py --project . --resume

# Run specific milestone only  
python cli.py --project . --milestone 2

# Verbose output with full logging
python cli.py --project . --verbose
```

### MCP Integration

Install MCP servers for enhanced functionality:

```bash
./install_mcp_servers.sh
```

Supported MCP servers:
- **Filesystem**: Enhanced file operations
- **Brave Search**: Web search alternative to WebSearch
- **Context7**: Library documentation access

## 🛠️ Error Recovery

CC_AUTOMATOR4 includes sophisticated error recovery for common SDK issues:

### TaskGroup Bug Handling
- **Automatic Detection**: Recognizes SDK TaskGroup async errors
- **CLI Fallback**: Switches to direct `claude` CLI execution 
- **Success Recovery**: Continues execution when work was completed despite errors
- **Cost Efficiency**: Prevents infinite retry loops

### Smart Validation
- **Output Detection**: Checks for created files even if SDK crashes
- **Flexible Naming**: Accepts variations like `research_CLAUDE.md` → `research.md`
- **Evidence-Based**: Validates actual functionality, not just claims

## 📁 Project Structure

```
my_project/
├── main.py              # Generated entry point
├── src/                 # Generated source code  
├── tests/               # Generated test suites
│   ├── unit/           # Unit tests
│   ├── integration/    # Integration tests  
│   └── e2e/            # End-to-end tests
├── requirements.txt     # Generated dependencies
├── CLAUDE.md           # Your project specification
└── .cc_automator/      # Execution artifacts
    ├── milestones/     # Per-milestone outputs
    ├── logs/           # Detailed execution logs
    └── checkpoints/    # Resume state
```

## 🎛️ Configuration

### CLAUDE.md Template

```markdown
# Project Name

## Project Overview
What you're building and why

## Technical Requirements  
- Language/framework requirements
- Dependencies and constraints
- Performance requirements

## Success Criteria
- Working software deliverables
- Quality standards
- Testing requirements

## Milestones

### Milestone 1: [Feature Name]
- Produces a working main.py with [specific functionality]
- [Concrete deliverable 1]
- [Concrete deliverable 2]
- All tests pass

### Milestone 2: [Next Feature]
- Produces a working main.py with [extended functionality] 
- [Additional deliverables]
- All tests pass

## Development Standards
- Code must pass flake8 linting
- Code must pass mypy strict type checking
- All tests must pass with pytest
- main.py must run successfully
```

## 🔍 Monitoring & Debugging

### Real-Time Monitoring
```bash
# Watch logs
tail -f .cc_automator/logs/*.log

# Check progress
cat .cc_automator/final_report.md

# View costs
grep "Cost:" .cc_automator/logs/*.log
```

### Common Issues

**TaskGroup Errors**: Automatically handled by CLI fallback
**WebSearch Timeouts**: Geographic restrictions (US-only), use MCP alternatives
**Validation Failures**: Check .cc_automator/logs/ for detailed error information

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Test your changes with the example projects
4. Submit a pull request

## 📄 License

MIT License - see LICENSE file for details

## 🔗 Links

- [Claude Code Documentation](https://docs.anthropic.com/en/docs/claude-code)
- [Model Context Protocol](https://github.com/modelcontextprotocol)
- [Issue Tracker](https://github.com/BrianMills2718/claude_code_automator/issues)

---

**Built with ❤️ by the Claude Code community**