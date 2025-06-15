#!/usr/bin/env python3
"""
Test script for core CC_AUTOMATOR3 components
Tests the phase orchestrator, session manager, and progress tracking
"""

import sys
from pathlib import Path
from phase_orchestrator import PhaseOrchestrator, create_phase
from session_manager import SessionManager
from preflight_validator import PreflightValidator
from progress_tracker import ProgressTracker


def test_preflight():
    """Test preflight validation"""
    print("\n" + "="*60)
    print("Testing Preflight Validator")
    print("="*60)
    
    validator = PreflightValidator()
    passed, errors = validator.run_all_checks()
    
    if not passed:
        print("\nPreflight checks failed. Please fix issues before proceeding.")
        return False
        
    return True


def test_simple_phase():
    """Test a simple phase execution"""
    print("\n" + "="*60)
    print("Testing Phase Execution")
    print("="*60)
    
    # Create test directory
    test_dir = Path("test_cc_automator_output")
    test_dir.mkdir(exist_ok=True)
    
    # Initialize components
    orchestrator = PhaseOrchestrator("Test Calculator Project", str(test_dir))
    session_mgr = SessionManager(test_dir)
    tracker = ProgressTracker(test_dir, "Test Calculator Project")
    
    # Add a milestone
    tracker.add_milestone("Basic Implementation", ["research", "planning", "implement"])
    tracker.start_milestone("Basic Implementation")
    
    # Create a simple research phase
    research_phase = create_phase(
        "research",
        "Research calculator requirements",
        """Create a simple analysis of what a basic Python calculator should include.
        List 3-5 key features and save your findings to research_output.md"""
    )
    
    # Execute the phase
    print("\nExecuting research phase...")
    tracker.update_phase("Basic Implementation", "research", "running")
    
    result = orchestrator.execute_phase(research_phase)
    
    # Update tracking based on result
    if result["status"] == "completed":
        tracker.update_phase("Basic Implementation", "research", "completed", 
                           cost=result.get("cost_usd", 0))
        
        # Save session
        if result.get("session_id"):
            session_mgr.add_session("research", result["session_id"], result)
            print(f"\nSession saved: {result['session_id']}")
    else:
        tracker.update_phase("Basic Implementation", "research", "failed")
        print(f"\nPhase failed: {result.get('error', 'Unknown error')}")
        
    # Display progress
    tracker.display_progress()
    
    # Check if output file was created
    research_file = test_dir / "research_output.md"
    if research_file.exists():
        print(f"\n✓ Research output created successfully")
        print(f"  File: {research_file}")
    else:
        print(f"\n✗ Research output not found")
        
    return result["status"] == "completed"


def test_session_resumption():
    """Test session resumption capability"""
    print("\n" + "="*60)
    print("Testing Session Resumption")
    print("="*60)
    
    test_dir = Path("test_cc_automator_output")
    session_mgr = SessionManager(test_dir)
    
    # Check if we have a saved session
    research_session = session_mgr.get_session("research")
    if research_session:
        print(f"Found saved session: {research_session}")
        
        resume_cmd = session_mgr.get_resume_command("research")
        if resume_cmd:
            print(f"Resume command: {' '.join(resume_cmd)}")
            
        # Get all sessions
        all_sessions = session_mgr.get_all_sessions()
        print(f"\nAll saved sessions:")
        for phase, session_id in all_sessions.items():
            print(f"  {phase}: {session_id}")
    else:
        print("No saved sessions found")
        
    return True


def test_progress_persistence():
    """Test progress loading and saving"""
    print("\n" + "="*60)
    print("Testing Progress Persistence")
    print("="*60)
    
    test_dir = Path("test_cc_automator_output")
    
    # Try to load existing progress
    tracker = ProgressTracker(test_dir, "Test Calculator Project")
    if tracker.load_progress():
        print("✓ Loaded existing progress")
        tracker.display_progress()
        
        # Check resume point
        resume_point = tracker.get_resume_point()
        if resume_point:
            print(f"\nResume from: {resume_point}")
    else:
        print("No existing progress found")
        
    # Create summary report
    report = tracker.create_summary_report()
    report_file = test_dir / "execution_report.md"
    with open(report_file, 'w') as f:
        f.write(report)
    print(f"\nReport saved to: {report_file}")
    
    return True


def main():
    """Run all tests"""
    print("CC_AUTOMATOR3 Core Components Test")
    print("="*60)
    
    tests = [
        ("Preflight Validation", test_preflight),
        ("Phase Execution", test_simple_phase),
        ("Session Management", test_session_resumption),
        ("Progress Tracking", test_progress_persistence)
    ]
    
    results = []
    for test_name, test_func in tests:
        try:
            passed = test_func()
            results.append((test_name, passed))
        except Exception as e:
            print(f"\n✗ {test_name} failed with error: {e}")
            results.append((test_name, False))
            
    # Summary
    print("\n" + "="*60)
    print("Test Summary")
    print("="*60)
    
    for test_name, passed in results:
        status = "✓ PASSED" if passed else "✗ FAILED"
        print(f"{status}: {test_name}")
        
    all_passed = all(passed for _, passed in results)
    
    if all_passed:
        print("\n✓ All tests passed! Core components are working correctly.")
        print("\nNext steps:")
        print("1. Create phase prompt templates")
        print("2. Build the setup script for project configuration")
        print("3. Implement milestone decomposition")
    else:
        print("\n✗ Some tests failed. Please check the errors above.")
        
    return 0 if all_passed else 1


if __name__ == "__main__":
    sys.exit(main())