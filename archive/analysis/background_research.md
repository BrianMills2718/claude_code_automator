# Claude Code Control Methods - Background Research

## Overview
This document captures our understanding of different methods to control and automate Claude Code, based on examination of the infinite-agentic-loop project and Claude Code documentation.

## Control Methods

### 1. CLI Invocation (Process-Level Isolation)
**Description**: Using `claude` command with various flags to run isolated sessions.

**Key Features**:
- Complete context isolation between invocations
- Headless mode with `-p` or `--print` flag
- JSON output for programmatic parsing
- Session management with `--continue` and `--resume`

**Example**:
```bash
# Single isolated command
claude -p "Write a function" --output-format json

# With pre-allowed tools to avoid prompts
claude -p "Edit the file" --allowedTools "Edit,Write,Read"

# Skip all permissions (dangerous but fully automated)
claude --dangerously-skip-permissions -p "Do the task"
```

**Pros**:
- Complete isolation between phases
- Easy to track costs per phase
- Can run from any programming language via subprocess
- Clear session boundaries

**Cons**:
- Overhead of starting new process for each phase
- No shared context between phases (also a pro for isolation)

### 2. Custom Slash Commands
**Description**: Markdown files in `.claude/commands/` that define reusable prompts.

**Key Features**:
- Accessible via `/project:commandname` in Claude
- Can use `$ARGUMENTS` placeholder for parameters
- Commands can be project-specific or global (`~/.claude/commands/`)
- Can include complex multi-step instructions

**Example Structure**:
```
.claude/
  commands/
    research.md      # /project:research command
    implement.md     # /project:implement command
    test.md         # /project:test command
```

**Pros**:
- Reusable across projects
- Can encode complex workflows
- Easy to version control
- Can chain commands sequentially

**Cons**:
- Still runs within same session (shared context)
- Manual invocation required (unless automated via CLI)

### 3. Task Tool (Sub-Agents)
**Description**: Claude's built-in Task tool that creates concurrent "agents" within a session.

**Key Features**:
- Creates parallel workers within same Claude session
- Each task gets its own focused context
- Can coordinate multiple tasks
- Results reported back to main orchestrator

**Example Usage** (from infinite-agentic-loop):
```markdown
Deploy multiple Sub Agents to generate iterations in parallel:
- Each Sub Agent receives specific context and task
- Agents work concurrently on different parts
- Main orchestrator coordinates results
```

**Pros**:
- Enables parallel work patterns
- Sophisticated coordination possible
- All within single session

**Cons**:
- Not true OS-level parallelism
- Shared session context (not isolated)
- Complex to debug and manage

### 4. Sequential Custom Commands
**Description**: Using custom commands one after another in the same session.

**Pattern**:
```
/project:research args
/project:implement args  
/project:test args
/project:commit args
```

**Pros**:
- Maintains context between phases
- Simple linear flow
- Easy to understand

**Cons**:
- Context accumulation can hit limits
- No isolation between phases
- Manual intervention required

### 5. Hybrid Approach
**Description**: Combining methods for optimal results.

**Example Patterns**:
1. **CLI + Custom Commands**: Use CLI to start isolated sessions, each running specific custom commands
2. **Task Tool + Sequential**: Use Task tool for parallel work within phases, sequential phases
3. **CLI Automation**: Python script orchestrating multiple CLI invocations

## Recommendations for cc_automator

Based on this research, for cc_automator's goal of isolated phases with no context mixing:

1. **Primary Method**: CLI invocation with `-p` flag
   - Each phase is a separate `claude -p "prompt" --output-format json` call
   - Complete isolation between phases
   - Easy to track metrics per phase

2. **Enhancement**: Custom commands for complex phase logic
   - Create `.claude/commands/` for each phase type
   - Can still invoke via CLI: `claude -p "/project:research args"`
   - Encapsulates phase-specific logic

3. **Execution Pattern**:
   ```python
   # Python orchestrator
   for phase in phases:
       result = subprocess.run([
           "claude", "-p", phase.prompt,
           "--output-format", "json",
           "--allowedTools", phase.allowed_tools
       ])
       # Process result, track metrics
   ```

## Key Insights

1. **Task Tool Clarification**: The "Sub Agents" in infinite-agentic-loop aren't separate processes but concurrent tasks managed by Claude within one session.

2. **Isolation vs Efficiency**: There's a tradeoff between complete isolation (CLI invocations) and efficiency (shared session).

3. **Context Management**: Each method has different implications for context accumulation and limits.

4. **Automation Capability**: CLI mode with `--print` flag is the most automation-friendly approach.

5. **Tool Permissions**: Pre-configuring allowed tools via `--allowedTools` or settings.json is crucial for automation.

## Testing Findings

From our test (`test_isolated_phases.py`):
- Confirmed CLI invocations provide complete isolation (different session IDs)
- JSON output includes cost tracking and session metadata
- Sequential phases can read outputs from previous phases
- Each phase starts fresh without prior context

## References
- Claude Code documentation: `/home/brian/autocoder2_cc/claude_code_documentation.md`
- Infinite agentic loop: `https://github.com/disler/infinite-agentic-loop`
- Test implementation: `/home/brian/autocoder2_cc/test_isolated_phases.py`