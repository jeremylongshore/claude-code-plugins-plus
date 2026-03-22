# clade-model-inference — One-Pager

Stream Claude responses, send images, and extract structured JSON output via the Messages API.

## The Problem

The Anthropic Messages API is the single inference endpoint for all Claude interactions, but it supports multiple interaction patterns (streaming, vision, structured output) that each require different request shapes and event handling. Developers need to understand streaming event types, image encoding requirements, and JSON extraction techniques to build production features.

## The Solution

This skill covers the three core Messages API patterns: streaming responses with event-by-event processing, sending images via base64 encoding for vision tasks, and extracting structured JSON output using system prompt constraints. Includes both TypeScript and Python examples with complete parameter reference.

## Who / What / When

| Aspect | Details |
|--------|---------|
| **Who** | Developers building features on top of Claude's Messages API |
| **What** | Implements streaming, vision (image input), and structured JSON output patterns |
| **When** | After initial SDK setup, when building real features that need streaming UX, image analysis, or typed responses |

## Key Features

1. **Streaming with Event Handling** — Process content_block_delta events for real-time text display with final usage stats via finalMessage()
2. **Vision / Image Input** — Send base64-encoded images (PNG, JPEG, GIF, WebP up to 5MB) alongside text prompts for multimodal analysis
3. **Structured JSON Output** — Extract typed data using system prompt schema constraints with JSON.parse on the response

## Quick Start

See [SKILL.md](../SKILL.md) for full instructions.
