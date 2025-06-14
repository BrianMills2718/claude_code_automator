#!/usr/bin/env python3
"""
Phase Orchestrator for CC_AUTOMATOR3
Executes isolated phases using Claude Code CLI with streaming JSON output
"""

import subprocess
import json
import os
import sys
import time
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional, Generator, Any
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
    prompt: str
    allowed_tools: List[str] = field(default_factory=lambda: ["Read", "Write", "Edit", "MultiEdit", "Bash"])
    think_mode: Optional[str] = None
    max_turns: int = 50  # Increased for async completion
    timeout_seconds: int = 600  # 10 minutes default
    
    # Execution results
    status: PhaseStatus = PhaseStatus.PENDING
    session_id: Optional[str] = None
    cost_usd: float = 0.0
    duration_ms: int = 0
    error: Optional[str] = None
    evidence: Optional[str] = None
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None


class StreamingJSONProcessor:
    """Processes streaming JSON output from Claude Code"""
    
    def __init__(self):
        self.messages = []
        self.current_session_id = None
        self.final_result = None
        
    def process_line(self, line: str) -> Optional[Dict[str, Any]]:
        """Process a single line of streaming JSON output"""
        if not line.strip():
            return None
            
        try:
            event = json.loads(line)
            
            # Track session ID from init message
            if event.get("type") == "system" and event.get("subtype") == "init":
                self.current_session_id = event.get("session_id")
                
            # Collect all messages
            self.messages.append(event)
            
            # Capture final result
            if event.get("type") == "result":
                self.final_result = event
                
            return event
            
        except json.JSONDecodeError as e:
            print(f"Failed to parse JSON: {line}")
            return None


