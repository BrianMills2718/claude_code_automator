#!/usr/bin/env python3
"""
Main runner for CC_AUTOMATOR3
Orchestrates the complete autonomous development process
"""

import sys
import json
import time
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional, Any

from phase_orchestrator import PhaseOrchestrator, create_phase, Phase
from session_manager import SessionManager
from preflight_validator import PreflightValidator
from progress_tracker import ProgressTracker
from milestone_decomposer import MilestoneDecomposer
from phase_prompt_generator import PhasePromptGenerator

# Phase 4 imports
try:
    from parallel_executor import ParallelExecutor
    PARALLEL_AVAILABLE = True
except ImportError:
    PARALLEL_AVAILABLE = False

try:
    from docker_executor import DockerExecutor
    DOCKER_AVAILABLE = True
except ImportError:
    DOCKER_AVAILABLE = False

try:
    from visual_progress import VisualProgressDisplay
    VISUAL_AVAILABLE = True
except ImportError:
    VISUAL_AVAILABLE = False


class CCAutomatorRunner:
    """Main runner for autonomous code generation"""
    
    def __init__(self, project_dir: Optional[Path] = None, resume: bool = False,
                 use_parallel: bool = True, use_docker: bool = False, use_visual: bool = True,
                 specific_milestone: Optional[int] = None):
        self.project_dir = Path(project_dir) if project_dir else Path.cwd()
        self.resume = resume
        self.use_parallel = use_parallel and PARALLEL_AVAILABLE
        self.use_docker = use_docker and DOCKER_AVAILABLE
        self.use_visual = use_visual and VISUAL_AVAILABLE
        self.specific_milestone = specific_milestone
        
        # Initialize components
        self.orchestrator = None
        self.parallel_executor = None
        self.docker_executor = None
        self.visual_progress = None
        self.session_manager = SessionManager(self.project_dir)
        self.progress_tracker = None
        self.decomposer = MilestoneDecomposer(self.project_dir)
        self.prompt_generator = PhasePromptGenerator(self.project_dir)
        
        # Execution state
        self.milestones = []
        self.current_milestone_idx = 0
        self.current_phase_idx = 0
        
    def run(self) -> int:
        """Run the complete automation process"""
        
        print("=" * 60)
        print("CC_AUTOMATOR3 - Autonomous Code Generation")
        print("=" * 60)
        print()
        
        # Step 1: Validate environment
        if not self._validate_environment():
            return 1
            
        # Step 2: Load project configuration
        if not self._load_project_config():
            return 1
            
        # Step 3: Initialize or resume progress
        if not self._initialize_progress():
            return 1
            
        # Step 3.5: Initialize Phase 4 components
        if self.use_parallel:
            self.parallel_executor = ParallelExecutor(self.project_dir)
            print("✓ Parallel execution enabled")
            
        if self.use_docker:
            self.docker_executor = DockerExecutor(self.project_dir)
            if self.docker_executor.check_docker_available():
                print("✓ Docker execution enabled")
            else:
                print("⚠️  Docker not available, disabling Docker execution")
                self.use_docker = False
                
        if self.use_visual:
            self.visual_progress = VisualProgressDisplay()
            print("✓ Visual progress display enabled")
            
        # Step 4: Execute milestones
        success = self._execute_milestones()
        
        # Step 5: Generate final report
        self._generate_final_report()
        
        return 0 if success else 1
        
    def _validate_environment(self) -> bool:
        """Validate the environment is ready"""
        print("Step 1: Validating environment...")
        
        validator = PreflightValidator(self.project_dir)
        passed, errors = validator.run_all_checks()
        
        if not passed:
            print("\n✗ Environment validation failed.")
            return False
            
        print("\n✓ Environment validated successfully!")
        return True
        
    def _load_project_config(self) -> bool:
        """Load project configuration from CLAUDE.md"""
        print("\nStep 2: Loading project configuration...")
        
        claude_md = self.project_dir / "CLAUDE.md"
        if not claude_md.exists():
            print("\n✗ CLAUDE.md not found. Run setup.py first.")
            return False
            
        # Extract project name
        with open(claude_md) as f:
            first_line = f.readline().strip()
            project_name = first_line[2:] if first_line.startswith("# ") else "Project"
            
        # Extract milestones
        try:
            self.milestones = self.decomposer.extract_milestones()
            if not self.milestones:
                print("\n✗ No milestones found in CLAUDE.md")
                return False
                
            # Validate milestones
            valid, issues = self.decomposer.validate_milestones()
            if not valid:
                print("\n✗ Milestone validation failed:")
                for issue in issues:
                    print(f"  - {issue}")
                return False
                
        except Exception as e:
            print(f"\n✗ Error loading milestones: {e}")
            return False
            
        print(f"\n✓ Loaded project: {project_name}")
        print(f"✓ Found {len(self.milestones)} milestones")
        
        # Initialize orchestrator
        self.orchestrator = PhaseOrchestrator(project_name, str(self.project_dir))
        self.progress_tracker = ProgressTracker(self.project_dir, project_name)
        
        return True
        
    def _initialize_progress(self) -> bool:
        """Initialize or resume progress"""
        print("\nStep 3: Initializing progress tracking...")
        
        # Add all milestones to tracker
        for milestone in self.milestones:
            phases = self.decomposer.get_milestone_phases(milestone)
            phase_names = [p["name"] for p in phases]
            self.progress_tracker.add_milestone(f"Milestone {milestone.number}", phase_names)
            
        if self.resume:
            # Try to load existing progress
            if self.progress_tracker.load_progress():
                print("✓ Loaded existing progress")
                
                # Find resume point
                resume_point = self.progress_tracker.get_resume_point()
                if resume_point:
                    self.current_milestone_idx = resume_point["milestone"] - 1
                    self.current_phase_idx = resume_point["next_phase_index"]
                    print(f"✓ Resuming from Milestone {resume_point['milestone']}, "
                          f"Phase {self.current_phase_idx + 1}")
                else:
                    print("✓ All milestones completed!")
                    return True
            else:
                print("✓ Starting fresh (no previous progress found)")
        else:
            print("✓ Starting fresh execution")
            
        return True
    
    def _execute_milestone_phases_parallel(self, milestone, phases: List[Dict]) -> bool:
        """Execute milestone phases with parallelization where possible"""
        
        milestone_name = f"Milestone {milestone.number}"
        previous_output = None
        p_idx = 0
        
        while p_idx < len(phases):
            # Look ahead to find parallelizable phases
            parallel_group = []
            
            # Collect phases that can run in parallel
            phase_types = []
            for i in range(p_idx, min(p_idx + 4, len(phases))):  # Look ahead up to 4 phases
                phase_types.append(phases[i]["type"])
            
            # Check if we have a parallel group
            if "lint" in phase_types and "typecheck" in phase_types:
                # Lint and typecheck can run in parallel
                for i in range(p_idx, len(phases)):
                    if phases[i]["type"] in ["lint", "typecheck"]:
                        parallel_group.append(phases[i])
                    else:
                        break
            elif "test" in phase_types and "integration" in phase_types:
                # Test and integration can run in parallel
                for i in range(p_idx, len(phases)):
                    if phases[i]["type"] in ["test", "integration"]:
                        parallel_group.append(phases[i])
                    else:
                        break
            
            # Execute parallel group if found
            if len(parallel_group) > 1:
                print(f"\n🚀 Executing {len(parallel_group)} phases in parallel: {[p['type'] for p in parallel_group]}")
                
                # Create phase objects
                phase_objects = []
                for phase_info in parallel_group:
                    prompt = self.prompt_generator.generate_prompt(
                        phase_info["type"], milestone, previous_output
                    )
                    phase = create_phase(
                        name=phase_info["type"],
                        description=phase_info["description"],
                        prompt=prompt
                    )
                    phase_objects.append(phase)
                
                # Execute in parallel
                results = self.parallel_executor.execute_parallel_group(phase_objects, self.orchestrator)
                
                # Check all results
                all_success = all(r.get("status") == "completed" for r in results)
                if not all_success:
                    return False
                
                # Update progress for all parallel phases
                for phase, result in zip(phase_objects, results):
                    self.progress_tracker.update_phase(
                        milestone_name, f"milestone_{milestone.number}_{phase.name}", "completed",
                        cost=phase.cost_usd
                    )
                
                p_idx += len(parallel_group)
            else:
                # Execute single phase sequentially
                phase_info = phases[p_idx]
                phase_name = phase_info["name"]
                phase_type = phase_info["type"]
                
                print(f"\n[{p_idx + 1}/{len(phases)}] {phase_type.upper()} Phase")
                
                # Execute as normal
                prompt = self.prompt_generator.generate_prompt(
                    phase_type, milestone, previous_output
                )
                phase = create_phase(
                    name=phase_type,
                    description=phase_info["description"],
                    prompt=prompt
                )
                
                result = self.orchestrator.execute_phase(phase)
                
                if phase.status.value != "completed":
                    return False
                
                # Update progress
                self.progress_tracker.update_phase(
                    milestone_name, phase_name, "completed",
                    cost=phase.cost_usd
                )
                
                # Capture output for next phase
                if phase_type in ["research", "planning"]:
                    previous_output = phase.evidence or "Phase completed"
                
                p_idx += 1
        
        return True
        
    def _execute_milestones(self) -> bool:
        """Execute all milestones"""
        print("\nStep 4: Executing milestones...")
        print("=" * 60)
        
        total_start_time = datetime.now()
        all_success = True
        
        # Filter milestones if specific one requested
        milestones_to_run = self.milestones
        if self.specific_milestone:
            milestones_to_run = [m for m in self.milestones if m.number == self.specific_milestone]
            if not milestones_to_run:
                print(f"\n✗ Milestone {self.specific_milestone} not found")
                return False
            print(f"\nRunning only Milestone {self.specific_milestone}")
        
        for m_idx in range(self.current_milestone_idx, len(self.milestones)):
            milestone = self.milestones[m_idx]
            
            # Skip if running specific milestone and this isn't it
            if self.specific_milestone and milestone.number != self.specific_milestone:
                continue
                
            milestone_name = f"Milestone {milestone.number}"
            
            print(f"\n{'#' * 60}")
            print(f"# {milestone_name}: {milestone.name}")
            print(f"{'#' * 60}")
            
            # Start milestone
            self.progress_tracker.start_milestone(milestone_name)
            
            # Get phases for this milestone
            phases = self.decomposer.get_milestone_phases(milestone)
            
            # Execute phases
            milestone_success = self._execute_milestone_phases(milestone, phases)
            
            if not milestone_success:
                print(f"\n✗ Milestone {milestone.number} failed")
                all_success = False
                break
            else:
                print(f"\n✓ Milestone {milestone.number} completed successfully!")
                
            # Reset phase index for next milestone
            self.current_phase_idx = 0
            
        total_duration = (datetime.now() - total_start_time).total_seconds()
        
        print(f"\n{'=' * 60}")
        print(f"Total execution time: {self._format_duration(total_duration)}")
        print(f"Total cost: ${self.progress_tracker.total_cost:.4f}")
        
        return all_success
        
    def _execute_milestone_phases(self, milestone, phases: List[Dict]) -> bool:
        """Execute all phases for a milestone"""
        
        milestone_name = f"Milestone {milestone.number}"
        previous_output = None
        
        # Check if we can use parallelization
        if self.use_parallel and self.parallel_executor:
            return self._execute_milestone_phases_parallel(milestone, phases)
        
        # Original sequential execution
        for p_idx in range(self.current_phase_idx, len(phases)):
            phase_info = phases[p_idx]
            phase_name = phase_info["name"]
            phase_type = phase_info["type"]
            
            # Visual progress update
            if self.visual_progress:
                self.visual_progress.start_phase(phase_name, phase_type, p_idx + 1, len(phases))
            else:
                print(f"\n[{p_idx + 1}/{len(phases)}] {phase_type.upper()} Phase")
            
            # Update progress
            self.progress_tracker.update_phase(milestone_name, phase_name, "running")
            
            # Generate prompt
            prompt = self.prompt_generator.generate_prompt(
                phase_type, milestone, previous_output
            )
            
            # Create phase
            phase = create_phase(
                name=phase_type,
                description=phase_info["description"],
                prompt=prompt
            )
            
            # Execute phase (with Docker if enabled)
            if self.use_docker and self.docker_executor and phase_type in ["lint", "typecheck", "test"]:
                result = self.docker_executor.execute_phase_in_docker(phase)
            else:
                result = self.orchestrator.execute_phase(phase)
            
            # Check result
            if phase.status.value != "completed":
                self.progress_tracker.update_phase(milestone_name, phase_name, "failed")
                if self.visual_progress:
                    self.visual_progress.update_phase(phase_name, "failed", error=phase.error)
                return False
                
            # Update progress
            self.progress_tracker.update_phase(
                milestone_name, phase_name, "completed",
                cost=phase.cost_usd
            )
            
            if self.visual_progress:
                self.visual_progress.update_phase(phase_name, "completed", cost=phase.cost_usd,
                                                session_id=phase.session_id)
            
            # Save session
            if phase.session_id:
                self.session_manager.add_session(phase_name, phase.session_id)
                
            # For certain phases, capture output for next phase
            if phase_type in ["research", "planning"]:
                # Try to read the output file
                output_file = (self.project_dir / ".cc_automator" / "milestones" / 
                             f"milestone_{milestone.number}" / f"{phase_type}.md")
                if output_file.exists():
                    with open(output_file) as f:
                        previous_output = f.read()[:1000]  # First 1000 chars
                        
            # Display progress
            self.progress_tracker.display_progress()
            
            # Small delay between phases
            time.sleep(2)
            
        return True
        
    def _generate_final_report(self):
        """Generate final execution report"""
        print("\nStep 5: Generating final report...")
        
        report = self.progress_tracker.create_summary_report()
        report_file = self.project_dir / ".cc_automator" / "final_report.md"
        
        with open(report_file, 'w') as f:
            f.write(report)
            
        print(f"✓ Report saved to: {report_file}")
        
        # Also save detailed results
        results = {
            "project_dir": str(self.project_dir),
            "total_cost": self.progress_tracker.total_cost,
            "milestones_completed": sum(
                1 for m in self.progress_tracker.milestones.values() 
                if m.is_complete
            ),
            "total_milestones": len(self.milestones),
            "sessions": self.session_manager.get_all_sessions()
        }
        
        results_file = self.project_dir / ".cc_automator" / "execution_results.json"
        with open(results_file, 'w') as f:
            json.dump(results, f, indent=2)
            
        print(f"✓ Results saved to: {results_file}")
        
    def _format_duration(self, seconds: float) -> str:
        """Format duration in human-readable format"""
        if seconds < 60:
            return f"{int(seconds)}s"
        elif seconds < 3600:
            minutes = int(seconds / 60)
            secs = int(seconds % 60)
            return f"{minutes}m {secs}s"
        else:
            hours = int(seconds / 3600)
            minutes = int((seconds % 3600) / 60)
            return f"{hours}h {minutes}m"


