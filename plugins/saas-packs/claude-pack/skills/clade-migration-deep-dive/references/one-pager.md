# clade-migration-deep-dive — One-Pager

Migrate from OpenAI/GPT to Anthropic/Claude with a complete API mapping and SDK swap guide.

## The Problem

Switching from OpenAI to Anthropic is not a drop-in replacement. The APIs differ in request shape (max_tokens is required, system is a top-level param), response shape (content[0].text vs choices[0].message.content), message ordering rules, streaming event types, and tool definition format. Missing any of these differences causes silent bugs or runtime errors.

## The Solution

This skill provides a complete mapping between OpenAI and Anthropic APIs, side-by-side before/after SDK code, a checklist of six key differences to address, tool use migration patterns, and grep commands to find all OpenAI-specific code in your codebase that needs updating.

## Who / What / When

| Aspect | Details |
|--------|---------|
| **Who** | Developers migrating existing OpenAI/GPT integrations to Anthropic/Claude |
| **What** | Maps API endpoints, rewrites SDK calls, restructures tool definitions, and finds all code that needs updating |
| **When** | When switching an existing project from OpenAI to Anthropic, or evaluating the migration effort |

## Key Features

1. **Full API Mapping Table** — Side-by-side comparison of every OpenAI endpoint, model ID, and response path to its Anthropic equivalent
2. **Before/After SDK Code** — Copy-pasteable TypeScript showing the exact import, client, and response access pattern changes
3. **Grep-and-Replace Commands** — Ready-to-run grep commands that find all OpenAI imports, response patterns, and tool definitions in your codebase

## Quick Start

See [SKILL.md](../SKILL.md) for full instructions.
