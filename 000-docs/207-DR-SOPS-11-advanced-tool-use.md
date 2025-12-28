# Advanced Tool Use: Dynamic Discovery, Programmatic Orchestration, and Parameter Guidance

## Introduction

Advanced tool use transforms Claude from a simple function-calling agent into an intelligent orchestrator capable of working with hundreds of tools, processing massive datasets, and executing complex multi-step workflows. Anthropic's three beta features—**Tool Search Tool**, **Programmatic Tool Calling**, and **Tool Use Examples**—solve the fundamental bottlenecks preventing production-scale agent deployments.

Traditional tool calling hits three critical walls: context bloat from loading tool definitions (55K+ tokens for basic MCP setups), context pollution from intermediate results (50KB+ of expense data for simple budget checks), and inference overhead (19+ separate model calls for 20-tool workflows). Advanced tool use eliminates these bottlenecks with dynamic tool discovery, code-based orchestration, and example-driven parameter guidance.

This playbook provides production implementation patterns for building agents that scale to enterprise tool libraries, handle multi-step research workflows, and process large datasets without context exhaustion.

## Table of Contents

1. [Core Problems and Solutions](#core-problems-and-solutions)
2. [Feature 1: Tool Search Tool](#feature-1-tool-search-tool)
3. [Feature 2: Programmatic Tool Calling](#feature-2-programmatic-tool-calling)
4. [Feature 3: Tool Use Examples](#feature-3-tool-use-examples)
5. [Architecture Patterns](#architecture-patterns)
6. [Implementation Guide](#implementation-guide)
7. [Performance Optimization](#performance-optimization)
8. [Error Handling and Monitoring](#error-handling-and-monitoring)
9. [Best Practices](#best-practices)
10. [Summary](#summary)

## Core Problems and Solutions

### Problem 1: Context Bloat from Tool Definitions

**Scenario:** You have 50+ MCP tools across GitHub, Slack, Sentry, Grafana, Splunk, and Jira integrations. Loading all tool definitions consumes 72K tokens before the conversation even starts. Adding one more server (Jira alone: 17K tokens) pushes overhead beyond 100K tokens.

**Traditional Approach:**
```typescript
// Load ALL tools upfront - massive context consumption
const tools = [
  githubTools,     // 15K tokens
  slackTools,      // 12K tokens
  sentryTools,     // 10K tokens
  grafanaTools,    // 8K tokens
  splunkTools,     // 10K tokens
  jiraTools        // 17K tokens
]; // Total: 72K tokens BEFORE any conversation
```

**Solution: Tool Search Tool** - Dynamic discovery loads only relevant tools on-demand, reducing overhead by 85%.

### Problem 2: Context Pollution from Intermediate Results

**Scenario:** Analyzing employee expenses across 20 team members. Each has 50-100 expense line items. Traditional tool calling forces all 2,000+ expense records into Claude's context (50KB+) just to find 2-3 budget violations.

**Traditional Flow:**
```
1. Fetch team members → 20 records (1KB)
2. Fetch expenses for each → 2,000 line items (50KB)
3. Fetch budget limits → 20 records (1KB)
4. Claude manually sums and compares → 52KB in context
```

**Solution: Programmatic Tool Calling** - Claude writes Python code that processes data in-flight, returning only the 2-3 violations (1KB total).

### Problem 3: Inference Overhead

**Traditional Multi-Step Workflow:**
```
Inference 1: Call get_team_members()
Inference 2: Call get_budget_limits()
Inference 3: Call get_expenses(user_1)
Inference 4: Call get_expenses(user_2)
... (18 more inferences)
Inference 22: Synthesize results
```

Each tool call requires a full model inference pass. A 20-tool workflow demands 20+ separate model runs, creating latency (minutes) and accuracy problems (context drift).

**Solution: Programmatic Tool Calling** - One code block orchestrates all calls, eliminating 19+ inference passes.

### Problem 4: Parameter Ambiguity

**Scenario:** Support ticket API with complex nested structures and format conventions. JSON schema defines structure but cannot express "when to include optional `escalation` parameter" or "reporter contact format."

**Schema Alone:**
```typescript
interface CreateTicketInput {
  title: string;
  description: string;
  priority?: "low" | "medium" | "high" | "critical";
  escalation?: {
    level: number;
    reason: string;
  };
  reporter?: {
    email?: string;
    slack?: string;
  };
}
// Schema says WHAT but not WHEN or HOW
```

**Solution: Tool Use Examples** - 1-5 realistic invocation examples show format conventions, parameter correlations, and usage patterns.

## Feature 1: Tool Search Tool

### How It Works

Rather than loading all tool definitions upfront, the Tool Search Tool discovers tools dynamically when needed. Developers mark tools with `defer_loading: true`, making them discoverable without consuming context initially. Claude searches for relevant tools, which expand into full definitions only when needed.

### Token Efficiency Comparison

**Before (Traditional Approach):**
```typescript
// All tools loaded upfront
const mcpSetup = {
  github: 15000,    // tokens
  slack: 12000,
  sentry: 10000,
  grafana: 8000,
  splunk: 10000,
  jira: 17000
};
// Total: 72,000 tokens consumed before conversation starts
```

**After (Tool Search Tool):**
```typescript
// Only search tool + discovered tools loaded
const optimizedSetup = {
  toolSearchTool: 500,           // Search capability
  discoveredTools: 3000          // 3-5 relevant tools
};
// Total: 3,500 tokens (85% reduction)
```

### Implementation Pattern

```typescript
// tools.config.ts
interface ToolConfiguration {
  name: string;
  description: string;
  defer_loading: boolean;  // Key parameter
  input_schema: object;
}

// Mark tools for deferred loading
const toolConfigs: ToolConfiguration[] = [
  {
    name: "github_create_pr",
    description: "Create GitHub pull requests with diff analysis",
    defer_loading: true,  // Discovered on-demand
    input_schema: githubPRSchema
  },
  {
    name: "slack_send_message",
    description: "Send messages to Slack channels and users",
    defer_loading: false,  // Always loaded (frequently used)
    input_schema: slackMessageSchema
  },
  // ... 48 more tools marked defer_loading: true
];

// Claude searches when needed
// User: "Create a PR for the authentication fix"
// Claude: Searches for "pull request creation" → discovers github_create_pr
// Only then does the full tool definition load
```

### Configuration Strategy

**Keep Always-Loaded (defer_loading: false):**
- Tools used in >50% of sessions
- Low-token tools (<500 tokens)
- Critical infrastructure (logging, error reporting)
- Frequently-paired tools (git + github, slack + notify)

**Mark Deferred (defer_loading: true):**
- Specialized tools (database migrations, ML model training)
- Domain-specific tools (legal document analysis, medical coding)
- Rarely-used integrations (legacy systems, backup services)
- Large tool libraries (>10 tools per service)

### System Prompt Guidance

Help Claude discover tools efficiently with context hints:

```typescript
const systemPrompt = `
You have access to tools across multiple domains:

**Communication:** Slack messaging, email sending, SMS notifications
**Version Control:** GitHub PRs, commits, issue tracking, code review
**Monitoring:** Sentry error tracking, Grafana dashboards, log analysis
**Project Management:** Jira tickets, sprint planning, roadmap updates
**Data:** Database queries, analytics, reporting, ETL pipelines

Use the Tool Search Tool to discover specific capabilities as needed.
Focus on the user's immediate task rather than loading all tools upfront.
`;
```

### Accuracy Improvements

Internal Anthropic testing revealed significant accuracy gains:

- **Claude Opus 4:** 49% → 74% (51% improvement)
- **Claude Opus 4.5:** 79.5% → 88.1% (11% improvement)

The improvement comes from reduced context noise—Claude focuses on relevant tools rather than scanning hundreds of definitions.

### When to Use Tool Search Tool

✅ **Use When:**
- Tool definitions exceed 10K tokens
- Large MCP setups with 10+ tools
- Many similar tool names causing confusion
- Accuracy concerns with tool selection
- Building multi-tenant systems with tenant-specific tools

❌ **Skip When:**
- Small libraries (under 10 tools)
- All tools used in every session
- Compact definitions (<5K total tokens)
- Real-time latency critical (discovery adds ~200ms)

### Prompt Caching Compatibility

Tool Search Tool maintains prompt caching benefits because deferred tools are excluded from the initial prompt entirely. They're only added to context after Claude searches for them, so cached prompts remain stable.

## Feature 2: Programmatic Tool Calling

### Core Concept

Instead of requesting tools sequentially, Claude writes Python code orchestrating multiple tools. Code runs in a sandboxed environment, pausing when tool results are needed. Results process within the execution context—**never entering Claude's context window**—until only final output returns.

### Workflow Transformation

**Traditional Multi-Step Scenario:**

```typescript
// User: "Which employees exceeded their quarterly budget?"

// Step 1: Fetch team members
const teamMembers = await getTeamMembers();  // 20 people
// Context: 1KB

// Step 2-21: Fetch expenses for each (20 sequential inferences)
for (const member of teamMembers) {
  const expenses = await getExpenses(member.id);  // 50-100 items each
  // Context grows: 1KB → 50KB (2,000 expense line items)
}

// Step 22: Fetch budget limits
const budgets = await getBudgetLimits();
// Context: 51KB

// Step 23: Claude manually sums and compares
// Final answer: "Alice, Bob, and Charlie exceeded budgets"
// Total: 23 inferences, 51KB context consumption
```

**With Programmatic Tool Calling:**

```python
# Claude writes this code (1 inference)
import asyncio

async def find_budget_violations():
    # Parallel fetches (no context pollution)
    teams, budgets = await asyncio.gather(
        get_team_members(),
        get_budget_limits()
    )

    # Fetch all expenses in parallel
    expense_tasks = [get_expenses(m.id) for m in teams]
    all_expenses = await asyncio.gather(*expense_tasks)

    # Process in Python (results never enter Claude's context)
    violations = []
    for member, expenses, budget in zip(teams, all_expenses, budgets):
        total = sum(e.amount for e in expenses)
        if total > budget.limit:
            violations.append({
                'name': member.name,
                'spent': total,
                'limit': budget.limit,
                'overage': total - budget.limit
            })

    return violations  # Only 2-3 records (1KB)

# Code executes outside Claude's context
# Only final result returns: [Alice: $12K/$10K, Bob: $8.5K/$8K, Charlie: $15K/$12K]
# Total: 1 inference, 1KB context consumption
```

### Efficiency Gains

**Token Reduction:**
- Average usage dropped from 43,588 → 27,297 tokens (37% reduction)
- Complex research tasks see 50%+ reductions

**Latency Improvement:**
- Eliminates 19+ inference passes
- Parallel execution (20 sequential calls → 1 async batch)
- Typical workflow: 45 seconds → 8 seconds

**Accuracy Boost:**
- Internal knowledge retrieval: 25.6% → 28.5%
- GIA benchmarks: 46.5% → 51.2%
- Reduced context drift from intermediate results

### Implementation Steps

**1. Enable Tools for Code Execution:**

```typescript
// tool-config.ts
interface ToolConfig {
  name: string;
  description: string;
  input_schema: object;
  allowed_callers?: string[];  // Key parameter
}

const expenseTools: ToolConfig[] = [
  {
    name: "get_team_members",
    description: "Fetch all team members with IDs",
    input_schema: { type: "object", properties: {} },
    allowed_callers: ["code_execution_20250825"]  // Opt-in
  },
  {
    name: "get_expenses",
    description: "Fetch expense records for a user",
    input_schema: {
      type: "object",
      properties: {
        user_id: { type: "string", description: "User ID" }
      },
      required: ["user_id"]
    },
    allowed_callers: ["code_execution_20250825"]  // Opt-in
  },
  {
    name: "get_budget_limits",
    description: "Fetch quarterly budget limits",
    input_schema: { type: "object", properties: {} },
    allowed_callers: ["code_execution_20250825"]  // Opt-in
  }
];
```

**2. Claude Generates Orchestration Code:**

Claude automatically writes async Python with:
- `asyncio.gather()` for parallel execution
- Data filtering and transformation
- Aggregation before returning results

**3. Tool Execution Outside Context:**

```typescript
// Execution flow
class ProgrammaticExecutor {
  async executeCode(pythonCode: string): Promise<any> {
    const sandbox = new CodeSandbox();

    // Parse code for tool calls
    const toolCalls = this.extractToolCalls(pythonCode);

    // Execute with tool pausing
    let result = null;
    for (const toolCall of toolCalls) {
      // Tool pauses execution, returns to API
      const toolResult = await this.invokeTool(toolCall);

      // Result goes back to code execution (NOT to Claude)
      sandbox.injectResult(toolCall.id, toolResult);
    }

    // Only final processed output returns
    return sandbox.getFinalResult();
  }
}
```

**4. Only Final Output Returns to Claude:**

```python
# Code processes 2,000 expense records internally
# Claude's context only receives:
[
  {"name": "Alice", "spent": 12000, "limit": 10000, "overage": 2000},
  {"name": "Bob", "spent": 8500, "limit": 8000, "overage": 500},
  {"name": "Charlie", "spent": 15000, "limit": 12000, "overage": 3000}
]
# 1KB vs 50KB (98% reduction)
```

### Advanced Patterns

**Pattern 1: Multi-Stage Data Pipeline**

```python
async def analyze_customer_churn():
    # Stage 1: Fetch raw data in parallel
    customers, transactions, support_tickets = await asyncio.gather(
        get_customers(status="active"),
        get_transactions(days=90),
        get_support_tickets(days=90)
    )

    # Stage 2: Enrich and filter (in Python, not context)
    enriched = []
    for customer in customers:
        tx = [t for t in transactions if t.customer_id == customer.id]
        tickets = [t for t in support_tickets if t.customer_id == customer.id]

        # Churn risk scoring
        revenue_trend = calculate_trend([t.amount for t in tx])
        ticket_sentiment = analyze_sentiment([t.description for t in tickets])

        if revenue_trend < -0.3 or ticket_sentiment < 0.4:
            enriched.append({
                'customer': customer.name,
                'risk_score': calculate_risk(revenue_trend, ticket_sentiment),
                'last_purchase': tx[-1].date if tx else None,
                'unresolved_tickets': len([t for t in tickets if not t.resolved])
            })

    # Stage 3: Return only high-risk customers
    return sorted(enriched, key=lambda x: x['risk_score'], reverse=True)[:10]
```

**Pattern 2: Iterative Refinement**

```python
async def find_optimal_pricing():
    # Fetch historical data
    sales_data = await get_sales_history(months=12)
    competitor_prices = await get_competitor_pricing()

    # Binary search for optimal price point
    low, high = 10, 100
    best_price = None
    best_revenue = 0

    while high - low > 1:
        mid = (low + high) // 2
        projected_revenue = simulate_revenue(sales_data, price=mid)

        if projected_revenue > best_revenue:
            best_revenue = projected_revenue
            best_price = mid

        if competitor_avg := average([c.price for c in competitor_prices]):
            if mid < competitor_avg:
                low = mid
            else:
                high = mid

    return {
        'optimal_price': best_price,
        'projected_revenue': best_revenue,
        'competitor_avg': competitor_avg
    }
```

### When to Use Programmatic Tool Calling

✅ **Use When:**
- Large datasets requiring aggregation (>1K records)
- Multi-step dependent workflows (3+ tool calls)
- Data transformation before reasoning
- Parallel operations across many items
- Intermediate data shouldn't influence reasoning

❌ **Skip When:**
- Simple single-tool calls
- Claude needs to see all intermediate results
- Quick lookups returning small responses (<1KB)
- Non-idempotent operations requiring human review

### Security Considerations

```typescript
// Safe tools for programmatic execution
const safeTools = [
  "read_database",      // Read-only, idempotent
  "fetch_api_data",     // GET requests only
  "calculate_metrics",  // Pure computation
  "analyze_logs"        // Read-only analysis
];

// Unsafe tools - require human approval
const unsafeTools = [
  "delete_records",     // Destructive
  "send_email",         // Side effects
  "charge_payment",     // Financial
  "deploy_code"         // Production changes
];

// Only mark safe tools for code execution
safeTools.forEach(tool => {
  tool.allowed_callers = ["code_execution_20250825"];
});
```

## Feature 3: Tool Use Examples

### Problem: Schema Ambiguity

JSON schemas define structure but cannot express usage patterns:

```typescript
// Schema shows WHAT but not WHEN or HOW
interface CreateTicketInput {
  title: string;                    // Always required
  description: string;              // Always required
  priority?: "low" | "medium" | "high" | "critical";  // When?
  escalation?: {                    // When to include?
    level: number;                  // What values are valid?
    reason: string;
  };
  reporter?: {                      // Format?
    email?: string;                 // Pattern?
    slack?: string;                 // Slack ID or @mention?
  };
  due_date?: string;                // Format? YYYY-MM-DD? ISO 8601?
}
```

**Common Errors Without Examples:**
- Missing required nested fields
- Wrong date formats (MM/DD/YYYY vs YYYY-MM-DD)
- Incorrect ID conventions (USR-123 vs 123 vs usr_123)
- Inappropriate parameter combinations
- Misunderstanding optional field usage

### Solution: Realistic Invocation Examples

Provide 1-5 examples showing minimal, partial, and full patterns:

```typescript
// tool-examples.ts
const createTicketExamples = [
  // Example 1: Minimal (required fields only)
  {
    title: "Login button unresponsive",
    description: "Users cannot click the login button on mobile Safari"
  },

  // Example 2: Partial (priority + reporter contact)
  {
    title: "Database connection pool exhausted",
    description: "Production API timing out due to connection pool limits",
    priority: "high",
    reporter: {
      slack: "U01ABC123XY"  // Shows Slack ID format
    }
  },

  // Example 3: Full (critical bug with escalation)
  {
    title: "Payment processing failures",
    description: "Stripe webhook timeouts causing failed charges",
    priority: "critical",
    escalation: {
      level: 2,  // Shows level values (1-3)
      reason: "Revenue impact: $50K/hour in failed transactions"
    },
    reporter: {
      email: "alice@company.com",
      slack: "U01ABC123XY"
    },
    due_date: "2025-01-15"  // Shows YYYY-MM-DD format
  },

  // Example 4: Feature request (no escalation)
  {
    title: "Add dark mode to dashboard",
    description: "Users requesting dark theme for night shift monitoring",
    priority: "low",
    reporter: {
      email: "bob@company.com"
    }
  },

  // Example 5: Medium priority with specific due date
  {
    title: "Upgrade PostgreSQL to v16",
    description: "Plan migration from v14 to v16 for performance improvements",
    priority: "medium",
    due_date: "2025-02-28"  // End of Q1
  }
];

// Attach to tool configuration
const createTicketTool = {
  name: "create_support_ticket",
  description: "Create support tickets for bugs, features, and infrastructure",
  input_schema: createTicketSchema,
  examples: createTicketExamples  // Key parameter
};
```

### What Examples Teach

**Format Conventions:**
- Date format: `2025-01-15` (YYYY-MM-DD)
- Slack IDs: `U01ABC123XY` (not @mentions)
- Email: Standard format

**Parameter Correlations:**
- Critical bugs → include escalation
- Feature requests → no escalation
- High priority → often includes reporter contact

**Nested Structure Usage:**
- Escalation: Only for critical/high priority
- Reporter: Email or Slack or both
- Due date: Optional for bugs, common for features

**Realistic Data:**
- Actual city names, plausible prices
- Real-world scenarios
- Varied examples (bugs, features, infrastructure)

### Internal Accuracy Results

Anthropic testing showed parameter handling improved from **72% → 90%** on complex tools.

### Best Practices for Examples

**1. Use Realistic Data:**
```typescript
// ❌ BAD: Generic placeholders
{
  title: "Title here",
  description: "Description here",
  priority: "medium"
}

// ✅ GOOD: Realistic scenario
{
  title: "API rate limiting returning 429 errors",
  description: "GitHub API calls exceeding 5000/hour limit during CI builds",
  priority: "high"
}
```

**2. Demonstrate Format Conventions:**
```typescript
// Show actual formats Claude should use
const examples = [
  { user_id: "USR-00123" },      // ID convention
  { created_at: "2025-01-15" },  // Date format
  { amount: 1299 },              // Cents not dollars
  { phone: "+1-555-0123" }       // Phone format
];
```

**3. Show Parameter Correlations:**
```typescript
// Critical bugs have escalation; features don't
const bugExample = {
  type: "bug",
  severity: "critical",
  escalation: { level: 2, reason: "Production outage" }
};

const featureExample = {
  type: "feature",
  priority: "low"
  // No escalation for features
};
```

**4. Clarify Optional Field Patterns:**
```typescript
// When to include optional nested structures
const minimalOrder = {
  items: [{ sku: "ABC-123", quantity: 2 }]
  // No shipping, no billing (digital goods)
};

const physicalOrder = {
  items: [{ sku: "XYZ-789", quantity: 1 }],
  shipping: {
    address: "123 Main St",
    city: "San Francisco",
    zip: "94102"
  },
  billing: {  // Include when different from shipping
    address: "456 Oak Ave",
    city: "Oakland",
    zip: "94601"
  }
};
```

**5. Keep to 1-5 Examples Per Tool:**
- Too few (1): Insufficient pattern coverage
- Optimal (3-5): Minimal, partial, full patterns
- Too many (10+): Cognitive overload, token waste

### When to Use Tool Use Examples

✅ **Use When:**
- Complex nested structures
- Many optional parameters with conditional patterns
- Domain-specific conventions (IDs, dates, formats)
- Disambiguating similar tools
- APIs with implicit parameter correlations

❌ **Skip When:**
- Simple single-parameter tools
- Standard formats Claude already understands
- Validation better handled by schema constraints
- Parameters are self-explanatory

## Architecture Patterns

### Pattern 1: Layered Tool Discovery

```typescript
// Layer 1: Always-loaded core tools
const corTools = [
  toolSearchTool,      // Discovery
  logError,            // Monitoring
  getUserContext       // Session management
];

// Layer 2: Frequently-used domain tools
const frequentTools = [
  slackSendMessage,    // Used in 80% of sessions
  getDatabaseRecord,   // Common queries
  searchDocuments      // Knowledge retrieval
];

// Layer 3: Deferred specialized tools (discovered on-demand)
const deferredTools = [
  githubCreatePR,      // 20% of sessions
  runDatabaseMigration, // 5% of sessions
  trainMLModel,        // 2% of sessions
  analyzeLegalDoc      // 1% of sessions
];

// Configuration
const toolConfig = {
  core: corTools.map(t => ({ ...t, defer_loading: false })),
  frequent: frequentTools.map(t => ({ ...t, defer_loading: false })),
  deferred: deferredTools.map(t => ({ ...t, defer_loading: true }))
};
```

### Pattern 2: Programmatic Orchestration with Fallback

```typescript
class ToolOrchestrator {
  async execute(task: string): Promise<any> {
    // Try programmatic execution first
    try {
      const code = await this.generateOrchestrationCode(task);
      const result = await this.executeProgrammatically(code);

      // Success - 37% token savings, 80% latency reduction
      return result;
    } catch (error) {
      // Fallback to traditional sequential tool calling
      console.warn('Programmatic execution failed, using sequential fallback');
      return await this.executeSequentially(task);
    }
  }

  private async executeProgrammatically(code: string): Promise<any> {
    const sandbox = new CodeSandbox();
    return await sandbox.run(code, {
      allowedTools: this.getSafeTools(),
      timeout: 30000,  // 30 second limit
      maxIterations: 100
    });
  }

  private getSafeTools(): string[] {
    // Only idempotent, read-only operations
    return [
      'get_*',      // All read operations
      'fetch_*',    // API fetches
      'calculate_*', // Pure computations
      'analyze_*'   // Read-only analysis
    ];
  }
}
```

### Pattern 3: Hybrid Tool Examples + Schema Validation

```typescript
interface ToolConfiguration {
  name: string;
  description: string;
  input_schema: JSONSchema;
  examples: ToolExample[];
  validation: ValidationRules;
}

const createOrderTool: ToolConfiguration = {
  name: "create_order",
  description: "Create customer orders with items, shipping, and billing",

  // Schema: Structural validation
  input_schema: {
    type: "object",
    properties: {
      items: { type: "array", minItems: 1 },
      shipping: { type: "object" },
      billing: { type: "object" }
    },
    required: ["items"]
  },

  // Examples: Behavioral guidance
  examples: [
    // Digital order (no shipping)
    { items: [{ sku: "DIG-001", qty: 1 }] },

    // Physical order (shipping required)
    {
      items: [{ sku: "PHY-123", qty: 2 }],
      shipping: { address: "123 Main St", city: "SF", zip: "94102" }
    },

    // Physical order with separate billing
    {
      items: [{ sku: "PHY-456", qty: 1 }],
      shipping: { address: "123 Main St", city: "SF", zip: "94102" },
      billing: { address: "456 Oak Ave", city: "Oakland", zip: "94601" }
    }
  ],

  // Validation: Runtime checks
  validation: {
    rules: [
      {
        condition: "item.sku.startsWith('PHY-')",
        requires: "shipping is provided",
        error: "Physical items require shipping address"
      },
      {
        condition: "billing is provided",
        requires: "billing.address !== shipping.address",
        error: "Billing address must differ from shipping when specified"
      }
    ]
  }
};
```

## Implementation Guide

### Step 1: Enable Advanced Tool Use Beta

```typescript
import Anthropic from "@anthropic-ai/sdk";

const client = new Anthropic({
  apiKey: process.env.ANTHROPIC_API_KEY
});

const response = await client.beta.messages.create({
  betas: ["advanced-tool-use-2025-11-20"],  // Enable beta features
  model: "claude-sonnet-4-5-20250929",
  max_tokens: 4096,
  tools: toolConfiguration,
  messages: [
    {
      role: "user",
      content: "Which employees exceeded their quarterly budget?"
    }
  ]
});
```

### Step 2: Configure Tool Discovery

```typescript
// tool-registry.ts
class ToolRegistry {
  private tools: Map<string, ToolConfig> = new Map();

  register(tool: ToolConfig): void {
    this.tools.set(tool.name, tool);
  }

  getConfiguration(): ToolConfig[] {
    const config: ToolConfig[] = [];

    // Always load: search tool + core utilities
    config.push(...this.getCoreTools());

    // Conditionally load: frequent tools
    config.push(...this.getFrequentTools());

    // Defer: specialized tools (85% token reduction)
    config.push(...this.getDeferredTools());

    return config;
  }

  private getCoreTools(): ToolConfig[] {
    return Array.from(this.tools.values()).filter(t =>
      t.category === "core" || t.usage_frequency > 0.5
    ).map(t => ({
      ...t,
      defer_loading: false
    }));
  }

  private getDeferredTools(): ToolConfig[] {
    return Array.from(this.tools.values()).filter(t =>
      t.category === "specialized" && t.usage_frequency < 0.2
    ).map(t => ({
      ...t,
      defer_loading: true
    }));
  }
}
```

### Step 3: Implement Programmatic Execution Handler

```typescript
// programmatic-executor.ts
class ProgrammaticExecutor {
  async handleToolUse(response: Message): Promise<ExecutionResult> {
    for (const content of response.content) {
      if (content.type === "code_execution") {
        return await this.executeCode(content);
      }
    }
    throw new Error("No code execution block found");
  }

  private async executeCode(codeBlock: CodeBlock): Promise<ExecutionResult> {
    const sandbox = this.createSandbox();

    try {
      // Parse code for tool dependencies
      const toolCalls = this.extractToolCalls(codeBlock.code);

      // Execute with paused tool resolution
      const result = await sandbox.execute(codeBlock.code, {
        onToolCall: async (name, params) => {
          // Verify tool is allowed for programmatic execution
          if (!this.isToolAllowed(name)) {
            throw new Error(`Tool ${name} not allowed for code execution`);
          }

          // Execute tool (result stays in sandbox, not in Claude's context)
          return await this.invokeTool(name, params);
        }
      });

      return {
        success: true,
        output: result,  // Only final processed result
        tokensConsumed: this.estimateTokens(result)  // Minimal
      };
    } catch (error) {
      return {
        success: false,
        error: error.message,
        fallback: "sequential_execution_recommended"
      };
    }
  }

  private isToolAllowed(toolName: string): boolean {
    const tool = this.toolRegistry.get(toolName);
    return tool?.allowed_callers?.includes("code_execution_20250825") ?? false;
  }
}
```

### Step 4: Add Tool Use Examples

```typescript
// tool-examples.ts
function createToolWithExamples(
  baseConfig: ToolConfig,
  examples: ToolExample[]
): EnrichedToolConfig {
  return {
    ...baseConfig,
    examples: examples.map(ex => ({
      input: ex,
      explanation: generateExplanation(ex, baseConfig.input_schema)
    }))
  };
}

// Example: Support ticket creation
const ticketTool = createToolWithExamples(
  {
    name: "create_ticket",
    description: "Create support tickets for bugs and features",
    input_schema: ticketSchema
  },
  [
    // Minimal
    {
      title: "Login fails on Safari",
      description: "Users report authentication errors"
    },
    // Partial
    {
      title: "API rate limit exceeded",
      description: "CI builds hitting GitHub rate limits",
      priority: "high",
      reporter: { slack: "U01ABC123" }
    },
    // Full
    {
      title: "Payment processor down",
      description: "Stripe webhooks timing out",
      priority: "critical",
      escalation: { level: 2, reason: "Revenue impact" },
      reporter: { email: "alice@co.com", slack: "U01ABC123" },
      due_date: "2025-01-15"
    }
  ]
);
```

## Performance Optimization

### Token Budget Management

```typescript
class TokenBudgetManager {
  private readonly maxContextTokens = 200000;  // Claude Sonnet 4.5
  private readonly reserveForResponse = 4096;

  calculateToolLoadingStrategy(): LoadingStrategy {
    const availableForTools = this.maxContextTokens - this.reserveForResponse;

    // Measure current tool definitions
    const currentToolTokens = this.estimateToolTokens();

    if (currentToolTokens < 10000) {
      return { strategy: "load_all", defer_loading: [] };
    } else if (currentToolTokens < 50000) {
      return {
        strategy: "selective_defer",
        defer_loading: this.identifyLowFrequencyTools()
      };
    } else {
      return {
        strategy: "aggressive_defer",
        defer_loading: this.identifyAllButCoreTools()
      };
    }
  }

  private estimateToolTokens(): number {
    return this.tools.reduce((total, tool) =>
      total + this.estimateSingleToolTokens(tool), 0
    );
  }

  private estimateSingleToolTokens(tool: ToolConfig): number {
    // Rough estimate: 1 token ≈ 4 characters
    const schemaSize = JSON.stringify(tool.input_schema).length / 4;
    const descriptionSize = tool.description.length / 4;
    return Math.ceil(schemaSize + descriptionSize + 50);  // +50 for overhead
  }
}
```

### Parallel Execution Optimization

```typescript
// Identify parallelizable tool calls in workflows
class ParallelExecutionOptimizer {
  analyzeWorkflow(steps: WorkflowStep[]): ExecutionPlan {
    const graph = this.buildDependencyGraph(steps);
    const parallelBatches = this.identifyParallelBatches(graph);

    return {
      batches: parallelBatches,
      estimatedLatency: this.estimateLatency(parallelBatches),
      tokenSavings: this.estimateTokenSavings(parallelBatches)
    };
  }

  private buildDependencyGraph(steps: WorkflowStep[]): DependencyGraph {
    const graph = new Map<string, Set<string>>();

    for (const step of steps) {
      const dependencies = new Set<string>();

      // Check if step parameters reference previous step outputs
      for (const param of Object.values(step.parameters)) {
        const refs = this.extractReferences(param);
        refs.forEach(ref => dependencies.add(ref));
      }

      graph.set(step.id, dependencies);
    }

    return graph;
  }

  private identifyParallelBatches(graph: DependencyGraph): ExecutionBatch[] {
    const batches: ExecutionBatch[] = [];
    const executed = new Set<string>();

    while (executed.size < graph.size) {
      // Find all steps with satisfied dependencies
      const ready = Array.from(graph.entries())
        .filter(([id, deps]) =>
          !executed.has(id) &&
          Array.from(deps).every(dep => executed.has(dep))
        )
        .map(([id]) => id);

      if (ready.length === 0) break;  // Circular dependency

      batches.push({
        steps: ready,
        parallelizable: true,
        estimatedTime: Math.max(...ready.map(id => this.estimateStepTime(id)))
      });

      ready.forEach(id => executed.add(id));
    }

    return batches;
  }
}
```

### Caching Strategy

```typescript
// Cache tool results for programmatic execution
class ToolResultCache {
  private cache = new Map<string, CachedResult>();
  private readonly ttl = 300000;  // 5 minutes

  async getCached(toolName: string, params: object): Promise<any | null> {
    const key = this.generateKey(toolName, params);
    const cached = this.cache.get(key);

    if (!cached) return null;
    if (Date.now() - cached.timestamp > this.ttl) {
      this.cache.delete(key);
      return null;
    }

    return cached.result;
  }

  async setCached(toolName: string, params: object, result: any): Promise<void> {
    const key = this.generateKey(toolName, params);
    this.cache.set(key, {
      result,
      timestamp: Date.now()
    });
  }

  private generateKey(toolName: string, params: object): string {
    // Stable serialization for consistent keys
    const sortedParams = this.sortObjectKeys(params);
    return `${toolName}:${JSON.stringify(sortedParams)}`;
  }
}
```

## Error Handling and Monitoring

### Programmatic Execution Error Recovery

```typescript
class ExecutionErrorHandler {
  async handleExecutionError(error: ExecutionError): Promise<RecoveryAction> {
    // Categorize error type
    if (error.type === "timeout") {
      return {
        action: "fallback_sequential",
        reason: "Code execution exceeded 30s timeout",
        recommendation: "Break workflow into smaller batches"
      };
    }

    if (error.type === "tool_not_allowed") {
      return {
        action: "request_permission",
        reason: `Tool ${error.toolName} not in allowed_callers list`,
        recommendation: "Add tool to allowed_callers or use sequential execution"
      };
    }

    if (error.type === "sandbox_crash") {
      return {
        action: "fallback_sequential",
        reason: "Code execution sandbox crashed",
        recommendation: "Review code for infinite loops or memory issues"
      };
    }

    // Default: fallback to sequential
    return {
      action: "fallback_sequential",
      reason: "Unknown execution error",
      recommendation: "Use traditional tool calling"
    };
  }
}
```

### Tool Discovery Monitoring

```typescript
// Monitor tool discovery patterns
class ToolDiscoveryMonitor {
  private metrics = {
    searches: 0,
    hits: 0,
    misses: 0,
    avgSearchLatency: 0
  };

  recordSearch(query: string, results: Tool[], latency: number): void {
    this.metrics.searches++;
    this.metrics.avgSearchLatency =
      (this.metrics.avgSearchLatency * (this.metrics.searches - 1) + latency)
      / this.metrics.searches;

    if (results.length > 0) {
      this.metrics.hits++;
    } else {
      this.metrics.misses++;
      this.logMissedSearch(query);
    }
  }

  private logMissedSearch(query: string): void {
    // Alert on common missed searches
    console.warn(`Tool search miss: "${query}"`);

    // Suggest tools to add or improve descriptions
    const suggestions = this.suggestToolImprovements(query);
    if (suggestions.length > 0) {
      console.info(`Consider adding tools: ${suggestions.join(', ')}`);
    }
  }

  getMetrics(): DiscoveryMetrics {
    return {
      ...this.metrics,
      hitRate: this.metrics.hits / this.metrics.searches,
      missRate: this.metrics.misses / this.metrics.searches
    };
  }
}
```

### Performance Metrics Dashboard

```typescript
interface AdvancedToolUseMetrics {
  // Token efficiency
  avgTokensPerRequest: number;
  tokenSavingsVsTraditional: number;

  // Latency
  avgLatencyMs: number;
  latencySavingsVsTraditional: number;

  // Accuracy
  toolSelectionAccuracy: number;
  parameterAccuracy: number;

  // Discovery
  toolSearchHitRate: number;
  avgToolsDiscovered: number;

  // Programmatic execution
  programmaticExecutionRate: number;
  avgResultSizeReduction: number;
}

class MetricsDashboard {
  async generateReport(): Promise<AdvancedToolUseMetrics> {
    const traditional = await this.getTraditionalBaseline();
    const advanced = await this.getAdvancedMetrics();

    return {
      avgTokensPerRequest: advanced.tokens,
      tokenSavingsVsTraditional:
        ((traditional.tokens - advanced.tokens) / traditional.tokens) * 100,

      avgLatencyMs: advanced.latency,
      latencySavingsVsTraditional:
        ((traditional.latency - advanced.latency) / traditional.latency) * 100,

      toolSelectionAccuracy: advanced.accuracy.toolSelection,
      parameterAccuracy: advanced.accuracy.parameters,

      toolSearchHitRate: advanced.discovery.hitRate,
      avgToolsDiscovered: advanced.discovery.avgDiscovered,

      programmaticExecutionRate: advanced.programmatic.executionRate,
      avgResultSizeReduction: advanced.programmatic.resultSizeReduction
    };
  }
}
```

## Best Practices

### DO: Progressive Feature Adoption

```typescript
// Phase 1: Start with Tool Search Tool (easiest win)
const phase1Config = {
  features: ["tool_search_tool"],
  defer_loading: identifyLowFrequencyTools(),  // 85% token reduction
  rollout: "all_users"
};

// Phase 2: Add Programmatic Tool Calling (complex workflows)
const phase2Config = {
  features: ["tool_search_tool", "programmatic_tool_calling"],
  programmatic_allowed: getSafeTools(),  // Read-only operations first
  rollout: "power_users"
};

// Phase 3: Tool Use Examples (accuracy improvements)
const phase3Config = {
  features: ["tool_search_tool", "programmatic_tool_calling", "tool_use_examples"],
  examples: addExamplesToComplexTools(),
  rollout: "all_users"
};
```

### DO: Document Tool Return Formats

```typescript
// Help Claude write better orchestration code
const toolWithDocumentedOutput = {
  name: "get_expenses",
  description: "Fetch expense records for a user",
  input_schema: { /* ... */ },
  output_format: {
    description: "Array of expense objects",
    example: [
      {
        id: "EXP-001",
        user_id: "USR-123",
        amount: 4599,  // Cents
        category: "travel",
        date: "2025-01-15",
        approved: true
      }
    ],
    fields: {
      id: "Unique expense ID (EXP-XXXXX)",
      amount: "Amount in cents (integer)",
      date: "ISO 8601 date string (YYYY-MM-DD)"
    }
  }
};
```

### DO: Use Clear, Descriptive Tool Names

```typescript
// ❌ BAD: Ambiguous names
const badNames = [
  "fetch",      // Fetch what?
  "process",    // Process what?
  "analyze"     // Analyze what?
];

// ✅ GOOD: Descriptive names for discovery
const goodNames = [
  "fetch_customer_expense_records",
  "process_invoice_payment",
  "analyze_sales_trend_quarterly"
];
```

### DON'T: Mark Unsafe Tools for Programmatic Execution

```typescript
// ❌ BAD: Dangerous tools in code execution
const dangerousConfig = {
  name: "delete_all_records",
  allowed_callers: ["code_execution_20250825"]  // NEVER DO THIS
};

// ✅ GOOD: Only safe, idempotent tools
const safeConfig = {
  name: "fetch_records",
  allowed_callers: ["code_execution_20250825"]  // Read-only, safe
};
```

### DON'T: Defer Frequently-Used Tools

```typescript
// ❌ BAD: Deferring high-frequency tools
const badDeferral = {
  name: "send_slack_message",  // Used in 80% of sessions
  defer_loading: true  // Adds discovery latency every time
};

// ✅ GOOD: Keep frequent tools always loaded
const goodConfig = {
  name: "send_slack_message",
  defer_loading: false  // Always available
};
```

### DON'T: Over-Engineer Examples

```typescript
// ❌ BAD: Too many examples (10+)
const tooManyExamples = [
  example1, example2, example3, example4, example5,
  example6, example7, example8, example9, example10,
  example11, example12  // Cognitive overload, token waste
];

// ✅ GOOD: 3-5 focused examples
const focusedExamples = [
  minimalExample,   // Required fields only
  partialExample,   // Common optional fields
  fullExample       // Complete usage
];
```

## Summary

Advanced tool use transforms Claude from a simple function-calling agent into an intelligent orchestrator capable of enterprise-scale deployments. The three beta features solve fundamental bottlenecks:

1. **Tool Search Tool** - Dynamic discovery reduces context overhead by 85% (72K → 3.5K tokens)
2. **Programmatic Tool Calling** - Code orchestration reduces token usage by 37% and eliminates 19+ inference passes
3. **Tool Use Examples** - Realistic invocations improve parameter accuracy from 72% → 90%

### Implementation Checklist

**Phase 1: Enable Beta Features**
- [ ] Add `betas: ["advanced-tool-use-2025-11-20"]` to API calls
- [ ] Use Claude Sonnet 4.5 (`claude-sonnet-4-5-20250929`)
- [ ] Test with existing tool configurations

**Phase 2: Configure Tool Discovery**
- [ ] Identify frequently-used tools (>50% of sessions)
- [ ] Mark 3-5 core tools `defer_loading: false`
- [ ] Mark specialized tools `defer_loading: true`
- [ ] Add system prompt guidance for discovery
- [ ] Monitor discovery hit rate (target: >80%)

**Phase 3: Enable Programmatic Execution**
- [ ] Identify safe, idempotent tools (read operations, calculations)
- [ ] Add `allowed_callers: ["code_execution_20250825"]` to safe tools
- [ ] Document tool return formats clearly
- [ ] Implement fallback to sequential execution
- [ ] Monitor execution success rate (target: >90%)

**Phase 4: Add Tool Use Examples**
- [ ] Identify tools with complex parameters (5+ optional fields)
- [ ] Create 3-5 realistic examples per complex tool
- [ ] Show minimal, partial, and full invocation patterns
- [ ] Demonstrate format conventions and parameter correlations
- [ ] Validate accuracy improvements (target: >10% gain)

**Phase 5: Production Monitoring**
- [ ] Track token usage (baseline vs advanced)
- [ ] Measure latency improvements
- [ ] Monitor tool selection accuracy
- [ ] Alert on discovery misses
- [ ] Review programmatic execution errors

### Key Metrics

**Target Performance:**
- Token reduction: 35-85% depending on feature mix
- Latency improvement: 50-80% for multi-step workflows
- Accuracy gains: 10-20% on complex tasks
- Discovery hit rate: >80%
- Programmatic execution success: >90%

### Next Steps

Advanced tool use is a beta feature rapidly evolving. Stay updated with [Anthropic's engineering blog](https://www.anthropic.com/engineering) for new capabilities, performance improvements, and production case studies.

For complex agent systems processing large datasets across hundreds of tools, these features are not optional—they're foundational for production deployments that scale beyond prototypes into enterprise production systems.

---

**Related Playbooks:**
- [Multi-Agent Rate Limits](01-multi-agent-rate-limits.md) - Coordinate tool calls across concurrent agents
- [MCP Server Reliability](03-mcp-reliability.md) - Build self-healing tool backends
- [Cost Attribution System](09-cost-attribution.md) - Track token usage per feature
- [Progressive Enhancement](10-progressive-enhancement.md) - Roll out advanced features safely