class PhaseOrchestrator:
    """Orchestrates execution of isolated phases using Claude Code CLI"""
    
    def __init__(self, project_name: str, working_dir: Optional[str] = None, verbose: bool = False):
        self.project_name = project_name
        self.working_dir = Path(working_dir) if working_dir else Path.cwd()
        self.verbose = verbose
        self.phases: List[Phase] = []
        self.session_manager = {}  # phase_name -> session_id
        self.checkpoints_dir = self.working_dir / ".cc_automator" / "checkpoints"
        self.evidence_dir = self.working_dir / ".cc_automator" / "evidence"
        self.current_milestone = None  # Will be set by runner
        
        # Create directories
        self.checkpoints_dir.mkdir(parents=True, exist_ok=True)
        self.evidence_dir.mkdir(parents=True, exist_ok=True)
        
    def add_phase(self, phase: Phase):
        """Add a phase to the execution plan"""
        # Apply think mode if specified
        if phase.think_mode:
            phase.prompt = f"{phase.think_mode} about this problem: {phase.prompt}"
        self.phases.append(phase)
        
    def execute_phase(self, phase: Phase) -> Dict[str, Any]:
        """Execute a single phase using Claude Code CLI with async completion"""
        
        # Print phase header (minimal by default)
        if hasattr(self, 'verbose') and self.verbose:
            print(f"\n{'='*60}")
            print(f"Phase: {phase.name}")
            print(f"{'='*60}")
            print(f"Description: {phase.description}")
            print(f"Think Mode: {phase.think_mode or 'None'}")
            print(f"Max Turns: {phase.max_turns}")
            print(f"Timeout: {phase.timeout_seconds}s")
            print(f"Allowed Tools: {', '.join(phase.allowed_tools)}")
            print()
        else:
            # Minimal output
            print(f"\n{'='*60}")
            print(f"Phase: {phase.name}")
            print(f"{'='*60}")
            print(f"Description: {phase.description}")
        
        # Mark phase as running
        phase.status = PhaseStatus.RUNNING
        phase.start_time = datetime.now()
        
        # For simple/fast phases, use direct execution
        if phase.name in ['lint', 'typecheck'] and phase.timeout_seconds <= 300:
            return self._execute_direct(phase)
        else:
            # Use async execution for complex phases
            return self._execute_async(phase)
    
    def _execute_direct(self, phase: Phase) -> Dict[str, Any]:
        """Direct execution for simple phases"""
        cmd = [
            "claude", "-p", phase.prompt,
            "--output-format", "json",
            "--max-turns", str(phase.max_turns),
            "--dangerously-skip-permissions"
        ]
        
        if phase.allowed_tools:
            cmd.extend(["--allowedTools", ",".join(phase.allowed_tools)])
        
        try:
            # Execute with 5-minute max timeout for direct execution
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=min(phase.timeout_seconds, 300),
                cwd=str(self.working_dir)
            )
            
            if result.returncode == 0:
                phase.status = PhaseStatus.COMPLETED
                # Try to parse JSON output
                try:
                    result_data = json.loads(result.stdout)
                    phase.session_id = result_data.get("session_id")
                    phase.cost_usd = result_data.get("cost_usd", 0.0)
                    phase.duration_ms = result_data.get("duration_ms", 0)
                except json.JSONDecodeError:
                    phase.session_id = "unknown"
                    phase.cost_usd = 0.0
                    phase.duration_ms = 0
            else:
                phase.status = PhaseStatus.FAILED
                phase.error = f"Command failed: {result.stderr}"
                
        except subprocess.TimeoutExpired:
            phase.status = PhaseStatus.TIMEOUT
            phase.error = f"Phase timed out after {min(phase.timeout_seconds, 300)} seconds"
        except Exception as e:
            phase.status = PhaseStatus.FAILED
            phase.error = f"Execution error: {str(e)}"
            
        finally:
            phase.end_time = datetime.now()
            self._save_checkpoint(phase)
            self._save_milestone_evidence(phase)
            self._print_phase_summary(phase)
            
        return self._phase_to_dict(phase)
    
    def _execute_async(self, phase: Phase) -> Dict[str, Any]:
        """Async execution with completion markers"""
        
        # Create completion markers
        markers_dir = self.working_dir / ".cc_automator"
        markers_dir.mkdir(exist_ok=True)
        
        completion_marker = markers_dir / f"phase_{phase.name}_complete"
        error_marker = markers_dir / f"phase_{phase.name}_error"
        output_file = markers_dir / f"phase_{phase.name}_output.json"
        
        # Ensure absolute paths
        completion_marker = completion_marker.absolute()
        error_marker = error_marker.absolute()
        output_file = output_file.absolute()
        
        # Clean up existing markers
        completion_marker.unlink(missing_ok=True)
        error_marker.unlink(missing_ok=True)
        output_file.unlink(missing_ok=True)
        
        # Modify prompt to include completion markers
        async_prompt = f"""{phase.prompt}

When done, create file: {completion_marker}
Write to it: PHASE_COMPLETE"""
        
        # Build command
        cmd = [
            "claude", "-p", async_prompt,
            "--output-format", "json",
            "--max-turns", str(phase.max_turns),
            "--dangerously-skip-permissions"  # Required for autonomous file operations
        ]
        
        if phase.allowed_tools:
            cmd.extend(["--allowedTools", ",".join(phase.allowed_tools)])
        
        if self.verbose:
            print(f"Starting async execution for {phase.name}")
            print(f"Completion marker: {completion_marker}")
        else:
            print(f"Starting {phase.name} phase...")
        
        try:
            # Start Claude Code process
            process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                cwd=str(self.working_dir)
            )
            
            # Check for immediate errors
            time.sleep(2)
            if process.poll() is not None:
                stdout, stderr = process.communicate()
                print(f"Process exited immediately with code {process.returncode}")
                print(f"STDOUT: {stdout}")
                print(f"STDERR: {stderr}")
                phase.status = PhaseStatus.FAILED
                phase.error = f"Process exited immediately: {stderr or stdout}"
                return self._phase_to_dict(phase)
            
            # Poll for completion
            poll_interval = 15  # Check every 15 seconds
            max_polls = phase.timeout_seconds // poll_interval
            
            for poll_count in range(max_polls):
                # Check for completion FIRST
                if completion_marker.exists():
                    print(f"✓ Phase {phase.name} completed!")
                    process.terminate()
                    process.wait()
                    
                    phase.status = PhaseStatus.COMPLETED
                    if output_file.exists():
                        try:
                            phase.evidence = output_file.read_text()
                        except Exception:
                            phase.evidence = "Phase completed successfully"
                    
                    # Extract session info from stdout if available
                    try:
                        stdout_output = process.stdout.read()
                        if stdout_output:
                            result_data = json.loads(stdout_output)
                            phase.session_id = result_data.get("session_id", "async")
                            phase.cost_usd = result_data.get("cost_usd", 0.0)
                            phase.duration_ms = result_data.get("duration_ms", 0)
                    except Exception:
                        phase.session_id = "async"
                        phase.cost_usd = 0.0
                        phase.duration_ms = 0
                    
                    break
                    
                # Check if process finished
                if process.poll() is not None:
                    # Process exited, but check one more time for marker
                    time.sleep(1)
                    if completion_marker.exists():
                        print(f"✓ Phase {phase.name} completed (found marker after exit)!")
                        phase.status = PhaseStatus.COMPLETED
                    else:
                        print(f"Process exited without creating completion marker")
                        stdout, stderr = process.communicate()
                        phase.status = PhaseStatus.FAILED
                        phase.error = f"Process exited without completion: {stderr or stdout}"
                    break
                    
                # Check for errors
                if error_marker.exists():
                    print(f"✗ Phase {phase.name} reported errors")
                    process.terminate()
                    process.wait()
                    
                    phase.status = PhaseStatus.FAILED
                    try:
                        phase.error = error_marker.read_text()
                    except Exception:
                        phase.error = "Phase failed with unknown error"
                    
                    break
                
                # Show progress
                elapsed = (poll_count + 1) * poll_interval
                print(f"Phase {phase.name} running... ({elapsed}s elapsed, checking {completion_marker.name})")
                time.sleep(poll_interval)
            
            else:
                # Timeout reached
                print(f"✗ Phase {phase.name} timed out after {phase.timeout_seconds}s")
                process.kill()
                process.wait()
                phase.status = PhaseStatus.TIMEOUT
                phase.error = f"Phase timed out after {phase.timeout_seconds} seconds"
            
        except Exception as e:
            phase.status = PhaseStatus.FAILED
            phase.error = f"Execution error: {str(e)}"
            
        finally:
            phase.end_time = datetime.now()
            self._save_checkpoint(phase)
            self._save_milestone_evidence(phase)
            self._print_phase_summary(phase)
            
        return self._phase_to_dict(phase)
    
    def _stream_with_timeout(self, process: subprocess.Popen, timeout: int) -> Generator[str, None, None]:
        """Stream output with timeout handling"""
        start_time = time.time()
        
        for line in process.stdout:
            if time.time() - start_time > timeout:
                raise subprocess.TimeoutExpired(process.args, timeout)
            yield line
            
    def _handle_stream_event(self, event: Dict[str, Any], phase: Phase):
        """Handle a streaming event"""
        event_type = event.get("type")
        
        if event_type == "assistant":
            # Claude's response
            content = event.get("message", {}).get("content", "")
            if content:
                print(f"Claude: {content[:100]}..." if len(content) > 100 else f"Claude: {content}")
                
        elif event_type == "user":
            # Tool use or user message
            pass
            
        elif event_type == "system":
            subtype = event.get("subtype")
            if subtype == "init":
                print(f"Session ID: {event.get('session_id')}")
                print(f"Tools available: {', '.join(event.get('tools', []))}")
                
    def _print_phase_summary(self, phase: Phase):
        """Print summary of phase execution"""
        duration = (phase.end_time - phase.start_time).total_seconds() if phase.start_time and phase.end_time else 0
        
        status_symbol = {
            PhaseStatus.COMPLETED: "✓",
            PhaseStatus.FAILED: "✗",
            PhaseStatus.TIMEOUT: "⏱",
            PhaseStatus.SKIPPED: "○",
            PhaseStatus.PENDING: "○",
            PhaseStatus.RUNNING: "⚡"
        }
        
        print(f"\n{status_symbol[phase.status]} Phase {phase.name}: {phase.status.value}")
        
        if phase.session_id:
            print(f"  Session ID: {phase.session_id}")
        if phase.cost_usd > 0:
            print(f"  Cost: ${phase.cost_usd:.4f}")
        if phase.duration_ms > 0:
            print(f"  Claude Duration: {phase.duration_ms}ms")
        if duration > 0:
            print(f"  Total Duration: {duration:.1f}s")
        if phase.error:
            print(f"  Error: {phase.error}")
            
    def _save_checkpoint(self, phase: Phase):
        """Save phase checkpoint for recovery"""
        checkpoint_file = self.checkpoints_dir / f"{phase.name}_checkpoint.json"
        checkpoint_data = self._phase_to_dict(phase)
        
        with open(checkpoint_file, 'w') as f:
            json.dump(checkpoint_data, f, indent=2, default=str)
            
    def _save_milestone_evidence(self, phase: Phase):
        """Save phase output to milestone directory for next phases"""
        if not self.current_milestone or phase.status != PhaseStatus.COMPLETED:
            return
            
        # Only save evidence for key phases
        if phase.name not in ["research", "planning", "implement"]:
            return
            
        milestone_dir = self.working_dir / ".cc_automator" / "milestones" / f"milestone_{self.current_milestone}"
        milestone_dir.mkdir(parents=True, exist_ok=True)
        
        evidence_file = milestone_dir / f"{phase.name}.md"
        
        # Get the actual output
        output_content = ""
        
        # Check phase outputs directory
        phase_output_file = self.working_dir / ".cc_automator" / "phase_outputs" / f"milestone_{self.current_milestone}_{phase.name}.md"
        if phase_output_file.exists():
            output_content = phase_output_file.read_text()
        elif phase.evidence:
            output_content = phase.evidence
            
        # For implement phase, also capture what was built
        if phase.name == "implement" and not output_content:
            files_created = []
            
            # Check main.py
            main_py = self.working_dir / "main.py"
            if main_py.exists():
                files_created.append(f"## main.py\n```python\n{main_py.read_text()}\n```\n")
                
            # Check src directory
            src_dir = self.working_dir / "src"
            if src_dir.exists():
                for py_file in src_dir.glob("**/*.py"):
                    rel_path = py_file.relative_to(self.working_dir)
                    files_created.append(f"## {rel_path}\n```python\n{py_file.read_text()}\n```\n")
                    
            if files_created:
                output_content = "# Implementation Output\n\n" + "\n".join(files_created)
                
        # Save the evidence
        if output_content:
            with open(evidence_file, 'w') as f:
                f.write(output_content)
            if self.verbose:
                print(f"  Saved evidence to: {evidence_file}")
            
    def _phase_to_dict(self, phase: Phase) -> Dict[str, Any]:
        """Convert phase to dictionary"""
        return {
            "name": phase.name,
            "description": phase.description,
            "status": phase.status.value,
            "session_id": phase.session_id,
            "cost_usd": phase.cost_usd,
            "duration_ms": phase.duration_ms,
            "error": phase.error,
            "start_time": phase.start_time.isoformat() if phase.start_time else None,
            "end_time": phase.end_time.isoformat() if phase.end_time else None,
            "think_mode": phase.think_mode
        }
    
    def execute_all(self) -> Dict[str, Any]:
        """Execute all phases sequentially"""
        
        print(f"\n{'#'*60}")
        print(f"# {self.project_name}")
        print(f"# Total Phases: {len(self.phases)}")
        print(f"# Working Directory: {self.working_dir}")
        print(f"{'#'*60}")
        
        start_time = datetime.now()
        results = []
        
        for i, phase in enumerate(self.phases, 1):
            print(f"\n[{i}/{len(self.phases)}] Starting {phase.name}")
            
            result = self.execute_phase(phase)
            results.append(result)
            
            # Stop if phase failed
            if phase.status in [PhaseStatus.FAILED, PhaseStatus.TIMEOUT]:
                print(f"\n❌ Stopping execution due to {phase.status.value} in phase '{phase.name}'")
                break
                
        # Final summary
        end_time = datetime.now()
        total_duration = (end_time - start_time).total_seconds()
        total_cost = sum(p.cost_usd for p in self.phases)
        completed_count = sum(1 for p in self.phases if p.status == PhaseStatus.COMPLETED)
        
        print(f"\n{'#'*60}")
        print(f"# Execution Summary")
        print(f"{'#'*60}")
        print(f"Completed: {completed_count}/{len(self.phases)} phases")
        print(f"Total Cost: ${total_cost:.4f}")
        print(f"Total Duration: {total_duration:.1f}s")
        print(f"Success: {all(p.status == PhaseStatus.COMPLETED for p in self.phases)}")
        
        return {
            "project_name": self.project_name,
            "start_time": start_time.isoformat(),
            "end_time": end_time.isoformat(),
            "total_duration_seconds": total_duration,
            "total_cost_usd": total_cost,
            "phases": results,
            "success": all(p.status == PhaseStatus.COMPLETED for p in self.phases)
        }
    
    def resume_from_checkpoint(self) -> Optional[str]:
        """Find the last successful phase to resume from"""
        for phase in reversed(self.phases):
            checkpoint_file = self.checkpoints_dir / f"{phase.name}_checkpoint.json"
            if checkpoint_file.exists():
                with open(checkpoint_file) as f:
                    checkpoint = json.load(f)
                    if checkpoint["status"] == PhaseStatus.COMPLETED.value:
                        return phase.name
        return None


