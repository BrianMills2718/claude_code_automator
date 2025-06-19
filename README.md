# 🤖 CC_AUTOMATOR4 - Intelligent Autonomous Code Generation

**V4: Now with intelligent meta-agent orchestration that adapts strategies based on project context and learns from failures.**

## ✨ What It Does

CC_AUTOMATOR4 orchestrates multiple Claude Code instances through a sophisticated 11-phase pipeline to build complete, production-ready software projects autonomously. Unlike simple AI coding tools, it enforces evidence-based validation and prevents Claude from taking shortcuts or mocking implementations.

### 🎯 Key Features

#### Core Features (V3)
- **Multi-Milestone Projects**: Automatically breaks complex projects into achievable milestones
- **11-Phase Pipeline**: Research → Planning → Implementation → Architecture → Lint → Typecheck → Test → Integration → E2E → Validate → Commit
- **Evidence-Based Validation**: Requires concrete proof of success (passing tests, clean code, working executables)
- **Advanced Error Recovery**: Intelligent step-back and retry mechanisms
- **MCP Integration**: Uses Model Context Protocol for enhanced tool access
- **Cost Tracking**: Per-phase token usage monitoring
- **Resume Support**: Checkpoint system for long-running projects

#### NEW V4 Intelligence Features
- **🧠 Meta-Agent Orchestration**: Intelligent strategy selection based on project type and complexity
- **📊 Failure Pattern Learning**: Learns from failures to avoid infinite loops and repeated errors
- **🔄 Adaptive Strategies**: Switches between pipeline, iterative, and parallel exploration approaches
- **🎯 Context-Aware Execution**: Different strategies for web apps, CLI tools, libraries, etc.
- **⚡ Multi-Strategy Exploration**: Can explore multiple approaches in parallel for ambiguous requirements
- **📈 Performance Optimization**: Learns which strategies work best for different project types

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

**V3 Mode (Default - Proven stable pipeline):**
```bash
python /path/to/cc_automator4/cli.py --project . --verbose
```

**V4 Mode (Intelligent meta-agent):**
```bash
python /path/to/cc_automator4/cli.py --project . --v4 --verbose

# With decision explanations
python /path/to/cc_automator4/cli.py --project . --v4 --explain

# With parallel strategy exploration
python /path/to/cc_automator4/cli.py --project . --v4 --v4-parallel
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

### Eleven-Phase Pipeline

```
Research → Planning → Implementation → Architecture → Lint → Typecheck → Test → Integration → E2E → Validate → Commit
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

## 🧠 V4 Intelligent Features

### How V4 Intelligence Works

V4 adds a meta-agent layer that makes intelligent decisions about how to approach your project:

1. **Context Analysis**: Analyzes your project to understand:
   - Project type (web app, CLI tool, library, ML project, etc.)
   - Complexity level and technical requirements
   - Requirement clarity and ambiguity
   - Expected test coverage and quality standards

2. **Strategy Selection**: Chooses the best approach:
   - **V3 Pipeline**: For simple, well-defined projects
   - **Iterative Refinement**: For complex projects with architecture challenges
   - **Parallel Exploration**: For projects with ambiguous requirements

3. **Failure Learning**: Learns from failures to:
   - Detect infinite loop patterns
   - Identify root causes of repeated failures
   - Generate constraints to break out of loops
   - Switch strategies when current approach isn't working

4. **Evidence Validation**: All V4 decisions are validated:
   - Meta-agent must provide evidence for strategy choices
   - Learning data must be concrete, not claimed
   - All strategies must produce V3-standard evidence

### V4 Strategy Examples

**Simple CLI Tool** → V3 Pipeline Strategy
```
Context: Low complexity, clear requirements
Strategy: Standard sequential pipeline
Result: Fast, efficient execution
```

**Complex Web App with Architecture Issues** → Iterative Refinement
```
Context: High complexity, previous architecture failures
Strategy: Focus on research/planning/architecture phases
Result: Better architecture, fewer downstream issues
```

**ML Project with Ambiguous Requirements** → Parallel Exploration
```
Context: Unclear specifications, multiple valid approaches
Strategy: Explore 3 approaches in parallel
Result: Best approach selected based on evidence
```

### V4 Command Line Options

```bash
# Basic V4 execution
python cli.py --project . --v4

# V4 with explanations of decisions
python cli.py --project . --v4 --explain

# V4 with parallel strategy exploration
python cli.py --project . --v4 --v4-parallel

# V4 without learning (useful for testing)
python cli.py --project . --v4 --no-v4-learning

# Set V4 as default mode
export V4_MODE=true
python cli.py --project .
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