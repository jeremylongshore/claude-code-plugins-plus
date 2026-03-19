---
name: langchain-migration-deep-dive
description: |
  Complex migration strategies for LangChain applications.
  Use when migrating from legacy LLM frameworks, refactoring large codebases,
  or implementing phased migration approaches.
  Trigger with phrases like "langchain migration strategy", "migrate to langchain",
  "langchain refactor", "legacy LLM migration", "langchain transition".
allowed-tools: Read, Write, Edit, Bash(python:*), Grep
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code, codex, openclaw
---
# LangChain Migration Deep Dive

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
Comprehensive strategies for migrating to LangChain from legacy LLM implementations or other frameworks (OpenAI SDK, LlamaIndex, custom agents).

## Prerequisites
- Existing LLM application to migrate
- Understanding of current architecture
- Test coverage for validation
- Staging environment for testing

## Instructions

### Step 1: Assess Codebase
Scan for migration items using pattern matching (OpenAI SDK calls, LlamaIndex imports, legacy LLMChain usage). Classify each by complexity.

### Step 2: Migrate Raw SDK to LangChain
Replace direct OpenAI/Anthropic SDK calls with LangChain equivalents using `ChatPromptTemplate`, `MessagesPlaceholder`, and chain composition (`prompt | llm | StrOutputParser()`).

### Step 3: Migrate RAG Systems
Replace LlamaIndex `VectorStoreIndex` with LangChain `DirectoryLoader` + `RecursiveCharacterTextSplitter` + FAISS/Pinecone retriever chains.

### Step 4: Migrate Custom Agents
Replace manual function-calling loops with `create_tool_calling_agent` and `AgentExecutor`.

### Step 5: Run Parallel Validation
Use a `DualRunner` class to execute both legacy and new implementations side-by-side, comparing outputs for discrepancies.

### Step 6: Gradual Rollout with Feature Flags
Control rollout percentage per user with consistent hashing, then validate and clean up legacy code.

See [detailed implementation](${CLAUDE_SKILL_DIR}/references/implementation.md) for before/after code examples and migration scripts.

## Output
- Migration assessment report
- Parallel validation framework
- Feature-flag rollout system
- Validation test suite

## Error Handling

| Issue | Solution |
|-------|----------|
| Different response format | Add output parser adapter |
| Missing streaming support | Implement streaming callbacks |
| Memory format mismatch | Convert message history format |
| Tool schema differences | Update tool definitions |

## Examples


**Basic usage**: Apply langchain migration deep dive to a standard project setup with default configuration options.

**Advanced scenario**: Customize langchain migration deep dive for production environments with multiple constraints and team-specific requirements.

## Resources
- [LangChain Migration Guide](https://python.langchain.com/docs/versions/migrating_chains/)
- [OpenAI SDK Migration](https://github.com/openai/openai-python/discussions/742)
- [Feature Flags Best Practices](https://launchdarkly.com/blog/best-practices-feature-flags/)

## Next Steps
Use `langchain-upgrade-migration` for LangChain version upgrades.