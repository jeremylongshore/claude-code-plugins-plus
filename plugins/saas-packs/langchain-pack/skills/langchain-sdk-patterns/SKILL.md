---
name: langchain-sdk-patterns
description: |
  Apply production-ready LangChain SDK patterns for chains, agents, and memory.
  Use when implementing LangChain integrations, refactoring code,
  or establishing team coding standards for LangChain applications.
  Trigger with phrases like "langchain SDK patterns", "langchain best practices",
  "langchain code patterns", "idiomatic langchain", "langchain architecture".
allowed-tools: Read, Write, Edit
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code, codex, openclaw
---
# LangChain SDK Patterns

## Overview
Production-ready patterns for LangChain applications including LCEL chains, structured output, and error handling.

## Prerequisites
- Completed `langchain-install-auth` setup
- Familiarity with async/await patterns
- Understanding of error handling best practices

## Core Patterns

### Pattern 1: Type-Safe Chain with Pydantic
```python
from pydantic import BaseModel, Field
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate

class SentimentResult(BaseModel):
    """Structured output for sentiment analysis."""
    sentiment: str = Field(description="positive, negative, or neutral")
    confidence: float = Field(description="Confidence score 0-1")
    reasoning: str = Field(description="Brief explanation")

llm = ChatOpenAI(model="gpt-4o-mini")
structured_llm = llm.with_structured_output(SentimentResult)

prompt = ChatPromptTemplate.from_template(
    "Analyze the sentiment of: {text}"
)

chain = prompt | structured_llm

# Returns typed SentimentResult
result: SentimentResult = chain.invoke({"text": "I love LangChain!"})
print(f"Sentiment: {result.sentiment} ({result.confidence})")
```

### Pattern 2: Retry with Fallback
```python
from langchain_openai import ChatOpenAI
from langchain_anthropic import ChatAnthropic
from langchain_core.runnables import RunnableWithFallbacks

primary = ChatOpenAI(model="gpt-4o")
fallback = ChatAnthropic(model="claude-3-5-sonnet-20241022")  # 20241022 = date/version stamp

# Automatically falls back on failure
robust_llm = primary.with_fallbacks([fallback])

response = robust_llm.invoke("Hello!")
```

### Pattern 3: Async Batch Processing
```python
import asyncio
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate

llm = ChatOpenAI(model="gpt-4o-mini")
prompt = ChatPromptTemplate.from_template("Summarize: {text}")
chain = prompt | llm

async def process_batch(texts: list[str]) -> list:
    """Process multiple texts concurrently."""
    inputs = [{"text": t} for t in texts]
    results = await chain.abatch(inputs, config={"max_concurrency": 5})
    return results

# Usage
results = asyncio.run(process_batch(["text1", "text2", "text3"]))
```

### Pattern 4: Streaming with Callbacks
```python
from langchain_openai import ChatOpenAI
from langchain_core.callbacks import StreamingStdOutCallbackHandler

llm = ChatOpenAI(
    model="gpt-4o-mini",
    streaming=True,
    callbacks=[StreamingStdOutCallbackHandler()]
)

# Streams tokens to stdout as they arrive
for chunk in llm.stream("Tell me a story"):
    # Each chunk contains partial content
    pass
```

### Pattern 5: Caching for Cost Reduction
```python
from langchain_openai import ChatOpenAI
from langchain_core.globals import set_llm_cache
from langchain_community.cache import SQLiteCache

# Enable SQLite caching
set_llm_cache(SQLiteCache(database_path=".langchain_cache.db"))

llm = ChatOpenAI(model="gpt-4o-mini")

# First call hits API
response1 = llm.invoke("What is 2+2?")

# Second identical call uses cache (no API cost)
response2 = llm.invoke("What is 2+2?")
```

## Output
- Type-safe chains with Pydantic models
- Robust error handling with fallbacks
- Efficient async batch processing
- Cost-effective caching strategies

## Error Handling

### Standard Error Pattern
```python
from langchain_core.exceptions import OutputParserException
from openai import RateLimitError, APIError

def safe_invoke(chain, input_data, max_retries=3):
    """Invoke chain with error handling."""
    for attempt in range(max_retries):
        try:
            return chain.invoke(input_data)
        except RateLimitError:
            if attempt < max_retries - 1:
                time.sleep(2 ** attempt)
                continue
            raise
        except OutputParserException as e:
            # Handle parsing failures
            return {"error": str(e), "raw": e.llm_output}
        except APIError as e:
            raise RuntimeError(f"API error: {e}")
```

## Resources
- [LCEL Documentation](https://python.langchain.com/docs/concepts/lcel/)
- [Structured Output](https://python.langchain.com/docs/concepts/structured_outputs/)
- [Fallbacks](https://python.langchain.com/docs/how_to/fallbacks/)
- [Caching](https://python.langchain.com/docs/how_to/llm_caching/)

## Next Steps
Proceed to `langchain-core-workflow-a` for chains and prompts workflow.

## Instructions

1. Assess the current state of the Langchain Sdk Patterns configuration
2. Identify the specific requirements and constraints
3. Apply the recommended patterns from this skill
4. Validate the changes against expected behavior
5. Document the configuration for team reference

## Examples

**Basic usage**: Apply langchain sdk patterns to a standard project setup with default configuration options.

**Advanced scenario**: Customize langchain sdk patterns for production environments with multiple constraints and team-specific requirements.