# clade-debug-bundle — One-Pager

Collect all the evidence Anthropic support needs in one structured bundle.

## The Problem

When something goes wrong with the Anthropic API, filing a support ticket without the right details leads to slow back-and-forth. Teams waste time hunting for request IDs, reproducing errors, and figuring out whether the issue is on their side or Anthropic's.

## The Solution

This skill walks you through a four-step debug collection process: extract the request ID from error headers, log a full error bundle (timestamp, status, rate limit state), build a minimal curl reproduction, and check the Anthropic status page — all ready to paste into a support ticket.

## Who / What / When

| Aspect | Details |
|--------|---------|
| **Who** | Backend developers and SREs integrating with the Claude API |
| **What** | Extracts request IDs, error payloads, rate limit headers, and builds curl reproductions |
| **When** | When you hit a persistent or unexplained API error and need to file a support ticket or escalate |

## Key Features

1. **Request ID Extraction** — Pulls the `request-id` header from both `APIError` exceptions (TypeScript/Python) so support can trace your exact call
2. **Structured Error Bundle** — Logs timestamp, status code, error type, message, and rate limit state in a single JSON object
3. **curl Reproduction** — Generates a ready-to-paste curl command that reproduces the issue without exposing your full codebase
4. **Status Page Check** — Queries `status.anthropic.com` API to confirm whether the issue is a known incident

## Quick Start

See [SKILL.md](../SKILL.md) for full instructions.
