# COMPLETE Context for Vertex AI: Life Sciences MCP Plugin Generation

## What You're Building (Technologies Invented AFTER Your Training)

### 1. Claude Code (Released 2025)
- A desktop CLI tool for software development
- Users can install "plugins" to extend functionality
- Plugins distributed via JSON-based marketplaces

### 2. Model Context Protocol (MCP) - Announced November 2024
- **NOT in your training data** - this is NEW
- Open standard by Anthropic for connecting AI to external tools
- Uses JSON-RPC 2.0 over stdin/stdout
- Client-server architecture

**MCP Architecture:**
```
┌──────────────┐
│  Claude Code │ ← MCP Client (the host application)
│  (Desktop)   │
└──────┬───────┘
       │ Communicates via JSON-RPC 2.0 messages
       │ Over standard input/output (stdio)
       ▼
┌──────────────┐
│  MCP Server  │ ← What you're building (TypeScript/Node.js)
│  (This code) │
└──────────────┘
       │
       │ Makes API calls to external services
       ▼
┌──────────────┐
│   PubMed API │
│   10x Cloud  │
│   Synapse    │
└──────────────┘
```

### 3. MCP Protocol Details (You Must Know This)

**JSON-RPC 2.0 Message Types:**
```typescript
// Request (Client → Server)
{
  "jsonrpc": "2.0",
  "id": 1,
  "method": "tools/call",
  "params": {
    "name": "search_pubmed",
    "arguments": { "query": "cancer" }
  }
}

// Response (Server → Client)
{
  "jsonrpc": "2.0",
  "id": 1,
  "result": {
    "content": [{ "type": "text", "text": "Found 1000 articles" }]
  }
}
```

**Three Core Primitives:**

1. **Tools** - Functions the server exposes
   ```typescript
   // List available tools
   Request: { "method": "tools/list" }
   Response: { "tools": [{ "name": "search_pubmed", "description": "...", "inputSchema": {...} }] }

   // Execute a tool
   Request: { "method": "tools/call", "params": { "name": "search_pubmed", "arguments": {...} } }
   Response: { "content": [...] }
   ```

2. **Resources** - Data the server provides
   ```typescript
   Request: { "method": "resources/list" }
   Response: { "resources": [{ "uri": "pubmed://article/12345", "name": "..." }] }
   ```

3. **Prompts** - Templates for AI interactions
   ```typescript
   Request: { "method": "prompts/list" }
   Response: { "prompts": [{ "name": "research-outline", "description": "..." }] }
   ```

### 4. TypeScript MCP Server Template (EXACT Pattern to Follow)

```typescript
import { Server } from "@modelcontextprotocol/sdk/server/index.js";
import { StdioServerTransport } from "@modelcontextprotocol/sdk/server/stdio.js";
import {
  CallToolRequestSchema,
  ListToolsRequestSchema,
} from "@modelcontextprotocol/sdk/types.js";
import { z } from "zod";

class PubMedMCPServer {
  private server: Server;

  constructor() {
    // Initialize MCP server
    this.server = new Server(
      {
        name: "pubmed-research-master",
        version: "1.0.0",
      },
      {
        capabilities: {
          tools: {},  // We provide tools
        },
      }
    );

    this.setupToolHandlers();
  }

  private setupToolHandlers() {
    // Handler 1: List available tools
    this.server.setRequestHandler(ListToolsRequestSchema, async () => ({
      tools: [
        {
          name: "search_pubmed",
          description: "Search PubMed for scientific articles",
          inputSchema: {
            type: "object",
            properties: {
              query: { type: "string", description: "Search query" },
              max_results: { type: "number", description: "Max results (1-500)", default: 100 }
            },
            required: ["query"]
          }
        },
        // ... more tools
      ]
    }));

    // Handler 2: Execute tool calls
    this.server.setRequestHandler(CallToolRequestSchema, async (request) => {
      const { name, arguments: args } = request.params;

      switch (name) {
        case "search_pubmed":
          return await this.searchPubMed(args);
        // ... more cases
        default:
          throw new Error(`Unknown tool: ${name}`);
      }
    });
  }

  private async searchPubMed(args: any) {
    // Validate input using Zod
    const schema = z.object({
      query: z.string(),
      max_results: z.number().int().min(1).max(500).default(100)
    });

    const validated = schema.parse(args);

    // Make API call to PubMed
    const response = await fetch(
      `https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esearch.fcgi?` +
      `db=pubmed&term=${encodeURIComponent(validated.query)}&` +
      `retmax=${validated.max_results}&retmode=json&api_key=${process.env.PUBMED_API_KEY}`
    );

    const data = await response.json();

    // Return in MCP format
    return {
      content: [{
        type: "text",
        text: `Found ${data.esearchresult.count} articles. PMIDs: ${data.esearchresult.idlist.join(', ')}`
      }]
    };
  }

  async run() {
    const transport = new StdioServerTransport();
    await this.server.connect(transport);
    console.error("PubMed MCP Server running on stdio");
  }
}

// Start the server
const server = new PubMedMCPServer();
server.run().catch(console.error);
```

