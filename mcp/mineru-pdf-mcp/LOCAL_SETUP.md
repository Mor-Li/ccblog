# MinerU 本地 PDF 解析完全指南 🚀

## ✅ 优势：完全本地运行，无需 API Key！

MinerU 支持完全本地运行，不需要注册账号或获取 API key，所有处理都在你的本地机器上完成。

## 📦 已完成的安装

1. ✅ MinerU 核心包和 pipeline 后端已安装
2. ✅ 所有依赖（PyTorch, Transformers 等）已安装
3. ✅ 配置已设置为本地模式

## 🎯 两种使用方式

### 方式一：直接使用 MinerU CLI（推荐用于简单场景）

```bash
# 激活环境
cd /Users/limo/Documents/GithubRepo/ccblog
source .venv/bin/activate

# 首次使用：下载模型（只需执行一次）
python -m mineru.cli.models_download

# 解析 PDF
python -m mineru.cli.client -i /path/to/document.pdf -o ./output

# 批量解析
python -m mineru.cli.client -i /path/to/pdfs -o ./output
```

### 方式二：通过 MCP 服务器（推荐用于 Claude Code 集成）

#### Step 1: 启动本地 MinerU API 服务

```bash
cd /Users/limo/Documents/GithubRepo/ccblog
source .venv/bin/activate

# 启动本地API服务
python -m mineru.cli.fast_api --host 0.0.0.0 --port 8888
```

#### Step 2: 配置 Claude Code MCP

在另一个终端中，添加 MCP 配置：

```bash
claude mcp add mineru-pdf-local \
  --command /Users/limo/Documents/GithubRepo/ccblog/.venv/bin/python \
  --args "-m" --args "mineru.cli" \
  --cwd /Users/limo/Documents/GithubRepo/ccblog/mcp/mineru-pdf-mcp \
  --env USE_LOCAL_API=true \
  --env LOCAL_MINERU_API_BASE=http://localhost:8888 \
  --env OUTPUT_DIR=./downloads
```

#### Step 3: 重启 Claude Code

重启后即可在 Claude Code 中使用本地 PDF 解析功能！

## 📝 使用示例

### CLI 方式

```bash
# 基本用法
python -m mineru.cli.client -i paper.pdf -o ./output

# 启用 OCR（用于扫描版 PDF）
python -m mineru.cli.client -i scan.pdf -o ./output --enable-ocr

# 指定语言
python -m mineru.cli.client -i paper.pdf -o ./output --lang en

# 只处理特定页面
python -m mineru.cli.client -i paper.pdf -o ./output --pages 1-5

# 批量处理
python -m mineru.cli.client -i ./pdfs_folder -o ./output
```

### Claude Code 方式

在 Claude Code 中直接说：

```
帮我解析这个PDF：/path/to/document.pdf
```

或

```
把这个文件夹里的所有PDF都转成Markdown：/path/to/pdfs/
```

## 🔧 模型下载（首次使用必需）

MinerU 使用深度学习模型进行 PDF 解析，首次使用需要下载模型：

```bash
source .venv/bin/activate

# 下载所有模型（约 2-3GB）
python -m mineru.cli.models_download

# 或者只下载基础模型
python -m mineru.cli.models_download --models layout mfd mfr ocr
```

模型会自动下载到 `~/.cache/huggingface/` 或 `~/.cache/modelscope/`

## 📁 输出结构

```
output/
└── document/
    ├── auto/               # 自动提取的内容
    │   ├── content_list.json
    │   ├── middle.json
    │   └── model.json
    ├── images/             # 提取的图片
    │   ├── image_001.png
    │   ├── image_002.png
    │   └── ...
    └── document.md         # 最终的 Markdown 文件
```

## ⚙️ 高级配置

### 性能优化

根据你的 Mac 配置调整：

```bash
# M1/M2/M3 Mac (使用 MPS 加速)
export PYTORCH_ENABLE_MPS_FALLBACK=1

# 调整并发数
export MINERU_CONCURRENT_TASKS=4
```

### OCR 语言

MinerU 支持多种语言的 OCR：

- `ch` - 中文
- `en` - 英文
- `ja` - 日语
- `ko` - 韩语
- `ar` - 阿拉伯语
- `de` - 德语
- `fr` - 法语
- `ru` - 俄语

## 💡 提示和技巧

### 1. 处理速度

- **CPU模式**: 处理1页约需 5-10 秒
- **GPU模式**: 如果有 GPU，速度可提升 3-5 倍

### 2. 内存使用

- 基础模型需要约 2GB RAM
- 处理复杂 PDF 可能需要更多内存

### 3. 批量处理

对于大量 PDF，建议：
```bash
# 逐个处理，避免内存溢出
for pdf in pdfs/*.pdf; do
  python -m mineru.cli.client -i "$pdf" -o ./output
done
```

## 🐛 故障排除

### 问题1: 模型下载失败

```bash
# 使用国内镜像
export HF_ENDPOINT=https://hf-mirror.com
python -m mineru.cli.models_download
```

### 问题2: 内存不足

```bash
# 减少并发
export MINERU_CONCURRENT_TASKS=1
```

### 问题3: PyTorch MPS 错误 (Mac M1/M2/M3)

```bash
# 禁用 MPS，使用 CPU
export PYTORCH_ENABLE_MPS_FALLBACK=1
# 或完全禁用 MPS
export PYTORCH_MPS_AVAILABLE=0
```

## 🎓 学习资源

- [MinerU GitHub](https://github.com/opendatalab/MinerU)
- [官方文档](https://opendatalab.github.io/MinerU/)
- [模型说明](https://huggingface.co/opendatalab)

## 🆚 本地模式 vs 云端 API

| 特性 | 本地模式 | 云端 API |
|------|---------|----------|
| 需要网络 | ❌ 否 | ✅ 是 |
| 需要 API Key | ❌ 否 | ✅ 是 |
| 处理速度 | 取决于本地硬件 | 通常更快 |
| 隐私性 | ✅ 完全本地 | ⚠️ 上传到云端 |
| 费用 | ✅ 完全免费 | 💰 可能收费 |
| 模型下载 | ✅ 需要（一次性） | ❌ 不需要 |

## 📌 总结

本地模式的 MinerU：
- ✅ **无需注册账号**
- ✅ **无需 API key**
- ✅ **完全免费**
- ✅ **数据隐私保护**
- ✅ **离线可用**

唯一的代价是：
- 首次使用需要下载模型（约 2-3GB）
- 处理速度取决于你的硬件配置

对于博客写作和学术研究来说，本地模式完全够用！🎉
