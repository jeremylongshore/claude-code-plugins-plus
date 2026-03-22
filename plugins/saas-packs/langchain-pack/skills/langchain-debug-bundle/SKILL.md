---
name: langchain-debug-bundle
description: |
  Collect LangChain debug evidence for troubleshooting and bug reports.
  Use when preparing GitHub issues, collecting LangSmith traces,
  or gathering diagnostic info for complex LangChain failures.
  Trigger: "langchain debug bundle", "langchain diagnostics",
  "langchain support info", "collect langchain logs", "langchain trace".
allowed-tools: Read, Write, Edit, Bash(node:*), Bash(npm:*), Bash(python:*), Grep
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code, codex, openclaw
tags: [saas, langchain, debugging]

---
# LangChain Debug Bundle

## Current State

!`node --version 2>/dev/null || echo 'N/A'`
!`python3 --version 2>/dev/null || echo 'N/A'`

## Overview

Collect comprehensive diagnostic information for LangChain issues: environment info, dependency versions, chain execution traces, and minimal reproduction scripts.

## Step 1: Environment Snapshot

```typescript
import { execSync } from "child_process";
import * as fs from "fs";

function collectEnvironment() {
  const env: Record<string, string> = {};

  env.nodeVersion = process.version;
  env.platform = `${process.platform} ${process.arch}`;

  // Get @langchain/* versions
  try {
    const pkg = JSON.parse(fs.readFileSync("package.json", "utf-8"));
    const deps = { ...pkg.dependencies, ...pkg.devDependencies };
    for (const [name, version] of Object.entries(deps)) {
      if (name.startsWith("@langchain") || name === "langchain") {
        env[name] = version as string;
      }
    }
  } catch {}

  // Check env vars (redacted)
  env.OPENAI_API_KEY = process.env.OPENAI_API_KEY ? "set (redacted)" : "NOT SET";
  env.ANTHROPIC_API_KEY = process.env.ANTHROPIC_API_KEY ? "set (redacted)" : "NOT SET";
  env.LANGSMITH_TRACING = process.env.LANGSMITH_TRACING ?? "NOT SET";

  return env;
}
```

## Step 2: Trace Callback for Evidence Collection

```typescript
import { BaseCallbackHandler } from "@langchain/core/callbacks/base";

interface TraceEvent {
  timestamp: string;
  event: string;
  data: Record<string, any>;
}

class DebugTraceHandler extends BaseCallbackHandler {
  name = "DebugTraceHandler";
  events: TraceEvent[] = [];

  private log(event: string, data: Record<string, any>) {
    this.events.push({
      timestamp: new Date().toISOString(),
      event,
      data,
    });
  }

  handleLLMStart(llm: any, prompts: string[]) {
    this.log("llm_start", {
      model: llm?.id?.[2] ?? "unknown",
      promptCount: prompts.length,
      firstPromptLength: prompts[0]?.length ?? 0,
    });
  }

  handleLLMEnd(output: any) {
    this.log("llm_end", {
      generations: output.generations?.length ?? 0,
      tokenUsage: output.llmOutput?.tokenUsage ?? null,
    });
  }

  handleLLMError(error: Error) {
    this.log("llm_error", {
      name: error.name,
      message: error.message,
      stack: error.stack?.split("\n").slice(0, 5).join("\n"),
    });
  }

  handleToolStart(_tool: any, input: string) {
    this.log("tool_start", { input: input.slice(0, 200) });
  }

  handleToolEnd(output: string) {
    this.log("tool_end", { output: output.slice(0, 200) });
  }

  handleToolError(error: Error) {
    this.log("tool_error", { name: error.name, message: error.message });
  }

  toJSON() {
    return JSON.stringify(this.events, null, 2);
  }
}
```

## Step 3: Generate Debug Bundle

```typescript
import * as fs from "fs";

async function generateDebugBundle(
  chain: any,
  testInput: Record<string, any>,
  outputPath = "debug_bundle.json",
) {
  const tracer = new DebugTraceHandler();
  const env = collectEnvironment();
  let result: any = null;
  let error: any = null;

  try {
    result = await chain.invoke(testInput, { callbacks: [tracer] });
  } catch (e: any) {
    error = {
      name: e.name,
      message: e.message,
      stack: e.stack?.split("\n").slice(0, 10).join("\n"),
    };
  }

  const bundle = {
    generatedAt: new Date().toISOString(),
    environment: env,
    input: testInput,
    result: result ? "(success)" : null,
    error,
    traceEvents: tracer.events,
    eventCount: tracer.events.length,
  };

  fs.writeFileSync(outputPath, JSON.stringify(bundle, null, 2));
  console.log(`Debug bundle written to ${outputPath}`);
  console.log(`  Events captured: ${tracer.events.length}`);
  console.log(`  Status: ${error ? "FAILED" : "SUCCESS"}`);

  return bundle;
}

// Usage:
// await generateDebugBundle(myChain, { input: "test query" });
```

## Step 4: Minimal Reproduction Template

```typescript
// Save as minimal_repro.ts
// Run: npx tsx minimal_repro.ts
import "dotenv/config";
import { ChatOpenAI } from "@langchain/openai";
import { ChatPromptTemplate } from "@langchain/core/prompts";
import { StringOutputParser } from "@langchain/core/output_parsers";

const model = new ChatOpenAI({ model: "gpt-4o-mini" });
const prompt = ChatPromptTemplate.fromTemplate("{input}");
const chain = prompt.pipe(model).pipe(new StringOutputParser());

try {
  const result = await chain.invoke({ input: "Hello" });
  console.log("SUCCESS:", result);
} catch (error) {
  console.error("FAILED:", error);
}
```

## Step 5: LangSmith Trace Export

```bash
# Export traces from LangSmith for a specific project
# pip install langsmith
python3 -c "
from langsmith import Client
import json

client = Client()
runs = list(client.list_runs(
    project_name='my-project',
    execution_order=1,
    limit=10,
    error=True,  # only failed runs
))

for run in runs:
    print(json.dumps({
        'id': str(run.id),
        'name': run.name,
        'status': run.status,
        'error': run.error,
        'start': str(run.start_time),
        'latency': str(run.end_time - run.start_time) if run.end_time else None,
        'tokens': run.total_tokens,
    }, indent=2))
"
```

## How to File a Good Bug Report

Include in your GitHub issue:

1. **Environment** (from Step 1 output)
2. **Minimal reproduction** (from Step 4)
3. **Debug bundle** (from Step 3) -- remove any sensitive data
4. **Expected vs actual behavior**
5. **LangSmith trace link** (if available)

## Error Handling

| Issue | Cause | Fix |
|-------|-------|-----|
| Callback not capturing events | Not passed to invoke | Use `{ callbacks: [tracer] }` as second arg |
| API key in bundle | Missing redaction | Filter env vars before export |
| Large trace file | Long-running chain | Filter events by time range |

## Resources

- [LangChain GitHub Issues](https://github.com/langchain-ai/langchainjs/issues)
- [LangSmith Tracing](https://docs.smith.langchain.com/)
- [LangChain Discord](https://discord.gg/langchain)

## Next Steps

Use `langchain-common-errors` for quick fixes or escalate with the debug bundle.
