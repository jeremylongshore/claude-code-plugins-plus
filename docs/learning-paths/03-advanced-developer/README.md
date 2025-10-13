# ⚡ Advanced Developer Path: Build Production MCP Servers

**Goal**: Build executable MCP server plugins with real TypeScript/JavaScript code.

**Prerequisites**:
- Completed [Plugin Creator](../02-plugin-creator/) path
- Node.js 18+ and TypeScript experience
- Understanding of async/await and APIs

**Time Required**: 1 day (8 hours)

**What You'll Build**: A production-ready MCP server plugin with tools, resources, and prompts

---

## Table of Contents

1. [MCP vs AI Instructions](#step-1-mcp-vs-ai-instructions) (30 min)
2. [Set Up Development Environment](#step-2-set-up-development-environment) (30 min)
3. [Build Your First MCP Server](#step-3-build-your-first-mcp-server) (2 hours)
4. [Add Tools and Resources](#step-4-add-tools-and-resources) (2 hours)
5. [Implement Advanced Features](#step-5-implement-advanced-features) (2 hours)
6. [Testing and Debugging](#step-6-testing-and-debugging) (45 min)
7. [Package and Deploy](#step-7-package-and-deploy) (45 min)

---

## Step 1: MCP vs AI Instructions (30 min)

### Understanding the Difference

**AI Instruction Plugins** (215+ plugins in this repo):
```markdown
# commands/analyze.md
When user runs /analyze:
1. Read the codebase
2. Check for patterns
3. Generate report
```
- Markdown instructions
- Claude interprets and executes
- No external code

**MCP Server Plugins** (5 plugins in this repo):
```typescript
// src/index.ts
server.setRequestHandler(ListToolsRequestSchema, async () => ({
  tools: [{
    name: "analyze_code",
    description: "Analyze code complexity",
    inputSchema: { /* ... */ }
  }]
}));
```
- Real TypeScript/JavaScript
- Runs as Node.js process
- Actual executable code (13-26KB compiled)

### When to Use Each

**Use AI Instructions When**:
- Simple automation
- Workflow guidance
- Templates and patterns
- No external data needed

**Use MCP Servers When**:
- Need external APIs
- Complex calculations
- Database access
- Real-time data
- Third-party integrations

**Official Docs**:
- [MCP Specification](https://modelcontextprotocol.io/)
- [Claude Code MCP Guide](https://docs.claude.com/en/docs/claude-code/mcp)

---

## Step 2: Set Up Development Environment (30 min)

### Prerequisites

```bash
# Check Node.js version (18+ required)
node --version

# Check npm/pnpm
npm --version
# or
pnpm --version
```

### Install MCP SDK

```bash
# Create project directory
mkdir my-mcp-plugin
cd my-mcp-plugin

# Initialize package.json
pnpm init

# Install MCP SDK
pnpm add @modelcontextprotocol/sdk zod

# Install dev dependencies
pnpm add -D typescript @types/node tsx
```

### Project Structure

```
my-mcp-plugin/
├── src/
│   └── index.ts              # Main server code
├── dist/                     # Compiled output (generated)
├── .claude-plugin/
│   └── plugin.json          # Plugin metadata
├── package.json             # Node.js dependencies
├── tsconfig.json            # TypeScript config
├── README.md
└── LICENSE
```

### Configure TypeScript

Create `tsconfig.json`:

```json
{
  "compilerOptions": {
    "target": "ES2022",
    "module": "Node16",
    "moduleResolution": "Node16",
    "outDir": "./dist",
    "rootDir": "./src",
    "strict": true,
    "esModuleInterop": true,
    "skipLibCheck": true,
    "forceConsistentCasingInFileNames": true,
    "resolveJsonModule": true,
    "declaration": true
  },
  "include": ["src/**/*"],
  "exclude": ["node_modules", "dist"]
}
```

### Add Build Scripts

Update `package.json`:

```json
{
  "name": "my-mcp-plugin",
  "version": "1.0.0",
  "type": "module",
  "bin": {
    "my-mcp-plugin": "./dist/index.js"
  },
  "scripts": {
    "build": "tsc",
    "dev": "tsx src/index.ts",
    "prepare": "npm run build"
  },
  "dependencies": {
    "@modelcontextprotocol/sdk": "^1.0.0",
    "zod": "^3.23.0"
  }
}
```

**Official Docs**: [MCP TypeScript SDK](https://github.com/modelcontextprotocol/typescript-sdk)

---

## Step 3: Build Your First MCP Server (2 hours)

### Create the Server

Create `src/index.ts`:

```typescript
#!/usr/bin/env node
import { Server } from "@modelcontextprotocol/sdk/server/index.js";
import { StdioServerTransport } from "@modelcontextprotocol/sdk/server/stdio.js";
import {
  CallToolRequestSchema,
  ListToolsRequestSchema,
} from "@modelcontextprotocol/sdk/types.js";
import { z } from "zod";

// Create MCP server instance
const server = new Server(
  {
    name: "my-mcp-plugin",
    version: "1.0.0",
  },
  {
    capabilities: {
      tools: {},
    },
  }
);

// Define tool schema with Zod
const AnalyzeInputSchema = z.object({
  code: z.string().describe("Code to analyze"),
  language: z.string().optional().describe("Programming language"),
});

// List available tools
server.setRequestHandler(ListToolsRequestSchema, async () => {
  return {
    tools: [
      {
        name: "analyze_code",
        description: "Analyze code complexity and provide insights",
        inputSchema: {
          type: "object",
          properties: {
            code: {
              type: "string",
              description: "Code to analyze",
            },
            language: {
              type: "string",
              description: "Programming language (optional)",
            },
          },
          required: ["code"],
        },
      },
    ],
  };
});

// Handle tool execution
server.setRequestHandler(CallToolRequestSchema, async (request) => {
  if (request.params.name === "analyze_code") {
    const args = AnalyzeInputSchema.parse(request.params.arguments);

    // Your analysis logic
    const lineCount = args.code.split('\n').length;
    const complexity = calculateComplexity(args.code);

    return {
      content: [
        {
          type: "text",
          text: JSON.stringify({
            lines: lineCount,
            complexity: complexity,
            language: args.language || "unknown",
            suggestions: [
              "Consider breaking down functions over 50 lines",
              "Add more comments for complex logic"
            ]
          }, null, 2)
        }
      ]
    };
  }

  throw new Error(`Unknown tool: ${request.params.name}`);
});

// Helper function
function calculateComplexity(code: string): string {
  const cyclomaticKeywords = ['if', 'else', 'for', 'while', 'case', 'catch'];
  let complexity = 1;

  cyclomaticKeywords.forEach(keyword => {
    const regex = new RegExp(`\\b${keyword}\\b`, 'g');
    const matches = code.match(regex);
    complexity += matches ? matches.length : 0;
  });

  if (complexity <= 5) return "low";
  if (complexity <= 10) return "medium";
  return "high";
}

// Start the server
async function main() {
  const transport = new StdioServerTransport();
  await server.connect(transport);
  console.error("MCP server running on stdio");
}

main().catch((error) => {
  console.error("Fatal error:", error);
  process.exit(1);
});
```

### Build and Test

```bash
# Build TypeScript
pnpm build

# Test locally
node dist/index.js
# Server should start and wait for input
```

### Create Plugin Config

Create `.claude-plugin/plugin.json`:

```json
{
  "name": "my-mcp-plugin",
  "version": "1.0.0",
  "description": "Code analysis MCP server",
  "mcpServers": {
    "my-mcp-plugin": {
      "command": "node",
      "args": ["${CLAUDE_PLUGIN_ROOT}/dist/index.js"]
    }
  }
}
```

**Important**: Use `${CLAUDE_PLUGIN_ROOT}` for portable paths!

---

## Step 4: Add Tools and Resources (2 hours)

### Add More Tools

Enhance `src/index.ts` with multiple tools:

```typescript
// List tools
server.setRequestHandler(ListToolsRequestSchema, async () => {
  return {
    tools: [
      {
        name: "analyze_code",
        description: "Analyze code complexity",
        inputSchema: { /* ... */ }
      },
      {
        name: "find_bugs",
        description: "Detect potential bugs in code",
        inputSchema: {
          type: "object",
          properties: {
            code: { type: "string" },
            strictMode: { type: "boolean" }
          },
          required: ["code"]
        }
      },
      {
        name: "suggest_refactor",
        description: "Suggest code refactoring improvements",
        inputSchema: { /* ... */ }
      }
    ]
  };
});

// Handle tools
server.setRequestHandler(CallToolRequestSchema, async (request) => {
  switch (request.params.name) {
    case "analyze_code":
      return analyzeCode(request.params.arguments);
    case "find_bugs":
      return findBugs(request.params.arguments);
    case "suggest_refactor":
      return suggestRefactor(request.params.arguments);
    default:
      throw new Error(`Unknown tool: ${request.params.name}`);
  }
});
```

### Add Resources

Resources provide data Claude can access:

```typescript
import {
  ListResourcesRequestSchema,
  ReadResourceRequestSchema,
} from "@modelcontextprotocol/sdk/types.js";

// List available resources
server.setRequestHandler(ListResourcesRequestSchema, async () => {
  return {
    resources: [
      {
        uri: "analysis://best-practices",
        name: "Coding Best Practices",
        mimeType: "text/plain",
      },
      {
        uri: "analysis://patterns",
        name: "Common Anti-Patterns",
        mimeType: "application/json",
      }
    ]
  };
});

// Read resource content
server.setRequestHandler(ReadResourceRequestSchema, async (request) => {
  const uri = request.params.uri;

  if (uri === "analysis://best-practices") {
    return {
      contents: [
        {
          uri: uri,
          mimeType: "text/plain",
          text: `
# Coding Best Practices

1. Keep functions small and focused
2. Use meaningful variable names
3. Write self-documenting code
4. Handle errors gracefully
5. Add comprehensive tests
          `.trim()
        }
      ]
    };
  }

  throw new Error(`Unknown resource: ${uri}`);
});
```

### Add Prompts

Prompts are templates Claude can use:

```typescript
import {
  ListPromptsRequestSchema,
  GetPromptRequestSchema,
} from "@modelcontextprotocol/sdk/types.js";

server.setRequestHandler(ListPromptsRequestSchema, async () => {
  return {
    prompts: [
      {
        name: "code_review",
        description: "Comprehensive code review template",
        arguments: [
          {
            name: "code",
            description: "Code to review",
            required: true
          }
        ]
      }
    ]
  };
});

server.setRequestHandler(GetPromptRequestSchema, async (request) => {
  if (request.params.name === "code_review") {
    const code = request.params.arguments?.code;
    return {
      messages: [
        {
          role: "user",
          content: {
            type: "text",
            text: `Please review this code:\n\n${code}\n\nProvide feedback on:\n- Code quality\n- Potential bugs\n- Performance\n- Security`
          }
        }
      ]
    };
  }
  throw new Error(`Unknown prompt: ${request.params.name}`);
});
```

**Official Docs**: [MCP Tools, Resources, Prompts](https://modelcontextprotocol.io/docs/concepts/architecture)

---

## Step 5: Implement Advanced Features (2 hours)

### Add Error Handling

```typescript
import { McpError, ErrorCode } from "@modelcontextprotocol/sdk/types.js";

server.setRequestHandler(CallToolRequestSchema, async (request) => {
  try {
    const args = AnalyzeInputSchema.parse(request.params.arguments);
    // ... tool logic
  } catch (error) {
    if (error instanceof z.ZodError) {
      throw new McpError(
        ErrorCode.InvalidParams,
        `Invalid arguments: ${error.message}`
      );
    }
    throw new McpError(
      ErrorCode.InternalError,
      `Analysis failed: ${error.message}`
    );
  }
});
```

### Add Logging

```typescript
import { createLogger } from "@modelcontextprotocol/sdk/server/index.js";

const logger = createLogger("my-mcp-plugin");

server.setRequestHandler(CallToolRequestSchema, async (request) => {
  logger.info(`Executing tool: ${request.params.name}`);

  try {
    const result = await executeTool(request.params);
    logger.debug(`Tool result:`, result);
    return result;
  } catch (error) {
    logger.error(`Tool failed:`, error);
    throw error;
  }
});
```

### Add External API Integration

```typescript
import fetch from 'node-fetch';

async function analyzeSecurity(code: string): Promise<any> {
  // Example: Call external security analysis API
  const response = await fetch('https://api.security-scanner.com/analyze', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ code })
  });

  if (!response.ok) {
    throw new Error(`API error: ${response.statusText}`);
  }

  return await response.json();
}
```

### Add Caching

```typescript
const cache = new Map<string, any>();

async function cachedAnalysis(code: string): Promise<any> {
  const hash = createHash('sha256').update(code).digest('hex');

  if (cache.has(hash)) {
    logger.debug('Cache hit');
    return cache.get(hash);
  }

  const result = await analyzeCode(code);
  cache.set(hash, result);
  return result;
}
```

---

## Step 6: Testing and Debugging (45 min)

### Unit Tests

Create `src/__tests__/index.test.ts`:

```typescript
import { describe, it, expect } from 'vitest';
import { calculateComplexity } from '../index.js';

describe('Code Analysis', () => {
  it('calculates complexity correctly', () => {
    const code = `
      if (x > 0) {
        for (let i = 0; i < 10; i++) {
          console.log(i);
        }
      }
    `;
    expect(calculateComplexity(code)).toBe('medium');
  });
});
```

Install testing:
```bash
pnpm add -D vitest
```

Add to `package.json`:
```json
{
  "scripts": {
    "test": "vitest"
  }
}
```

### Debug with Claude Code

```bash
# Install locally for testing
/plugin install . --name my-mcp-plugin@local

# Enable debug logging
export MCP_DEBUG=1

# Use the tool
# Claude will call your MCP server
```

### Check Logs

```bash
# MCP server logs go to stderr
# Check Claude Code logs
tail -f ~/.claude/logs/mcp-*.log
```

**Official Docs**: [Testing MCP Servers](https://modelcontextprotocol.io/docs/tools/testing)

---

## Step 7: Package and Deploy (45 min)

### Final Package Structure

```
my-mcp-plugin/
├── dist/                    # Compiled JS (generated)
│   └── index.js
├── src/                     # TypeScript source
│   ├── index.ts
│   └── __tests__/
├── .claude-plugin/
│   └── plugin.json
├── package.json
├── tsconfig.json
├── README.md
├── LICENSE
└── .gitignore
```

### Create .gitignore

```
node_modules/
dist/
*.log
.env
.DS_Store
```

### Build for Production

```bash
# Clean build
rm -rf dist/
pnpm build

# Test build
node dist/index.js
```

### Publish to npm (Optional)

```bash
# Login to npm
npm login

# Publish
npm publish --access public
```

### Add to Marketplace

Update marketplace.json:

```json
{
  "name": "my-mcp-plugin",
  "source": "./plugins/mcp/my-mcp-plugin",
  "description": "Code analysis MCP server with tools and resources",
  "version": "1.0.0",
  "category": "analysis",
  "keywords": ["mcp", "code-analysis", "tools"],
  "author": {
    "name": "Your Name",
    "email": "you@example.com"
  }
}
```

Users install with:
```bash
/plugin install my-mcp-plugin@claude-code-plugins
```

---

## Real-World Examples

Study these production MCP servers in this repo:

### 1. project-health-auditor (13KB)
- 4 tools: complexity, churn, coverage, health score
- File analysis and git metrics
- JSON output format

**Location**: `plugins/mcp/project-health-auditor/`

### 2. conversational-api-debugger (26KB)
- OpenAPI spec parsing
- HAR file analysis
- Root cause detection
- 4 debugging tools

**Location**: `plugins/mcp/conversational-api-debugger/`

### 3. domain-memory-agent
- TF-IDF semantic search
- Knowledge base management
- 6 tools for memory operations

**Location**: `plugins/mcp/domain-memory-agent/`

---

## Congratulations! 🎉

You've mastered:
✅ MCP server architecture
✅ TypeScript MCP development
✅ Tools, resources, and prompts
✅ Error handling and logging
✅ Testing and debugging
✅ Production deployment

### Continue Learning

**Explore More**:
- [MCP Specification](https://modelcontextprotocol.io/)
- [MCP TypeScript SDK](https://github.com/modelcontextprotocol/typescript-sdk)
- [Claude Code MCP Guide](https://docs.claude.com/en/docs/claude-code/mcp)

**Join Community**:
- 💬 [GitHub Discussions](https://github.com/jeremylongshore/claude-code-plugins/discussions)
- 🗨️ [Discord](https://discord.com/invite/6PPFFzqPDZ)
- 📚 [MCP Community](https://github.com/modelcontextprotocol)

---

**You're now an advanced Claude Code plugin developer!** 🚀
