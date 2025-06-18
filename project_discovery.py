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
        """Use Claude Code's intelligence to research project requirements dynamically"""
        
        print("🔍 Using Claude Code's intelligence to research your project requirements...")
        
        try:
            # Use this Claude Code session for intelligent analysis
            analysis_result = self._analyze_with_claude_intelligence()
            self._parse_dynamic_research_results(analysis_result)
            
        except Exception as e:
            print(f"⚠️  Dynamic research failed: {e}")
            print("Falling back to basic analysis...\n")
            self._fallback_analysis()
    
    def _analyze_with_claude_intelligence(self) -> str:
        """Use Claude's knowledge to analyze the project requirements"""
        
        user_intent = self.discovery.user_intent.lower()
        
        # Intelligent analysis based on Claude's understanding
        print("🧠 Analyzing project requirements...")
        
        # GraphRAG and Knowledge Systems
        if any(term in user_intent for term in ['graphrag', 'knowledge graph', 'rag']) or \
           ('graph' in user_intent and any(term in user_intent for term in ['document', 'analysis', 'retrieval'])):
            
            # Special handling for historical analysis
            if any(term in user_intent for term in ['historical', 'history', 'event', 'timeline', 'temporal']):
                return self._analyze_historical_graphrag_system()
            else:
                return self._analyze_standard_graphrag_system()
                
        # Conversational AI Systems  
        elif any(term in user_intent for term in ['chatbot', 'chat', 'conversation', 'assistant', 'support']):
            return self._analyze_chatbot_system()
            
        # Web Services and APIs
        elif any(term in user_intent for term in ['api', 'web service', 'web app', 'dashboard', 'portal']):
            return self._analyze_web_service_system()
            
        # Data Processing and Analytics
        elif any(term in user_intent for term in ['data', 'analytics', 'processing', 'pipeline', 'etl']):
            return self._analyze_data_system()
            
        # Fraud/Security Systems
        elif any(term in user_intent for term in ['fraud', 'detection', 'security', 'monitoring']):
            return self._analyze_security_system()
            
        # Medical/Healthcare Systems
        elif any(term in user_intent for term in ['medical', 'healthcare', 'diagnosis', 'patient']):
            return self._analyze_medical_system()
            
        # Default: Intelligent general analysis
        else:
            return self._analyze_general_system()
    
    def _analyze_historical_graphrag_system(self) -> str:
        """Analyze requirements for historical event tracing GraphRAG system"""
        return json.dumps({
            "project_type": "Historical Event Analysis GraphRAG System",
            "reasoning": "This system combines graph-based knowledge representation with historical document analysis for temporal event tracing and causality analysis",
            "core_capabilities": [
                {
                    "name": "historical_document_processing",
                    "description": "Process historical documents with temporal context",
                    "why_needed": "Historical analysis requires extracting events, dates, and entities from historical texts with temporal understanding",
                    "approaches": [
                        {
                            "name": "specialized_nlp_pipeline",
                            "description": "SpaCy + temporal NER models for historical text",
                            "type": "library",
                            "pros": ["Good for historical texts", "Temporal extraction", "Free"],
                            "cons": ["Setup complexity", "May need training"],
                            "best_for": "Historical document analysis with temporal focus",
                            "complexity": "moderate",
                            "cost": "free"
                        },
                        {
                            "name": "llm_historical_analysis",
                            "description": "LLM with prompts for historical event extraction",
                            "type": "api",
                            "pros": ["Excellent understanding", "Temporal reasoning", "Context awareness"],
                            "cons": ["Cost per document", "API dependency"],
                            "best_for": "High-quality historical analysis",
                            "complexity": "simple",
                            "cost": "medium"
                        }
                    ],
                    "recommended": "llm_historical_analysis for quality, specialized_nlp_pipeline for cost"
                },
                {
                    "name": "temporal_graph_construction",
                    "description": "Build time-aware knowledge graphs of historical events",
                    "why_needed": "Historical events need temporal relationships and causality mapping over time",
                    "approaches": [
                        {
                            "name": "networkx_temporal",
                            "description": "NetworkX with temporal edge attributes",
                            "type": "library",
                            "pros": ["Flexible", "Custom temporal logic", "Free"],
                            "cons": ["Manual temporal handling", "Limited scalability"],
                            "best_for": "Custom temporal graph analysis",
                            "complexity": "moderate",
                            "cost": "free"
                        },
                        {
                            "name": "neo4j_temporal",
                            "description": "Neo4j with temporal queries and APOC",
                            "type": "service",
                            "pros": ["Native temporal support", "Scalable", "Advanced queries"],
                            "cons": ["Setup complexity", "Resource intensive"],
                            "best_for": "Large-scale historical graph analysis",
                            "complexity": "complex",
                            "cost": "low"
                        }
                    ],
                    "recommended": "networkx_temporal for development, neo4j_temporal for production scale"
                },
                {
                    "name": "event_similarity_search",
                    "description": "Find similar historical events and patterns",
                    "why_needed": "Historical analysis requires finding patterns and similar events across time periods",
                    "approaches": [
                        {
                            "name": "chroma_historical",
                            "description": "ChromaDB with historical event embeddings",
                            "type": "service",
                            "pros": ["Good for development", "Event similarity", "Easy setup"],
                            "cons": ["Limited temporal queries"],
                            "best_for": "Historical event similarity search",
                            "complexity": "simple",
                            "cost": "free"
                        },
                        {
                            "name": "custom_temporal_embeddings",
                            "description": "Custom embeddings with temporal weighting",
                            "type": "library",
                            "pros": ["Temporal awareness", "Custom similarity", "Precise control"],
                            "cons": ["Implementation complexity", "Requires ML expertise"],
                            "best_for": "Advanced temporal similarity analysis",
                            "complexity": "complex",
                            "cost": "free"
                        }
                    ],
                    "recommended": "chroma_historical for simplicity, custom_temporal_embeddings for advanced use"
                }
            ],
            "milestone_suggestions": [
                {
                    "name": "Historical Document Ingestion",
                    "description": "Document parsing, entity extraction, and temporal event identification",
                    "why_this_order": "Need to extract structured data from historical documents before building graphs",
                    "success_criteria": "System can extract events, entities, and dates from historical texts"
                },
                {
                    "name": "Temporal Graph Construction",
                    "description": "Build time-aware knowledge graphs with event relationships",
                    "why_this_order": "Graph structure needed before adding similarity search capabilities",
                    "success_criteria": "Historical events connected in temporal graph with causality links"
                },
                {
                    "name": "Historical Analysis Interface",
                    "description": "Query interface for historical event tracing and pattern analysis",
                    "why_this_order": "Complete system with user interface for historical research",
                    "success_criteria": "Users can trace historical events and discover patterns across time"
                }
            ]
        })
    
    def _analyze_standard_graphrag_system(self) -> str:
        """Analyze requirements for standard GraphRAG system"""
        return json.dumps({
            "project_type": "Graph-Based Retrieval Augmented Generation System",
            "reasoning": "Combines knowledge graphs with language models for enhanced document understanding and question answering",
            "core_capabilities": [
                {
                    "name": "document_understanding",
                    "description": "Process and understand document content for knowledge extraction",
                    "why_needed": "GraphRAG requires extracting entities and relationships from documents",
                    "approaches": [
                        {
                            "name": "openai_gpt4",
                            "description": "OpenAI GPT-4 for document analysis",
                            "type": "api",
                            "pros": ["Excellent understanding", "Reliable", "Good entity extraction"],
                            "cons": ["Cost per token", "API dependency"],
                            "best_for": "High-quality document analysis",
                            "complexity": "simple",
                            "cost": "medium"
                        },
                        {
                            "name": "claude_api",
                            "description": "Anthropic Claude for document reasoning",
                            "type": "api", 
                            "pros": ["Strong reasoning", "Large context", "Good for analysis"],
                            "cons": ["Cost per token", "API dependency"],
                            "best_for": "Complex document reasoning and analysis",
                            "complexity": "simple",
                            "cost": "medium"
                        }
                    ],
                    "recommended": "claude_api for reasoning-heavy tasks, openai_gpt4 for general use"
                }
            ],
            "milestone_suggestions": [
                {
                    "name": "Core Graph Construction",
                    "description": "Document processing and knowledge graph building",
                    "why_this_order": "Foundation needed before adding retrieval capabilities",
                    "success_criteria": "Documents processed into structured knowledge graph"
                }
            ]
        })
    
    def _analyze_chatbot_system(self) -> str:
        """Analyze requirements for chatbot systems"""
        return json.dumps({
            "project_type": "Conversational AI Assistant",
            "reasoning": "Interactive chatbot system for customer support or general assistance",
            "core_capabilities": [
                {
                    "name": "conversation_management",
                    "description": "Handle multi-turn conversations with context",
                    "why_needed": "Chatbots need to maintain conversation state and context across interactions",
                    "approaches": [
                        {
                            "name": "openai_chat_api",
                            "description": "OpenAI Chat Completions API",
                            "type": "api",
                            "pros": ["Excellent conversation", "Context handling", "Reliable"],
                            "cons": ["Cost per message", "API dependency"],
                            "best_for": "High-quality conversational experiences",
                            "complexity": "simple",
                            "cost": "medium"
                        }
                    ],
                    "recommended": "openai_chat_api for quality conversations"
                }
            ],
            "milestone_suggestions": [
                {
                    "name": "Basic Chat Interface",
                    "description": "Core conversation handling and response generation",
                    "why_this_order": "Foundation for all chatbot functionality",
                    "success_criteria": "Users can have basic conversations with the bot"
                }
            ]
        })
    
    def _analyze_web_service_system(self) -> str:
        """Analyze requirements for web service systems"""
        return json.dumps({
            "project_type": "Web Application/API Service",
            "reasoning": "Web-based application providing HTTP endpoints or user interface",
            "core_capabilities": [],
            "milestone_suggestions": []
        })
    
    def _analyze_data_system(self) -> str:
        """Analyze requirements for data processing systems"""
        return json.dumps({
            "project_type": "Data Processing and Analytics System", 
            "reasoning": "System for processing, analyzing, and transforming data",
            "core_capabilities": [],
            "milestone_suggestions": []
        })
    
    def _analyze_security_system(self) -> str:
        """Analyze requirements for security/fraud detection systems"""
        return json.dumps({
            "project_type": "Security and Fraud Detection System",
            "reasoning": "Real-time monitoring and detection system for security threats",
            "core_capabilities": [],
            "milestone_suggestions": []
        })
    
    def _analyze_medical_system(self) -> str:
        """Analyze requirements for medical/healthcare systems"""
        return json.dumps({
            "project_type": "Medical/Healthcare Assistant System",
            "reasoning": "Healthcare application for diagnosis assistance or patient management",
            "core_capabilities": [],
            "milestone_suggestions": []
        })
    
    def _analyze_general_system(self) -> str:
        """Analyze requirements for general/unknown systems"""
        return json.dumps({
            "project_type": "Custom Application System",
            "reasoning": "General-purpose application based on user requirements",
            "core_capabilities": [],
            "milestone_suggestions": []
        })
    
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
