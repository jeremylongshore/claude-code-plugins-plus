---
name: deepgram-performance-tuning
description: |
  Optimize Deepgram API performance for faster transcription and lower latency.
  Use when improving transcription speed, reducing latency,
  or optimizing audio processing pipelines.
  Trigger with phrases like "deepgram performance", "speed up deepgram",
  "optimize transcription", "deepgram latency", "deepgram faster".
allowed-tools: Read, Write, Edit, Bash(gh:*), Bash(curl:*)
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code, codex, openclaw
---
# Deepgram Performance Tuning

## Contents
- [Overview](#overview)
- [Prerequisites](#prerequisites)
- [Instructions](#instructions)
- [Output](#output)
- [Error Handling](#error-handling)
- [Examples](#examples)
- [Resources](#resources)

## Overview
Optimize Deepgram integration performance through audio preprocessing (16kHz mono PCM), connection pooling, model selection, streaming for large files, parallel processing, and result caching.

## Prerequisites
- Working Deepgram integration
- Performance monitoring in place
- Audio processing capabilities (ffmpeg)
- Baseline metrics established

## Instructions

### Step 1: Optimize Audio Format
Preprocess audio to 16-bit PCM, mono channel, 16kHz sample rate WAV format using ffmpeg. This is optimal for Deepgram's speech models.

### Step 2: Configure Connection Pooling
Create a pool of Deepgram clients (min 2, max 10) with acquire timeout and idle timeout. Use `execute()` pattern to auto-acquire and release connections.

### Step 3: Select Optimal Model
Choose Nova-2 for best accuracy/speed balance. Use Base model for cost-sensitive batch jobs. Match model to priority: accuracy, speed, or cost.

### Step 4: Implement Streaming for Large Files
Use live transcription WebSocket for files over 60 seconds. Stream file data in chunks (1MB) and collect final transcripts.

### Step 5: Enable Parallel Processing
Use p-limit to process multiple audio files concurrently (default 5). Track per-file timing and total throughput.

### Step 6: Cache Transcription Results
Hash audio URL + options as cache key. Store in Redis with configurable TTL. Return cached results for repeated requests.

See [detailed implementation](${CLAUDE_SKILL_DIR}/references/implementation.md) for advanced patterns.

## Output
- Audio preprocessing pipeline
- Connection pool with auto-management
- Model selection engine
- Streaming transcription for large files
- Parallel processing with concurrency control
- Redis-backed result caching

## Error Handling
| Issue | Cause | Solution |
|-------|-------|----------|
| Slow transcription | Wrong audio format | Preprocess to 16kHz mono WAV |
| Connection exhaustion | No pooling | Use connection pool |
| High latency | Large files | Switch to streaming |
| Redundant API calls | No caching | Enable transcription cache |

## Examples

### Performance Factors
| Factor | Impact | Optimization |
|--------|--------|--------------|
| Audio Format | High | 16-bit PCM, mono, 16kHz |
| File Size | High | Stream large files |
| Model Choice | High | Balance accuracy vs speed |
| Concurrency | Medium | Pool connections |
| Network Latency | Medium | Use closest region |

## Resources
- [Deepgram Performance Guide](https://developers.deepgram.com/docs/performance-guide)
- [Audio Format Best Practices](https://developers.deepgram.com/docs/audio-best-practices)
- [FFmpeg Documentation](https://ffmpeg.org/documentation.html)