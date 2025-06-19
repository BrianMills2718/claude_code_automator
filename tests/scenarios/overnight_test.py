#!/usr/bin/env python3
"""
Overnight test with manually created multi-milestone project
Creates a robust 3-milestone project that should run to completion
"""

import json
import os
import tempfile
import subprocess
from pathlib import Path

def create_overnight_test():
    """Create a robust multi-milestone project for overnight testing"""
    
    # Create temp directory
    project_dir = Path(tempfile.mkdtemp(prefix="overnight_test_"))
    print(f"📁 Created overnight test project: {project_dir}")
    
    # Initialize git repository
    subprocess.run(['git', 'init'], cwd=project_dir, capture_output=True)
    subprocess.run(['git', 'config', 'user.email', 'test@example.com'], cwd=project_dir, capture_output=True)
    subprocess.run(['git', 'config', 'user.name', 'Test User'], cwd=project_dir, capture_output=True)
    print("✅ Git repository initialized")
    
    # Create .env file with API key
    env_content = """OPENAI_API_KEY=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"""
    (project_dir / ".env").write_text(env_content)
    
    # Create CLAUDE.md with 3 solid milestones
    claude_md = """# Data Processing Pipeline System

## Description
A comprehensive data processing pipeline that ingests CSV files, processes them, and generates reports with a web interface.

## Milestones

### Milestone 1: Core Data Processing Engine
**Description**: CSV file ingestion, data validation, and basic processing capabilities

**Requirements**:
- CSV file reader with error handling
- Data validation and cleaning functions  
- Basic statistical analysis capabilities
- Configuration management
- Comprehensive unit tests

**Success Criteria**:
- Can read and validate CSV files
- Processes data with error handling
- All unit tests pass
- Code is properly typed and linted

### Milestone 2: Report Generation System
**Description**: Generate detailed reports from processed data with multiple output formats

**Requirements**:
- Report generation engine
- Multiple output formats (JSON, HTML, PDF)
- Template system for custom reports
- Data visualization capabilities
- Integration tests with sample data

**Success Criteria**:
- Generates reports in multiple formats
- Templates are customizable
- Integration tests pass
- Performance meets requirements

### Milestone 3: Web Interface and API
**Description**: REST API and web interface for managing the data processing pipeline

**Requirements**:
- FastAPI REST endpoints
- File upload functionality
- Processing status tracking
- Report download capabilities
- Web interface for management
- End-to-end tests

**Success Criteria**:
- API endpoints work correctly
- Web interface is functional
- File uploads and downloads work
- End-to-end tests pass
- System runs without errors
"""
    
    (project_dir / "CLAUDE.md").write_text(claude_md)
    
    print("🎯 OVERNIGHT TEST PROJECT CREATED")
    print("=" * 50)
    print("📊 Project: Data Processing Pipeline System")
    print("📋 Milestones: 3 comprehensive milestones")
    print("⏰ Expected duration: 2-4 hours")
    print("💰 Expected cost: $2-5 with Sonnet")
    print()
    print("🚀 COMMAND TO RUN OVERNIGHT:")
    print(f"   FORCE_SONNET=true python /home/brian/cc_automator4/run.py --project {project_dir} --verbose")
    print()
    print("📝 WHAT IT WILL BUILD:")
    print("   • Milestone 1: Core data processing engine")
    print("   • Milestone 2: Report generation system") 
    print("   • Milestone 3: Web interface and API")
    print("   • Full test suite for each milestone")
    print("   • Production-ready code with typing")
    print()
    print("🔧 TECHNICAL FEATURES:")
    print("   • No external API dependencies (self-contained)")
    print("   • Uses standard Python libraries")
    print("   • Comprehensive error handling")
    print("   • Full validation pipeline")
    
    return project_dir

if __name__ == "__main__":
    create_overnight_test()