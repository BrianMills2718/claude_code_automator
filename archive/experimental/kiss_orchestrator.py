#!/usr/bin/env python3
"""
KISS (Keep It Simple, Stupid) Orchestrator
Minimal complexity, maximum speed
"""

import subprocess
import json
import time
from pathlib import Path
from typing import Dict, Optional

class KISSOrchestrator:
    """Dead simple orchestrator - no fancy features"""
    
    def __init__(self, project_dir: str):
        self.project_dir = Path(project_dir)
        self.log_dir = self.project_dir / ".cc_automator" / "logs"
        self.log_dir.mkdir(parents=True, exist_ok=True)
        
    def run_phase(self, phase: str, milestone_name: str, milestone_num: int) -> Dict:
        """Run a single phase - simple and direct"""
        
        print(f"\n=== {phase.upper()} ===")
        
        # Get simple prompt
        from simple_prompts import get_simple_prompt
        prompt = get_simple_prompt(phase, milestone_name)
        
        # Add output file requirement for key phases
        if phase in ["research", "planning", "implement"]:
            output_file = f".cc_automator/milestones/milestone_{milestone_num}/{phase}.md"
            prompt += f"\n\nSave output to: {output_file}"
        
        # Build command
        cmd = [
            "claude", "-p", prompt,
            "--output-format", "json",
            "--max-turns", "10",
            "--dangerously-skip-permissions"
        ]
        
        # For mechanical fixes, reduce turns
        if phase in ["lint", "typecheck"]:
            cmd[5] = "5"  # Reduce max turns
        
        # Run it
        start = time.time()
        result = subprocess.run(
            cmd, 
            capture_output=True, 
            text=True, 
            cwd=self.project_dir,
            timeout=300  # 5 minute timeout
        )
        duration = time.time() - start
        
        # Parse result
        if result.returncode == 0:
            data = json.loads(result.stdout)
            print(f"✓ Completed in {duration:.1f}s")
            print(f"  Cost: ${data.get('cost_usd', 0):.4f}")
            
            # Save log
            log_file = self.log_dir / f"{phase}_{int(time.time())}.json"
            log_file.write_text(result.stdout)
            
            return {
                "success": True,
                "duration": duration,
                "cost": data.get('cost_usd', 0),
                "session_id": data.get('session_id')
            }
        else:
            print(f"✗ Failed after {duration:.1f}s")
            print(f"  Error: {result.stderr[:200]}")
            return {
                "success": False,
                "duration": duration,
                "error": result.stderr
            }
    
    def run_milestone(self, milestone_name: str, milestone_num: int):
        """Run all phases for a milestone"""
        
        print(f"\n{'='*60}")
        print(f"MILESTONE {milestone_num}: {milestone_name}")
        print(f"{'='*60}")
        
        phases = [
            "research",
            "planning", 
            "implement",
            "lint",
            "typecheck",
            "test",
            "integration",
            "e2e"
        ]
        
        total_time = 0
        total_cost = 0
        
        for phase in phases:
            result = self.run_phase(phase, milestone_name, milestone_num)
            
            total_time += result["duration"]
            total_cost += result.get("cost", 0)
            
            if not result["success"]:
                print(f"\n⚠ Stopping due to {phase} failure")
                break
        
        print(f"\n{'='*60}")
        print(f"MILESTONE COMPLETE")
        print(f"Total time: {total_time:.1f}s")
        print(f"Total cost: ${total_cost:.4f}")
        print(f"{'='*60}")


def main():
    """Test with calculator project"""
    import sys
    
    project_dir = sys.argv[1] if len(sys.argv) > 1 else "/home/brian/autocoder2_cc/test_calculator"
    
    orchestrator = KISSOrchestrator(project_dir)
    orchestrator.run_milestone("Basic arithmetic operations", 1)


if __name__ == "__main__":
    main()