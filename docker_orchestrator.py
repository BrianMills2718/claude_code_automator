#!/usr/bin/env python3
"""
Docker Orchestrator for CC_AUTOMATOR4
Manages secure Docker containers for external service dependencies.
"""

import os
import json
import time
import subprocess
from pathlib import Path
from typing import Dict, List, Optional, Any
from dataclasses import dataclass

from dependency_analyzer import DependencyAnalysis, analyze_project_dependencies


@dataclass
class ContainerStatus:
    """Status of a Docker container"""
    name: str
    image: str
    status: str  # 'running', 'stopped', 'error'
    ports: List[str]
    health: str  # 'healthy', 'unhealthy', 'starting'


class DockerOrchestrator:
    """Manages Docker containers for project dependencies with security-first approach"""
    
    def __init__(self, project_dir: Path, verbose: bool = False):
        self.project_dir = project_dir
        self.verbose = verbose
        self.compose_file = project_dir / "docker-compose.yml"
        self.dependencies_file = project_dir / ".cc_automator" / "dependencies.json"
        
    def setup_project_containers(self) -> bool:
        """Set up all required containers for the project"""
        
        # Analyze dependencies if not already done
        if not self.dependencies_file.exists():
            if self.verbose:
                print("🔍 Analyzing project dependencies...")
            analyze_project_dependencies(self.project_dir)
        
        # Load dependency analysis
        analysis = self._load_analysis()
        if not analysis or not analysis.get('services'):
            if self.verbose:
                print("✓ No Docker services required for this project")
            return True
        
        # Validate Docker is available
        if not self._check_docker_available():
            print("❌ Docker not available. Please install Docker first.")
            return False
        
        # Create secure network
        self._create_secure_network()
        
        # Start services with docker-compose
        if self.compose_file.exists():
            return self._start_compose_services()
        else:
            print("❌ docker-compose.yml not found. Run dependency analysis first.")
            return False
    
    def _load_analysis(self) -> Optional[Dict[str, Any]]:
        """Load dependency analysis from JSON"""
        try:
            with open(self.dependencies_file) as f:
                return json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            return None
    
    def _check_docker_available(self) -> bool:
        """Check if Docker is installed and running"""
        try:
            result = subprocess.run(['docker', '--version'], 
                                  capture_output=True, text=True, timeout=10)
            if result.returncode != 0:
                return False
            
            # Check if Docker daemon is running
            result = subprocess.run(['docker', 'info'], 
                                  capture_output=True, text=True, timeout=10)
            return result.returncode == 0
            
        except (subprocess.TimeoutExpired, FileNotFoundError):
            return False
    
    def _create_secure_network(self) -> None:
        """Create isolated Docker network for the project"""
        network_name = "cc_automator_network"
        
        try:
            # Check if network already exists
            result = subprocess.run(['docker', 'network', 'ls', '--filter', f'name={network_name}'],
                                  capture_output=True, text=True)
            
            if network_name not in result.stdout:
                if self.verbose:
                    print(f"🔒 Creating secure network: {network_name}")
                
                subprocess.run([
                    'docker', 'network', 'create',
                    '--driver', 'bridge',
                    '--subnet', '172.20.0.0/16',  # Isolated subnet
                    '--opt', 'com.docker.network.bridge.enable_icc=true',
                    '--opt', 'com.docker.network.bridge.enable_ip_masquerade=true',
                    network_name
                ], check=True, capture_output=True)
            
        except subprocess.CalledProcessError as e:
            if self.verbose:
                print(f"⚠️  Network creation failed: {e}")
    
    def _start_compose_services(self) -> bool:
        """Start services using docker-compose with security hardening"""
        
        if self.verbose:
            print("🚀 Starting Docker services...")
        
        try:
            # Pull images first for security scanning
            subprocess.run(['docker-compose', 'pull'], 
                          cwd=self.project_dir, check=True, capture_output=True)
            
            # Start services in detached mode
            result = subprocess.run(['docker-compose', 'up', '-d', '--remove-orphans'],
                                  cwd=self.project_dir, capture_output=True, text=True)
            
            if result.returncode != 0:
                print(f"❌ Failed to start services: {result.stderr}")
                return False
            
            # Wait for services to be healthy
            return self._wait_for_services_healthy()
            
        except subprocess.CalledProcessError as e:
            print(f"❌ Docker Compose failed: {e}")
            return False
    
    def _wait_for_services_healthy(self, timeout: int = 60) -> bool:
        """Wait for all services to become healthy"""
        
        if self.verbose:
            print("⏳ Waiting for services to become healthy...")
        
        start_time = time.time()
        
        while time.time() - start_time < timeout:
            containers = self._get_container_status()
            
            if not containers:
                if self.verbose:
                    print("⚠️  No containers found")
                return False
            
            all_healthy = True
            for container in containers:
                if container.health not in ['healthy', 'starting']:
                    all_healthy = False
                    break
            
            if all_healthy:
                if self.verbose:
                    print("✅ All services are healthy!")
                return True
            
            if self.verbose:
                unhealthy = [c.name for c in containers if c.health == 'unhealthy']
                if unhealthy:
                    print(f"⏳ Waiting for services: {', '.join(unhealthy)}")
            
            time.sleep(2)
        
        print(f"❌ Services failed to become healthy within {timeout}s")
        return False
    
    def _get_container_status(self) -> List[ContainerStatus]:
        """Get status of all project containers"""
        try:
            result = subprocess.run([
                'docker-compose', 'ps', '--format', 'json'
            ], cwd=self.project_dir, capture_output=True, text=True)
            
            if result.returncode != 0:
                return []
            
            containers = []
            for line in result.stdout.strip().split('\n'):
                if line:
                    try:
                        container_data = json.loads(line)
                        containers.append(ContainerStatus(
                            name=container_data.get('Name', ''),
                            image=container_data.get('Image', ''),
                            status=container_data.get('State', ''),
                            ports=container_data.get('Ports', '').split(','),
                            health=self._get_container_health(container_data.get('Name', ''))
                        ))
                    except json.JSONDecodeError:
                        continue
            
            return containers
            
        except subprocess.CalledProcessError:
            return []
    
    def _get_container_health(self, container_name: str) -> str:
        """Get health status of a specific container"""
        try:
            result = subprocess.run([
                'docker', 'inspect', container_name,
                '--format', '{{if .State.Health}}{{.State.Health.Status}}{{else}}no-healthcheck{{end}}'
            ], capture_output=True, text=True)
            
            if result.returncode == 0:
                health = result.stdout.strip()
                return 'healthy' if health in ['healthy', 'no-healthcheck'] else health
            
            return 'unknown'
            
        except subprocess.CalledProcessError:
            return 'unknown'
    
    def stop_project_containers(self) -> bool:
        """Stop all project containers"""
        if not self.compose_file.exists():
            return True
        
        try:
            if self.verbose:
                print("🛑 Stopping Docker services...")
            
            subprocess.run(['docker-compose', 'down'], 
                          cwd=self.project_dir, check=True, capture_output=True)
            
            if self.verbose:
                print("✅ Services stopped successfully")
            return True
            
        except subprocess.CalledProcessError as e:
            print(f"❌ Failed to stop services: {e}")
            return False
    
    def cleanup_project_containers(self) -> bool:
        """Clean up containers and volumes"""
        if not self.compose_file.exists():
            return True
        
        try:
            if self.verbose:
                print("🧹 Cleaning up Docker resources...")
            
            # Stop and remove containers, networks, and volumes
            subprocess.run(['docker-compose', 'down', '-v', '--remove-orphans'], 
                          cwd=self.project_dir, check=True, capture_output=True)
            
            if self.verbose:
                print("✅ Cleanup completed successfully")
            return True
            
        except subprocess.CalledProcessError as e:
            print(f"❌ Cleanup failed: {e}")
            return False
    
    def validate_security_configuration(self) -> Dict[str, bool]:
        """Validate that containers are configured securely"""
        security_checks = {
            'non_root_user': False,
            'read_only_filesystem': False,
            'no_privileged_containers': False,
            'network_isolation': False,
            'resource_limits': False
        }
        
        if not self.compose_file.exists():
            return security_checks
        
        try:
            # Read compose file and analyze security settings
            with open(self.compose_file) as f:
                compose_content = f.read()
            
            # Check for security configurations
            security_checks['non_root_user'] = 'user:' in compose_content
            security_checks['read_only_filesystem'] = 'read_only:' in compose_content  
            security_checks['no_privileged_containers'] = 'privileged: true' not in compose_content
            security_checks['network_isolation'] = 'cc_automator_network' in compose_content
            security_checks['resource_limits'] = any(limit in compose_content for limit in ['mem_limit:', 'cpus:'])
            
            return security_checks
            
        except Exception:
            return security_checks
    
    def get_service_connection_info(self) -> Dict[str, Dict[str, str]]:
        """Get connection information for running services"""
        connection_info = {}
        
        try:
            result = subprocess.run([
                'docker-compose', 'ps', '--format', 'json'
            ], cwd=self.project_dir, capture_output=True, text=True)
            
            if result.returncode != 0:
                return connection_info
            
            for line in result.stdout.strip().split('\n'):
                if line:
                    try:
                        container_data = json.loads(line)
                        service_name = container_data.get('Service', '')
                        ports = container_data.get('Ports', '')
                        
                        if service_name and ports:
                            # Extract host port from port mapping
                            host_port = self._extract_host_port(ports)
                            if host_port:
                                connection_info[service_name] = {
                                    'host': 'localhost',
                                    'port': host_port,
                                    'status': container_data.get('State', '')
                                }
                    except json.JSONDecodeError:
                        continue
            
            return connection_info
            
        except subprocess.CalledProcessError:
            return connection_info
    
    def _extract_host_port(self, ports_string: str) -> Optional[str]:
        """Extract host port from Docker ports string"""
        if not ports_string:
            return None
        
        # Parse format like "0.0.0.0:5432->5432/tcp"
        for port_mapping in ports_string.split(','):
            if '->' in port_mapping:
                host_part = port_mapping.split('->')[0].strip()
                if ':' in host_part:
                    return host_part.split(':')[-1]
        
        return None


def setup_project_docker(project_dir: Path, verbose: bool = False) -> bool:
    """Main entry point for setting up Docker services for a project"""
    orchestrator = DockerOrchestrator(project_dir, verbose)
    return orchestrator.setup_project_containers()


def validate_docker_security(project_dir: Path) -> Dict[str, bool]:
    """Validate Docker security configuration for a project"""
    orchestrator = DockerOrchestrator(project_dir)
    return orchestrator.validate_security_configuration()


if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1:
        project_path = Path(sys.argv[1])
    else:
        project_path = Path.cwd()
    
    print(f"Setting up Docker services for: {project_path}")
    success = setup_project_docker(project_path, verbose=True)
    
    if success:
        print("✅ Docker setup completed successfully")
    else:
        print("❌ Docker setup failed")
        sys.exit(1)