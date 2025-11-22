#!/usr/bin/env node

import { Server } from '@modelcontextprotocol/sdk/server/index.js';
import { StdioServerTransport } from '@modelcontextprotocol/sdk/server/stdio.js';
import {
  CallToolRequestSchema,
  ListToolsRequestSchema,
} from '@modelcontextprotocol/sdk/types.js';
import OpenAI from 'openai';
import { readFileSync, writeFileSync, mkdirSync } from 'fs';
import { resolve, dirname } from 'path';

// Initialize OpenAI client with custom base URL
const client = new OpenAI({
  apiKey: process.env.OPENAI_API_KEY,
  baseURL: process.env.OPENAI_BASE_URL || 'https://openai.app.msh.team/v1',
});

const MODEL = process.env.GEMINI_MODEL || 'gemini-3-pro-preview';

// Create MCP server
const server = new Server(
  {
    name: 'gemini-openai-mcp',
    version: '1.0.0',
  },
  {
    capabilities: {
      tools: {},
    },
  }
);

// List available tools
server.setRequestHandler(ListToolsRequestSchema, async () => {
  return {
    tools: [
      {
        name: 'gemini_query',
        description: 'Query Gemini 3 model with text prompt and optional file attachments (txt/md)',
        inputSchema: {
          type: 'object',
          properties: {
            prompt: {
              type: 'string',
              description: 'The prompt to send to Gemini 3',
            },
            file_paths: {
              type: 'array',
              items: {
                type: 'string',
              },
              description: 'Optional list of file paths (txt/md) to include in the query',
            },
            output_file_path: {
              type: 'string',
              description: 'Optional output file path (relative or absolute) to save Gemini response as markdown',
            },
          },
          required: ['prompt'],
        },
      },
    ],
  };
});

// Handle tool calls
server.setRequestHandler(CallToolRequestSchema, async (request) => {
  if (request.params.name === 'gemini_query') {
    const { prompt, file_paths, output_file_path } = request.params.arguments;

    let fullPrompt = prompt;

    // Read and append file contents if provided
    if (file_paths && Array.isArray(file_paths) && file_paths.length > 0) {
      fullPrompt += '\n\n--- Attached Files ---\n';

      for (const filePath of file_paths) {
        const ext = filePath.toLowerCase().split('.').pop();
        if (!['txt', 'md', 'markdown'].includes(ext)) {
          return {
            content: [
              {
                type: 'text',
                text: `Error: File ${filePath} has unsupported extension. Only .txt and .md files are allowed.`,
              },
            ],
          };
        }

        try {
          const absolutePath = resolve(filePath);
          const content = readFileSync(absolutePath, 'utf-8');
          fullPrompt += `\nFile: ${filePath}\nContent:\n${content}\n`;
        } catch (error) {
          return {
            content: [
              {
                type: 'text',
                text: `Error reading file ${filePath}: ${error.message}`,
              },
            ],
          };
        }
      }
    }

    try {
      const response = await client.chat.completions.create({
        model: MODEL,
        messages: [
          {
            role: 'user',
            content: fullPrompt,
          },
        ],
      });

      const answer = response.choices[0]?.message?.content || 'No response';

      // If output_file_path is provided, save to file
      if (output_file_path) {
        try {
          const absoluteOutputPath = resolve(output_file_path);
          const outputDir = dirname(absoluteOutputPath);

          // Create directory if it doesn't exist
          mkdirSync(outputDir, { recursive: true });

          // Write response to file
          writeFileSync(absoluteOutputPath, answer, 'utf-8');

          return {
            content: [
              {
                type: 'text',
                text: `Response saved to: ${absoluteOutputPath}`,
              },
            ],
          };
        } catch (error) {
          return {
            content: [
              {
                type: 'text',
                text: `Error writing to file ${output_file_path}: ${error.message}`,
              },
            ],
          };
        }
      }

      // If no output_file_path, return response directly
      return {
        content: [
          {
            type: 'text',
            text: answer,
          },
        ],
      };
    } catch (error) {
      return {
        content: [
          {
            type: 'text',
            text: `Error calling Gemini API: ${error.message}`,
          },
        ],
      };
    }
  }

  return {
    content: [
      {
        type: 'text',
        text: `Unknown tool: ${request.params.name}`,
      },
    ],
  };
});

// Start server
async function main() {
  const transport = new StdioServerTransport();
  await server.connect(transport);
  console.error('Gemini OpenAI MCP server running on stdio');
}

main().catch((error) => {
  console.error('Server error:', error);
  process.exit(1);
});
