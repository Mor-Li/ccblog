# Gemini OpenAI MCP

Simple MCP server for querying Gemini 3 via OpenAI-compatible API.

## Features

- Query Gemini 3 Pro model
- Support for text file attachments (txt/md)
- Save responses to markdown files
- Uses OpenAI-compatible API endpoint

## Installation

```bash
npm install
```

## Configuration

Set environment variables in your shell:

```bash
export OPENAI_API_KEY=your-api-key
export OPENAI_BASE_URL=https://openai.app.msh.team/v1
export GEMINI_MODEL=gemini-3-pro-preview  # optional, default value
```

## Add to Claude Code

Use the `claude mcp add` command:

```bash
claude mcp add --transport stdio \
  -e OPENAI_API_KEY=你的千循API密钥 \
  -e OPENAI_BASE_URL=https://openai.app.msh.team/v1 \
  -e GEMINI_MODEL=gemini-3-pro-preview \
  -- gemini node /home/limo/ccblog/mcp/gemini-openai-mcp/index.js
```

**注意：** 请将路径替换为你本地的实际路径。

验证配置：
```bash
claude mcp list
```

## Usage

Once configured, you can use the `gemini_query` tool in Claude Code:

```
Query Gemini with a simple prompt:
- prompt: "What is quantum computing?"

Query with file attachments:
- prompt: "Summarize these files"
- file_paths: ["/path/to/file1.txt", "/path/to/file2.md"]
```

## Tool: gemini_query

**Parameters:**
- `prompt` (required): The text prompt to send to Gemini 3
- `file_paths` (optional): Array of file paths (txt/md only) to include
- `output_file_path` (optional): Output file path (relative or absolute) to save response as markdown

**Behavior:**
- If `output_file_path` is provided: Response is saved to file, returns file path confirmation
- If `output_file_path` is NOT provided: Response is returned directly in the MCP result

**Examples:**

```javascript
// Direct response
{
  "prompt": "What is quantum computing?"
}

// With file attachments
{
  "prompt": "Summarize these files",
  "file_paths": ["/path/to/file1.txt", "/path/to/file2.md"]
}

// Save to file (absolute path)
{
  "prompt": "Explain this code",
  "file_paths": ["/path/to/code.txt"],
  "output_file_path": "/home/user/output/explanation.md"
}

// Save to file (relative path)
{
  "prompt": "Write a blog post about AI",
  "output_file_path": "./blog/ai-article.md"
}
```
