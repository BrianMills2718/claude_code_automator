#!/usr/bin/env python3
"""
Simple overnight test that will actually complete
Uses simpler milestones that are easier to test
"""

import tempfile
import subprocess
from pathlib import Path

def create_simple_overnight():
    # Create temp directory
    project_dir = Path(tempfile.mkdtemp(prefix="simple_overnight_"))
    
    # Initialize git
    subprocess.run(['git', 'init'], cwd=project_dir, capture_output=True)
    subprocess.run(['git', 'config', 'user.email', 'test@example.com'], cwd=project_dir, capture_output=True)
    subprocess.run(['git', 'config', 'user.name', 'Test User'], cwd=project_dir, capture_output=True)
    
    # Create .env
    (project_dir / ".env").write_text("OPENAI_API_KEY=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")
    
    # Create simple CLAUDE.md with easier-to-test milestones
    claude_md = """# Text Processing Utilities

## Description
Command-line utilities for text processing with simple, testable functions.

## Milestones

### Milestone 1: Basic text operations in main.py
**Description**: Create main.py with word count, line count, and character count functions

**Requirements**:
- main.py with count_words(), count_lines(), count_chars() functions
- Command-line interface to call these functions
- Simple file reading capabilities
- Unit tests for each function

### Milestone 2: Text transformation features in main.py
**Description**: Add text transformation capabilities to main.py

**Requirements**:
- Add to_uppercase(), to_lowercase(), reverse_text() functions
- Add remove_punctuation() and extract_numbers() functions
- Extend CLI to support these operations
- Integration tests for all features

### Milestone 3: File processing pipeline in main.py
**Description**: Add batch file processing to main.py

**Requirements**:
- Process multiple files with any operation
- Save results to output files
- Add progress reporting
- End-to-end tests for full pipeline
"""
    
    (project_dir / "CLAUDE.md").write_text(claude_md)
    
    print(f"✅ SIMPLE OVERNIGHT TEST READY")
    print(f"📁 Project: {project_dir}")
    print("🚀 RUN THIS:")
    print(f"FORCE_SONNET=true python /home/brian/cc_automator4/run.py --project {project_dir} --verbose")
    print("\n✨ Why this will work:")
    print("  • Simple, pure functions that are easy to test")
    print("  • No complex state or external dependencies")
    print("  • Clear input/output for each function")
    print("  • 3 milestones = ~3 hours runtime")

if __name__ == "__main__":
    create_simple_overnight()