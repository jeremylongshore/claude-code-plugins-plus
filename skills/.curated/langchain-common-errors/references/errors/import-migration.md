# Import & Migration Errors (0.2 / 0.3 → 1.0)

Pain-catalog anchors: **P38, P39, P40, P41, P42, P66**.

Every error below was raised by LangChain 0.2/0.3-era code running against pinned `langchain-core 1.0.x`. The top-level re-exports from the `langchain` meta-package were removed in 1.0. Provider integrations, agent factories, legacy chain classes, and `ConversationBufferMemory` now live in separate packages.

Last verified against `langchain-core==1.0.0`, `langchain==1.0.0`, `langgraph==1.0.0`, `langchain-openai==1.0.0`, `langchain-anthropic==1.0.0`, `anthropic==0.42.0`.

---

## E01 — `ImportError: cannot import name 'ChatOpenAI' from 'langchain.chat_models'`

**Pain:** P38

**Before:**

```python
from langchain.chat_models import ChatOpenAI  # 0.2 path
from langchain.chat_models import ChatAnthropic  # 0.2 path
```

**Cause:** Provider integrations moved to `langchain-<provider>` packages in 0.3. The top-level re-exports from `langchain.chat_models` and `langchain.llms` were **removed** in 1.0.

**After:**

```python
from langchain_openai import ChatOpenAI
from langchain_anthropic import ChatAnthropic
from langchain_google_genai import ChatGoogleGenerativeAI
```

**Codemod:** `python -m langchain_cli migrate path/to/src/` rewrites the imports. Run `pip install langchain-cli>=0.1` first. Re-run tests — imports will now succeed but you may hit E04 (`AIMessage.content` shape) and E05 (`list[Union]` structured output) next.

**Install:** `pip install "langchain-openai>=1.0,<2.0" "langchain-anthropic>=1.0,<2.0" "langchain-google-genai>=1.0,<2.0"`.

---

## E02 — `AttributeError: module 'langchain' has no attribute 'LLMChain'`

**Pain:** P39

**Before:**

```python
from langchain.chains import LLMChain
chain = LLMChain(llm=llm, prompt=prompt)
result = chain.run({"input": text})
```

**Cause:** `LLMChain` (and `SimpleSequentialChain`, `SequentialChain`, `TransformChain`, etc.) were deprecated in 0.3 and **removed** in 1.0 in favor of LCEL composition. The 1.0 `langchain` package has no `chains` module.

**After:**

```python
from langchain_core.output_parsers import StrOutputParser
chain = prompt | llm | StrOutputParser()
result = chain.invoke({"input": text})
```

**Notes:** If you need fallbacks, use `chain.with_fallbacks([backup])`. If you need retries, use `chain.with_retry(...)`. `.run(x)` became `.invoke({"input": x})`; single-positional-string input is gone.

---

## E03 — `ImportError: cannot import name 'ConversationBufferMemory'`

**Pain:** P40

**Before:**

```python
from langchain.memory import ConversationBufferMemory
memory = ConversationBufferMemory(memory_key="history")
```

**Cause:** All `ConversationBufferMemory`, `ConversationSummaryMemory`, `ConversationTokenBufferMemory`, `VectorStoreRetrieverMemory` classes deprecated in 0.3, **removed** in 1.0. LangGraph checkpointing is the supported replacement for multi-turn chat memory.

**After:**

```python
from langgraph.checkpoint.memory import InMemorySaver
from langgraph.prebuilt import create_react_agent

checkpointer = InMemorySaver()  # or PostgresSaver / SqliteSaver
agent = create_react_agent(model=llm, tools=tools, checkpointer=checkpointer)
result = agent.invoke(
    {"messages": [("user", "hi")]},
    config={"configurable": {"thread_id": "user-42"}},
)
```

**Notes:** `thread_id` is **required** — without it every invocation gets a fresh state (see E12). For process-restart persistence use `PostgresSaver` or `SqliteSaver`, not `InMemorySaver`.

---

## E04 — `ImportError: cannot import name 'initialize_agent'`

**Pain:** P41

**Before:**

```python
from langchain.agents import initialize_agent, AgentType
agent = initialize_agent(
    tools=tools,
    llm=llm,
    agent=AgentType.ZERO_SHOT_REACT_DESCRIPTION,
)
```

