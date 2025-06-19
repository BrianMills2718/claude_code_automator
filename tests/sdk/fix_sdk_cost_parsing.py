#!/usr/bin/env python3
"""
Fix the Claude Code SDK cost parsing bug
Creates a patched version of the SDK client that handles the correct field names
"""

import os
import shutil
from pathlib import Path

def patch_sdk():
    """Patch the SDK to fix the cost_usd parsing error"""
    
    # Find the SDK installation
    sdk_path = Path("/home/brian/miniconda3/lib/python3.10/site-packages/claude_code_sdk")
    client_file = sdk_path / "_internal" / "client.py"
    
    if not client_file.exists():
        print(f"❌ SDK client file not found at: {client_file}")
        return False
    
    # Backup original
    backup_file = client_file.with_suffix('.py.bak')
    if not backup_file.exists():
        shutil.copy(client_file, backup_file)
        print(f"✅ Created backup: {backup_file}")
    
    # Read the current content
    with open(client_file, 'r') as f:
        content = f.read()
    
    # Apply the fix - replace the incorrect field access
    original_lines = [
        '                    cost_usd=data["cost_usd"],',
        '                    total_cost_usd=data["total_cost"],'
    ]
    
    fixed_lines = [
        '                    cost_usd=data.get("cost_usd", data.get("total_cost_usd", 0.0)),',
        '                    total_cost_usd=data.get("total_cost_usd", data.get("total_cost", 0.0)),'
    ]
    
    # Apply fixes
    patched_content = content
    for original, fixed in zip(original_lines, fixed_lines):
        if original in patched_content:
            patched_content = patched_content.replace(original, fixed)
            print(f"✅ Fixed: {original.strip()} -> {fixed.strip()}")
        else:
            print(f"⚠️  Could not find line to patch: {original.strip()}")
    
    # Write the patched content
    with open(client_file, 'w') as f:
        f.write(patched_content)
    
    print(f"\n✅ SDK patched successfully!")
    print(f"📝 Original backed up to: {backup_file}")
    
    return True

def create_sdk_wrapper():
    """Create a wrapper that monkey-patches the SDK at runtime"""
    
    wrapper_content = '''#!/usr/bin/env python3
"""
Claude Code SDK wrapper that fixes the cost_usd parsing bug
This monkey-patches the SDK's _parse_message method to handle missing fields gracefully
"""

import claude_code_sdk
from claude_code_sdk._internal.client import AsyncClaudeCodeClient
from claude_code_sdk.types import ResultMessage

# Store original parse method
_original_parse_message = AsyncClaudeCodeClient._parse_message

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
AsyncClaudeCodeClient._parse_message = _patched_parse_message

# Re-export everything from the original SDK
from claude_code_sdk import *

print("✅ Claude Code SDK wrapper loaded - cost parsing bug fixed")
'''
    
    wrapper_file = Path("/home/brian/cc_automator4/claude_code_sdk_fixed.py")
    with open(wrapper_file, 'w') as f:
        f.write(wrapper_content)
    
    print(f"\n✅ Created SDK wrapper: {wrapper_file}")
    print("To use the fixed SDK, import from claude_code_sdk_fixed instead of claude_code_sdk")
    
    return wrapper_file

if __name__ == "__main__":
    print("=" * 80)
    print("Claude Code SDK Cost Parsing Fix")
    print("=" * 80)
    print()
    
    # Create runtime wrapper (safer than patching installed files)
    wrapper_file = create_sdk_wrapper()
    
    print("\n" + "=" * 80)
    print("SOLUTION OPTIONS:")
    print("=" * 80)
    print()
    print("1. Use the wrapper (recommended):")
    print(f"   Replace: from claude_code_sdk import ...")
    print(f"   With:    from claude_code_sdk_fixed import ...")
    print()
    print("2. Apply the patch directly (risky):")
    print("   Run: python fix_sdk_cost_parsing.py --apply-patch")
    print()
    print("3. Set environment variable to disable SDK:")
    print("   export USE_CLAUDE_SDK=false")
    
    # Check if user wants to apply the patch
    import sys
    if "--apply-patch" in sys.argv:
        print("\n⚠️  Applying patch directly to SDK installation...")
        if patch_sdk():
            print("✅ Patch applied successfully!")
        else:
            print("❌ Failed to apply patch")