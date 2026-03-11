---
name: klingai-job-monitoring
description: |
  Monitor and track Kling AI video generation jobs. Use when managing multiple generations or
  building job dashboards. Trigger with phrases like 'klingai job status', 'track klingai jobs',
  'kling ai monitoring', 'klingai job queue'.
allowed-tools: Read, Write, Edit, Grep
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code, codex, openclaw
---
# Klingai Job Monitoring

## Overview

This skill covers job status tracking, progress monitoring, webhook notifications, and building dashboards to manage multiple concurrent video generation jobs.

## Prerequisites

- Kling AI API key configured
- Multiple concurrent jobs to track
- Python 3.8+ or Node.js 18+

## Instructions

Follow these steps to monitor jobs:

1. **Track Job Submission**: Record job IDs and metadata
2. **Poll for Status**: Implement efficient status polling
3. **Handle State Changes**: React to status transitions
4. **Build Dashboard**: Create monitoring interface
5. **Set Up Alerts**: Configure notifications

## Output

Successful execution produces:
- Real-time job status updates
- Progress tracking dashboard
- Status change notifications
- Batch completion monitoring

## Error Handling

See `${CLAUDE_SKILL_DIR}/references/errors.md` for comprehensive error handling.

## Examples

See `${CLAUDE_SKILL_DIR}/references/examples.md` for detailed examples.

## Resources

- [Kling AI Job API](https://docs.klingai.com/api/jobs)
- [Rich Library](https://rich.readthedocs.io/)
- [Async Monitoring Patterns](https://docs.python.org/3/library/asyncio.html)