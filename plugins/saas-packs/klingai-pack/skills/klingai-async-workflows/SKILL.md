---
name: klingai-async-workflows
description: |
  Build asynchronous video generation workflows with Kling AI. Use when integrating video
  generation into larger systems or pipelines. Trigger with phrases like 'klingai async',
  'kling ai workflow', 'klingai pipeline', 'async video generation'.
allowed-tools: Read, Write, Edit, Grep
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code, codex, openclaw
---
# Klingai Async Workflows

## Overview

This skill demonstrates building asynchronous workflows for video generation, including job queues, state machines, event-driven processing, and integration with workflow orchestration systems.

## Prerequisites

- Kling AI API key configured
- Python 3.8+ or Node.js 18+
- Message queue (Redis, RabbitMQ) or workflow engine

## Instructions

Follow these steps to build async workflows:

1. **Design Workflow**: Map out the video generation pipeline
2. **Implement Queue**: Set up job queue for async processing
3. **Create Workers**: Build workers to process jobs
4. **Handle States**: Manage job state transitions
5. **Add Monitoring**: Track workflow progress

## Output

Successful execution produces:
- Validated and queued workflow jobs
- State machine driven processing
- Complete audit trail of transitions
- Reliable job completion or failure handling

## Error Handling

See `${CLAUDE_SKILL_DIR}/references/errors.md` for comprehensive error handling.

## Examples

See `${CLAUDE_SKILL_DIR}/references/examples.md` for detailed examples.

## Resources

- [Kling AI API](https://docs.klingai.com/api)
- [Redis Queues](https://redis.io/docs/data-types/lists/)
- [State Machine Patterns](https://python-statemachine.readthedocs.io/)