# Breaking Changes Matrix — LangChain 0.3.x → 1.0.x

Every removed or renamed public API between LangChain 0.3 and LangChain 1.0 / LangGraph 1.0, grouped by module, with the exact 1.0 replacement and a one-line code snippet. Pain codes refer to the `langchain-py-pack` pain catalog.

## Import Paths

| 0.3.x API (removed) | 1.0.x Replacement | Pain | One-liner |
|---|---|---|---|
| `from langchain.chat_models import ChatOpenAI` | `from langchain_openai import ChatOpenAI` | P38 | Provider imports live in `langchain-openai`, `langchain-anthropic`, etc. |
| `from langchain.chat_models import ChatAnthropic` | `from langchain_anthropic import ChatAnthropic` | P38, P66 | Requires `anthropic >= 0.40` alongside `langchain-anthropic >= 1.0`. |
| `from langchain.llms import OpenAI` | `from langchain_openai import OpenAI` | P38 | Same package as `ChatOpenAI`; completions-style models are still available but the chat model is preferred. |
| `from langchain.embeddings import OpenAIEmbeddings` | `from langchain_openai import OpenAIEmbeddings` | P38 | Also affects `HuggingFaceEmbeddings` → `langchain_huggingface`. |
| `from langchain.vectorstores import Chroma` | `from langchain_chroma import Chroma` | P38 | Vectorstores were extracted into `langchain-<store>` partner packages. |

## Chains

| 0.3.x API (removed) | 1.0.x Replacement | Pain | One-liner |
|---|---|---|---|
| `from langchain.chains import LLMChain` | LCEL: `prompt \| llm \| StrOutputParser()` | P39 | `chain.invoke({"x": 1})` replaces `chain.run(x=1)` / `chain({"x": 1})`. |
| `from langchain.chains import ConversationChain` | LCEL + LangGraph checkpointer | P39, P40 | Wire history via a LangGraph `MemorySaver` or `SqliteSaver`. |
| `from langchain.chains import SequentialChain` | LCEL pipe: `a \| b \| c` | P39 | Named outputs use `RunnablePassthrough.assign(...)`. |
| `from langchain.chains import RetrievalQA` | `create_retrieval_chain(retriever, combine_docs_chain)` | P39 | `combine_docs_chain = create_stuff_documents_chain(llm, prompt)`. |
| `from langchain.chains import LLMMathChain` | LCEL tool calling with a Python REPL tool | P39 | No drop-in replacement; rebuild as a tool-using agent. |

## Agents

| 0.3.x API (removed) | 1.0.x Replacement | Pain | One-liner |
|---|---|---|---|
| `from langchain.agents import initialize_agent` | `from langgraph.prebuilt import create_react_agent` | P41 | `agent = create_react_agent(llm, tools)`; `invoke({"messages": [...]})`. |
| `AgentType.ZERO_SHOT_REACT_DESCRIPTION` | `create_react_agent(llm, tools)` | P41 | ReAct is now the default prebuilt; other AgentTypes are gone. |
| `AgentType.CHAT_CONVERSATIONAL_REACT_DESCRIPTION` | `create_react_agent` + LangGraph checkpointer | P40, P41 | History lives in the graph state, not in a memory object. |
| `AgentExecutor(...).intermediate_steps` yielding `(AgentAction, str)` | Messages in graph state; `ToolCall` objects with `name`, `args`, `id` | P42 | Old `step.tool` / `step.tool_input` becomes `tool_call["name"]` / `tool_call["args"]`. |
| `from langchain.agents import Tool` | `from langchain_core.tools import tool` (decorator) or `StructuredTool.from_function` | P41 | Plain `Tool(name=..., func=...)` still works but the decorator is preferred. |

## Memory

| 0.3.x API (removed) | 1.0.x Replacement | Pain | One-liner |
|---|---|---|---|
| `from langchain.memory import ConversationBufferMemory` | LangGraph checkpointer: `MemorySaver()` or `SqliteSaver.from_conn_string(...)` | P40 | Persist via `graph.compile(checkpointer=saver)`; thread id via `config={"configurable": {"thread_id": "..."}}`. |
| `from langchain.memory import ConversationBufferWindowMemory` | LangGraph state + `trim_messages(max_tokens=...)` | P40 | Trimming is explicit in the graph node, not hidden in memory. |
| `from langchain.memory import ConversationSummaryMemory` | Graph node that periodically summarises and writes back to state | P40 | No drop-in; build a summariser node. |
| `BaseChatMessageHistory` subclasses (e.g. `RedisChatMessageHistory`) | Still supported under `langchain_community.chat_message_histories` | P40 | Keep the store; wrap it in a checkpointer or a graph node. |

## Streaming / Observability

| 0.3.x API (soft-deprecated) | 1.0.x Replacement | Pain | One-liner |
|---|---|---|---|
| `astream_log(...)` | `astream_events(version="v2")` | P67 | `v2` is stable; event names and payload shapes are the supported surface. |
| `CallbackManager.configure(...)` legacy context | Runnable config (`RunnableConfig`) | — | Pass `config={"callbacks": [...]}` to `invoke` / `astream_events`. |
| `get_openai_callback()` context manager | Still available; prefer LangSmith tracing or OpenAI usage events from `astream_events` | — | Both work on 1.0, but LangSmith is the recommended path. |

## Embeddings / Indexing

| 0.3.x API (behaviour change) | 1.0.x Behaviour | Pain | One-liner |
|---|---|---|---|
| Embedding dimension implicit on vectorstore create | Explicit `dim` required for most partner stores; mismatches raise on upsert | P14 | On model swap (`text-embedding-ada-002` → `text-embedding-3-*`), reindex — the dim differs. |
| `OpenAIEmbeddings(model="text-embedding-ada-002")` | Works, but ada-002 is deprecated at OpenAI; prefer `text-embedding-3-small` / `-large` | P14 | Schedule a reindex during the migration window. |

## Verification Checklist

After applying every change above, these greps should return **zero hits** in your codebase:

```
langchain.chat_models         # P38
langchain.llms                # P38 (except tests that intentionally pin 0.3)
langchain.chains              # P39
langchain.memory              # P40
langchain.agents.initialize_agent   # P41
AgentAction\.tool             # P42 — both field accesses gone
astream_log\(                 # P67
```

If any of these still hit, re-open [codemod-patterns.md](codemod-patterns.md) and apply the matching pattern.
