#!/usr/bin/env python3
"""
Test runner for Todo API tests.
Runs unit and integration tests directly without pytest due to version compatibility issues.
"""
import sys
import traceback
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent))

def run_unit_tests():
    """Run unit tests for TodoService."""
    print("="*50)
    print("RUNNING UNIT TESTS")
    print("="*50)
    
    from tests.unit.test_todo_service import TestTodoService
    
    test_class = TestTodoService()
    test_methods = [method for method in dir(test_class) if method.startswith('test_')]
    
    passed = 0
    failed = 0
    
    for method_name in test_methods:
        try:
            print(f"\nRunning {method_name}...")
            test_class.setup_method()
            method = getattr(test_class, method_name)
            method()
            print(f"✓ {method_name} PASSED")
            passed += 1
        except Exception as e:
            print(f"✗ {method_name} FAILED: {e}")
            traceback.print_exc()
            failed += 1
    
    print(f"\nUnit Tests Summary: {passed} passed, {failed} failed")
    return failed == 0

def run_integration_tests():
    """Run integration tests for Todo API."""
    print("="*50)
    print("RUNNING INTEGRATION TESTS")
    print("="*50)
    
    from tests.integration.test_todo_api import TestTodoAPI
    
    test_class = TestTodoAPI()
    test_methods = [method for method in dir(test_class) if method.startswith('test_')]
    
    passed = 0
    failed = 0
    
    for method_name in test_methods:
        try:
            print(f"\nRunning {method_name}...")
            test_class.setup_method()
            method = getattr(test_class, method_name)
            method()
            print(f"✓ {method_name} PASSED")
            passed += 1
        except Exception as e:
            print(f"✗ {method_name} FAILED: {e}")
            traceback.print_exc()
            failed += 1
    
    print(f"\nIntegration Tests Summary: {passed} passed, {failed} failed")
    return failed == 0

def main():
    """Run all tests."""
    print("Running Todo API Test Suite")
    print("="*50)
    
    unit_success = run_unit_tests()
    integration_success = run_integration_tests()
    
    print("\n" + "="*50)
    print("FINAL TEST RESULTS")
    print("="*50)
    
    if unit_success and integration_success:
        print("🎉 ALL TESTS PASSED!")
        return True
    else:
        if not unit_success:
            print("❌ Unit tests failed")
        if not integration_success:
            print("❌ Integration tests failed")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)