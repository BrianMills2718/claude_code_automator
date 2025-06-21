#!/usr/bin/env python3
"""
Pre-flight Dependency Analyzer for CC_AUTOMATOR4
Analyzes project requirements and identifies external dependencies before execution.
"""

import re
import json
import sys
from pathlib import Path
from typing import Dict, List, Set, Optional, Any
from dataclasses import dataclass, field


@dataclass
class DependencyOption:
    """Represents a potential solution for a dependency requirement"""
    name: str
    description: str
    approach: str  # 'api', 'local', 'library', 'service'
    setup_requirements: List[str]
    pros: List[str]
    cons: List[str]
    recommended_for: str
    complexity: str  # 'simple', 'moderate', 'complex'
    cost: str  # 'free', 'paid', 'freemium'


@dataclass
class ExternalDependency:
    """Represents an external dependency requirement"""
    name: str
    type: str  # 'capability' (LLM, vector storage, etc), 'service', 'command', 'file'
    description: str
    required: bool = True
    capability_needed: Optional[str] = None  # 'language_model', 'vector_database', etc.
    available_options: List[DependencyOption] = field(default_factory=list)
    recommended_option: Optional[str] = None
    selected_option: Optional[str] = None
    setup_instructions: List[str] = field(default_factory=list)
    validation_command: Optional[str] = None
    docker_service: Optional[str] = None


@dataclass
class DependencyAnalysis:
    """Complete dependency analysis result"""
    capabilities: List[ExternalDependency] = field(default_factory=list)
    services: List[ExternalDependency] = field(default_factory=list)
    commands: List[ExternalDependency] = field(default_factory=list)
    files: List[ExternalDependency] = field(default_factory=list)
    api_keys: List[ExternalDependency] = field(default_factory=list)  # Derived from selected capabilities
    docker_services: Dict[str, Dict[str, Any]] = field(default_factory=dict)
    setup_script: List[str] = field(default_factory=list)
    

