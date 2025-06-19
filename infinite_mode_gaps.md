# Infinite Mode Implementation Gaps

This document identifies all places in the codebase where infinite mode (`--infinite`) should remove limits but currently doesn't.

## Current Implementation Status

### ✅ Already Implemented
1. **Phase Orchestrator** (`src/phase_orchestrator.py`)
   - Line 1759: `max_attempts = 1 if not self.infinite_mode else 999999`
   - Line 1817-1826: Step-back limit handling with infinite mode check

2. **File Parallel Executor** (`src/file_parallel_executor.py`)
   - Line 272: `max_iterations = 999999 if self.infinite_mode else 5` (lint phase)
   - Line 372: `max_iterations = 999999 if self.infinite_mode else 5` (typecheck phase)

3. **CLI Integration** (`cli.py`)
   - Line 58-59: `--infinite` flag properly defined
   - Line 97: Passed to orchestrator

4. **Orchestrator** (`src/orchestrator.py`)
   - Line 54: Accepts `infinite_mode` parameter
   - Line 90: Passes to FileParallelExecutor
   - Line 193: Passes to PhaseOrchestrator

### ❌ Missing Implementations / Gaps Found

1. **Hardcoded Turn Limits in PHASE_CONFIGS** (`src/phase_orchestrator.py:2377-2387`)
   ```python
   PHASE_CONFIGS = [
       ("research",     "...", [...], None, 30),  # Fixed 30 turns
       ("planning",     "...", [...], None, 50),  # Fixed 50 turns
       ("implement",    "...", [...], None, 50),  # Fixed 50 turns
       ("lint",         "...", [...], None, 20),  # Fixed 20 turns
       ("typecheck",    "...", [...], None, 20),  # Fixed 20 turns
       ("test",         "...", [...], None, 30),  # Fixed 30 turns
       ("integration",  "...", [...], None, 30),  # Fixed 30 turns
       ("e2e",          "...", [...], None, 20),  # Fixed 20 turns
       ("validate",     "...", [...], None, 50),  # Fixed 50 turns
       ("commit",       "...", [...], None, 15)   # Fixed 15 turns
   ]
   ```
   **Issue**: These turn limits are hardcoded and don't respect infinite mode. In infinite mode, all phases should have unlimited turns (999999).

2. **WebSearch Timeout** (`src/phase_orchestrator.py:566`)
   ```python
   websearch_timeout_seconds = 30  # Hardcoded 30 second timeout
   ```
   **Issue**: WebSearch has a hardcoded 30-second timeout that doesn't respect infinite mode. This was mentioned in CLAUDE.md as resolved in V3, but the legacy code path still has this limit.

3. **Phase Timeout** (`src/phase_orchestrator.py:60`)
   ```python
   timeout_seconds: int = 600  # 10 minutes default
   ```
   **Issue**: Phase timeout is hardcoded to 600 seconds (10 minutes) and doesn't adjust for infinite mode. In infinite mode, phases should have no timeout or a very large timeout.

4. **Message Buffer Limits** (`src/phase_orchestrator.py:77,99,577`)
   ```python
   self.max_messages = max_messages = 1000  # Fixed buffer size
   if len(messages) > self.max_messages:
       messages = messages[-self.max_messages//2:]  # Truncates messages
   ```
   **Issue**: Message buffer has a fixed size that could cause issues in infinite mode with very long-running phases.

5. **Stagnation Detection in Typecheck** (`src/file_parallel_executor.py:404-406`)
   ```python
   if stagnant_iterations >= 3:
       print(f"🛑 Breaking infinite loop - same errors persist after {stagnant_iterations} attempts")
       break
   ```
   **Issue**: Even in infinite mode, typecheck breaks after 3 stagnant iterations. This defeats the purpose of infinite mode.

## Recommended Fixes

### 1. Dynamic Turn Limits Based on Infinite Mode
In `src/phase_orchestrator.py`, modify the `create_phase` function to override turn limits when infinite mode is active:

```python
def create_phase(name: str, description: str, prompt: str, 
                 allowed_tools: Optional[List[str]] = None, 
                 think_mode: Optional[str] = None,
                 max_turns: Optional[int] = None) -> Phase:
    """Helper to create a phase with defaults from PHASE_CONFIGS"""
    
    # Check if orchestrator is in infinite mode (need to pass this through)
    infinite_mode = getattr(orchestrator, 'infinite_mode', False) if 'orchestrator' in globals() else False
    
    # Find config for this phase
    for config_name, config_desc, config_tools, config_think, config_max_turns in PHASE_CONFIGS:
        if config_name == name:
            phase = Phase(
                name=name,
                description=description or config_desc,
                prompt=prompt,
                allowed_tools=allowed_tools or config_tools,
                think_mode=think_mode or config_think
            )
            # Use explicit max_turns if provided, otherwise use config, otherwise use default
            if max_turns is not None:
                phase.max_turns = max_turns
            elif infinite_mode:
                phase.max_turns = 999999  # Override with infinite turns
            elif config_max_turns is not None:
                phase.max_turns = config_max_turns
            return phase
```

### 2. Remove WebSearch Timeout in Infinite Mode
In `src/phase_orchestrator.py:566`, make timeout conditional:

```python
websearch_timeout_seconds = None if self.infinite_mode else 30
```

### 3. Adjust Phase Timeout for Infinite Mode
In Phase dataclass definition:

```python
timeout_seconds: int = field(default_factory=lambda: 999999 if infinite_mode else 600)
```

### 4. Increase Message Buffer for Infinite Mode
Dynamic buffer sizing based on mode:

```python
self.max_messages = 10000 if self.infinite_mode else 1000
```

### 5. Disable Stagnation Breaking in Infinite Mode
In `src/file_parallel_executor.py:404-406`:

```python
if stagnant_iterations >= 3 and not self.infinite_mode:
    print(f"🛑 Breaking infinite loop - same errors persist after {stagnant_iterations} attempts")
    break
elif stagnant_iterations >= 3 and self.infinite_mode:
    print(f"⚠️  Same errors for {stagnant_iterations} iterations, but continuing (infinite mode)")
```

## Summary

The main gaps are:
1. **Turn limits** in PHASE_CONFIGS are hardcoded and ignore infinite mode
2. **Timeouts** (WebSearch, phase timeout) don't respect infinite mode
3. **Buffer limits** could cause issues in very long-running infinite mode sessions
4. **Stagnation detection** breaks loops even in infinite mode

These fixes would ensure that `--infinite` truly removes all artificial constraints and allows the system to run until success.