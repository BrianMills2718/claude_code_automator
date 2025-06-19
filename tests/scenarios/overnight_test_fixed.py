#!/usr/bin/env python3
"""
Fixed overnight test that will actually run
"""

import json
import os
import tempfile
import subprocess
from pathlib import Path

def create_overnight_test():
    """Create a working multi-milestone project"""
    
    # Create temp directory
    project_dir = Path(tempfile.mkdtemp(prefix="overnight_fixed_"))
    print(f"📁 Created project: {project_dir}")
    
    # Initialize git
    subprocess.run(['git', 'init'], cwd=project_dir, capture_output=True)
    subprocess.run(['git', 'config', 'user.email', 'test@example.com'], cwd=project_dir, capture_output=True)
    subprocess.run(['git', 'config', 'user.name', 'Test User'], cwd=project_dir, capture_output=True)
    
    # Create .env
    env_content = """OPENAI_API_KEY=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"""
    (project_dir / ".env").write_text(env_content)
    
    # Create CLAUDE.md that will pass validation
    claude_md = """# Task Management System

## Description
A command-line task management system with persistence and reporting.

## Milestones

### Milestone 1: Basic task operations with CLI (main.py)
**Description**: Create main.py with basic task management operations: add, list, complete, and delete tasks

**Requirements**:
- main.py with command-line interface
- Task data structure and operations
- File-based persistence (JSON)
- Basic error handling
- Unit tests for core functions

### Milestone 2: Advanced features and reports in main.py
**Description**: Extend main.py with filtering, sorting, and report generation

**Requirements**:
- Filter tasks by status, date, priority
- Sort tasks by various criteria
- Generate summary reports
- Export to CSV/JSON formats
- Integration tests for all features

### Milestone 3: Interactive menu system in main.py
**Description**: Add an interactive menu interface to main.py for easier task management

**Requirements**:
- Interactive menu loop in main.py
- Input validation and error handling
- Help system and user guidance
- Batch operations support
- End-to-end tests for full workflow
"""
    
    (project_dir / "CLAUDE.md").write_text(claude_md)
    
    print("✅ FIXED PROJECT READY")
    print("🚀 RUN THIS:")
    print(f"FORCE_SONNET=true python /home/brian/cc_automator4/run.py --project {project_dir} --verbose")
    
    return project_dir

if __name__ == "__main__":
    create_overnight_test()