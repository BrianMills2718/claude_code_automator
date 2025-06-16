# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

# CC_AUTOMATOR4: Advanced Orchestration with Simple Debugging

## Debugging Philosophy: KISS (Keep It Simple, Stupid) - For Debugging Only!

**CRITICAL CLARIFICATION**: KISS applies ONLY to debugging approach, NOT to system design. When something doesn't work, look for simple causes first (file permissions, existing files, path issues) before assuming complex architectural problems. The system itself should maintain ALL its sophisticated features.

### What This System Really Is

CC_AUTOMATOR4 is a sophisticated orchestration system with FULL functionality:
1. **Milestone Decomposition** - Breaking complex projects into achievable chunks
2. **Nine-Phase Pipeline** - Research → Planning → Implementation → Testing → Commit
3. **WebSearch Integration** - For up-to-date information in research phase
4. **Context Flow** - Each phase builds on previous phase outputs
5. **Intelligent Backtracking** - Agents can request earlier phases re-run
6. **Evidence-Based Validation** - Concrete proof of success required
7. **Cost Tracking** - Per-phase token usage monitoring
8. **Session Management** - Resume/checkpoint functionality
9. **Enhanced Error Recovery** - Retry mechanisms with context

### The Simple Debugging Mindset

When something breaks, check SIMPLE causes first:
```python
# Example: Research phase not creating research.md
# ❌ DON'T assume: "The async architecture is fundamentally broken"
# ✅ DO check: "Is the path in the prompt matching the validation path?"
# ✅ DO check: "Is WebSearch timing out due to geographic restrictions?"
# ✅ DO check: "Does the milestone directory already exist with old files?"
```

### Current Issues Are Often Simple

1. **WebSearch timeouts** - Likely geographic restriction (US-only per SDK docs), not architecture
2. **TaskGroup errors** - Probably tool timeouts, not fundamental async problems
3. **File write errors** - Just existing files that need cleanup, not complex state issues

### Root Cause of Write Errors & Fix
**THE BUG**: When milestone files exist from previous runs, Claude tries to Write to them, gets "File has not been read yet" error, and retries infinitely.

**THE FIX**: Automatically clean up milestone directories when starting fresh (not resuming).

```python
# In orchestrator.py line 269
if self.current_phase_idx == 0:  # Starting fresh
    milestone_dir = self.project_dir / ".cc_automator" / "milestones" / f"milestone_{milestone.number}"
    if milestone_dir.exists():
        shutil.rmtree(milestone_dir)
```

## High-Level Architecture (Vision)

### The Core Problem CC_AUTOMATOR4 Solves

When you ask Claude Code to build something complex, it often:
1. Claims success without actually completing the task
2. Implements partial solutions that don't meet specifications
3. Creates code that doesn't run or pass tests
4. Loses context between different parts of the implementation

### The Intelligent Solution

CC_AUTOMATOR4 orchestrates multiple Claude Code instances with:

1. **Milestone Decomposition**: Breaking complex projects into achievable chunks
   - "Build FastAPI app with auth" → Basic CRUD → Add Auth → Add UI

2. **Nine-Phase Pipeline with Intelligence**:
   - Research → Planning → Implementation → Lint → Typecheck → Test → Integration → E2E → Commit
   - Each phase has a focused goal and can't self-validate
   - Agents can request backtracking when they discover issues

3. **Leveraging Agent Intelligence**:
   - Agents assess their own success/failure with evidence
   - Agents provide context for why they need to retry/backtrack
   - System orchestrates based on agent feedback, not rigid rules

4. **Evidence-Based Validation**:
   - Simple file existence checks (research.md, plan.md)
   - Command output verification (pytest passing, flake8 clean)
   - No complex parsing - just "does the evidence exist?"

### How It Should Work (Simple Implementation)

```python
# The entire system distilled to its essence
async def run_milestone(milestone):
    context = ""
    for phase_name, prompt_template, expected_output in PHASES:
        # Build prompt with context from previous phases
        prompt = prompt_template.format(milestone=milestone, context=context)
        
        # Let Claude Code work with its full intelligence
        result = await execute_phase(prompt)
        
        # Simple validation
        if not Path(expected_output).exists():
            # Let agent explain why it failed
            context += f"\n{phase_name} failed: {result.explanation}"
            if result.suggests_backtrack:
                return "backtrack", result.backtrack_to
            else:
                return "retry", context
        
        # Accumulate context for next phase
        context += f"\n{phase_name} completed: {result.summary}"
    
    return "success", context
```

### The Nine Phases (From PHASE_CONFIGS)

