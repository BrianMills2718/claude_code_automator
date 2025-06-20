#!/usr/bin/env python3
"""
Test SDK stability with consecutive operations
This proves the SDK can execute multiple operations without failure.
"""

import asyncio
import sys
from pathlib import Path

# Add the project root to path
sys.path.append(str(Path(__file__).parent.parent.parent))

from src.claude_code_sdk_stable import stable_query, get_sdk_stats, ClaudeCodeOptions

async def test_consecutive_operations(num_operations: int = 10):
    """Test multiple consecutive SDK operations"""
    print(f"Testing {num_operations} consecutive SDK operations...")
    
    successes = 0
    failures = 0
    
    for i in range(num_operations):
        try:
            print(f"Operation {i+1}/{num_operations}: Testing SDK query...")
            
            # Create a simple query
            test_prompt = f"Test operation {i+1}: Please respond with 'Operation {i+1} successful'"
            
            # Use the stable SDK wrapper
            messages = []
            async for message in stable_query(test_prompt):
                messages.append(message)
                if message.get("type") == "assistant":
                    print(f"  ✅ Operation {i+1} completed")
                    break
            
            if messages:
                successes += 1
            else:
                failures += 1
                print(f"  ❌ Operation {i+1} failed: No messages received")
                
        except Exception as e:
            failures += 1
            print(f"  ❌ Operation {i+1} failed: {str(e)}")
    
    # Get final stats
    stats = get_sdk_stats()
    
    print(f"\n{'='*60}")
    print("CONSECUTIVE OPERATIONS TEST RESULTS")
    print(f"{'='*60}")
    print(f"Total Operations: {num_operations}")
    print(f"Successes: {successes}")
    print(f"Failures: {failures}")
    print(f"Success Rate: {(successes/num_operations)*100:.1f}%")
    print(f"\nSDK Statistics:")
    print(f"  Total SDK Operations: {stats['total_operations']}")
    print(f"  SDK Success Rate: {stats['success_rate']*100:.1f}%")
    print(f"  Active Sessions: {stats['active_sessions']}")
    print(f"  Error Breakdown: {stats['error_breakdown']}")
    
    # Determine overall success
    if failures == 0:
        print(f"\n🎉 ALL {num_operations} CONSECUTIVE OPERATIONS SUCCESSFUL")
        print("✅ SDK IS PROVEN STABLE")
        return True
    else:
        print(f"\n❌ {failures}/{num_operations} OPERATIONS FAILED")
        print("❌ SDK STABILITY NOT PROVEN")
        return False

if __name__ == "__main__":
    # Test with 10 consecutive operations
    success = asyncio.run(test_consecutive_operations(10))
    sys.exit(0 if success else 1)