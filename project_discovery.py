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

# Dynamic project discovery using Claude Code's capabilities


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
        """Use Claude Code's dynamic research capabilities to discover project requirements"""
        
        print("🔍 Using Claude Code's intelligence to research your project requirements...")
        
        try:
            # Use the CC_AUTOMATOR4 Task tool for dynamic research
            import sys
            sys.path.append(str(Path(__file__).parent))
            
            # For now, we'll implement a mock Task that simulates the behavior
            # In a real implementation, this would use the actual Task tool
            class MockTask:
                def __init__(self, description: str, prompt: str):
                    self.description = description
                    self.prompt = prompt
                    
                def execute(self):
                    # This would normally call the actual Task tool
                    # For now, return a placeholder that triggers fallback
                    raise Exception("Task tool integration not yet implemented")
            
            Task = MockTask
            
            research_task = Task(
                description="Dynamic project requirement analysis",
                prompt=f"""Research what building "{self.discovery.user_intent}" would actually require.

I need you to use your knowledge to analyze this project request dynamically:

User's Project Intent: "{self.discovery.user_intent}"

Please research and determine:

1. **Project Classification**: What type of project is this? (Don't assume - analyze the intent)

2. **Core Capabilities Needed**: What technical capabilities would this project require? 
   - Think about the user's goals and what would be needed to achieve them
   - Consider data flow, user interaction, processing requirements, etc.

3. **Implementation Approaches**: For each capability you identify, research what approaches exist:
   - API-based solutions (cloud services, third-party APIs)
   - Library-based solutions (Python packages, frameworks)
   - Local/self-hosted solutions (databases, services)
   - Consider pros/cons, complexity, cost, and use cases for each

4. **Logical Implementation Order**: What would be a sensible milestone progression?
   - Consider dependencies between components
   - Think about what should be built first to establish a foundation
   - What order would allow for iterative testing and validation

IMPORTANT: Don't hardcode assumptions about technologies. Use your knowledge to research what approaches actually exist for the capabilities this project needs.

Format your response as JSON with this structure:
{{
    "project_type": "your analysis of what type of project this is",
    "reasoning": "why you classified it this way",
    "core_capabilities": [
        {{
            "name": "capability_name",
            "description": "what this capability does",
            "why_needed": "why this specific project requires this capability",
            "approaches": [
                {{
                    "name": "approach_name", 
                    "description": "description of this approach",
                    "type": "api|library|service|local|hybrid",
                    "pros": ["list of advantages"],
                    "cons": ["list of disadvantages"],
                    "best_for": "what use cases this approach is ideal for",
                    "complexity": "simple|moderate|complex",
                    "cost": "free|low|medium|high"
                }}
            ],
            "recommended": "which approach you recommend and why"
        }}
    ],
    "milestone_suggestions": [
        {{
            "name": "milestone name",
            "description": "what functionality gets implemented",
            "why_this_order": "reasoning for why this should come at this stage",
            "success_criteria": "how to know this milestone is complete"
        }}
    ]
}}"""
            )
            
            # Execute the research task
            analysis_result = research_task.execute()
            self._parse_dynamic_research_results(analysis_result)
            
        except Exception as e:
            print(f"⚠️  Dynamic research failed: {e}")
            print("Falling back to basic analysis...\n")
            self._fallback_analysis()
    
    def _parse_dynamic_research_results(self, analysis_result: str) -> None:
        """Parse Claude's dynamic research into project requirements"""
        
        try:
            # Extract JSON from Claude's response
            import re
            json_match = re.search(r'\{.*\}', analysis_result, re.DOTALL)
            if json_match:
                data = json.loads(json_match.group())
            else:
                raise ValueError("No JSON found in response")
            
            # Store project type with reasoning
            project_type = data.get("project_type", "Unknown")
            reasoning = data.get("reasoning", "")
            self.discovery.project_type = project_type
            
            print(f"🎯 Project Analysis: {project_type}")
            if reasoning:
                print(f"📝 Reasoning: {reasoning}")
            
            # Convert capabilities to requirements with enhanced data structure
            capabilities = data.get("core_capabilities", [])
            for cap in capabilities:
                # Convert approaches with enhanced metadata
                approaches = []
                for approach in cap.get("approaches", []):
                    approach_data = {
                        "name": approach["name"],
                        "description": approach["description"],
                        "type": approach["type"],
                        "pros": approach["pros"],
                        "cons": approach["cons"],
                        "best_for": approach["best_for"],
                        "complexity": approach.get("complexity", "unknown"),
                        "cost": approach.get("cost", "unknown")
                    }
                    approaches.append(approach_data)
                
                requirement = ProjectRequirement(
                    name=cap["name"],
                    description=cap["description"],
                    why_needed=cap["why_needed"],
                    approaches=approaches,
                    recommended_approach=cap.get("recommended", "")
                )
                self.discovery.requirements.append(requirement)
            
            # Store enhanced milestone suggestions
            milestones = data.get("milestone_suggestions", [])
            for milestone in milestones:
                milestone_data = {
                    "name": milestone["name"],
                    "description": milestone["description"],
                    "why_this_order": milestone.get("why_this_order", milestone.get("why_first", "")),
                    "success_criteria": milestone.get("success_criteria", "Functionality implemented and tested")
                }
                self.discovery.suggested_milestones.append(milestone_data)
            
            print(f"📋 Discovered {len(self.discovery.requirements)} core capabilities needed")
            print(f"🎯 Generated {len(self.discovery.suggested_milestones)} milestone progression\n")
            
        except Exception as e:
            print(f"⚠️  Could not parse dynamic analysis: {e}")
            print("Falling back to basic analysis...\n")
            self._fallback_analysis()
    
    def _fallback_analysis(self) -> None:
        """Fallback analysis when dynamic research fails"""
        
        print("📋 Using basic analysis based on project description...")
        
        intent_lower = self.discovery.user_intent.lower()
        
        # Basic analysis without hardcoded assumptions
        if any(term in intent_lower for term in ['rag', 'retrieval', 'knowledge', 'graph', 'document']):
            self.discovery.project_type = "Document Analysis System"
            self._add_basic_text_processing_requirements()
            
        elif any(term in intent_lower for term in ['api', 'web', 'service', 'server', 'http']):
            self.discovery.project_type = "Web Service"
            self._add_basic_web_requirements()
            
        elif any(term in intent_lower for term in ['chat', 'bot', 'conversation', 'assistant']):
            self.discovery.project_type = "Conversational Application"
            self._add_basic_conversation_requirements()
            
        elif any(term in intent_lower for term in ['data', 'process', 'pipeline', 'csv', 'file']):
            self.discovery.project_type = "Data Processing System"
            self._add_basic_data_requirements()
            
        else:
            self.discovery.project_type = "Custom Application"
            self._add_basic_application_requirements()
        
        # Add basic milestones for fallback
        self.discovery.suggested_milestones = [
            {
                "name": "Core Implementation",
                "description": "Implement main functionality",
                "why_this_order": "Foundation must be built first",
                "success_criteria": "Basic features working"
            },
            {
                "name": "Enhancement",
                "description": "Add advanced features and improvements",
                "why_this_order": "Build on working foundation",
                "success_criteria": "Enhanced functionality complete"
            },
            {
                "name": "Production Ready",
                "description": "Testing, error handling, and deployment preparation",
                "why_this_order": "Make system robust and ready for use",
                "success_criteria": "All tests pass, system deployable"
            }
        ]
        
        print(f"🎯 Project Type: {self.discovery.project_type}")
        print(f"📋 Basic requirements identified\n")
    
    def _add_basic_text_processing_requirements(self) -> None:
        """Add basic text processing requirements"""
        self.discovery.requirements.append(ProjectRequirement(
            name="text_processing",
            description="Text analysis and processing capabilities",
            why_needed="Document analysis systems need to process and understand text content",
            approaches=[
                {
                    "name": "cloud_llm",
                    "description": "Cloud-based language model API",
                    "type": "api",
                    "pros": ["High quality", "No local resources"],
                    "cons": ["Paid", "Internet required"],
                    "best_for": "Production systems",
                    "complexity": "simple",
                    "cost": "medium"
                },
                {
                    "name": "local_processing",
                    "description": "Local NLP libraries",
                    "type": "library",
                    "pros": ["Free", "Private"],
                    "cons": ["Limited capabilities"],
                    "best_for": "Basic processing",
                    "complexity": "moderate",
                    "cost": "free"
                }
            ],
            recommended_approach="cloud_llm"
        ))
    
    def _add_basic_web_requirements(self) -> None:
        """Add basic web service requirements"""
        self.discovery.requirements.append(ProjectRequirement(
            name="web_framework",
            description="HTTP server and API framework",
            why_needed="Web services need to handle HTTP requests and responses",
            approaches=[
                {
                    "name": "fastapi",
                    "description": "FastAPI framework",
                    "type": "library",
                    "pros": ["Modern", "Fast", "Auto docs"],
                    "cons": ["Learning curve"],
                    "best_for": "API development",
                    "complexity": "simple",
                    "cost": "free"
                }
            ],
            recommended_approach="fastapi"
        ))
    
    def _add_basic_conversation_requirements(self) -> None:
        """Add basic conversation requirements"""
        self.discovery.requirements.append(ProjectRequirement(
            name="conversation_ai",
            description="Natural language conversation capabilities",
            why_needed="Chat applications need to understand and respond to user messages",
            approaches=[
                {
                    "name": "chat_api",
                    "description": "Chat completion API",
                    "type": "api",
                    "pros": ["High quality", "Easy integration"],
                    "cons": ["Paid", "Internet required"],
                    "best_for": "Conversational AI",
                    "complexity": "simple",
                    "cost": "medium"
                }
            ],
            recommended_approach="chat_api"
        ))
    
    def _add_basic_data_requirements(self) -> None:
        """Add basic data processing requirements"""
        self.discovery.requirements.append(ProjectRequirement(
            name="data_processing",
            description="Data manipulation and analysis",
            why_needed="Data processing systems need to read, transform, and write data",
            approaches=[
                {
                    "name": "pandas",
                    "description": "Pandas data analysis library",
                    "type": "library",
                    "pros": ["Powerful", "Well documented"],
                    "cons": ["Memory intensive"],
                    "best_for": "Data analysis",
                    "complexity": "simple",
                    "cost": "free"
                }
            ],
            recommended_approach="pandas"
        ))
    
    def _add_basic_application_requirements(self) -> None:
        """Add basic application requirements"""
        self.discovery.requirements.append(ProjectRequirement(
            name="core_functionality",
            description="Core application logic",
            why_needed="Every application needs its main functionality implemented",
            approaches=[
                {
                    "name": "python_standard",
                    "description": "Python standard library",
                    "type": "library",
                    "pros": ["No dependencies", "Reliable"],
                    "cons": ["More implementation work"],
                    "best_for": "General applications",
                    "complexity": "simple",
                    "cost": "free"
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
                complexity = approach.get("complexity", "unknown")
                cost = approach.get("cost", "unknown")
                print(f"{marker} {j}. {approach['description']}")
                print(f"      Complexity: {complexity.title()} | Cost: {cost.title()}")
                print(f"      Pros: {', '.join(approach['pros'][:2])}")
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
            if 'why_this_order' in milestone:
                print(f"   Why now: {milestone['why_this_order']}")
            elif 'why_first' in milestone:
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
        
        return [
            {
                "name": "Foundation",
                "description": "Core functionality and basic features",
                "why_this_order": "Start with essential functionality",
                "success_criteria": "Basic features working"
            },
            {
                "name": "Enhancement", 
                "description": "Additional features and improvements",
                "why_this_order": "Build on working foundation",
                "success_criteria": "Enhanced functionality complete"
            },
            {
                "name": "Production Ready",
                "description": "Error handling, testing, and production readiness",
                "why_this_order": "Make it robust and deployable",
                "success_criteria": "All tests pass, system deployable"
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
            "cloud_llm": "OPENAI_API_KEY",
            "chat_api": "OPENAI_API_KEY",
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
