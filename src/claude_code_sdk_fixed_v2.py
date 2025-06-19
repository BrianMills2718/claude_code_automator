#!/usr/bin/env python3
"""
Claude Code SDK wrapper v2 - Improved future-proof version
Handles both current broken SDK and future fixed SDK
"""

import claude_code_sdk
from claude_code_sdk._internal.client import InternalClient
from claude_code_sdk.types import ResultMessage

# Store original parse method
_original_parse_message = InternalClient._parse_message

def _patched_parse_message(self, data):
    """Patched version that handles all cases gracefully"""
    
    # Special handling for result messages
    if data.get("type") == "result":
        # Build ResultMessage with safe field access
        return ResultMessage(
            subtype=data.get("subtype", ""),
            # Handle various cost field names safely
            cost_usd=data.get("cost_usd", data.get("total_cost_usd", 0.0)),
            duration_ms=data.get("duration_ms", 0),
            duration_api_ms=data.get("duration_api_ms", 0),
            is_error=data.get("is_error", False),
            num_turns=data.get("num_turns", 0),
            session_id=data.get("session_id", ""),
            # Handle both total_cost_usd and total_cost
            total_cost_usd=data.get("total_cost_usd", data.get("total_cost", 0.0)),
            usage=data.get("usage"),
            result=data.get("result"),
        )
    
    # For non-result messages, use original parser
    try:
        return _original_parse_message(self, data)
    except KeyError as e:
        # If original parser fails, handle gracefully
        if "cost" in str(e):
            # Try our safe parser for any cost-related errors
            return _patched_parse_message(self, data)
        else:
            raise

# Apply monkey patch
InternalClient._parse_message = _patched_parse_message

# Re-export everything from the original SDK
from claude_code_sdk import *

print("✅ Claude Code SDK wrapper v2 loaded - future-proof implementation")