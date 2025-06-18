#!/usr/bin/env python3
"""
Dynamic Project Discovery and Setup Wizard for CC_AUTOMATOR4
Intelligently discovers project requirements through conversation and research.
"""

import json
import os
from pathlib import Path
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, field

# Use Claude Code agent for intelligent research and analysis
try:
    from mcp_server import claude_research_agent
    CLAUDE_AVAILABLE = True
except ImportError:
    try:
        from simple_claude_interface import claude_research_agent_fallback as claude_research_agent
        CLAUDE_AVAILABLE = True
    except ImportError:
        CLAUDE_AVAILABLE = False


@dataclass
class ProjectRequirement:
    """A discovered requirement for the project"""
    name: str
    description: str
    why_needed: str
    approaches: List[Dict[str, Any]] = field(default_factory=list)
    recommended_approach: Optional[str] = None
    user_choice: Optional[str] = None
    priority: str = "required"  # required, recommended, optional


@dataclass
class ProjectDiscovery:
    """Result of project discovery process"""
    user_intent: str
    project_type: str
    requirements: List[ProjectRequirement] = field(default_factory=list)
    suggested_milestones: List[Dict[str, Any]] = field(default_factory=list)
    final_dependencies: List[Dict[str, Any]] = field(default_factory=list)
    

