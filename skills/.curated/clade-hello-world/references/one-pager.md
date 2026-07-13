# clade-hello-world — One-Pager

Send your first message to Claude and get a response using the Messages API.

## The Problem

Getting started with the Anthropic API involves understanding the Messages API structure — which parameters are required, how system prompts work differently from other LLM APIs, and how to build multi-turn conversations. The official docs are comprehensive but scattered across multiple pages.

## The Solution

This skill provides a three-step progression from a basic single message, to adding a system prompt, to building a multi-turn conversation — with complete TypeScript and Python examples. It also documents the response object fields and lists all available models with pricing.

## Who / What / When

| Aspect | Details |
|--------|---------|
| **Who** | Developers new to the Anthropic API or evaluating Claude for a project |
| **What** | Working code for basic messages, system prompts, and multi-turn conversations in TypeScript and Python |
| **When** | After completing `clade-install-auth` setup, when you want to verify your integration works and learn the API basics |

## Key Features

1. **Basic Message Call** — Minimal `messages.create()` call with model, max_tokens, and messages — the three required parameters
2. **System Prompt and Multi-Turn** — Shows the top-level `system` parameter (not a message role) and how to build conversations with alternating user/assistant messages
3. **Model Reference Table** — All current Claude models with context window sizes and per-token pricing for quick selection

## Quick Start

See [SKILL.md](../SKILL.md) for full instructions.
