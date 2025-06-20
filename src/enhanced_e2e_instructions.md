# Enhanced E2E Phase Instructions

## CRITICAL: User Journey Testing Required

The E2E phase MUST test complete user workflows, not just individual commands. This includes:

### 1. **Sequential Command Testing**
Test realistic sequences of commands that users would actually perform:
```bash
# Example for data analysis system:
python main.py fetch AAPL      # Step 1: Get data
python main.py analyze AAPL    # Step 2: Analyze that data (MUST work!)

# Example for task tracker:
python main.py add "Task 1"    # Step 1: Create task
python main.py list            # Step 2: See the task
python main.py complete 1      # Step 3: Mark it done
```

### 2. **State Dependency Testing**
Test that commands that depend on previous state work correctly:
- If `fetch` stores data, `analyze` must be able to use it
- If `create` makes an item, `update` must be able to modify it
- If `delete` removes something, `list` must reflect the change

### 3. **Error Scenario Testing**
Test graceful handling when dependencies are missing:
- What happens when analyzing without data?
- What happens when database is unavailable?
- Do all commands handle missing prerequisites gracefully?

### 4. **Environment Variation Testing**
Test with different configurations:
- Without database (in-memory fallback?)
- Without API keys (degraded functionality?)
- With minimal dependencies

### 5. **Evidence Requirements**
Your e2e_evidence.log MUST include:
```
=== User Journey: Fetch Then Analyze ===
Command 1: python main.py fetch AAPL
Output: [actual output showing success]

Command 2: python main.py analyze AAPL  
Output: [actual output - should NOT say "No data found"]
Status: ✅ PASSED - Analysis worked after fetch

=== User Journey: Search Then Fetch ===
[Similar format for other journeys]
```

## VALIDATION CRITERIA

The E2E phase will now check:
1. ✅ Evidence log exists (current requirement)
2. ✅ main.py runs without errors (current requirement)
3. ✅ **NEW**: User journeys pass (sequential commands work together)
4. ✅ **NEW**: State dependencies work (commands can use data from previous commands)
5. ✅ **NEW**: Error handling is graceful (missing dependencies don't crash)

## Example E2E Test Script

```python
# Example of what your E2E testing should look like:
import subprocess
import sys

def run_command(cmd):
    """Run a command and return output"""
    result = subprocess.run(cmd.split(), capture_output=True, text=True)
    return result.returncode, result.stdout, result.stderr

def test_fetch_analyze_journey():
    """Test that analyze works after fetch"""
    print("=== Testing Fetch->Analyze Journey ===")
    
    # Step 1: Fetch data
    code, out, err = run_command("python main.py fetch AAPL")
    print(f"Fetch result: {code}")
    print(f"Output: {out[:200]}...")
    
    if code != 0:
        print("❌ FAILED: Fetch command failed")
        return False
        
    # Step 2: Analyze the fetched data
    code, out, err = run_command("python main.py analyze AAPL")
    print(f"Analyze result: {code}")
    print(f"Output: {out[:200]}...")
    
    if "No data found" in out:
        print("❌ FAILED: Analyze couldn't use fetched data!")
        return False
        
    print("✅ PASSED: Analyze successfully used fetched data")
    return True

# Run all journey tests
if __name__ == "__main__":
    passed = test_fetch_analyze_journey()
    # Add more journey tests...
    
    sys.exit(0 if passed else 1)
```

## Remember

The goal is to ensure the generated system works for REAL USERS doing REAL TASKS, not just that individual commands run in isolation. Test the complete user experience!