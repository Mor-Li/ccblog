#!/usr/bin/env node

/**
 * This is a template MCP server that implements a simple notes system.
 * It demonstrates core MCP concepts like resources and tools by allowing:
 * - Listing notes as resources
 * - Reading individual notes
 * - Creating new notes via a tool
 * - Summarizing all notes via a prompt
 */

import { Server } from "@modelcontextprotocol/sdk/server/index.js";
import { StdioServerTransport } from "@modelcontextprotocol/sdk/server/stdio.js";
import {
    CallToolRequestSchema,
    ListToolsRequestSchema,
} from "@modelcontextprotocol/sdk/types.js";
import { getGzhContent } from "@wenyan-md/core/wrapper";
import { publishToDraft } from "./publish.js";  // Use custom publish module with axios + form-data
import { themes, Theme } from "@wenyan-md/core/theme";
import * as fs from "fs";
import * as path from "path";

/**
 * Convert relative image paths in markdown to absolute paths
 * @param content - The markdown content
 * @param baseDir - The directory containing the markdown file
 * @returns The markdown content with absolute image paths
 */
function resolveImagePaths(content: string, baseDir: string): string {
    // Match markdown image syntax: ![alt](path) and ![alt](path "title")
    // Also match HTML img tags: <img src="path" />
    // Also match frontmatter cover field: cover: path
    return content
        // Resolve frontmatter cover path
        .replace(/^(cover:\s*)([^\s\r\n]+)/gm, (match, prefix, coverPath) => {
            // Skip if already absolute path (starts with / or http:// or https://)
            if (coverPath.startsWith('/') || coverPath.startsWith('http://') || coverPath.startsWith('https://')) {
                return match;
            }
            // Resolve relative path to absolute path
            const absolutePath = path.resolve(baseDir, coverPath);
            return `${prefix}${absolutePath}`;
        })
        // Resolve markdown image syntax
        .replace(/!\[([^\]]*)\]\(([^)"\s]+)(?:\s+"[^"]*")?\)/g, (match, alt, imagePath) => {
            // Skip if already absolute path (starts with / or http:// or https://)
            if (imagePath.startsWith('/') || imagePath.startsWith('http://') || imagePath.startsWith('https://')) {
                return match;
            }
            // Resolve relative path to absolute path
            const absolutePath = path.resolve(baseDir, imagePath);
            return `![${alt}](${absolutePath})`;
        })
        // Resolve HTML img tags
        .replace(/<img\s+([^>]*?)src=["']([^"']+)["']([^>]*?)>/gi, (match, before, imagePath, after) => {
            // Skip if already absolute path
            if (imagePath.startsWith('/') || imagePath.startsWith('http://') || imagePath.startsWith('https://')) {
                return match;
            }
            // Resolve relative path to absolute path
            const absolutePath = path.resolve(baseDir, imagePath);
            return `<img ${before}src="${absolutePath}"${after}>`;
        });
}

/**
 * Create an MCP server with capabilities for resources (to list/read notes),
 * tools (to create new notes), and prompts (to summarize notes).
 */
const server = new Server(
    {
        name: "wenyan-mcp",
        version: "0.1.0",
    },
    {
        capabilities: {
            resources: {},
            tools: {},
            prompts: {},
            // logging: {},
        },
    }
);

/**
 * Handler that lists available tools.
 * Exposes a single "publish_article" tool that lets clients publish new article.
 */
server.setRequestHandler(ListToolsRequestSchema, async () => {
    return {
        tools: [
            {
                name: "publish_article",
                description:
                    "Format a Markdown article using a selected theme and publish it to '微信公众号'.",
                inputSchema: {
                    type: "object",
                    properties: {
                        content: {
                            type: "string",
                            description: "The original Markdown content to publish, preserving its frontmatter (if present). Use this OR file_path, not both.",
                        },
                        file_path: {
                            type: "string",
                            description: "Path to a local Markdown file to publish. Use this OR content, not both. The file will be read and published directly.",
                        },
                        theme_id: {
                            type: "string",
                            description:
                                "ID of the theme to use (e.g., default, orangeheart, rainbow, lapis, pie, maize, purple, phycat).",
                        },
                    },
                    required: [],
                },
            },
            {
                name: "list_themes",
                description:
                    "List the themes compatible with the 'publish_article' tool to publish an article to '微信公众号'.",
                inputSchema: {
                    type: "object",
                    properties: {}
                },
            },
        ],
    };
});

/**
 * Handler for the publish_article tool.
 * Publish a new article with the provided title and content, and returns success message.
 */
server.setRequestHandler(CallToolRequestSchema, async (request) => {
    if (request.params.name === "publish_article") {
        // server.sendLoggingMessage({
        //     level: "debug",
        //     data: JSON.stringify(request.params.arguments),
        // });

        // Get content from either file_path or content parameter
        let content: string;
        const filePath = request.params.arguments?.file_path as string | undefined;
        const contentArg = request.params.arguments?.content as string | undefined;

        if (filePath) {
            // Read content from file
            try {
                content = fs.readFileSync(filePath, 'utf-8');
                // Resolve relative image paths to absolute paths
                const baseDir = path.dirname(filePath);
                content = resolveImagePaths(content, baseDir);
            } catch (error) {
                return {
                    content: [
                        {
                            type: "text",
                            text: `Error reading file: ${error instanceof Error ? error.message : String(error)}`,
                        },
                    ],
                    isError: true,
                };
            }
        } else if (contentArg) {
            content = contentArg;
        } else {
            return {
                content: [
                    {
                        type: "text",
                        text: "Error: Either 'content' or 'file_path' parameter is required.",
                    },
                ],
                isError: true,
            };
        }

        const themeId = String(request.params.arguments?.theme_id || "");
        const gzhContent = await getGzhContent(content, themeId, "solarized-light", true, true);
        const title = gzhContent.title ?? "this is title";
        const cover = gzhContent.cover ?? "";
        const response = await publishToDraft(title, gzhContent.content, cover);

        return {
            content: [
                {
                    type: "text",
                    text: `Your article was successfully published to '公众号草稿箱'. The media ID is ${response.media_id}.`,
                },
            ],
        };
    } else if (request.params.name === "list_themes") {
        const themeResources = Object.entries(themes).map(([id, theme]: [string, Theme]) => ({
            type: "text",
            text: JSON.stringify({
                id: theme.id,
                name: theme.name,
                description: theme.description
            }),
        }));
        return {
            content: themeResources,
        };
    }

    throw new Error("Unknown tool");
});


/**
 * Start the server using stdio transport.
 * This allows the server to communicate via standard input/output streams.
 */
async function main() {
    const transport = new StdioServerTransport();
    await server.connect(transport);
}

main().catch((error) => {
    console.error("Server error:", error);
    process.exit(1);
});
