# CC_AUTOMATOR3 - Autonomous Code Generation System

An autonomous code generation system that uses isolated Claude Code CLI invocations to build complete software projects without human intervention.

## Overview

CC_AUTOMATOR3 orchestrates Claude Code through a 9-phase development process for each milestone:
1. **Research** - Analyze requirements and explore solutions
2. **Planning** - Create detailed implementation plans
3. **Implementation** - Build the solution
4. **Linting** - Fix code style issues (flake8 F-errors)
5. **Type Checking** - Fix type errors (mypy --strict)
6. **Unit Testing** - Ensure unit tests pass
7. **Integration Testing** - Verify component interactions
8. **E2E Testing** - Validate main.py runs successfully
9. **Commit** - Create git commit with changes

## Key Features

- **Isolated Phase Execution**: Each phase runs in a separate Claude Code instance
- **Completion Markers**: Bypasses 10-minute timeout limits using file-based completion tracking
- **Template-Based Configuration**: Projects defined using CLAUDE.md templates
- **Progress Tracking**: Real-time monitoring with cost and duration tracking
- **Self-Healing Patterns**: Built-in best practices for robust code generation
- **Think Modes**: Strategic use of Claude's thinking capabilities per phase

## Requirements

- Python 3.8+
- Claude Code CLI (authenticated with Claude Max subscription)
- Git repository
- Standard Python development tools (flake8, mypy, pytest)

## Quick Start

1. Clone the repository:
```bash
git clone https://github.com/BrianMills2718/claude_code_automator.git
cd claude_code_automator
```

2. Create a new project:
```bash
python setup.py --project my_project
# Follow the interactive prompts to configure your project
```

3. Run the automator:
```bash
cd my_project
python ../run.py
```

## Project Structure

```
cc_automator3/
├── run.py                      # Main orchestrator
├── phase_orchestrator.py       # Manages isolated phase execution
├── phase_prompt_generator.py   # Generates phase-specific prompts
├── milestone_decomposer.py     # Parses milestones from CLAUDE.md
├── preflight_validator.py      # Pre-execution environment checks
├── progress_tracker.py         # Tracks execution progress
├── session_manager.py          # Manages Claude session IDs
├── setup.py                    # Interactive project setup
└── templates/
    ├── CLAUDE_TEMPLATE.md      # Project configuration template
    └── CLAUDE_TEMPLATE_QA.md   # Q&A setup guide
```

## How It Works

1. **Project Setup**: Define your project using the CLAUDE.md template with milestones
2. **Milestone Decomposition**: Each milestone is broken into 9 phases
3. **Phase Execution**: Each phase runs with:
   - Specific prompt and tool restrictions
   - Completion marker requirements
   - Think mode (when appropriate)
   - Evidence validation
4. **Progress Monitoring**: Real-time tracking of:
   - Phase completion status
   - Execution time and costs
   - Session IDs for debugging

## Completion Markers

To bypass subprocess timeout limitations, each phase is instructed to create a completion marker file when done. The orchestrator polls for this file instead of waiting for process exit, allowing phases to run for hours if needed.

## Configuration

Projects are configured through CLAUDE.md files with:
- Project overview and requirements
- Milestone definitions (vertical slices)
- Success criteria per milestone
- Development standards
- Self-healing patterns

## Example Project

See `test_calculator_project/` for a complete example of a configured project.

## Advanced Features

- **Think Modes**: Research uses "think harder", planning uses "think hard"
- **Tool Restrictions**: Each phase has specific allowed tools
- **Evidence Requirements**: Phases must produce verifiable outputs
- **Checkpoint/Resume**: Automatic progress saving and recovery

## Troubleshooting

- Ensure Claude Code CLI is authenticated: `claude --version`
- Check preflight validation output for environment issues
- Review phase completion markers in `.cc_automator/`
- Check session costs: Free for Claude Max users (display only)

## License

MIT License - See LICENSE file for details