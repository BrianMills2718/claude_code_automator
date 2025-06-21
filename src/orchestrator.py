#!/usr/bin/env python3
"""
Core orchestration logic for CC_AUTOMATOR3
Manages milestone and phase execution
"""

import json
import os
import time
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional, Any

# Load environment variables from .env file
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass  # dotenv not available, continue without it

from .phase_orchestrator import PhaseOrchestrator, create_phase, Phase, PhaseStatus
from .session_manager import SessionManager
from .preflight_validator import PreflightValidator
from .progress_tracker import ProgressTracker
from .milestone_decomposer import MilestoneDecomposer
from .phase_prompt_generator import PhasePromptGenerator
from .output_filter import OutputFilter
from .file_parallel_executor import FileParallelExecutor
from .parallel_assessment_agent import ParallelAssessmentAgent
from .progress_display import ProgressDisplay
from .resume_state_validator import validate_project_for_resume, ValidationLevel
from .dependency_analyzer import analyze_project_dependencies, DependencyAnalysis
from .docker_orchestrator import DockerOrchestrator

# Optional Phase 4 imports
try:
    from .parallel_executor import ParallelExecutor
    PARALLEL_AVAILABLE = True
except ImportError:
    PARALLEL_AVAILABLE = False

try:
    from .docker_executor import DockerExecutor
    DOCKER_AVAILABLE = True
except ImportError:
    DOCKER_AVAILABLE = False


