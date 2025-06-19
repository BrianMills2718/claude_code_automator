#!/usr/bin/env python3
"""
Minimal SDK Test for TaskGroup Issues

This test specifically reproduces TaskGroup cleanup race conditions
WITHOUT error masking to see the real failures that are being hidden.

Based on the real ML Portfolio test failure pattern:
- Test stuck in validate phase for 2+ hours
- Error message: "Phase completed successfully (TaskGroup cleanup noise ignored)"
- Orphaned subprocess (PID 157253) still running
- Resource leaks from incomplete async cleanup
"""

import asyncio
import sys
import time
import logging
from pathlib import Path
from typing import AsyncIterator, Dict, Any

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

# Import original SDK WITHOUT our wrapper masking
import claude_code_sdk
from claude_code_sdk import ClaudeCodeOptions

# Configure detailed logging to see real errors
def setup_logging():
    """Set up logging to both console and file."""
    import os
    from datetime import datetime
    
    # Create logs directory
    log_dir = Path(__file__).parent / "logs"
    log_dir.mkdir(exist_ok=True)
    
    # Create timestamped log file
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    log_file = log_dir / f"minimal_sdk_test_{timestamp}.txt"
    
    # Configure logging to both file and console
    logging.basicConfig(
        level=logging.DEBUG,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(log_file),
            logging.StreamHandler()
        ]
    )
    
    logger = logging.getLogger(__name__)
    logger.info(f"📝 Logging to file: {log_file}")
    return logger, log_file

logger, log_file = setup_logging()

