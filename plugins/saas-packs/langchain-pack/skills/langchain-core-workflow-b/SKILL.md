---
name: langchain-core-workflow-b
description: |
  Build LangChain agents with tools for autonomous task execution.
  Use when creating AI agents, implementing tool calling,
  or building autonomous workflows with decision-making.
  Trigger with phrases like "langchain agents", "langchain tools",
  "tool calling", "langchain autonomous", "create agent", "function calling".
allowed-tools: Read, Write, Edit
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code, codex, openclaw
---
# LangChain Core Workflow B: Agents & Tools

## Overview
Build autonomous agents that can use tools, make decisions, and execute multi-step tasks using LangChain's agent framework.

## Prerequisites
- Completed `langchain-core-workflow-a` (chains)
- Understanding of function/tool calling concepts
- Familiarity with async programming

## Instructions

### Step 1: Define Tools
```python
from langchain_core.tools import tool
from pydantic import BaseModel, Field

class SearchInput(BaseModel):
    query: str = Field(description="The search query")

@tool(args_schema=SearchInput)
def search_web(query: str) -> str:
    """Search the web for information."""
    # Implement actual search logic
    return f"Search results for: {query}"

@tool
def calculate(expression: str) -> str:
    """Evaluate a mathematical expression."""
    try:
        result = eval(expression)  # Use safer alternative in production
        return str(result)
    except Exception as e:
        return f"Error: {e}"

@tool
def get_current_time() -> str:
    """Get the current date and time."""
    from datetime import datetime
    return datetime.now().isoformat()

tools = [search_web, calculate, get_current_time]
```

### Step 2: Create Agent with Tools
```python
from langchain_openai import ChatOpenAI
from langchain.agents import create_tool_calling_agent, AgentExecutor
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder

llm = ChatOpenAI(model="gpt-4o-mini")

prompt = ChatPromptTemplate.from_messages([
    ("system", "You are a helpful assistant with access to tools."),
    MessagesPlaceholder(variable_name="chat_history", optional=True),
    ("human", "{input}"),
    MessagesPlaceholder(variable_name="agent_scratchpad"),
])

agent = create_tool_calling_agent(llm, tools, prompt)

agent_executor = AgentExecutor(
    agent=agent,
    tools=tools,
    verbose=True,
    max_iterations=10,
    handle_parsing_errors=True
)
```

### Step 3: Run the Agent
```python
# Simple invocation
result = agent_executor.invoke({
    "input": "What's 25 * 4 and what time is it?"
})
print(result["output"])

# With chat history
from langchain_core.messages import HumanMessage, AIMessage

history = [
    HumanMessage(content="Hi, I'm Alice"),
    AIMessage(content="Hello Alice! How can I help you?")
]

result = agent_executor.invoke({
    "input": "What's my name?",
    "chat_history": history
})
```

### Step 4: Streaming Agent Output
```python
async def stream_agent():
    async for event in agent_executor.astream_events(
        {"input": "Search for LangChain news"},
        version="v2"
    ):
        if event["event"] == "on_chat_model_stream":
            print(event["data"]["chunk"].content, end="", flush=True)
        elif event["event"] == "on_tool_start":
            print(f"\n[Using tool: {event['name']}]")
```

## Output
- Typed tool definitions with Pydantic schemas
- Configured agent executor with error handling
- Working agent that can reason and use tools
- Streaming output for real-time feedback

## Advanced Patterns

### Custom Tool with Async Support
```python
from langchain_core.tools import StructuredTool

async def async_search(query: str) -> str:
    """Async search implementation."""
    import aiohttp
    async with aiohttp.ClientSession() as session:
        # Implement async search
        return f"Async results for: {query}"

search_tool = StructuredTool.from_function(
    func=lambda q: "sync fallback",
    coroutine=async_search,
    name="search",
    description="Search the web"
)
```

### Agent with Memory
```python
from langchain_community.chat_message_histories import ChatMessageHistory
from langchain_core.runnables.history import RunnableWithMessageHistory

message_history = ChatMessageHistory()

agent_with_memory = RunnableWithMessageHistory(
    agent_executor,
    lambda session_id: message_history,
    input_messages_key="input",
    history_messages_key="chat_history"
)

result = agent_with_memory.invoke(
    {"input": "Remember, I prefer Python"},
    config={"configurable": {"session_id": "user123"}}
)
```

## Error Handling
| Error | Cause | Solution |
|-------|-------|----------|
| Tool Not Found | Tool name mismatch | Verify tool names in prompt |
| Max Iterations | Agent stuck in loop | Increase limit or improve prompts |
| Parse Error | Invalid tool call format | Enable `handle_parsing_errors` |
| Tool Error | Tool execution failed | Add try/except in tool functions |

## Resources
- [Agents Conceptual Guide](https://python.langchain.com/docs/concepts/agents/)
- [Tool Calling](https://python.langchain.com/docs/concepts/tool_calling/)
- [Agent Types](https://python.langchain.com/docs/how_to/agent_executor/)

## Next Steps
Proceed to `langchain-common-errors` for debugging guidance.

## Examples

**Basic usage**: Apply langchain core workflow b to a standard project setup with default configuration options.

**Advanced scenario**: Customize langchain core workflow b for production environments with multiple constraints and team-specific requirements.