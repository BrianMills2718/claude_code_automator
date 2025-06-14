#!/usr/bin/env python3
"""
Docker Executor for CC_AUTOMATOR3
Provides consistent execution environment using Docker
"""

import subprocess
import json
import tempfile
import time
from pathlib import Path
from typing import Dict, List, Optional

from phase_orchestrator import Phase, PhaseStatus


class DockerExecutor:
    """Executes phases in Docker containers for consistency"""
    
    # Default Docker image with Python and development tools
    DEFAULT_IMAGE = "python:3.11-slim"
    
    # Dockerfile template for custom environments
    DOCKERFILE_TEMPLATE = """
FROM {base_image}

# Install system dependencies
RUN apt-get update && apt-get install -y \\
    git \\
    build-essential \\
    && rm -rf /var/lib/apt/lists/*

# Install Python dev tools
RUN pip install --no-cache-dir \\
    flake8 \\
    mypy \\
    pytest \\
    pytest-cov \\
    black \\
    isort

# Install Claude Code CLI (if available in container)
# Note: This would need to be configured based on actual Claude Code distribution

WORKDIR /workspace
"""
    
    def __init__(self, project_dir: Path, image: Optional[str] = None):
        self.project_dir = Path(project_dir)
        self.image = image or self.DEFAULT_IMAGE
        self.container_name = f"cc_automator_{project_dir.name}_{int(time.time())}"
        
    def build_custom_image(self, requirements_file: Optional[Path] = None) -> str:
        """Build a custom Docker image for the project"""
        
        dockerfile_content = self.DOCKERFILE_TEMPLATE.format(base_image=self.image)
        
        # Add project-specific requirements
        if requirements_file and requirements_file.exists():
            dockerfile_content += f"""
# Install project requirements
COPY {requirements_file.name} /tmp/requirements.txt
RUN pip install --no-cache-dir -r /tmp/requirements.txt
"""
        
        # Create temporary Dockerfile
        with tempfile.NamedTemporaryFile(mode='w', suffix='.Dockerfile', delete=False) as f:
            f.write(dockerfile_content)
            dockerfile_path = f.name
        
        # Build image
        image_tag = f"cc_automator:{self.project_dir.name}"
        result = subprocess.run(
            ["docker", "build", "-t", image_tag, "-f", dockerfile_path, "."],
            cwd=self.project_dir,
            capture_output=True,
            text=True
        )
        
        Path(dockerfile_path).unlink()  # Clean up
        
        if result.returncode != 0:
            raise RuntimeError(f"Failed to build Docker image: {result.stderr}")
            
        return image_tag
    
    def execute_phase_in_docker(self, phase: Phase, mount_dir: Optional[Path] = None) -> Dict:
        """Execute a phase inside a Docker container"""
        
        print(f"\n🐳 Executing {phase.name} in Docker container")
        
        # Prepare mount directory
        mount_dir = mount_dir or self.project_dir
        
        # Build docker run command
        docker_cmd = [
            "docker", "run",
            "--rm",  # Remove container after execution
            "--name", self.container_name,
            "-v", f"{mount_dir.absolute()}:/workspace",
            "-w", "/workspace",
        ]
        
        # Add environment variables if needed
        if hasattr(phase, 'env_vars') and phase.env_vars:
            for key, value in phase.env_vars.items():
                docker_cmd.extend(["-e", f"{key}={value}"])
        
        # Add the image
        docker_cmd.append(self.image)
        
        # Add the phase command
        # Note: This would need to be adapted based on how Claude Code CLI works in containers
        phase_cmd = self._build_phase_command(phase)
        docker_cmd.extend(["sh", "-c", phase_cmd])
        
        try:
            # Execute in Docker
            result = subprocess.run(
                docker_cmd,
                capture_output=True,
                text=True,
                timeout=phase.timeout_seconds
            )
            
            if result.returncode == 0:
                phase.status = PhaseStatus.COMPLETED
                return {
                    "status": "completed",
                    "stdout": result.stdout,
                    "duration_seconds": 0  # Would need proper timing
                }
            else:
                phase.status = PhaseStatus.FAILED
                phase.error = result.stderr
                return {
                    "status": "failed",
                    "error": result.stderr
                }
                
        except subprocess.TimeoutExpired:
            # Kill the container
            subprocess.run(["docker", "kill", self.container_name], capture_output=True)
            phase.status = PhaseStatus.TIMEOUT
            phase.error = f"Docker execution timed out after {phase.timeout_seconds}s"
            return {
                "status": "timeout",
                "error": phase.error
            }
        except Exception as e:
            phase.status = PhaseStatus.FAILED
            phase.error = str(e)
            return {
                "status": "failed",
                "error": str(e)
            }
    
    def _build_phase_command(self, phase: Phase) -> str:
        """Build the command to execute inside Docker"""
        
        # Map phase types to actual commands
        phase_commands = {
            "lint": "flake8 --select=F --exclude=venv,__pycache__,.git",
            "typecheck": "mypy --strict .",
            "test": "pytest tests/unit -xvs",
            "integration": "pytest tests/integration -xvs",
        }
        
        # For phases that need Claude Code, we'd need a different approach
        # This is a simplified version for mechanical phases
        if phase.name in phase_commands:
            return phase_commands[phase.name]
        else:
            # Would need to handle Claude Code execution differently
            return f"echo 'Phase {phase.name} would run Claude Code here'"
    
    def check_docker_available(self) -> bool:
        """Check if Docker is available and running"""
        
        try:
            result = subprocess.run(
                ["docker", "version"],
                capture_output=True,
                text=True
            )
            return result.returncode == 0
        except FileNotFoundError:
            return False
    
    def cleanup_containers(self):
        """Clean up any running containers"""
        
        # List containers with our prefix
        result = subprocess.run(
            ["docker", "ps", "-a", "--filter", f"name=cc_automator", "--format", "{{.Names}}"],
            capture_output=True,
            text=True
        )
        
        for container in result.stdout.strip().split('\n'):
            if container:
                subprocess.run(["docker", "rm", "-f", container], capture_output=True)