#!/usr/bin/env node

/**
 * AI Experiment Logger - MCP Server
 * Provides tools for tracking and analyzing AI experiments
 */

import { Server } from '@modelcontextprotocol/sdk/server/index.js';
import { StdioServerTransport } from '@modelcontextprotocol/sdk/server/stdio.js';
import {
  CallToolRequestSchema,
  ListToolsRequestSchema,
  Tool,
} from '@modelcontextprotocol/sdk/types.js';
import { z } from 'zod';
import { ExperimentStorage } from './storage.js';
import type { ExperimentInput } from './types.js';

// Initialize storage
const storage = new ExperimentStorage();
await storage.initialize();

// Define tool schemas
const LogExperimentSchema = z.object({
  aiTool: z.string().describe('Name of the AI tool used (e.g., "ChatGPT", "Claude", "Gemini")'),
  prompt: z.string().describe('The prompt or query sent to the AI'),
  result: z.string().describe('Summary of the AI response or outcome'),
  rating: z.number().min(1).max(5).describe('Effectiveness rating from 1 (poor) to 5 (excellent)'),
  tags: z.array(z.string()).optional().describe('Optional tags for categorization'),
  date: z.string().optional().describe('Experiment date (ISO 8601), defaults to now')
});

const ListExperimentsSchema = z.object({
  aiTool: z.string().optional().describe('Filter by AI tool name'),
  rating: z.number().min(1).max(5).optional().describe('Filter by rating'),
  tags: z.array(z.string()).optional().describe('Filter by tags'),
  dateFrom: z.string().optional().describe('Filter from date (ISO 8601)'),
  dateTo: z.string().optional().describe('Filter to date (ISO 8601)'),
  searchQuery: z.string().optional().describe('Search across all fields')
});

const UpdateExperimentSchema = z.object({
  id: z.string().describe('Experiment ID'),
  aiTool: z.string().optional(),
  prompt: z.string().optional(),
  result: z.string().optional(),
  rating: z.number().min(1).max(5).optional(),
  tags: z.array(z.string()).optional(),
  date: z.string().optional()
});

const DeleteExperimentSchema = z.object({
  id: z.string().describe('Experiment ID to delete')
});

// Define tools
const tools: Tool[] = [
  {
    name: 'log_experiment',
    description: 'Log a new AI experiment with details about the tool, prompt, result, and effectiveness rating',
    inputSchema: {
      type: 'object',
      properties: {
        aiTool: {
          type: 'string',
          description: 'Name of the AI tool used (e.g., "ChatGPT", "Claude", "Gemini")'
        },
        prompt: {
          type: 'string',
          description: 'The prompt or query sent to the AI'
        },
        result: {
          type: 'string',
          description: 'Summary of the AI response or outcome'
        },
        rating: {
          type: 'number',
          description: 'Effectiveness rating from 1 (poor) to 5 (excellent)',
          minimum: 1,
          maximum: 5
        },
        tags: {
          type: 'array',
          items: { type: 'string' },
          description: 'Optional tags for categorization'
        },
        date: {
          type: 'string',
          description: 'Experiment date (ISO 8601), defaults to now'
        }
      },
      required: ['aiTool', 'prompt', 'result', 'rating']
    }
  },
  {
    name: 'list_experiments',
    description: 'List all experiments with optional filtering by tool, rating, tags, date range, or search query',
    inputSchema: {
      type: 'object',
      properties: {
        aiTool: {
          type: 'string',
          description: 'Filter by AI tool name'
        },
        rating: {
          type: 'number',
          description: 'Filter by rating (1-5)',
          minimum: 1,
          maximum: 5
        },
        tags: {
          type: 'array',
          items: { type: 'string' },
          description: 'Filter by tags (returns experiments with any of these tags)'
        },
        dateFrom: {
          type: 'string',
          description: 'Filter from date (ISO 8601 format)'
        },
        dateTo: {
          type: 'string',
          description: 'Filter to date (ISO 8601 format)'
        },
        searchQuery: {
          type: 'string',
          description: 'Search across tool, prompt, result, and tags'
        }
      }
    }
  },
  {
    name: 'get_experiment',
    description: 'Get a specific experiment by ID',
    inputSchema: {
      type: 'object',
      properties: {
        id: {
          type: 'string',
          description: 'Experiment ID'
        }
      },
      required: ['id']
    }
  },
  {
    name: 'update_experiment',
    description: 'Update an existing experiment',
    inputSchema: {
      type: 'object',
      properties: {
        id: {
          type: 'string',
          description: 'Experiment ID'
        },
        aiTool: { type: 'string' },
        prompt: { type: 'string' },
        result: { type: 'string' },
        rating: { type: 'number', minimum: 1, maximum: 5 },
        tags: { type: 'array', items: { type: 'string' } },
        date: { type: 'string' }
      },
      required: ['id']
    }
  },
  {
    name: 'delete_experiment',
    description: 'Delete an experiment by ID',
    inputSchema: {
      type: 'object',
      properties: {
        id: {
          type: 'string',
          description: 'Experiment ID to delete'
        }
      },
      required: ['id']
    }
  },
  {
    name: 'get_statistics',
    description: 'Get comprehensive statistics about all experiments including most effective tools, average ratings, and trends',
    inputSchema: {
      type: 'object',
      properties: {}
    }
  },
  {
    name: 'export_experiments',
    description: 'Export all experiments to CSV format',
    inputSchema: {
      type: 'object',
      properties: {}
    }
  }
];

