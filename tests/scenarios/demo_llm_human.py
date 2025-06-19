#!/usr/bin/env python3
"""
Demo script for LLM-as-human interaction with CC_AUTOMATOR4
Creates a complex project that demonstrates Sonnet's planning capabilities
"""

import json
import os
import tempfile
from pathlib import Path

def create_complex_demo_project():
    """Create a complex project for LLM demonstration"""
    
    # Create temp directory
    project_dir = Path(tempfile.mkdtemp(prefix="demo_complex_"))
    print(f"📁 Created demo project: {project_dir}")
    
    # Create CC_AUTOMATOR4 config
    config = {
        "name": "GraphRAG Document Intelligence System",
        "description": "Multi-modal document processing with real-time knowledge graph updates",
        "milestones": [
            {
                "name": "Document Processing Pipeline",
                "description": "PDF/text ingestion with OCR, chunking, and embedding generation using sentence-transformers",
                "requirements": [
                    "PDF parsing with PyMuPDF or similar",
                    "OCR for scanned documents",
                    "Text chunking strategies", 
                    "Embedding generation pipeline",
                    "Document metadata extraction"
                ]
            },
            {
                "name": "Knowledge Graph Construction", 
                "description": "Entity extraction, relationship mapping, and Neo4j graph database integration",
                "requirements": [
                    "Named entity recognition",
                    "Relationship extraction",
                    "Neo4j database setup",
                    "Graph schema design",
                    "CRUD operations for nodes/edges"
                ]
            },
            {
                "name": "RAG Query Interface",
                "description": "REST API with semantic search, graph traversal, and LLM integration for intelligent responses", 
                "requirements": [
                    "FastAPI REST endpoints",
                    "Vector similarity search",
                    "Graph traversal queries", 
                    "LLM integration (OpenAI/local)",
                    "Response synthesis and ranking"
                ]
            }
        ]
    }
    
    # Write config
    config_path = project_dir / "cc_automator_config.json"
    with open(config_path, 'w') as f:
        json.dump(config, f, indent=2)
    
    print("🎯 COMPLEX DEMO PROJECT CREATED")
    print("📊 Features:")
    print("  - Multi-modal document processing")  
    print("  - Knowledge graph construction")
    print("  - RAG with semantic search")
    print("  - REST API with LLM integration")
    print("  - Expected: 20+ files, complex dependencies")
    print()
    print("🤖 TO RUN WITH LLM-AS-HUMAN:")
    print(f"   FORCE_SONNET=true python /home/brian/cc_automator4/run.py --project {project_dir} --verbose")
    print()
    print("📋 INTERACTION GUIDANCE FOR LLM:")
    print("   • When prompted for technology choices, you can:")
    print("     - Ask clarifying questions about requirements")  
    print("     - Suggest alternatives with reasoning")
    print("     - Request specific implementation approaches")
    print("   • The system will work through planning → implementation → testing")
    print("   • Watch for Sonnet's comprehensive file creation in planning phase")
    
    return project_dir

if __name__ == "__main__":
    create_complex_demo_project()