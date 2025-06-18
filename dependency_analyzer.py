#!/usr/bin/env python3
"""
Pre-flight Dependency Analyzer for CC_AUTOMATOR4
Analyzes project requirements and identifies external dependencies before execution.
"""

import re
import json
from pathlib import Path
from typing import Dict, List, Set, Optional, Any
from dataclasses import dataclass, field


@dataclass
class ExternalDependency:
    """Represents an external dependency requirement"""
    name: str
    type: str  # 'api_key', 'service', 'command', 'file'
    description: str
    required: bool = True
    setup_instructions: List[str] = field(default_factory=list)
    validation_command: Optional[str] = None
    docker_service: Optional[str] = None


@dataclass
class DependencyAnalysis:
    """Complete dependency analysis result"""
    api_keys: List[ExternalDependency] = field(default_factory=list)
    services: List[ExternalDependency] = field(default_factory=list)
    commands: List[ExternalDependency] = field(default_factory=list)
    files: List[ExternalDependency] = field(default_factory=list)
    docker_services: Dict[str, Dict[str, Any]] = field(default_factory=dict)
    setup_script: List[str] = field(default_factory=list)
    

class DependencyAnalyzer:
    """Analyzes project specifications to identify external dependencies"""
    
    def __init__(self, project_dir: Path):
        self.project_dir = project_dir
        self.claude_md = project_dir / "CLAUDE.md"
        
        # Known patterns for different dependency types
        self.api_key_patterns = {
            r'openai|gpt|chatgpt': 'OPENAI_API_KEY',
            r'anthropic|claude': 'ANTHROPIC_API_KEY', 
            r'pinecone': 'PINECONE_API_KEY',
            r'hugging\s*face|hf': 'HUGGINGFACE_API_KEY',
            r'google|gemini': 'GOOGLE_API_KEY',
            r'azure': 'AZURE_OPENAI_API_KEY',
            r'cohere': 'COHERE_API_KEY',
            r'langchain': 'OPENAI_API_KEY',
        }
        
        self.service_patterns = {
            r'redis': ('redis', 'redis:7-alpine'),
            r'postgres|postgresql': ('postgres', 'postgres:15-alpine'),
            r'mongodb|mongo': ('mongodb', 'mongo:7'),
            r'elasticsearch|elastic': ('elasticsearch', 'elasticsearch:8.11.0'),
            r'vector\s+database|embeddings': ('chroma', 'chromadb/chroma:latest'),
            r'mysql': ('mysql', 'mysql:8.0'),
            r'nginx': ('nginx', 'nginx:alpine'),
        }
        
    def analyze(self) -> DependencyAnalysis:
        """Perform complete dependency analysis"""
        analysis = DependencyAnalysis()
        
        if not self.claude_md.exists():
            return analysis
            
        content = self.claude_md.read_text().lower()
        
        # Analyze API key requirements
        analysis.api_keys = self._analyze_api_keys(content)
        
        # Analyze service requirements 
        analysis.services = self._analyze_services(content)
        
        # Analyze command requirements
        analysis.commands = self._analyze_commands(content)
        
        # Analyze file requirements
        analysis.files = self._analyze_files(content)
        
        # Generate Docker services configuration
        analysis.docker_services = self._generate_docker_services(analysis.services)
        
        # Generate setup script
        analysis.setup_script = self._generate_setup_script(analysis)
        
        return analysis
    
    def _analyze_api_keys(self, content: str) -> List[ExternalDependency]:
        """Detect required API keys from project description"""
        api_keys = []
        
        for pattern, key_name in self.api_key_patterns.items():
            if re.search(pattern, content, re.IGNORECASE):
                api_keys.append(ExternalDependency(
                    name=key_name,
                    type='api_key',
                    description=f'API key for {pattern} integration',
                    setup_instructions=[
                        f'export {key_name}="your-api-key-here"',
                        f'# Or add to .env file: {key_name}=your-api-key-here'
                    ],
                    validation_command=f'test -n "${key_name}"'
                ))
        
        return api_keys
    
    def _analyze_services(self, content: str) -> List[ExternalDependency]:
        """Detect required external services"""
        services = []
        
        for pattern, (service_name, docker_image) in self.service_patterns.items():
            if re.search(pattern, content, re.IGNORECASE):
                services.append(ExternalDependency(
                    name=service_name,
                    type='service',
                    description=f'{service_name.title()} database/service',
                    setup_instructions=[
                        f'docker run -d --name {service_name} -p {self._get_default_port(service_name)}:{self._get_default_port(service_name)} {docker_image}',
                        f'# Or use docker-compose (recommended)'
                    ],
                    validation_command=f'docker ps | grep {service_name}',
                    docker_service=service_name
                ))
        
        return services
    
    def _analyze_commands(self, content: str) -> List[ExternalDependency]:
        """Detect required system commands/tools"""
        commands = []
        
        # Common command patterns
        command_patterns = {
            r'docker': 'docker',
            r'git': 'git',
            r'curl': 'curl',
            r'wget': 'wget',
        }
        
        for pattern, cmd in command_patterns.items():
            if re.search(pattern, content, re.IGNORECASE):
                commands.append(ExternalDependency(
                    name=cmd,
                    type='command',
                    description=f'{cmd} command line tool',
                    setup_instructions=[f'# Install {cmd} via package manager'],
                    validation_command=f'command -v {cmd}'
                ))
        
        return commands
    
    def _analyze_files(self, content: str) -> List[ExternalDependency]:
        """Detect required files or models"""
        files = []
        
        # Model download patterns
        if re.search(r'model|embedding|download', content, re.IGNORECASE):
            files.append(ExternalDependency(
                name='models',
                type='file',
                description='Pre-trained models or embeddings',
                setup_instructions=[
                    '# Models will be downloaded automatically on first run',
                    '# Ensure sufficient disk space (1-5GB typical)'
                ],
                required=False
            ))
        
        return files
    
    def _generate_docker_services(self, services: List[ExternalDependency]) -> Dict[str, Dict[str, Any]]:
        """Generate docker-compose service definitions"""
        docker_services = {}
        
        for service in services:
            if service.docker_service:
                docker_services[service.name] = self._get_docker_config(service.name)
        
        return docker_services
    
    def _get_docker_config(self, service_name: str) -> Dict[str, Any]:
        """Get secure Docker configuration for a service"""
        configs = {
            'redis': {
                'image': 'redis:7-alpine',
                'ports': ['6379:6379'],
                'environment': ['REDIS_PASSWORD=secure_password'],
                'command': 'redis-server --requirepass secure_password',
                'volumes': ['redis_data:/data'],
                'restart': 'unless-stopped',
                'networks': ['cc_automator_network'],
                'security_opt': ['no-new-privileges:true'],
                'user': '999:999'
            },
            'postgres': {
                'image': 'postgres:15-alpine',
                'ports': ['5432:5432'], 
                'environment': [
                    'POSTGRES_DB=app_db',
                    'POSTGRES_USER=app_user',
                    'POSTGRES_PASSWORD=secure_password'
                ],
                'volumes': ['postgres_data:/var/lib/postgresql/data'],
                'restart': 'unless-stopped',
                'networks': ['cc_automator_network'],
                'security_opt': ['no-new-privileges:true']
            },
            'mongodb': {
                'image': 'mongo:7',
                'ports': ['27017:27017'],
                'environment': [
                    'MONGO_INITDB_ROOT_USERNAME=admin',
                    'MONGO_INITDB_ROOT_PASSWORD=secure_password'
                ],
                'volumes': ['mongodb_data:/data/db'],
                'restart': 'unless-stopped',
                'networks': ['cc_automator_network'],
                'security_opt': ['no-new-privileges:true']
            }
        }
        
        return configs.get(service_name, {
            'image': f'{service_name}:latest',
            'restart': 'unless-stopped',
            'networks': ['cc_automator_network'],
            'security_opt': ['no-new-privileges:true']
        })
    
    def _get_default_port(self, service_name: str) -> str:
        """Get default port for a service"""
        ports = {
            'redis': '6379',
            'postgres': '5432',
            'mongodb': '27017',
            'elasticsearch': '9200',
            'mysql': '3306',
            'nginx': '80'
        }
        return ports.get(service_name, '8080')
    
    def _generate_setup_script(self, analysis: DependencyAnalysis) -> List[str]:
        """Generate setup script commands"""
        script = []
        
        # Header
        script.append('#!/bin/bash')
        script.append('# CC_AUTOMATOR4 Dependency Setup Script')
        script.append('set -e  # Exit on any error')
        script.append('')
        
        # API key validation
        if analysis.api_keys:
            script.append('echo "Validating API keys..."')
            for api_key in analysis.api_keys:
                script.append(f'if [ -z "${{{api_key.name}}}" ]; then')
                script.append(f'  echo "ERROR: {api_key.name} environment variable not set"')
                script.append('  exit 1')
                script.append('fi')
            script.append('')
        
        # Docker services
        if analysis.docker_services:
            script.append('echo "Starting Docker services..."')
            script.append('docker-compose up -d')
            script.append('')
            
            # Wait for services to be ready
            script.append('echo "Waiting for services to be ready..."')
            for service in analysis.services:
                if service.docker_service:
                    script.append(f'until docker exec {service.name} {self._get_health_check(service.name)}; do')
                    script.append('  echo "Waiting for service to be ready..."')
                    script.append('  sleep 2')
                    script.append('done')
            script.append('')
        
        # Final validation
        script.append('echo "All dependencies validated successfully!"')
        
        return script
    
    def _get_health_check(self, service_name: str) -> str:
        """Get health check command for a service"""
        checks = {
            'redis': 'redis-cli ping',
            'postgres': 'pg_isready -U app_user',
            'mongodb': 'mongosh --eval "db.runCommand({ping:1})"'
        }
        return checks.get(service_name, 'echo "ok"')
    
    def save_analysis(self, analysis: DependencyAnalysis) -> None:
        """Save dependency analysis to project files"""
        
        # Save DEPENDENCIES.md
        self._save_dependencies_md(analysis)
        
        # Save docker-compose.yml
        if analysis.docker_services:
            self._save_docker_compose(analysis)
        
        # Save setup script
        self._save_setup_script(analysis)
        
        # Save analysis JSON for programmatic access
        self._save_analysis_json(analysis)
    
    def _save_dependencies_md(self, analysis: DependencyAnalysis) -> None:
        """Save human-readable dependencies documentation"""
        deps_file = self.project_dir / "DEPENDENCIES.md"
        
        content = []
        content.append("# Project Dependencies")
        content.append("")
        content.append("This project requires the following external dependencies:")
        content.append("")
        
        if analysis.api_keys:
            content.append("## API Keys (Required)")
            for api_key in analysis.api_keys:
                content.append(f"- `{api_key.name}`: {api_key.description}")
            content.append("")
            
        if analysis.services:
            content.append("## External Services")
            for service in analysis.services:
                content.append(f"- **{service.name.title()}**: {service.description}")
            content.append("")
            
        if analysis.commands:
            content.append("## Required Commands")
            for cmd in analysis.commands:
                content.append(f"- `{cmd.name}`: {cmd.description}")
            content.append("")
            
        content.append("## Quick Setup")
        content.append("")
        content.append("1. Set environment variables:")
        content.append("```bash")
        for api_key in analysis.api_keys:
            content.append(f'export {api_key.name}="your-key-here"')
        content.append("```")
        content.append("")
        
        if analysis.docker_services:
            content.append("2. Start services:")
            content.append("```bash")
            content.append("docker-compose up -d")
            content.append("```")
            content.append("")
            
        content.append("3. Run setup validation:")
        content.append("```bash")
        content.append("./setup.sh")
        content.append("```")
        content.append("")
        
        content.append("## Manual Validation")
        content.append("")
        for api_key in analysis.api_keys:
            if api_key.validation_command:
                content.append(f"Check {api_key.name}: `{api_key.validation_command}`")
        content.append("")
        
        deps_file.write_text("\n".join(content))
    
    def _save_docker_compose(self, analysis: DependencyAnalysis) -> None:
        """Save secure docker-compose.yml"""
        compose_file = self.project_dir / "docker-compose.yml"
        
        compose_config = {
            'version': '3.8',
            'services': analysis.docker_services,
            'networks': {
                'cc_automator_network': {
                    'driver': 'bridge',
                    'internal': False  # Allow external access for API calls
                }
            },
            'volumes': {}
        }
        
        # Add volume definitions
        for service_config in analysis.docker_services.values():
            if 'volumes' in service_config:
                for volume in service_config['volumes']:
                    volume_name = volume.split(':')[0]
                    compose_config['volumes'][volume_name] = {
                        'driver': 'local'
                    }
        
        # Convert to YAML format (simple implementation)
        yaml_content = self._dict_to_yaml(compose_config)
        compose_file.write_text(yaml_content)
    
    def _save_setup_script(self, analysis: DependencyAnalysis) -> None:
        """Save executable setup script"""
        setup_file = self.project_dir / "setup.sh"
        setup_file.write_text("\n".join(analysis.setup_script))
        setup_file.chmod(0o755)  # Make executable
    
    def _save_analysis_json(self, analysis: DependencyAnalysis) -> None:
        """Save analysis for programmatic access"""
        analysis_file = self.project_dir / ".cc_automator" / "dependencies.json"
        analysis_file.parent.mkdir(exist_ok=True)
        
        # Convert to JSON-serializable format
        data = {
            'api_keys': [vars(dep) for dep in analysis.api_keys],
            'services': [vars(dep) for dep in analysis.services], 
            'commands': [vars(dep) for dep in analysis.commands],
            'files': [vars(dep) for dep in analysis.files],
            'docker_services': analysis.docker_services
        }
        
        with open(analysis_file, 'w') as f:
            json.dump(data, f, indent=2)
    
    def _dict_to_yaml(self, data: Any, indent: int = 0) -> str:
        """Simple YAML serialization"""
        lines = []
        prefix = "  " * indent
        
        if isinstance(data, dict):
            for key, value in data.items():
                if isinstance(value, dict):
                    lines.append(f"{prefix}{key}:")
                    lines.append(self._dict_to_yaml(value, indent + 1))
                elif isinstance(value, list):
                    lines.append(f"{prefix}{key}:")
                    for item in value:
                        if isinstance(item, str):
                            lines.append(f"{prefix}  - {item}")
                        else:
                            lines.append(f"{prefix}  -")
                            lines.append(self._dict_to_yaml(item, indent + 2))
                else:
                    lines.append(f"{prefix}{key}: {value}")
        
        return "\n".join(lines)


def analyze_project_dependencies(project_dir: Path) -> DependencyAnalysis:
    """Main entry point for dependency analysis"""
    analyzer = DependencyAnalyzer(project_dir)
    analysis = analyzer.analyze()
    analyzer.save_analysis(analysis)
    return analysis


if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1:
        project_path = Path(sys.argv[1])
    else:
        project_path = Path.cwd()
    
    print(f"Analyzing dependencies for: {project_path}")
    analysis = analyze_project_dependencies(project_path)
    
    print(f"Found {len(analysis.api_keys)} API keys, {len(analysis.services)} services")
    print("Check DEPENDENCIES.md for details")