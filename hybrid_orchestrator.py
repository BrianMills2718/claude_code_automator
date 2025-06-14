#!/usr/bin/env python3
"""
Hybrid Orchestrator for CC_AUTOMATOR3
Uses Claude command templates with separate CLI invocations
"""

import subprocess
import json
import time
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field
from enum import Enum


class PhaseStatus(Enum):
    """Status of a phase execution"""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    TIMEOUT = "timeout"
    SKIPPED = "skipped"


@dataclass
class Phase:
    """Represents a single execution phase"""
    name: str
    description: str
    args: Dict[str, str] = field(default_factory=dict)
    max_turns: int = 10
    timeout_seconds: int = 600
    
    # Execution results
    status: PhaseStatus = PhaseStatus.PENDING
    session_id: Optional[str] = None
    cost_usd: float = 0.0
    duration_ms: int = 0
    error: Optional[str] = None
    output: Optional[str] = None
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None


class HybridOrchestrator:
    """Orchestrator using Claude command templates"""
    
    def __init__(self, working_dir: str, verbose: bool = False):
        self.working_dir = Path(working_dir)
        self.verbose = verbose
        self.phases: List[Phase] = []
        
        # Ensure .claude/commands exists
        self.command_dir = Path(__file__).parent / ".claude" / "commands"
        if not self.command_dir.exists():
            raise RuntimeError(f"Command templates not found at {self.command_dir}")
            
        # Setup logging
        self.log_dir = self.working_dir / ".cc_automator" / "logs"
        self.log_dir.mkdir(parents=True, exist_ok=True)
        
        # Setup milestone output dir
        self.milestone_dir = self.working_dir / ".cc_automator" / "milestones"
        self.milestone_dir.mkdir(parents=True, exist_ok=True)
        
    def execute_phase(self, phase: Phase) -> Dict[str, Any]:
        """Execute a single phase using Claude command template"""
        
        print(f"\n{'='*60}")
        print(f"Phase: {phase.name}")
        print(f"Description: {phase.description}")
        if self.verbose and phase.args:
            print(f"Args: {phase.args}")
        print(f"{'='*60}")
        
        # Mark as running
        phase.status = PhaseStatus.RUNNING
        phase.start_time = datetime.now()
        
        # For now, we need to use -p with the template content
        # until Claude supports project-level commands
        template_file = self.command_dir / f"{phase.name}.md"
        if not template_file.exists():
            raise RuntimeError(f"Template not found: {template_file}")
            
        # Read template and substitute arguments
        template = template_file.read_text()
        for key, value in phase.args.items():
            template = template.replace(f"{{{{{key}}}}}", str(value))
            
        # Build command using prompt flag
        cmd = [
            "claude", "-p", template,
            "--output-format", "json",
            "--max-turns", str(phase.max_turns),
            "--dangerously-skip-permissions"
        ]
        
        # Log file for this phase
        log_file = self.log_dir / f"{phase.name}_{int(time.time())}.json"
        
        try:
            # Execute
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                cwd=self.working_dir,
                timeout=phase.timeout_seconds
            )
            
            if result.returncode == 0:
                # Parse JSON output
                data = json.loads(result.stdout)
                phase.status = PhaseStatus.COMPLETED
                phase.session_id = data.get('session_id')
                phase.cost_usd = data.get('cost_usd', 0.0)
                
                # Save log
                log_file.write_text(result.stdout)
                
                # Extract phase output if needed
                phase.output = self._extract_phase_output(phase.name, data)
                
                if self.verbose:
                    print(f"✓ Completed successfully")
                    print(f"  Session: {phase.session_id}")
                    print(f"  Cost: ${phase.cost_usd:.4f}")
            else:
                phase.status = PhaseStatus.FAILED
                phase.error = result.stderr
                print(f"✗ Failed: {result.stderr[:200]}")
                
        except subprocess.TimeoutExpired:
            phase.status = PhaseStatus.TIMEOUT
            phase.error = f"Timed out after {phase.timeout_seconds}s"
            print(f"✗ Timeout after {phase.timeout_seconds}s")
            
        except Exception as e:
            phase.status = PhaseStatus.FAILED
            phase.error = str(e)
            print(f"✗ Error: {e}")
            
        finally:
            phase.end_time = datetime.now()
            phase.duration_ms = int((phase.end_time - phase.start_time).total_seconds() * 1000)
            
        return self._phase_to_dict(phase)
    
    def _extract_phase_output(self, phase_name: str, data: Dict) -> Optional[str]:
        """Extract relevant output from phase for context passing"""
        # For phases that produce output files, read them
        if phase_name in ["research", "planning", "implement"]:
            # Look for the output file mentioned in the phase
            # This is a simplified version - could be enhanced
            return f"Phase {phase_name} completed successfully"
        return None
    
    def _phase_to_dict(self, phase: Phase) -> Dict[str, Any]:
        """Convert phase to dictionary"""
        return {
            "name": phase.name,
            "status": phase.status.value,
            "session_id": phase.session_id,
            "cost_usd": phase.cost_usd,
            "duration_ms": phase.duration_ms,
            "error": phase.error,
            "output": phase.output
        }
    
    def run_milestone(self, milestone_name: str, milestone_number: int, 
                     success_criteria: List[str]) -> Dict[str, Any]:
        """Run all phases for a milestone"""
        
        print(f"\n{'='*70}")
        print(f"MILESTONE {milestone_number}: {milestone_name}")
        print(f"{'='*70}")
        
        # Convert success criteria to string
        criteria_str = "\n".join(f"- {c}" for c in success_criteria)
        
        # Define phases with their arguments
        phases_config = [
            ("research", {
                "milestone_name": milestone_name,
                "milestone_number": str(milestone_number),
                "success_criteria": criteria_str
            }),
            ("planning", {
                "milestone_name": milestone_name,
                "milestone_number": str(milestone_number),
                "success_criteria": criteria_str,
                "research_output": "See research.md"  # Will be loaded from file
            }),
            ("implement", {
                "milestone_name": milestone_name,
                "milestone_number": str(milestone_number),
                "success_criteria": criteria_str,
                "plan_output": "See plan.md"  # Will be loaded from file
            }),
            ("lint", {}),
            ("typecheck", {}),
            ("test", {
                "milestone_name": milestone_name,
                "milestone_number": str(milestone_number),
                "implement_output": "See implement.md"
            }),
            ("integration", {}),
            ("e2e", {
                "milestone_name": milestone_name,
                "milestone_number": str(milestone_number)
            })
        ]
        
        results = []
        total_cost = 0.0
        total_time = 0
        
        for phase_name, args in phases_config:
            # Load previous phase output if needed
            if phase_name == "planning" and "research_output" in args:
                research_file = self.milestone_dir / f"milestone_{milestone_number}" / "research.md"
                if research_file.exists():
                    args["research_output"] = research_file.read_text()
                    
            elif phase_name == "implement" and "plan_output" in args:
                plan_file = self.milestone_dir / f"milestone_{milestone_number}" / "plan.md"
                if plan_file.exists():
                    args["plan_output"] = plan_file.read_text()
                    
            elif phase_name == "test" and "implement_output" in args:
                impl_file = self.milestone_dir / f"milestone_{milestone_number}" / "implement.md"
                if impl_file.exists():
                    args["implement_output"] = impl_file.read_text()
            
            # Create and execute phase
            phase = Phase(
                name=phase_name,
                description=f"{phase_name.title()} phase for {milestone_name}",
                args=args
            )
            
            result = self.execute_phase(phase)
            results.append(result)
            
            total_cost += result["cost_usd"]
            total_time += result["duration_ms"]
            
            # Stop on failure
            if result["status"] == "failed":
                print(f"\n⚠ Stopping due to {phase_name} failure")
                break
        
        print(f"\n{'='*70}")
        print(f"MILESTONE COMPLETE")
        print(f"Total time: {total_time/1000:.1f}s")
        print(f"Total cost: ${total_cost:.4f}")
        print(f"{'='*70}")
        
        return {
            "milestone": milestone_name,
            "number": milestone_number,
            "phases": results,
            "total_cost": total_cost,
            "total_time_ms": total_time
        }


def main():
    """Test the hybrid orchestrator"""
    import sys
    
    project_dir = sys.argv[1] if len(sys.argv) > 1 else "/home/brian/autocoder2_cc/test_calculator"
    
    orchestrator = HybridOrchestrator(project_dir, verbose=True)
    
    # Run milestone 1
    result = orchestrator.run_milestone(
        "Basic arithmetic operations",
        1,
        ["Add, subtract, multiply, divide functions", "All tests pass"]
    )
    
    print(f"\nFinal result: {json.dumps(result, indent=2)}")


if __name__ == "__main__":
    main()