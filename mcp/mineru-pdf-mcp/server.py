#!/usr/bin/env python3
"""
MinerU PDF 解析 MCP Server
直接调用本地 MinerU CLI 进行 PDF 解析
"""

import json
import sys
import subprocess
import os
import shutil
import tempfile
from pathlib import Path
from typing import Any


def log_error(message: str):
    """输出错误日志到 stderr"""
    print(json.dumps({"error": message}), file=sys.stderr, flush=True)


def send_response(response: dict):
    """发送 JSON-RPC 响应"""
    print(json.dumps(response), flush=True)


def parse_pdf(pdf_path: str, output_dir: str = "./output", language: str = "en",
              mode: str = "auto", enable_formula: bool = True, enable_table: bool = True) -> dict:
    """
    调用 MinerU CLI 解析 PDF

    Args:
        pdf_path: PDF 文件路径
        output_dir: 输出目录
        language: 语言 (en, ch, ja, etc.)
        mode: 解析模式 (auto, txt, ocr)
        enable_formula: 启用公式识别
        enable_table: 启用表格识别

    Returns:
        解析结果字典
    """
    try:
        # 确保 PDF 文件存在
        if not os.path.exists(pdf_path):
            return {"success": False, "error": f"PDF 文件不存在: {pdf_path}"}

        # 获取虚拟环境的 Python 路径
        venv_python = "/home/limo/ccblog/.venv/bin/python"

        # 使用临时目录，因为 MinerU 会创建 pdf_name/auto/ 结构
        with tempfile.TemporaryDirectory() as temp_dir:
            # 构建命令，先输出到临时目录
            cmd = [
                venv_python,
                "-m", "mineru.cli.client",
                "-p", pdf_path,
                "-o", temp_dir,
                "-l", language,
                "-m", mode
            ]

            if enable_formula:
                cmd.extend(["-f", "true"])
            if enable_table:
                cmd.extend(["-t", "true"])

            # 执行命令
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                cwd="/home/limo/ccblog"
            )

            if result.returncode == 0:
                # MinerU 会创建 pdf_name/auto/ 结构，我们需要将内容移动到用户指定的目录
                pdf_name = Path(pdf_path).stem
                mineru_output = Path(temp_dir) / pdf_name / "auto"

                if mineru_output.exists():
                    # 将 auto/ 目录下的所有内容移动到用户指定的输出目录
                    target_dir = Path(output_dir)
                    target_dir.mkdir(parents=True, exist_ok=True)

                    # 移动所有文件和文件夹
                    for item in mineru_output.iterdir():
                        target_path = target_dir / item.name
                        # 如果目标已存在，先删除
                        if target_path.exists():
                            if target_path.is_dir():
                                shutil.rmtree(target_path)
                            else:
                                target_path.unlink()
                        # 移动文件/文件夹
                        shutil.move(str(item), str(target_path))

                    # 更新路径
                    md_file = target_dir / f"{pdf_name}.md"
                    images_dir = target_dir / "images"
                else:
                    # 如果 auto 目录不存在，返回错误
                    return {
                        "success": False,
                        "error": f"MinerU 输出目录不存在: {mineru_output}"
                    }

                # 统计图片数量
                image_count = 0
                if images_dir.exists():
                    image_count = len(list(images_dir.glob("*")))

                return {
                    "success": True,
                    "message": "PDF 解析成功",
                    "markdown_file": str(md_file) if md_file.exists() else None,
                    "images_dir": str(images_dir) if images_dir.exists() else None,
                    "image_count": image_count,
                    "output_dir": str(target_dir)
                }
            else:
                return {
                    "success": False,
                    "error": result.stderr or "解析失败",
                    "stdout": result.stdout
                }

    except Exception as e:
        return {"success": False, "error": str(e)}


def handle_request(request: dict) -> dict:
    """处理 MCP 请求"""
    method = request.get("method")
    params = request.get("params", {})
    request_id = request.get("id")

    # Initialize
    if method == "initialize":
        return {
            "jsonrpc": "2.0",
            "id": request_id,
            "result": {
                "protocolVersion": "2024-11-05",
                "capabilities": {
                    "tools": {}
                },
                "serverInfo": {
                    "name": "mineru-pdf",
                    "version": "1.0.0"
                }
            }
        }

    # List tools
    elif method == "tools/list":
        return {
            "jsonrpc": "2.0",
            "id": request_id,
            "result": {
                "tools": [
                    {
                        "name": "parse_pdf",
                        "description": "解析 PDF 文件为 Markdown 并提取图片。支持公式识别、表格识别和多语言 OCR。",
                        "inputSchema": {
                            "type": "object",
                            "properties": {
                                "pdf_path": {
                                    "type": "string",
                                    "description": "PDF 文件的路径（绝对路径或相对路径）"
                                },
                                "output_dir": {
                                    "type": "string",
                                    "description": "输出目录路径（默认: ./output）",
                                    "default": "./output"
                                },
                                "language": {
                                    "type": "string",
                                    "description": "文档语言 (en=英文, ch=中文, ja=日语, ko=韩语等，默认: en)",
                                    "default": "en"
                                },
                                "mode": {
                                    "type": "string",
                                    "enum": ["auto", "txt", "ocr"],
                                    "description": "解析模式: auto=自动, txt=文本型PDF, ocr=扫描版PDF (默认: auto)",
                                    "default": "auto"
                                },
                                "enable_formula": {
                                    "type": "boolean",
                                    "description": "是否启用公式识别（默认: true）",
                                    "default": True
                                },
                                "enable_table": {
                                    "type": "boolean",
                                    "description": "是否启用表格识别（默认: true）",
                                    "default": True
                                }
                            },
                            "required": ["pdf_path"]
                        }
                    }
                ]
            }
        }

    # Call tool
    elif method == "tools/call":
        tool_name = params.get("name")
        arguments = params.get("arguments", {})

        if tool_name == "parse_pdf":
            result = parse_pdf(
                pdf_path=arguments.get("pdf_path"),
                output_dir=arguments.get("output_dir", "./output"),
                language=arguments.get("language", "en"),
                mode=arguments.get("mode", "auto"),
                enable_formula=arguments.get("enable_formula", True),
                enable_table=arguments.get("enable_table", True)
            )

            return {
                "jsonrpc": "2.0",
                "id": request_id,
                "result": {
                    "content": [
                        {
                            "type": "text",
                            "text": json.dumps(result, ensure_ascii=False, indent=2)
                        }
                    ]
                }
            }
        else:
            return {
                "jsonrpc": "2.0",
                "id": request_id,
                "error": {
                    "code": -32601,
                    "message": f"Unknown tool: {tool_name}"
                }
            }

    # notifications/initialized
    elif method == "notifications/initialized":
        # This is a notification, no response needed
        return None

    else:
        return {
            "jsonrpc": "2.0",
            "id": request_id,
            "error": {
                "code": -32601,
                "message": f"Method not found: {method}"
            }
        }


def main():
    """MCP Server 主循环"""
    log_error("MinerU PDF MCP Server 已启动")

    for line in sys.stdin:
        try:
            request = json.loads(line)
            response = handle_request(request)
            if response:  # Only send response if not None (notifications don't need response)
                send_response(response)
        except json.JSONDecodeError as e:
            log_error(f"JSON 解析错误: {e}")
        except Exception as e:
            log_error(f"处理请求时出错: {e}")


if __name__ == "__main__":
    main()
