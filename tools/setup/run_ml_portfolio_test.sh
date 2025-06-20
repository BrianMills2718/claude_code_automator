#!/bin/bash

# ML Portfolio Analyzer Test Run
# This script runs the ML Portfolio Analyzer project with:
# - Sonnet model forced for all phases (cost optimization)
# - Infinite mode (unlimited step-backs until success)
# - Verbose output for detailed monitoring

set -e

echo "🚀 Starting ML Portfolio Analyzer Test Run"
echo "=================================================="
echo "📁 Project: ML Portfolio Analyzer (Advanced Financial Analysis)"
echo "🧠 Model: Claude Sonnet 4 (forced for all phases)"
echo "♾️  Mode: Infinite (unlimited retries until success)"
echo "📝 Phases: 11-phase pipeline with architecture quality gate"
echo "=================================================="

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
echo "🎯 Starting CC_AUTOMATOR4 V2 with 11-phase pipeline..."
echo "Expected phases:"
echo "  1. research     - Analyze ML/finance requirements"
echo "  2. planning     - Create implementation plan"
echo "  3. implement    - Build core system"
echo "  4. architecture - Review code structure (NEW QUALITY GATE)"
echo "  5. lint         - Fix code style issues"
echo "  6. typecheck    - Add type hints and fix errors"
echo "  7. test         - Create and fix unit tests"
echo "  8. integration - Fix integration tests"
echo "  9. e2e          - Test complete system"
echo " 10. validate     - Ensure no mocks/stubs"
echo " 11. commit       - Create git commit"
echo ""

# Run the orchestrator
python ../../cli.py --verbose --infinite

echo ""
echo "✅ ML Portfolio Analyzer test run completed!"
echo "Check the .cc_automator directory for detailed logs and evidence."