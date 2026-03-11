---
name: twinmind-performance-tuning
description: |
  Optimize TwinMind transcription accuracy and processing speed.
  Use when improving transcription quality, reducing latency,
  or tuning model parameters for specific use cases.
  Trigger with phrases like "twinmind performance", "improve transcription accuracy",
  "faster twinmind", "optimize twinmind", "transcription quality".
allowed-tools: Read, Write, Edit
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code, codex, openclaw
---
# TwinMind Performance Tuning

## Contents
- [Overview](#overview)
- [Prerequisites](#prerequisites)
- [Instructions](#instructions)
- [Output](#output)
- [Error Handling](#error-handling)
- [Examples](#examples)
- [Resources](#resources)

## Overview
Optimize TwinMind for better transcription accuracy (WER), faster processing, audio preprocessing, model selection per use case, streaming optimization, and transcript caching/deduplication.

## Prerequisites
- TwinMind Pro/Enterprise account
- Understanding of audio processing concepts
- Access to quality metrics and logs

## Instructions

### Step 1: Understand Performance Metrics
Track key metrics: Word Error Rate (Ear-3: ~5.26%), Diarization Error Rate (~3.8%), confidence score, processing time, real-time factor (~0.3x), and first word latency (~300ms). Analyze metrics to generate recommendations.

### Step 2: Audio Quality Optimization
Build preprocessing pipeline with ffmpeg: target 16kHz sample rate, mono channel, noise reduction (highpass 200Hz + lowpass 3kHz + FFT denoiser), and EBU R128 loudness normalization. Assess audio quality before transcription.

### Step 3: Model Selection and Configuration
Create optimized configs per scenario: standard meeting (ear-3, auto language, diarization on), technical presentation (ear-3 + custom vocabulary), call center (diarization + profanity filter), medical (ear-3-custom), lecture (single speaker, no diarization), podcast (diarization on).

### Step 4: Streaming Optimization
Configure streaming with 100ms chunks, 50ms overlap, 5s max buffer, interim results, and endpoint detection. Build `OptimizedStreamingClient` that accumulates chunks and processes when sufficient data is available.

### Step 5: Caching and Deduplication
Implement `TranscriptCache` with SHA-256 audio hashing for deduplication, 24-hour TTL, and `transcribeWithCache()` that skips re-processing of identical audio.

See [detailed implementation](${CLAUDE_SKILL_DIR}/references/implementation.md) for complete audio preprocessing, model configs, streaming client, and caching code.

## Output
- Performance metrics tracking
- Audio preprocessing pipeline
- Model configuration for use cases
- Streaming optimization
- Caching and deduplication

## Error Handling

| Issue | Cause | Solution |
|-------|-------|----------|
| High WER | Poor audio quality | Apply preprocessing pipeline |
| Slow processing | Large file | Use streaming API |
| Wrong language | Auto-detect failed | Specify language explicitly |
| Missing speakers | Low audio separation | Improve microphone setup |

## Examples


**Basic usage**: Apply twinmind performance tuning to a standard project setup with default configuration options.

**Advanced scenario**: Customize twinmind performance tuning for production environments with multiple constraints and team-specific requirements.

## Performance Benchmarks

| Metric | Target | Ear-3 Actual |
|--------|--------|--------------|
| Word Error Rate | < 10% | ~5.26% |
| Diarization Error Rate | < 5% | ~3.8% |
| Real-time Factor | < 0.5x | ~0.3x |
| First Word Latency | < 500ms | ~300ms |
| Languages | 100+ | 140+ |

## Resources
- [TwinMind Ear-3 Model](https://twinmind.com/ear-3)
- [Audio Best Practices](https://twinmind.com/docs/audio-quality)
- [Streaming API](https://twinmind.com/docs/streaming)

## Next Steps
For cost optimization, see `twinmind-cost-tuning`.