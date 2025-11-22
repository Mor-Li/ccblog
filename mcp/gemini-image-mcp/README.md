# Gemini Image MCP

MCP server for generating images using Gemini 3 Pro Image Preview model (千循).

## Features

- Generate images from text prompts using Gemini 3 Pro
- Save generated images to local files
- Base64 encoded image support

## Installation

```bash
cd mcp/gemini-image-mcp
npm install
npm run build
```

## Configuration

Add to your Claude Code MCP config (`~/.claude/claude_desktop_config.json`):

```json
{
  "mcpServers": {
    "gemini-image": {
      "name": "Gemini 图片生成",
      "command": "node",
      "args": [
        "/Users/limo/Documents/GithubRepo/ccblog/mcp/gemini-image-mcp/dist/index.js"
      ],
      "env": {
        "OPENAI_API_KEY": "***REMOVED-API-KEY***",
        "OPENAI_BASE_URL": "https://openai.app.msh.team/v1"
      }
    }
  }
}
```

Or use environment variables from your shell.

## Usage

In Claude Code:

```
请帮我生成一张图片：一个蓝色的圆圈在白色背景上，保存到 /tmp/test.png
```

The MCP provides one tool:

### generate_image

- **prompt** (required): Detailed description of the image to generate
- **save_path** (optional): File path to save the generated image

## Model

Uses `gemini-3-pro-image-preview` from 千循 (nano banana 2).
