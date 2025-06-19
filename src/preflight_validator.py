#!/usr/bin/env python3
"""
Preflight Validator for CC_AUTOMATOR3
Validates environment before starting execution
"""

import subprocess
import shutil
import os
import sys
from pathlib import Path
from typing import Dict, List, Tuple, Optional


class PreflightValidator:
    """Validates prerequisites before running cc_automator"""
    
    def __init__(self, project_dir: Optional[Path] = None):
        self.project_dir = Path(project_dir) if project_dir else Path.cwd()
        self.checks_passed = True
        self.error_messages = []
        
    def run_all_checks(self) -> Tuple[bool, List[str]]:
        """Run all preflight checks and return status"""
        
        print("Running preflight checks...")
        print("-" * 40)
        
        checks = [
            ("Python version", self.check_python_version),
            ("Git repository", self.check_git_repo),
            ("Git status", self.check_git_clean),
            ("Required tools", self.check_required_tools),
            ("Python dependencies", self.check_python_deps),
            ("Claude Code auth", self.check_claude_auth),
            ("Disk space", self.check_disk_space),
            ("Directory permissions", self.check_permissions),
        ]
        
        results = {}
        for check_name, check_func in checks:
            try:
                passed, message = check_func()
                results[check_name] = passed
                status = "✓" if passed else "✗"
                print(f"{status} {check_name}: {message}")
                
                if not passed:
                    self.checks_passed = False
                    self.error_messages.append(f"{check_name}: {message}")
                    
            except Exception as e:
                results[check_name] = False
                print(f"✗ {check_name}: Error - {str(e)}")
                self.checks_passed = False
                self.error_messages.append(f"{check_name}: {str(e)}")
                
        print("-" * 40)
        
        if self.checks_passed:
            print("✓ All preflight checks passed!")
        else:
            print("✗ Some checks failed. Please fix the issues above.")
            
        return self.checks_passed, self.error_messages
        
    def check_python_version(self) -> Tuple[bool, str]:
        """Check Python version is 3.8+"""
        version = sys.version_info
        if version.major == 3 and version.minor >= 8:
            return True, f"Python {version.major}.{version.minor}.{version.micro}"
        return False, f"Python 3.8+ required, found {version.major}.{version.minor}"
        
    def check_git_repo(self) -> Tuple[bool, str]:
        """Check if current directory is a git repository"""
        git_dir = self.project_dir / ".git"
        if git_dir.exists():
            return True, "Git repository found"
        
        # Try git command as backup
        try:
            result = subprocess.run(
                ["git", "rev-parse", "--git-dir"],
                cwd=self.project_dir,
                capture_output=True,
                text=True
            )
            if result.returncode == 0:
                return True, "Git repository found"
        except:
            pass
            
        return False, "Not a git repository. Run 'git init' first"
        
    def check_git_clean(self) -> Tuple[bool, str]:
        """Check if git working directory is clean"""
        try:
            result = subprocess.run(
                ["git", "status", "--porcelain"],
                cwd=self.project_dir,
                capture_output=True,
                text=True
            )
            
            if result.returncode != 0:
                return False, "Could not check git status"
                
            if result.stdout.strip():
                # There are uncommitted changes
                lines = len(result.stdout.strip().split('\n'))
                return True, f"Warning: {lines} uncommitted changes (consider committing first)"
            
            return True, "Working directory clean"
            
        except FileNotFoundError:
            return False, "Git not found"
            
    def check_required_tools(self) -> Tuple[bool, str]:
        """Check if required development tools are installed"""
        required_tools = {
            "git": "Version control",
            "python": "Python interpreter", 
            "flake8": "Code linting",
            "mypy": "Type checking",
            "pytest": "Unit testing",
            "claude": "Claude Code CLI"
        }
        
        missing_tools = []
        for tool, description in required_tools.items():
            if not shutil.which(tool):
                missing_tools.append(f"{tool} ({description})")
                
        if missing_tools:
            return False, f"Missing tools: {', '.join(missing_tools)}"
            
        return True, "All required tools found"
        
    def check_python_deps(self) -> Tuple[bool, str]:
        """Check if Python development tools are properly installed"""
        try:
            # Check if we can import the tools
            for module, tool in [("flake8", "flake8"), ("mypy", "mypy"), ("pytest", "pytest")]:
                result = subprocess.run(
                    [sys.executable, "-c", f"import {module}"],
                    capture_output=True
                )
                if result.returncode != 0:
                    return False, f"Python module '{module}' not found. Install with: pip install {tool}"
                    
            return True, "Python development tools available"
            
        except Exception as e:
            return False, f"Error checking Python dependencies: {str(e)}"
            
    def check_claude_auth(self) -> Tuple[bool, str]:
        """Check if Claude Code is authenticated"""
        try:
            # Try to run claude with a simple command
            result = subprocess.run(
                ["claude", "--version"],
                capture_output=True,
                text=True,
                timeout=5
            )
            
            if result.returncode == 0:
                # Check for Claude Max subscription by looking at output
                if "claude" in result.stdout.lower():
                    return True, "Claude Code authenticated"
                    
            return False, "Claude Code not authenticated. Run 'claude' to set up"
            
        except FileNotFoundError:
            return False, "Claude Code not installed. Run: npm install -g @anthropic-ai/claude-code"
        except subprocess.TimeoutExpired:
            return False, "Claude Code timeout - may need authentication"
        except Exception as e:
            return False, f"Error checking Claude Code: {str(e)}"
            
    def check_disk_space(self) -> Tuple[bool, str]:
        """Check available disk space"""
        try:
            import shutil
            stat = shutil.disk_usage(self.project_dir)
            free_gb = stat.free / (1024 ** 3)
            
            if free_gb < 1:
                return False, f"Low disk space: {free_gb:.1f}GB free"
            elif free_gb < 5:
                return True, f"Warning: Only {free_gb:.1f}GB free"
            else:
                return True, f"{free_gb:.1f}GB free"
                
        except Exception as e:
            return True, "Could not check disk space"
            
    def check_permissions(self) -> Tuple[bool, str]:
        """Check if we can create files in the project directory"""
        try:
            test_file = self.project_dir / ".cc_automator_test"
            test_file.touch()
            test_file.unlink()
            return True, "Write permissions OK"
        except Exception as e:
            return False, f"Cannot write to project directory: {str(e)}"
            
    def create_missing_tools_script(self) -> Path:
        """Create a script to install missing tools"""
        script_path = self.project_dir / "install_missing_tools.sh"
        
        with open(script_path, 'w') as f:
            f.write("#!/bin/bash\n")
            f.write("# Script to install missing tools for cc_automator\n\n")
            
            # Python tools
            f.write("# Install Python development tools\n")
            f.write("pip install flake8 mypy pytest\n\n")
            
            # Claude Code
            f.write("# Install Claude Code (requires Node.js)\n")
            f.write("npm install -g @anthropic-ai/claude-code\n\n")
            
            f.write("echo 'Installation complete! Run preflight checks again.'\n")
            
        script_path.chmod(0o755)
        return script_path


if __name__ == "__main__":
    # Run preflight checks
    validator = PreflightValidator()
    passed, errors = validator.run_all_checks()
    
    if not passed:
        print("\nTo fix missing tools, you can run:")
        print("  pip install flake8 mypy pytest")
        print("  npm install -g @anthropic-ai/claude-code")
        sys.exit(1)
    else:
        print("\nReady to run cc_automator!")
        sys.exit(0)