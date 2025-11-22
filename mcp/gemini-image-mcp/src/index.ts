#!/usr/bin/env node

import { Server } from "@modelcontextprotocol/sdk/server/index.js";
import { StdioServerTransport } from "@modelcontextprotocol/sdk/server/stdio.js";
import {
  CallToolRequestSchema,
  ListToolsRequestSchema,
} from "@modelcontextprotocol/sdk/types.js";

interface GenerateImageArgs {
  prompt: string;
  save_path?: string;
}

const OPENAI_API_KEY = process.env.OPENAI_API_KEY || process.env.QIANXUN_API_KEY;
const OPENAI_BASE_URL = process.env.OPENAI_BASE_URL || "your-openai-compatible-api-url";
const MODEL = "gemini-3-pro-image-preview";

if (!OPENAI_API_KEY) {
  console.error("Error: OPENAI_API_KEY or QIANXUN_API_KEY environment variable is required");
  process.exit(1);
}

async function generateImage(prompt: string, savePath?: string): Promise<string> {
  const response = await fetch(`${OPENAI_BASE_URL}/chat/completions`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      "Authorization": `Bearer ${OPENAI_API_KEY}`,
    },
    body: JSON.stringify({
      model: MODEL,
      messages: [
        {
          role: "user",
          content: prompt,
        },
      ],
    }),
  });

  if (!response.ok) {
    const errorText = await response.text();
    throw new Error(`API request failed: ${response.status} ${response.statusText}\n${errorText}`);
  }

  const data = await response.json();
  const content = data.choices?.[0]?.message?.content;

  if (!content) {
    throw new Error("No image generated in response");
  }

  // Extract base64 image from markdown format: ![image](data:image/png;base64,...)
  const imageMatch = content.match(/!\[.*?\]\(data:image\/(png|jpeg|jpg);base64,([^)]+)\)/);

  if (!imageMatch) {
    throw new Error("No base64 image found in response");
  }

  const imageFormat = imageMatch[1];
  const base64Data = imageMatch[2];

  // Save to file if path provided
  if (savePath) {
    const fs = await import("fs/promises");
    const path = await import("path");

    // Ensure the path ends with correct extension
    let finalPath = savePath;
    if (!finalPath.match(/\.(png|jpg|jpeg)$/i)) {
      finalPath += `.${imageFormat}`;
    }

    // Create directory if it doesn't exist
    const dir = path.dirname(finalPath);
    await fs.mkdir(dir, { recursive: true });

    // Write the file
    const buffer = Buffer.from(base64Data, "base64");
    await fs.writeFile(finalPath, buffer);

    return `Image generated and saved to: ${finalPath}`;
  }

  return `Image generated successfully (base64 encoded, ${base64Data.length} chars).\n\nTo view the image, you can:\n1. Save it using the save_path parameter\n2. View the base64 data directly\n\nBase64 preview (first 100 chars): ${base64Data.substring(0, 100)}...`;
}

const server = new Server(
  {
    name: "gemini-image-mcp",
    version: "1.0.0",
  },
  {
    capabilities: {
      tools: {},
    },
  }
);

server.setRequestHandler(ListToolsRequestSchema, async () => {
  return {
    tools: [
      {
        name: "generate_image",
        description:
          "Generate an image using Gemini 3 Pro Image Preview model. " +
          "Provide a detailed text prompt describing the image you want to create. " +
          "Optionally specify a file path to save the generated image.",
        inputSchema: {
          type: "object",
          properties: {
            prompt: {
              type: "string",
              description: "Detailed description of the image to generate",
            },
            save_path: {
              type: "string",
              description: "Optional: File path to save the generated image (e.g., '/path/to/image.png')",
            },
          },
          required: ["prompt"],
        },
      },
    ],
  };
});

server.setRequestHandler(CallToolRequestSchema, async (request) => {
  if (request.params.name !== "generate_image") {
    throw new Error(`Unknown tool: ${request.params.name}`);
  }

  const args = request.params.arguments as unknown as GenerateImageArgs;

  if (!args || !args.prompt) {
    throw new Error("Missing required argument: prompt");
  }

  try {
    const result = await generateImage(args.prompt, args.save_path);

    return {
      content: [
        {
          type: "text",
          text: result,
        },
      ],
    };
  } catch (error) {
    const errorMessage = error instanceof Error ? error.message : String(error);
    return {
      content: [
        {
          type: "text",
          text: `Error generating image: ${errorMessage}`,
        },
      ],
      isError: true,
    };
  }
});

async function main() {
  const transport = new StdioServerTransport();
  await server.connect(transport);
  console.error("Gemini Image MCP server running on stdio");
}

main().catch((error) => {
  console.error("Fatal error in main():", error);
  process.exit(1);
});
