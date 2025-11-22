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

使用 `claude mcp add` 命令添加 MCP 服务：

```bash
claude mcp add --transport stdio \
  -e OPENAI_API_KEY=你的千循API密钥 \
  -e OPENAI_BASE_URL=https://openai.app.msh.team/v1 \
  -- gemini-image node /path/to/ccblog/mcp/gemini-image-mcp/dist/index.js
```

**注意：** 请将路径替换为你本地的实际路径。

验证配置：
```bash
claude mcp list
```

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
