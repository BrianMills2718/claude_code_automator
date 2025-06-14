#!/usr/bin/env python3
"""
Simple test of multi-phase execution
"""

from phase_orchestrator import PhaseOrchestrator, Phase
from pathlib import Path


def main():
    # Create output directory
    output_dir = Path("/home/brian/autocoder2_cc/cc_automator3/simple_test_output")
    output_dir.mkdir(exist_ok=True)
    
    # Create orchestrator
    orchestrator = PhaseOrchestrator(
        project_name="Simple Write and Review",
        working_dir=str(output_dir)
    )
    
    # Phase 1: Write a simple script
    write_phase = Phase(
        name="Write Hello Script",
        prompt="""Create a simple Python script called hello.py that:
1. Has a greet() function that takes a name parameter
2. Prints a greeting message
3. Has a main() function that demonstrates usage

Write this script now.""",
        allowed_tools=["Write"]
    )
    
    # Phase 2: Review the script  
    review_phase = Phase(
        name="Review Hello Script",
        prompt="""Review the hello.py script and create review_notes.md with:
1. Code quality observations
2. Any suggestions for improvement

Keep the review brief but constructive.""",
        allowed_tools=["Read", "Write"]
    )
    
    # Add phases
    orchestrator.add_phase(write_phase)
    orchestrator.add_phase(review_phase)
    
    # Execute all phases
    results = orchestrator.execute_all()
    
    # Show results
    print("\n" + "="*60)
    print("FINAL RESULTS")
    print("="*60)
    
    if results["completed"]:
        print("✓ All phases completed successfully!")
        
        # List created files
        created_files = list(output_dir.glob("*"))
        if created_files:
            print("\nCreated files:")
            for f in created_files:
                print(f"  - {f.name}")
    else:
        print("✗ Execution failed")
    
    return 0 if results["completed"] else 1


if __name__ == "__main__":
    import sys
    sys.exit(main())