def main():
    """Main entry point"""
    import argparse
    
    parser = argparse.ArgumentParser(description="Run CC_AUTOMATOR3")
    parser.add_argument("--project", type=str, help="Project directory (default: current)")
    parser.add_argument("--resume", action="store_true", help="Resume from last checkpoint")
    parser.add_argument("--milestone", type=int, help="Run specific milestone only")
    
    # Phase 4 features
    parser.add_argument("--parallel", action="store_true", default=True,
                       help="Enable parallel execution (default: enabled)")
    parser.add_argument("--no-parallel", action="store_true", 
                       help="Disable parallel execution")
    parser.add_argument("--docker", action="store_true",
                       help="Run mechanical phases in Docker containers")
    parser.add_argument("--visual", action="store_true", default=True,
                       help="Enable visual progress display (default: enabled)")
    parser.add_argument("--no-visual", action="store_true",
                       help="Disable visual progress display")
    
    args = parser.parse_args()
    
    # Determine project directory
    project_dir = Path(args.project) if args.project else Path.cwd()
    
    if not project_dir.exists():
        print(f"Error: Project directory not found: {project_dir}")
        return 1
        
    # Determine feature flags
    use_parallel = not args.no_parallel
    use_visual = not args.no_visual
        
    # Run automation
    runner = CCAutomatorRunner(
        project_dir, 
        resume=args.resume,
        use_parallel=use_parallel,
        use_docker=args.docker,
        use_visual=use_visual,
        specific_milestone=args.milestone
    )
    
    try:
        return runner.run()
    except KeyboardInterrupt:
        print("\n\nExecution interrupted by user.")
        print("You can resume with: python run.py --resume")
        return 1
    except Exception as e:
        print(f"\nUnexpected error: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())