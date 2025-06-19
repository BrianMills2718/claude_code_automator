#!/usr/bin/env python3
"""
Setup script for CC_AUTOMATOR3
Guides users through project configuration
"""

import os
import sys
import json
import subprocess
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional, Any

from preflight_validator import PreflightValidator


class ProjectSetup:
    """Interactive setup for cc_automator projects"""
    
    def __init__(self, project_dir: Optional[Path] = None):
        self.project_dir = Path(project_dir) if project_dir else Path.cwd()
        self.cc_automator_dir = Path(__file__).parent
        self.template_dir = self.cc_automator_dir / "templates"
        self.config = {}
        
    def run(self) -> bool:
        """Run the complete setup process"""
        
        print("=" * 60)
        print("CC_AUTOMATOR3 Project Setup")
        print("=" * 60)
        print()
        
        # Step 1: Run preflight checks
        if not self._run_preflight():
            return False
            
        # Step 2: Check for existing CLAUDE.md
        if self._check_existing_config():
            return True
            
        # Step 3: Run interactive Q&A with Claude
        if not self._run_interactive_qa():
            return False
            
        # Step 4: Validate the configuration
        if not self._validate_config():
            return False
            
        # Step 5: Create project structure
        self._create_project_structure()
        
        # Step 6: Create initial git commit
        self._create_initial_commit()
        
        print("\n✓ Setup complete! Your project is ready for automated development.")
        print(f"\nTo start development, run:")
        print(f"  python {self.cc_automator_dir}/run.py")
        
        return True
        
    def _run_preflight(self) -> bool:
        """Run preflight validation"""
        print("Running preflight checks...\n")
        
        validator = PreflightValidator(self.project_dir)
        passed, errors = validator.run_all_checks()
        
        if not passed:
            print("\n✗ Preflight checks failed. Please fix the issues above.")
            print("\nCommon fixes:")
            print("  - Initialize git: git init")
            print("  - Install tools: pip install flake8 mypy pytest")
            print("  - Install Claude: npm install -g @anthropic-ai/claude-code")
            return False
            
        return True
        
    def _check_existing_config(self) -> bool:
        """Check if CLAUDE.md already exists"""
        claude_md = self.project_dir / "CLAUDE.md"
        
        if claude_md.exists():
            print(f"\n✓ Found existing CLAUDE.md configuration")
            response = input("\nDo you want to reconfigure the project? [y/N]: ").lower()
            
            if response != 'y':
                print("Using existing configuration.")
                return True
            else:
                # Backup existing config
                backup_name = f"CLAUDE.md.backup.{datetime.now().strftime('%Y%m%d_%H%M%S')}"
                claude_md.rename(self.project_dir / backup_name)
                print(f"Backed up existing config to: {backup_name}")
                
        return False
        
    def _run_interactive_qa(self) -> bool:
        """Run interactive Q&A session with Claude"""
        print("\nStarting interactive configuration...\n")
        
        # Copy QA template to project directory temporarily
        qa_template = self.template_dir / "CLAUDE_TEMPLATE_QA.md"
        temp_qa = self.project_dir / ".cc_automator_qa.md"
        
        # Read QA template
        with open(qa_template) as f:
            qa_content = f.read()
            
        # Create a prompt for Claude
        prompt = f"""
I'm setting up a project for automated development using CC_AUTOMATOR3. 
Please help me configure it by asking the questions in the setup guide and filling in the template.

Current directory: {self.project_dir}

Please:
1. First, examine any existing documentation (README.md, etc.)
2. Ask me the questions from the setup guide
3. Create a filled CLAUDE.md based on my answers
4. Make sure each milestone produces a runnable main.py

Here's the setup guide to follow:

{qa_content}
"""
        
        # Run Claude interactively for Q&A
        print("Launching Claude for interactive configuration...")
        print("Please answer the questions to configure your project.\n")
        
        try:
            result = subprocess.run(
                ["claude"],
                cwd=str(self.project_dir)
            )
            
            if result.returncode != 0:
                print("\n✗ Configuration was cancelled.")
                return False
                
            # Check if CLAUDE.md was created
            claude_md = self.project_dir / "CLAUDE.md"
            if not claude_md.exists():
                print("\n✗ CLAUDE.md was not created. Please try again.")
                return False
                
            print("\n✓ Configuration completed successfully!")
            return True
            
        except FileNotFoundError:
            print("\n✗ Claude Code not found. Please install it first:")
            print("  npm install -g @anthropic-ai/claude-code")
            return False
        except KeyboardInterrupt:
            print("\n\n✗ Setup interrupted by user.")
            return False
            
    def _validate_config(self) -> bool:
        """Validate the created configuration"""
        claude_md = self.project_dir / "CLAUDE.md"
        
        if not claude_md.exists():
            print("\n✗ CLAUDE.md not found.")
            return False
            
        # Read and check for required sections
        with open(claude_md) as f:
            content = f.read()
            
        required_sections = [
            "Project Overview",
            "Technical Requirements", 
            "Success Criteria",
            "Milestones",
            "Development Standards"
        ]
        
        missing = []
        for section in required_sections:
            if section not in content:
                missing.append(section)
                
        if missing:
            print(f"\n⚠ Warning: Missing sections in CLAUDE.md: {', '.join(missing)}")
            response = input("Continue anyway? [y/N]: ").lower()
            if response != 'y':
                return False
                
        # Check for placeholder values
        if "{{" in content and "}}" in content:
            print("\n⚠ Warning: Found unfilled placeholders in CLAUDE.md")
            print("Please edit CLAUDE.md to fill in any {{PLACEHOLDER}} values.")
            response = input("Continue anyway? [y/N]: ").lower()
            if response != 'y':
                return False
                
        # Validate milestones are vertical slices
        if "Milestone" in content:
            print("\n✓ Milestones defined")
            # Could add more sophisticated validation here
        else:
            print("\n⚠ Warning: No milestones found in CLAUDE.md")
            print("Milestones help break the project into manageable pieces.")
            
        return True
        
    def _create_project_structure(self):
        """Create basic project structure if it doesn't exist"""
        print("\nCreating project structure...")
        
        # Create directories
        directories = [
            self.project_dir / "src",
            self.project_dir / "tests" / "unit",
            self.project_dir / "tests" / "integration", 
            self.project_dir / "tests" / "e2e",
            self.project_dir / ".cc_automator"
        ]
        
        for dir_path in directories:
            dir_path.mkdir(parents=True, exist_ok=True)
            
        # Create main.py if it doesn't exist
        main_py = self.project_dir / "main.py"
        if not main_py.exists():
            with open(main_py, 'w') as f:
                f.write('''#!/usr/bin/env python3
"""
Main entry point for the application
"""

def main():
    """Main function"""
    print("Hello from main.py!")
    # TODO: Implement main functionality
    return 0

if __name__ == "__main__":
    import sys
    sys.exit(main())
''')
            main_py.chmod(0o755)
            print("  ✓ Created main.py")
            
        # Create requirements.txt if it doesn't exist
        requirements = self.project_dir / "requirements.txt"
        if not requirements.exists():
            with open(requirements, 'w') as f:
                f.write("# Project dependencies\n")
            print("  ✓ Created requirements.txt")
            
        # Create .gitignore if it doesn't exist
        gitignore = self.project_dir / ".gitignore"
        if not gitignore.exists():
            with open(gitignore, 'w') as f:
                f.write("""# Python
__pycache__/
*.py[cod]
*$py.class
*.so
.Python
venv/
.env

# CC_AUTOMATOR
.cc_automator/
*.log

# IDE
.vscode/
.idea/
*.swp
*.swo
""")
            print("  ✓ Created .gitignore")
            
        # Create initial README if it doesn't exist
        readme = self.project_dir / "README.md"
        if not readme.exists():
            # Extract project name from CLAUDE.md
            claude_md = self.project_dir / "CLAUDE.md"
            project_name = "Project"
            
            if claude_md.exists():
                with open(claude_md) as f:
                    content = f.read()
                    if content.startswith("# "):
                        project_name = content.split("\n")[0][2:].strip()
                        
            with open(readme, 'w') as f:
                f.write(f"""# {project_name}

This project is being developed using CC_AUTOMATOR3.

## Getting Started

1. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

2. Run the application:
   ```bash
   python main.py
   ```

## Development

This project is automatically developed using CC_AUTOMATOR3.
See CLAUDE.md for project specifications and milestones.
""")
            print("  ✓ Created README.md")
            
    def _create_initial_commit(self):
        """Create an initial git commit if there are no commits"""
        import subprocess
        
        # Check if there are any commits
        result = subprocess.run(
            ["git", "rev-list", "--count", "HEAD"],
            cwd=self.project_dir,
            capture_output=True,
            text=True
        )
        
        # If no commits (command fails or returns 0)
        if result.returncode != 0 or result.stdout.strip() == "0":
            print("\nCreating initial git commit...")
            
            # Add all files
            subprocess.run(
                ["git", "add", "-A"],
                cwd=self.project_dir,
                capture_output=True
            )
            
            # Create initial commit
            result = subprocess.run(
                ["git", "commit", "-m", "Initial commit - CC_AUTOMATOR3 project setup"],
                cwd=self.project_dir,
                capture_output=True,
                text=True
            )
            
            if result.returncode == 0:
                print("  ✓ Created initial git commit")
            else:
                print("  ⚠ Could not create initial commit:", result.stderr)
        else:
            print("  ✓ Git repository already has commits")
            
    def create_example_project(self, example_type: str = "calculator"):
        """Create an example project configuration"""
        examples = {
            "calculator": {
                "name": "Python Calculator",
                "description": "A command-line calculator with basic arithmetic operations",
                "milestones": [
                    "Basic arithmetic operations (add, subtract, multiply, divide)",
                    "Advanced operations (power, sqrt, modulo)",
                    "Expression parser for complex calculations"
                ]
            },
            "todo": {
                "name": "Todo List CLI", 
                "description": "A command-line todo list manager with persistence",
                "milestones": [
                    "Basic CRUD operations for todos",
                    "File persistence and data management",
                    "Categories and priority features"
                ]
            }
        }
        
        if example_type not in examples:
            print(f"Unknown example type: {example_type}")
            return False
            
        example = examples[example_type]
        
        # Create CLAUDE.md from template
        template_path = self.template_dir / "CLAUDE_TEMPLATE.md"
        with open(template_path) as f:
            template = f.read()
            
        # Fill in the template
        filled = template.replace("{{PROJECT_NAME}}", example["name"])
        filled = filled.replace("{{PROJECT_DESCRIPTION}}", example["description"])
        filled = filled.replace("{{TECHNICAL_REQUIREMENTS}}", "- Python 3.8+\n- No external dependencies for core functionality")
        filled = filled.replace("{{SUCCESS_CRITERIA}}", "- All arithmetic operations work correctly\n- Proper error handling\n- User-friendly interface")
        
        milestones_text = ""
        for i, milestone in enumerate(example["milestones"], 1):
            milestones_text += f"### Milestone {i}: {milestone}\n"
            milestones_text += f"- Produces a working main.py with this functionality\n"
            milestones_text += f"- All tests pass\n\n"
            
        filled = filled.replace("{{MILESTONES}}", milestones_text)
        filled = filled.replace("{{ENV_VARIABLES}}", "None required")
        filled = filled.replace("{{EXTERNAL_DEPENDENCIES}}", "None")
        filled = filled.replace("{{SPECIAL_CONSIDERATIONS}}", "- Focus on code clarity and good error messages")
        
        # Save CLAUDE.md
        claude_md = self.project_dir / "CLAUDE.md"
        with open(claude_md, 'w') as f:
            f.write(filled)
            
        print(f"\n✓ Created example project configuration: {example['name']}")
        return True


def main():
    """Main entry point"""
    import argparse
    
    parser = argparse.ArgumentParser(description="Setup CC_AUTOMATOR3 project")
    parser.add_argument("--project", type=str, help="Project directory (default: current)")
    parser.add_argument("--example", type=str, choices=["calculator", "todo"],
                       help="Create an example project configuration")
    
    args = parser.parse_args()
    
    # Determine project directory
    project_dir = Path(args.project) if args.project else Path.cwd()
    if not project_dir.exists():
        project_dir.mkdir(parents=True)
        
    # Run setup
    setup = ProjectSetup(project_dir)
    
    # Create example if requested
    if args.example:
        setup.create_example_project(args.example)
        setup._create_project_structure()
        setup._create_initial_commit()  # Add initial commit
        print(f"\nExample project ready! Run:")
        print(f"  python {Path(__file__).parent}/run.py")
        return 0
        
    # Run normal setup
    if setup.run():
        return 0
    else:
        return 1


if __name__ == "__main__":
    sys.exit(main())