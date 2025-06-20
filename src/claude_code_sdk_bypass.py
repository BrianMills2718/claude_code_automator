#!/usr/bin/env python3
"""
SDK Bypass Mode for CC_AUTOMATOR4
Directly uses Claude Code CLI when SDK has persistent issues
"""

import subprocess
import json
import time
from pathlib import Path
from typing import Dict, Any, Optional
import logging

logger = logging.getLogger(__name__)

class ClaudeCodeCLI:
    """Direct CLI interface bypassing problematic SDK"""
    
    def __init__(self, project_dir: Path):
        self.project_dir = project_dir
        self.cli_path = "claude_code"  # Assumes claude_code is in PATH
        
    def execute_phase(self, prompt: str, max_turns: int = 30) -> Dict[str, Any]:
        """Execute a phase using CLI directly"""
        start_time = time.time()
        
        # Create a temporary prompt file
        prompt_file = self.project_dir / ".cc_automator" / "temp_prompt.txt"
        prompt_file.parent.mkdir(exist_ok=True)
        prompt_file.write_text(prompt)
        
        # Build CLI command
        cmd = [
            self.cli_path,
            "--prompt-file", str(prompt_file),
            "--max-turns", str(max_turns),
            "--no-stream"  # Get complete output
        ]
        
        logger.info(f"Executing CLI command: {' '.join(cmd)}")
        
        try:
            # Run the command
            result = subprocess.run(
                cmd,
                cwd=str(self.project_dir),
                capture_output=True,
                text=True,
                timeout=600  # 10 minute timeout
            )
            
            # Parse results
            duration = time.time() - start_time
            
            # Estimate cost based on duration (rough approximation)
            estimated_cost = duration * 0.001  # $0.001 per second
            
            # Check success
            if result.returncode == 0:
                return {
                    "status": "completed",
                    "cost_usd": estimated_cost,
                    "duration_ms": int(duration * 1000),
                    "session_id": f"cli-{int(start_time)}",
                    "output": result.stdout,
                    "error": None
                }
            else:
                return {
                    "status": "failed",
                    "cost_usd": estimated_cost,
                    "duration_ms": int(duration * 1000),
                    "session_id": f"cli-{int(start_time)}",
                    "output": result.stdout,
                    "error": result.stderr or "CLI execution failed"
                }
                
        except subprocess.TimeoutExpired:
            return {
                "status": "failed",
                "cost_usd": 0.0,
                "duration_ms": 600000,
                "session_id": f"cli-{int(start_time)}",
                "output": "",
                "error": "CLI execution timed out after 10 minutes"
            }
        except Exception as e:
            return {
                "status": "failed",
                "cost_usd": 0.0,
                "duration_ms": int((time.time() - start_time) * 1000),
                "session_id": f"cli-{int(start_time)}",
                "output": "",
                "error": str(e)
            }
        finally:
            # Cleanup
            if prompt_file.exists():
                prompt_file.unlink()
                
    def validate_cli_available(self) -> bool:
        """Check if Claude Code CLI is available"""
        try:
            result = subprocess.run(
                [self.cli_path, "--version"],
                capture_output=True,
                timeout=5
            )
            return result.returncode == 0
        except:
            return False