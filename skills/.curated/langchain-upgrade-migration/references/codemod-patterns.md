# Codemod Patterns — 0.3 → 1.0

Before/after snippets for the seven migrations that cover ~95% of a typical LangChain 0.3 codebase. Apply in order — each pattern assumes the import paths from Pattern 1 are already fixed.

## Pattern 1 — Provider Import Paths (P38)

Every import from `langchain.chat_models`, `langchain.llms`, `langchain.embeddings`, or `langchain.vectorstores` is gone. Replace with the partner package.

```python
# BEFORE (0.3)
from langchain.chat_models import ChatOpenAI, ChatAnthropic
from langchain.embeddings import OpenAIEmbeddings
from langchain.vectorstores import Chroma

# AFTER (1.0)
from langchain_openai import ChatOpenAI, OpenAIEmbeddings
from langchain_anthropic import ChatAnthropic
from langchain_chroma import Chroma
```

Search pattern: `grep -rn "from langchain\.\(chat_models\|llms\|embeddings\|vectorstores\)" .`

## Pattern 2 — LLMChain → LCEL (P39)

`LLMChain` is removed. Replace with the pipe operator and an output parser.

```python
# BEFORE (0.3)
from langchain.chains import LLMChain
from langchain.prompts import PromptTemplate

prompt = PromptTemplate.from_template("Translate to French: {text}")
chain = LLMChain(llm=llm, prompt=prompt)
result = chain.run(text="hello")           # or: chain({"text": "hello"})["text"]

# AFTER (1.0)
from langchain_core.prompts import PromptTemplate
from langchain_core.output_parsers import StrOutputParser

prompt = PromptTemplate.from_template("Translate to French: {text}")
chain = prompt | llm | StrOutputParser()
result = chain.invoke({"text": "hello"})    # returns str directly
```

Caller change: `chain.run(x=1)` becomes `chain.invoke({"x": 1})`. Any code that treated the result as a dict (`result["text"]`) now gets the unwrapped string.

## Pattern 3 — initialize_agent → create_react_agent (P41)

`initialize_agent` and all `AgentType.*` values are removed. The 1.0 path is LangGraph's prebuilt ReAct agent.

```python
# BEFORE (0.3)
from langchain.agents import initialize_agent, AgentType, Tool

tools = [Tool(name="search", func=search_fn, description="Web search")]
agent = initialize_agent(
    tools,
    llm,
    agent=AgentType.ZERO_SHOT_REACT_DESCRIPTION,
    verbose=True,
)
result = agent.run("What's the weather in Austin?")

# AFTER (1.0)
from langgraph.prebuilt import create_react_agent
from langchain_core.tools import tool

@tool
def search(query: str) -> str:
    """Web search."""
    return search_fn(query)

agent = create_react_agent(llm, [search])
result = agent.invoke({"messages": [("user", "What's the weather in Austin?")]})
final_text = result["messages"][-1].content
```

Caller change: input shape is `{"messages": [...]}`, output is a dict with `"messages"` whose last element holds the final AI reply.

## Pattern 4 — ConversationBufferMemory → LangGraph Checkpointer (P40)

`ConversationBufferMemory` (and `ConversationBufferWindowMemory`, `ConversationSummaryMemory`) are removed. History is now graph state persisted by a checkpointer.

```python
# BEFORE (0.3)
from langchain.memory import ConversationBufferMemory
from langchain.chains import ConversationChain

memory = ConversationBufferMemory()
chain = ConversationChain(llm=llm, memory=memory)
chain.predict(input="Hi, I'm Jeremy")
chain.predict(input="What's my name?")   # remembers "Jeremy"

# AFTER (1.0)
from langgraph.checkpoint.memory import MemorySaver
from langgraph.prebuilt import create_react_agent

checkpointer = MemorySaver()              # or SqliteSaver.from_conn_string("checkpoints.sqlite")
agent = create_react_agent(llm, tools=[], checkpointer=checkpointer)

config = {"configurable": {"thread_id": "user-42"}}
agent.invoke({"messages": [("user", "Hi, I'm Jeremy")]}, config=config)
agent.invoke({"messages": [("user", "What's my name?")]}, config=config)   # same thread_id → recalls "Jeremy"
```

For production, swap `MemorySaver` for `SqliteSaver`, `PostgresSaver`, or `RedisSaver`. The `thread_id` is the primary key for a conversation.

## Pattern 5 — astream_log → astream_events v2 (P67)

`astream_log` still works in 1.0 but is soft-deprecated and will not get new features. The replacement is `astream_events(version="v2")`.

```python
# BEFORE (0.3) — RunLog patch stream
async for patch in chain.astream_log({"input": "hi"}):
    for op in patch.ops:
        if op["op"] == "add" and op["path"].endswith("/streamed_output/-"):
            print(op["value"], end="", flush=True)

# AFTER (1.0) — typed event stream
async for event in chain.astream_events({"input": "hi"}, version="v2"):
    if event["event"] == "on_chat_model_stream":
        chunk = event["data"]["chunk"]
        print(chunk.content, end="", flush=True)
```

Key event names in v2: `on_chain_start`, `on_chain_end`, `on_chat_model_start`, `on_chat_model_stream`, `on_chat_model_end`, `on_tool_start`, `on_tool_end`. The payload under `data` is typed — `chunk` is an `AIMessageChunk`, not a raw string.

## Pattern 6 — AgentAction → ToolCall field rename (P42)

If you ever inspected `intermediate_steps` on `AgentExecutor`, the tuple shape changed and the field names drifted.

```python
# BEFORE (0.3)
for action, observation in result["intermediate_steps"]:
    print(action.tool, action.tool_input, observation)

# AFTER (1.0) — LangGraph state inspection
for msg in result["messages"]:
    for tc in getattr(msg, "tool_calls", []) or []:
        print(tc["name"], tc["args"])    # .tool -> ["name"], .tool_input -> ["args"]
```

The `ToolCall` dict keys are `name`, `args`, `id`. There is no `tool` or `tool_input` attribute anywhere in 1.0.

## Pattern 7 — langchain-anthropic + anthropic peer pin (P66)

`langchain-anthropic 1.0` requires `anthropic >= 0.40`. A lone `pip install -U langchain-anthropic` without bumping the `anthropic` SDK triggers `AttributeError: module 'anthropic' has no attribute 'AsyncAnthropic'` at import.

```
# BEFORE (0.3)
langchain==0.3.*
langchain-anthropic==0.2.*
anthropic==0.34.*          # old SDK — fine with 0.2 integration

# AFTER (1.0)
langchain==1.*
langchain-core==0.3.*
langchain-anthropic==1.*
anthropic>=0.40,<1.0       # MUST bump together
```

Pin all four lines in the same commit. If you bump `langchain-anthropic` without `anthropic`, the integration will import-fail before your app code runs.

## After Running All Seven Patterns

Re-run the verification greps from [breaking-changes-matrix.md](breaking-changes-matrix.md). Zero hits means the codemod is complete and the test suite is safe to run.