class DependencyAnalyzer:
    """Analyzes project specifications to identify external dependencies"""
    
    def __init__(self, project_dir: Path, interactive: bool = True):
        self.project_dir = project_dir
        self.claude_md = project_dir / "CLAUDE.md"
        self.interactive = interactive
        
        # Capability detection patterns - what the project needs to do
        self.capability_patterns = {
            r'language model|llm|gpt|claude|text generation|natural language|langchain': 'language_model',
            r'vector database|embeddings|vector search|semantic search|chroma': 'vector_database',
            r'graph database|knowledge graph|networkx|neo4j': 'graph_database',
            r'redis|cache|session': 'caching',
            r'postgres|mysql|database|sql': 'relational_database',
            r'elasticsearch|search engine|full.?text search': 'search_engine',
        }
        
    def analyze(self) -> DependencyAnalysis:
        """Perform intelligent dependency analysis with interactive selection"""
        analysis = DependencyAnalysis()
        
        if not self.claude_md.exists():
            return analysis
            
        content = self.claude_md.read_text()
        
        # 1. Detect required capabilities
        detected_capabilities = self._detect_capabilities(content)
        
        # 2. Research options for each capability  
        for capability in detected_capabilities:
            capability_dep = self._research_capability_options(capability, content)
            if capability_dep:
                analysis.capabilities.append(capability_dep)
        
        # 3. Interactive selection (if enabled)
        if self.interactive and analysis.capabilities:
            self._interactive_capability_selection(analysis)
        
        # 4. Generate concrete dependencies from selections
        self._generate_concrete_dependencies(analysis)
        
        # 5. Analyze other requirements (commands, files)
        analysis.commands = self._analyze_commands(content)
        analysis.files = self._analyze_files(content)
        
        # 6. Generate Docker services configuration
        analysis.docker_services = self._generate_docker_services(analysis.services)
        
        # 7. Generate setup script
        analysis.setup_script = self._generate_setup_script(analysis)
        
        return analysis
    
    def _detect_capabilities(self, content: str) -> List[str]:
        """Detect what capabilities the project needs"""
        detected = []
        content_lower = content.lower()
        
        for pattern, capability in self.capability_patterns.items():
            if re.search(pattern, content_lower, re.IGNORECASE):
                if capability not in detected:
                    detected.append(capability)
        
        return detected
    
    def _research_capability_options(self, capability: str, project_content: str) -> Optional[ExternalDependency]:
        """Research available options for a capability and provide intelligent recommendations"""
        
        if capability == 'language_model':
            return self._research_language_model_options(project_content)
        elif capability == 'vector_database':
            return self._research_vector_database_options(project_content)
        elif capability == 'graph_database':
            return self._research_graph_database_options(project_content)
        elif capability == 'caching':
            return self._research_caching_options(project_content)
        elif capability == 'relational_database':
            return self._research_relational_database_options(project_content)
        
        return None
    
    def _research_language_model_options(self, project_content: str) -> ExternalDependency:
        """Research LLM options with intelligent recommendations based on project needs"""
        
        # Analyze project to determine best recommendations
        project_lower = project_content.lower()
        is_rag_system = any(term in project_lower for term in ['rag', 'retrieval', 'knowledge', 'graph'])
        needs_reasoning = any(term in project_lower for term in ['reasoning', 'analysis', 'complex'])
        is_production = any(term in project_lower for term in ['production', 'enterprise', 'scale'])
        
        options = [
            DependencyOption(
                name="openai",
                description="OpenAI GPT models (GPT-4, GPT-3.5)",
                approach="api",
                setup_requirements=["OPENAI_API_KEY"],
                pros=["Highest quality outputs", "Fast response times", "Excellent reasoning", "Large context windows"],
                cons=["Paid service", "Requires internet", "Data sent to OpenAI"],
                recommended_for="Production systems requiring highest quality",
                complexity="simple",
                cost="paid"
            ),
            DependencyOption(
                name="anthropic",
                description="Anthropic Claude models",
                approach="api", 
                setup_requirements=["ANTHROPIC_API_KEY"],
                pros=["Excellent reasoning", "Strong safety", "Good for analysis", "Large context"],
                cons=["Paid service", "Requires internet", "Data sent to Anthropic"],
                recommended_for="Complex reasoning and analysis tasks",
                complexity="simple",
                cost="paid"
            ),
            DependencyOption(
                name="ollama",
                description="Local LLM execution with Ollama",
                approach="local",
                setup_requirements=["ollama installed", "model downloaded"],
                pros=["Free to use", "Data stays local", "No internet required", "Good for development"],
                cons=["Slower than APIs", "Requires powerful hardware", "Setup complexity", "Lower quality"],
                recommended_for="Development, privacy-sensitive applications",
                complexity="moderate",
                cost="free"
            ),
            DependencyOption(
                name="spacy",
                description="spaCy NLP library (non-generative)",
                approach="library",
                setup_requirements=["spacy installed", "language model downloaded"],
                pros=["Fast", "Free", "Good for NER/parsing", "Works offline"],
                cons=["No text generation", "Limited understanding", "Not suitable for RAG"],
                recommended_for="Basic NLP tasks, entity extraction only",
                complexity="simple",
                cost="free"
            )
        ]
        
        # Intelligent recommendation logic
        if is_rag_system and is_production:
            recommended = "openai"
            recommendation_reason = "RAG systems benefit from high-quality language models, and OpenAI provides excellent performance for production use"
        elif needs_reasoning:
            recommended = "anthropic"
            recommendation_reason = "Claude excels at reasoning tasks and complex analysis"
        elif "development" in project_lower or "prototype" in project_lower:
            recommended = "ollama"
            recommendation_reason = "For development/prototyping, local models provide good balance of capability and cost"
        else:
            recommended = "openai"
            recommendation_reason = "OpenAI provides the best general-purpose language model capabilities"
        
        return ExternalDependency(
            name="language_model",
            type="capability",
            description="Language model for text understanding and generation",
            capability_needed="language_model",
            available_options=options,
            recommended_option=recommended,
            setup_instructions=[f"Recommended: {recommended} - {recommendation_reason}"]
        )
    
    def _research_vector_database_options(self, project_content: str) -> ExternalDependency:
        """Research vector database options"""
        options = [
            DependencyOption(
                name="chroma",
                description="ChromaDB vector database",
                approach="service",
                setup_requirements=["Docker container"],
                pros=["Easy setup", "Good for development", "Python-native", "Free"],
                cons=["Less scalable than alternatives"],
                recommended_for="Development and small-scale applications",
                complexity="simple",
                cost="free"
            ),
            DependencyOption(
                name="pinecone",
                description="Pinecone cloud vector database",
                approach="api",
                setup_requirements=["PINECONE_API_KEY"],
                pros=["Highly scalable", "Managed service", "Good performance"],
                cons=["Paid service", "Vendor lock-in"],
                recommended_for="Production applications with scale requirements",
                complexity="simple",
                cost="paid"
            ),
            DependencyOption(
                name="in_memory",
                description="In-memory vector storage (simple)",
                approach="library",
                setup_requirements=["numpy", "faiss (optional)"],
                pros=["No external dependencies", "Fast for small datasets", "Free"],
                cons=["Data not persistent", "Limited scalability", "No advanced features"],
                recommended_for="Prototyping and small datasets",
                complexity="simple",
                cost="free"
            )
        ]
        
        # Simple recommendation: in-memory for development, Chroma for most cases
        is_production = "production" in project_content.lower()
        recommended = "pinecone" if is_production else "chroma"
        
        return ExternalDependency(
            name="vector_database",
            type="capability", 
            description="Vector database for embeddings and semantic search",
            capability_needed="vector_database",
            available_options=options,
            recommended_option=recommended,
            setup_instructions=[f"Recommended: {recommended} for your use case"]
        )
    
    def _research_graph_database_options(self, project_content: str) -> ExternalDependency:
        """Research graph database options"""
        # For now, keep it simple - most projects use NetworkX for graph operations
        options = [
            DependencyOption(
                name="networkx",
                description="NetworkX Python library",
                approach="library",
                setup_requirements=["pip install networkx"],
                pros=["Simple to use", "Good for analysis", "Free", "Pure Python"],
                cons=["Not optimized for large graphs", "No persistence"],
                recommended_for="Most graph analysis tasks",
                complexity="simple",
                cost="free"
            )
        ]
        
        return ExternalDependency(
            name="graph_database", 
            type="capability",
            description="Graph database for knowledge graph operations",
            capability_needed="graph_database",
            available_options=options,
            recommended_option="networkx",
            setup_instructions=["NetworkX is sufficient for most graph operations"]
        )
    
    def _interactive_capability_selection(self, analysis: DependencyAnalysis) -> None:
        """Present options to user and get their selections"""
        
        print("\n" + "="*60)
        print("🤖 DEPENDENCY ANALYSIS - Interactive Setup")
        print("="*60)
        print(f"Detected {len(analysis.capabilities)} capabilities that need configuration:\n")
        
        for capability in analysis.capabilities:
            print(f"📋 {capability.description.upper()}")
            print("-" * 50)
            
            # Show intelligent recommendation first
            if capability.recommended_option:
                recommended_option = next(
                    (opt for opt in capability.available_options if opt.name == capability.recommended_option), 
                    None
                )
                if recommended_option:
                    print(f"🎯 RECOMMENDED: {recommended_option.description}")
                    print(f"   Reason: {capability.setup_instructions[0].split(' - ', 1)[1] if ' - ' in capability.setup_instructions[0] else 'Best general choice'}")
                    print()
            
            # Show all options
            print("Available options:")
            for i, option in enumerate(capability.available_options, 1):
                marker = "⭐" if option.name == capability.recommended_option else "  "
                print(f"{marker} {i}. {option.description}")
                print(f"      Cost: {option.cost.title()} | Complexity: {option.complexity.title()}")
                print(f"      Pros: {', '.join(option.pros[:2])}")
                print(f"      Best for: {option.recommended_for}")
                print()
            
            # Get user choice
            while True:
                try:
                    default_choice = next(
                        (i for i, opt in enumerate(capability.available_options, 1) 
                         if opt.name == capability.recommended_option), 1
                    )
                    
                    choice = input(f"Choose option [1-{len(capability.available_options)}] (default: {default_choice}): ").strip()
                    
                    if not choice:
                        choice = default_choice
                    else:
                        choice = int(choice)
                    
                    if 1 <= choice <= len(capability.available_options):
                        selected_option = capability.available_options[choice - 1]
                        capability.selected_option = selected_option.name
                        print(f"✅ Selected: {selected_option.description}\n")
                        break
                    else:
                        print(f"Please enter a number between 1 and {len(capability.available_options)}")
                        
                except (ValueError, KeyboardInterrupt):
                    print(f"Please enter a number between 1 and {len(capability.available_options)}")
                    
        print("="*60)
        print("✅ Configuration complete!\n")
    
    def _generate_concrete_dependencies(self, analysis: DependencyAnalysis) -> None:
        """Convert capability selections into concrete API keys and services"""
        
        for capability in analysis.capabilities:
            if not capability.selected_option:
                # Use recommended option if no selection made
                capability.selected_option = capability.recommended_option
            
            selected = next(
                (opt for opt in capability.available_options if opt.name == capability.selected_option),
                None
            )
            
            if not selected:
                continue
                
            # Generate concrete dependencies based on selection
            if selected.approach == "api":
                for req in selected.setup_requirements:
                    if req.endswith("_API_KEY"):
                        api_key_dep = ExternalDependency(
                            name=req,
                            type="api_key",
                            description=f"API key for {selected.description}",
                            setup_instructions=[
                                f'export {req}="your-api-key-here"',
                                f'# {selected.description} - {selected.recommended_for}'
                            ],
                            validation_command=f'test -n "${req}"'
                        )
                        analysis.api_keys.append(api_key_dep)
                        
            elif selected.approach == "service":
                service_dep = ExternalDependency(
                    name=capability.selected_option,
                    type="service", 
                    description=selected.description,
                    docker_service=capability.selected_option
                )
                analysis.services.append(service_dep)
    
    def _research_caching_options(self, project_content: str) -> ExternalDependency:
        """Research caching options"""
        options = [
            DependencyOption(
                name="redis",
                description="Redis in-memory cache",
                approach="service",
                setup_requirements=["Docker container"],
                pros=["Fast", "Persistent", "Feature-rich"],
                cons=["Requires setup", "Memory usage"],
                recommended_for="Most caching needs",
                complexity="simple",
                cost="free"
            )
        ]
        
        return ExternalDependency(
            name="caching",
            type="capability",
            description="Caching system for performance",
            capability_needed="caching",
            available_options=options,
            recommended_option="redis",
            setup_instructions=["Redis is the standard choice for caching"]
        )
    
    def _research_relational_database_options(self, project_content: str) -> ExternalDependency:
        """Research relational database options"""
        options = [
            DependencyOption(
                name="postgres",
                description="PostgreSQL database",
                approach="service",
                setup_requirements=["Docker container"],
                pros=["Full-featured", "Standards compliant", "Free"],
                cons=["Requires setup"],
                recommended_for="Most applications requiring SQL database",
                complexity="simple",
                cost="free"
            ),
            DependencyOption(
                name="sqlite",
                description="SQLite file database",
                approach="library",
                setup_requirements=["Built into Python"],
                pros=["No setup", "Lightweight", "Good for development"],
                cons=["Limited concurrency", "No network access"],
                recommended_for="Development and single-user applications",
                complexity="simple",
                cost="free"
            )
        ]
        
        is_production = "production" in project_content.lower()
        recommended = "postgres" if is_production else "sqlite"
        
        return ExternalDependency(
            name="relational_database",
            type="capability",
            description="Relational database for structured data",
            capability_needed="relational_database",
            available_options=options,
            recommended_option=recommended,
            setup_instructions=[f"Recommended: {recommended} for your use case"]
        )
    
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