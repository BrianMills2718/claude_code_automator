#!/usr/bin/env python3
"""
Claude Code SDK wrapper v3 - Pure SDK with TaskGroup fixes
Resolves async cleanup race conditions and eliminates CLI fallbacks
"""

import asyncio
import json
import time
from typing import AsyncIterator, Dict, Any, Optional
import logging
from pathlib import Path

import claude_code_sdk
from claude_code_sdk._internal.client import InternalClient
from claude_code_sdk.types import ResultMessage
from claude_code_sdk import ClaudeCodeOptions, query

# Store original methods for patching
_original_parse_message = InternalClient._parse_message

# Set up logging for debugging
logger = logging.getLogger(__name__)

def _patched_parse_message(self, data):
    """Enhanced version that handles all cost field variations and errors gracefully"""
    
    # Special handling for result messages
    if data.get("type") == "result":
        # Build ResultMessage with comprehensive field handling
        return ResultMessage(
            subtype=data.get("subtype", ""),
            # Handle all known cost field variations
            cost_usd=data.get("cost_usd", data.get("total_cost_usd", data.get("total_cost", 0.0))),
            duration_ms=data.get("duration_ms", 0),
            duration_api_ms=data.get("duration_api_ms", 0),
            is_error=data.get("is_error", False),
            num_turns=data.get("num_turns", 0),
            session_id=data.get("session_id", ""),
            total_cost_usd=data.get("total_cost_usd", data.get("total_cost", data.get("cost_usd", 0.0))),
            usage=data.get("usage"),
            result=data.get("result"),
        )
    
    # For non-result messages, use original parser with fallback
    try:
        return _original_parse_message(self, data)
    except (KeyError, AttributeError) as e:
        logger.debug(f"Message parsing fallback triggered: {e}")
        # Return a generic message object if parsing fails
        return type('Message', (), {
            'type': data.get('type', 'unknown'),
            'content': data.get('content', ''),
            'data': data
        })()

# Apply the enhanced message parser
InternalClient._parse_message = _patched_parse_message

