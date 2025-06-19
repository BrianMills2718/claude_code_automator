#!/usr/bin/env python3
"""
Claude Code SDK wrapper WITHOUT error masking

This version removes all error masking from the V3 wrapper to expose
the real TaskGroup failures that are being hidden. Based on analysis
of the ML Portfolio test getting stuck with fabricated success messages.

KEY CHANGE: Instead of catching TaskGroup errors and fabricating success,
we let them bubble up to see what's really failing.
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

class NoMaskingQueryWrapper:
    """
    SDK wrapper that DOES NOT mask TaskGroup errors.
    
    This is the opposite of the V3 wrapper - instead of hiding TaskGroup
    errors behind fabricated success messages, we let them bubble up
    to see what's really failing.
    """
    
    def __init__(self, working_dir: Path, verbose: bool = False):
        self.working_dir = working_dir
        self.verbose = verbose
        self.error_log = []
        
    async def execute_phase_no_masking(self, prompt: str, options: ClaudeCodeOptions) -> AsyncIterator[Dict[str, Any]]:
        """
        Execute a phase with NO error masking - let real failures surface.
        """
        last_activity_time = time.time()
        
        if self.verbose:
            print("🔍 Starting SDK query WITHOUT error masking...")
        
        try:
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
                
                # Log all messages when verbose
                if self.verbose:
                    print(f"📨 Message: {msg_dict.get('type', 'unknown')}")
                
                # Yield the processed message
                yield msg_dict
                
        except Exception as e:
            # *** KEY CHANGE: NO ERROR MASKING ***
            # Instead of catching and masking TaskGroup errors, we:
            # 1. Log the real error for analysis
            # 2. Re-raise it to see what actually fails
            
            error_details = {
                "timestamp": time.time(),
                "error_type": type(e).__name__,
                "error_message": str(e),
                "is_taskgroup_related": self._is_taskgroup_error(e),
                "is_base_exception_group": isinstance(e, BaseExceptionGroup)
            }
            
            self.error_log.append(error_details)
            
            if self.verbose:
                print(f"🚨 REAL SDK ERROR (NO MASKING): {type(e).__name__}")
                print(f"📋 Error message: {str(e)}")
                print(f"🔍 TaskGroup related: {error_details['is_taskgroup_related']}")
                
                if isinstance(e, BaseExceptionGroup):
                    print(f"📊 BaseExceptionGroup with {len(e.exceptions)} sub-exceptions:")
                    for i, sub_e in enumerate(e.exceptions):
                        print(f"  {i+1}. {type(sub_e).__name__}: {sub_e}")
            
            # *** CRITICAL: DO NOT MASK - RE-RAISE THE REAL ERROR ***
            raise e
    
    def _is_taskgroup_error(self, error: Exception) -> bool:
        """Check if error is TaskGroup related."""
        error_str = str(error).lower()
        error_type = type(error).__name__.lower()
        
        # Check for TaskGroup indicators
        taskgroup_indicators = [
            "taskgroup", "baseexceptiongroup", "cancel_scope", 
            "unhandled errors", "cleanup", "cancelled"
        ]
        
        return any(indicator in error_str or indicator in error_type 
                  for indicator in taskgroup_indicators)
    
    def get_error_summary(self) -> Dict[str, Any]:
        """Get summary of all errors encountered (for analysis)."""
        if not self.error_log:
            return {"total_errors": 0, "no_errors": True}
        
        taskgroup_errors = [e for e in self.error_log if e["is_taskgroup_related"]]
        base_exception_groups = [e for e in self.error_log if e["is_base_exception_group"]]
        
        return {
            "total_errors": len(self.error_log),
            "taskgroup_errors": len(taskgroup_errors),
            "base_exception_groups": len(base_exception_groups),
            "error_types": [e["error_type"] for e in self.error_log],
            "latest_error": self.error_log[-1] if self.error_log else None,
            "all_errors": self.error_log
        }

# Create global instance for easy access
_no_masking_wrapper = None

def get_no_masking_wrapper(working_dir: Path, verbose: bool = False) -> NoMaskingQueryWrapper:
    """Get or create the no-masking wrapper instance"""
    global _no_masking_wrapper
    if _no_masking_wrapper is None:
        _no_masking_wrapper = NoMaskingQueryWrapper(working_dir, verbose)
    return _no_masking_wrapper

# Enhanced query function that does NOT mask errors
async def query_no_masking(prompt: str, options: ClaudeCodeOptions, working_dir: Path, verbose: bool = False):
    """
    Query function that exposes real TaskGroup failures instead of masking them
    """
    wrapper = get_no_masking_wrapper(working_dir, verbose)
    async for message in wrapper.execute_phase_no_masking(prompt, options):
        yield message

# Re-export everything from original SDK
from claude_code_sdk import *

# Note: Callers should use query_no_masking instead of the standard query
__all__ = [name for name in dir(claude_code_sdk) if not name.startswith('_')] + ['query_no_masking', 'get_no_masking_wrapper']

if __name__ == "__main__":
    print("✅ Claude Code SDK wrapper (NO ERROR MASKING) loaded")
    print("🔍 This version exposes real TaskGroup failures instead of hiding them")
    print("🎯 Use query_no_masking() to see actual SDK failures")