// Create MCP server
const server = new Server(
  {
    name: 'ai-experiment-logger',
    version: '1.0.0',
  },
  {
    capabilities: {
      tools: {},
    },
  }
);

// Register tool handlers
server.setRequestHandler(ListToolsRequestSchema, async () => ({
  tools
}));

server.setRequestHandler(CallToolRequestSchema, async (request) => {
  const { name, arguments: args } = request.params;

  try {
    switch (name) {
      case 'log_experiment': {
        const parsed = LogExperimentSchema.parse(args);
        const experiment = await storage.createExperiment({
          ...parsed,
          rating: parsed.rating as 1 | 2 | 3 | 4 | 5
        });
        return {
          content: [
            {
              type: 'text',
              text: JSON.stringify({
                success: true,
                message: 'Experiment logged successfully',
                experiment
              }, null, 2)
            }
          ]
        };
      }

      case 'list_experiments': {
        const filters = ListExperimentsSchema.parse(args);
        const experiments = await storage.listExperiments(filters);
        return {
          content: [
            {
              type: 'text',
              text: JSON.stringify({
                success: true,
                count: experiments.length,
                experiments
              }, null, 2)
            }
          ]
        };
      }

      case 'get_experiment': {
        const { id } = z.object({ id: z.string() }).parse(args);
        const experiment = await storage.getExperiment(id);
        if (!experiment) {
          return {
            content: [
              {
                type: 'text',
                text: JSON.stringify({
                  success: false,
                  error: 'Experiment not found'
                })
              }
            ],
            isError: true
          };
        }
        return {
          content: [
            {
              type: 'text',
              text: JSON.stringify({
                success: true,
                experiment
              }, null, 2)
            }
          ]
        };
      }

      case 'update_experiment': {
        const { id, rating, ...otherUpdates } = UpdateExperimentSchema.parse(args);
        const updates: Partial<ExperimentInput> = {
          ...otherUpdates,
          ...(rating !== undefined && { rating: rating as 1 | 2 | 3 | 4 | 5 })
        };
        const experiment = await storage.updateExperiment(id, updates);
        if (!experiment) {
          return {
            content: [
              {
                type: 'text',
                text: JSON.stringify({
                  success: false,
                  error: 'Experiment not found'
                })
              }
            ],
            isError: true
          };
        }
        return {
          content: [
            {
              type: 'text',
              text: JSON.stringify({
                success: true,
                message: 'Experiment updated successfully',
                experiment
              }, null, 2)
            }
          ]
        };
      }

      case 'delete_experiment': {
        const { id } = DeleteExperimentSchema.parse(args);
        const deleted = await storage.deleteExperiment(id);
        if (!deleted) {
          return {
            content: [
              {
                type: 'text',
                text: JSON.stringify({
                  success: false,
                  error: 'Experiment not found'
                })
              }
            ],
            isError: true
          };
        }
        return {
          content: [
            {
              type: 'text',
              text: JSON.stringify({
                success: true,
                message: 'Experiment deleted successfully'
              })
            }
          ]
        };
      }

      case 'get_statistics': {
        const stats = await storage.getStatistics();
        return {
          content: [
            {
              type: 'text',
              text: JSON.stringify({
                success: true,
                statistics: stats
              }, null, 2)
            }
          ]
        };
      }

      case 'export_experiments': {
        const csv = await storage.exportToCSV();
        return {
          content: [
            {
              type: 'text',
              text: JSON.stringify({
                success: true,
                format: 'csv',
                data: csv,
                message: 'Experiments exported successfully. Save this data to a .csv file.'
              })
            }
          ]
        };
      }

      default:
        return {
          content: [
            {
              type: 'text',
              text: JSON.stringify({
                success: false,
                error: `Unknown tool: ${name}`
              })
            }
          ],
          isError: true
        };
    }
  } catch (error) {
    return {
      content: [
        {
          type: 'text',
          text: JSON.stringify({
            success: false,
            error: error instanceof Error ? error.message : 'Unknown error'
          })
        }
      ],
      isError: true
    };
  }
});

// Start server
const transport = new StdioServerTransport();
await server.connect(transport);

console.error('AI Experiment Logger MCP server running');
console.error(`Data stored at: ${storage.getDataFilePath()}`);
