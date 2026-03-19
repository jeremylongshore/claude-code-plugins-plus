---
name: twinmind-migration-deep-dive
description: |
  Comprehensive migration guide from other meeting AI tools to TwinMind.
  Use when migrating from Otter.ai, Fireflies, Rev, or other transcription services.
  Trigger with phrases like "migrate to twinmind", "switch from otter",
  "twinmind migration", "move to twinmind", "replace fireflies".
allowed-tools: Read, Write, Edit, Bash(npm:*), Grep
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code, codex, openclaw
---
# TwinMind Migration Deep Dive

## Current State
!`npm list 2>/dev/null | head -20`
!`pip freeze 2>/dev/null | head -20`

## Contents
- [Overview](#overview)
- [Prerequisites](#prerequisites)
- [Instructions](#instructions)
- [Output](#output)
- [Error Handling](#error-handling)
- [Examples](#examples)
- [Resources](#resources)

## Overview
Comprehensive guide for migrating from Otter.ai, Fireflies.ai, Rev.ai, Zoom, Google Meet, Teams, and other meeting AI services to TwinMind. Covers assessment, export, transformation, import, and verification.

## Prerequisites
- TwinMind Pro/Enterprise account
- Export access on source platform
- Understanding of data formats
- Sufficient storage for migration data

## Instructions

### Step 1: Assess Current Data
Build a migration assessment script that scans exported files, counts transcripts, calculates total duration hours, identifies date range and data formats, estimates migration time, and flags potential issues.

### Step 2: Export Data from Source
Use platform-specific exporters: Otter.ai (via Puppeteer web scraping), Fireflies.ai (GraphQL API), Rev.ai (REST API with transcript retrieval), Zoom (VTT file parsing).

### Step 3: Transform Data to TwinMind Format
Build transformer functions per source: `transformOtterToTwinMind()`, `transformFirefliesToTwinMind()`, `transformRevToTwinMind()`, `transformZoomVTTToTwinMind()`. Map speakers, segments, timestamps, and metadata to TwinMind's `Transcript` schema.

### Step 4: Import to TwinMind
Create batch import with configurable batch size, rate limit delays, duplicate detection (by original_id metadata), and progress logging.

### Step 5: Verify Migration
Run verification comparing source vs imported counts, spot-checking content (word count within 10%), validating duration accuracy, and identifying missing transcripts.

See [detailed implementation](${CLAUDE_SKILL_DIR}/references/implementation.md) for complete assessment script, platform exporters, transformers, batch importer, and verification code.

## Output
- Migration assessment tool
- Platform-specific exporters
- Data transformation functions
- TwinMind import utility
- Verification scripts

## Error Handling

| Issue | Cause | Solution |
|-------|-------|----------|
| Export rate limited | Too many requests | Add delays between requests |
| Data format changed | API version update | Update transformer functions |
| Import duplicate | Already migrated | Skip or overwrite (dedup by original_id) |
| Missing speakers | Source didn't export | Set as "unknown" |

## Examples


**Basic usage**: Apply twinmind migration deep dive to a standard project setup with default configuration options.

**Advanced scenario**: Customize twinmind migration deep dive for production environments with multiple constraints and team-specific requirements.

## Platform Comparison

| Feature | TwinMind | Otter.ai | Fireflies |
|---------|----------|----------|-----------|
| WER | 5.26% | ~8% | ~7% |
| Languages | 140+ | 30+ | 60+ |
| On-device | Yes | No | No |
| No audio storage | Yes | No | No |

## Resources
- [TwinMind Import API](https://twinmind.com/docs/import)
- [Data Export Best Practices](https://twinmind.com/docs/migration)
- [Platform Comparison](https://twinmind.com/compare)

## Congratulations!
You have completed the TwinMind skill pack.