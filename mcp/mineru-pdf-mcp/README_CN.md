# MinerU 本地 PDF 解析 - 快速开始 🚀

## 🎉 好消息：完全本地运行，无需 API Key！

已经为你配置好了 MinerU 本地解析环境，可以直接使用，无需注册账号或API key。

## ⚡ 快速使用（三步搞定）

### Step 1: 下载模型（首次使用，约2-3GB）

```bash
cd /Users/limo/Documents/GithubRepo/ccblog
source .venv/bin/activate
python -m mineru.cli.models_download
```

### Step 2: 解析 PDF

```bash
# 解析单个PDF
python -m mineru.cli.client -p /path/to/paper.pdf -o ./output

# 解析文件夹中的所有PDF
python -m mineru.cli.client -p /path/to/pdfs/ -o ./output
```

### Step 3: 查看结果

转换后的 Markdown 和图片都在 `./output` 目录中！

## 📝 常用命令

```bash
# 激活环境（每次使用前）
cd /Users/limo/Documents/GithubRepo/ccblog && source .venv/bin/activate

# 基本解析
python -m mineru.cli.client -p document.pdf -o ./output

# 启用OCR（扫描版PDF）
python -m mineru.cli.client -p scan.pdf -o ./output -m ocr

# 指定语言（提高OCR准确度）
python -m mineru.cli.client -p paper.pdf -o ./output -l en

# 只解析部分页面（从0开始计数）
python -m mineru.cli.client -p paper.pdf -o ./output -s 0 -e 5

# 批量处理
for pdf in *.pdf; do
  python -m mineru.cli.client -p "$pdf" -o ./output
done
```

## 📁 输出结构

```
output/
└── paper/
    ├── auto/
    │   ├── content_list.json  # 结构化内容
    │   ├── middle.json        # 中间结果
    │   └── model.json         # 模型输出
    ├── images/                # 提取的图片
    │   ├── image_001.png
    │   ├── image_002.png
    │   └── ...
    └── paper.md              # 最终Markdown文件
```

## 🌍 支持的语言

- `ch` - 中文（默认）
- `en` - 英文
- `japan` - 日语
- `korean` - 韩语
- `arabic` - 阿拉伯语
- `devanagari` - 天城文
- 更多语言请参考 `--help`

## ⚙️ 解析模式

```bash
# 自动模式（推荐）
python -m mineru.cli.client -p file.pdf -o ./output -m auto

# 文本模式（文字型PDF，速度最快）
python -m mineru.cli.client -p file.pdf -o ./output -m txt

# OCR模式（扫描版PDF）
python -m mineru.cli.client -p file.pdf -o ./output -m ocr
```

## 💡 使用技巧

### 1. 批量处理脚本

创建 `batch_convert.sh`:
```bash
#!/bin/bash
cd /Users/limo/Documents/GithubRepo/ccblog
source .venv/bin/activate

for pdf in "$1"/*.pdf; do
  echo "Processing: $pdf"
  python -m mineru.cli.client -p "$pdf" -o "$2"
done
```

使用：
```bash
chmod +x batch_convert.sh
./batch_convert.sh /path/to/pdfs /path/to/output
```

### 2. 处理学术论文

```bash
# 英文论文，启用公式和表格解析
python -m mineru.cli.client \
  -p paper.pdf \
  -o ./output \
  -l en \
  -m auto \
  -f true \
  -t true
```

### 3. 处理扫描版书籍

```bash
# 中文扫描书，使用OCR
python -m mineru.cli.client \
  -p book.pdf \
  -o ./output \
  -l ch \
  -m ocr
```

## 🔧 性能优化

### Mac M1/M2/M3 用户

```bash
# 启用 MPS 加速
export PYTORCH_ENABLE_MPS_FALLBACK=1

# 然后运行解析命令
python -m mineru.cli.client -p file.pdf -o ./output
```

### 内存优化

```bash
# 减少并发任务
export MINERU_CONCURRENT_TASKS=1

# 处理大文件
python -m mineru.cli.client -p large.pdf -o ./output
```

## 🐛 常见问题

### Q: 模型下载慢或失败？

```bash
# 使用国内镜像
export HF_ENDPOINT=https://hf-mirror.com
python -m mineru.cli.models_download
```

### Q: 内存不足？

```bash
# 减少并发
export MINERU_CONCURRENT_TASKS=1
# 或者分页处理
python -m mineru.cli.client -p file.pdf -o ./output -s 0 -e 10
```

### Q: OCR识别不准确？

```bash
# 1. 指定正确的语言
python -m mineru.cli.client -p file.pdf -o ./output -l en

# 2. 确保使用OCR模式
python -m mineru.cli.client -p file.pdf -o ./output -m ocr
```

## 📊 性能参考

在 MacBook Pro M1/M2 上：
- 文字型PDF: 约 **2-3秒/页**
- 扫描版PDF: 约 **5-8秒/页**
- 复杂表格PDF: 约 **8-10秒/页**

## 🎯 使用场景

### 1. 学术论文

```bash
# 英文论文 + 公式 + 表格
python -m mineru.cli.client -p paper.pdf -o ./papers -l en
```

### 2. 技术文档

```bash
# 中文技术文档
python -m mineru.cli.client -p docs.pdf -o ./docs -l ch
```

### 3. 扫描书籍

```bash
# OCR + 中文
python -m mineru.cli.client -p book.pdf -o ./books -m ocr -l ch
```

### 4. 批量转换

```bash
# 整个文件夹
python -m mineru.cli.client -p ./pdf_folder -o ./output
```

## 📚 进阶使用

查看完整文档：
- [本地部署详细指南](LOCAL_SETUP.md)
- [MinerU GitHub](https://github.com/opendatalab/MinerU)
- [官方文档](https://opendatalab.github.io/MinerU/)

## ✅ 检查清单

安装完成后，确认以下步骤：

- [ ] 虚拟环境已激活（`source .venv/bin/activate`）
- [ ] 模型已下载（`python -m mineru.cli.models_download`）
- [ ] 可以运行 `python -m mineru.cli.client --help`
- [ ] 测试解析一个简单PDF成功

全部完成后，就可以开始使用了！🎉

---

**提示**: 如果遇到问题，查看 [LOCAL_SETUP.md](LOCAL_SETUP.md) 获取详细的故障排除指南。
