#!/bin/bash

# Install MCP Servers for CC_AUTOMATOR4
# Provides alternatives to problematic claude-code-sdk tools

echo "🔧 Installing MCP servers for CC_AUTOMATOR4..."

# Check if npm is available
if ! command -v npm &> /dev/null; then
    echo "❌ npm is required but not installed. Please install Node.js first."
    exit 1
fi

echo "📦 Installing MCP servers globally..."

# Core web search replacements
echo "Installing web search servers..."
npm install -g pskill9/web-search || echo "⚠️  Failed to install pskill9/web-search"

# Documentation and development tools
echo "Installing development tools..."
npm install -g @anthropic/ref || echo "⚠️  Failed to install @anthropic/ref"
npm install -g @anthropic/github || echo "⚠️  Failed to install @anthropic/github" 
npm install -g @anthropic/firecrawl || echo "⚠️  Failed to install @anthropic/firecrawl"

# Advanced search (may require API keys)
echo "Installing advanced search tools..."
npm install -g @exa-ai/exa-mcp-server || echo "⚠️  Failed to install @exa-ai/exa-mcp-server (may need API key)"

# Code context and workspace tools  
echo "Installing workspace tools..."
npm install -g juehang/vscode-mcp-server || echo "⚠️  Failed to install juehang/vscode-mcp-server"
npm install -g wonderwhy-er/DesktopCommanderMCP || echo "⚠️  Failed to install wonderwhy-er/DesktopCommanderMCP"

# Secure execution sandbox
echo "Installing sandbox execution..."
npm install -g pydantic/pydantic-ai/mcp-run-python || echo "⚠️  Failed to install pydantic/pydantic-ai/mcp-run-python"

echo ""
echo "✅ MCP server installation complete!"
echo ""
echo "📋 Next steps:"
echo "1. Set DISABLE_MCP=false to enable MCP servers"
echo "2. Test with: python cli.py --project test_example --verbose"
echo "3. Check logs in .cc_automator/logs/ for MCP connectivity"
echo ""
echo "🔍 Troubleshooting:"
echo "- Some servers may need API keys (check server documentation)"
echo "- Use 'claude mcp list' to verify server connectivity"
echo "- Check mcp_config.json for server configurations"