```python
# From phase_orchestrator.py line 946
PHASE_CONFIGS = [
    1. research     → Analyze requirements and explore solutions (creates research.md)
    2. planning     → Create detailed implementation plan (creates plan.md)
    3. implement    → Build the solution (creates/modifies code files)
    4. lint         → Fix code style issues - flake8 F-errors only
    5. typecheck    → Fix type errors - mypy --strict must pass
    6. test         → Fix unit tests - pytest tests/unit must pass
    7. integration  → Fix integration tests - pytest tests/integration must pass
    8. e2e          → Verify main.py runs successfully (creates e2e_evidence.log)
    9. commit       → Create git commit with changes
]
```

### Intelligent Phase Flow

- **Forward progress**: Each phase builds on previous phase outputs
- **Smart retries**: Phases can retry with context about what failed
- **Intelligent backtracking**: Later phases can request earlier phases re-run
  - Example: Test phase discovers design flaw → backtrack to Planning
  - Example: Implementation realizes research missed a requirement → backtrack to Research
- **Evidence gates**: Can't proceed without concrete evidence (files, clean output)

## Usage

```bash
# SDK is now the default mode (uses Claude Max subscription)
python cli.py --project /path/to/project

# Resume from last checkpoint
python cli.py --project /path/to/project --resume

# Run specific milestone only
python cli.py --project /path/to/project --milestone 2

# Verbose mode to see details
python cli.py --project /path/to/project --verbose
```

## Critical Validation Requirements

**NEVER TRUST CLAUDE'S CLAIMS WITHOUT VERIFICATION**

Every phase MUST provide evidence and pass independent validation:

