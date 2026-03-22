---
name: wispr-webhooks-events
description: |
  Wispr Flow webhooks events for voice-to-text API integration.
  Use when integrating Wispr Flow dictation, WebSocket streaming,
  or building voice-powered applications.
  Trigger: "wispr webhooks events".
allowed-tools: Read, Write, Edit, Bash(npm:*), Grep
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
tags: [saas, voice, dictation, wispr]
compatible-with: claude-code
---

# Wispr Flow Webhooks Events

## Overview

Guidance for webhooks events with Wispr Flow voice-to-text API.

## Instructions

### Key Wispr Flow Concepts

- **WebSocket API**: `wss://api.wisprflow.ai/api/v1/ws` (recommended, low latency)
- **REST API**: `POST /api/v1/transcribe` (simpler, higher latency)
- **Auth**: API key (backend) or access token (client-side)
- **Audio format**: 16kHz mono PCM preferred
- **Context awareness**: Understands code, CLI commands, dev jargon
- **Platforms**: Mac, Windows, iOS, browser API

## Error Handling

| Error | Cause | Solution |
|-------|-------|----------|
| `401 Unauthorized` | Invalid key | Check at wisprflow.ai/developers |
| WebSocket closed | Network issue | Reconnect with backoff |
| Poor accuracy | Wrong context | Set context to 'programming' for code |

## Resources

- [Wispr Flow Developers](https://wisprflow.ai/developers)
- [API Docs](https://api-docs.wisprflow.ai/introduction)
- [WebSocket Quickstart](https://api-docs.wisprflow.ai/websocket_quickstart)

## Next Steps

See related Wispr Flow skills for more patterns.