**Cause:** `initialize_agent`, `AgentType`, `create_openai_functions_agent`, `create_structured_chat_agent`, and most legacy agent factories are **removed** in 1.0. `AgentExecutor` is still importable but LangGraph's `create_react_agent` is the supported path for new code.

**After:**

```python
from langgraph.prebuilt import create_react_agent
from langgraph.checkpoint.memory import InMemorySaver

agent = create_react_agent(
    model=llm,
    tools=tools,
    checkpointer=InMemorySaver(),
)
```

**Notes:** `create_react_agent` uses provider-native tool calling (no free-text ReAct parsing) and raises on tool errors by default, unlike legacy `AgentExecutor` which swallowed them as empty strings (E08). Default `recursion_limit=25` — see E13.

---

## E05 — `AttributeError: 'AgentAction' object has no attribute 'tool_name'` (or inverse `.tool`)

**Pain:** P42

**Before:**

```python
result = executor.invoke({"input": q})
for action, observation in result["intermediate_steps"]:
    print(action.tool, action.tool_input)  # 0.2 / 0.3 shape
```

**Cause:** Legacy `AgentAction` / `AgentFinish` tuple shape was replaced by `ToolCall` objects in 1.0. Fields renamed: `.tool` → `.tool_name`, `.tool_input` → `.args`, `.log` removed. LangGraph agents emit messages with `.tool_calls` instead of a separate `intermediate_steps` key.

**After (LangGraph `create_react_agent`):**

```python
result = agent.invoke({"messages": [("user", q)]}, config=cfg)
for msg in result["messages"]:
    for tool_call in getattr(msg, "tool_calls", []) or []:
        print(tool_call["name"], tool_call["args"])
```

**Notes:** When migrating, `grep -rn "intermediate_steps" src/` and `grep -rn "\.tool_input" src/` to find all call-sites. Both shapes compile, so type-checking will not catch this — only runtime AttributeError.

---

## E06 — `KeyError: 'input'` inside `tool_use` block parsing (after upgrading `langchain-anthropic`)

**Pain:** P66

**Before:** `langchain-anthropic==0.3.x` pinned alongside `langchain-anthropic==1.0`.

**Cause:** `langchain-anthropic >= 1.0` **requires** `anthropic >= 0.40`. The Anthropic SDK's tool_use block schema changed; pinning to an old `anthropic` breaks `AIMessage.content` parsing for tool calls. Chat-only responses still work — tool calling is the first place it breaks.

**After:**

```bash
pip install "langchain-anthropic>=1.0,<2.0" "anthropic>=0.42,<1.0"
```

Pin both in the same `pip install` or `pyproject.toml` bump — upgrading one without the other is the bug.

**Notes:** Sanity-check with:

```python
import anthropic, langchain_anthropic
print(anthropic.__version__, langchain_anthropic.__version__)
# Must be anthropic >= 0.40 and langchain-anthropic >= 1.0
```

---

## Codemod-driven migration checklist

1. `pip install "langchain-cli>=0.1"` (dev dep).
2. `python -m langchain_cli migrate .` — rewrites imports for E01.
3. Manually handle E02/E03/E04 (the codemod does not rewrite `LLMChain`, memory, or agent construction).
4. `grep -rn "intermediate_steps\|AgentAction\|AgentType\|initialize_agent\|LLMChain\|ConversationBuffer\|from langchain\.chat_models\|from langchain\.llms" src/` → every hit is a manual fix.
5. Pin all three: `langchain-core`, `langchain`, `langgraph`, plus any provider packages, to the same 1.0.x major.
6. `pytest -x` — expect E07-E14 from the other reference files next. That is normal on a 0.2/0.3 → 1.0 jump.

## Sources

- Pain catalog: `docs/pain-catalog.md` (P38, P39, P40, P41, P42, P66)
- [LangChain 1.0 release notes](https://blog.langchain.com/langchain-langgraph-1dot0/)
- [LangChain migration guide](https://python.langchain.com/docs/versions/migrating_chains/)
- [`langchain-cli` migrate command](https://python.langchain.com/docs/versions/migrating/)
- [LangGraph `create_react_agent`](https://langchain-ai.github.io/langgraph/reference/prebuilt/)
