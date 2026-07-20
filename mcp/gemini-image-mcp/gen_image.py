#!/usr/bin/env python3
"""生成配图：调用 OpenAI 兼容接口的图像模型（默认 Gemini 3 Pro Image，即 Nano Banana 2 / Pro）。

纯 stdlib，任何 python3 直接跑，不依赖 openai / requests。
endpoint 和 key 都从环境变量或同目录 .env 读取，脚本本身不含任何具体地址或密钥。

用法:
    python3 gen_image.py -p "画面描述" -o out.png
    python3 gen_image.py -p "..." -o out.png --model gemini-2.5-flash-image

需要提供（环境变量，或写进同目录 .env，每行一条 KEY=VALUE）:
    IMAGE_BASE_URL   OpenAI 兼容 endpoint，形如 https://<host>/v1
                     （别名: LITELLM_BASE_URL / OPENAI_BASE_URL）
    IMAGE_API_KEY    对应 API key
                     （别名: LITELLM_API_KEY / OPENAI_API_KEY / ANTHROPIC_AUTH_TOKEN）

stdout 只打印最终图片路径，方便管道 / Read；进度和报错走 stderr。
"""
from __future__ import annotations

import argparse
import base64
import json
import os
import re
import struct
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path

HERE = Path(__file__).resolve().parent
DEFAULT_MODEL = "gemini-3-pro-image-preview"

BASE_URL_VARS = ["IMAGE_BASE_URL", "LITELLM_BASE_URL", "OPENAI_BASE_URL"]
API_KEY_VARS = ["IMAGE_API_KEY", "LITELLM_API_KEY", "OPENAI_API_KEY", "ANTHROPIC_AUTH_TOKEN"]


# ---------------------------------------------------------------- 配置查找
def _from_envfile(names: list[str]) -> str | None:
    envfile = HERE / ".env"
    if not envfile.exists():
        return None
    for line in envfile.read_text().splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        k, v = line.split("=", 1)
        if k.strip() in names:
            return v.strip().strip("'\"")
    return None


def _from_rc(names: list[str]) -> str | None:
    """Claude Code 的 Bash 是非交互 shell，不 source rc 文件；主动提取并缓存进 .env。"""
    envfile = HERE / ".env"
    for rc in ("~/.zshrc", "~/.bashrc"):
        p = Path(rc).expanduser()
        if not p.exists():
            continue
        m = re.search(rf"^export\s+({'|'.join(names)})=['\"]?([^'\"\n]+)", p.read_text(), re.M)
        if m:
            var, val = m.group(1), m.group(2).strip()
            try:  # 缓存进 .env，之后没有 shell 环境也能跑
                cached = envfile.read_text() if envfile.exists() else ""
                if f"{var}=" not in cached:
                    envfile.write_text(cached + f"{var}={val}\n")
                    envfile.chmod(0o600)
            except OSError:
                pass
            return val
    return None


def find_conf(names: list[str], label: str) -> str:
    for var in names:
        if v := os.environ.get(var):
            return v.strip()
    if v := _from_envfile(names):
        return v
    if v := _from_rc(names):
        return v
    sys.exit(f"❌ 找不到 {label}（查过环境变量 {'/'.join(names)}、同目录 .env、~/.zshrc）。"
             f"请 export 对应变量，或写进 {HERE / '.env'}")


# ---------------------------------------------------------------- 工具
def dims(raw: bytes) -> str:
    """读图片头拿分辨率，不依赖 PIL。"""
    if raw[:8] == b"\x89PNG\r\n\x1a\n":
        w, h = struct.unpack(">II", raw[16:24])
        return f"{w}x{h}"
    if raw[:2] == b"\xff\xd8":
        i = 2
        while i < len(raw) - 9:
            if raw[i] != 0xFF:
                i += 1
                continue
            if raw[i + 1] in (0xC0, 0xC1, 0xC2, 0xC3):
                h, w = struct.unpack(">HH", raw[i + 5:i + 9])
                return f"{w}x{h}"
            i += 2 + struct.unpack(">H", raw[i + 2:i + 4])[0]
    return "未知"


