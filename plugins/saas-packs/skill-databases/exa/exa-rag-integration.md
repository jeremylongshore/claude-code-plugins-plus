# exa-rag-integration

## Skill Scaffold

```
exa-rag-integration/
  SKILL.md
```

## File Descriptions

### 1. SKILL.md
**Purpose:** Build RAG (Retrieval Augmented Generation) pipelines using Exa for real-time web knowledge retrieval to enhance LLM responses.
**Workflow:** Key integration pattern for AI applications - connects Exa search to LLM workflows.
**Relates to:** Follows exa-content-extraction; integrates with exa-embedding-integration

## Summary

This skill implements RAG pipelines with Exa: query reformulation for optimal retrieval, Exa search with content extraction, context windowing and chunking, LLM prompt construction with retrieved context, source attribution and citation, response grounding verification, caching strategies for repeated queries, and multi-turn conversation context management. Includes integration patterns for OpenAI, Anthropic, and local LLMs.
