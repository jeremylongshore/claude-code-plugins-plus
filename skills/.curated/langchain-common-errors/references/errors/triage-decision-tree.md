# Triage Decision Tree

Routing logic for LangChain 1.0 / LangGraph 1.0 tracebacks. Pipe your error in, walk the tree to the right reference file and entry code. Two minutes, no guessing.

## ASCII flowchart

```
START: you have a traceback
  │
  ├── 1. Is the FIRST line of the traceback an ImportError or ModuleNotFoundError?
  │   │
  │   ├── "cannot import name 'ChatOpenAI' / 'ChatAnthropic' from 'langchain.chat_models'"
  │   │     → errors/import-migration.md § E01 (P38)
  │   │
  │   ├── "cannot import name 'ConversationBufferMemory'"
  │   │     → errors/import-migration.md § E03 (P40)
  │   │
  │   ├── "cannot import name 'initialize_agent'"
  │   │     → errors/import-migration.md § E04 (P41)
  │   │
  │   ├── "No module named 'langchain_openai' / 'langchain_anthropic'"
  │   │     → pip install "langchain-<provider>>=1.0,<2.0"
  │   │
  │   └── anything else starting with ImportError
  │         → check package pins; `langchain-anthropic>=1.0` needs `anthropic>=0.40`
  │           → errors/import-migration.md § E06 (P66)
  │
  ├── 2. Is it an AttributeError?
  │   │
  │   ├── "'list' object has no attribute 'lower' / 'strip' / 'split' / 'format'"
  │   │     → errors/content-shape.md § E07 (P02)
  │   │     FIX: use msg.text() or the block-iterator extractor
  │   │
  │   ├── "module 'langchain' has no attribute 'LLMChain'"
  │   │     → errors/import-migration.md § E02 (P39)
  │   │     FIX: prompt | llm | StrOutputParser()
  │   │
  │   ├── "'AgentAction' object has no attribute 'tool_name'" (or inverse)
  │   │     → errors/import-migration.md § E05 (P42)
  │   │     FIX: use .tool_name on new, .tool on old; migrate to LangGraph
  │   │
  │   └── anything else — likely shape drift between LangChain versions
  │         → grep the attribute name in the `langchain-core` source
  │
  ├── 3. Is it a KeyError?
  │   │
  │   ├── Stack trace passes through runnables/passthrough.py or runnables/base.py
  │   │     → errors/content-shape.md § E08 (P06)
  │   │     FIX: add RunnableLambda debug probes; set_debug(True)
  │   │
  │   ├── Stack trace passes through prompts/chat.py or prompts/prompt.py
  │   │     → errors/content-shape.md § E09 (P57)
  │   │     FIX: MessagesPlaceholder or template_format="jinja2"
  │   │
  │   ├── KeyError: 'input' or 'content' inside tool_use block parsing (anthropic)
  │   │     → errors/import-migration.md § E06 (P66)
  │   │     FIX: bump anthropic to >=0.40 alongside langchain-anthropic>=1.0
  │   │
  │   └── anything else — inspect dict shape at each runnable stage
  │
  ├── 4. Is it a GraphRecursionError?
  │   │
  │   └── "Recursion limit of N reached without hitting a stop condition"
  │         → errors/graph-traps.md § E10 (P10, P55)
  │         FIX: recursion_limit=10, terminal edge on repeated tool calls
  │
  ├── 5. Is it a TypeError?
  │   │
  │   ├── "Object of type datetime / bytes / Decimal / set is not JSON serializable"
  │   │     → errors/graph-traps.md § E13 (P17)
  │   │     FIX: primitives-only state; JsonPlusSerializer for Pydantic
  │   │
  │   └── anything else involving async / coroutine
  │         → likely sync invoke() inside async endpoint — use ainvoke()
  │
  ├── 6. No exception, but behavior is wrong?
  │   │
  │   ├── Agent forgets conversation between turns
  │   │     → errors/graph-traps.md § E12 (P16)
  │   │     FIX: require thread_id on every invocation
  │   │
  │   ├── Graph returns input unchanged, no nodes executed
  │   │     → errors/graph-traps.md § E14 (P56)
  │   │     FIX: assert router return is in path_map; include END explicitly
  │   │
  │   ├── Agent returns "I couldn't find the answer" on every call
  │   │     → errors/graph-traps.md § E11 (P09)
  │   │     FIX: return_intermediate_steps=True, handle_parsing_errors=False
  │   │         or migrate to LangGraph create_react_agent
  │   │
  │   └── Token counts are zero during streaming
  │         → use astream_events(version="v2") and read on_chat_model_stream
  │
  └── 7. Exception class not listed above?
        │
        ├── anthropic.BadRequestError / openai.BadRequestError
        │     → check tool_choice / schema shape against provider docs
        │
        ├── pydantic.ValidationError
        │     → model added extra fields (P53) — set ConfigDict(extra="ignore")
        │     → or method="function_calling" dropped Optional[list[X]] (P03)
        │
        └── Other
              → search docs/pain-catalog.md for the class name or message substring
```

## Quick-match table

| First-line pattern of traceback | Entry | Reference |
|---|---|---|
| `ImportError: cannot import name 'ChatOpenAI'` | E01 | import-migration.md |
| `AttributeError: module 'langchain' has no attribute 'LLMChain'` | E02 | import-migration.md |
| `ImportError: cannot import name 'ConversationBufferMemory'` | E03 | import-migration.md |
| `ImportError: cannot import name 'initialize_agent'` | E04 | import-migration.md |
| `AttributeError: '<Agent...>' object has no attribute 'tool_name'` | E05 | import-migration.md |
| `KeyError: 'input'` in tool_use block | E06 | import-migration.md |
| `AttributeError: 'list' object has no attribute 'lower'` | E07 | content-shape.md |
| `KeyError: '<var>'` in runnables/ | E08 | content-shape.md |
| `KeyError: '<var>'` in prompts/ | E09 | content-shape.md |
| `GraphRecursionError: Recursion limit of <N>` | E10 | graph-traps.md |
| `AgentExecutor` returns "I couldn't find the answer" | E11 | graph-traps.md |
| Multi-turn agent forgets context | E12 | graph-traps.md |
| `TypeError: Object of type <...> is not JSON serializable` | E13 | graph-traps.md |
| Graph halts without reaching `END` | E14 | graph-traps.md |

## When the tree does not match

1. Check `docs/pain-catalog.md` for the exception class name or a substring of the message.
2. Search LangChain 1.0 / LangGraph 1.0 source on GitHub for the exact message literal:
   - `langchain-ai/langchain` for core / prompts / runnables
   - `langchain-ai/langgraph` for state / checkpointers / agents
3. If the error only reproduces against a specific provider, check the provider integration package (`langchain-anthropic`, `langchain-openai`, etc.) release notes.
4. Escalate to the main thread and file a pain-catalog extension request — do not silently add speculative fixes to this skill.

## Sources

- Pain catalog: `docs/pain-catalog.md`
- [LangChain source](https://github.com/langchain-ai/langchain)
- [LangGraph source](https://github.com/langchain-ai/langgraph)
- [LangChain 1.0 release notes](https://blog.langchain.com/langchain-langgraph-1dot0/)
