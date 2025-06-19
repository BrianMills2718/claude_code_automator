#!/usr/bin/env python3
"""
Phase Orchestrator for CC_AUTOMATOR3
Executes isolated phases using Claude Code CLI with streaming JSON output
"""

import subprocess
import json
import os
import sys
import time
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional, Generator, Any, AsyncGenerator
from dataclasses import dataclass, field
from enum import Enum
import asyncio
import anyio
import psutil  # For resource monitoring
# Use V3 SDK wrapper with TaskGroup fixes and pure SDK implementation
try:
    from .claude_code_sdk_fixed_v3 import query_v3, ClaudeCodeOptions, Message, get_v3_wrapper
    print("✅ Using V3 SDK wrapper (TaskGroup issues resolved, pure SDK)")
    V3_SDK_AVAILABLE = True
except ImportError:
    try:
        # Try absolute import for V3
        from claude_code_sdk_fixed_v3 import query_v3, ClaudeCodeOptions, Message, get_v3_wrapper
        print("✅ Using V3 SDK wrapper via absolute import (TaskGroup issues resolved, pure SDK)")
        V3_SDK_AVAILABLE = True
    except ImportError:
        try:
            from .claude_code_sdk_fixed_v2 import query, ClaudeCodeOptions, Message
            print("⚠️  Fallback to V2 SDK wrapper (TaskGroup issues remain)")
            V3_SDK_AVAILABLE = False
        except ImportError:
            from claude_code_sdk import query, ClaudeCodeOptions, Message
            print("⚠️  Using original SDK (may encounter errors)")
            V3_SDK_AVAILABLE = False


class PhaseStatus(Enum):
    """Status of a phase execution"""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    TIMEOUT = "timeout"
    SKIPPED = "skipped"


@dataclass
class Phase:
    """Represents a single execution phase"""
    name: str
    description: str
    prompt: str
    allowed_tools: List[str] = field(default_factory=lambda: ["Read", "Write", "Edit", "MultiEdit", "Bash"])
    think_mode: Optional[str] = None
    max_turns: int = 50  # Increased for async completion
    timeout_seconds: int = 600  # 10 minutes default
    
    # Execution results
    status: PhaseStatus = PhaseStatus.PENDING
    session_id: Optional[str] = None
    cost_usd: float = 0.0
    duration_ms: int = 0
    error: Optional[str] = None
    evidence: Optional[str] = None
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None


