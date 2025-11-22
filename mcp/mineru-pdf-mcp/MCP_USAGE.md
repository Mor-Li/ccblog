# MinerU PDF MCP Server 使用指南

## 简介

这是一个完全本地运行的 MinerU PDF 解析 MCP 服务器，无需任何 API Key，直接调用本地 MinerU CLI 进行 PDF 解析。

## 特性

- ✅ **完全本地运行**：无需云端 API，所有处理都在本地完成
- ✅ **零配置**：无需 API Key 或额外的服务端
- ✅ **MCP 协议**：标准的 Model Context Protocol 实现
- ✅ **功能完整**：支持公式识别、表格提取、多语言 OCR
- ✅ **自动提取图片**：自动保存 PDF 中的所有图片

## 安装

### 1. 确保已安装 MinerU

```bash
cd /Users/limo/Documents/GithubRepo/ccblog
source .venv/bin/activate

# 首次使用：下载模型（约 2-3GB）
python -m mineru.cli.models_download
```

### 2. 添加 MCP 服务器

```bash
claude mcp add --transport stdio \
  -- mineru-pdf /Users/limo/Documents/GithubRepo/ccblog/.venv/bin/python \
     /Users/limo/Documents/GithubRepo/ccblog/mcp/mineru-pdf-mcp/server.py
```

### 3. 验证安装

```bash
claude mcp list
```

你应该看到：
```
mineru-pdf: ... - ✓ Connected
```

## 使用方法

### 在 Claude Code 中使用

配置完成后，直接在 Claude Code 对话中说：

#### 示例 1：基本使用
```
帮我解析这个 PDF：/path/to/paper.pdf
```

#### 示例 2：指定输出目录
```
把 /path/to/document.pdf 解析为 Markdown，输出到 ./output 目录
```

#### 示例 3：中文 PDF
```
解析这个中文 PDF：/path/to/chinese.pdf，语言设置为中文
```

#### 示例 4：扫描版 PDF
```
这是一个扫描版 PDF，请使用 OCR 模式解析：/path/to/scan.pdf
```

### MCP 工具参数

`parse_pdf` 工具支持以下参数：

| 参数 | 类型 | 必填 | 默认值 | 说明 |
|------|------|------|--------|------|
| `pdf_path` | string | ✅ | - | PDF 文件路径（绝对或相对） |
| `output_dir` | string | ❌ | `./output` | 输出目录路径 |
| `language` | string | ❌ | `en` | 文档语言（en, ch, ja, ko 等） |
| `mode` | string | ❌ | `auto` | 解析模式（auto, txt, ocr） |
| `enable_formula` | boolean | ❌ | `true` | 是否启用公式识别 |
| `enable_table` | boolean | ❌ | `true` | 是否启用表格识别 |

## 输出结果

解析成功后，会生成以下文件：

```
output/
└── document/
    ├── document.md           # 最终的 Markdown 文件
    ├── images/               # 提取的所有图片
    │   ├── image_001.jpg
    │   ├── image_002.jpg
    │   └── ...
    └── auto/                 # 中间处理文件
        ├── content_list.json
        ├── middle.json
        └── model.json
```

MCP 工具会返回一个 JSON 结果：

```json
{
  "success": true,
  "message": "PDF 解析成功",
  "markdown_file": "/path/to/output/document/auto/document.md",
  "images_dir": "/path/to/output/document/auto/images",
  "image_count": 15,
  "output_dir": "/path/to/output/document"
}
```

## 支持的语言

- `en` - 英文（默认）
- `ch` - 中文
- `ja` - 日语
- `ko` - 韩语
- `ar` - 阿拉伯语
- `de` - 德语
- `fr` - 法语
- `ru` - 俄语

## 解析模式

- `auto` - 自动检测（推荐）
- `txt` - 文本型 PDF（速度最快）
- `ocr` - 扫描版 PDF（使用 OCR）

## 故障排除

### 问题1: MCP 连接失败

**解决方法**：
```bash
# 检查 Python 路径是否正确
/Users/limo/Documents/GithubRepo/ccblog/.venv/bin/python --version

# 检查 server.py 是否可执行
ls -l /Users/limo/Documents/GithubRepo/ccblog/mcp/mineru-pdf-mcp/server.py
```

### 问题2: 模型未下载

**解决方法**：
```bash
cd /Users/limo/Documents/GithubRepo/ccblog
source .venv/bin/activate
python -m mineru.cli.models_download
```

### 问题3: 解析失败

**常见原因**：
1. PDF 文件路径不存在
2. 输出目录没有写入权限
3. 内存不足（可以尝试关闭其他程序）

**查看详细日志**：
错误信息会在 MCP 响应中返回，检查返回的 JSON 中的 `error` 字段。

### 问题4: 解析速度慢

**优化建议**：
- Mac M1/M2/M3 用户：确保启用了 MPS 加速
  ```bash
  export PYTORCH_ENABLE_MPS_FALLBACK=1
  ```
- 对于大文件，可以分页处理

## 性能参考

在 MacBook Pro M1/M2 上：
- 文字型 PDF: 约 **2-3秒/页**
- 扫描版 PDF: 约 **5-8秒/页**
- 复杂表格 PDF: 约 **8-10秒/页**

## 技术实现

- **协议**：MCP (Model Context Protocol) stdio transport
- **后端**：直接调用 MinerU CLI (`mineru.cli.client`)
- **模式**：完全本地 pipeline，不依赖任何远程 API
- **语言**：Python 3.10+

## 与官方 MCP 的区别

| 特性 | 本实现 | 官方 mineru-mcp |
|------|--------|-----------------|
| 运行模式 | 直接调用本地 CLI | 需要 API 服务 |
| API Key | ❌ 不需要 | ✅ 需要（云端或本地API） |
| 依赖 | MinerU CLI | FastAPI 服务 + 额外依赖 |
| 启动速度 | ⚡ 快速 | 需要先启动 API 服务 |
| 适用场景 | 本地开发 | 生产环境/多用户 |

## 相关文档

- [MinerU 快速开始](README_CN.md)
- [本地部署详细指南](LOCAL_SETUP.md)
- [MinerU GitHub](https://github.com/opendatalab/MinerU)
- [MCP 协议文档](https://modelcontextprotocol.io/)

## License

MIT License
