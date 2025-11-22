#!/bin/bash

# Test script for gemini-image-mcp
# This simulates how Claude Code would call the MCP

export OPENAI_API_KEY="***REMOVED-API-KEY***"
export OPENAI_BASE_URL="https://openai.app.msh.team/v1"

echo "Testing Gemini Image MCP..."
echo ""

# Start the MCP server and send a test request
node dist/index.js <<EOF
{"jsonrpc": "2.0", "id": 1, "method": "tools/list"}
EOF

echo ""
echo "If you see the tool list above, the MCP is working correctly!"
echo ""
echo "To use with Claude Code, add this to ~/.claude/claude_desktop_config.json:"
echo ""
cat <<CONFIG
{
  "mcpServers": {
    "gemini-image": {
      "name": "Gemini 图片生成",
      "command": "node",
      "args": [
        "$(pwd)/dist/index.js"
      ],
      "env": {
        "OPENAI_API_KEY": "***REMOVED-API-KEY***",
        "OPENAI_BASE_URL": "https://openai.app.msh.team/v1"
      }
    }
  }
}
CONFIG
