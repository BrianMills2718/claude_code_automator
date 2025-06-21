"""
Integration Consistency Validator
Ensures related commands have consistent dependency requirements and runtime availability
"""

import ast
import re
import subprocess
import socket
import requests
from pathlib import Path
from typing import List, Dict, Set, Tuple, Optional
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
class RuntimeDependencyStatus:
    """Status of runtime dependencies"""
    dependency_type: str  # "database", "api_key", "network", "file_storage"
    is_available: bool
    error_message: Optional[str] = None
    tested_resource: Optional[str] = None

@dataclass
class DependencyInconsistency:
    """Represents an inconsistency between related commands"""
    command1: str
    command2: str
    issue: str
    severity: str  # "error", "warning"
    runtime_impact: Optional[str] = None

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
                # Check if it's a CLI command (has @app.command decorator or similar)
                is_command = False
                for decorator in node.decorator_list:
                    # Handle @app.command(), @app.command, @typer.command(), etc.
                    if isinstance(decorator, ast.Call):
                        # @app.command() or @typer.command()
                        if (isinstance(decorator.func, ast.Attribute) and 
                            decorator.func.attr == 'command'):
                            is_command = True
                            break
                    elif isinstance(decorator, ast.Attribute):
                        # @app.command
                        if decorator.attr == 'command':
                            is_command = True
                            break
                    elif isinstance(decorator, ast.Name):
                        # @command
                        if decorator.id == 'command':
                            is_command = True
                            break
                
                # Also include specific function names that are likely commands
                if not is_command and node.name in ['fetch', 'search', 'analyze', 'create', 'update', 'delete', 'list', 'get']:
                    is_command = True
                
                if is_command:
                    logger.debug(f"Found command function: {node.name}")
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
        
        # Fallback if ast.get_source_segment doesn't work
        if not func_source:
            # Extract manually using line numbers
            lines = full_content.split('\n')
            start_line = func_node.lineno - 1
            end_line = func_node.end_lineno if hasattr(func_node, 'end_lineno') else start_line + 10
            func_source = '\n'.join(lines[start_line:end_line])
            
        logger.debug(f"Analyzing function {func_node.name}, source length: {len(func_source) if func_source else 0}")
        
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
            if func_source and re.search(pattern, func_source):
                requires_db = True
                logger.debug(f"Function {func_node.name} requires DB due to pattern: {pattern}")
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
    
    def check_runtime_dependencies(self, dependencies: List[CommandDependencies]) -> List[RuntimeDependencyStatus]:
        """Check if runtime dependencies are actually available"""
        status_list = []
        
        # Check database connectivity
        if any(dep.requires_db for dep in dependencies):
            db_status = self._check_database_connection()
            status_list.append(db_status)
            
        # Check API keys
        all_api_keys = set()
        for dep in dependencies:
            all_api_keys.update(dep.requires_api_keys)
        
        for api_key in all_api_keys:
            api_status = self._check_api_key_availability(api_key)
            status_list.append(api_status)
            
        # Check network connectivity
        if any(dep.requires_network for dep in dependencies):
            network_status = self._check_network_connectivity()
            status_list.append(network_status)
            
        # Check file storage
        storage_status = self._check_file_storage_availability()
        status_list.append(storage_status)
        
        return status_list
    
    def _check_database_connection(self) -> RuntimeDependencyStatus:
        """Check if database is accessible"""
        try:
            # Try to connect to common database ports
            databases_to_check = [
                ("postgresql", "localhost", 5432),
                ("mysql", "localhost", 3306),
                ("mongodb", "localhost", 27017)
            ]
            
            for db_type, host, port in databases_to_check:
                try:
                    sock = socket.create_connection((host, port), timeout=2)
                    sock.close()
                    return RuntimeDependencyStatus(
                        dependency_type="database",
                        is_available=True,
                        tested_resource=f"{db_type}://{host}:{port}"
                    )
                except (socket.error, ConnectionRefusedError):
                    continue
                    
            return RuntimeDependencyStatus(
                dependency_type="database",
                is_available=False,
                error_message="No database servers accessible on standard ports",
                tested_resource="localhost:5432,3306,27017"
            )
            
        except Exception as e:
            return RuntimeDependencyStatus(
                dependency_type="database",
                is_available=False,
                error_message=f"Database connectivity check failed: {str(e)}"
            )
    
    def _check_api_key_availability(self, api_key: str) -> RuntimeDependencyStatus:
        """Check if API key is set and potentially valid"""
        import os
        
        key_value = os.environ.get(api_key)
        if not key_value:
            return RuntimeDependencyStatus(
                dependency_type="api_key",
                is_available=False,
                error_message=f"Environment variable {api_key} not set",
                tested_resource=api_key
            )
            
        # Basic validation - not empty and reasonable length
        if len(key_value.strip()) < 10:
            return RuntimeDependencyStatus(
                dependency_type="api_key",
                is_available=False,
                error_message=f"API key {api_key} appears to be invalid (too short)",
                tested_resource=api_key
            )
            
        return RuntimeDependencyStatus(
            dependency_type="api_key",
            is_available=True,
            tested_resource=api_key
        )
    
    def _check_network_connectivity(self) -> RuntimeDependencyStatus:
        """Check if network/internet is accessible"""
        try:
            # Try to reach a reliable endpoint
            response = requests.get("https://httpbin.org/status/200", timeout=5)
            if response.status_code == 200:
                return RuntimeDependencyStatus(
                    dependency_type="network",
                    is_available=True,
                    tested_resource="https://httpbin.org"
                )
            else:
                return RuntimeDependencyStatus(
                    dependency_type="network",
                    is_available=False,
                    error_message=f"Network test returned status {response.status_code}",
                    tested_resource="https://httpbin.org"
                )
        except Exception as e:
            return RuntimeDependencyStatus(
                dependency_type="network",
                is_available=False,
                error_message=f"Network connectivity failed: {str(e)}",
                tested_resource="https://httpbin.org"
            )
    
    def _check_file_storage_availability(self) -> RuntimeDependencyStatus:
        """Check if file storage is available and writable"""
        try:
            # Check if we can write to common data directories
            data_dirs_to_check = [
                self.project_dir / "data",
                self.project_dir / "storage", 
                self.project_dir / "cache",
                self.project_dir  # Project root as fallback
            ]
            
            for data_dir in data_dirs_to_check:
                try:
                    # Try to create directory if it doesn't exist
                    data_dir.mkdir(exist_ok=True, parents=True)
                    
                    # Try to write a test file
                    test_file = data_dir / ".write_test"
                    test_file.write_text("test")
                    test_file.unlink()  # Clean up
                    
                    return RuntimeDependencyStatus(
                        dependency_type="file_storage",
                        is_available=True,
                        tested_resource=str(data_dir)
                    )
                except (PermissionError, OSError):
                    continue
                    
            return RuntimeDependencyStatus(
                dependency_type="file_storage",
                is_available=False,
                error_message="No writable data directories available",
                tested_resource=str(self.project_dir)
            )
            
        except Exception as e:
            return RuntimeDependencyStatus(
                dependency_type="file_storage",
                is_available=False,
                error_message=f"File storage check failed: {str(e)}",
                tested_resource=str(self.project_dir)
            )
    
    def validate_runtime_integration_consistency(self) -> Tuple[List[DependencyInconsistency], List[RuntimeDependencyStatus]]:
        """Complete validation including runtime dependency checks"""
        # Analyze command dependencies
        dependencies = self.analyze_command_dependencies()
        
        # Check runtime availability
        runtime_status = self.check_runtime_dependencies(dependencies)
        
        # Find inconsistencies  
        inconsistencies = self.find_inconsistencies(dependencies)
        
        # Add runtime impact to inconsistencies
        for inconsistency in inconsistencies:
            runtime_issues = []
            for status in runtime_status:
                if not status.is_available:
                    runtime_issues.append(f"{status.dependency_type}: {status.error_message}")
            
            if runtime_issues:
                inconsistency.runtime_impact = "; ".join(runtime_issues)
        
        return inconsistencies, runtime_status