class ProjectDiscoveryWizard:
    """Interactive wizard that discovers project requirements from user intent"""
    
    def __init__(self, project_dir: Path):
        self.project_dir = project_dir
        self.discovery = ProjectDiscovery(user_intent="", project_type="")
        
    def run_discovery(self) -> ProjectDiscovery:
        """Run the complete project discovery process"""
        
        print("="*60)
        print("🤖 CC_AUTOMATOR4 - Project Discovery Wizard")
        print("="*60)
        print("Let's figure out exactly what you want to build!\n")
        
        # Step 1: Capture user intent
        self._capture_user_intent()
        
        # Step 2: Research and analyze requirements
        self._research_project_requirements()
        
        # Step 3: Interactive requirement refinement
        self._refine_requirements_with_user()
        
        # Step 4: Generate milestones based on discoveries
        self._generate_dynamic_milestones()
        
        # Step 5: Finalize dependencies
        self._finalize_dependencies()
        
        # Step 6: Save discovery results
        self._save_discovery_results()
        
        return self.discovery
    
    def _capture_user_intent(self) -> None:
        """Capture what the user wants to build"""
        
        print("📝 What would you like to build?")
        print("Examples:")
        print("  - 'A GraphRAG system for document analysis'")
        print("  - 'A FastAPI web service with authentication'") 
        print("  - 'A data pipeline that processes CSV files'")
        print("  - 'A chatbot that can answer questions about my docs'")
        print()
        
        while True:
            user_input = input("Your project idea: ").strip()
            if user_input:
                self.discovery.user_intent = user_input
                break
            print("Please describe what you'd like to build.")
        
        print(f"\n✅ Got it! You want to build: {self.discovery.user_intent}")
        print("\n🔍 Let me research what this will require...\n")
    
    def _research_project_requirements(self) -> None:
        """Use intelligent analysis to discover project requirements"""
        
        if not CLAUDE_AVAILABLE:
            # Fallback to simple analysis if Claude not available
            self._simple_requirement_analysis()
            return
        
        # Use Claude to intelligently analyze the user's intent
        research_prompt = f"""
        Analyze this project request and identify what technical capabilities will be needed:
        
        User Request: "{self.discovery.user_intent}"
        
        Please identify:
        1. What type of project this is (web API, data pipeline, ML system, etc.)
        2. What core capabilities are needed (text processing, database, web framework, etc.)
        3. For each capability, what approaches exist (API services, local libraries, cloud services)
        4. What would be the most logical milestone breakdown
        
        Be specific about WHY each capability is needed for this particular project.
        Don't assume specific technologies - research what options exist.
        
        Format as JSON with this structure:
        {{
            "project_type": "description of project type",
            "core_capabilities": [
                {{
                    "name": "capability_name",
                    "description": "what this capability does", 
                    "why_needed": "why this specific project needs it",
                    "approaches": [
                        {{
                            "name": "approach_name",
                            "description": "description",
                            "type": "api|library|service|local",
                            "pros": ["list of pros"],
                            "cons": ["list of cons"], 
                            "best_for": "when to use this approach"
                        }}
                    ],
                    "recommended": "which approach is best for this use case"
                }}
            ],
            "milestone_suggestions": [
                {{
                    "name": "milestone name",
                    "description": "what gets built",
                    "why_first": "why this should be built in this order"
                }}
            ]
        }}
        """
        
        try:
            # Get intelligent analysis from Claude
            analysis_result = claude_research_agent(research_prompt)
            self._parse_research_results(analysis_result)
            
        except Exception as e:
            print(f"⚠️  Advanced analysis failed: {e}")
            print("Falling back to simple analysis...\n")
            self._simple_requirement_analysis()
    
    def _parse_research_results(self, analysis_result: str) -> None:
        """Parse Claude's analysis into project requirements"""
        
        try:
            # Extract JSON from Claude's response
            import re
            json_match = re.search(r'\{.*\}', analysis_result, re.DOTALL)
            if json_match:
                data = json.loads(json_match.group())
            else:
                raise ValueError("No JSON found in response")
            
            self.discovery.project_type = data.get("project_type", "Unknown")
            
            # Convert capabilities to requirements
            for cap in data.get("core_capabilities", []):
                requirement = ProjectRequirement(
                    name=cap["name"],
                    description=cap["description"],
                    why_needed=cap["why_needed"],
                    approaches=[{
                        "name": approach["name"],
                        "description": approach["description"],
                        "type": approach["type"],
                        "pros": approach["pros"],
                        "cons": approach["cons"],
                        "best_for": approach["best_for"]
                    } for approach in cap.get("approaches", [])],
                    recommended_approach=cap.get("recommended")
                )
                self.discovery.requirements.append(requirement)
            
            # Store milestone suggestions
            self.discovery.suggested_milestones = data.get("milestone_suggestions", [])
            
            print(f"🎯 Project Type: {self.discovery.project_type}")
            print(f"📋 Discovered {len(self.discovery.requirements)} core capabilities needed\n")
            
        except Exception as e:
            print(f"⚠️  Could not parse analysis: {e}")
            self._simple_requirement_analysis()
    
    def _simple_requirement_analysis(self) -> None:
        """Fallback simple analysis when Claude is not available"""
        
        intent_lower = self.discovery.user_intent.lower()
        
        # Simple keyword-based detection
        if any(term in intent_lower for term in ['graphrag', 'rag', 'retrieval', 'knowledge graph']):
            self.discovery.project_type = "RAG System"
            self._add_rag_requirements()
            
        elif any(term in intent_lower for term in ['api', 'web service', 'fastapi', 'flask']):
            self.discovery.project_type = "Web API"
            self._add_web_api_requirements()
            
        elif any(term in intent_lower for term in ['pipeline', 'csv', 'data processing']):
            self.discovery.project_type = "Data Pipeline"
            self._add_data_pipeline_requirements()
            
        elif any(term in intent_lower for term in ['chatbot', 'chat', 'conversation']):
            self.discovery.project_type = "Chatbot"
            self._add_chatbot_requirements()
            
        else:
            self.discovery.project_type = "General Application"
            self._add_general_requirements()
    
    def _add_rag_requirements(self) -> None:
        """Add requirements for RAG systems"""
        
        # Text understanding capability
        self.discovery.requirements.append(ProjectRequirement(
            name="text_understanding",
            description="Ability to understand and process natural language",
            why_needed="RAG systems need to understand queries and generate responses",
            approaches=[
                {
                    "name": "openai_api",
                    "description": "OpenAI GPT models",
                    "type": "api",
                    "pros": ["Highest quality", "Fast", "Large context"],
                    "cons": ["Paid", "Requires internet", "Data sent externally"],
                    "best_for": "Production systems needing best quality"
                },
                {
                    "name": "anthropic_api", 
                    "description": "Anthropic Claude models",
                    "type": "api",
                    "pros": ["Excellent reasoning", "Safe", "Large context"],
                    "cons": ["Paid", "Requires internet", "Data sent externally"],
                    "best_for": "Complex analysis and reasoning tasks"
                },
                {
                    "name": "local_llm",
                    "description": "Local LLM with Ollama",
                    "type": "local",
                    "pros": ["Free", "Private", "No internet needed"],
                    "cons": ["Slower", "Requires powerful hardware", "Lower quality"],
                    "best_for": "Development and privacy-sensitive applications"
                }
            ],
            recommended_approach="anthropic_api"
        ))
        
        # Vector search capability
        self.discovery.requirements.append(ProjectRequirement(
            name="vector_search",
            description="Ability to find similar documents using embeddings",
            why_needed="RAG systems need semantic search to retrieve relevant context",
            approaches=[
                {
                    "name": "chroma",
                    "description": "ChromaDB vector database",
                    "type": "service",
                    "pros": ["Easy setup", "Python native", "Free"],
                    "cons": ["Limited scalability"],
                    "best_for": "Development and small scale"
                },
                {
                    "name": "pinecone",
                    "description": "Pinecone cloud vector DB",
                    "type": "api", 
                    "pros": ["Highly scalable", "Managed", "Fast"],
                    "cons": ["Paid", "Vendor lock-in"],
                    "best_for": "Production applications"
                }
            ],
            recommended_approach="chroma"
        ))
    
    def _add_web_api_requirements(self) -> None:
        """Add requirements for web APIs"""
        
        self.discovery.requirements.append(ProjectRequirement(
            name="web_framework",
            description="Framework for building HTTP APIs",
            why_needed="Need to handle HTTP requests and responses",
            approaches=[
                {
                    "name": "fastapi",
                    "description": "FastAPI with automatic docs",
                    "type": "library",
                    "pros": ["Fast", "Auto docs", "Type hints", "Modern"],
                    "cons": ["Newer ecosystem"],
                    "best_for": "Modern APIs with good docs"
                },
                {
                    "name": "flask",
                    "description": "Flask micro framework",
                    "type": "library", 
                    "pros": ["Simple", "Flexible", "Mature"],
                    "cons": ["Manual setup", "No auto docs"],
                    "best_for": "Simple APIs and prototypes"
                }
            ],
            recommended_approach="fastapi"
        ))
    
    def _add_data_pipeline_requirements(self) -> None:
        """Add requirements for data pipelines"""
        
        self.discovery.requirements.append(ProjectRequirement(
            name="data_processing",
            description="Library for processing structured data",
            why_needed="Need to read, transform, and write data files",
            approaches=[
                {
                    "name": "pandas",
                    "description": "Pandas data analysis library",
                    "type": "library",
                    "pros": ["Powerful", "Widely used", "Good docs"],
                    "cons": ["Memory intensive", "Single machine"],
                    "best_for": "Most data processing tasks"
                },
                {
                    "name": "polars",
                    "description": "Polars fast dataframe library",
                    "type": "library",
                    "pros": ["Very fast", "Memory efficient", "Rust-based"],
                    "cons": ["Newer", "Smaller ecosystem"],
                    "best_for": "Large datasets needing speed"
                }
            ],
            recommended_approach="pandas"
        ))
    
    def _add_chatbot_requirements(self) -> None:
        """Add requirements for chatbots"""
        
        # Similar to RAG but simpler
        self.discovery.requirements.append(ProjectRequirement(
            name="conversation_ai",
            description="AI model for natural conversation",
            why_needed="Chatbots need to understand and respond naturally",
            approaches=[
                {
                    "name": "openai_api",
                    "description": "OpenAI GPT for conversation",
                    "type": "api",
                    "pros": ["Excellent conversation", "Easy to use"],
                    "cons": ["Paid", "Requires internet"],
                    "best_for": "High quality conversational AI"
                },
                {
                    "name": "local_llm",
                    "description": "Local conversational model",
                    "type": "local",
                    "pros": ["Free", "Private"],
                    "cons": ["Setup complexity", "Lower quality"],
                    "best_for": "Development and privacy"
                }
            ],
            recommended_approach="openai_api"
        ))
    
    def _add_general_requirements(self) -> None:
        """Add basic requirements for general applications"""
        
        self.discovery.requirements.append(ProjectRequirement(
            name="basic_functionality",
            description="Core application functionality",
            why_needed="Every application needs basic structure and logic",
            approaches=[
                {
                    "name": "python_standard",
                    "description": "Python standard library",
                    "type": "library",
                    "pros": ["No dependencies", "Always available"],
                    "cons": ["Limited functionality"],
                    "best_for": "Simple applications"
                }
            ],
            recommended_approach="python_standard"
        ))
    
    def _refine_requirements_with_user(self) -> None:
        """Interactive refinement of discovered requirements"""
        
        print("🔧 Let's configure your project requirements:\n")
        
        for i, req in enumerate(self.discovery.requirements, 1):
            print(f"📋 {i}. {req.description.upper()}")
            print(f"   Why needed: {req.why_needed}")
            print("-" * 50)
            
            if req.recommended_approach:
                recommended = next(
                    (approach for approach in req.approaches if approach["name"] == req.recommended_approach),
                    None
                )
                if recommended:
                    print(f"🎯 RECOMMENDED: {recommended['description']}")
                    print(f"   Best for: {recommended['best_for']}")
                    print()
            
            print("Available approaches:")
            for j, approach in enumerate(req.approaches, 1):
                marker = "⭐" if approach["name"] == req.recommended_approach else "  "
                print(f"{marker} {j}. {approach['description']}")
                print(f"      Type: {approach['type'].title()} | Pros: {', '.join(approach['pros'][:2])}")
                print(f"      Best for: {approach['best_for']}")
                print()
            
            # Get user choice
            while True:
                try:
                    default_choice = next(
                        (j for j, approach in enumerate(req.approaches, 1) 
                         if approach["name"] == req.recommended_approach), 1
                    )
                    
                    choice = input(f"Choose approach [1-{len(req.approaches)}] (default: {default_choice}): ").strip()
                    
                    if not choice:
                        choice = default_choice
                    else:
                        choice = int(choice)
                    
                    if 1 <= choice <= len(req.approaches):
                        selected = req.approaches[choice - 1]
                        req.user_choice = selected["name"]
                        print(f"✅ Selected: {selected['description']}\n")
                        break
                    else:
                        print(f"Please enter a number between 1 and {len(req.approaches)}")
                        
                except (ValueError, KeyboardInterrupt):
                    print(f"Please enter a number between 1 and {len(req.approaches)}")
        
        print("="*60)
        print("✅ Requirements configuration complete!\n")
    
    def _generate_dynamic_milestones(self) -> None:
        """Generate milestones based on project type and requirements"""
        
        print("🎯 Generating project milestones based on your choices...\n")
        
        # Use suggested milestones from research, or generate based on type
        if self.discovery.suggested_milestones:
            milestones = self.discovery.suggested_milestones
        else:
            milestones = self._generate_default_milestones()
        
        print("📅 Suggested milestone progression:")
        for i, milestone in enumerate(milestones, 1):
            print(f"{i}. {milestone['name']}")
            print(f"   {milestone['description']}")
            if 'why_first' in milestone:
                print(f"   Why now: {milestone['why_first']}")
            print()
        
        # Ask user if they want to modify milestones
        modify = input("Would you like to modify these milestones? (y/N): ").strip().lower()
        if modify in ['y', 'yes']:
            self._customize_milestones(milestones)
        else:
            self.discovery.suggested_milestones = milestones
            print("✅ Using suggested milestones\n")
    
    def _generate_default_milestones(self) -> List[Dict[str, Any]]:
        """Generate default milestones based on project type"""
        
        if self.discovery.project_type == "RAG System":
            return [
                {
                    "name": "Core Infrastructure",
                    "description": "Document processing and knowledge graph construction",
                    "why_first": "Need basic data structures before adding AI"
                },
                {
                    "name": "Search & Retrieval", 
                    "description": "Vector embeddings and semantic search",
                    "why_first": "Search capability needed before response generation"
                },
                {
                    "name": "AI Integration",
                    "description": "LLM integration and response generation",
                    "why_first": "Complete the RAG pipeline with AI responses"
                }
            ]
        elif self.discovery.project_type == "Web API":
            return [
                {
                    "name": "Core API",
                    "description": "Basic HTTP endpoints and routing",
                    "why_first": "Foundation for all API functionality"
                },
                {
                    "name": "Data Layer",
                    "description": "Database integration and data models", 
                    "why_first": "APIs need persistent data storage"
                },
                {
                    "name": "Advanced Features",
                    "description": "Authentication, validation, and production features",
                    "why_first": "Production-ready features on solid foundation"
                }
            ]
        else:
            return [
                {
                    "name": "Foundation",
                    "description": "Core functionality and basic features",
                    "why_first": "Start with essential functionality"
                },
                {
                    "name": "Enhancement", 
                    "description": "Additional features and improvements",
                    "why_first": "Build on working foundation"
                },
                {
                    "name": "Polish",
                    "description": "Error handling, testing, and production readiness",
                    "why_first": "Make it robust and deployable"
                }
            ]
    
    def _customize_milestones(self, milestones: List[Dict[str, Any]]) -> None:
        """Allow user to customize milestone definitions"""
        # For now, just use the defaults
        # This could be expanded to allow interactive milestone editing
        print("📝 Milestone customization not yet implemented, using defaults\n")
        self.discovery.suggested_milestones = milestones
    
    def _finalize_dependencies(self) -> None:
        """Convert user choices into concrete dependencies"""
        
        print("🔧 Finalizing dependencies based on your choices...\n")
        
        for req in self.discovery.requirements:
            if not req.user_choice:
                req.user_choice = req.recommended_approach
            
            selected_approach = next(
                (approach for approach in req.approaches if approach["name"] == req.user_choice),
                None
            )
            
            if not selected_approach:
                continue
            
            # Convert to concrete dependency based on approach type
            dependency = {
                "requirement": req.name,
                "approach": selected_approach["name"],
                "description": selected_approach["description"],
                "type": selected_approach["type"]
            }
            
            # Add specific setup requirements based on type
            if selected_approach["type"] == "api":
                dependency["api_key_needed"] = self._get_api_key_name(selected_approach["name"])
            elif selected_approach["type"] == "service":
                dependency["docker_service"] = selected_approach["name"]
            elif selected_approach["type"] == "library":
                dependency["pip_package"] = selected_approach["name"]
            
            self.discovery.final_dependencies.append(dependency)
        
        # Show final dependency summary
        api_keys = [dep for dep in self.discovery.final_dependencies if "api_key_needed" in dep]
        services = [dep for dep in self.discovery.final_dependencies if "docker_service" in dep]
        packages = [dep for dep in self.discovery.final_dependencies if "pip_package" in dep]
        
        if api_keys:
            print("🔑 API Keys needed:")
            for dep in api_keys:
                print(f"  - {dep['api_key_needed']}: {dep['description']}")
        
        if services:
            print("🐳 Docker services needed:")
            for dep in services:
                print(f"  - {dep['docker_service']}: {dep['description']}")
        
        if packages:
            print("📦 Python packages needed:")
            for dep in packages:
                print(f"  - {dep['pip_package']}: {dep['description']}")
        
        print()
    
    def _get_api_key_name(self, approach_name: str) -> str:
        """Get the API key environment variable name for an approach"""
        key_mapping = {
            "openai_api": "OPENAI_API_KEY",
            "anthropic_api": "ANTHROPIC_API_KEY", 
            "pinecone": "PINECONE_API_KEY",
            "huggingface": "HUGGINGFACE_API_KEY"
        }
        return key_mapping.get(approach_name, f"{approach_name.upper()}_API_KEY")
    
    def _save_discovery_results(self) -> None:
        """Save discovery results to project files"""
        
        # Create project directory structure
        self.project_dir.mkdir(exist_ok=True)
        cc_dir = self.project_dir / ".cc_automator"
        cc_dir.mkdir(exist_ok=True)
        
        # Save discovery data
        discovery_file = cc_dir / "project_discovery.json"
        discovery_data = {
            "user_intent": self.discovery.user_intent,
            "project_type": self.discovery.project_type,
            "requirements": [
                {
                    "name": req.name,
                    "description": req.description,
                    "why_needed": req.why_needed,
                    "approaches": req.approaches,
                    "recommended_approach": req.recommended_approach,
                    "user_choice": req.user_choice,
                    "priority": req.priority
                }
                for req in self.discovery.requirements
            ],
            "suggested_milestones": self.discovery.suggested_milestones,
            "final_dependencies": self.discovery.final_dependencies
        }
        
        with open(discovery_file, 'w') as f:
            json.dump(discovery_data, f, indent=2)
        
        # Generate CLAUDE.md based on discoveries
        self._generate_claude_md()
        
        print(f"✅ Discovery results saved to {discovery_file}")
        print(f"✅ Project configuration saved to {self.project_dir / 'CLAUDE.md'}")
    
    def _generate_claude_md(self) -> None:
        """Generate CLAUDE.md based on discovery results"""
        
        claude_md = self.project_dir / "CLAUDE.md"
        
        content = [
            f"# {self._get_project_name()}",
            "",
            "## Project Overview", 
            f"**User Intent:** {self.discovery.user_intent}",
            f"**Project Type:** {self.discovery.project_type}",
            "",
            "## Technical Requirements",
            "- Python 3.9+",
        ]
        
        # Add package requirements
        packages = [dep for dep in self.discovery.final_dependencies if "pip_package" in dep]
        for dep in packages:
            content.append(f"- {dep['pip_package']}: {dep['description']}")
        
        content.extend([
            "- Proper async/await patterns",
            "- Comprehensive error handling", 
            "- Full test coverage",
            "",
            "## Success Criteria",
            "- Working main.py with CLI interface",
            "- All functionality implemented and tested",
            "- Clean code passing linting and type checking",
            "- Complete documentation",
            "",
            "## Milestones"
        ])
        
        # Add generated milestones
        for i, milestone in enumerate(self.discovery.suggested_milestones, 1):
            content.extend([
                f"",
                f"### Milestone {i}: {milestone['name']}",
                f"**Produces a working main.py that can:**",
                f"- {milestone['description']}",
                f"- Pass all tests for this milestone",
                f"- Demonstrate progress toward final goal"
            ])
        
        content.extend([
            "",
            "## Development Standards",
            "",
            "### Code Quality",
            "- All code must pass flake8 linting (max-line-length=100)",
            "- All code must pass mypy strict type checking", 
            "- All tests must pass with pytest",
            "- main.py must run successfully as the entry point",
            "",
            "### Testing Requirements",
            "- Unit tests: Test individual components in isolation",
            "- Integration tests: Test component interactions", 
            "- E2E tests: Test complete workflows via main.py",
            "",
            "### Architecture Patterns",
            "- Use dependency injection for testability",
            "- Implement proper async patterns for I/O operations",
            "- Use dataclasses/Pydantic for data models",
            "- Separate concerns between components"
        ])
        
        # Add external dependencies section
        api_keys = [dep for dep in self.discovery.final_dependencies if "api_key_needed" in dep]
        services = [dep for dep in self.discovery.final_dependencies if "docker_service" in dep]
        
        if api_keys or services:
            content.extend([
                "",
                "## External Dependencies"
            ])
            
            for dep in packages:
                content.append(f"- {dep['pip_package']}: {dep['description']}")
            
            if api_keys:
                content.append("### API Keys Required:")
                for dep in api_keys:
                    content.append(f"- {dep['api_key_needed']}: {dep['description']}")
            
            if services:
                content.append("### Services Required:")
                for dep in services:
                    content.append(f"- {dep['docker_service']}: {dep['description']}")
        
        content.extend([
            "",
            "## Special Considerations",
            "- Handle errors gracefully with informative messages",
            "- Use async patterns for I/O-bound operations", 
            "- Consider memory usage and performance",
            "- Implement proper logging and monitoring"
        ])
        
        claude_md.write_text("\n".join(content))
    
    def _get_project_name(self) -> str:
        """Generate a project name from user intent"""
        intent = self.discovery.user_intent.lower()
        
        if "graphrag" in intent:
            return "GraphRAG System"
        elif "api" in intent or "web service" in intent:
            return "Web API Service"
        elif "pipeline" in intent or "data processing" in intent:
            return "Data Processing Pipeline"
        elif "chatbot" in intent or "chat" in intent:
            return "Chatbot Application"
        else:
            # Extract key words and make a name
            words = intent.replace("a ", "").replace("an ", "").split()
            key_words = [w.title() for w in words[:3] if len(w) > 3]
            return " ".join(key_words) + " System"


def run_project_discovery(project_dir: Path) -> ProjectDiscovery:
    """Main entry point for project discovery"""
    wizard = ProjectDiscoveryWizard(project_dir)
    return wizard.run_discovery()


if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1:
        project_path = Path(sys.argv[1])
    else:
        project_path = Path.cwd()
    
    print(f"Running project discovery for: {project_path}")
    discovery = run_project_discovery(project_path)
    print(f"\n✅ Discovery complete! Check {project_path}/CLAUDE.md for results")