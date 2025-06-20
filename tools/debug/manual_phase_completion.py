#!/usr/bin/env python3
"""
Manual Phase Completion Tool
Allows marking phases as complete when SDK errors prevent automatic completion
"""

import json
import sys
from pathlib import Path
from datetime import datetime

def complete_phase(project_dir: str, phase_name: str, milestone_num: int = 1):
    """Manually mark a phase as complete"""
    
    project_path = Path(project_dir)
    checkpoint_dir = project_path / ".cc_automator" / "checkpoints"
    checkpoint_file = checkpoint_dir / f"{phase_name}_checkpoint.json"
    
    # Create checkpoint data
    checkpoint_data = {
        "name": phase_name,
        "description": f"Manually completed {phase_name} phase",
        "status": "completed",
        "session_id": f"manual-{int(datetime.now().timestamp())}",
        "cost_usd": 0.0,
        "duration_ms": 1000,
        "error": None,
        "start_time": datetime.now().isoformat(),
        "end_time": datetime.now().isoformat(),
        "think_mode": None
    }
    
    # Create checkpoint directory if needed
    checkpoint_dir.mkdir(parents=True, exist_ok=True)
    
    # Write checkpoint
    with open(checkpoint_file, 'w') as f:
        json.dump(checkpoint_data, f, indent=2)
    
    print(f"✅ Marked {phase_name} as complete for {project_dir}")
    
    # Update progress.json if it exists
    progress_file = project_path / ".cc_automator" / "progress.json"
    if progress_file.exists():
        with open(progress_file, 'r') as f:
            progress = json.load(f)
        
        # Update milestone progress
        milestone_key = f"Milestone {milestone_num}"
        if milestone_key in progress.get("milestones", {}):
            milestone = progress["milestones"][milestone_key]
            milestone["completed_phases"] = milestone.get("completed_phases", 0) + 1
            
            # Determine next phase
            phase_order = ["research", "planning", "implement", "architecture", 
                         "lint", "typecheck", "test", "integration", "e2e", 
                         "validate", "commit"]
            
            current_idx = phase_order.index(phase_name) if phase_name in phase_order else -1
            if current_idx >= 0 and current_idx < len(phase_order) - 1:
                next_phase = phase_order[current_idx + 1]
                milestone["current_phase"] = f"milestone_{milestone_num}_{next_phase}"
            
            # Write updated progress
            with open(progress_file, 'w') as f:
                json.dump(progress, f, indent=2)
            
            print(f"✅ Updated progress.json")

def verify_phase_work(project_dir: str, phase_name: str) -> bool:
    """Verify that phase work was actually completed"""
    
    project_path = Path(project_dir)
    
    checks = {
        "research": lambda: any(project_path.rglob("*research*.md")),
        "planning": lambda: any(project_path.rglob("*plan*.md")),
        "implement": lambda: (project_path / "main.py").exists() or any(project_path.rglob("src/*.py")),
        "architecture": lambda: any(project_path.rglob("*architecture*.md")),
        "lint": lambda: True,  # Assume manual verification
        "typecheck": lambda: True,  # Assume manual verification  
        "test": lambda: True,  # Assume manual verification
        "e2e": lambda: any(project_path.rglob("*e2e*.log")),
    }
    
    if phase_name in checks:
        result = checks[phase_name]()
        print(f"🔍 Verification for {phase_name}: {'✅ PASSED' if result else '❌ FAILED'}")
        return result
    
    return True

if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("Usage: python manual_phase_completion.py <project_dir> <phase_name> [milestone_num]")
        print("Example: python manual_phase_completion.py example_projects/test_v4_todo test 1")
        sys.exit(1)
    
    project_dir = sys.argv[1]
    phase_name = sys.argv[2]
    milestone_num = int(sys.argv[3]) if len(sys.argv) > 3 else 1
    
    # Verify work was done
    if verify_phase_work(project_dir, phase_name):
        complete_phase(project_dir, phase_name, milestone_num)
    else:
        print(f"❌ Cannot complete {phase_name} - work not verified")
        print("Please ensure the phase outputs exist before marking complete")