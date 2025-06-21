# V4 Monitoring & Debugging Guide

## Running ML Portfolio Test with V4

### Quick Start

```bash
# Run with V4 intelligent orchestration
./run_ml_portfolio_test_v4.sh
```

This script provides:
- V4 intelligent meta-agent orchestration
- Full decision explanations
- Real-time monitoring suggestions
- Learning data collection

### Manual V4 Execution

```bash
cd example_projects/ml_portfolio_analyzer

# Basic V4 run
python ../../cli.py --v4 --verbose

# V4 with full visibility
python ../../cli.py --v4 --explain --verbose --infinite

# V4 with parallel strategies
python ../../cli.py --v4 --v4-parallel --explain --verbose
```

## Real-Time Monitoring

### 1. Interactive Dashboard (Recommended)

In a separate terminal:

```bash
# Start real-time V4 monitor
python tools/monitor_v4_realtime.py --project example_projects/ml_portfolio_analyzer

# Simple text mode (if curses fails)
python tools/monitor_v4_realtime.py --project example_projects/ml_portfolio_analyzer --simple
```

The dashboard shows:
- 📊 Current phase and strategy
- ❌ Failure patterns and counts
- 📈 Strategy performance metrics
- 📡 Real-time V4 decision events

### 2. Log Monitoring

Monitor specific V4 events in logs:

```bash
# Watch for V4 decisions
tail -f example_projects/ml_portfolio_analyzer/.cc_automator/logs/*.log | grep -E "(Strategy|Failure|Loop|Switch|Context)"

# Watch for infinite loops
tail -f example_projects/ml_portfolio_analyzer/.cc_automator/logs/*.log | grep -i "infinite loop"

# Watch for strategy switches
tail -f example_projects/ml_portfolio_analyzer/.cc_automator/logs/*.log | grep "Switching from"
```

### 3. Learning Data Monitoring

```bash
cd example_projects/ml_portfolio_analyzer

# Watch failure patterns
watch -n 5 'jq ".failures[-10:]" .cc_automator/v4_failure_history.json'

# Watch strategy performance
watch -n 5 'jq ".performances[-5:]" .cc_automator/v4_strategy_performance.json'

# Get failure summary
jq '.failures | group_by(.phase_name) | map({phase: .[0].phase_name, count: length})' .cc_automator/v4_failure_history.json
```

## V4 Decision Visibility

### What V4 Shows with --explain

1. **Context Analysis**
```
🔍 Project Context Analysis:
  - Project Type: ml_project
  - Complexity Score: 0.85/1.0
  - Technology Stack: python, pandas, scikit-learn
  - Requirement Clarity: 0.65/1.0
  - Similar Past Projects: 3
```

2. **Strategy Selection**
```
🎯 Strategy Selection: IterativeRefinementStrategy
  - Reason: History of 12 architecture failures
  - Best for: Complex projects with architecture challenges
  - Expected phases: 15 (including iterations)
```

3. **Failure Analysis**
```
❌ Failure Analysis:
  - Type: validation_error
  - Root Cause: Implementation violating architectural constraints repeatedly
  - Pattern: architecture_infinite_loop
  - Suggested Action: step_back_with_constraints
```

4. **Loop Breaking**
```
🔄 Infinite Loop Detected:
  - Phase: architecture
  - Attempts: 66
  - Generating constraints to break loop...
  - Constraints: Functions must be <40 lines, classes <15 methods
```

## Debugging V4 Behavior

### 1. Check Current Strategy

```bash
# Find current strategy
grep "Strategy Selection" .cc_automator/logs/*.log | tail -1

# See all strategies used
grep "Strategy Selection" .cc_automator/logs/*.log | sort | uniq
```

### 2. Analyze Failure Patterns

```python
# Python script to analyze failures
import json

with open('.cc_automator/v4_failure_history.json') as f:
    data = json.load(f)
    
# Find most problematic phases
from collections import Counter
phase_failures = Counter(f['phase_name'] for f in data['failures'])
print("Most failed phases:", phase_failures.most_common(5))

# Find infinite loop patterns
for phase, count in phase_failures.items():
    if count > 10:
        print(f"Possible infinite loop in {phase}: {count} failures")
```

### 3. Understand Strategy Decisions

Look for these key log entries:

```bash
# Why a strategy was selected
grep -A5 "Selecting strategy" .cc_automator/logs/*.log

# Why strategy switched
grep -B5 -A5 "Switching from" .cc_automator/logs/*.log

# What constraints were generated
grep -A10 "Generating constraints" .cc_automator/logs/*.log
```

## V4 Performance Metrics

### Key Metrics to Monitor

1. **Strategy Success Rate**
```bash
# Calculate strategy success rates
jq '.performances | group_by(.strategy) | map({strategy: .[0].strategy, success_rate: (map(select(.evidence_quality > 0.7)) | length) / length})' .cc_automator/v4_strategy_performance.json
```

2. **Phase Failure Rates**
```bash
# Get phase failure rates
jq '.failures | group_by(.phase_name) | map({phase: .[0].phase_name, failures: length})' .cc_automator/v4_failure_history.json
```

3. **Learning Effectiveness**
```bash
# Check if failures decrease over time
jq '.failures | group_by(.phase_name) | map({phase: .[0].phase_name, early_failures: map(select(.attempt_num <= 3)) | length, late_failures: map(select(.attempt_num > 3)) | length})' .cc_automator/v4_failure_history.json
```

## Common V4 Scenarios

### Scenario 1: Architecture Loop Detection

V4 detects the infinite loop pattern:
```
🔄 Infinite loop detected in phase architecture
📊 Pattern: Same error repeated 5 times
🔧 Action: Generating loop-breaking constraints
✅ Result: Constraints force different approach
```

### Scenario 2: Strategy Switch

V4 switches strategies due to failures:
```
❌ V3PipelineStrategy failed after 3 attempts
📊 Analyzing failure patterns...
🔀 Switching to IterativeRefinementStrategy
✅ New strategy focuses on problematic phases
```

### Scenario 3: Parallel Exploration

For ambiguous requirements:
```
🔍 Context: Requirement clarity 0.2/1.0
🎯 Decision: Use parallel exploration
⚡ Running 3 strategies simultaneously
✅ Best result selected based on evidence
```

## Troubleshooting V4

### V4 Not Learning?

Check learning is enabled:
```bash
# Verify learning files are being created
ls -la .cc_automator/v4_*.json

# Check if learning is disabled
grep "learning_enabled" .cc_automator/logs/*.log
```

### Strategy Not Switching?

Check failure analysis:
```bash
# Look for failure analysis results
grep -A10 "Failure analysis:" .cc_automator/logs/*.log

# Check confidence levels
grep "confidence:" .cc_automator/logs/*.log
```

### Performance Issues?

Monitor resource usage:
```bash
# Check parallel execution
grep "Resource usage" .cc_automator/logs/*.log

# Monitor memory
top -p $(pgrep -f "cli.py --v4")
```

## Best Practices

1. **Always use --explain for new projects** to understand V4's reasoning
2. **Monitor failure patterns** to see if V4 is learning effectively
3. **Check strategy performance** to validate V4's choices
4. **Use real-time monitor** for complex projects
5. **Review learning data** after runs to improve future executions

## Summary

V4 provides extensive visibility through:
- Real-time monitoring dashboard
- Detailed decision explanations
- Learning data persistence
- Strategy performance metrics
- Failure pattern analysis

Use these tools to debug issues and understand V4's intelligent behavior!