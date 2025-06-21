#!/bin/bash

# ML Portfolio Analyzer Test Run - V4 Intelligent Mode
# This script runs the ML Portfolio Analyzer project with:
# - V4 intelligent meta-agent orchestration
# - Full decision explanations for visibility
# - Sonnet model forced for all phases (cost optimization)
# - Infinite mode (unlimited step-backs until success)
# - Enhanced monitoring and debugging output

set -e

echo "🚀 Starting ML Portfolio Analyzer Test Run with V4 Intelligence"
echo "================================================================"
echo "📁 Project: ML Portfolio Analyzer (Advanced Financial Analysis)"
echo "🧠 Model: Claude Sonnet 4 (forced for all phases)"
echo "🤖 Mode: V4 Intelligent Meta-Agent with Explanations"
echo "♾️  Retries: Infinite (unlimited retries with learning)"
echo "📊 Features: Failure pattern learning, adaptive strategies"
echo "📝 Phases: 11-phase pipeline with intelligent orchestration"
echo "================================================================"

# Change to project directory
cd example_projects/ml_portfolio_analyzer

# Set environment variables for configuration
export FORCE_SONNET=true
export CLAUDE_MODEL=claude-sonnet-4-20250514
export CC_INFINITE_MODE=true

# Show current git status
echo "📋 Git Status:"
git status --short

echo ""
echo "🎯 V4 Intelligence Features:"
echo "  • Context Analysis - Understands this is an ML/Finance project"
echo "  • Strategy Selection - Chooses optimal approach based on complexity"
echo "  • Failure Learning - Detects and breaks infinite loops"
echo "  • Multi-Strategy - Can explore parallel approaches if needed"
echo ""

echo "📊 Expected V4 Behavior:"
echo "  1. Analyze project context (ML project, high complexity)"
echo "  2. Select appropriate strategy (likely iterative refinement)"
echo "  3. Monitor for architecture phase loops (known V3 issue)"
echo "  4. Adapt strategy if failures detected"
echo "  5. Generate constraints to break any infinite loops"
echo ""

echo "🔍 Enhanced Visibility Options:"
echo "  • --explain: Shows V4 decision reasoning"
echo "  • --verbose: Detailed phase execution logs"
echo "  • Real-time failure pattern detection"
echo "  • Strategy switching explanations"
echo ""

# Create monitoring script that runs in background
cat > monitor_v4.sh << 'EOF'
#!/bin/bash
# Background monitoring script
echo "📡 Starting V4 monitoring in background..."

# Monitor for failure patterns
tail -f .cc_automator/logs/*.log 2>/dev/null | grep -E "(FAILURE|LOOP|STRATEGY|DECISION)" &

# Monitor learning data
watch -n 5 'if [ -f .cc_automator/v4_failure_history.json ]; then echo "=== Failure Patterns ==="; jq -r ".failures[-5:] | .[] | \"Phase: \\(.phase_name) Attempt: \\(.attempt_num) Error: \\(.error_type)\"" .cc_automator/v4_failure_history.json 2>/dev/null; fi' &

# Monitor strategy performance
watch -n 10 'if [ -f .cc_automator/v4_strategy_performance.json ]; then echo "=== Strategy Performance ==="; jq -r ".performances[-3:] | .[] | \"Strategy: \\(.strategy) Time: \\(.execution_time)s Quality: \\(.evidence_quality)\"" .cc_automator/v4_strategy_performance.json 2>/dev/null; fi' &
EOF

chmod +x monitor_v4.sh

echo "💡 TIP: Run ./monitor_v4.sh in another terminal for real-time monitoring"
echo ""

echo "🏃 Starting V4 orchestration with full explanations..."
echo "================================================================"

# Run the V4 orchestrator with all visibility features
python ../../cli.py \
    --v4 \
    --explain \
    --verbose \
    --infinite \
    --v4-learning \
    2>&1 | tee v4_execution.log

echo ""
echo "✅ ML Portfolio Analyzer V4 test run completed!"
echo ""
echo "📊 V4 Analysis Results:"
echo "  • Check .cc_automator/v4_failure_history.json for learned patterns"
echo "  • Check .cc_automator/v4_strategy_performance.json for strategy metrics"
echo "  • Check v4_execution.log for complete execution history"
echo "  • Check .cc_automator/logs/ for detailed phase logs"
echo ""

# Show summary of V4 learning
if [ -f .cc_automator/v4_failure_history.json ]; then
    echo "🧠 Failure Patterns Learned:"
    jq -r '.failures | group_by(.phase_name) | .[] | "\(.[-1].phase_name): \(length) failures"' .cc_automator/v4_failure_history.json
fi

if [ -f .cc_automator/v4_strategy_performance.json ]; then
    echo ""
    echo "📈 Strategy Performance:"
    jq -r '.performances | group_by(.strategy) | .[] | "\(.[-1].strategy): \(length) executions, avg quality: \([.[].evidence_quality] | add/length)"' .cc_automator/v4_strategy_performance.json
fi

# Cleanup monitoring script
rm -f monitor_v4.sh