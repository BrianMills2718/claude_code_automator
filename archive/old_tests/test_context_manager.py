#!/usr/bin/env python3
"""Test the context manager to show how it provides focused context"""

from pathlib import Path
from context_manager import ContextManager, PhaseContext

# Create test project directory
test_dir = Path("test_calculator_project")

# Initialize context manager
cm = ContextManager(test_dir)

# Test 1: Research phase (no previous output needed)
print("=" * 60)
print("RESEARCH PHASE CONTEXT")
print("=" * 60)
research_context = cm.get_phase_context("research")
print(research_context)
print("\nNote: Research gets CLAUDE.md, README.md, requirements.txt only")

# Test 2: Planning phase (needs research summary)
print("\n" + "=" * 60)
print("PLANNING PHASE CONTEXT")
print("=" * 60)
fake_research_output = """
# Research Phase Output

## Analysis
Detailed analysis of 500 lines...

## Technical Decisions
Many technical details here...

## Summary
Key findings:
- Need to implement 4 basic arithmetic operations
- Should use class-based design
- Need comprehensive error handling
- Must pass all tests
"""

planning_context = cm.get_phase_context("planning", fake_research_output)
print(planning_context)
print("\nNote: Planning gets only the SUMMARY from research, not all details")

# Test 3: Lint phase (no previous output, just Python files)
print("\n" + "=" * 60)
print("LINT PHASE CONTEXT")
print("=" * 60)
lint_context = cm.get_phase_context("lint", "Previous implementation details...")
print(lint_context)
print("\nNote: Lint ignores previous output, only gets Python files and lint guidelines")

# Show what each phase needs
print("\n" + "=" * 60)
print("PHASE CONTEXT REQUIREMENTS")
print("=" * 60)
for phase_type, phase_ctx in cm.PHASE_CONTEXTS.items():
    print(f"\n{phase_type.upper()}:")
    print(f"  - Needs previous output: {phase_ctx.needs_previous_output}")
    print(f"  - Needs files: {phase_ctx.needs_files}")
    print(f"  - Summary only: {phase_ctx.needs_summary_only}")