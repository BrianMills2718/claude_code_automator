# CC_AUTOMATOR3 Usage Guide

## Installation Options

### Option 1: System-Wide Installation (Recommended)

1. Clone to a permanent location:
```bash
cd ~
git clone https://github.com/BrianMills2718/claude_code_automator.git
```

2. Add alias to your shell config (~/.bashrc or ~/.zshrc):
```bash
echo 'alias cc-automator="python ~/claude_code_automator/setup.py"' >> ~/.bashrc
source ~/.bashrc
```

3. Use from any directory:
```bash
cd /path/to/my/new/project
cc-automator --project .
```

### Option 2: Per-Project Copy

1. Copy the automator to your project:
```bash
cd /path/to/my/project
git clone https://github.com/BrianMills2718/claude_code_automator.git .cc_automator_tools
```

2. Run setup:
```bash
python .cc_automator_tools/setup.py --project .
```

## Usage Workflow

### Step 1: Setup New Project

```bash
# Navigate to your empty project directory
cd ~/projects/my_new_app

# Run setup (using system-wide install)
cc-automator --project .

# Or using per-project copy
python .cc_automator_tools/setup.py --project .
```

This will:
- Create CLAUDE.md from template
- Run interactive Q&A with Claude
- Set up project structure
- Initialize git repository

### Step 2: Define Milestones

Edit the generated CLAUDE.md to define your milestones:

```markdown
### Milestone 1: Core authentication system
- User registration and login
- JWT token management
- Password hashing

### Milestone 2: API endpoints
- RESTful API design
- CRUD operations
- Input validation
```

### Step 3: Run Automator

```bash
# Using system-wide install
python ~/claude_code_automator/run.py

# Or using per-project copy
python .cc_automator_tools/run.py
```

### Step 4: Monitor Progress

- Check `.cc_automator/progress.json` for current status
- Review `.cc_automator/milestones/` for phase outputs
- Watch console for real-time updates

## Project Structure After Setup

```
my_project/
├── CLAUDE.md              # Your project configuration
├── main.py               # Entry point (created by automator)
├── requirements.txt      # Dependencies
├── src/                  # Source code
├── tests/               # Test suites
│   ├── unit/
│   ├── integration/
│   └── e2e/
└── .cc_automator/       # Automator working directory
    ├── progress.json    # Current progress
    ├── milestones/      # Phase outputs
    └── sessions.json    # Claude session tracking
```

## Best Practices

1. **Start Small**: Begin with 2-3 focused milestones
2. **Vertical Slices**: Each milestone should produce a working main.py
3. **Clear Success Criteria**: Be specific about what each milestone delivers
4. **Git Commits**: The automator will commit after each milestone

## Common Commands

```bash
# Check current progress
cat .cc_automator/progress.json | jq .

# View specific milestone research
cat .cc_automator/milestones/milestone_1/research.md

# Resume after interruption (automatic)
python ~/claude_code_automator/run.py

# Clean up for fresh start
rm -rf .cc_automator/ src/ tests/ main.py
```

## Tips

- The automator handles interruptions gracefully
- Each phase has a 10-minute timeout (bypassed with completion markers)
- Total execution time depends on project complexity
- Monitor costs in progress.json (display only for Claude Max)

## Troubleshooting

If the automator seems stuck:
1. Check for completion markers: `ls .cc_automator/phase_*`
2. Review the latest phase output
3. Ensure Claude Code is authenticated: `claude --version`
4. Check disk space and permissions

## Example Projects

See `test_calculator_project/` in the automator directory for a complete example.