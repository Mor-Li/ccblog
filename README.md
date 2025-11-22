# ccblog - 通过 Claude Code 自动发布博客到微信公众号

使用 wenyan-mcp 服务，通过 Claude Code 自动读取本地 Markdown 文件并发布到微信公众号。

## 工作原理

```
本地 MD 文件 → Claude Code (MCP Client) → wenyan-mcp (MCP Server) → 微信公众号
```

## 快速开始

### 1. 编译 wenyan-mcp（已完成 ✅）

```bash
cd mcp/wenyan-mcp
npm install
npx tsc -b
```

### 2. 配置 Claude Code MCP

将以下配置添加到你的 Claude Code MCP 配置文件中：

**macOS/Linux**: `~/.claude/claude_desktop_config.json`
**Windows**: `%APPDATA%\Claude\claude_desktop_config.json`

```json
{
  "mcpServers": {
    "wenyan-mcp": {
      "name": "公众号助手",
      "command": "node",
      "args": [
        "/Users/limo/Documents/GithubRepo/ccblog/mcp/wenyan-mcp/dist/index.js"
      ],
      "env": {
        "WECHAT_APP_ID": "你的微信公众号 App ID",
        "WECHAT_APP_SECRET": "你的微信公众号 App Secret"
      }
    }
  }
}
```

### 3. 获取微信公众号认证信息

1. 登录微信公众平台：https://mp.weixin.qq.com
2. 进入「设置与开发」→「基本配置」
3. 获取开发者ID(AppID) 和 开发者密码(AppSecret)
4. 配置 IP 白名单（必须！）

详细配置说明：https://yuzhi.tech/docs/wenyan/upload

### 4. 重启 Claude Code

配置完成后重启 Claude Code，让 MCP 服务生效。

### 5. 使用 Claude Code 发布文章

现在你可以直接在 Claude Code 中这样操作：

```
帮我把 blog_pydantic_model.md 这个文件发布到微信公众号，使用 rainbow 主题
```

Claude Code 会：
1. 读取你的 MD 文件
2. 调用 wenyan-mcp 进行排版
3. 自动上传图片
4. 发布到公众号草稿箱

## Markdown 文件格式要求

在你的 MD 文件开头添加 frontmatter：

```markdown
---
title: 文章标题
cover: /path/to/cover/image.jpg
---

你的文章内容...
```

- `title`: 必填，文章标题
- `cover`: 可选，封面图（本地路径或网络 URL）
  - 如果正文有图片可省略
  - 无图片时必须提供

## 可用主题

wenyan-mcp 提供 8 种精美主题：

- `default` - 默认主题
- `orangeheart` - Orange Heart（橙心）
- `rainbow` - Rainbow（彩虹）
- `lapis` - Lapis（青金石）
- `pie` - Pie（派）
- `maize` - Maize（玉米）
- `purple` - Purple（紫色）
- `phycat` - 物理猫-薄荷

主题预览：https://yuzhi.tech/docs/wenyan/theme

## 示例文章

本仓库包含一个示例文章：`blog_pydantic_model.md`

你可以直接在 Claude Code 中说：

```
帮我看看 blog_pydantic_model.md 文件，然后发布到微信公众号
```

## MCP 提供的工具

wenyan-mcp 提供了两个工具：

1. **`list_themes`** - 列出所有可用主题
   ```
   列出公众号发布的所有可用主题
   ```

2. **`publish_article`** - 发布文章到公众号
   - 参数：
     - `content`: Markdown 内容（包含 frontmatter）
     - `theme_id`: 主题 ID（可选，默认 default）

## 使用示例

### 简单发布
```
帮我把 my_article.md 发布到公众号
```

Claude Code 会：
1. 读取你的 MD 文件
2. 调用 wenyan-mcp 进行排版
3. 自动上传图片
4. 发布到公众号草稿箱

### 指定主题发布
```
把 blog_pydantic_model.md 用 rainbow 主题发布到公众号
```

### 查看可用主题
```
公众号助手有哪些主题可以用？
```

