#!/usr/bin/env python3
"""Test a single phase execution"""

import sys
sys.path.append('..')

from phase_orchestrator import PhaseOrchestrator, Phase
from pathlib import Path

# Create a simple test phase
phase = Phase(
    name='test',
    description='Test phase',
    prompt='Create a file test123.txt with content "Hello from test phase"',
    allowed_tools=['Write'],
    max_turns=5,
    timeout_seconds=120
)

# Run it
orchestrator = PhaseOrchestrator(Path('.'))
result = orchestrator.execute_phase(phase)

print(f"\nPhase result: {result}")
print(f"Status: {result.get('status')}")
print(f"Duration: {result.get('duration_seconds')}s")

# Check if file was created
if Path('test123.txt').exists():
    print("✓ Test file created successfully")
else:
    print("✗ Test file not created")