#!/bin/bash

# MinerU PDF 解析脚本
# 使用方法: ./parse_pdf.sh <input_pdf> <output_dir>

set -e

# 切换到项目根目录
cd /Users/limo/Documents/GithubRepo/ccblog

# 激活虚拟环境
source .venv/bin/activate

# 获取参数
INPUT_PDF="${1:-}"
OUTPUT_DIR="${2:-./mineru_output}"

if [ -z "$INPUT_PDF" ]; then
    echo "使用方法: $0 <input_pdf> [output_dir]"
    echo ""
    echo "示例:"
    echo "  $0 paper.pdf"
    echo "  $0 paper.pdf ./output"
    exit 1
fi

# 检查文件是否存在
if [ ! -f "$INPUT_PDF" ]; then
    echo "错误: 文件不存在: $INPUT_PDF"
    exit 1
fi

echo "================================================"
echo "MinerU PDF 解析"
echo "================================================"
echo "输入文件: $INPUT_PDF"
echo "输出目录: $OUTPUT_DIR"
echo "================================================"
echo ""

# 解析PDF
python -m mineru.cli.client \
    -p "$INPUT_PDF" \
    -o "$OUTPUT_DIR" \
    -l en \
    -m auto \
    -f true \
    -t true

echo ""
echo "================================================"
echo "✅ 解析完成！"
echo "================================================"
echo "输出位置: $OUTPUT_DIR"
echo ""
echo "查看结果:"
echo "  Markdown: find $OUTPUT_DIR -name '*.md'"
echo "  图片: find $OUTPUT_DIR -name 'images' -type d"
echo "================================================"
