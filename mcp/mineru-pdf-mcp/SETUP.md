# MinerU PDF MCP 服务设置指南

## 概述

这是一个基于 MinerU 的 MCP 服务器，可以将 PDF 文档转换为 Markdown 格式并提取图片。

## 已完成的安装步骤

✅ 1. MinerU MCP 已安装到 `/Users/limo/Documents/GithubRepo/ccblog/.venv`
✅ 2. 项目位于 `/Users/limo/Documents/GithubRepo/ccblog/mcp/mineru-pdf-mcp`

## 配置步骤

### 1. 获取 MinerU API Key

访问 [https://mineru.net](https://mineru.net) 注册并获取 API key

### 2. 配置环境变量

编辑 `.env` 文件：

```bash
cd /Users/limo/Documents/GithubRepo/ccblog/mcp/mineru-pdf-mcp
vi .env
```

将 `your_api_key_here` 替换为你的实际 API key

### 3. 添加到 Claude Code 配置

在 Claude Code 的 MCP 配置中添加（通常是 `~/.config/claude/mcp.json` 或类似位置）:

```json
{
  "mcpServers": {
    "mineru-pdf": {
      "command": "/Users/limo/Documents/GithubRepo/ccblog/.venv/bin/python",
      "args": ["-m", "mineru.cli"],
      "cwd": "/Users/limo/Documents/GithubRepo/ccblog/mcp/mineru-pdf-mcp",
      "env": {
        "MINERU_API_BASE": "https://mineru.net",
        "MINERU_API_KEY": "your_api_key_here",
        "OUTPUT_DIR": "./downloads",
        "USE_LOCAL_API": "false"
      }
    }
  }
}
```

## 使用方法

### 主要工具

1. **parse_documents** - 解析文档（PDF、Word、PPT、图片等）
   - 参数:
     - `file_sources`: 文件路径或 URL（支持多个，逗号分隔）
     - `enable_ocr`: 是否启用 OCR（默认 false）
     - `language`: 文档语言（默认 "ch"，可选 "en" 等）
     - `page_ranges`: 页码范围（可选，如 "2,4-6"）

2. **get_ocr_languages** - 获取支持的 OCR 语言列表

### 示例

在 Claude Code 中可以直接使用：

```
请解析这个 PDF 文件：/path/to/document.pdf
```

或者：

```
帮我把这些 PDF 转换为 Markdown：
- /path/to/file1.pdf
- https://example.com/file2.pdf
```

## 手动测试

你也可以手动运行服务器进行测试：

```bash
cd /Users/limo/Documents/GithubRepo/ccblog/mcp/mineru-pdf-mcp
source /Users/limo/Documents/GithubRepo/ccblog/.venv/bin/activate
mineru-mcp --transport sse
```

服务将在 `http://localhost:8001` 启动

## 输出说明

- 转换后的 Markdown 文件保存在 `./downloads` 目录下
- 图片会被提取并保存在相应的子目录中
- 每个文档会有自己的子目录，包含 Markdown 文件和提取的图片

## 支持的文件格式

- PDF (.pdf)
- Word (.doc, .docx)
- PowerPoint (.ppt, .pptx)
- 图片 (.jpg, .jpeg, .png)

## 故障排除

### API Key 错误

如果遇到 API key 相关错误，确保：
1. 已在 https://mineru.net 注册并获取有效的 API key
2. `.env` 文件中的 API key 正确无误
3. 环境变量正确传递给 MCP 服务器

### 超时问题

处理大型 PDF 可能需要较长时间，如果遇到超时：
1. 尝试处理较小的文件
2. 分批处理多个文件
3. 考虑增加客户端超时设置

## 本地 API 模式（可选）

如果需要更高的隐私性或离线使用，可以部署本地 MinerU API：

1. 设置 `USE_LOCAL_API=true`
2. 配置 `LOCAL_MINERU_API_BASE` 为你的本地 API 地址
3. 参考 MinerU 官方文档部署本地服务
