#!/usr/bin/env python3
"""
Claude Code SDK wrapper that fixes the cost_usd parsing bug
This monkey-patches the SDK's _parse_message method to handle missing fields gracefully
"""

import claude_code_sdk
from claude_code_sdk._internal.client import InternalClient
from claude_code_sdk.types import ResultMessage

# Store original parse method
_original_parse_message = InternalClient._parse_message

def _patched_parse_message(self, data):
    """Patched version that handles missing cost fields gracefully"""
    try:
        return _original_parse_message(self, data)
    except KeyError as e:
        if "cost_usd" in str(e) and data.get("type") == "result":
            # Fix the result message parsing
            return ResultMessage(
                subtype=data["subtype"],
                cost_usd=data.get("cost_usd", data.get("total_cost_usd", 0.0)),
                duration_ms=data.get("duration_ms", 0),
                duration_api_ms=data.get("duration_api_ms", 0),
                is_error=data.get("is_error", False),
                num_turns=data.get("num_turns", 0),
                session_id=data.get("session_id", ""),
                total_cost_usd=data.get("total_cost_usd", data.get("total_cost", 0.0)),
                usage=data.get("usage"),
                result=data.get("result"),
            )
        else:
            raise

# Apply monkey patch
InternalClient._parse_message = _patched_parse_message

# Re-export everything from the original SDK
from claude_code_sdk import *

print("✅ Claude Code SDK wrapper loaded - cost parsing bug fixed")
