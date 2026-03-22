# clade-webhooks-events — One-Pager

Async bulk processing with Anthropic's Message Batches API.

## The Problem

Processing thousands of prompts synchronously through the Claude API is slow, expensive, and rate-limited. Anthropic doesn't offer traditional webhooks for async completion notifications, so developers need a different pattern for bulk workloads like document summarization, content moderation, or data extraction at scale.

## The Solution

Use the Message Batches API to submit up to 10,000 requests per batch at 50% of standard pricing, with a 24-hour processing SLA. The workflow is: create the batch with custom IDs for each request, poll for completion status, then stream results with per-request success/error/expired status. Both TypeScript and Python implementations are provided.

## Who / What / When

| Aspect | Details |
|--------|---------|
| **Who** | Engineers processing large document sets, running bulk classification, or doing batch content generation |
| **What** | Batch creation, polling for completion, result retrieval with error handling, Python and TypeScript examples |
| **When** | When you have 100+ prompts to process and can tolerate async results (up to 24 hours) |

## Key Features

1. **50% cost savings** — Batch pricing is half of standard per-token pricing, with up to 10,000 requests per batch and 100 concurrent batches
2. **Full lifecycle management** — Create with `custom_id` tracking, poll via `processing_status`, retrieve with `for await...of` streaming, and handle `succeeded`/`errored`/`expired`/`canceled` result types
3. **Dual-language examples** — Complete TypeScript and Python implementations covering batch creation, polling loops, and result iteration with error handling

## Quick Start

See [SKILL.md](../SKILL.md) for full instructions.
