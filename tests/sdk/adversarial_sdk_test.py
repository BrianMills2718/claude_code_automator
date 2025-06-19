#!/usr/bin/env python3
"""
Adversarial test to verify if the SDK cost_usd bug actually exists
Tests both with and without the wrapper to prove the issue
"""

import asyncio
import traceback
import sys
from pathlib import Path

async def test_original_sdk():
    """Test the original SDK without our wrapper"""
    print("\n" + "=" * 80)
    print("TEST 1: Original SDK (should fail with KeyError)")
    print("=" * 80)
    
    # Force import of original SDK
    if 'claude_code_sdk_fixed' in sys.modules:
        del sys.modules['claude_code_sdk_fixed']
    if 'claude_code_sdk' in sys.modules:
        del sys.modules['claude_code_sdk']
    
    from claude_code_sdk import query, ClaudeCodeOptions
    
    options = ClaudeCodeOptions(
        max_turns=2,
        allowed_tools=["Write"],
        permission_mode="bypassPermissions",
        cwd=str(Path.cwd())
    )
    
    try:
        message_count = 0
        async for message in query(prompt="Write 'test' to test1.txt", options=options):
            message_count += 1
            print(f"Message {message_count}: {type(message).__name__}")
        print(f"✅ Original SDK worked! (Total messages: {message_count})")
        return True
    except KeyError as e:
        print(f"❌ KeyError as expected: {e}")
        print(f"   Full traceback:")
        traceback.print_exc()
        return False
    except Exception as e:
        print(f"❌ Different error: {type(e).__name__}: {e}")
        traceback.print_exc()
        return False

async def test_wrapped_sdk():
    """Test with our wrapper"""
    print("\n" + "=" * 80)
    print("TEST 2: Wrapped SDK (should work)")
    print("=" * 80)
    
    # Force reload with wrapper
    if 'claude_code_sdk' in sys.modules:
        del sys.modules['claude_code_sdk']
    if 'claude_code_sdk_fixed' in sys.modules:
        del sys.modules['claude_code_sdk_fixed']
    
    from claude_code_sdk_fixed import query, ClaudeCodeOptions
    
    options = ClaudeCodeOptions(
        max_turns=2,
        allowed_tools=["Write"],
        permission_mode="bypassPermissions",
        cwd=str(Path.cwd())
    )
    
    try:
        message_count = 0
        async for message in query(prompt="Write 'test' to test2.txt", options=options):
            message_count += 1
            print(f"Message {message_count}: {type(message).__name__}")
        print(f"✅ Wrapped SDK worked! (Total messages: {message_count})")
        return True
    except Exception as e:
        print(f"❌ Wrapped SDK failed: {type(e).__name__}: {e}")
        traceback.print_exc()
        return False

async def main():
    """Run adversarial tests"""
    print("ADVERSARIAL SDK TESTING")
    print("Testing claim: SDK has KeyError bug on cost_usd field")
    
    # Test 1: Original SDK
    original_failed = not await test_original_sdk()
    
    # Test 2: Wrapped SDK
    wrapped_worked = await test_wrapped_sdk()
    
    # Summary
    print("\n" + "=" * 80)
    print("ADVERSARIAL TEST SUMMARY")
    print("=" * 80)
    
    if original_failed and wrapped_worked:
        print("✅ CLAIM VERIFIED: Original SDK has KeyError bug, wrapper fixes it")
    elif not original_failed:
        print("❌ CLAIM FALSE: Original SDK works fine, no bug exists")
    else:
        print("⚠️  INCONCLUSIVE: Both versions had issues")
    
    print(f"\nOriginal SDK failed: {original_failed}")
    print(f"Wrapped SDK worked: {wrapped_worked}")

if __name__ == "__main__":
    asyncio.run(main())