### 批量发布
```
帮我把 posts 目录下所有 .md 文件都发布到公众号，使用 lapis 主题
```

### 修改后重新发布
```
帮我修改 article.md 的标题，然后重新发布到公众号
```

## 图片处理

支持以下图片路径：

1. **本地绝对路径**：`/Users/limo/Pictures/image.jpg`
2. **本地相对路径**：`./images/photo.png`
3. **网络 URL**：`https://example.com/image.jpg`

所有图片会自动上传到微信公众号素材库。

## 故障排除

### MCP 服务未连接

1. 检查配置文件路径是否正确
2. 确认 wenyan-mcp 已编译（存在 `mcp/wenyan-mcp/dist/index.js`）
3. 重启 Claude Code

### 发布失败

常见原因：

1. **IP 白名单未配置**（最常见！）
   - 登录微信公众平台：https://mp.weixin.qq.com
   - 进入「设置与开发」→「基本配置」→「IP白名单」
   - 添加你的服务器/本机 IP 地址
   - 查看本机公网 IP：`curl ifconfig.me`
   - 详细说明：https://yuzhi.tech/docs/wenyan/upload

2. **认证错误**：检查 App ID 和 App Secret 是否正确

3. **frontmatter 格式错误**：检查 YAML 格式是否正确

4. **图片路径错误**：确认文件存在且路径正确

### 查看 MCP 日志

在 Claude Code 对话中，MCP 的错误信息会直接显示。

## 高级配置

### 使用 Docker 运行 MCP

如果你想在服务器上运行 wenyan-mcp，可以使用 Docker：

```json
{
  "mcpServers": {
    "wenyan-mcp": {
      "name": "公众号助手",
      "command": "docker",
      "args": [
        "run",
        "--rm",
        "-i",
        "-v", "/Users/limo/Pictures:/mnt/host-downloads",
        "-e", "WECHAT_APP_ID=your_app_id",
        "-e", "WECHAT_APP_SECRET=your_app_secret",
        "-e", "HOST_IMAGE_PATH=/Users/limo/Pictures",
        "caol64/wenyan-mcp"
      ]
    }
  }
}
```

### 全局安装 wenyan-mcp

如果你想在任何地方使用：

```bash
npm install -g @wenyan-md/mcp
```

然后配置文件简化为：

```json
{
  "mcpServers": {
    "wenyan-mcp": {
      "name": "公众号助手",
      "command": "wenyan-mcp",
      "env": {
        "WECHAT_APP_ID": "your_app_id",
        "WECHAT_APP_SECRET": "your_app_secret"
      }
    }
  }
}
```

## 项目结构

```
ccblog/
├── blog/                       # 博客文章目录
├── mcp/                        # MCP 服务目录
│   ├── wenyan-mcp/            # 文颜 MCP 服务（微信公众号发布）
│   │   ├── src/               # 源代码
│   │   ├── dist/              # 编译输出
│   │   └── package.json
│   ├── xiaohongshu-mcp/       # 小红书 MCP 服务
│   └── generate-image-mcp/    # 图片生成 MCP 服务
├── scripts/                    # Python 工具脚本
│   ├── download_arxiv_images.py
│   ├── extract_arxiv_images.py
│   ├── scrape_arxiv_images.py
│   └── scrape_arxiv_playwright.py
└── mcp-config-example.json     # MCP 配置示例
```

## 相关资源

- [文颜官网](https://yuzhi.tech/wenyan)
- [文颜文档](https://yuzhi.tech/docs/wenyan/theme)
- [wenyan-mcp GitHub](https://github.com/caol64/wenyan-mcp)
- [Claude Code 文档](https://docs.anthropic.com/claude-code)
- [MCP 协议文档](https://modelcontextprotocol.io/)

## License

Apache License Version 2.0

## 致谢

- [文颜 MCP](https://github.com/caol64/wenyan-mcp) - 微信公众号排版工具
- [小红书 MCP](https://github.com/xpzouying/xiaohongshu-mcp) - 小红书发布工具
