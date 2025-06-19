#!/bin/bash
# Background monitoring script
echo "📡 Starting V4 monitoring in background..."

# Monitor for failure patterns
tail -f .cc_automator/logs/*.log 2>/dev/null | grep -E "(FAILURE|LOOP|STRATEGY|DECISION)" &

# Monitor learning data
watch -n 5 'if [ -f .cc_automator/v4_failure_history.json ]; then echo "=== Failure Patterns ==="; jq -r ".failures[-5:] | .[] | \"Phase: \\(.phase_name) Attempt: \\(.attempt_num) Error: \\(.error_type)\"" .cc_automator/v4_failure_history.json 2>/dev/null; fi' &

# Monitor strategy performance
watch -n 10 'if [ -f .cc_automator/v4_strategy_performance.json ]; then echo "=== Strategy Performance ==="; jq -r ".performances[-3:] | .[] | \"Strategy: \\(.strategy) Time: \\(.execution_time)s Quality: \\(.evidence_quality)\"" .cc_automator/v4_strategy_performance.json 2>/dev/null; fi' &
