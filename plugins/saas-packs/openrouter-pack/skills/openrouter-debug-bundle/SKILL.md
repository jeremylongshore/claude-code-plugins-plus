---
name: openrouter-debug-bundle
description: |
  Create debug bundles for troubleshooting OpenRouter issues. Use when diagnosing API failures or unexpected behavior. Trigger with phrases like 'openrouter debug', 'openrouter troubleshoot', 'debug openrouter', 'openrouter issue'.
allowed-tools: Read, Write, Edit, Grep
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code, codex, openclaw
---
# Openrouter Debug Bundle

## Current State
!`node --version 2>/dev/null || echo 'N/A'`
!`python3 --version 2>/dev/null || echo 'N/A'`
!`uname -a`

## Overview

This skill provides a systematic approach to collecting diagnostic information when OpenRouter requests fail or return unexpected results.

## Prerequisites

- OpenRouter integration with logging enabled
- Access to request/response logs

## Instructions

1. **Capture the full request**: Log the complete request including URL, headers (redact the API key), body, model ID, and timestamp
2. **Capture the full response**: Log status code, response headers (especially `X-Request-ID`, rate limit headers), response body, and response time
3. **Check the generation ID**: Extract the `id` field from the response (e.g., `gen-abc123`) — this is needed when contacting OpenRouter support
4. **Compare against a known-good request**: Diff the failing request against a previously successful one to isolate what changed
5. **Bundle and report**: Package the sanitized request, response, error message, and environment info (SDK version, Node/Python version) into a debug report

## Output

- A structured debug bundle with request, response, and environment metadata
- Isolated diff showing what changed between working and failing requests
- Actionable next steps based on the error pattern

## Error Handling

| Error | Cause | Fix |
|-------|-------|-----|
| No request ID in response | Request failed before reaching OpenRouter | Check network connectivity; verify base URL is correct |
| Intermittent failures | Model provider instability | Log timestamps and correlate with OpenRouter status page; try a different provider |
| Response differs from docs | Model-specific behavior variation | Check the specific model's documentation; some models handle parameters differently |

See `${CLAUDE_SKILL_DIR}/references/errors.md` for full error reference.

## Examples

See `${CLAUDE_SKILL_DIR}/references/examples.md` for runnable code samples.

## Resources

- [OpenRouter Documentation](https://openrouter.ai/docs)
- [OpenRouter Models](https://openrouter.ai/models)
- [OpenRouter API Reference](https://openrouter.ai/docs/api-reference)
- [OpenRouter Status](https://status.openrouter.ai)
