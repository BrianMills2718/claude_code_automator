#!/bin/bash
# Fast automated V4 testing with 10s retry delay

echo "🚀 Starting Fast Automated V4 Testing"
echo "📁 Project: example_projects/ml_portfolio_analyzer"
echo "⏱️  Retry delay: 10 seconds (fast iteration)"
echo "🔄 Continuous mode enabled"
echo "📊 Enhanced pattern monitoring active"
echo ""

cd /home/brian/cc_automator4

# Set environment for debugging and cost efficiency
export FORCE_SONNET=true
export PYTHONUNBUFFERED=1

# Run with fast retry for debugging
python tools/automated_v4_tester.py \
    --project example_projects/ml_portfolio_analyzer \
    --continuous \
    --timeout 120 \
    --retry-delay 10 \
    --max-attempts 100