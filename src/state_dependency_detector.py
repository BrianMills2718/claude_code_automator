"""
State Dependency Detector for CC_AUTOMATOR4
Detects when commands have missing prerequisites and suggests graceful handling
"""

import subprocess
from pathlib import Path
from typing import List, Dict, Set, Tuple, Optional
from dataclasses import dataclass
import logging
import json

logger = logging.getLogger(__name__)

@dataclass
class StateRequirement:
    """Represents a state requirement for a command"""
    command: str
    requires_data_for: Optional[str] = None  # e.g., "AAPL" symbol
    requires_files: List[str] = None  # File paths that must exist
    requires_config: List[str] = None  # Config values that must be set
    requires_services: List[str] = None  # Services that must be running
    
    def __post_init__(self):
        if self.requires_files is None:
            self.requires_files = []
        if self.requires_config is None:
            self.requires_config = []
        if self.requires_services is None:
            self.requires_services = []

@dataclass
class StateViolation:
    """Represents a missing state prerequisite"""
    command: str
    violation_type: str  # "missing_data", "missing_file", "missing_config", "service_down"
    missing_item: str
    suggested_action: str
    severity: str = "error"  # "error", "warning"

class StateDependencyDetector:
    """Detects missing state dependencies and suggests graceful handling"""
    
    def __init__(self, project_dir: Path):
        self.project_dir = project_dir
        
    def detect_command_state_requirements(self, command: str, args: List[str]) -> StateRequirement:
        """Detect what state a command requires based on its name and arguments"""
        
        # Extract symbol from arguments for financial commands
        symbol = None
        if args:
            # Look for stock symbol patterns (3-5 uppercase letters)
            import re
            for arg in args:
                if re.match(r'^[A-Z]{1,5}$', arg):
                    symbol = arg
                    break
        
        requirements = StateRequirement(command=command)
        
        # Command-specific state requirements
        if command == "analyze":
            if symbol:
                requirements.requires_data_for = symbol
                requirements.requires_files = [
                    f"data/{symbol}.json",
                    f"data/{symbol}.csv",
                    f"cache/{symbol}_data.json"
                ]
            requirements.requires_config = ["database_url", "data_directory"]
            requirements.requires_services = ["database", "cache_service"]
            
        elif command == "update":
            if symbol:
                requirements.requires_data_for = symbol
                requirements.requires_files = [f"data/{symbol}.json"]
            requirements.requires_services = ["database"]
            
        elif command == "export":
            requirements.requires_config = ["export_directory", "export_format"]
            requirements.requires_files = ["data/"]  # Any data files
            
        elif command == "backtest":
            if symbol:
                requirements.requires_data_for = symbol
            requirements.requires_config = ["backtest_period", "strategy_config"]
            requirements.requires_files = ["strategies/", "data/"]
            
        return requirements
    
    def check_state_prerequisites(self, requirements: StateRequirement) -> List[StateViolation]:
        """Check if all state prerequisites are met"""
        violations = []
        
        # Check file requirements
        for file_path in requirements.requires_files:
            full_path = self.project_dir / file_path
            
            if file_path.endswith("/"):
                # Directory requirement
                if not full_path.exists() or not full_path.is_dir():
                    violations.append(StateViolation(
                        command=requirements.command,
                        violation_type="missing_directory",
                        missing_item=file_path,
                        suggested_action=f"Create directory: mkdir -p {file_path}",
                        severity="error"
                    ))
            else:
                # File requirement
                if not full_path.exists():
                    violations.append(StateViolation(
                        command=requirements.command,
                        violation_type="missing_file",
                        missing_item=file_path,
                        suggested_action=self._suggest_file_creation_action(file_path, requirements),
                        severity="error"
                    ))
        
        # Check data requirements
        if requirements.requires_data_for:
            symbol = requirements.requires_data_for
            has_data = self._check_symbol_data_exists(symbol)
            if not has_data:
                violations.append(StateViolation(
                    command=requirements.command,
                    violation_type="missing_data",
                    missing_item=f"Data for {symbol}",
                    suggested_action=f"Fetch data first: python main.py fetch {symbol}",
                    severity="error"
                ))
        
        # Check config requirements
        for config_key in requirements.requires_config:
            has_config = self._check_config_exists(config_key)
            if not has_config:
                violations.append(StateViolation(
                    command=requirements.command,
                    violation_type="missing_config",
                    missing_item=config_key,
                    suggested_action=f"Set config: export {config_key.upper()}=<value>",
                    severity="warning"
                ))
        
        # Check service requirements
        for service in requirements.requires_services:
            is_running = self._check_service_running(service)
            if not is_running:
                violations.append(StateViolation(
                    command=requirements.command,
                    violation_type="service_down",
                    missing_item=service,
                    suggested_action=self._suggest_service_start_action(service),
                    severity="error"
                ))
        
        return violations
    
    def _suggest_file_creation_action(self, file_path: str, requirements: StateRequirement) -> str:
        """Suggest how to create a missing file"""
        if file_path.endswith(".json") and requirements.requires_data_for:
            symbol = requirements.requires_data_for
            return f"Fetch data first: python main.py fetch {symbol}"
        elif file_path.startswith("data/"):
            return "Run data collection commands to populate data directory"
        elif file_path.startswith("config/"):
            return f"Create config file: touch {file_path}"
        else:
            return f"Create required file: touch {file_path}"
    
    def _check_symbol_data_exists(self, symbol: str) -> bool:
        """Check if data exists for a symbol in any common location"""
        data_locations = [
            self.project_dir / "data" / f"{symbol}.json",
            self.project_dir / "data" / f"{symbol}.csv", 
            self.project_dir / "cache" / f"{symbol}_data.json",
            self.project_dir / f"{symbol.lower()}_data.json"
        ]
        
        return any(path.exists() for path in data_locations)
    
    def _check_config_exists(self, config_key: str) -> bool:
        """Check if a configuration value is set"""
        import os
        
        # Check environment variables
        env_key = config_key.upper()
        if os.environ.get(env_key):
            return True
            
        # Check config files
        config_files = [
            self.project_dir / "config.json",
            self.project_dir / ".env",
            self.project_dir / "settings.py"
        ]
        
        for config_file in config_files:
            if config_file.exists():
                try:
                    content = config_file.read_text()
                    if config_key in content or env_key in content:
                        return True
                except:
                    continue
                    
        return False
    
    def _check_service_running(self, service: str) -> bool:
        """Check if a service is running"""
        if service == "database":
            # Check common database ports
            import socket
            ports = [5432, 3306, 27017]  # PostgreSQL, MySQL, MongoDB
            for port in ports:
                try:
                    sock = socket.create_connection(("localhost", port), timeout=1)
                    sock.close()
                    return True
                except:
                    continue
            return False
            
        elif service == "cache_service":
            # Check Redis port
            import socket
            try:
                sock = socket.create_connection(("localhost", 6379), timeout=1)
                sock.close()
                return True
            except:
                return False
                
        else:
            # Generic service check - look for process
            try:
                result = subprocess.run(
                    ["pgrep", "-f", service], 
                    capture_output=True, 
                    timeout=5
                )
                return result.returncode == 0
            except:
                return False
    
    def _suggest_service_start_action(self, service: str) -> str:
        """Suggest how to start a missing service"""
        if service == "database":
            return "Start database: sudo systemctl start postgresql (or install/configure database)"
        elif service == "cache_service":
            return "Start Redis: sudo systemctl start redis (or install Redis)"
        else:
            return f"Start {service}: sudo systemctl start {service}"
    
    def validate_command_prerequisites(self, command: str, args: List[str]) -> Tuple[bool, List[StateViolation]]:
        """Complete validation of command prerequisites"""
        requirements = self.detect_command_state_requirements(command, args)
        violations = self.check_state_prerequisites(requirements)
        
        # Categorize violations
        errors = [v for v in violations if v.severity == "error"]
        warnings = [v for v in violations if v.severity == "warning"]
        
        # Command can proceed if no errors (warnings are OK)
        can_proceed = len(errors) == 0
        
        return can_proceed, violations
    
    def generate_graceful_error_message(self, command: str, args: List[str], violations: List[StateViolation]) -> str:
        """Generate a helpful error message with suggested actions"""
        if not violations:
            return ""
            
        message_parts = [
            f"❌ Cannot execute '{command}' - missing prerequisites:",
            ""
        ]
        
        errors = [v for v in violations if v.severity == "error"]
        warnings = [v for v in violations if v.severity == "warning"]
        
        if errors:
            message_parts.append("🚨 Errors (must fix):")
            for error in errors:
                message_parts.append(f"  • {error.missing_item}")
                message_parts.append(f"    → {error.suggested_action}")
            message_parts.append("")
        
        if warnings:
            message_parts.append("⚠️  Warnings (recommended):")
            for warning in warnings:
                message_parts.append(f"  • {warning.missing_item}")
                message_parts.append(f"    → {warning.suggested_action}")
            message_parts.append("")
        
        message_parts.append("Once prerequisites are met, retry the command.")
        
        return "\n".join(message_parts)