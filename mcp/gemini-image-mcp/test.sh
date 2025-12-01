#!/bin/bash

# Test script for gemini-image-mcp
# This simulates how Claude Code would call the MCP

# Please set these environment variables before running this script:
# export OPENAI_API_KEY="your-api-key-here"
# export OPENAI_BASE_URL="https://openai.app.msh.team/v1"

if [ -z "$OPENAI_API_KEY" ]; then
    echo "Error: OPENAI_API_KEY environment variable is not set"
    echo "Please run: export OPENAI_API_KEY=\"your-api-key-here\""
    exit 1
fi

if [ -z "$OPENAI_BASE_URL" ]; then
    echo "Error: OPENAI_BASE_URL environment variable is not set"
    echo "Please run: export OPENAI_BASE_URL=\"https://openai.app.msh.team/v1\""
    exit 1
fi

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
        "OPENAI_API_KEY": "your-api-key-here",
        "OPENAI_BASE_URL": "https://openai.app.msh.team/v1"
      }
    }
  }
}
CONFIG
