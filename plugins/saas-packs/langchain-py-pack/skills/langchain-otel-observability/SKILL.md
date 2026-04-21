---
name: langchain-otel-observability
description: |
  Analyze, implement, and verify Native OTEL export, Jaeger/Honeycomb config, LLM-specific SLO dashboards against LangChain 1.0.x baseline.
  Use when you need to native otel export.
  Trigger with "langchain otel observability", "langchain python otel observability", "otel observability".
allowed-tools: Read, Write, Edit, Bash(python:*)
version: 2.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
tags: [saas, langchain, langgraph, python, langchain-1.0]
compatible-with: claude-code, codex
---

# Langchain Otel Observability

## Overview

This skill covers: native otel export, jaeger/honeycomb config, llm-specific slo dashboards. The full v2.0 treatment will open with P27 from the pain catalog — a real production failure mode — and walk through the exact fix with code pinned to LangChain 1.0.x.

Baseline: `langchain-core 1.0.x`, `langgraph 1.0.x`. Pain-catalog anchors: `P27`, `P28`
(defined in the pack-level `docs/pain-catalog.md` — read that file first to ground
yourself in the specific failure modes this skill addresses before extending it).

Expanded content ships in a later v2.0 epic. This scaffold exists so the pack directory
is present and the marketplace catalog validates end-to-end while the full treatment
is authored.

## Prerequisites

- Python 3.10+
- `langchain-core >= 1.0, < 2.0` and `langgraph >= 1.0, < 2.0` installed
- Provider package for your model (`langchain-anthropic`, `langchain-openai`, etc.)

## Instructions

Detailed step-by-step instructions are authored in the next epic. For now, read the
pack `README.md` for the quickstart and the pain-catalog entries listed above for the
specific failure modes this skill targets.

## Output

Working code that addresses the linked pain-catalog entries, verified against
`langchain-core 1.0.x` and `langgraph 1.0.x`.

## Error Handling

Shared error patterns are covered in `langchain-common-errors`. Skill-specific
error tables land alongside the full skill content in the next epic.

## Examples

Worked examples pulled from real production scenarios ship with the full skill.
Synthetic examples are intentionally omitted here to avoid teaching anti-patterns.

## Resources

- [LangChain 1.0 release](https://blog.langchain.com/langchain-langgraph-1dot0/)
- [LangChain Python docs](https://python.langchain.com/docs/)
- [LangGraph overview](https://docs.langchain.com/oss/python/langgraph/overview)
