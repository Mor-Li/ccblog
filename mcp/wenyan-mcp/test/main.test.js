import { describe, it, expect } from "vitest";
import { initMarkdownRenderer, handleFrontMatter, renderMarkdown } from "../src/main.js";
import { readFile, writeFile } from "fs/promises";
import { dirname, join } from "path";
import { fileURLToPath } from "url";

describe("handleFrontMatter", () => {
    it("should parse frontmatter and return title, cover, and body", () => {
        const md = `---
title: 测试标题
cover: https://example.com/image.jpg
---
# 正文

Hello world!`;

        const result = handleFrontMatter(md);

        expect(result.title).toBe("测试标题");
        expect(result.cover).toBe("https://example.com/image.jpg");
        expect(result.body).toContain("# 正文");
    });
});

describe("renderMarkdown", () => {
    it("should convert markdown to HTML", async () => {
        const __dirname = dirname(fileURLToPath(import.meta.url));
        const path = join(__dirname, "test.md");
        const md = await readFile(path, "utf8");
        initMarkdownRenderer();
        const html = await renderMarkdown(md, "phycat");

        // console.log(html);

        // const outputPath = join(__dirname, "out.txt");
        // await writeFile(outputPath, html, "utf8");
        expect(html).toContain("</h2>");
    });
});
