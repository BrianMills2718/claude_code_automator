"""
Integration Consistency Validator
Ensures related commands have consistent dependency requirements
"""

import ast
import re
from pathlib import Path
from typing import List, Dict, Set, Tuple
from dataclasses import dataclass
import logging

logger = logging.getLogger(__name__)

@dataclass
class CommandDependencies:
    """Dependencies required by a command"""
    command: str
    requires_db: bool
    requires_api_keys: Set[str]
    requires_network: bool
    requires_previous_state: bool

@dataclass
class DependencyInconsistency:
    """Represents an inconsistency between related commands"""
    command1: str
    command2: str
    issue: str
    severity: str  # "error", "warning"

class IntegrationConsistencyValidator:
    """Validates consistency across integrated components"""
    
    def __init__(self, project_dir: Path):
        self.project_dir = project_dir
        self.cli_dir = project_dir / "src" / "cli"
        
    def analyze_command_dependencies(self) -> List[CommandDependencies]:
        """Analyze dependencies for all CLI commands"""
        dependencies = []
        
        # Look for command files
        commands_file = self.cli_dir / "commands.py"
        if not commands_file.exists():
            return dependencies
            
        content = commands_file.read_text()
        tree = ast.parse(content)
        
        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef):
                # Check if it's a CLI command (has @app.command decorator)
                if any(isinstance(d, ast.Name) and d.id == 'command' for d in node.decorator_list):
                    deps = self._analyze_function_dependencies(node, content)
                    dependencies.append(deps)
                    
        return dependencies
    
    def _analyze_function_dependencies(self, func_node: ast.FunctionDef, full_content: str) -> CommandDependencies:
        """Analyze what a function depends on"""
        requires_db = False
        requires_api_keys = set()
        requires_network = False
        requires_previous_state = False
        
        # Get function source
        func_source = ast.get_source_segment(full_content, func_node)
        
        # Check for database operations
        db_patterns = [
            r'repository\.',
            r'session\.',
            r'\.save\(',
            r'\.get_market_data\(',
            r'database',
            r'storage'
        ]
        for pattern in db_patterns:
            if re.search(pattern, func_source):
                requires_db = True
                break
                
        # Check for API key usage
        api_key_patterns = {
            'ALPHA_VANTAGE_API_KEY': r'alpha.*vantage|ALPHA_VANTAGE',
            'OPENAI_API_KEY': r'openai|gpt',
            'POSTGRES_PASSWORD': r'postgres|database'
        }
        for key, pattern in api_key_patterns.items():
            if re.search(pattern, func_source, re.IGNORECASE):
                requires_api_keys.add(key)
                
        # Check for network operations
        network_patterns = [
            r'requests\.',
            r'httpx\.',
            r'urllib',
            r'fetch.*data',
            r'api\.',
            r'download'
        ]
        for pattern in network_patterns:
            if re.search(pattern, func_source):
                requires_network = True
                break
                
        # Check if it requires previous state
        state_patterns = [
            r'get_.*data',
            r'load_',
            r'retrieve_',
            r'analyze',
            r'update',
            r'modify'
        ]
        for pattern in state_patterns:
            if re.search(pattern, func_source):
                requires_previous_state = True
                break
                
        return CommandDependencies(
            command=func_node.name,
            requires_db=requires_db,
            requires_api_keys=requires_api_keys,
            requires_network=requires_network,
            requires_previous_state=requires_previous_state
        )
    
    def find_inconsistencies(self, dependencies: List[CommandDependencies]) -> List[DependencyInconsistency]:
        """Find inconsistencies between related commands"""
        inconsistencies = []
        
        # Group related commands
        related_groups = self._group_related_commands(dependencies)
        
        for group in related_groups:
            # Check for database consistency
            db_requirements = {cmd.command: cmd.requires_db for cmd in group}
            if len(set(db_requirements.values())) > 1:
                # Some commands need DB, others don't
                for cmd1 in group:
                    for cmd2 in group:
                        if cmd1.requires_db and not cmd2.requires_db and cmd2.requires_previous_state:
                            inconsistencies.append(DependencyInconsistency(
                                command1=cmd1.command,
                                command2=cmd2.command,
                                issue=f"{cmd1.command} saves to DB but {cmd2.command} doesn't use DB for reading",
                                severity="error"
                            ))
                            
            # Check for API key consistency
            all_api_keys = set()
            for cmd in group:
                all_api_keys.update(cmd.requires_api_keys)
                
            for cmd in group:
                if cmd.requires_network and not cmd.requires_api_keys and all_api_keys:
                    inconsistencies.append(DependencyInconsistency(
                        command1=cmd.command,
                        command2="group",
                        issue=f"{cmd.command} uses network but doesn't check for API keys that other commands use",
                        severity="warning"
                    ))
                    
        return inconsistencies
    
    def _group_related_commands(self, dependencies: List[CommandDependencies]) -> List[List[CommandDependencies]]:
        """Group commands that are likely related"""
        groups = []
        
        # Common groupings
        data_commands = ['fetch', 'get', 'download', 'pull', 'import']
        analysis_commands = ['analyze', 'calculate', 'compute', 'process']
        crud_commands = ['create', 'read', 'update', 'delete', 'list']
        
        # Group by pattern matching
        data_group = []
        analysis_group = []
        crud_group = []
        
        for dep in dependencies:
            cmd_lower = dep.command.lower()
            
            if any(pattern in cmd_lower for pattern in data_commands):
                data_group.append(dep)
            elif any(pattern in cmd_lower for pattern in analysis_commands):
                analysis_group.append(dep)
            elif any(pattern in cmd_lower for pattern in crud_commands):
                crud_group.append(dep)
                
        # Add groups that have multiple commands
        if len(data_group) > 1:
            groups.append(data_group)
        if len(analysis_group) > 1:
            groups.append(analysis_group)
        if len(crud_group) > 1:
            groups.append(crud_group)
            
        # Also group fetch+analyze specifically
        fetch_analyze = []
        for dep in dependencies:
            if dep.command in ['fetch', 'analyze']:
                fetch_analyze.append(dep)
        if len(fetch_analyze) == 2:
            groups.append(fetch_analyze)
            
        return groups
    
    def generate_consistency_report(self, inconsistencies: List[DependencyInconsistency]) -> str:
        """Generate a report of found inconsistencies"""
        report = ["# Integration Consistency Report\n"]
        
        if not inconsistencies:
            report.append("✅ No integration inconsistencies found!")
            return "\n".join(report)
            
        errors = [i for i in inconsistencies if i.severity == "error"]
        warnings = [i for i in inconsistencies if i.severity == "warning"]
        
        report.append(f"**Found {len(errors)} errors and {len(warnings)} warnings**\n")
        
        if errors:
            report.append("## Errors (Must Fix)")
            for error in errors:
                report.append(f"- **{error.command1} ↔ {error.command2}**: {error.issue}")
                
        if warnings:
            report.append("\n## Warnings (Should Fix)")
            for warning in warnings:
                report.append(f"- **{warning.command1}**: {warning.issue}")
                
        return "\n".join(report)