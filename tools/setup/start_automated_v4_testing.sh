#!/bin/bash
# Quick start script for automated V4 testing
# Runs the automated tester with default settings for the ML Portfolio project

echo "🤖 Starting Automated V4 Testing..."
echo "📁 Project: example_projects/ml_portfolio_analyzer"
echo "💰 Using FORCE_SONNET=true for cost efficiency"
echo "🔄 Will run continuously with 30s delays between attempts"
echo "⏱️  Each attempt has 1 hour timeout"
echo ""
echo "📋 You can:"
echo "   • Press Ctrl+C to stop gracefully"  
echo "   • Monitor logs in logs/automated_v4_testing/"
echo "   • Check progress in real-time below"
echo ""
echo "🚀 Starting in 3 seconds..."
sleep 3

cd /home/brian/cc_automator4

# Set environment for cost efficiency
export FORCE_SONNET=true

# Run the automated tester
python tools/automated_v4_tester.py \
    --project example_projects/ml_portfolio_analyzer \
    --continuous \
    --timeout 3600 \
    --retry-delay 30 \
    --max-attempts 50