1. **Lint**: `flake8 --select=F` must return zero errors
2. **Typecheck**: `mypy --strict` must pass
3. **Test**: `pytest tests/unit` must pass
4. **Integration**: `pytest tests/integration` must pass  
5. **Research**: Must create research.md with >100 chars
6. **Planning**: Must create plan.md with >50 chars
7. **Implement**: Must create main.py or src/*.py files
8. **E2E**: Must create e2e_evidence.log
9. **Commit**: Must create actual git commit

The `_validate_phase_outputs()` method enforces these requirements.

## Current Status & Root Cause Analysis

### What's Actually Happening

1. **Research phase fails** - Claude doesn't create research.md
2. **WebSearch hangs** - Possibly geographic restriction (US-only per SDK docs)  
3. **TaskGroup errors** - Nested async contexts from over-engineered error handling
4. **Complex prompts** - Too much instruction instead of trusting Claude

### The Real Problem

Current bugs are likely from SIMPLE issues being misdiagnosed:
- Path mismatches between prompts and validation
- Geographic restrictions on WebSearch (US-only)
- Existing files causing "File not read" errors
- Tool timeouts being interpreted as architectural flaws

### Debugging Approach (Not System Simplification!)

1. **First, check simple causes** - File paths, permissions, existing files
2. **Test individual components** - Isolate what's actually failing
3. **Keep ALL functionality** - Don't remove features, fix root causes

## The Fix Plan: Debug Simple Issues First

### Step 1: Diagnose Specific Failures
Test individual components to find actual issues:
```python
# test_websearch.py - Test if WebSearch works in your location
from claude_code_sdk import query, ClaudeCodeOptions
import asyncio

async def test():
    prompt = "Use WebSearch to find information about Python asyncio and write a summary to test.md"
    async for msg in query(prompt=prompt, options=ClaudeCodeOptions(max_turns=5)):
        print(msg)

asyncio.run(test())
```

### Step 2: Fix Path and Validation Issues
Common simple fixes that solve "complex" problems:
- Ensure prompt paths match validation paths (relative vs absolute)
- Clean up existing milestone directories before fresh runs
- Check if WebSearch is available in your geographic location
- Verify file permissions in project directory

### Step 3: Maintain Full System Functionality
Keep ALL features working:
- All 9 phases remain active
- WebSearch stays enabled (with geographic fallback if needed)
- Context flow between phases
- Intelligent backtracking
- Evidence-based validation
- Full error recovery mechanisms

## Testing

```bash
# Test with example project
cd test_example/
python ../cli.py --project . --verbose

# Check logs for any errors
cat .cc_automator/logs/*.log | grep "error"

# Verify milestone files created
ls -la .cc_automator/milestones/milestone_1/
```

## Key Benefits of Current Implementation

1. **Context Preservation** ✅ - SDK maintains conversation history
2. **No Infinite Loops** ✅ - Cleanup prevents write errors
3. **Accurate Costs** ✅ - Per-phase cost tracking  
4. **Session Management** ✅ - Resume/continue support
5. **No API Key Required** ✅ - Uses Claude Max subscription
6. **Validation Enforcement** ✅ - Catches false success claims

## Key Files and Code Structure

### Core Files
- **`phase_orchestrator.py`** - Main SDK integration and phase execution
  - Contains `PHASE_CONFIGS` (line 946) defining all 9 phases
  - `_execute_with_sdk()` method handles SDK communication
  - `_validate_phase_outputs()` enforces evidence requirements
  
- **`orchestrator.py`** - Main orchestration logic and milestone management
  - Handles milestone decomposition and phase sequencing
  - Contains directory cleanup fix (line 269)
  - Manages resume/checkpoint functionality
  
- **`phase_prompt_generator.py`** - Generates prompts for each phase
  - `_get_base_prompt()` has prompts for all 9 phases
  - Recently fixed to use relative paths instead of absolute
  
- **`milestone_decomposer.py`** - Breaks projects into achievable milestones
  - Uses LLM to intelligently decompose complex projects
  - Creates milestone objects with success criteria
  
- **`cli.py`** - Command-line interface
  - Entry point for running the automator
  - Handles arguments like --resume, --milestone, --verbose

### Directory Structure
```
.cc_automator/
├── milestones/
│   └── milestone_1/
│       ├── research.md         # Created by research phase
│       ├── plan.md            # Created by planning phase
│       └── e2e_evidence.log   # Created by e2e phase
├── checkpoints/               # Session state for resume
├── logs/                      # Detailed execution logs
└── evidence/                  # Phase execution evidence
```

## Current Implementation Status

### What's Working
1. **SDK Integration** ✅ - Basic SDK communication established
2. **File Cleanup** ✅ - Milestone directories cleaned on fresh start
3. **Session Management** ✅ - Can resume from checkpoints
4. **Cost Tracking** ✅ - Tracks token usage per phase
5. **Basic Phase Structure** ✅ - 9 phases defined and executable

### What's Not Working
1. **Research Phase** ❌ - Fails to create research.md
   - WebSearch hangs (possibly geographic restriction)
   - Prompts may be too complex
   - Path issues between prompt and validation
   
2. **TaskGroup Errors** ❌ - Async errors in SDK execution
   - Happens when WebSearch is used
   - Enhanced error handling partially mitigates but doesn't fix root cause
   
3. **Context Flow** ❌ - Previous phase outputs not properly passed
   - Each phase starts fresh without context
   - Need to implement context accumulation

### Error Messages and Meanings
- **"File has not been read yet"** - Claude trying to Write existing file without Read
- **"TaskGroup: unhandled errors"** - Nested async context or tool timeout
- **"Phase validation failed"** - Expected output file doesn't exist
- **"AttributeError: 'str' object has no attribute 'name'"** - Phase object type mismatch

## Milestone Decomposition Process

The system automatically breaks complex projects into milestones:

1. **Input**: Project description (e.g., "Build expense tracker with categories")
2. **Decomposer**: Uses LLM to create logical milestones
3. **Output**: List of milestones with:
   - Name and description
   - Success criteria
   - Dependencies on previous milestones

Example decomposition:
```
Project: "FastAPI CRUD with authentication"
→ Milestone 1: Basic CRUD API
→ Milestone 2: Add database persistence  
→ Milestone 3: Add JWT authentication
→ Milestone 4: Add user management
```

## Important Notes

- SDK mode is default (USE_CLAUDE_SDK=true)
- Milestone directories cleaned on fresh starts
- Validation may catch failures - this is good!
- Each phase has specific output requirements
- Logs saved in .cc_automator/logs/
- WebSearch may timeout due to geographic restrictions

## For Claude Code Agents

When working on this codebase:
1. **Always validate outputs** - Don't trust claims, verify with subprocess
2. **Create required files** - Each phase has specific file requirements
3. **Show evidence** - Include command outputs that prove success
4. **Handle existing files** - Check if files exist before writing
5. **Use absolute paths** - Avoid relative path issues
6. **Remember context** - Previous phases create files you might need
7. **NEVER REMOVE FUNCTIONALITY** - Do not disable tools like WebSearch, Context7, or MCP without explicit user permission. These are essential features. If there are issues, find the root cause instead of reducing functionality.

## File Write/Edit Guidelines

**IMPORTANT**: Claude Code has a safety feature:
- **Write tool**: Only for NEW files (or after reading existing ones)
- **Edit tool**: For modifying EXISTING files
- If you get "File has not been read yet", either:
  1. Read the file first, then Write
  2. Use Edit instead of Write
  3. Check if the file should be deleted first

This prevents accidental data loss but can cause confusion if not understood.