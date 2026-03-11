---
name: klingai-batch-processing
description: |
  Process multiple video generation requests efficiently with Kling AI. Use when generating
  multiple videos or building content pipelines. Trigger with phrases like 'klingai batch',
  'kling ai bulk', 'multiple videos klingai', 'klingai parallel generation'.
allowed-tools: Read, Write, Edit, Grep
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code, codex, openclaw
---
# Klingai Batch Processing

## Overview

This skill teaches efficient batch processing patterns for generating multiple videos, including parallel submission, progress tracking, rate limit management, and result collection.

## Prerequisites

- Kling AI API key with sufficient credits
- Python 3.8+ with asyncio support
- Understanding of async/await patterns

## Instructions

Follow these steps for batch processing:

1. **Prepare Batch**: Collect all prompts and parameters
2. **Rate Limit Planning**: Calculate submission pace
3. **Parallel Submission**: Submit jobs within limits
4. **Track Progress**: Monitor all jobs simultaneously
5. **Collect Results**: Gather outputs and handle failures

## Output

Successful execution produces:
- Parallel job submission within rate limits
- Real-time progress tracking
- Collected results with success/failure status
- Performance metrics (duration, throughput)

## Error Handling

See `${CLAUDE_SKILL_DIR}/references/errors.md` for comprehensive error handling.

## Examples

See `${CLAUDE_SKILL_DIR}/references/examples.md` for detailed examples.

## Resources

- [Kling AI Batch API](https://docs.klingai.com/batch)
- [Python asyncio](https://docs.python.org/3/library/asyncio.html)
- [aiohttp Documentation](https://docs.aiohttp.org/)