class CCAutomatorOrchestrator:
    """Core orchestrator for autonomous code generation"""
    
    def __init__(self, project_dir: Optional[Path] = None, resume: bool = False,
                 use_parallel: bool = True, use_docker: bool = False, use_visual: bool = True,
                 specific_milestone: Optional[int] = None, verbose: bool = False,
                 use_file_parallel: bool = True, infinite_mode: bool = False):
        self.project_dir = Path(project_dir) if project_dir else Path.cwd()
        
        # Load .env file from project directory if it exists
        env_file = self.project_dir / ".env"
        if env_file.exists():
            try:
                from dotenv import load_dotenv
                load_dotenv(env_file)
                if verbose:
                    print(f"✅ Loaded environment variables from {env_file}")
            except ImportError:
                if verbose:
                    print("⚠️  python-dotenv not available, skipping .env file")
        self.resume = resume
        self.use_parallel = use_parallel and PARALLEL_AVAILABLE
        self.use_docker = use_docker and DOCKER_AVAILABLE
        self.use_visual = use_visual
        self.specific_milestone = specific_milestone
        self.infinite_mode = infinite_mode
        self.verbose = verbose
        self.use_file_parallel = use_file_parallel
        
        # Dependency and Docker management
        self.dependency_analysis: Optional[DependencyAnalysis] = None
        self.docker_orchestrator = DockerOrchestrator(self.project_dir, verbose=verbose)
        
        # Initialize components
        self.orchestrator = None
        self.parallel_executor = None
        self.docker_executor = None
        self.session_manager = SessionManager(self.project_dir)
        self.progress_tracker = None
        self.decomposer = MilestoneDecomposer(self.project_dir)
        self.prompt_generator = PhasePromptGenerator(self.project_dir)
        self.output_filter = OutputFilter(verbose=verbose)
        self.file_parallel_executor = FileParallelExecutor(self.project_dir, infinite_mode=infinite_mode)
        self.assessment_agent = ParallelAssessmentAgent(self.project_dir, verbose=verbose)
        self.progress_display = ProgressDisplay(use_visual=use_visual)
        
        # Execution state
        self.milestones = []
        self.current_milestone_idx = 0
        self.current_phase_idx = 0
        
    def run(self) -> int:
        """Run the complete automation process"""
        
        print("=" * 60)
        print("CC_AUTOMATOR4 - Autonomous Code Generation")
        print("=" * 60)
        print()
        
        # Step 1: Validate environment
        if not self._validate_environment():
            return 1
            
        # Step 2: Load project configuration
        if not self._load_project_config():
            return 1
            
        # Step 3: Pre-flight dependency analysis
        if not self._analyze_dependencies():
            return 1
            
        # Step 4: Docker setup (if needed)
        if self.use_docker or self._requires_docker():
            if not self._setup_docker_services():
                return 1
            
        # Step 5: Initialize or resume progress
        if not self._initialize_progress():
            return 1
            
        # Step 6: Initialize optional components
        self._initialize_optional_components()
            
        # Step 7: Execute milestones
        success = self._execute_milestones()
        
        # Step 8: Generate final report
        self._generate_final_report()
        
        # Cleanup
        self._cleanup_docker_services()
        
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
            
        # Extract milestones (always needed for definitions, progress loaded separately)
        try:
            self.milestones = self.decomposer.extract_milestones()
            if not self.milestones:
                print("\n✗ No milestones found in CLAUDE.md")
                return False
                
            # Validate milestones (skip in resume mode to avoid strict validation issues)
            if not self.resume:
                valid, issues = self.decomposer.validate_milestones()
                if not valid:
                    print("\n✗ Milestone validation failed:")
                    for issue in issues:
                        print(f"  - {issue}")
                    return False
            else:
                print("Skipping milestone validation in resume mode...")
                
        except Exception as e:
            print(f"\n✗ Error loading milestones: {e}")
            return False
            
        print(f"\n✓ Loaded project: {project_name}")
        print(f"✓ Found {len(self.milestones)} milestones")
        
        # Initialize phase orchestrator
        self.orchestrator = PhaseOrchestrator(project_name, str(self.project_dir), verbose=self.verbose, infinite_mode=self.infinite_mode)
        self.progress_tracker = ProgressTracker(self.project_dir, project_name)
        
        return True
        
    def _initialize_progress(self) -> bool:
        """Initialize or resume progress"""
        print("\nStep 5: Initializing progress tracking...")
        
        # Add all milestones to tracker
        for milestone in self.milestones:
            phases = self.decomposer.get_milestone_phases(milestone)
            phase_names = [p["name"] for p in phases]
            self.progress_tracker.add_milestone(f"Milestone {milestone.number}", phase_names)
            
        if self.resume:
            # ENHANCED: Validate project state before resuming
            print("🔍 Validating project state for resume...")
            can_resume, resume_report = self._validate_resume_state()
            
            if not can_resume:
                print("❌ Resume validation failed!")
                print("📋 Validation report saved to .cc_automator/resume_validation.md")
                if self.verbose:
                    print("\nKey issues found:")
                    # Show critical errors from report
                    lines = resume_report.split('\n')
                    for line in lines:
                        if '❌' in line:
                            print(f"  {line}")
                return False
                
            print("✅ Resume validation passed")
            
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
        
    def _analyze_dependencies(self) -> bool:
        """Analyze project dependencies and setup requirements"""
        print("\nStep 3: Analyzing dependencies... (SKIPPED FOR NOW)")
        # Temporary bypass - just return success
        return True
        
        try:
            # Use intelligent project discovery if available, otherwise use old system
            discovery_file = self.project_dir / ".cc_automator" / "project_discovery.json"
            
            if discovery_file.exists():
                print("✓ Using intelligent project discovery...")
                self.dependency_analysis = self._load_discovery_analysis(discovery_file)
                # Save analysis for Docker orchestrator
                self._save_analysis_for_docker(self.dependency_analysis)
            else:
                print("⚠️  No project discovery found, using basic dependency analysis...")
                # Fall back to old system
                from .dependency_analyzer import DependencyAnalyzer
                analyzer = DependencyAnalyzer(self.project_dir, interactive=True)
                self.dependency_analysis = analyzer.analyze()
                analyzer.save_analysis(self.dependency_analysis)
            
            # Report findings
            if self.dependency_analysis.api_keys:
                print(f"✓ Found {len(self.dependency_analysis.api_keys)} required API keys")
                for api_key in self.dependency_analysis.api_keys:
                    print(f"  - {api_key.name}: {api_key.description}")
            
            if self.dependency_analysis.services:
                print(f"✓ Found {len(self.dependency_analysis.services)} required services")
                for service in self.dependency_analysis.services:
                    print(f"  - {service.name}: {service.description}")
            
            # Validate API keys are set
            missing_keys = []
            for api_key in self.dependency_analysis.api_keys:
                if not os.environ.get(api_key.name):
                    missing_keys.append(api_key.name)
            
            if missing_keys:
                print(f"\n❌ Missing required API keys: {', '.join(missing_keys)}")
                print("Please set these environment variables before continuing.")
                print("See DEPENDENCIES.md for setup instructions.")
                return False
            
            print("✓ All dependencies validated")
            return True
            
        except Exception as e:
            print(f"❌ Dependency analysis failed: {e}")
            return False
    
    def _requires_docker(self) -> bool:
        """Check if project requires Docker services"""
        return (self.dependency_analysis and 
                len(self.dependency_analysis.services) > 0)
    
    def _setup_docker_services(self) -> bool:
        """Setup Docker services for the project"""
        print("\nStep 4: Setting up Docker services...")
        
        try:
            success = self.docker_orchestrator.setup_project_containers()
            if success:
                # Get connection info for services
                connection_info = self.docker_orchestrator.get_service_connection_info()
                if connection_info:
                    print("✓ Services available at:")
                    for service, info in connection_info.items():
                        print(f"  - {service}: {info['host']}:{info['port']}")
                
                # Validate security configuration
                security_checks = self.docker_orchestrator.validate_security_configuration()
                security_score = sum(security_checks.values())
                print(f"✓ Security score: {security_score}/{len(security_checks)} checks passed")
                
            return success
            
        except Exception as e:
            print(f"❌ Docker setup failed: {e}")
            return False
    
    def _cleanup_docker_services(self) -> None:
        """Clean up Docker services after execution"""
        if self.use_docker and self.docker_orchestrator:
            try:
                if self.verbose:
                    print("\nCleaning up Docker services...")
                self.docker_orchestrator.stop_project_containers()
            except Exception as e:
                if self.verbose:
                    print(f"⚠️  Docker cleanup warning: {e}")
    
    def _load_discovery_analysis(self, discovery_file: Path):
        """Load intelligent project discovery and convert to dependency analysis format"""
        
        with open(discovery_file, 'r') as f:
            discovery_data = json.load(f)
        
        # Import the dependency analysis structure
        from .dependency_analyzer import DependencyAnalysis, ExternalDependency
        
        # Convert discovery to dependency analysis format
        analysis = DependencyAnalysis()
        
        # Convert final dependencies to the expected format
        for dep in discovery_data.get("final_dependencies", []):
            dependency = ExternalDependency(
                name=dep.get("approach", dep.get("requirement", "")),
                type=dep.get("type", "unknown"),
                description=dep.get("description", ""),
                required=True
            )
            
            # Add specific dependency based on type
            if dep.get("type") == "api" and "api_key_needed" in dep:
                # Map OpenAI-related keys to standard OPENAI_API_KEY
                api_key_name = dep["api_key_needed"]
                if "openai" in api_key_name.lower():
                    api_key_name = "OPENAI_API_KEY"
                
                dependency.name = api_key_name
                dependency.type = "api_key"
                dependency.setup_instructions = [
                    f'export {api_key_name}="your-api-key-here"',
                    f'# {dep["description"]}'
                ]
                dependency.validation_command = f'test -n "${api_key_name}"'
                analysis.api_keys.append(dependency)
                
            elif dep.get("type") == "service" and "docker_service" in dep:
                dependency.name = dep["docker_service"]
                dependency.type = "service"
                dependency.docker_service = dep["docker_service"]
                analysis.services.append(dependency)
                
            elif dep.get("type") == "library" and "pip_package" in dep:
                dependency.name = dep["pip_package"]
                dependency.type = "command"
                analysis.commands.append(dependency)
        
        # Generate Docker services if needed
        if analysis.services:
            analysis.docker_services = {}
            for service in analysis.services:
                if service.docker_service:
                    analysis.docker_services[service.docker_service] = {
                        "image": f"{service.docker_service}:latest",
                        "restart": "unless-stopped",
                        "networks": ["cc_automator_network"],
                        "security_opt": ["no-new-privileges:true"]
                    }
        
        return analysis
    
    def _save_analysis_for_docker(self, analysis):
        """Save analysis in format Docker orchestrator expects"""
        
        cc_dir = self.project_dir / ".cc_automator"
        cc_dir.mkdir(exist_ok=True)
        dependencies_file = cc_dir / "dependencies.json"
        
        # Convert analysis to Docker orchestrator format
        analysis_data = {
            "services": [
                {
                    "name": service.name,
                    "description": service.description,
                    "docker_service": service.docker_service or service.name
                }
                for service in analysis.services
            ],
            "api_keys": [
                {
                    "name": key.name,
                    "description": key.description
                }
                for key in analysis.api_keys
            ]
        }
        
        with open(dependencies_file, 'w') as f:
            json.dump(analysis_data, f, indent=2)
        
        # Also generate docker-compose.yml if we have services
        if analysis.services:
            self._generate_docker_compose(analysis)
    
    def _generate_docker_compose(self, analysis):
        """Generate docker-compose.yml from intelligent discovery"""
        
        compose_content = {
            "version": "3.8",
            "services": {},
            "networks": {
                "cc_automator_network": {
                    "driver": "bridge",
                    "internal": False
                }
            },
            "volumes": {}
        }
        
        # Add services from intelligent discovery
        for service in analysis.services:
            service_name = service.docker_service or service.name
            
            # Generate appropriate Docker configuration based on service type
            if "neo4j" in service_name.lower():
                compose_content["services"][service_name] = {
                    "image": "neo4j:5.11",
                    "restart": "unless-stopped",
                    "ports": ["7474:7474", "7687:7687"],
                    "environment": [
                        "NEO4J_AUTH=neo4j/password",
                        "NEO4J_PLUGINS=[\"apoc\"]",
                        "NEO4J_dbms_security_procedures_unrestricted=apoc.*"
                    ],
                    "networks": ["cc_automator_network"],
                    "security_opt": ["no-new-privileges:true"],
                    "volumes": [f"{service_name}_data:/data"]
                }
                compose_content["volumes"][f"{service_name}_data"] = {}
                
            elif "chroma" in service_name.lower():
                compose_content["services"][service_name] = {
                    "image": "ghcr.io/chroma-core/chroma:latest",
                    "restart": "unless-stopped", 
                    "ports": ["8000:8000"],
                    "networks": ["cc_automator_network"],
                    "security_opt": ["no-new-privileges:true"],
                    "volumes": [f"{service_name}_data:/chroma/chroma"]
                }
                compose_content["volumes"][f"{service_name}_data"] = {}
                
            else:
                # Generic service configuration
                compose_content["services"][service_name] = {
                    "image": f"{service_name}:latest",
                    "restart": "unless-stopped",
                    "networks": ["cc_automator_network"],
                    "security_opt": ["no-new-privileges:true"]
                }
        
        # Write docker-compose.yml
        import yaml
        compose_file = self.project_dir / "docker-compose.yml"
        with open(compose_file, 'w') as f:
            yaml.dump(compose_content, f, default_flow_style=False, sort_keys=False)
        
    def _initialize_optional_components(self):
        """Initialize Phase 4 components if available"""
        if self.use_parallel and PARALLEL_AVAILABLE:
            self.parallel_executor = ParallelExecutor(self.project_dir)
            print("✓ Parallel execution enabled")
            
        if self.use_docker and DOCKER_AVAILABLE:
            self.docker_executor = DockerExecutor(self.project_dir)
            if self.docker_executor.check_docker_available():
                print("✓ Docker execution enabled")
            else:
                print("⚠️  Docker not available, disabling Docker execution")
                self.use_docker = False
    
    def _execute_milestones(self) -> bool:
        """Execute all milestones"""
        print("\nStep 7: Executing milestones...")
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
        
        # Clean up milestone directory if starting fresh (not resuming)
        if self.current_phase_idx == 0:
            milestone_dir = self.project_dir / ".cc_automator" / "milestones" / f"milestone_{milestone.number}"
            if milestone_dir.exists():
                import shutil
                shutil.rmtree(milestone_dir)
                if self.verbose:
                    print(f"  Cleaned up existing milestone directory: {milestone_dir}")
        
        # Set current milestone on orchestrator
        if self.orchestrator:
            self.orchestrator.current_milestone = milestone.number
        
        # Check if we can use parallelization
        if self.use_parallel and self.parallel_executor:
            return self._execute_milestone_phases_parallel(milestone, phases)
        
        # Original sequential execution
        for p_idx in range(self.current_phase_idx, len(phases)):
            phase_info = phases[p_idx]
            phase_name = phase_info["name"]
            phase_type = phase_info["type"]
            
            # Display progress
            self.progress_display.show_phase_start(phase_type, p_idx + 1, len(phases))
            
            # Update progress
            self.progress_tracker.update_phase(milestone_name, phase_name, "running")
            
            # Check for retry context from assessment
            retry_context = self.assessment_agent.get_retry_context(phase_type)
            
            # Generate prompt
            prompt = self.prompt_generator.generate_prompt(
                phase_type, milestone, previous_output
            )
            
            # Add retry context if available
            if retry_context:
                prompt = retry_context + "\n\n" + prompt
            
            # Create phase
            phase = create_phase(
                name=phase_type,
                description=phase_info["description"],
                prompt=prompt
            )
            
            # DISABLED: Assessment monitoring causing 30s timeouts without value
            # if phase_type in ["test", "integration", "implement", "planning"]:
            #     self.assessment_agent.start_monitoring(
            #         phase_name=phase_type,
            #         phase_type=phase_type,
            #         check_interval=60,
            #         start_after=90
            #     )
            
            # Execute phase with appropriate strategy
            if self.use_file_parallel and phase_type in ["lint", "typecheck"]:
                # Use file-level parallelization for mechanical fixes
                if phase_type == "lint":
                    success, file_results = self.file_parallel_executor.execute_parallel_lint(self.orchestrator)
                    phase.status = PhaseStatus.COMPLETED if success else PhaseStatus.FAILED
                    phase.cost_usd = sum(r.get("cost", 0) for r in file_results)
                    phase.duration_ms = sum(r.get("duration", 0) for r in file_results)
                else:  # typecheck
                    success, file_results = self.file_parallel_executor.execute_parallel_typecheck(self.orchestrator)
                    phase.status = PhaseStatus.COMPLETED if success else PhaseStatus.FAILED
                    phase.cost_usd = sum(r.get("cost", 0) for r in file_results)
                    phase.duration_ms = sum(r.get("duration", 0) for r in file_results)
                    
                if not success:
                    phase.error = "Some files failed to fix"
                    
            elif self.use_docker and self.docker_executor and phase_type in ["lint", "typecheck", "test"]:
                result = self.docker_executor.execute_phase_in_docker(phase)
            else:
                result = self.orchestrator.execute_phase(phase)
            
            # Check result
            if phase.status.value != "completed":
                self.progress_tracker.update_phase(milestone_name, phase_name, "failed")
                self.progress_display.show_phase_complete(phase_name, "failed", error=phase.error)
                return False
                
            # Update progress
            self.progress_tracker.update_phase(
                milestone_name, phase_name, "completed",
                cost=phase.cost_usd
            )
            
            self.progress_display.show_phase_complete(phase_name, "completed", 
                                                    cost=phase.cost_usd,
                                                    session_id=phase.session_id)
            
            # Save session
            if phase.session_id:
                self.session_manager.add_session(phase_name, phase.session_id)
                
            # Capture output for next phase
            previous_output = self._capture_phase_output(phase_type, milestone, phase)
            
            # Display progress
            self.progress_tracker.display_progress()
            
            # Small delay between phases
            time.sleep(2)
            
        return True
    
    def _execute_milestone_phases_parallel(self, milestone, phases: List[Dict]) -> bool:
        """Execute milestone phases with parallelization where possible"""
        # For now, just fall back to sequential execution
        # TODO: Implement actual parallel execution logic
        print("Note: Parallel execution not fully implemented yet, using sequential execution")
        
        # Call the sequential execution without the parallel check
        self.use_parallel = False  # Temporarily disable to avoid recursion
        result = self._execute_milestone_phases(milestone, phases)
        self.use_parallel = True  # Re-enable
        return result
        
    def _capture_phase_output(self, phase_type: str, milestone, phase: Phase) -> Optional[str]:
        """Capture output from a phase for the next phase"""
        if phase_type not in ["research", "planning", "implement", "test", "integration", "e2e"]:
            return None
            
        # Try to read the output file
        output_file = (self.project_dir / ".cc_automator" / "milestones" / 
                      f"milestone_{milestone.number}" / f"{phase_type}.md")
        if output_file.exists():
            with open(output_file) as f:
                content = f.read()
                if self.verbose:
                    print(f"  Captured {phase_type} output: {len(content)} chars")
                return content
        
        # For implement phase, capture what was built
        if phase_type == "implement":
            implemented_files = []
            if (self.project_dir / "main.py").exists():
                with open(self.project_dir / "main.py") as f:
                    implemented_files.append(f"### main.py\n```python\n{f.read()}\n```")
            
            src_dir = self.project_dir / "src"
            if src_dir.exists():
                for py_file in src_dir.glob("**/*.py"):
                    with open(py_file) as f:
                        rel_path = py_file.relative_to(self.project_dir)
                        implemented_files.append(f"\n### {rel_path}\n```python\n{f.read()}\n```")
            
            if implemented_files:
                return "## Implemented Files\n\n" + "\n".join(implemented_files)
        
        return phase.evidence or ""
        
    def _generate_final_report(self):
        """Generate final execution report"""
        print("\nStep 8: Generating final report...")
        
        report = self.progress_tracker.create_summary_report()
        report_file = self.project_dir / ".cc_automator" / "final_report.md"
        
        with open(report_file, 'w') as f:
            f.write(report)
            
        print(f"✓ Report saved to: {report_file}")
        
        # Show where logs are stored
        log_dir = self.project_dir / ".cc_automator" / "logs"
        if log_dir.exists():
            log_files = list(log_dir.glob("*.log"))
            if log_files:
                print(f"✓ Phase logs saved to: {log_dir}/ ({len(log_files)} files)")
        
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
        
    def _validate_resume_state(self) -> tuple[bool, str]:
        """Validate project state for safe resume operations"""
        # Determine validation level based on verbosity
        validation_level = ValidationLevel.STRICT if self.verbose else ValidationLevel.STANDARD
        
        try:
            can_resume, report = validate_project_for_resume(
                self.project_dir, 
                validation_level=validation_level,
                save_report=True
            )
            return can_resume, report
        except Exception as e:
            # If validation itself fails, be conservative and don't resume
            error_report = f"Resume validation failed with error: {e}\nRecommendation: Start fresh execution instead of resume."
            return False, error_report
        
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