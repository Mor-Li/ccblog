# 微信公众号文章发布注意事项

## 必需的 Frontmatter

```markdown
---
title: 文章标题
cover: /绝对/路径/到/封面图.png
---
```

## 支持的格式

- **数学公式**：LaTeX 语法（`$...$` 和 `$$...$$`）
- **标准 Markdown**：标题、列表、粗体、斜体、引用等
- **图片**：相对或绝对路径
- **代码块**：` ```language `

## 不支持

- **Markdown 锚点链接**：`[文本](#anchor)` 会导致发布失败（错误码 45166）
- **WebP 图片格式**：会导致发布失败（错误码 40113）

## 常见错误及解决方案

### system error：图片过大

**问题原因**：微信公众号 API 接口上传图片限制为 **1MB 以下**（手动后台上传是10MB，但 wenyan-mcp 走API）

**官方限制**：
- 公众号后台手动上传：10MB
- **API 接口上传：1MB**（wenyan-mcp 使用此方式）

参考：[微信官方文档 - 上传图文消息内的图片获取URL](https://developers.weixin.qq.com/doc/offiaccount/Asset_Management/Adding_Permanent_Assets)

**症状**：
- 错误信息：`上传失败，错误码：-1，错误信息：system error`
- 多次重试仍然失败

**诊断方法**：

```bash
# 检查图片大小，找出超过 1MB 的图片
find . \( -name "*.png" -o -name "*.jpg" \) -size +1M -exec ls -lh {} \;
```

**解决方案**：

使用 ImageMagick 压缩大图：

```bash
# 单张图片压缩（限制最大尺寸 2000px，质量 85%）
convert input.png -resize 2000x2000\> -quality 85 output.png

# 批量压缩超过 1MB 的图片
for f in *.png; do
  size=$(stat -c%s "$f")
  if [ "$size" -gt 1000000 ]; then
    convert "$f" -resize 2000x2000\> -quality 85 "${f%.png}_compressed.png"
    mv "$f" "${f%.png}_original.png"
    mv "${f%.png}_compressed.png" "$f"
    echo "压缩: $f"
  fi
done
```

### 错误码 45166：内容验证失败

错误码 45166 (`invalid content`) 有多种触发原因：

#### 原因 1：Markdown 锚点链接

发布前删除所有目录中的锚点链接：

```markdown
<!-- 会失败 -->
- [章节一](#章节一)

<!-- 可以 -->
- 章节一：介绍
```

#### 原因 2：无效的微信公众号链接

文章中引用的微信公众号文章链接如果不存在或已失效，会导致发布失败：

```markdown
<!-- 会失败 - 链接不存在 -->
在[上一篇文章](https://mp.weixin.qq.com/s/不存在的ID)中...

<!-- 可以 - 移除无效链接 -->
在上一篇文章中...
```

**诊断方法**：如果遇到 45166 错误，检查文章中所有 `mp.weixin.qq.com` 链接是否有效

### 错误码 40113：unsupported file type

**问题原因**：图片文件的实际格式与扩展名不符，最常见的是 WebP 图片被命名为 `.png`

**症状**：
- 错误信息：`上传失败，错误码：40113，错误信息：unsupported file type`
- 文章内容正常，但包含的图片无法上传

**微信公众号支持的图片格式**：
- JPG/JPEG、PNG、GIF、BMP
- 不支持：WebP、SVG

**诊断方法**：

```bash
file /path/to/image.png

# 真正的 PNG
image.png: PNG image data, 1197 x 291, 8-bit/color RGBA, non-interlaced

# 伪装成 PNG 的 WebP
image.png: RIFF (little-endian) data, Web/P image, VP8 encoding, 960x540
```

**解决方案**：

```bash
# 转换 WebP 为 PNG
convert input.webp output.png

# 批量检查并转换
for img in *.png; do
  if file "$img" | grep -q "Web/P"; then
    echo "转换 WebP: $img"
    convert "$img" "${img%.png}_real.png"
    mv "$img" "${img%.png}_webp_backup"
    mv "${img%.png}_real.png" "$img"
  fi
done
```

## 发布前检查清单

```bash
#!/bin/bash
# 发布前检查脚本

echo "=== 检查图片大小 ==="
find . -name "*.png" -o -name "*.jpg" | while read f; do
  size=$(stat -c%s "$f")
  if [ "$size" -gt 1000000 ]; then
    echo "警告: $f 过大 ($(echo "scale=1; $size/1024/1024" | bc)MB)"
  fi
done

echo "=== 检查图片格式 ==="
for img in *.png; do
  [ -f "$img" ] && file "$img" | grep -q "Web/P" && echo "警告: $img 是 WebP 格式"
done

echo "=== 检查锚点链接 ==="
grep -n '\](#' *.md && echo "警告: 发现锚点链接"

echo "=== 检查完成 ==="
```
