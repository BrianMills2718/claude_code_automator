#!/usr/bin/env python3
"""Debug script to reproduce the file parallel executor error"""

from pathlib import Path
from phase_orchestrator import PhaseOrchestrator, create_phase, Phase
from file_parallel_executor import FileParallelExecutor

# Create minimal orchestrator
orchestrator = PhaseOrchestrator("debug_test", str(Path.cwd()), verbose=False)

# Test creating a phase like FileParallelExecutor does
allowed_tools = ["Read", "Edit", "Bash"]

print(f"Creating phase with allowed_tools: {allowed_tools}")
print(f"Type of allowed_tools: {type(allowed_tools)}")

phase = create_phase(
    name="lint_test",
    description="Fix lint errors in test.py",
    prompt="Test prompt",
    allowed_tools=allowed_tools
)

print(f"\nPhase created:")
print(f"  name: {phase.name}")
print(f"  allowed_tools: {phase.allowed_tools}")
print(f"  type of allowed_tools: {type(phase.allowed_tools)}")

# Try to execute it (this might fail)
print("\nAttempting to execute phase...")
try:
    # Just test the phase header printing
    if hasattr(orchestrator, 'verbose') and orchestrator.verbose:
        print("Would print verbose header")
    else:
        print("Would print minimal header")
        
    # Test the join that might be failing
    if phase.allowed_tools:
        tools_str = ', '.join(phase.allowed_tools)
        print(f"Tools string: {tools_str}")
    else:
        print("No allowed_tools")
        
except Exception as e:
    print(f"ERROR: {e}")
    print(f"Error type: {type(e).__name__}")
    import traceback
    traceback.print_exc()