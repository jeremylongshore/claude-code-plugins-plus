# clade-core-workflow-b — One-Pager

Entry point that routes you to the secondary Claude workflow: tool use and function calling.

## The Problem

Tool use (function calling) is the second most important Claude integration pattern after basic message creation, but it lives in a separate skill. Developers searching for "anthropic tools" or "claude function calling" need a clear pointer to the right place without wading through unrelated content.

## The Solution

This skill acts as a redirect to `clade-embeddings-search`, which contains the complete tool use guide. It lists exactly what that skill covers: defining tools with JSON Schema, sending tool-enabled messages, executing tool calls, building agentic loops, and handling tool use edge cases. A quick example shows the tool definition format so you can confirm you are looking for the right thing.

## Who / What / When

| Aspect | Details |
|--------|---------|
| **Who** | Developers looking to implement tool use or function calling with Claude |
| **What** | Redirect to `clade-embeddings-search` for tool definitions, agentic loops, and tool result handling |
| **When** | When you search for "anthropic tools" or "claude function calling" and need to find the right skill |

## Key Features

1. **Clear redirect** — Points directly to `clade-embeddings-search` as the canonical tool use skill
2. **Topic index** — Lists covered topics: JSON Schema tool definitions, tool execution, agentic loops, error handling
3. **Quick example** — Includes a minimal tool definition and `messages.create` call with tools to orient you

## Quick Start

See [SKILL.md](../SKILL.md) for full instructions.
