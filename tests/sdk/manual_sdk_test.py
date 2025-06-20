#!/usr/bin/env python3
"""
Manual SDK Test - No pytest dependencies

This directly tests the stable SDK wrapper to prove it works.
This is the test that MUST pass for the SDK to be considered stable.
"""

import asyncio
import sys
from pathlib import Path

# Add the project root to path
sys.path.append(str(Path(__file__).parent.parent.parent))

from src.claude_code_sdk_stable import (
    StableSDKWrapper, 
    SDKErrorType
)

def test_wrapper_initialization():
    """Test that wrapper initializes correctly"""
    print("Testing wrapper initialization...")
    wrapper = StableSDKWrapper()
    assert wrapper is not None
    assert hasattr(wrapper, 'operations')
    assert hasattr(wrapper, 'active_sessions')
    assert wrapper.log_file.exists()
    print("✅ Wrapper initialization test passed")

def test_error_classification():
    """Test that errors are classified correctly"""
    print("Testing error classification...")
    wrapper = StableSDKWrapper()
    
    # TaskGroup error
    taskgroup_error = Exception("TaskGroup unhandled errors")
    assert wrapper._classify_error(taskgroup_error) == SDKErrorType.TASKGROUP_ERROR
    
    # JSON decode error  
    json_error = Exception("Failed to decode JSON")
    assert wrapper._classify_error(json_error) == SDKErrorType.JSON_DECODE_ERROR
    
    # Cost parsing error
    cost_error = KeyError("cost_usd")
    assert wrapper._classify_error(cost_error) == SDKErrorType.COST_PARSING_ERROR
    
    print("✅ Error classification test passed")

def test_json_repair():
    """Test JSON repair functionality"""
    print("Testing JSON repair...")
    wrapper = StableSDKWrapper()
    
    # Test truncated JSON
    truncated = '{"type":"assistant","message":{"role":"assistan...'
    repaired = wrapper._repair_truncated_json(truncated)
    assert isinstance(repaired, dict)
    assert "role" in repaired
    print("✅ JSON repair test passed")

def test_cost_parsing_robustness():
    """Test that cost parsing handles all variations"""
    print("Testing cost parsing robustness...")
    wrapper = StableSDKWrapper()
    
    test_cases = [
        {"cost_usd": 1.5},
        {"total_cost_usd": 2.0},
        {"total_cost": 1.25},
        {"cost": 0.75},
        {"cost_usd": "invalid"},  # Should handle gracefully
        {},  # No cost field
    ]
    
    for data in test_cases:
        data["type"] = "result"
        result = wrapper._parse_result_message(data)
        assert hasattr(result, 'cost_usd')
        assert isinstance(result.cost_usd, float)
    
    print("✅ Cost parsing robustness test passed")

async def test_managed_session_success():
    """Test successful session management"""
    print("Testing managed session success...")
    wrapper = StableSDKWrapper()
    
    async with wrapper.managed_session("test_operation") as session_id:
        assert session_id in wrapper.active_sessions
        assert session_id.startswith("session_")
    
    # Session should be moved to completed operations
    assert session_id not in wrapper.active_sessions
    assert len(wrapper.operations) == 1
    assert wrapper.operations[0].success == True
    print("✅ Managed session success test passed")

async def test_managed_session_failure():
    """Test session management with failures"""
    print("Testing managed session failure...")
    wrapper = StableSDKWrapper()
    
    session_id = None
    try:
        async with wrapper.managed_session("test_failure") as sid:
            session_id = sid
            assert session_id in wrapper.active_sessions
            raise RuntimeError("Test error")
    except RuntimeError:
        pass
    
    # Session should still be cleaned up
    assert session_id not in wrapper.active_sessions
    assert len(wrapper.operations) == 1
    assert wrapper.operations[0].success == False
    assert "Test error" in wrapper.operations[0].error
    print("✅ Managed session failure test passed")

def test_operation_stats():
    """Test operation statistics tracking"""
    print("Testing operation stats...")
    wrapper = StableSDKWrapper()
    
    # Add some mock operations
    from src.claude_code_sdk_stable import SDKOperation
    import time
    
    wrapper.operations = [
        SDKOperation("session1", "query", time.time(), time.time(), True),
        SDKOperation("session2", "query", time.time(), time.time(), False, "Test error", SDKErrorType.JSON_DECODE_ERROR),
    ]
    
    stats = wrapper.get_operation_stats()
    assert stats["total_operations"] == 2
    assert stats["successful_operations"] == 1
    assert stats["success_rate"] == 0.5
    assert stats["error_breakdown"]["json_decode"] == 1
    print("✅ Operation stats test passed")

def test_no_unhandled_exceptions_in_parsing():
    """CRITICAL: Message parsing must never throw unhandled exceptions"""
    print("Testing parsing exception handling...")
    wrapper = StableSDKWrapper()
    
    # Test malformed data that should be handled gracefully
    malformed_data = [
        {"type": "result"},  # Missing cost fields
        {"type": "assistant", "message": '{"incomplete":'},  # Truncated JSON
        {"type": "unknown", "random_field": "value"},  # Unknown message type
    ]
    
    for data in malformed_data:
        try:
            # This should either return a valid result or raise a controlled RuntimeError
            result = wrapper._patched_parse_message(wrapper, data)
            assert result is not None
        except RuntimeError:
            # Controlled failures are acceptable
            pass
        except Exception as e:
            # Unhandled exceptions are NOT acceptable
            raise AssertionError(f"Unhandled exception for data {data}: {e}")
    
    print("✅ Parsing exception handling test passed")

async def test_session_cleanup_guarantee():
    """CRITICAL: Sessions must always be cleaned up, even on errors"""
    print("Testing session cleanup guarantee...")
    wrapper = StableSDKWrapper()
    initial_active = len(wrapper.active_sessions)
    
    # Test that cleanup happens even with errors
    try:
        async with wrapper.managed_session("test") as session_id:
            assert len(wrapper.active_sessions) == initial_active + 1
            raise Exception("Simulated error")
    except:
        pass
    
    # Must be cleaned up
    assert len(wrapper.active_sessions) == initial_active
    assert len(wrapper.operations) > 0
    print("✅ Session cleanup guarantee test passed")

def run_all_tests():
    """Run all tests and report results"""
    print("=" * 60)
    print("STABLE SDK WRAPPER TEST SUITE")
    print("=" * 60)
    
    # Synchronous tests
    sync_tests = [
        test_wrapper_initialization,
        test_error_classification,
        test_json_repair,
        test_cost_parsing_robustness,
        test_operation_stats,
        test_no_unhandled_exceptions_in_parsing,
    ]
    
    for test in sync_tests:
        try:
            test()
        except Exception as e:
            print(f"❌ {test.__name__} FAILED: {e}")
            return False
    
    # Async tests
    async_tests = [
        test_managed_session_success,
        test_managed_session_failure,
        test_session_cleanup_guarantee,
    ]
    
    async def run_async_tests():
        for test in async_tests:
            try:
                await test()
            except Exception as e:
                print(f"❌ {test.__name__} FAILED: {e}")
                return False
        return True
    
    # Run async tests
    async_result = asyncio.run(run_async_tests())
    
    if async_result:
        print("\n" + "=" * 60)
        print("🎉 ALL TESTS PASSED - SDK IS STABLE")
        print("=" * 60)
        return True
    else:
        print("\n" + "=" * 60)
        print("❌ TESTS FAILED - SDK IS NOT STABLE")
        print("=" * 60)
        return False

if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)