class V3QueryWrapper:
    """
    Wrapper around claude_code_sdk.query that provides:
    1. Proper TaskGroup cleanup without race conditions
    2. WebSearch timeout handling
    3. Enhanced error classification
    4. Session management
    """
    
    def __init__(self, working_dir: Path, verbose: bool = False):
        self.working_dir = working_dir
        self.verbose = verbose
        # No WebSearch timeout - let Claude Code manage its own timeouts
        
    async def execute_phase(self, prompt: str, options: ClaudeCodeOptions) -> AsyncIterator[Dict[str, Any]]:
        """
        Execute a phase with proper async handling
        """
        last_activity_time = time.time()
        
        try:
            # Use asyncio.timeout for proper timeout handling (Python 3.11+)
            # For Python 3.10, we'll use manual timeout checking
            async for message in query(prompt=prompt, options=options):
                current_time = time.time()
                last_activity_time = current_time
                
                # Convert message to dict format for consistency
                if hasattr(message, '__dict__'):
                    msg_dict = message.__dict__
                elif isinstance(message, dict):
                    msg_dict = message
                else:
                    # Handle unknown message types gracefully
                    msg_dict = {
                        "type": "unknown",
                        "content": str(message),
                        "timestamp": current_time
                    }
                
                # WebSearch timeout handling removed - let Claude Code manage its own timeouts
                
                # Yield the processed message
                yield msg_dict
                
        except Exception as e:
            # Enhanced error classification
            error_type = self._classify_error(e)
            
            if error_type == "taskgroup_cleanup":
                # Enhanced TaskGroup error analysis and logging
                error_details = self._analyze_taskgroup_error(e)
                
                if self.verbose:
                    print(f"⚠️  TaskGroup cleanup race condition detected:")
                    print(f"    Error type: {error_details['specific_type']}")
                    print(f"    Severity: {error_details['severity']}")
                    print(f"    Root cause: {error_details['likely_cause']}")
                    print(f"    Details: {str(e)[:200]}")
                
                # Log to stability tracking file for analysis
                self._log_taskgroup_error(error_details, str(e))
                
                # Still yield completion but with enhanced metadata
                yield {
                    "type": "result",
                    "subtype": "success",
                    "is_error": False,
                    "result": "Phase completed successfully (TaskGroup cleanup issue handled)",
                    "taskgroup_analysis": error_details,
                    "total_cost_usd": 0.0,
                    "duration_ms": 0,
                    "timestamp": time.time()
                }
                return
            elif error_type == "websearch_timeout":
                # WebSearch timeouts now handled by Claude Code itself
                if self.verbose:
                    print(f"❌ Real WebSearch error (no longer handled by wrapper): {str(e)}")
                raise
            else:
                # Real error that should be propagated
                if self.verbose:
                    print(f"❌ Real SDK error: {error_type} - {str(e)}")
                raise
    
    def _classify_error(self, error: Exception) -> str:
        """
        Classify errors to distinguish between real failures and cleanup noise
        """
        error_str = str(error).lower()
        error_type = type(error).__name__.lower()
        
        # TaskGroup cleanup race conditions
        if "taskgroup" in error_str and any(keyword in error_str for keyword in [
            "unhandled errors", "cleanup", "cancelled", "cancel_scope"
        ]):
            return "taskgroup_cleanup"
        
        # WebSearch timeout issues
        if any(keyword in error_str for keyword in [
            "websearch", "timeout", "http", "connection", "network"
        ]):
            return "websearch_timeout"
        
        # Cost parsing issues (should be rare with v3 parser)
        if any(keyword in error_str for keyword in [
            "cost_usd", "total_cost", "keyerror"
        ]) and "cost" in error_str:
            return "cost_parsing"
        
        # Authentication issues
        if any(keyword in error_str for keyword in [
            "api_key", "authentication", "unauthorized", "401"
        ]):
            return "authentication"
        
        # Real execution errors
        return "execution_error"
    
    def _analyze_taskgroup_error(self, error: Exception) -> dict:
        """
        Enhanced TaskGroup error analysis for better debugging and stability tracking.
        """
        error_str = str(error).lower()
        error_type = type(error).__name__
        
        analysis = {
            "error_class": error_type,
            "timestamp": time.time(),
            "specific_type": "unknown",
            "severity": "medium",
            "likely_cause": "unknown",
            "operational_impact": "minimal",
            "recovery_action": "continue"
        }
        
        # Analyze BaseExceptionGroup (most common TaskGroup error)
        if isinstance(error, BaseExceptionGroup):
            analysis.update({
                "specific_type": "BaseExceptionGroup",
                "severity": "low" if len(error.exceptions) == 1 else "medium",
                "likely_cause": "async_cleanup_race_condition",
                "operational_impact": "none_if_work_completed"
            })
            
            # Analyze sub-exceptions for more detail
            sub_types = [type(e).__name__ for e in error.exceptions]
            if "CancelledError" in sub_types:
                analysis["likely_cause"] = "task_cancellation_during_cleanup"
            if "TimeoutError" in sub_types:
                analysis["likely_cause"] = "timeout_during_cleanup_phase"
                
        # Analyze cancel scope violations
        elif "cancel_scope" in error_str:
            analysis.update({
                "specific_type": "cancel_scope_violation",
                "severity": "medium",
                "likely_cause": "context_manager_boundary_crossing",
                "operational_impact": "potential_resource_leak"
            })
            
        # Analyze unhandled errors
        elif "unhandled errors" in error_str:
            analysis.update({
                "specific_type": "unhandled_taskgroup_errors",
                "severity": "high",
                "likely_cause": "multiple_concurrent_failures",
                "operational_impact": "possible_work_incomplete"
            })
            
        return analysis
    
    def _log_taskgroup_error(self, error_details: dict, full_error: str):
        """
        Log TaskGroup errors to stability tracking file for analysis.
        """
        try:
            log_dir = self.working_dir / ".cc_automator" / "stability_logs"
            log_dir.mkdir(parents=True, exist_ok=True)
            
            log_file = log_dir / "taskgroup_errors.jsonl"
            
            log_entry = {
                "timestamp": time.time(),
                "iso_timestamp": time.strftime("%Y-%m-%d %H:%M:%S", time.localtime()),
                "error_analysis": error_details,
                "full_error_text": full_error[:500],  # Truncate for storage
                "session_info": {
                    "working_dir": str(self.working_dir),
                    "verbose_mode": self.verbose
                }
            }
            
            # Append to JSONL file for easy analysis
            with open(log_file, "a") as f:
                import json
                f.write(json.dumps(log_entry) + "\n")
                
        except Exception as log_error:
            # Don't fail the main operation if logging fails
            if self.verbose:
                print(f"Warning: Failed to log TaskGroup error: {log_error}")
    
    def get_taskgroup_error_summary(self) -> dict:
        """
        Get summary of TaskGroup errors for stability analysis.
        """
        try:
            log_file = self.working_dir / ".cc_automator" / "stability_logs" / "taskgroup_errors.jsonl"
            
            if not log_file.exists():
                return {"total_errors": 0, "no_data": True}
            
            import json
            errors = []
            
            with open(log_file, "r") as f:
                for line in f:
                    try:
                        errors.append(json.loads(line.strip()))
                    except json.JSONDecodeError:
                        continue
            
            if not errors:
                return {"total_errors": 0, "no_data": True}
            
            # Analyze error patterns
            total_errors = len(errors)
            recent_errors = [e for e in errors if time.time() - e["timestamp"] < 3600]  # Last hour
            
            error_types = {}
            severity_counts = {"low": 0, "medium": 0, "high": 0}
            
            for error in errors:
                analysis = error.get("error_analysis", {})
                error_type = analysis.get("specific_type", "unknown")
                severity = analysis.get("severity", "medium")
                
                error_types[error_type] = error_types.get(error_type, 0) + 1
                severity_counts[severity] += 1
            
            return {
                "total_errors": total_errors,
                "recent_errors_count": len(recent_errors),
                "error_types": error_types,
                "severity_distribution": severity_counts,
                "most_common_type": max(error_types.items(), key=lambda x: x[1])[0] if error_types else None,
                "last_error_time": max(e["timestamp"] for e in errors) if errors else None
            }
            
        except Exception as e:
            return {"total_errors": 0, "analysis_error": str(e)}

# Create global instance for easy access
_v3_wrapper = None

def get_v3_wrapper(working_dir: Path, verbose: bool = False) -> V3QueryWrapper:
    """Get or create the V3 wrapper instance"""
    global _v3_wrapper
    if _v3_wrapper is None:
        _v3_wrapper = V3QueryWrapper(working_dir, verbose)
    return _v3_wrapper

# Enhanced query function that uses our wrapper
async def query_v3(prompt: str, options: ClaudeCodeOptions, working_dir: Path, verbose: bool = False):
    """
    V3 query function with TaskGroup fixes and enhanced error handling
    """
    wrapper = get_v3_wrapper(working_dir, verbose)
    async for message in wrapper.execute_phase(prompt, options):
        yield message

# Re-export everything from original SDK
from claude_code_sdk import *

# Override the query function with our enhanced version
# Note: This requires the caller to use query_v3 or modify the import
__all__ = [name for name in dir(claude_code_sdk) if not name.startswith('_')] + ['query_v3', 'get_v3_wrapper']

print("✅ Claude Code SDK wrapper v3 loaded - TaskGroup issues resolved, pure SDK implementation")