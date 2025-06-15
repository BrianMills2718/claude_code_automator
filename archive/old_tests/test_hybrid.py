#!/usr/bin/env python3
"""
Test the hybrid orchestrator with a simple lint phase
"""

import sys
import json
from pathlib import Path
from hybrid_orchestrator import HybridOrchestrator, Phase

# Test project directory
test_dir = Path("/tmp/test_hybrid")
test_dir.mkdir(exist_ok=True)

# Create a simple Python file with lint errors
test_file = test_dir / "test.py"
test_file.write_text("""
import os
def hello( ):
    print("Hello")
    x=1+2
""")

# Create orchestrator
orchestrator = HybridOrchestrator(test_dir, verbose=True)

# Test lint phase
print("Testing lint phase with hybrid approach...")
phase = Phase(
    name="lint",
    description="Fix linting errors",
    args={},  # No args needed for lint
    max_turns=5
)

result = orchestrator.execute_phase(phase)

print(f"\nResult: {json.dumps(result, indent=2)}")

# Clean up
test_file.unlink()
test_dir.rmdir()