class MinimalSDKTester:
    """
    Test SDK directly without any error masking to see real failures.
    """
    
    def __init__(self):
        self.test_results = []
        self.working_dir = Path("/tmp/minimal_sdk_test")
        self.working_dir.mkdir(exist_ok=True)
        
    async def test_basic_operations_no_masking(self):
        """Test basic SDK operations that typically trigger TaskGroup issues."""
        logger.info("🔍 Testing basic SDK operations WITHOUT error masking...")
        
        try:
            options = ClaudeCodeOptions(
                max_turns=3,
                allowed_tools=["Read", "Write"],
                cwd=str(self.working_dir),
                permission_mode="bypassPermissions"
            )
            
            test_prompt = """
            Please create a simple text file called 'test.txt' with the content 'Hello World'.
            Then read it back to verify it was created correctly.
            This is a simple test to see if basic SDK operations trigger TaskGroup issues.
            """
            
            messages = []
            start_time = time.time()
            
            logger.info("🚀 Starting SDK query...")
            async for message in claude_code_sdk.query(prompt=test_prompt, options=options):
                messages.append(message)
                logger.info(f"📨 Message received: {message.__class__.__name__}")
                
                # Log message details for debugging
                if hasattr(message, '__dict__'):
                    logger.debug(f"Message content: {message.__dict__}")
                
            duration = time.time() - start_time
            logger.info(f"✅ Basic operations completed in {duration:.1f}s")
            logger.info(f"📊 Total messages: {len(messages)}")
            
            return True, f"Success: {len(messages)} messages in {duration:.1f}s"
            
        except Exception as e:
            # DO NOT MASK - let's see the real error
            logger.error(f"❌ REAL SDK ERROR (no masking): {type(e).__name__}: {e}")
            logger.error(f"📍 Error details: {str(e)}")
            return False, f"Real error: {type(e).__name__}: {e}"
    
    async def test_websearch_taskgroup_trigger(self):
        """Test WebSearch operations that are known to trigger TaskGroup issues."""
        logger.info("🔍 Testing WebSearch operations that trigger TaskGroup issues...")
        
        try:
            options = ClaudeCodeOptions(
                max_turns=5,
                allowed_tools=["WebSearch"],
                cwd=str(self.working_dir),
                permission_mode="bypassPermissions"
            )
            
            test_prompt = """
            Please search for information about "Python asyncio TaskGroup race conditions"
            and provide a brief summary. This test specifically tries to reproduce
            the TaskGroup cleanup issues seen in the ML Portfolio test.
            """
            
            messages = []
            start_time = time.time()
            taskgroup_errors = []
            
            logger.info("🌐 Starting WebSearch operation...")
            
            async for message in claude_code_sdk.query(prompt=test_prompt, options=options):
                messages.append(message)
                logger.info(f"📨 WebSearch message: {message.__class__.__name__}")
                
                # Check for any error indicators
                if hasattr(message, 'is_error') and message.is_error:
                    logger.warning(f"⚠️ Error message detected: {message}")
                    
            duration = time.time() - start_time
            logger.info(f"🌐 WebSearch completed in {duration:.1f}s")
            logger.info(f"📊 Total messages: {len(messages)}")
            
            return True, f"WebSearch success: {len(messages)} messages in {duration:.1f}s"
            
        except Exception as e:
            # Specifically look for TaskGroup related errors
            error_str = str(e).lower()
            
            if "taskgroup" in error_str:
                logger.error(f"🚨 TASKGROUP ERROR DETECTED: {type(e).__name__}: {e}")
                logger.error(f"🔍 Full error: {str(e)}")
                
                # Check if this is BaseExceptionGroup
                if isinstance(e, BaseExceptionGroup):
                    logger.error(f"📊 BaseExceptionGroup with {len(e.exceptions)} sub-exceptions:")
                    for i, sub_e in enumerate(e.exceptions):
                        logger.error(f"  {i+1}. {type(sub_e).__name__}: {sub_e}")
                        
                return False, f"TaskGroup error: {type(e).__name__}: {e}"
            else:
                logger.error(f"❌ Non-TaskGroup error: {type(e).__name__}: {e}")
                return False, f"Other error: {type(e).__name__}: {e}"
    
    async def test_session_cleanup_race(self):
        """Test session cleanup specifically to trigger race conditions."""
        logger.info("🔍 Testing session cleanup race conditions...")
        
        try:
            # Run multiple quick operations to stress cleanup
            for i in range(3):
                logger.info(f"🔄 Session test {i+1}/3...")
                
                options = ClaudeCodeOptions(
                    max_turns=2,
                    allowed_tools=["Read"],
                    cwd=str(self.working_dir),
                    permission_mode="bypassPermissions"
                )
                
                test_prompt = f"Test {i+1}: Please read the current working directory."
                
                messages = []
                async for message in claude_code_sdk.query(prompt=test_prompt, options=options):
                    messages.append(message)
                
                logger.info(f"✅ Session {i+1} completed: {len(messages)} messages")
                
                # Small delay to allow cleanup
                await asyncio.sleep(0.5)
            
            return True, "Session cleanup test completed without errors"
            
        except Exception as e:
            logger.error(f"❌ Session cleanup error: {type(e).__name__}: {e}")
            return False, f"Session cleanup error: {type(e).__name__}: {e}"
    
    async def run_all_tests(self):
        """Run all minimal SDK tests without error masking."""
        logger.info("=" * 60)
        logger.info("MINIMAL SDK TASKGROUP TEST (NO ERROR MASKING)")
        logger.info("=" * 60)
        logger.info("🎯 Goal: Reproduce real TaskGroup failures without hiding them")
        
        tests = [
            ("Basic Operations", self.test_basic_operations_no_masking),
            ("WebSearch TaskGroup Trigger", self.test_websearch_taskgroup_trigger),
            ("Session Cleanup Race", self.test_session_cleanup_race)
        ]
        
        results = []
        
        for test_name, test_func in tests:
            logger.info(f"\n🧪 Running: {test_name}")
            try:
                success, message = await test_func()
                results.append((test_name, success, message))
                
                status = "✅ PASSED" if success else "❌ FAILED"
                logger.info(f"{test_name}: {status} - {message}")
                
            except Exception as e:
                logger.error(f"{test_name}: ❌ FAILED with exception: {type(e).__name__}: {e}")
                results.append((test_name, False, f"Exception: {e}"))
        
        # Summary
        logger.info("\n" + "=" * 60)
        logger.info("MINIMAL SDK TEST RESULTS")
        logger.info("=" * 60)
        
        passed = sum(1 for _, success, _ in results if success)
        total = len(results)
        
        for test_name, success, message in results:
            status = "✅ PASSED" if success else "❌ FAILED"
            logger.info(f"{test_name}: {status}")
            if not success:
                logger.info(f"  └─ {message}")
        
        logger.info(f"\nOverall: {passed}/{total} tests passed")
        
        if passed == total:
            logger.info("🎉 All tests PASSED - No TaskGroup issues detected")
        else:
            logger.info("🚨 Some tests FAILED - TaskGroup issues confirmed")
            logger.info("🔍 Review the error details above to see real SDK failures")
        
        return passed == total

async def main():
    """Main test entry point."""
    print("🔍 Starting minimal SDK TaskGroup test...")
    print("📋 This test runs SDK operations WITHOUT error masking")
    print("🎯 Goal: See real TaskGroup failures that V3 wrapper hides")
    print()
    
    tester = MinimalSDKTester()
    
    try:
        success = await tester.run_all_tests()
        
        print(f"\n🏁 Test completed. Success: {success}")
        
        if not success:
            print("🚨 TaskGroup issues detected - see logs above for real errors")
            print("💡 Next step: Strip error masking from V3 wrapper")
        else:
            print("✅ No TaskGroup issues in basic tests")
            print("💡 May need more complex scenarios to trigger the race conditions")
            
        sys.exit(0 if success else 1)
        
    except KeyboardInterrupt:
        print("\n🛑 Test interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n💥 Test suite failed: {type(e).__name__}: {e}")
        logger.exception("Test suite failure details:")
        sys.exit(1)

if __name__ == "__main__":
    # Run the async test
    asyncio.run(main())