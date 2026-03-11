---
name: klingai-storage-integration
description: |
  Execute integrate Kling AI video output with cloud storage providers. Use when storing generated
  videos in S3, GCS, or Azure Blob. Trigger with phrases like 'klingai storage', 'save klingai video',
  'kling ai cloud storage', 'klingai s3 upload'.
allowed-tools: Read, Write, Edit, Grep
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code, codex, openclaw
---

# Klingai Storage Integration

## Overview

This skill demonstrates how to download and store generated videos in cloud storage services including AWS S3, Google Cloud Storage, and Azure Blob Storage.

## Prerequisites

- Kling AI API key configured
- Cloud storage credentials (AWS, GCP, or Azure)
- Python 3.8+ with cloud SDKs installed

## Instructions

Follow these steps to integrate storage:

1. **Configure Storage**: Set up cloud storage credentials
2. **Download Video**: Fetch generated video from Kling AI
3. **Upload to Cloud**: Store in your preferred provider
4. **Generate URLs**: Create access URLs (signed or public)
5. **Clean Up**: Remove temporary files

## Output

Successful execution produces:
- Downloaded video from Kling AI
- Uploaded to cloud storage
- Metadata preserved with video
- Signed URLs for secure access

## Error Handling

See `${CLAUDE_SKILL_DIR}/references/errors.md` for comprehensive error handling.

## Examples

See `${CLAUDE_SKILL_DIR}/references/examples.md` for detailed examples.

## Resources

- [AWS S3 SDK](https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/s3.html)
- [Google Cloud Storage](https://cloud.google.com/storage/docs)
- [Azure Blob Storage](https://docs.microsoft.com/en-us/azure/storage/blobs/)
