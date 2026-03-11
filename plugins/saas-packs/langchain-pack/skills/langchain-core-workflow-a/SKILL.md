---
name: langchain-core-workflow-a
description: |
  Build LangChain chains and prompts for structured LLM workflows.
  Use when creating prompt templates, building LCEL chains,
  or implementing sequential processing pipelines.
  Trigger with phrases like "langchain chains", "langchain prompts",
  "LCEL workflow", "langchain pipeline", "prompt template".
allowed-tools: Read, Write, Edit
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code, codex, openclaw
---
# LangChain Core Workflow A: Chains & Prompts

## Overview
Build production-ready chains using LangChain Expression Language (LCEL) with prompt templates, output parsers, and composition patterns.

## Prerequisites
- Completed `langchain-install-auth` setup
- Understanding of prompt engineering basics
- Familiarity with Python type hints

## Instructions

### Step 1: Create Prompt Templates
```python
from langchain_core.prompts import (
    ChatPromptTemplate,
    SystemMessagePromptTemplate,
    HumanMessagePromptTemplate,
    MessagesPlaceholder
)

# Simple template
simple_prompt = ChatPromptTemplate.from_template(
    "Translate '{text}' to {language}"
)

# Chat-style template
chat_prompt = ChatPromptTemplate.from_messages([
    SystemMessagePromptTemplate.from_template(
        "You are a {role}. Respond in {style} style."
    ),
    MessagesPlaceholder(variable_name="history", optional=True),
    HumanMessagePromptTemplate.from_template("{input}")
])
```

### Step 2: Build LCEL Chains
```python
from langchain_openai import ChatOpenAI
from langchain_core.output_parsers import StrOutputParser, JsonOutputParser

llm = ChatOpenAI(model="gpt-4o-mini")

# Basic chain: prompt -> llm -> parser
basic_chain = simple_prompt | llm | StrOutputParser()

# Invoke the chain
result = basic_chain.invoke({
    "text": "Hello, world!",
    "language": "Spanish"
})
print(result)  # "Hola, mundo!"
```

### Step 3: Chain Composition
```python
from langchain_core.runnables import RunnablePassthrough, RunnableParallel

# Sequential chain
chain1 = prompt1 | llm | StrOutputParser()
chain2 = prompt2 | llm | StrOutputParser()

sequential = chain1 | (lambda x: {"summary": x}) | chain2

# Parallel execution
parallel = RunnableParallel(
    summary=prompt1 | llm | StrOutputParser(),
    keywords=prompt2 | llm | StrOutputParser(),
    sentiment=prompt3 | llm | StrOutputParser()
)

results = parallel.invoke({"text": "Your input text"})
# Returns: {"summary": "...", "keywords": "...", "sentiment": "..."}
```

### Step 4: Branching Logic
```python
from langchain_core.runnables import RunnableBranch

# Conditional branching
branch = RunnableBranch(
    (lambda x: x["type"] == "question", question_chain),
    (lambda x: x["type"] == "command", command_chain),
    default_chain  # Fallback
)

result = branch.invoke({"type": "question", "input": "What is AI?"})
```

## Output
- Reusable prompt templates with variable substitution
- Type-safe LCEL chains with clear data flow
- Composable chain patterns (sequential, parallel, branching)
- Consistent output parsing

## Examples

### Multi-Step Processing Chain
```python
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser

llm = ChatOpenAI(model="gpt-4o-mini")

# Step 1: Extract key points
extract_prompt = ChatPromptTemplate.from_template(
    "Extract 3 key points from: {text}"
)

# Step 2: Summarize
summarize_prompt = ChatPromptTemplate.from_template(
    "Create a one-sentence summary from these points: {points}"
)

# Compose the chain
chain = (
    {"points": extract_prompt | llm | StrOutputParser()}
    | summarize_prompt
    | llm
    | StrOutputParser()
)

summary = chain.invoke({"text": "Long article text here..."})
```

### With Context Injection
```python
from langchain_core.runnables import RunnablePassthrough

def get_context(input_dict):
    """Fetch relevant context from database."""
    return f"Context for: {input_dict['query']}"

chain = (
    RunnablePassthrough.assign(context=get_context)
    | prompt
    | llm
    | StrOutputParser()
)

result = chain.invoke({"query": "user question"})
```

## Error Handling
| Error | Cause | Solution |
|-------|-------|----------|
| Missing Variable | Template variable not provided | Check input dict keys match template |
| Type Error | Wrong input type | Ensure inputs match expected schema |
| Parse Error | Output doesn't match parser | Use more specific prompts or fallback |

## Resources
- [LCEL Conceptual Guide](https://python.langchain.com/docs/concepts/lcel/)
- [Prompt Templates](https://python.langchain.com/docs/concepts/prompt_templates/)
- [Runnables](https://python.langchain.com/docs/concepts/runnables/)

## Next Steps
Proceed to `langchain-core-workflow-b` for agents and tools workflow.