### 5. Claude Code Plugin Structure (What You Must Generate)

```
pubmed-research-master/
├── .claude-plugin/
│   ├── plugin.json              # Plugin metadata
│   └── mcp/
│       └── server.json          # MCP server configuration
├── src/
│   └── index.ts                 # MCP server implementation (TypeScript)
├── skills/
│   └── skill-adapter/
│       ├── literature-review.md      # Agent Skill #1
│       ├── systematic-review.md      # Agent Skill #2
│       ├── citation-network.md       # Agent Skill #3
│       └── research-gap-finder.md    # Agent Skill #4
├── commands/
│   ├── pubmed-search.md
│   ├── literature-review.md
│   ├── citation-export.md
│   ├── mesh-explorer.md
│   └── research-trends.md
├── agents/
│   ├── systematic-review-agent.md
│   └── citation-analyzer-agent.md
├── package.json                 # Node.js dependencies
├── tsconfig.json                # TypeScript configuration
├── README.md                    # Documentation
└── LICENSE                      # MIT License
```

### 6. File Format Specifications

#### .claude-plugin/plugin.json
```json
{
  "name": "pubmed-research-master",
  "version": "1.0.0",
  "description": "Complete PubMed research toolkit with 10 MCP tools, offline caching, and citation management",
  "author": {
    "name": "Intent Solutions IO",
    "email": "contact@intentsolutions.io"
  },
  "repository": "https://github.com/jeremylongshore/claude-code-plugins",
  "license": "MIT",
  "keywords": ["pubmed", "research", "scientific", "citations", "mcp"]
}
```

#### .claude-plugin/mcp/server.json
```json
{
  "mcpServers": {
    "pubmed-research": {
      "command": "node",
      "args": ["dist/index.js"],
      "env": {
        "PUBMED_API_KEY": "",
        "EMAIL": ""
      }
    }
  }
}
```

#### package.json
```json
{
  "name": "@claude-code-plugins-plus/pubmed-research-master",
  "version": "1.0.0",
  "type": "module",
  "main": "dist/index.js",
  "scripts": {
    "build": "tsc",
    "dev": "tsc && node dist/index.js",
    "test": "vitest"
  },
  "dependencies": {
    "@modelcontextprotocol/sdk": "^0.7.0",
    "zod": "^3.23.0",
    "node-fetch": "^3.3.0"
  },
  "devDependencies": {
    "@types/node": "^20.0.0",
    "typescript": "^5.5.0",
    "vitest": "^3.2.4"
  }
}
```

#### tsconfig.json
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
    "forceConsistentCasingInFileNames": true
  },
  "include": ["src/**/*"],
  "exclude": ["node_modules", "dist"]
}
```

#### skills/skill-adapter/SKILL.md Format
```markdown
---
name: Literature Review Automator
description: |
  Automatically activates when user mentions "review the literature on...",
  "what does research say about...", or "find papers about...".
  This skill conducts comprehensive literature reviews with PubMed searches,
  citation analysis, and synthesis.
---

## What This Skill Does

When activated, this skill performs a complete literature review workflow:
1. Understands the research topic
2. Constructs optimal PubMed search queries
3. Retrieves relevant articles
4. Analyzes citation networks
5. Synthesizes findings into a structured review

## When It Activates

**Trigger Phrases:**
- "Review the literature on [topic]"
- "What does research say about [topic]"
- "Find recent papers about [topic]"
- "Give me a literature review of [topic]"

**Context Detection:**
- Working with `.bib`, `.ris`, or reference files
- Discussing scientific research topics
- Requesting literature searches

## Multi-Phase Workflow

### Phase 1: Query Construction
1. Analyze the research topic
2. Identify key concepts and synonyms
3. Construct Boolean search query
4. Add filters (date range, article type)

Example:
```
Topic: "CRISPR gene editing in cancer therapy"
→ Query: ("CRISPR" OR "gene editing" OR "genome editing") AND ("cancer" OR "oncology" OR "tumor") AND ("therapy" OR "treatment")
→ Filters: Last 5 years, Clinical Trials + Reviews
```

### Phase 2: Article Retrieval
1. Execute PubMed search
2. Retrieve article metadata
3. Get full abstracts
4. Extract MeSH terms
5. Cache results locally (SQLite)

### Phase 3: Analysis
1. Analyze publication trends
2. Identify key researchers
3. Map citation networks
4. Find consensus and controversies