# Default phase configurations based on specification
# Format: (name, description, allowed_tools, think_mode, max_turns_override)
PHASE_CONFIGS = [
    ("research",     "Analyze requirements and explore solutions", ["Read", "Grep", "Bash"], "think harder", None),
    ("planning",     "Create detailed implementation plan", ["Read", "Write"], "think hard", None),
    ("implement",    "Build the solution", ["Read", "Write", "Edit", "MultiEdit"], "think", 60),  # Give more turns for complex implementations
    ("lint",         "Fix code style issues (flake8)", ["Read", "Edit", "Bash"], None, 20),
    ("typecheck",    "Fix type errors (mypy --strict)", ["Read", "Edit", "Bash"], None, 20),
    ("test",         "Fix unit tests (pytest)", ["Read", "Write", "Edit", "Bash"], "think", 40),
    ("integration",  "Fix integration tests", ["Read", "Write", "Edit", "Bash"], "think", 40),
    ("e2e",          "Verify main.py runs successfully", ["Read", "Bash", "Write"], "think hard", None),
    ("commit",       "Create git commit with changes", ["Bash", "Read"], None, 10)
]


def create_phase(name: str, description: str, prompt: str, 
                 allowed_tools: Optional[List[str]] = None, 
                 think_mode: Optional[str] = None,
                 max_turns: Optional[int] = None) -> Phase:
    """Helper to create a phase with defaults from PHASE_CONFIGS"""
    
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
            elif config_max_turns is not None:
                phase.max_turns = config_max_turns
            return phase
    
    # Default if not found
    phase = Phase(name=name, description=description, prompt=prompt,
                  allowed_tools=allowed_tools, think_mode=think_mode)
    if max_turns is not None:
        phase.max_turns = max_turns
    return phase


if __name__ == "__main__":
    # Example usage
    orchestrator = PhaseOrchestrator("Test Project", ".")
    
    # Add a simple test phase
    test_phase = create_phase(
        "research",
        "Research the project structure",
        "List all Python files in this directory and summarize what this project does."
    )
    
    orchestrator.add_phase(test_phase)
    results = orchestrator.execute_all()
    
    print(f"\nFinal results saved to .cc_automator/checkpoints/")