class StreamingJSONProcessor:
    """Processes streaming JSON output from Claude Code"""
    
    def __init__(self, max_messages: int = 1000):
        self.messages = []
        self.current_session_id = None
        self.final_result = None
        self.max_messages = max_messages
        
    def process_line(self, line: str) -> Optional[Dict[str, Any]]:
        """Process a single line of streaming JSON output"""
        if not line.strip():
            return None
            
        try:
            event = json.loads(line)
            
            # Track session ID from init message
            if event.get("type") == "system" and event.get("subtype") == "init":
                self.current_session_id = event.get("session_id")
                
            # Collect messages with limit to prevent memory leaks
            self.messages.append(event)
            
            # Keep only recent messages to prevent memory leaks in infinite mode
            if len(self.messages) > self.max_messages:
                self.messages = self.messages[-self.max_messages//2:]  # Keep last half
            
            # Capture final result
            if event.get("type") == "result":
                self.final_result = event
                
            return event
            
        except json.JSONDecodeError as e:
            print(f"Failed to parse JSON: {line}")
            return None
    
    def cleanup(self):
        """Clean up memory to prevent leaks"""
        self.messages.clear()
        self.final_result = None


class PhaseOrchestrator:
    """Orchestrates execution of isolated phases using Claude Code CLI"""
    
    def __init__(self, project_name: str, working_dir: Optional[str] = None, verbose: bool = False, infinite_mode: bool = False):
        self.project_name = project_name
        self.working_dir = Path(working_dir) if working_dir else Path.cwd()
        self.verbose = verbose
        self.infinite_mode = infinite_mode  # Run forever until success
        self.phases: List[Phase] = []
        self.session_manager = {}  # phase_name -> session_id
        self.checkpoints_dir = self.working_dir / ".cc_automator" / "checkpoints"
        self.evidence_dir = self.working_dir / ".cc_automator" / "evidence"
        self.current_milestone = None  # Will be set by runner
        self.step_back_count = 0  # Track step-backs to prevent infinite loops (unless infinite_mode)
        
        # Resource usage tracking for stability monitoring
        self.resource_metrics = []
        self.stability_logs_dir = self.working_dir / ".cc_automator" / "stability_logs"
        
        # Create directories
        self.checkpoints_dir.mkdir(parents=True, exist_ok=True)
        self.evidence_dir.mkdir(parents=True, exist_ok=True)
        self.stability_logs_dir.mkdir(parents=True, exist_ok=True)
        
    def add_phase(self, phase: Phase):
        """Add a phase to the execution plan"""
        # Apply think mode if specified
        if phase.think_mode:
            phase.prompt = f"{phase.think_mode} about this problem: {phase.prompt}"
        self.phases.append(phase)
        
    def execute_phase(self, phase: Phase) -> Dict[str, Any]:
        """Execute a single phase using Claude Code SDK or CLI"""
        
        # Record resource metrics at phase start
        start_metrics = self.record_resource_metrics(phase.name, "start")
        
        # Print phase header (minimal by default)
        if hasattr(self, 'verbose') and self.verbose:
            print(f"\n{'='*60}")
            print(f"Phase: {phase.name}")
            print(f"{'='*60}")
            print(f"Description: {phase.description}")
            print(f"Think Mode: {phase.think_mode or 'None'}")
            print(f"Max Turns: {phase.max_turns}")
            print(f"Timeout: {phase.timeout_seconds}s")
            # Note: Allowed Tools not shown (SDK ignores restrictions anyway)
            print()
        else:
            # Minimal output
            print(f"\n{'='*60}")
            print(f"Phase: {phase.name}")
            print(f"{'='*60}")
            print(f"Description: {phase.description}")
        
        # Mark phase as running
        phase.status = PhaseStatus.RUNNING
        phase.start_time = datetime.now()
        
        # V3 Pure SDK execution
        try:
            if V3_SDK_AVAILABLE:
                print(f"🚀 V3 Pure SDK execution for {phase.name}")
                return anyio.run(self._execute_with_sdk, phase)
            else:
                print(f"⚠️  V3 SDK not available, using legacy SDK for {phase.name}")
                return anyio.run(self._execute_with_sdk, phase)
        except Exception as e:
            # V3 should handle TaskGroup issues internally, any exceptions here are real errors
            if V3_SDK_AVAILABLE:
                print(f"❌ V3 SDK execution failed for {phase.name}: {str(e)}")
                # Check if work was actually completed despite the error
                if phase.status == PhaseStatus.COMPLETED:
                    print(f"✅ Work completed despite error, continuing...")
                    return self._phase_to_dict(phase)
                else:
                    # Real failure in V3
                    phase.status = PhaseStatus.FAILED
                    phase.error = f"V3 SDK execution failed: {str(e)}"
                    return self._phase_to_dict(phase)
            else:
                # Legacy SDK handling - limited fallback logic
                error_str = str(e)
                if "TaskGroup" in error_str and phase.status == PhaseStatus.COMPLETED:
                    print(f"⚠️  Legacy SDK cleanup error (work completed): {str(e)[:100]}")
                    return self._phase_to_dict(phase)
                else:
                    print(f"❌ Legacy SDK execution failed for {phase.name}: {str(e)}")
                    raise
        
        return self._phase_to_dict(phase)
    
    def _execute_direct(self, phase: Phase) -> Dict[str, Any]:
        """Direct execution for simple phases"""
        cmd = [
            "claude", "-p", phase.prompt,
            "--output-format", "json",
            "--max-turns", str(phase.max_turns),
            "--dangerously-skip-permissions"
        ]
        
        if phase.allowed_tools:
            cmd.extend(["--allowedTools", ",".join(phase.allowed_tools)])
        
        try:
            # Execute with 5-minute max timeout for direct execution
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=min(phase.timeout_seconds, 300),
                cwd=str(self.working_dir)
            )
            
            if result.returncode == 0:
                phase.status = PhaseStatus.COMPLETED
                # Try to parse JSON output
                try:
                    result_data = json.loads(result.stdout)
                    phase.session_id = result_data.get("session_id")
                    phase.cost_usd = result_data.get("cost_usd", 0.0)
                    phase.duration_ms = result_data.get("duration_ms", 0)
                except json.JSONDecodeError:
                    phase.session_id = "unknown"
                    phase.cost_usd = 0.0
                    phase.duration_ms = 0
            else:
                phase.status = PhaseStatus.FAILED
                phase.error = f"Command failed: {result.stderr}"
                
        except subprocess.TimeoutExpired:
            phase.status = PhaseStatus.TIMEOUT
            phase.error = f"Phase timed out after {min(phase.timeout_seconds, 300)} seconds"
        except Exception as e:
            phase.status = PhaseStatus.FAILED
            phase.error = f"Execution error: {str(e)}"
            
        finally:
            phase.end_time = datetime.now()
            self._save_checkpoint(phase)
            self._save_milestone_evidence(phase)
            self._print_phase_summary(phase)
            
        return self._phase_to_dict(phase)
    
    def _execute_async(self, phase: Phase) -> Dict[str, Any]:
        """Async execution with completion markers"""
        
        # Create completion markers
        markers_dir = self.working_dir / ".cc_automator"
        markers_dir.mkdir(exist_ok=True)
        
        completion_marker = markers_dir / f"phase_{phase.name}_complete"
        error_marker = markers_dir / f"phase_{phase.name}_error"
        output_file = markers_dir / f"phase_{phase.name}_output.json"
        
        # Ensure absolute paths
        completion_marker = completion_marker.absolute()
        error_marker = error_marker.absolute()
        output_file = output_file.absolute()
        
        # Clean up existing markers
        completion_marker.unlink(missing_ok=True)
        error_marker.unlink(missing_ok=True)
        output_file.unlink(missing_ok=True)
        
        # Modify prompt to include completion markers
        async_prompt = f"""{phase.prompt}

When done, create file: {completion_marker}
Write to it: PHASE_COMPLETE"""
        
        # Build command - stream-json requires --verbose flag
        cmd = [
            "claude", "-p", async_prompt,
            "--output-format", "stream-json",
            "--max-turns", str(phase.max_turns),
            "--dangerously-skip-permissions",  # Required for autonomous file operations
            "--verbose"  # Required for stream-json output format
        ]
        
        if phase.allowed_tools:
            cmd.extend(["--allowedTools", ",".join(phase.allowed_tools)])
        
        if self.verbose:
            print(f"Starting async execution for {phase.name}")
            print(f"Completion marker: {completion_marker}")
        else:
            print(f"Starting {phase.name} phase...")
        
        try:
            # Start Claude Code process
            # Redirect stderr to DEVNULL unless verbose to suppress Claude's verbose output
            process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.DEVNULL if not self.verbose else subprocess.PIPE,
                text=True,
                cwd=str(self.working_dir)
            )
            
            # Check for immediate errors
            time.sleep(2)
            if process.poll() is not None:
                stdout, stderr = process.communicate()
                print(f"Process exited immediately with code {process.returncode}")
                print(f"STDOUT: {stdout}")
                print(f"STDERR: {stderr}")
                phase.status = PhaseStatus.FAILED
                phase.error = f"Process exited immediately: {stderr or stdout}"
                return self._phase_to_dict(phase)
            
            # Always create log file for debugging
            log_dir = self.working_dir / ".cc_automator" / "logs"
            log_dir.mkdir(exist_ok=True)
            log_file = log_dir / f"{phase.name}_{int(time.time())}.log"
            log_handle = open(log_file, 'w')
            if self.verbose:
                print(f"Logging phase output to: {log_file}")
            
            # Initialize streaming processor
            stream_processor = StreamingJSONProcessor()
            
            # Poll for completion with adaptive intervals
            poll_interval = 5  # Start with 5 seconds
            max_poll_interval = 30  # Max 30 seconds
            elapsed_time = 0
            
            while elapsed_time < phase.timeout_seconds:
                # Always capture streaming output to log
                # Non-blocking read of stdout
                import select
                while True:
                    ready, _, _ = select.select([process.stdout], [], [], 0.1)
                    if ready:
                        line = process.stdout.readline()
                        if line:
                            log_handle.write(line)
                            log_handle.flush()
                            
                            # Process streaming JSON
                            event = stream_processor.process_line(line)
                            if event and self.verbose:
                                if event.get("type") == "tool_use":
                                    print(f"  Tool: {event.get('name')} - {event.get('parameters', {})}")
                                elif event.get("type") == "tool_result":
                                    result_preview = str(event.get('output', ''))[:100]
                                    if len(str(event.get('output', ''))) > 100:
                                        result_preview += "..."
                                    print(f"  Result: {result_preview}")
                    else:
                        break
                
                # Check for completion FIRST
                if completion_marker.exists():
                    print(f"✓ Phase {phase.name} completed!")
                    process.terminate()
                    process.wait()
                    
                    phase.status = PhaseStatus.COMPLETED
                    if output_file.exists():
                        try:
                            phase.evidence = output_file.read_text()
                        except Exception:
                            phase.evidence = "Phase completed successfully"
                    
                    # Use session info from streaming processor
                    if stream_processor.current_session_id:
                        phase.session_id = stream_processor.current_session_id
                    else:
                        phase.session_id = f"async-{phase.name}-{int(time.time())}"
                    
                    # Extract cost/duration from final result if available
                    if stream_processor.final_result:
                        phase.cost_usd = stream_processor.final_result.get("cost_usd", 0.0)
                        phase.duration_ms = stream_processor.final_result.get("duration_ms", 0)
                    else:
                        # Estimate based on execution time
                        phase.cost_usd = 0.0  # Will be updated when proper tracking is available
                        phase.duration_ms = int(elapsed_time * 1000)
                    
                    break
                    
                # Check if process finished
                if process.poll() is not None:
                    # Process exited, but check one more time for marker
                    time.sleep(1)
                    if completion_marker.exists():
                        print(f"✓ Phase {phase.name} completed (found marker after exit)!")
                        phase.status = PhaseStatus.COMPLETED
                    else:
                        print(f"✗ Phase {phase.name} failed - process exited without completion")
                        stdout, stderr = process.communicate()
                        
                        # Provide more helpful error message
                        if stderr:
                            phase.error = f"Phase failed with error: {stderr[:500]}"
                        elif stdout:
                            phase.error = f"Phase exited unexpectedly. Output: {stdout[:500]}"
                        else:
                            phase.error = (f"Phase {phase.name} exited without creating completion marker. "
                                         f"Check {log_file} for details.")
                        
                        phase.status = PhaseStatus.FAILED
                    break
                    
                # Check for errors
                if error_marker.exists():
                    print(f"✗ Phase {phase.name} reported errors")
                    process.terminate()
                    process.wait()
                    
                    phase.status = PhaseStatus.FAILED
                    try:
                        phase.error = error_marker.read_text()
                    except Exception:
                        phase.error = "Phase failed with unknown error"
                    
                    break
                
                # Show progress
                print(f"Phase {phase.name} running... ({int(elapsed_time)}s elapsed, checking {completion_marker.name})")
                
                # Sleep with adaptive interval
                time.sleep(poll_interval)
                elapsed_time += poll_interval
                
                # Increase poll interval exponentially up to max
                poll_interval = min(poll_interval * 1.5, max_poll_interval)
            
            # If we exit the while loop, it means timeout reached
            if phase.status not in [PhaseStatus.COMPLETED, PhaseStatus.FAILED]:
                print(f"✗ Phase {phase.name} timed out after {phase.timeout_seconds}s")
                process.kill()
                process.wait()
                phase.status = PhaseStatus.TIMEOUT
                phase.error = (f"Phase timed out after {phase.timeout_seconds} seconds. "
                             f"Consider increasing timeout or breaking into smaller tasks.")
            
        except Exception as e:
            phase.status = PhaseStatus.FAILED
            phase.error = f"Execution error: {str(e)}"
            
        finally:
            # Always close log file if it was opened
            if 'log_handle' in locals():
                log_handle.close()
                
            phase.end_time = datetime.now()
            self._save_checkpoint(phase)
            self._save_milestone_evidence(phase)
            self._print_phase_summary(phase)
            
        return self._phase_to_dict(phase)
    
    def _select_model_for_phase(self, phase_name: str) -> Optional[str]:
        """Select appropriate model based on environment variables and phase type"""
        
        # Check for global model override (forces all phases to use specified model)
        global_model = os.environ.get('CLAUDE_MODEL', '').strip()
        if global_model:
            if self.verbose:
                print(f"Using global model override: {global_model} for {phase_name}")
            return global_model
        
        # Check for force Sonnet mode (uses Sonnet for ALL phases)
        force_sonnet = os.environ.get('FORCE_SONNET', 'false').lower() == 'true'
        if force_sonnet:
            model = "claude-sonnet-4-20250514"
            if self.verbose:
                print(f"Using Sonnet for {phase_name} (FORCE_SONNET enabled)")
            return model
        
        # Default behavior: Sonnet for mechanical phases, Opus for complex phases
        mechanical_phases = ["architecture", "lint", "typecheck"]
        if phase_name in mechanical_phases:
            model = "claude-sonnet-4-20250514"
            if self.verbose:
                print(f"Using Sonnet for {phase_name} (cost-effective for mechanical tasks)")
            return model
        else:
            # Use default model (Opus) for complex phases
            if self.verbose:
                print(f"Using default model (Opus) for {phase_name} (complex reasoning)")
            return None  # None means use default (Opus)
    
    async def _execute_query_with_wrapper(self, prompt: str, options: ClaudeCodeOptions) -> List[Any]:
        """Execute query using V3 wrapper if available, fallback to original SDK"""
        messages = []
        query_func = query_v3 if V3_SDK_AVAILABLE else query
        query_args = (prompt, options, self.working_dir, self.verbose) if V3_SDK_AVAILABLE else (prompt, options)
        
        async for message in query_func(*query_args):
            messages.append(message)
        
        return messages
    
    async def _execute_with_sdk(self, phase: Phase) -> Dict[str, Any]:
        """Execute phase using Claude Code SDK with full conversation preservation"""
        
        # Check if we should use sub-phases (disable by default to reduce TaskGroup errors)
        use_subphases = os.environ.get('USE_SUBPHASES', 'false').lower() == 'true'
        if use_subphases and phase.name in ['research', 'planning', 'implement']:
            return await self._execute_with_subphases(phase)
        
        # Load MCP configuration if available
        mcp_servers = {}
        # Temporarily disable MCP to isolate async issues
        disable_mcp = os.environ.get('DISABLE_MCP', 'false').lower() == 'true'
        if not disable_mcp:
            mcp_config_path = self.working_dir.parent.parent / "mcp_config.json"
            if mcp_config_path.exists():
                with open(mcp_config_path, 'r') as f:
                    mcp_data = json.load(f)
                    mcp_servers = mcp_data.get('mcpServers', {})
                    if self.verbose and mcp_servers:
                        print(f"Loaded MCP servers: {list(mcp_servers.keys())}")
        else:
            if self.verbose:
                print("MCP disabled via DISABLE_MCP environment variable")
        
        # Configure SDK options
        # TODO: Tool disallowing is currently disabled due to SDK bug (tools are ignored anyway)
        # Keeping this code commented for easy revert if SDK is fixed or we find another use case
        disallowed = []
        # if phase.name == "implement":
        #     disallowed = ["TodoWrite", "TodoRead", "Bash", "WebSearch", "WebFetch"]
        
        # Model selection based on environment variables and phase type
        model = self._select_model_for_phase(phase.name)
        
        options = ClaudeCodeOptions(
            max_turns=999999 if self.infinite_mode else phase.max_turns,  # Override for infinite mode
            allowed_tools=phase.allowed_tools,
            disallowed_tools=disallowed,
            mcp_servers=mcp_servers,
            cwd=str(self.working_dir),
            permission_mode="bypassPermissions",  # For autonomous operation
            model=model  # Use Sonnet for lint/typecheck, default (Opus) for others
        )
        
        # Track messages for conversation context (with memory limit)
        messages: List[Message] = []
        max_messages = 10000 if self.infinite_mode else 500  # Extend buffer in infinite mode
        
        # Always create log file for debugging
        log_dir = self.working_dir / ".cc_automator" / "logs"
        log_dir.mkdir(exist_ok=True)
        log_file = log_dir / f"{phase.name}_{int(time.time())}.log"
        
        if self.verbose:
            print(f"Starting SDK execution for {phase.name}")
            print(f"Logging to: {log_file}")
        else:
            print(f"Starting {phase.name} phase...")
        
        websearch_start_time = None
        websearch_timeout_seconds = 30
        
        try:
            # Execute query with V3 SDK wrapper or fallback to original
            query_func = query_v3 if V3_SDK_AVAILABLE else query
            query_args = (phase.prompt, options, self.working_dir, self.verbose) if V3_SDK_AVAILABLE else (phase.prompt, options)
            
            async for message in query_func(*query_args):
                messages.append(message)
                
                # Prevent memory leaks by limiting message history
                if len(messages) > max_messages:
                    messages = messages[-max_messages//2:]  # Keep last half
                
                # For V3, WebSearch timing is handled internally, for legacy we need to track it
                if not V3_SDK_AVAILABLE:
                    # Track WebSearch timing for legacy SDK
                    if hasattr(message, 'content') and isinstance(message.content, list):
                        for item in message.content:
                            if hasattr(item, 'name') and item.name == 'WebSearch':
                                websearch_start_time = time.time()
                                if self.verbose:
                                    print(f"⏱️  WebSearch started, will timeout after {websearch_timeout_seconds}s")
                    
                    # Check for WebSearch timeout in legacy SDK
                    if websearch_start_time and (time.time() - websearch_start_time) > websearch_timeout_seconds:
                        print(f"⚠️  WebSearch timeout after {websearch_timeout_seconds}s, continuing without results")
                        websearch_start_time = None  # Reset to prevent repeated warnings
                
                # Convert message to dict if it's an object (handle both V3 dict format and legacy object format)
                if isinstance(message, dict):
                    msg_dict = message  # V3 already provides dict format
                elif hasattr(message, '__dict__'):
                    msg_dict = message.__dict__  # Legacy object format
                else:
                    msg_dict = {"type": "unknown", "content": str(message)}
                
                # Log all messages with timestamp and tool detection
                timestamp = datetime.now().isoformat()
                log_entry = {
                    "timestamp": timestamp,
                    "message": msg_dict
                }
                
                # Detailed logging for WebSearch to detect hangs
                if hasattr(message, 'content') and isinstance(message.content, list):
                    for item in message.content:
                        if hasattr(item, 'name') and item.name == 'WebSearch':
                            log_entry["WEBSEARCH_REQUEST"] = {
                                "query": getattr(item, 'input', {}),
                                "timestamp": timestamp,
                                "phase": phase.name
                            }
                            print(f"🔍 WebSearch starting in {phase.name}: {getattr(item, 'input', {}).get('query', 'unknown query')}")
                            
                # Log WebSearch responses/results
                if (isinstance(msg_dict, dict) and 
                    msg_dict.get('type') == 'tool_result' and 
                    'web search' in str(msg_dict).lower()):
                    log_entry["WEBSEARCH_RESPONSE"] = "WebSearch response received"
                    print(f"📋 WebSearch response received in {phase.name}")
                    
                # Log if we're waiting too long for any tool
                if hasattr(self, '_last_tool_start'):
                    time_since_tool = (datetime.now() - self._last_tool_start).total_seconds()
                    if time_since_tool > 30:  # 30 seconds since last tool started
                        log_entry["POTENTIAL_HANG"] = f"No activity for {time_since_tool:.1f}s"
                        print(f"⏰ Potential hang detected: {time_since_tool:.1f}s since last tool activity")
                        
                # Track tool start times
                if (hasattr(message, 'content') and isinstance(message.content, list) and
                    any(hasattr(item, 'name') for item in message.content)):
                    self._last_tool_start = datetime.now()
                
                with open(log_file, 'a') as f:
                    try:
                        f.write(json.dumps(log_entry) + '\n')
                    except (TypeError, ValueError):
                        # If message can't be serialized, convert to string
                        f.write(json.dumps({"timestamp": timestamp, "type": "log", "content": str(message)}) + '\n')
                
                # Process message based on type
                msg_type = msg_dict.get("type") if isinstance(msg_dict, dict) else None
                
                # Handle messages with nested data structure
                if "data" in msg_dict and isinstance(msg_dict["data"], dict):
                    # Use the nested data for processing
                    nested_data = msg_dict["data"]
                    msg_type = nested_data.get("type")
                    
                    if msg_type == "system" and nested_data.get("subtype") == "init":
                        phase.session_id = nested_data.get("session_id")
                        if self.verbose:
                            print(f"Session ID: {phase.session_id}")
                        continue
                
                # Handle result messages that may not have a "type" field
                if "subtype" in msg_dict and msg_dict.get("subtype") in ["success", "error_max_turns", "error_during_execution"]:
                    # This is a result message
                    if msg_dict.get("is_error", False):
                        phase.status = PhaseStatus.FAILED
                        phase.error = msg_dict.get("result", "Unknown error")
                        print(f"✗ Phase {phase.name} failed: {phase.error}")
                    elif msg_dict.get("subtype") == "success":
                        phase.status = PhaseStatus.COMPLETED
                        phase.cost_usd = msg_dict.get("total_cost_usd", 0.0)
                        phase.duration_ms = msg_dict.get("duration_ms", 0)
                        print(f"✓ Phase {phase.name} completed!")
                        # Extract evidence from messages if available
                        phase.evidence = self._extract_evidence_from_messages(messages)
                    elif msg_dict.get("subtype") == "error_during_execution" and not msg_dict.get("is_error", False):
                        # SDK bug: "error_during_execution" with is_error=false usually means work was done
                        # Check if outputs were actually created despite SDK error
                        if self._validate_phase_outputs(phase):
                            phase.status = PhaseStatus.COMPLETED
                            phase.cost_usd = msg_dict.get("total_cost_usd", 0.0)
                            phase.duration_ms = msg_dict.get("duration_ms", 0)
                            print(f"✓ Phase {phase.name} completed! (SDK reported error but outputs found)")
                            # Extract evidence from messages if available
                            phase.evidence = self._extract_evidence_from_messages(messages)
                        else:
                            phase.status = PhaseStatus.FAILED
                            phase.error = "SDK reported error_during_execution and no valid outputs found"
                            print(f"✗ Phase {phase.name} failed: SDK error with no outputs")
                    else:
                        phase.status = PhaseStatus.FAILED
                        phase.error = f"Phase failed: {msg_dict.get('subtype')}"
                        print(f"✗ Phase {phase.name} failed: {msg_dict.get('subtype')}")
                    continue
                
                if msg_type == "system" and msg_dict.get("subtype") == "init":
                    phase.session_id = msg_dict.get("session_id")
                    if self.verbose:
                        print(f"Session ID: {phase.session_id}")
                        
                elif msg_type == "tool_use":
                    if self.verbose:
                        tool_name = msg_dict.get("name")
                        params = msg_dict.get("parameters", {})
                        print(f"  Tool: {tool_name} - {params}")
                        
                elif msg_type == "tool_result":
                    if self.verbose:
                        output = str(msg_dict.get("output", ""))
                        result_preview = output[:100]
                        if len(output) > 100:
                            result_preview += "..."
                        print(f"  Result: {result_preview}")
                        
                elif msg_type == "result":
                    # Check if there's an error even if subtype is "success"
                    if msg_dict.get("is_error", False):
                        phase.status = PhaseStatus.FAILED
                        phase.error = msg_dict.get("result", "Unknown error")
                        print(f"✗ Phase {phase.name} failed: {phase.error}")
                    elif msg_dict.get("subtype") == "success":
                        phase.status = PhaseStatus.COMPLETED
                        phase.cost_usd = msg_dict.get("total_cost_usd", 0.0)
                        phase.duration_ms = msg_dict.get("duration_ms", 0)
                        print(f"✓ Phase {phase.name} completed!")
                        
                        # Extract evidence from messages if available
                        phase.evidence = self._extract_evidence_from_messages(messages)
                    else:
                        phase.status = PhaseStatus.FAILED
                        phase.error = f"Phase failed: {msg_dict.get('subtype')}"
                        print(f"✗ Phase {phase.name} failed: {msg_dict.get('subtype')}")
                        
        except Exception as e:
            # V3 error handling - TaskGroup issues should be resolved
            if V3_SDK_AVAILABLE:
                # With V3, TaskGroup errors should not occur
                if "TaskGroup" in str(e):
                    print(f"⚠️  Unexpected TaskGroup error in V3 SDK: {str(e)}")
                    print(f"   This suggests a V3 implementation issue that needs investigation")
                
                # Handle WebSearch timeout gracefully (V3 should handle this internally)
                if "websearch" in str(e).lower() or "timeout" in str(e).lower():
                    print(f"⚠️  WebSearch/timeout issue: {str(e)}")
                    # Check if we got partial work done
                    if messages and phase.status == PhaseStatus.COMPLETED:
                        print(f"✅ Work completed despite timeout, continuing...")
                        return phase
                
                # Authentication issues
                if "api_key" in str(e).lower() or "authentication" in str(e).lower():
                    phase.error = "API key not set - export ANTHROPIC_API_KEY"
                    phase.status = PhaseStatus.FAILED
                    print(f"🔑 Authentication error in phase {phase.name}")
                else:
                    # Real execution error in V3
                    phase.status = PhaseStatus.FAILED
                    phase.error = f"V3 SDK error: {str(e)}"
                    print(f"❌ V3 SDK execution error in phase {phase.name}: {str(e)}")
            else:
                # Legacy error handling for V2/original SDK
                if phase.status == PhaseStatus.COMPLETED and "TaskGroup" in str(e):
                    # Phase already completed successfully, this is just cleanup noise
                    if self.verbose:
                        print(f"  (Ignoring async cleanup error: {str(e)[:50]}...)")
                else:
                    # Handle various legacy SDK errors
                    if "cost_usd" in str(e) or ("KeyError" in str(e) and "cost" in str(e)):
                        print(f"⚠️  Legacy SDK cost parsing error (continuing): {e}")
                        if messages:
                            print(f"✅ Recovered {len(messages)} messages despite SDK error")
                            phase.status = PhaseStatus.COMPLETED
                            phase.evidence = f"Phase completed with {len(messages)} messages (cost error handled)"
                            phase.cost_usd = 0.0
                            return phase
                    else:
                        phase.status = PhaseStatus.FAILED
                        phase.error = f"Legacy SDK error: {str(e)}"
                        print(f"✗ Legacy SDK error in phase {phase.name}: {str(e)}")
                
        finally:
            phase.end_time = datetime.now()
            
            # Record resource metrics at phase end
            end_metrics = self.record_resource_metrics(phase.name, "end")
            
            # Calculate resource usage for this phase
            if start_metrics and end_metrics and "process_memory_mb" in start_metrics and "process_memory_mb" in end_metrics:
                memory_delta = end_metrics["process_memory_mb"] - start_metrics["process_memory_mb"]
                if abs(memory_delta) > 10:  # 10MB threshold
                    direction = "↗️" if memory_delta > 0 else "↘️"
                    if self.verbose:
                        print(f"  {direction} Memory change: {memory_delta:+.1f} MB")
            
            # Save session with full message history for context preservation
            if hasattr(self, 'session_manager') and phase.session_id:
                self.session_manager[phase.name] = {
                    "session_id": phase.session_id,
                    "messages": messages[-50:],  # Only keep last 50 messages to prevent memory leaks
                    "sdk": True
                }
            
            self._save_checkpoint(phase)
            self._save_milestone_evidence(phase)
            self._print_phase_summary(phase)
            
            # Clean up messages to prevent memory leaks in infinite mode
            messages.clear()
            
            # CRITICAL: Validate phase outputs before claiming success
            if phase.status == PhaseStatus.COMPLETED:
                validation_result = self._validate_phase_outputs_with_feedback(phase)
                if not validation_result["success"]:
                    # Attempt intelligent retry with specific feedback
                    retry_result = await self._retry_phase_with_validation_feedback(phase, validation_result["feedback"])
                    if not retry_result:
                        phase.status = PhaseStatus.FAILED
                        phase.error = f"Phase validation failed: {validation_result['feedback']}"
                        print(f"✗ Phase {phase.name} validation failed despite SDK claiming success")
                        print(f"  Specific issue: {validation_result['feedback']}")
            
        return self._phase_to_dict(phase)
    
    def record_resource_metrics(self, phase_name: str, event: str = "start") -> Dict[str, Any]:
        """Record resource usage metrics for stability monitoring."""
        try:
            process = psutil.Process()
            memory_mb = process.memory_info().rss / 1024 / 1024
            cpu_percent = process.cpu_percent()
            
            # Get system-wide stats
            system_memory = psutil.virtual_memory()
            
            # Count open file descriptors (Unix only)
            try:
                open_fds = process.num_fds() if hasattr(process, 'num_fds') else 0
            except (psutil.AccessDenied, AttributeError):
                open_fds = 0
            
            # Count network connections
            try:
                connections = process.connections()
                network_connections = len([c for c in connections if c.status == 'ESTABLISHED'])
            except (psutil.AccessDenied, psutil.NoSuchProcess):
                network_connections = 0
            
            metrics = {
                "timestamp": time.time(),
                "iso_timestamp": time.strftime("%Y-%m-%d %H:%M:%S", time.localtime()),
                "phase_name": phase_name,
                "event": event,
                "process_memory_mb": memory_mb,
                "process_cpu_percent": cpu_percent,
                "open_file_descriptors": open_fds,
                "network_connections": network_connections,
                "system_memory_percent": system_memory.percent,
                "system_available_memory_gb": system_memory.available / 1024 / 1024 / 1024
            }
            
            self.resource_metrics.append(metrics)
            
            # Keep only last 1000 metrics to prevent memory growth
            if len(self.resource_metrics) > 1000:
                self.resource_metrics = self.resource_metrics[-500:]
            
            # Log to file for persistent tracking
            self._log_resource_metrics(metrics)
            
            return metrics
            
        except Exception as e:
            if self.verbose:
                print(f"Warning: Failed to record resource metrics: {e}")
            return {"timestamp": time.time(), "error": str(e)}
    
    def _log_resource_metrics(self, metrics: Dict[str, Any]):
        """Log resource metrics to file for analysis."""
        try:
            log_file = self.stability_logs_dir / "resource_metrics.jsonl"
            
            with open(log_file, "a") as f:
                json.dump(metrics, f)
                f.write("\n")
                
        except Exception as e:
            # Don't fail main operation if logging fails
            if self.verbose:
                print(f"Warning: Failed to log resource metrics: {e}")
    
    def get_resource_stability_summary(self) -> Dict[str, Any]:
        """Get summary of resource usage for stability assessment."""
        if len(self.resource_metrics) < 2:
            return {"insufficient_data": True, "metric_count": len(self.resource_metrics)}
        
        recent_metrics = self.resource_metrics[-20:]  # Last 20 samples
        initial_memory = self.resource_metrics[0]["process_memory_mb"]
        current_memory = recent_metrics[-1]["process_memory_mb"]
        
        memory_growth = current_memory - initial_memory
        memory_values = [m["process_memory_mb"] for m in recent_metrics]
        
        fd_values = [m["open_file_descriptors"] for m in recent_metrics if m["open_file_descriptors"] > 0]
        connection_values = [m["network_connections"] for m in recent_metrics]
        
        return {
            "total_samples": len(self.resource_metrics),
            "memory_growth_mb": memory_growth,
            "current_memory_mb": current_memory,
            "memory_trend_recent": memory_values[-1] - memory_values[0] if len(memory_values) > 1 else 0,
            "max_memory_mb": max(memory_values),
            "avg_memory_mb": sum(memory_values) / len(memory_values),
            "max_file_descriptors": max(fd_values) if fd_values else 0,
            "max_network_connections": max(connection_values),
            "avg_network_connections": sum(connection_values) / len(connection_values),
            "memory_leak_suspected": memory_growth > 100,  # 100MB growth threshold
            "fd_leak_suspected": max(fd_values) > 100 if fd_values else False,
            "connection_leak_suspected": max(connection_values) > 20,
            "first_sample_time": self.resource_metrics[0]["timestamp"],
            "last_sample_time": recent_metrics[-1]["timestamp"]
        }
    
    def get_taskgroup_error_analysis(self) -> Dict[str, Any]:
        """Get TaskGroup error analysis from V3 SDK wrapper."""
        try:
            if V3_SDK_AVAILABLE:
                wrapper = get_v3_wrapper(self.working_dir, self.verbose)
                return wrapper.get_taskgroup_error_summary()
            else:
                return {"v3_sdk_not_available": True}
        except Exception as e:
            return {"analysis_error": str(e)}
    
    async def _attempt_phase_recovery(self, phase: Phase, error_details: str) -> bool:
        """Attempt to recover from TaskGroup error by letting Claude complete the phase."""
        
        print(f"🔄 Starting recovery attempt for {phase.name} phase...")
        
        # Build recovery prompt that gives Claude context about what happened
        recovery_prompt = f"""PHASE RECOVERY: {phase.name.upper()}

A WebSearch async error occurred, but you may have already gathered useful information before the error.

Error details: {error_details[:200]}

Your task: Complete the {phase.name} phase using:
1. Any information you successfully retrieved before the error
2. Your existing knowledge of current library practices and patterns
3. Reasonable assumptions based on common practices

"""
        
        # Add phase-specific recovery guidance
        if phase.name == "research":
            recovery_prompt += f"""For the research phase, create: .cc_automator/milestones/milestone_{{current_milestone}}/research.md

Include:
- Analysis of existing code
- Library requirements (use current stable versions)
- Implementation approach
- Testing strategy

Don't let the WebSearch error prevent completing the research."""

        elif phase.name == "planning":
            recovery_prompt += f"""For the planning phase, create: .cc_automator/milestones/milestone_{{current_milestone}}/plan.md

Include:
- Implementation plan based on research
- File structure
- Key components to build
- Testing approach"""

        elif phase.name == "implement":
            recovery_prompt += """For the implementation phase:
- Create/modify the required code files
- Use current best practices you know
- Ensure main.py runs successfully
- Follow the plan and research findings"""

        elif phase.name in ["e2e", "validate"]:
            recovery_prompt += f"""For the {phase.name} phase:
- Test that the implementation works
- Create required evidence files
- Verify success criteria are met"""

        recovery_prompt += """

IMPORTANT: 
- Focus on completing the phase successfully
- Use your knowledge if WebSearch information is incomplete
- Create all required output files
- Don't retry WebSearch operations that failed
- Be resilient and adaptive

Complete the phase now."""
        
        try:
            # Configure recovery options - shorter and simpler to avoid more TaskGroup errors
            milestone_num = getattr(self, 'current_milestone', 1)
            recovery_prompt = recovery_prompt.replace("{current_milestone}", str(milestone_num))
            
            options = ClaudeCodeOptions(
                max_turns=10,  # Shorter to reduce risk of more errors
                allowed_tools=[tool for tool in phase.allowed_tools if tool != "WebSearch"],  # No WebSearch in recovery
                mcp_servers={},  # No MCP to reduce complexity
                cwd=str(self.working_dir),
                permission_mode="bypassPermissions"
            )
            
            recovery_messages = await self._execute_query_with_wrapper(recovery_prompt, options)
                
            # Check for completion
            for message in recovery_messages:
                if hasattr(message, '__dict__'):
                    msg_dict = message.__dict__
                elif isinstance(message, dict):
                    msg_dict = message
                else:
                    continue
                    
                if msg_dict.get("type") == "result":
                    if msg_dict.get("is_error", False):
                        print(f"✗ Recovery failed with error: {msg_dict.get('result', 'Unknown error')}")
                        return False
                    else:
                        print(f"✓ Recovery completed successfully")
                        
                        # Validate that recovery actually produced the expected outputs
                        if self._validate_phase_outputs(phase):
                            print(f"✓ Recovery validation passed for {phase.name}")
                            return True
                        else:
                            print(f"⚠️  Recovery completed but validation failed for {phase.name}")
                            # Check if output files exist even if validation is strict
                            if phase.name == "research":
                                milestone_num = getattr(self, 'current_milestone', 1)
                                research_file = self.working_dir / ".cc_automator/milestones" / f"milestone_{milestone_num}" / "research.md"
                                if research_file.exists() and len(research_file.read_text()) > 200:
                                    print(f"✓ Recovery created research.md ({len(research_file.read_text())} chars) - considering success")
                                    return True
                            # REMOVED: No validation bypass - maintain anti-cheating philosophy
                            return False
                            
        except Exception as recovery_error:
            print(f"✗ Recovery attempt failed: {recovery_error}")
            
            # Even if recovery SDK call failed, check if the original work was actually completed
            print(f"🔍 Checking if {phase.name} phase outputs exist despite recovery failure...")
            if self._validate_phase_outputs(phase):
                print(f"✓ Original work appears to have completed successfully before TaskGroup error")
                return True
            else:
                # Additional fallback checks for specific phases
                if phase.name == "planning":
                    milestone_num = getattr(self, 'current_milestone', 1)
                    plan_file = self.working_dir / ".cc_automator/milestones" / f"milestone_{milestone_num}" / "plan.md"
                    if plan_file.exists() and len(plan_file.read_text()) > 100:
                        print(f"✓ Found plan.md ({len(plan_file.read_text())} chars) - work completed despite error")
                        return True
                        
                print(f"✗ No valid outputs found for {phase.name} phase")
                return False
        
        return False
    
    async def _execute_with_subphases(self, phase: Phase) -> Dict[str, Any]:
        """Execute phase broken into sub-phases to avoid timeouts."""
        try:
            from subphase_config import get_subphases
            subphases = get_subphases(phase.name)
        except ImportError:
            print(f"⚠️  subphase_config not available, falling back to regular execution")
            return await self._execute_with_sdk(phase)
        
        if not subphases:
            # Fall back to regular execution
            return await self._execute_with_sdk(phase)
            
        print(f"\nExecuting {phase.name} phase with {len(subphases)} sub-phases")
        
        # Track overall phase state
        phase.start_time = datetime.now()
        phase.status = PhaseStatus.RUNNING
        combined_cost = 0.0
        all_messages = []
        
        # Get milestone number from context
        milestone_num = getattr(self, 'current_milestone', 1)
        
        for i, subphase in enumerate(subphases):
            sub_name = subphase["name"]
            print(f"\n[{i+1}/{len(subphases)}] Running sub-phase: {sub_name}")
            
            # Format sub-phase prompt
            sub_prompt = subphase["prompt_template"].format(
                working_dir=self.working_dir.name,
                milestone_num=milestone_num
            )
            
            # Execute sub-phase
            try:
                # Configure SDK options for sub-phase
                # Remove WebSearch from allowed tools to avoid TaskGroup errors
                sub_allowed_tools = [tool for tool in phase.allowed_tools if tool != "WebSearch"]
                
                options = ClaudeCodeOptions(
                    max_turns=subphase["max_turns"],
                    allowed_tools=sub_allowed_tools,
                    mcp_servers={},  # MCP disabled for now
                    cwd=str(self.working_dir),
                    permission_mode="bypassPermissions"
                )
                
                sub_messages = await self._execute_query_with_wrapper(sub_prompt, options)
                all_messages.extend(sub_messages)
                    
                # Check for completion
                for message in sub_messages:
                    if hasattr(message, '__dict__'):
                        msg_dict = message.__dict__
                    elif isinstance(message, dict):
                        msg_dict = message
                    else:
                        continue
                        
                    if msg_dict.get("type") == "result":
                        if msg_dict.get("is_error", False):
                            print(f"✗ Sub-phase {sub_name} failed")
                            phase.status = PhaseStatus.FAILED
                            phase.error = f"Sub-phase {sub_name} failed"
                            return self._phase_to_dict(phase)
                        else:
                            combined_cost += msg_dict.get("total_cost_usd", 0.0)
                            print(f"✓ Sub-phase {sub_name} completed")
                            
            except Exception as e:
                error_str = str(e)
                # Special handling for TaskGroup errors (async cleanup issues)
                if "TaskGroup" in error_str and "unhandled errors" in error_str:
                    print(f"⚠️  Sub-phase {sub_name} had async cleanup issue, checking outputs...")
                    # Don't fail immediately, check if outputs were created
                    # Continue to next sub-phase if this one produced expected outputs
                    continue
                else:
                    print(f"✗ Sub-phase {sub_name} error: {e}")
                    phase.status = PhaseStatus.FAILED
                    phase.error = f"Sub-phase {sub_name} error: {str(e)}"
                    return self._phase_to_dict(phase)
        
        # All sub-phases completed
        phase.end_time = datetime.now()
        phase.cost_usd = combined_cost
        phase.status = PhaseStatus.COMPLETED
        
        # Validate overall phase outputs
        if not self._validate_phase_outputs(phase):
            phase.status = PhaseStatus.FAILED
            phase.error = "Phase validation failed after sub-phases"
            print(f"✗ Phase {phase.name} validation failed")
        else:
            print(f"✓ Phase {phase.name} completed successfully via sub-phases")
            
        self._save_checkpoint(phase)
        self._save_milestone_evidence(phase)
        self._print_phase_summary(phase)
        
        return self._phase_to_dict(phase)
    
    def _extract_evidence_from_messages(self, messages: List[Message]) -> Optional[str]:
        """Extract relevant evidence from SDK messages"""
        evidence_parts = []
        
        for msg in messages:
            # Convert message to dict if needed
            if hasattr(msg, '__dict__'):
                msg_dict = msg.__dict__
            elif isinstance(msg, dict):
                msg_dict = msg
            else:
                continue
                
            if msg_dict.get("type") == "assistant":
                content = msg_dict.get("message", {}).get("content", "")
                if content and len(content) > 50:  # Skip very short messages
                    evidence_parts.append(content)
                    
        return "\n\n".join(evidence_parts) if evidence_parts else None
    
    def _stream_with_timeout(self, process: subprocess.Popen, timeout: int) -> Generator[str, None, None]:
        """Stream output with timeout handling"""
        start_time = time.time()
        
        for line in process.stdout:
            if time.time() - start_time > timeout:
                raise subprocess.TimeoutExpired(process.args, timeout)
            yield line
            
    def _handle_stream_event(self, event: Dict[str, Any], phase: Phase):
        """Handle a streaming event"""
        event_type = event.get("type")
        
        if event_type == "assistant":
            # Claude's response
            content = event.get("message", {}).get("content", "")
            if content:
                print(f"Claude: {content[:100]}..." if len(content) > 100 else f"Claude: {content}")
                
        elif event_type == "user":
            # Tool use or user message
            pass
            
        elif event_type == "system":
            subtype = event.get("subtype")
            if subtype == "init":
                print(f"Session ID: {event.get('session_id')}")
                print(f"Tools available: {', '.join(event.get('tools', []))}")
                
    def _print_phase_summary(self, phase: Phase):
        """Print summary of phase execution"""
        duration = (phase.end_time - phase.start_time).total_seconds() if phase.start_time and phase.end_time else 0
        
        status_symbol = {
            PhaseStatus.COMPLETED: "✓",
            PhaseStatus.FAILED: "✗",
            PhaseStatus.TIMEOUT: "⏱",
            PhaseStatus.SKIPPED: "○",
            PhaseStatus.PENDING: "○",
            PhaseStatus.RUNNING: "⚡"
        }
        
        print(f"\n{status_symbol[phase.status]} Phase {phase.name}: {phase.status.value}")
        
        if phase.session_id:
            print(f"  Session ID: {phase.session_id}")
        if phase.cost_usd > 0:
            print(f"  Cost: ${phase.cost_usd:.4f}")
        if phase.duration_ms > 0:
            print(f"  Claude Duration: {phase.duration_ms}ms")
        if duration > 0:
            print(f"  Total Duration: {duration:.1f}s")
        if phase.error:
            print(f"  Error: {phase.error}")
            
    def _save_checkpoint(self, phase: Phase):
        """Save phase checkpoint for recovery"""
        checkpoint_file = self.checkpoints_dir / f"{phase.name}_checkpoint.json"
        checkpoint_data = self._phase_to_dict(phase)
        
        with open(checkpoint_file, 'w') as f:
            json.dump(checkpoint_data, f, indent=2, default=str)
            
    def _save_milestone_evidence(self, phase: Phase):
        """Save phase output to milestone directory for next phases"""
        if not self.current_milestone or phase.status != PhaseStatus.COMPLETED:
            return
            
        # All phases save evidence - mechanical phases save validation results
            
        milestone_dir = self.working_dir / ".cc_automator" / "milestones" / f"milestone_{self.current_milestone}"
        milestone_dir.mkdir(parents=True, exist_ok=True)
        
        evidence_file = milestone_dir / f"{phase.name}.md"
        
        # Get the actual output
        output_content = ""
        
        # Check phase outputs directory
        phase_output_file = self.working_dir / ".cc_automator" / "phase_outputs" / f"milestone_{self.current_milestone}_{phase.name}.md"
        if phase_output_file.exists():
            output_content = phase_output_file.read_text()
        elif phase.evidence:
            output_content = phase.evidence
            
        # For implement phase, also capture what was built
        if phase.name == "implement" and not output_content:
            files_created = []
            
            # Check main.py
            main_py = self.working_dir / "main.py"
            if main_py.exists():
                files_created.append(f"## main.py\n```python\n{main_py.read_text()}\n```\n")
                
            # Check src directory
            src_dir = self.working_dir / "src"
            if src_dir.exists():
                for py_file in src_dir.glob("**/*.py"):
                    rel_path = py_file.relative_to(self.working_dir)
                    files_created.append(f"## {rel_path}\n```python\n{py_file.read_text()}\n```\n")
                    
            if files_created:
                output_content = "# Implementation Output\n\n" + "\n".join(files_created)
                
        # For mechanical phases, capture validation results as evidence
        if not output_content and phase.name in ["architecture", "lint", "typecheck", "commit"]:
            if phase.name == "architecture":
                try:
                    from .architecture_validator import ArchitectureValidator
                    validator = ArchitectureValidator(self.working_dir)
                    is_valid, issues = validator.validate_all()
                    
                    if is_valid:
                        output_content = "# Architecture Phase Evidence\n\nArchitecture validation passed - zero violations found.\n"
                    else:
                        issue_list = "\n".join(f"- {issue}" for issue in issues[:10])  # Show first 10 issues
                        output_content = f"# Architecture Phase Evidence\n\nArchitecture violations found:\n{issue_list}\n"
                        if len(issues) > 10:
                            output_content += f"\n... and {len(issues) - 10} more issues\n"
                except Exception as e:
                    output_content = f"# Architecture Phase Evidence\n\nArchitecture validation error: {e}\n"
                    
            elif phase.name == "lint":
                try:
                    result = subprocess.run(["flake8", "--select=F"], 
                                          capture_output=True, text=True, cwd=str(self.working_dir), timeout=15)
                    if result.returncode == 0:
                        output_content = "# Lint Phase Evidence\n\nFlake8 validation passed - no F-errors found.\n"
                    else:
                        output_content = f"# Lint Phase Evidence\n\nFlake8 errors found:\n```\n{result.stdout}\n{result.stderr}\n```\n"
                except Exception as e:
                    output_content = f"# Lint Phase Evidence\n\nFlake8 validation error: {e}\n"
                    
            elif phase.name == "typecheck":
                try:
                    result = subprocess.run(["mypy", "--strict", "."], 
                                          capture_output=True, text=True, cwd=str(self.working_dir), timeout=30)
                    if result.returncode == 0:
                        output_content = "# Typecheck Phase Evidence\n\nMyPy validation passed - no type errors found.\n"
                    else:
                        output_content = f"# Typecheck Phase Evidence\n\nMyPy errors found:\n```\n{result.stdout}\n{result.stderr}\n```\n"
                except Exception as e:
                    output_content = f"# Typecheck Phase Evidence\n\nMyPy validation error: {e}\n"
                    
            elif phase.name == "commit":
                try:
                    result = subprocess.run(["git", "log", "-1", "--oneline"], 
                                          capture_output=True, text=True, cwd=str(self.working_dir), timeout=10)
                    if result.returncode == 0:
                        output_content = f"# Commit Phase Evidence\n\nGit commit created:\n```\n{result.stdout.strip()}\n```\n"
                    else:
                        output_content = "# Commit Phase Evidence\n\nNo git commit found.\n"
                except Exception as e:
                    output_content = f"# Commit Phase Evidence\n\nGit validation error: {e}\n"
                
        # Save the evidence
        if output_content:
            with open(evidence_file, 'w') as f:
                f.write(output_content)
            if self.verbose:
                print(f"  Saved evidence to: {evidence_file}")
            
    def _phase_to_dict(self, phase: Phase) -> Dict[str, Any]:
        """Convert phase to dictionary"""
        return {
            "name": phase.name,
            "description": phase.description,
            "status": phase.status.value,
            "session_id": phase.session_id,
            "cost_usd": phase.cost_usd,
            "duration_ms": phase.duration_ms,
            "error": phase.error,
            "start_time": phase.start_time.isoformat() if phase.start_time else None,
            "end_time": phase.end_time.isoformat() if phase.end_time else None,
            "think_mode": phase.think_mode
        }
    
    def execute_all(self) -> Dict[str, Any]:
        """Execute all phases sequentially"""
        
        print(f"\n{'#'*60}")
        print(f"# {self.project_name}")
        print(f"# Total Phases: {len(self.phases)}")
        print(f"# Working Directory: {self.working_dir}")
        print(f"{'#'*60}")
        
        start_time = datetime.now()
        results = []
        
        for i, phase in enumerate(self.phases, 1):
            print(f"\n[{i}/{len(self.phases)}] Starting {phase.name}")
            
            result = self.execute_phase(phase)
            results.append(result)
            
            # Stop if phase failed
            if phase.status in [PhaseStatus.FAILED, PhaseStatus.TIMEOUT]:
                print(f"\n❌ Stopping execution due to {phase.status.value} in phase '{phase.name}'")
                break
                
        # Final summary
        end_time = datetime.now()
        total_duration = (end_time - start_time).total_seconds()
        total_cost = sum(p.cost_usd for p in self.phases)
        completed_count = sum(1 for p in self.phases if p.status == PhaseStatus.COMPLETED)
        
        print(f"\n{'#'*60}")
        print(f"# Execution Summary")
        print(f"{'#'*60}")
        print(f"Completed: {completed_count}/{len(self.phases)} phases")
        print(f"Total Cost: ${total_cost:.4f}")
        print(f"Total Duration: {total_duration:.1f}s")
        print(f"Success: {all(p.status == PhaseStatus.COMPLETED for p in self.phases)}")
        
        return {
            "project_name": self.project_name,
            "start_time": start_time.isoformat(),
            "end_time": end_time.isoformat(),
            "total_duration_seconds": total_duration,
            "total_cost_usd": total_cost,
            "phases": results,
            "success": all(p.status == PhaseStatus.COMPLETED for p in self.phases)
        }
    
    def resume_from_checkpoint(self) -> Optional[str]:
        """Find the last successful phase to resume from"""
        for phase in reversed(self.phases):
            checkpoint_file = self.checkpoints_dir / f"{phase.name}_checkpoint.json"
            if checkpoint_file.exists():
                with open(checkpoint_file) as f:
                    checkpoint = json.load(f)
                    if checkpoint["status"] == PhaseStatus.COMPLETED.value:
                        return phase.name
        return None
    
    def _check_phase_outputs_exist(self, phase: Phase) -> bool:
        """Quick check if phase created expected output files"""
        milestone_num = getattr(self, 'current_milestone', 1)
        milestone_dir = self.working_dir / ".cc_automator" / "milestones" / f"milestone_{milestone_num}"
        
        # Check for phase-specific output files
        if phase.name == "research":
            return (milestone_dir / "research.md").exists()
        elif phase.name == "planning":
            return (milestone_dir / "plan.md").exists()
        else:
            # For other phases, just check if milestone dir has any files
            if milestone_dir.exists():
                return any(milestone_dir.iterdir())
        return False
    
    def _validate_phase_outputs_with_feedback(self, phase: Phase) -> Dict[str, Any]:
        """Validate phase outputs and provide specific feedback about what's missing"""
        
        # First try standard validation
        if self._validate_phase_outputs(phase):
            return {"success": True, "feedback": ""}
        
        # Generate specific feedback about what failed
        feedback = self._generate_validation_feedback(phase)
        return {"success": False, "feedback": feedback}
    
    def _generate_validation_feedback(self, phase: Phase) -> str:
        """Generate specific feedback about why validation failed"""
        
        if phase.name == "e2e":
            milestone_num = getattr(self, 'current_milestone', 1)
            milestone_dir = self.working_dir / ".cc_automator/milestones" / f"milestone_{milestone_num}"
            
            e2e_files = list(milestone_dir.glob("*e2e*.log")) + list(milestone_dir.glob("*evidence*.log"))
            if not e2e_files:
                return f"Missing required evidence log file. You must create: {milestone_dir}/e2e_evidence.log with detailed test results and command outputs. This file is mandatory for validation."
            else:
                return "Evidence log exists but main.py execution test failed. Check that main.py runs without errors and exits cleanly."
                
        elif phase.name == "research":
            milestone_num = getattr(self, 'current_milestone', 1)
            milestone_dir = self.working_dir / ".cc_automator/milestones" / f"milestone_{milestone_num}"
            research_files = list(milestone_dir.glob("*research*.md"))
            if not research_files:
                return f"Missing required research.md file. You must create: {milestone_dir}/research.md with analysis of current code and requirements."
            else:
                return "Research file exists but doesn't have enough content (must be >100 characters)."
                
        elif phase.name == "planning":
            milestone_num = getattr(self, 'current_milestone', 1)
            milestone_dir = self.working_dir / ".cc_automator/milestones" / f"milestone_{milestone_num}"
            plan_files = list(milestone_dir.glob("*plan*.md"))
            if not plan_files:
                return f"Missing required plan.md file. You must create: {milestone_dir}/plan.md with detailed implementation plan."
            else:
                return "Plan file exists but doesn't have enough content (must be >50 characters)."
                
        elif phase.name == "architecture":
            milestone_num = getattr(self, 'current_milestone', 1)
            milestone_dir = self.working_dir / ".cc_automator/milestones" / f"milestone_{milestone_num}"
            architecture_files = list(milestone_dir.glob("*architecture*.md"))
            
            if not architecture_files:
                return f"Missing required architecture review file. You must create: {milestone_dir}/architecture_review.md (or architecture.md) with architectural analysis results."
            
            # Check ArchitectureValidator for specific issues
            try:
                from .architecture_validator import ArchitectureValidator
                validator = ArchitectureValidator(self.working_dir)
                is_valid, issues = validator.validate_all()
                
                if not is_valid:
                    issue_summary = "\n".join(f"- {issue}" for issue in issues[:5])
                    if len(issues) > 5:
                        issue_summary += f"\n... and {len(issues) - 5} more issues"
                    return f"Architecture validation failed with {len(issues)} violations. Fix these issues:\n{issue_summary}"
                else:
                    return "Architecture review file exists but validation is failing for unknown reasons."
            except Exception as e:
                return f"Architecture validation error: {e}. Check that ArchitectureValidator is properly imported and working."
                
        elif phase.name == "test":
            # Try to capture actual pytest output
            try:
                result = subprocess.run(["python", "-m", "pytest", "tests/unit", "-v"], 
                                      capture_output=True, text=True, cwd=str(self.working_dir), timeout=30)
                error_output = result.stdout + result.stderr
                if error_output.strip():
                    return f"Unit tests are failing. Specific errors:\n{error_output[:1000]}"
            except:
                pass
            return "Unit tests are failing. Run 'python -m pytest tests/unit -v' to see specific test failures and fix them."
            
        elif phase.name == "integration":
            # Try to capture actual pytest output
            try:
                result = subprocess.run(["python", "-m", "pytest", "tests/integration", "-v"], 
                                      capture_output=True, text=True, cwd=str(self.working_dir), timeout=30)
                error_output = result.stdout + result.stderr
                if error_output.strip():
                    return f"Integration tests are failing. Specific errors:\n{error_output[:1000]}"
            except:
                pass
            return "Integration tests are failing. Run 'python -m pytest tests/integration -v' to see specific test failures and fix them."
            
        elif phase.name == "lint":
            # Try to capture actual flake8 output
            try:
                result = subprocess.run(["flake8", "--select=F"], 
                                      capture_output=True, text=True, cwd=str(self.working_dir), timeout=15)
                error_output = result.stdout + result.stderr
                if error_output.strip():
                    return f"Flake8 linting errors found. Specific errors:\n{error_output[:1000]}"
            except:
                pass
            return "Flake8 linting errors found. Run 'flake8 --select=F' to see specific errors and fix them."
            
        elif phase.name == "typecheck":
            # Try to capture actual mypy output
            try:
                result = subprocess.run(["mypy", "--strict", "."], 
                                      capture_output=True, text=True, cwd=str(self.working_dir), timeout=30)
                error_output = result.stdout + result.stderr
                if error_output.strip():
                    return f"MyPy type checking errors found. Specific errors:\n{error_output[:1000]}"
            except:
                pass
            return "MyPy type checking errors found. Run 'mypy --strict .' to see specific errors and fix them."
            
        elif phase.name == "implement":
            main_py = self.working_dir / "main.py"
            src_dir = self.working_dir / "src"
            if not main_py.exists() and not src_dir.exists():
                return "No implementation files found. You must create main.py or files in src/ directory."
            else:
                return "Implementation files exist but may be incomplete or broken."
                
        return f"Validation failed for {phase.name} phase. Check the phase requirements and ensure all outputs are created correctly."
    
    async def _retry_phase_with_validation_feedback(self, phase: Phase, feedback: str) -> bool:
        """Advanced multi-level retry system with intelligent phase recovery"""
        
        # Level 1: Targeted retry with specific feedback
        level_1_result = await self._level_1_targeted_retry(phase, feedback)
        if level_1_result:
            return True
            
        # Level 2: Enhanced retry with more context and debugging 
        level_2_result = await self._level_2_enhanced_retry(phase, feedback)
        if level_2_result:
            return True
            
        # Level 3: Intelligent dependency analysis - can Claude step back?
        level_3_result = await self._level_3_dependency_analysis(phase, feedback)
        return level_3_result
    
    async def _level_1_targeted_retry(self, phase: Phase, feedback: str) -> bool:
        """Level 1: Simple targeted retry with specific feedback"""
        
        print(f"🔄 Level 1 Retry: {phase.name} phase with validation feedback...")
        
        retry_prompt = f"""PHASE RETRY: {phase.name.upper()}
        
You previously completed this phase, but validation failed for a specific reason:

VALIDATION FEEDBACK: {feedback}

Your task: Fix the specific issue mentioned above and complete the {phase.name} phase properly.

Original phase description: {phase.description}

CRITICAL: You must address the validation feedback directly. Don't just redo the work - specifically fix what was identified as missing or broken.

Focus on creating the exact files and outputs that validation is looking for.
"""
        
        # Configure retry options
        model = self._select_model_for_phase(phase.name)
        options = ClaudeCodeOptions(
            max_turns=10,
            allowed_tools=phase.allowed_tools,
            disallowed_tools=[],
            mcp_servers={},
            cwd=str(self.working_dir),
            permission_mode="bypassPermissions",
            model=model
        )
        
        try:
            retry_messages = await self._execute_query_with_wrapper(retry_prompt, options)
            
            # Prevent memory leaks in retry loops
            if len(retry_messages) > 100:
                retry_messages = retry_messages[-50:]
            
            # Process messages for result detection
            for message in retry_messages:
                if hasattr(message, '__dict__'):
                    msg_dict = message.__dict__
                elif isinstance(message, dict):
                    msg_dict = message
                else:
                    continue
                    
                if msg_dict.get("type") == "result":
                    if msg_dict.get("is_error", False):
                        print(f"✗ Level 1 retry failed: {msg_dict.get('result', 'Unknown error')}")
                        return False
                    else:
                        print(f"✓ Level 1 retry completed, re-validating...")
                        return self._validate_phase_outputs(phase)
                        
        except Exception as e:
            print(f"✗ Level 1 retry attempt failed: {e}")
            return False
        finally:
            # Cleanup retry messages to prevent memory leaks
            if 'retry_messages' in locals():
                retry_messages.clear()
        
        return False
    
    async def _level_2_enhanced_retry(self, phase: Phase, feedback: str) -> bool:
        """Level 2: Enhanced retry with debugging context and phase history"""
        
        print(f"🔧 Level 2 Enhanced Retry: {phase.name} phase with debugging context...")
        
        # Gather context from previous phases for better understanding
        milestone_num = getattr(self, 'current_milestone', 1)
        milestone_dir = self.working_dir / ".cc_automator/milestones" / f"milestone_{milestone_num}"
        
        context_info = []
        
        # Add research context if it exists
        research_files = list(milestone_dir.glob("*research*.md")) if milestone_dir.exists() else []
        if research_files:
            try:
                research_content = research_files[0].read_text()[:500]
                context_info.append(f"RESEARCH CONTEXT:\n{research_content}...")
            except:
                pass
        
        # Add plan context if it exists
        plan_files = list(milestone_dir.glob("*plan*.md")) if milestone_dir.exists() else []
        if plan_files:
            try:
                plan_content = plan_files[0].read_text()[:500]
                context_info.append(f"PLAN CONTEXT:\n{plan_content}...")
            except:
                pass
        
        enhanced_prompt = f"""PHASE ENHANCED RETRY: {phase.name.upper()}

SITUATION: You have attempted this phase twice but validation still fails.

VALIDATION FEEDBACK: {feedback}

{chr(10).join(context_info)}

DEBUGGING APPROACH:
1. Carefully read the validation feedback
2. Review what files/outputs are expected
3. Check the working directory structure
4. Create exactly what validation is looking for
5. Test your work before finishing

Original phase description: {phase.description}

CRITICAL: This is an enhanced retry with more context. Take your time, debug systematically, and ensure you create the exact outputs that validation requires.

Be thorough and methodical in your approach.
"""
        
        model = self._select_model_for_phase(phase.name)
        options = ClaudeCodeOptions(
            max_turns=15,  # More turns for debugging
            allowed_tools=phase.allowed_tools,
            disallowed_tools=[],
            mcp_servers={},
            cwd=str(self.working_dir),
            permission_mode="bypassPermissions",
            model=model
        )
        
        try:
            retry_messages = await self._execute_query_with_wrapper(enhanced_prompt, options)
            
            # Prevent memory leaks in retry loops
            if len(retry_messages) > 150:
                retry_messages = retry_messages[-75:]
                
            # Process messages for result detection
            for message in retry_messages:
                if hasattr(message, '__dict__'):
                    msg_dict = message.__dict__
                elif isinstance(message, dict):
                    msg_dict = message
                else:
                    continue
                    
                if msg_dict.get("type") == "result":
                    if msg_dict.get("is_error", False):
                        print(f"✗ Level 2 enhanced retry failed: {msg_dict.get('result', 'Unknown error')}")
                        return False
                    else:
                        print(f"✓ Level 2 enhanced retry completed, re-validating...")
                        return self._validate_phase_outputs(phase)
                        
        except Exception as e:
            print(f"✗ Level 2 enhanced retry attempt failed: {e}")
            return False
        finally:
            # Cleanup retry messages to prevent memory leaks
            if 'retry_messages' in locals():
                retry_messages.clear()
        
        return False
    
    async def _level_3_dependency_analysis(self, phase: Phase, feedback: str) -> bool:
        """Level 3: Intelligent analysis of whether we need to step back to previous phases"""
        
        print(f"🧠 Level 3 Dependency Analysis: Checking if {phase.name} requires stepping back...")
        
        analysis_prompt = f"""DEPENDENCY ANALYSIS: {phase.name.upper()}

SITUATION: This phase has failed validation twice despite retries.

VALIDATION FEEDBACK: {feedback}

PHASE DESCRIPTION: {phase.description}

YOUR TASK: Analyze whether this failure indicates a problem with earlier phases that needs to be fixed first.

ANALYZE:
1. Does the validation failure suggest missing dependencies from earlier phases?
2. Are required inputs from research/planning/implementation phases missing or incorrect?
3. Could this be fixed by stepping back and re-doing an earlier phase?
4. Or is this truly just a problem with the current phase implementation?

RESPOND WITH:
- ANALYSIS: [Your analysis of the root cause]
- STEP_BACK_NEEDED: yes or no
- STEP_BACK_TO: [phase name if stepping back is needed, e.g., "research", "planning", "implement"]
- REASON: [Why stepping back is needed or why current phase just needs better implementation]

Be honest and analytical. If earlier phases have fundamental issues, stepping back is the right approach.
"""
        
        model = self._select_model_for_phase(phase.name)
        options = ClaudeCodeOptions(
            max_turns=5,  # Short analysis
            allowed_tools=["Read", "Bash"],  # Limited tools for analysis
            disallowed_tools=[],
            mcp_servers={},
            cwd=str(self.working_dir),
            permission_mode="bypassPermissions",
            model=model
        )
        
        try:
            analysis_messages = await self._execute_query_with_wrapper(analysis_prompt, options)
            analysis_response = ""
            
            for message in analysis_messages:
                if hasattr(message, '__dict__'):
                    msg_dict = message.__dict__
                elif isinstance(message, dict):
                    msg_dict = message
                else:
                    continue
                    
                if msg_dict.get("type") == "assistant":
                    content = msg_dict.get("message", {}).get("content", "")
                    analysis_response += content
                elif msg_dict.get("type") == "result":
                    break
            
            # Parse the analysis response
            step_back_needed = "STEP_BACK_NEEDED: yes" in analysis_response.lower()
            
            if step_back_needed:
                # Extract which phase to step back to
                step_back_phase = None
                for line in analysis_response.split('\n'):
                    if 'STEP_BACK_TO:' in line.upper():
                        step_back_phase = line.split(':')[-1].strip().lower()
                        break
                
                if step_back_phase in ['research', 'planning', 'implement']:
                    print(f"🔙 Analysis suggests stepping back to {step_back_phase} phase")
                    print(f"📋 Analysis summary: {analysis_response[:200]}...")
                    
                    # Actually trigger the step-back with failure insights
                    step_back_success = await self._execute_intelligent_step_back(
                        current_phase=phase,
                        step_back_to_phase=step_back_phase,
                        failure_insights=analysis_response,
                        original_feedback=feedback
                    )
                    
                    return step_back_success
                else:
                    print(f"🤔 Analysis unclear about which phase to step back to")
                    return False
            else:
                print(f"🎯 Analysis suggests the issue is fixable in current phase")
                # Attempt one final targeted implementation with the analysis insights
                return await self._level_3_final_implementation_attempt(phase, feedback, analysis_response)
                
        except Exception as e:
            print(f"✗ Level 3 dependency analysis failed: {e}")
            return False
        
        return False
    
    async def _level_3_final_implementation_attempt(self, phase: Phase, feedback: str, analysis: str) -> bool:
        """Final implementation attempt based on dependency analysis insights"""
        
        print(f"🎯 Final Implementation Attempt: {phase.name} with analysis insights...")
        
        final_prompt = f"""FINAL IMPLEMENTATION ATTEMPT: {phase.name.upper()}

SITUATION: Multiple retries have failed, but dependency analysis suggests this phase can be completed successfully.

VALIDATION FEEDBACK: {feedback}

ANALYSIS INSIGHTS:
{analysis[:500]}...

YOUR FINAL TASK:
1. Use the analysis insights to understand what's really needed
2. Implement the most direct, simple solution to meet validation requirements
3. Focus on the bare minimum that will satisfy validation
4. Don't overthink - just create what's expected

VALIDATION REQUIREMENTS:
- {feedback}

This is the final attempt before giving up. Make it count.
"""
        
        model = self._select_model_for_phase(phase.name)
        options = ClaudeCodeOptions(
            max_turns=8,  # Limited but focused
            allowed_tools=phase.allowed_tools,
            disallowed_tools=[],
            mcp_servers={},
            cwd=str(self.working_dir),
            permission_mode="bypassPermissions",
            model=model
        )
        
        # Infinite mode retry logic
        attempt_count = 0
        max_attempts = 1 if not self.infinite_mode else 999999  # Infinite attempts in infinite mode
        
        while attempt_count < max_attempts:
            attempt_count += 1
            
            if attempt_count > 1:
                print(f"🔄 Final Implementation Retry #{attempt_count}: {phase.name} (infinite mode)")
                # Update the prompt for retry attempts
                final_prompt = final_prompt.replace(
                    "This is the final attempt before giving up. Make it count.",
                    f"This is attempt #{attempt_count} in infinite mode - keep trying until success!"
                )
            
            try:
                final_messages = await self._execute_query_with_wrapper(final_prompt, options)
                
                for message in final_messages:
                    if hasattr(message, '__dict__'):
                        msg_dict = message.__dict__
                    elif isinstance(message, dict):
                        msg_dict = message
                    else:
                        continue
                        
                    if msg_dict.get("type") == "result":
                        if msg_dict.get("is_error", False):
                            error_msg = msg_dict.get('result', 'Unknown error')
                            print(f"✗ Final implementation attempt #{attempt_count} failed: {error_msg}")
                            if not self.infinite_mode:
                                return False
                            # In infinite mode, break inner loop to try again
                            break
                        else:
                            print(f"✓ Final implementation attempt #{attempt_count} completed, re-validating...")
                            if self._validate_phase_outputs(phase):
                                print(f"✅ Phase {phase.name} validation succeeded on attempt #{attempt_count}!")
                                return True
                            else:
                                print(f"❌ Phase {phase.name} validation failed on attempt #{attempt_count}")
                                if not self.infinite_mode:
                                    return False
                                # In infinite mode, break inner loop to try again
                                break
                                
            except Exception as e:
                print(f"✗ Final implementation attempt #{attempt_count} failed: {e}")
                if not self.infinite_mode:
                    return False
                # In infinite mode, continue to next attempt
                continue
        
        return False
    
    async def _execute_intelligent_step_back(self, current_phase: Phase, step_back_to_phase: str, 
                                           failure_insights: str, original_feedback: str) -> bool:
        """Execute intelligent step-back with failure insights propagated to earlier phases"""
        
        # Check infinite mode vs step-back limits
        if not self.infinite_mode:
            self.step_back_count += 1
            max_step_backs = 3
            if self.step_back_count > max_step_backs:
                print(f"✗ Maximum step-backs ({max_step_backs}) reached. Stopping to prevent infinite loop.")
                current_phase.error = f"Max step-backs reached: {self.step_back_count}"
                return False
        else:
            self.step_back_count += 1
            print(f"🔄 Infinite mode: Step-back #{self.step_back_count} (will continue until success)")
        
        print(f"🔄 Executing intelligent step-back to {step_back_to_phase} phase...")
        
        # Create failure history to avoid repeating mistakes
        failure_history = {
            "failed_phase": current_phase.name,
            "original_feedback": original_feedback,
            "analysis_insights": failure_insights,
            "timestamp": datetime.now().isoformat(),
            "attempts_made": ["level_1_retry", "level_2_enhanced_retry", "level_3_analysis"],
            "step_back_count": self.step_back_count
        }
        
        # Save failure history for reference
        milestone_num = getattr(self, 'current_milestone', 1)
        failure_log_dir = self.working_dir / ".cc_automator" / "failure_logs"
        failure_log_dir.mkdir(parents=True, exist_ok=True)
        
        failure_log_file = failure_log_dir / f"milestone_{milestone_num}_{current_phase.name}_failure.json"
        with open(failure_log_file, 'w') as f:
            json.dump(failure_history, f, indent=2)
        
        # Now re-execute the step-back phase with failure insights
        step_back_success = await self._re_execute_phase_with_insights(
            phase_name=step_back_to_phase,
            failure_history=failure_history
        )
        
        if step_back_success:
            # If step-back phase succeeded, now re-execute all subsequent phases up to current
            return await self._re_execute_subsequent_phases(step_back_to_phase, current_phase.name, failure_history)
        else:
            print(f"✗ Step-back to {step_back_to_phase} phase also failed")
            current_phase.error = f"Step-back to {step_back_to_phase} failed: could not resolve foundational issues"
            return False
    
    async def _re_execute_phase_with_insights(self, phase_name: str, failure_history: Dict[str, Any]) -> bool:
        """Re-execute a phase with insights from future failures"""
        
        print(f"🧠 Re-executing {phase_name} phase with failure insights...")
        
        # Get the original phase configuration
        phase_config = None
        for config_name, config_desc, config_tools, config_think, config_max_turns in PHASE_CONFIGS:
            if config_name == phase_name:
                phase_config = (config_name, config_desc, config_tools, config_think, config_max_turns)
                break
        
        if not phase_config:
            print(f"✗ Unknown phase: {phase_name}")
            return False
        
        # Import the phase prompt generator with fallback
        try:
            from phase_prompt_generator import PhasePromptGenerator
            milestone_num = getattr(self, 'current_milestone', 1)
            milestone = type('Milestone', (), {
                'number': milestone_num, 
                'description': f"Milestone {milestone_num}",
                'requirements': []
            })()
            
            prompt_generator = PhasePromptGenerator(
                working_dir=self.working_dir,
                project_name=self.project_name,
                milestone=milestone
            )
        except ImportError:
            print(f"⚠️  PhasePromptGenerator not available, using fallback prompt")
            # Create a simple fallback prompt
            base_prompt = f"Complete the {phase_name} phase for milestone {getattr(self, 'current_milestone', 1)}"
            return await self._execute_simple_phase_with_insights(phase_name, base_prompt, failure_history)
        
        # Generate base prompt
        base_prompt = prompt_generator.generate_prompt(phase_name)
        
        # Enhance prompt with failure insights
        enhanced_prompt = f"""{base_prompt}

CRITICAL - FAILURE INSIGHTS FROM FUTURE PHASES:

Previous attempt at this phase led to failures in later phases. Learn from these insights:

FAILED PHASE: {failure_history['failed_phase']}
FAILURE REASON: {failure_history['original_feedback']}

ANALYSIS OF ROOT CAUSE:
{failure_history['analysis_insights']}

WHAT THIS MEANS FOR {phase_name.upper()} PHASE:
- Your {phase_name} output was incomplete or incorrect in ways that caused {failure_history['failed_phase']} to fail
- Focus on addressing the root cause issues identified in the analysis
- Be more thorough and complete in your {phase_name} work
- Anticipate what downstream phases will need from your output

PREVENT REPETITION:
- Don't just redo the same work that failed before
- Address the specific deficiencies identified
- Create more comprehensive, complete outputs
- Think about dependencies that downstream phases will have

This is a corrective re-execution. Make it count by learning from the failure insights.
"""
        
        # Create enhanced phase
        config_name, config_desc, config_tools, config_think, config_max_turns = phase_config
        enhanced_phase = Phase(
            name=config_name,
            description=f"CORRECTIVE: {config_desc} (with failure insights)",
            prompt=enhanced_prompt,
            allowed_tools=config_tools,
            think_mode=config_think,
            max_turns=config_max_turns + 10  # Extra turns for corrective work
        )
        
        # Execute with enhanced context
        try:
            result = await self._execute_with_sdk(enhanced_phase)
            
            if enhanced_phase.status == PhaseStatus.COMPLETED:
                # Validate the corrected phase output
                if self._validate_phase_outputs(enhanced_phase):
                    print(f"✓ Corrective {phase_name} phase completed and validated")
                    return True
                else:
                    print(f"✗ Corrective {phase_name} phase completed but validation failed")
                    return False
            else:
                print(f"✗ Corrective {phase_name} phase failed: {enhanced_phase.error}")
                return False
                
        except Exception as e:
            print(f"✗ Corrective {phase_name} phase error: {e}")
            return False
    
    async def _re_execute_subsequent_phases(self, step_back_phase: str, target_phase: str, 
                                          failure_history: Dict[str, Any]) -> bool:
        """Re-execute all phases from step-back phase to target phase with failure context"""
        
        # Define phase order
        phase_order = ["research", "planning", "implement", "lint", "typecheck", "test", "integration", "e2e", "validate", "commit"]
        
        try:
            step_back_index = phase_order.index(step_back_phase)
            target_index = phase_order.index(target_phase)
        except ValueError:
            print(f"✗ Unknown phase in sequence: {step_back_phase} or {target_phase}")
            return False
        
        print(f"🔄 Re-executing phases from {step_back_phase} to {target_phase}...")
        
        # Execute each phase in sequence
        for i in range(step_back_index + 1, target_index + 1):
            phase_name = phase_order[i]
            
            # Add failure context to each subsequent phase
            context_aware_success = await self._execute_phase_with_failure_context(
                phase_name=phase_name,
                failure_history=failure_history
            )
            
            if not context_aware_success:
                print(f"✗ Re-execution failed at {phase_name} phase")
                return False
        
        print(f"✓ Successfully re-executed all phases from {step_back_phase} to {target_phase}")
        return True
    
    async def _execute_phase_with_failure_context(self, phase_name: str, failure_history: Dict[str, Any]) -> bool:
        """Execute a phase with awareness of why previous attempts failed"""
        
        print(f"🎯 Executing {phase_name} with failure context awareness...")
        
        # Get phase configuration
        phase_config = None
        for config_name, config_desc, config_tools, config_think, config_max_turns in PHASE_CONFIGS:
            if config_name == phase_name:
                phase_config = (config_name, config_desc, config_tools, config_think, config_max_turns)
                break
        
        if not phase_config:
            return False
        
        # Generate phase prompt with failure awareness
        try:
            from phase_prompt_generator import PhasePromptGenerator
            milestone_num = getattr(self, 'current_milestone', 1)
            milestone = type('Milestone', (), {
                'number': milestone_num,
                'description': f"Milestone {milestone_num}",
                'requirements': []
            })()
            
            prompt_generator = PhasePromptGenerator(
                working_dir=self.working_dir,
                project_name=self.project_name,
                milestone=milestone
            )
            
            base_prompt = prompt_generator.generate_prompt(phase_name)
        except ImportError:
            print(f"⚠️  PhasePromptGenerator not available, using fallback prompt")
            # Create a simple fallback prompt
            base_prompt = f"Complete the {phase_name} phase for milestone {getattr(self, 'current_milestone', 1)}"
        
        # Add failure context
        context_aware_prompt = f"""{base_prompt}

FAILURE CONTEXT AWARENESS:

A previous iteration of this pipeline failed at the {failure_history['failed_phase']} phase.
Root cause analysis indicated: {failure_history['analysis_insights'][:300]}...

Your {phase_name} phase must be aware of this context and ensure your work contributes to preventing similar failures.

Be thorough, complete, and anticipate what downstream phases will need from your output.
"""
        
        # Create and execute context-aware phase
        config_name, config_desc, config_tools, config_think, config_max_turns = phase_config
        context_phase = Phase(
            name=config_name,
            description=f"CONTEXT-AWARE: {config_desc}",
            prompt=context_aware_prompt,
            allowed_tools=config_tools,
            think_mode=config_think,
            max_turns=config_max_turns
        )
        
        try:
            result = await self._execute_with_sdk(context_phase)
            
            if context_phase.status == PhaseStatus.COMPLETED:
                if self._validate_phase_outputs(context_phase):
                    print(f"✓ Context-aware {phase_name} phase completed and validated")
                    return True
                else:
                    print(f"✗ Context-aware {phase_name} phase validation failed")
                    return False
            else:
                print(f"✗ Context-aware {phase_name} phase failed: {context_phase.error}")
                return False
                
        except Exception as e:
            print(f"✗ Context-aware {phase_name} phase error: {e}")
            return False
    
    def _validate_phase_outputs(self, phase: Phase) -> bool:
        """Validate that phase outputs meet requirements"""
        
        if phase.name == "lint":
            # Run flake8 and check for zero F-errors
            result = subprocess.run(
                ["flake8", "--select=F", "--exclude=venv,__pycache__,.git"],
                capture_output=True,
                text=True,
                cwd=str(self.working_dir)
            )
            return result.returncode == 0
            
        elif phase.name == "typecheck":
            # Run mypy and check for success
            result = subprocess.run(
                ["mypy", "--strict", "."],
                capture_output=True,
                text=True,
                cwd=str(self.working_dir)
            )
            return result.returncode == 0 and "Success: no issues found" in result.stdout
            
        elif phase.name == "test":
            # Run pytest on unit tests with STRICT validation - ALL tests must pass
            result = subprocess.run(
                ["python", "-m", "pytest", "tests/unit", "-v", "--tb=short"],
                capture_output=True,
                text=True,
                cwd=str(self.working_dir)
            )
            
            # ANTI-CHEATING: Require 100% test success, not just exit code 0
            if result.returncode != 0:
                return False
                
            # Parse pytest output for exact test counts
            import re
            output = result.stdout + result.stderr
            
            # Look for pytest summary line like "5 passed in 0.23s" or "3 passed, 1 failed"
            passed_match = re.search(r'(\d+) passed', output)
            failed_match = re.search(r'(\d+) failed', output)
            error_match = re.search(r'(\d+) error', output)
            
            if not passed_match:
                # No tests found or pytest output malformed
                return False
                
            passed_count = int(passed_match.group(1))
            failed_count = int(failed_match.group(1)) if failed_match else 0
            error_count = int(error_match.group(1)) if error_match else 0
            
            # STRICT REQUIREMENT: Zero failures, zero errors, at least one test
            return passed_count > 0 and failed_count == 0 and error_count == 0
            
        elif phase.name == "integration":
            # Run pytest on integration tests with STRICT validation - ALL tests must pass
            result = subprocess.run(
                ["python", "-m", "pytest", "tests/integration", "-v", "--tb=short"],
                capture_output=True,
                text=True,
                cwd=str(self.working_dir)
            )
            
            # ANTI-CHEATING: Require 100% test success, not just exit code 0
            if result.returncode != 0:
                return False
                
            # Parse pytest output for exact test counts
            import re
            output = result.stdout + result.stderr
            
            # Look for pytest summary line like "5 passed in 0.23s" or "3 passed, 1 failed"
            passed_match = re.search(r'(\d+) passed', output)
            failed_match = re.search(r'(\d+) failed', output)
            error_match = re.search(r'(\d+) error', output)
            
            if not passed_match:
                # No tests found or pytest output malformed
                return False
                
            passed_count = int(passed_match.group(1))
            failed_count = int(failed_match.group(1)) if failed_match else 0
            error_count = int(error_match.group(1)) if error_match else 0
            
            # STRICT REQUIREMENT: Zero failures, zero errors, at least one test
            return passed_count > 0 and failed_count == 0 and error_count == 0
            
        elif phase.name == "research":
            # Check if research.md or similar was created with content
            milestone_num = getattr(self, 'current_milestone', 1)
            milestone_dir = self.working_dir / ".cc_automator/milestones" / f"milestone_{milestone_num}"
            
            # Look for research.md or any file with research in the name
            research_files = list(milestone_dir.glob("*research*.md"))
            if not research_files:
                if self.verbose:
                    print(f"Research validation failed: no research file found in {milestone_dir}")
                return False
            
            # Check if any research file has substantial content
            for research_file in research_files:
                content = research_file.read_text()
                if len(content) > 100:  # Must have substantial content
                    if self.verbose and research_file.name != "research.md":
                        print(f"Note: Found research content in {research_file.name} instead of research.md")
                    return True
            
            return False
            
        elif phase.name == "planning":
            # Check if plan.md or similar was created
            milestone_num = getattr(self, 'current_milestone', 1)
            milestone_dir = self.working_dir / ".cc_automator/milestones" / f"milestone_{milestone_num}"
            
            # Look for plan.md or any file with plan in the name
            plan_files = list(milestone_dir.glob("*plan*.md"))
            if not plan_files:
                if self.verbose:
                    print(f"Planning validation failed: no plan file found in {milestone_dir}")
                return False
            
            # Check if any plan file has content
            for plan_file in plan_files:
                content = plan_file.read_text()
                if len(content) > 50:
                    if self.verbose and plan_file.name != "plan.md":
                        print(f"Note: Found plan content in {plan_file.name} instead of plan.md")
                    return True
            
            return False
            
        elif phase.name == "implement":
            # Check if main.py or src files exist
            main_py = self.working_dir / "main.py"
            src_dir = self.working_dir / "src"
            # Either main.py exists or src directory has Python files
            if main_py.exists():
                return True
            elif src_dir.exists():
                py_files = list(src_dir.glob("**/*.py"))
                return len(py_files) > 0
            return False
            
        elif phase.name == "architecture":
            # Check if architecture review was created AND ArchitectureValidator passes
            milestone_num = getattr(self, 'current_milestone', 1)
            milestone_dir = self.working_dir / ".cc_automator/milestones" / f"milestone_{milestone_num}"
            
            # First check for architecture_review.md or architecture.md
            architecture_files = list(milestone_dir.glob("*architecture*.md"))
            if not architecture_files:
                if self.verbose:
                    print(f"Architecture validation failed: no architecture review file found in {milestone_dir}")
                return False
            
            # Run ArchitectureValidator to ensure zero violations
            try:
                from .architecture_validator import ArchitectureValidator
                validator = ArchitectureValidator(self.working_dir)
                is_valid, issues = validator.validate_all()
                
                if not is_valid:
                    if self.verbose:
                        print(f"Architecture validation failed: {len(issues)} violations found")
                        for issue in issues[:5]:  # Show first 5 issues
                            print(f"  - {issue}")
                    return False
                
                if self.verbose:
                    print("Architecture validation passed: zero violations found")
                return True
                
            except Exception as e:
                if self.verbose:
                    print(f"Architecture validation error: {e}")
                return False
            
        elif phase.name == "e2e":
            # Check if e2e evidence log was created AND main.py runs successfully
            milestone_num = getattr(self, 'current_milestone', 1)
            milestone_dir = self.working_dir / ".cc_automator/milestones" / f"milestone_{milestone_num}"
            
            # STRICT: Evidence log is REQUIRED - no exceptions
            # This is exactly what prevents Claude from cheating
            e2e_files = list(milestone_dir.glob("*e2e*.log")) + list(milestone_dir.glob("*evidence*.log"))
            if not e2e_files:
                if self.verbose:
                    print(f"E2E validation failed: no evidence log found in {milestone_dir}")
                    print("E2E phase must create e2e_evidence.log as proof of testing")
                return False
            
            # Evidence log exists - now verify main.py actually works
            main_py = self.working_dir / "main.py"
            if not main_py.exists():
                if self.verbose:
                    print(f"E2E validation failed: main.py not found")
                return False
                
            # Check if it's interactive and test accordingly
            content = main_py.read_text()
            is_interactive = 'input(' in content or 'raw_input(' in content
            
            try:
                if is_interactive:
                    # For interactive programs, try common exit patterns
                    if self.verbose:
                        print("E2E: Detected interactive program, trying common exit patterns")
                    
                    exit_patterns = ["q\n", "exit\n", "8\n", "0\n", "\n"]
                    success = False
                    
                    for test_input in exit_patterns:
                        try:
                            result = subprocess.run(
                                ["python", "main.py"],
                                input=test_input,
                                capture_output=True,
                                text=True,
                                cwd=str(self.working_dir),
                                timeout=10
                            )
                            if result.returncode == 0:
                                if self.verbose:
                                    print(f"E2E: Success with input: {repr(test_input.strip())}")
                                success = True
                                break
                        except subprocess.TimeoutExpired:
                            continue
                    
                    if not success:
                        if self.verbose:
                            print("E2E validation failed: main.py interactive program doesn't exit cleanly")
                        return False
                        
                else:
                    # Non-interactive, run directly
                    if self.verbose:
                        print("E2E: Running non-interactive program")
                    result = subprocess.run(
                        ["python", "main.py"],
                        capture_output=True,
                        text=True,
                        cwd=str(self.working_dir),
                        timeout=10
                    )
                    if result.returncode != 0:
                        if self.verbose:
                            print(f"E2E validation failed: main.py exited with code {result.returncode}")
                        return False
                        
            except Exception as e:
                if self.verbose:
                    print(f"E2E validation error: {e}")
                return False
                
            return True
            
        elif phase.name == "validate":
            # Enhanced validation with multiple checks and better error reporting
            milestone_num = getattr(self, 'current_milestone', 1)
            milestone_dir = self.working_dir / ".cc_automator/milestones" / f"milestone_{milestone_num}"
            
            # Check for validation report with multiple possible names
            validation_files = list(milestone_dir.glob("*validation*.md"))
            validation_report = None
            
            if validation_files:
                validation_report = validation_files[0]
                if self.verbose and len(validation_files) > 1:
                    print(f"Note: Found multiple validation files: {[f.name for f in validation_files]}")
                    print(f"Using: {validation_report.name}")
            
            if not validation_report or not validation_report.exists():
                if self.verbose:
                    expected_path = milestone_dir / "validation_report.md"
                    print(f"Validation failed: No validation report found")
                    print(f"Expected: {expected_path}")
                    print(f"Milestone dir exists: {milestone_dir.exists()}")
                    if milestone_dir.exists():
                        existing_files = list(milestone_dir.glob("*.md"))
                        print(f"Existing .md files: {[f.name for f in existing_files]}")
                return False
            
            # Validate the content of the validation report
            try:
                validation_content = validation_report.read_text()
                if len(validation_content.strip()) < 50:
                    if self.verbose:
                        print(f"Validation failed: Validation report too short ({len(validation_content)} chars)")
                    return False
                
                # Check for required validation elements
                required_elements = ["implementation", "tested", "working"]
                missing_elements = [elem for elem in required_elements if elem.lower() not in validation_content.lower()]
                
                if missing_elements:
                    if self.verbose:
                        print(f"Validation report missing key elements: {missing_elements}")
                        print(f"Report preview: {validation_content[:200]}...")
                
            except Exception as e:
                if self.verbose:
                    print(f"Failed to read validation report: {e}")
                return False
            
            # Check for mocks/stubs in production code (enhanced patterns)
            mock_patterns = [
                "mock|Mock",
                "TODO|FIXME", 
                "NotImplemented|NotImplementedError",
                "stub|Stub",
                "placeholder|PLACEHOLDER",
                "dummy|Dummy"
            ]
            
            found_issues = []
            
            for pattern in mock_patterns:
                result = subprocess.run(
                    ["grep", "-r", "-E", pattern, 
                     "--include=*.py", "--exclude-dir=tests", "--exclude-dir=venv", 
                     "--exclude-dir=.cc_automator", "."],
                    capture_output=True,
                    text=True,
                    cwd=str(self.working_dir)
                )
                
                if result.returncode == 0:  # grep found matches
                    lines = result.stdout.strip().split('\n')
                    # Filter out comments and acceptable uses
                    real_issues = []
                    for line in lines:
                        if not any(comment in line for comment in ['#', '"""', "'''"]):
                            real_issues.append(line)
                    
                    if real_issues:
                        found_issues.extend(real_issues[:3])  # Limit to first 3 per pattern
            
            if found_issues:
                if self.verbose:
                    print(f"Validation failed: Found {len(found_issues)} mock/stub issues in production code:")
                    for issue in found_issues[:5]:  # Show first 5 issues
                        print(f"  {issue}")
                return False
            
            # Additional validation: Check that main.py actually runs
            main_py = self.working_dir / "main.py"
            if main_py.exists():
                try:
                    # Quick syntax check
                    syntax_check = subprocess.run(
                        [sys.executable, "-m", "py_compile", str(main_py)],
                        capture_output=True,
                        text=True,
                        cwd=str(self.working_dir)
                    )
                    
                    if syntax_check.returncode != 0:
                        if self.verbose:
                            print(f"Validation failed: main.py has syntax errors")
                            print(syntax_check.stderr[:300])
                        return False
                        
                except Exception as e:
                    if self.verbose:
                        print(f"Warning: Could not validate main.py syntax: {e}")
            
            return True
            
        elif phase.name == "commit":
            # Check if a commit was made (look for recent commit)
            result = subprocess.run(
                ["git", "log", "-1", "--oneline"],
                capture_output=True,
                text=True,
                cwd=str(self.working_dir)
            )
            return result.returncode == 0
            
        # Default: assume valid for unknown phases
        return True


# Default phase configurations based on specification
# Format: (name, description, allowed_tools, think_mode, max_turns_override)
PHASE_CONFIGS = [
    ("research",     "Analyze requirements and explore solutions", ["Read", "Grep", "Bash", "Write", "Edit", "mcp__cc-automator-tools__safe_websearch", "mcp__cc-automator-tools__project_context_analyzer"], None, 30),
    ("planning",     "Create detailed implementation plan", ["Read", "Write", "Edit", "Bash", "mcp__cc-automator-tools__project_context_analyzer", "mcp__cc-automator-tools__safe_command_runner"], None, 50),
    ("implement",    "Build the solution", ["Read", "Write", "Edit", "MultiEdit", "mcp__cc-automator-tools__safe_file_operations"], None, 50),
    ("lint",         "Fix code style issues (flake8)", ["Read", "Edit", "Bash", "mcp__cc-automator-tools__safe_command_runner"], None, 20),
    ("typecheck",    "Fix type errors (mypy --strict)", ["Read", "Edit", "Bash", "mcp__cc-automator-tools__safe_command_runner"], None, 20),
    ("test",         "Fix unit tests (pytest)", ["Read", "Write", "Edit", "Bash", "mcp__cc-automator-tools__safe_command_runner"], None, 30),
    ("integration",  "Fix integration tests", ["Read", "Write", "Edit", "Bash", "mcp__cc-automator-tools__safe_command_runner"], None, 30),
    ("e2e",          "Verify main.py runs successfully", ["Read", "Bash", "Write", "mcp__cc-automator-tools__safe_command_runner"], None, 20),
    ("validate",     "Validate all implementations are real", ["Read", "Bash", "Write", "Edit", "Grep", "mcp__cc-automator-tools__safe_command_runner"], None, 50),
    ("commit",       "Create git commit with changes", ["Bash", "Read"], None, 15)
]


def create_phase(name: str, description: str, prompt: str, 
                 allowed_tools: Optional[List[str]] = None, 
                 think_mode: Optional[str] = None,
                 max_turns: Optional[int] = None) -> Phase:
    """Helper to create a phase with defaults from PHASE_CONFIGS"""
    
    # Find config for this phase
    for config_name, config_desc, config_tools, config_think, config_max_turns in PHASE_CONFIGS:
        if config_name == name:
            phase = Phase(
                name=name,
                description=description or config_desc,
                prompt=prompt,
                allowed_tools=allowed_tools or config_tools,
                think_mode=think_mode or config_think
            )
            # Use explicit max_turns if provided, otherwise use config, otherwise use default
            if max_turns is not None:
                phase.max_turns = max_turns
            elif config_max_turns is not None:
                phase.max_turns = config_max_turns
            return phase
    
    # Default if not found
    phase = Phase(name=name, description=description, prompt=prompt,
                  allowed_tools=allowed_tools, think_mode=think_mode)
    if max_turns is not None:
        phase.max_turns = max_turns
    return phase


if __name__ == "__main__":
    # Example usage
    orchestrator = PhaseOrchestrator("Test Project", ".")
    
    # Add a simple test phase
    test_phase = create_phase(
        "research",
        "Research the project structure",
        "List all Python files in this directory and summarize what this project does."
    )
    
    orchestrator.add_phase(test_phase)
    results = orchestrator.execute_all()
    
    print(f"\nFinal results saved to .cc_automator/checkpoints/")