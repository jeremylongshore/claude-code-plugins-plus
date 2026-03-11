---
name: langchain-hello-world
description: |
  Create a minimal working LangChain example.
  Use when starting a new LangChain integration, testing your setup,
  or learning basic LangChain patterns with chains and prompts.
  Trigger with phrases like "langchain hello world", "langchain example",
  "langchain quick start", "simple langchain code", "first langchain app".
allowed-tools: Read, Write, Edit
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code, codex, openclaw
---
# LangChain Hello World

## Overview
Minimal working example demonstrating core LangChain functionality with chains and prompts.

## Prerequisites
- Completed `langchain-install-auth` setup
- Valid LLM provider API credentials configured
- Python 3.9+ or Node.js 18+ environment ready

## Instructions

### Step 1: Create Entry File
Create a new file `hello_langchain.py` for your hello world example.

### Step 2: Import and Initialize
```python
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate

llm = ChatOpenAI(model="gpt-4o-mini")
```

### Step 3: Create Your First Chain
```python
from langchain_core.output_parsers import StrOutputParser

prompt = ChatPromptTemplate.from_messages([
    ("system", "You are a helpful assistant."),
    ("user", "{input}")
])

chain = prompt | llm | StrOutputParser()

response = chain.invoke({"input": "Hello, LangChain!"})
print(response)
```

## Output
- Working Python file with LangChain chain
- Successful LLM response confirming connection
- Console output showing:
```
Hello! I'm your LangChain-powered assistant. How can I help you today?
```

## Error Handling
| Error | Cause | Solution |
|-------|-------|----------|
| Import Error | SDK not installed | Run `pip install langchain langchain-openai` |
| Auth Error | Invalid credentials | Check environment variable is set |
| Timeout | Network issues | Increase timeout or check connectivity |
| Rate Limit | Too many requests | Wait and retry with exponential backoff |
| Model Not Found | Invalid model name | Check available models in provider docs |

## Examples

### Simple Chain (Python)
```python
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser

llm = ChatOpenAI(model="gpt-4o-mini")
prompt = ChatPromptTemplate.from_template("Tell me a joke about {topic}")
chain = prompt | llm | StrOutputParser()

result = chain.invoke({"topic": "programming"})
print(result)
```

### With Memory (Python)
```python
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.messages import HumanMessage, AIMessage

llm = ChatOpenAI(model="gpt-4o-mini")
prompt = ChatPromptTemplate.from_messages([
    ("system", "You are a helpful assistant."),
    MessagesPlaceholder(variable_name="history"),
    ("user", "{input}")
])

chain = prompt | llm

history = []
response = chain.invoke({"input": "Hi!", "history": history})
print(response.content)
```

### TypeScript Example
```typescript
import { ChatOpenAI } from "@langchain/openai";
import { ChatPromptTemplate } from "@langchain/core/prompts";
import { StringOutputParser } from "@langchain/core/output_parsers";

const llm = new ChatOpenAI({ modelName: "gpt-4o-mini" });
const prompt = ChatPromptTemplate.fromTemplate("Tell me about {topic}");
const chain = prompt.pipe(llm).pipe(new StringOutputParser());

const result = await chain.invoke({ topic: "LangChain" });
console.log(result);
```

## Resources
- [LangChain LCEL Guide](https://python.langchain.com/docs/concepts/lcel/)
- [Prompt Templates](https://python.langchain.com/docs/concepts/prompt_templates/)
- [Output Parsers](https://python.langchain.com/docs/concepts/output_parsers/)

## Next Steps
Proceed to `langchain-local-dev-loop` for development workflow setup.