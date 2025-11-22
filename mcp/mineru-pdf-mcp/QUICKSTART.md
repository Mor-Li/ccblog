# MinerU PDF MCP 快速开始

## 🎯 一键配置指南

### Step 1: 获取 API Key

1. 访问 [https://mineru.net](https://mineru.net)
2. 注册账号并获取 API key

### Step 2: 配置环境变量

编辑 `.env` 文件：

```bash
cd /Users/limo/Documents/GithubRepo/ccblog/mcp/mineru-pdf-mcp
```

替换 `MINERU_API_KEY` 为你的 API key

### Step 3: 添加到 Claude Code

使用 `claude mcp add` 命令（推荐）：

```bash
claude mcp add mineru-pdf \
  --command /Users/limo/Documents/GithubRepo/ccblog/.venv/bin/python \
  --args "-m" --args "mineru.cli" \
  --cwd /Users/limo/Documents/GithubRepo/ccblog/mcp/mineru-pdf-mcp \
  --env MINERU_API_BASE=https://mineru.net \
  --env MINERU_API_KEY=your_api_key_here \
  --env OUTPUT_DIR=./downloads \
  --env USE_LOCAL_API=false
```

或者手动编辑 MCP 配置文件，将 `claude-code-config.json` 的内容合并到你的 MCP 配置中。

### Step 4: 重启 Claude Code

重启 Claude Code 以加载新的 MCP 服务器配置。

## 🚀 使用示例

### 1. 解析单个 PDF 文件

```
请帮我解析这个 PDF：/path/to/document.pdf
```

### 2. 批量解析多个文件

```
帮我把这些文件转换为 Markdown：
- /path/to/file1.pdf
- /path/to/file2.pdf
- https://example.com/paper.pdf
```

### 3. 启用 OCR 扫描版 PDF

```
这是一个扫描版PDF，请用OCR解析：/path/to/scanned.pdf，需要启用OCR
```

### 4. 指定页面范围

```
只解析 PDF 的第 2-5 页：/path/to/document.pdf，页面范围 2-5
```

### 5. 查询支持的语言

```
MinerU 支持哪些 OCR 语言？
```

## 📁 输出结构

转换后的文件保存在 `./downloads` 目录：

```
downloads/
├── document_abc123/
│   ├── full.md          # 完整的 Markdown 文件
│   ├── images/          # 提取的图片
│   │   ├── image_1.png
│   │   ├── image_2.png
│   │   └── ...
│   └── auto/            # 其他辅助文件
```

## 🔧 手动测试 MCP 服务器

如果需要手动测试服务器：

```bash
# 激活虚拟环境
cd /Users/limo/Documents/GithubRepo/ccblog
source .venv/bin/activate

# 以 stdio 模式运行（用于 MCP）
cd mcp/mineru-pdf-mcp
mineru-mcp

# 或以 SSE 服务器模式运行（用于调试）
mineru-mcp --transport sse --port 8001
```

## 💡 使用技巧

1. **大文件处理**: 大型 PDF 可能需要较长时间，建议分批处理
2. **图片质量**: MinerU 会自动提取 PDF 中的图片，保持原始质量
3. **表格识别**: 支持识别复杂表格并转换为 Markdown 表格格式
4. **公式识别**: 支持数学公式的识别和转换
5. **多语言支持**: 通过 `get_ocr_languages` 工具查看支持的语言

## 📚 支持的文件格式

- ✅ PDF (.pdf)
- ✅ Word (.doc, .docx)
- ✅ PowerPoint (.ppt, .pptx)
- ✅ 图片 (.jpg, .jpeg, .png)

## ⚠️ 常见问题

### Q: API Key 无效？

A: 确保从 https://mineru.net 获取了有效的 API key，并正确配置在 `.env` 文件中

### Q: 处理超时？

A:
- 尝试处理较小的文件
- 检查网络连接
- 考虑使用本地 API 模式（需要额外配置）

### Q: 图片没有提取？

A: 图片会自动提取到输出目录的 `images/` 子目录中，检查 `downloads/` 目录

### Q: OCR 识别不准确？

A:
- 确保启用了 OCR（`enable_ocr=true`）
- 选择正确的语言参数
- 扫描版 PDF 建议使用高分辨率版本

## 🔗 相关资源

- [MinerU 官方文档](https://github.com/opendatalab/MinerU)
- [MinerU API 文档](https://mineru.net/docs)
- [FastMCP 文档](https://github.com/jlowin/fastmcp)

## 📝 下一步

安装完成后，你可以在 Claude Code 中直接使用 MinerU 的 PDF 解析功能，无需手动运行任何命令！