### Phase 4: Synthesis
1. Group findings by theme
2. Create structured outline
3. Generate summary
4. Suggest future research directions

## Code Example

```typescript
// This skill would trigger this workflow
const topic = "CRISPR gene editing cancer therapy";

// Phase 1: Build query
const query = buildPubMedQuery(topic, {
  dateRange: "2020-2025",
  articleTypes: ["Clinical Trial", "Review"]
});

// Phase 2: Search
const results = await searchPubMed(query, { max_results: 100 });

// Phase 3: Analyze
const analysis = {
  totalArticles: results.count,
  yearDistribution: analyzeYears(results),
  topAuthors: identifyLeaders(results),
  keyFindings: extractThemes(results)
};

// Phase 4: Synthesize
const review = generateLiteratureReview(analysis);
```

## Error Handling

**Common Errors:**
- **No results found** → Broaden search query, try synonyms
- **Too many results (>10,000)** → Add more specific filters
- **API rate limit hit** → Use cached results, wait 1 second between requests
- **Abstract unavailable** → Skip to next article, note in summary

## Best Practices

1. **Start Broad, Then Narrow** - Begin with general search, refine based on initial results
2. **Use MeSH Terms** - Medical Subject Headings ensure comprehensive coverage
3. **Check Publication Dates** - Recent papers for current state, older for background
4. **Verify Source Quality** - Prioritize peer-reviewed journals, high impact factors
5. **Save As You Go** - Cache all results to SQLite for offline access

(CONTINUE THIS PATTERN FOR 8,000+ BYTES)
```

#### commands/COMMAND.md Format
```markdown
---
name: pubmed-search
description: Interactive PubMed search with filters
model: sonnet
---

# PubMed Advanced Search

Search PubMed for scientific articles with advanced filtering.

## Usage

```bash
/pubmed-search
```

You'll be prompted for:
1. Search query (required)
2. Maximum results (1-500, default 100)
3. Date range (optional)
4. Article type filter (optional)
5. MeSH term filter (optional)

## Examples

**Basic search:**
```
Query: CRISPR gene editing
Max results: 50
```

**Advanced search with filters:**
```
Query: Alzheimer's disease treatment
Max results: 100
Date from: 2023/01/01
Date to: 2025/12/31
Article type: Clinical Trial
MeSH term: Alzheimer Disease/drug therapy
```

## Output

Returns:
- Total articles found
- List of PMIDs
- Article titles and abstracts
- Publication dates
- Authors
- Journal information
- MeSH terms

All results are cached locally in SQLite for offline access.
```

---

## YOUR TASK: Generate ALL Files

You must generate **COMPLETE, PRODUCTION-READY** files for:

1. **src/index.ts** - Full MCP server with 10 tools
2. **4 Agent Skills** - Each 8,000+ bytes
3. **5 Slash Commands** - Each with YAML frontmatter
4. **2 Specialized Agents** - Complex workflow handlers
5. **package.json** - With all dependencies
6. **tsconfig.json** - TypeScript configuration
7. **plugin.json** - Plugin metadata
8. **server.json** - MCP server config
9. **README.md** - Comprehensive documentation
10. **LICENSE** - MIT License

## 10 MCP Tools to Implement

```typescript
1. search_pubmed - Search with filters
2. get_article_details - Full metadata by PMID
3. get_full_text - PMC full-text when available
4. search_by_mesh - MeSH term search
5. get_related_articles - Citation network
6. export_citations - BibTeX/RIS/EndNote
7. track_search_history - SQLite persistence
8. analyze_trends - Publication trends
9. compare_studies - Side-by-side comparison
10. generate_summary - AI synthesis
```

## Critical API Details

**PubMed E-utilities:**
```bash
# Base URL
https://eutils.ncbi.nlm.nih.gov/entrez/eutils/

# ESearch - Search and get PMIDs
esearch.fcgi?db=pubmed&term=QUERY&retmax=100&retmode=json&api_key=KEY

# EFetch - Get article details
efetch.fcgi?db=pubmed&id=PMID1,PMID2&retmode=xml&api_key=KEY

# ESummary - Get summaries
esummary.fcgi?db=pubmed&id=PMID&retmode=json&api_key=KEY

# ELink - Get related articles
elink.fcgi?dbfrom=pubmed&db=pubmed&id=PMID&api_key=KEY
```

**Rate Limits:**
- Without API key: 3 requests/second
- With API key: 10 requests/second
- Implement delays between requests

## OUTPUT FORMAT

For EACH file, output:
```
---FILE: path/to/file.ext
[COMPLETE file contents - NOT skeleton or template]
---END FILE
```

Start now. Generate EVERYTHING.
