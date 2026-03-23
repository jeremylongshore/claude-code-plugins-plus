# clade-embeddings-search — One-Pager

Implement Claude tool use (function calling) so Claude can query databases, call APIs, and take actions.

## The Problem

Out of the box, Claude can only generate text. It cannot look up live data, execute code, or interact with external systems. Developers need a structured way to let Claude decide when to call a function and how to feed results back into the conversation.

## The Solution

This skill covers Anthropic's tool use API end-to-end: defining tools with JSON Schema, sending messages with tools attached, executing tool calls, returning results, and building a full agentic loop that keeps calling Claude until all tool requests are resolved. Includes TypeScript and Python examples.

## Who / What / When

| Aspect | Details |
|--------|---------|
| **Who** | Developers building Claude-powered agents or any integration that needs Claude to interact with external systems |
| **What** | Tool definitions, tool_use/tool_result message flow, and a complete agentic loop pattern |
| **When** | When Claude needs to call functions — query a database, hit an API, do math, or take actions based on user input |

## Key Features

1. **Tool Definition with JSON Schema** — Declare tools with name, description, and `input_schema` so Claude knows when and how to call them
2. **Tool Result Round-Trip** — Full message flow showing how to execute a tool call and feed the result back with the correct `tool_use_id`
3. **Agentic Tool Loop** — A while-loop pattern that keeps calling Claude until `stop_reason` is `end_turn`, handling multiple sequential tool calls automatically

## Quick Start

See [SKILL.md](../SKILL.md) for full instructions.