def post(url: str, payload: dict, key: str, timeout: int) -> dict:
    req = urllib.request.Request(
        url,
        data=json.dumps(payload).encode(),
        headers={"Authorization": f"Bearer {key}", "Content-Type": "application/json"},
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=timeout) as r:
            return json.loads(r.read())
    except urllib.error.HTTPError as e:
        body = e.read().decode(errors="replace")
        try:
            msg = json.loads(body).get("error", {}).get("message", body)
        except Exception:
            msg = body
        raise RuntimeError(f"HTTP {e.code}: {msg[:400]}") from None


def extract_image(data: dict) -> tuple[str | None, str | None]:
    """抠 base64 图：优先 message.images[].image_url.url（OpenAI 兼容多模态），
    fallback 到 content 字符串里的 markdown data-uri。返回 (格式, base64)。"""
    for ch in data.get("choices") or []:
        msg = ch.get("message", {}) or {}
        for im in msg.get("images") or []:
            url = (im.get("image_url") or {}).get("url", "")
            m = re.match(r"^data:image/(png|jpeg|jpg|webp);base64,(.+)$", url, re.S)
            if m:
                return m.group(1), m.group(2)
        c = msg.get("content")
        if isinstance(c, str):
            m = re.search(r"!\[.*?\]\(data:image/(png|jpeg|jpg);base64,([^)]+)\)", c)
            if m:
                return m.group(1), m.group(2)
    return None, None


# ---------------------------------------------------------------- 主流程
def main() -> None:
    ap = argparse.ArgumentParser(
        description="生成配图（OpenAI 兼容图像模型，默认 Gemini 3 Pro Image / Nano Banana 2）",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="示例:\n  python3 %(prog)s -p '技术架构图：Generator 指向 Reviser' -o fig.png\n",
    )
    ap.add_argument("-p", "--prompt", required=True, help="画面描述")
    ap.add_argument("-o", "--output", required=True, type=Path, help="输出图片路径")
    ap.add_argument("--model", default=os.environ.get("IMAGE_MODEL", DEFAULT_MODEL),
                    help=f"模型名，默认 {DEFAULT_MODEL}")
    ap.add_argument("--timeout", type=int, default=300, help="秒，默认 300")
    ap.add_argument("--retries", type=int, default=2, help="失败重试次数")
    args = ap.parse_args()

    base = find_conf(BASE_URL_VARS, "endpoint (IMAGE_BASE_URL)").rstrip("/")
    key = find_conf(API_KEY_VARS, "API key (IMAGE_API_KEY)")
    url = base + "/chat/completions"
    payload = {"model": args.model, "messages": [{"role": "user", "content": args.prompt}]}

    print(f"[生图] {args.model} @ {base}", file=sys.stderr)
    last = None
    t0 = time.time()
    for attempt in range(args.retries + 1):
        t0 = time.time()
        try:
            data = post(url, payload, key, args.timeout)
            break
        except Exception as exc:  # noqa: BLE001
            last = exc
            if "HTTP 4" in str(exc) and "429" not in str(exc):
                sys.exit(f"❌ 请求被拒: {exc}")
            if attempt < args.retries:
                wait = 5 * (attempt + 1)
                print(f"  第{attempt + 1}次失败({str(exc)[:80]})，{wait}s 后重试", file=sys.stderr)
                time.sleep(wait)
    else:
        sys.exit(f"❌ 重试耗尽: {last}")

    fmt, b64 = extract_image(data)
    if not b64 or not fmt:
        sys.exit(f"❌ 响应里没有图片: {json.dumps(data, ensure_ascii=False)[:400]}")
    raw = base64.b64decode(b64)
    if len(raw) < 100:
        sys.exit(f"❌ 图太小（{len(raw)} bytes），疑似生成失败")

    ext = "jpg" if fmt == "jpeg" else fmt
    out = args.output
    if out.suffix.lower().lstrip(".") not in ("png", "jpg", "jpeg"):
        out = out.with_suffix(f".{ext}")
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_bytes(raw)
    print(f"  ✅ {out}  {dims(raw)}  {len(raw) / 1024:.0f}KB  耗时{time.time() - t0:.0f}s", file=sys.stderr)
    print(str(out))  # stdout 只输出路径


if __name__ == "__main__":
    main()
