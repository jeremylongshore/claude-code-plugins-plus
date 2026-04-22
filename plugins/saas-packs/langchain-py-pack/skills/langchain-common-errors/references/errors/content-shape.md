# Content-Shape & Prompt-Template Errors

Pain-catalog anchors: **P02, P06, P57**.

These three errors share a root cause: LangChain 1.0 surfaces provider-native shapes (lists of blocks, typed tool calls) but legacy and user code still assumes string-ish payloads. Stack traces point at user code, not LangChain — which is why they are mis-diagnosed as "my code is wrong."

Last verified against `langchain-core==1.0.0`, `langchain-anthropic==1.0.0`, `langchain-openai==1.0.0`.

---

## E07 — `AttributeError: 'list' object has no attribute 'lower'` (or `.strip()`, `.split()`, `.format()`)

**Pain:** P02

**Where you see it:** First production call against Claude after tests only exercised fake or OpenAI models. Also surfaces on OpenAI as soon as tools are bound.

**Example traceback:**

```
Traceback (most recent call last):
  File "app.py", line 42, in handle
    text = response.content.lower()
AttributeError: 'list' object has no attribute 'lower'
```

**Cause:** `AIMessage.content` is a `str` on simple OpenAI calls and a `list[dict | ContentBlock]` the instant any non-text block (`tool_use`, `thinking`, `image`, `document`, `tool_result`) enters the response. Claude responses are lists **whenever** `extended_thinking` is on or tools are bound. OpenAI becomes a list once tools are bound. Gemini is a list for anything multi-modal.

**Fix — preferred (LangChain 1.0 helper):**

```python
text = msg.text()  # Concatenates all text blocks. Handles both shapes. Returns "" if no text.
```

**Fix — manual extractor (when you need to filter specific block types):**

```python
from langchain_core.messages import AIMessage

def extract_text(msg: AIMessage) -> str:
    if isinstance(msg.content, str):
        return msg.content
    parts = []
    for block in msg.content:
        # Block may be a dict (provider-native) or a typed object (1.0 wrapper)
        btype = block.get("type") if isinstance(block, dict) else getattr(block, "type", None)
        if btype == "text":
            parts.append(block["text"] if isinstance(block, dict) else block.text)
    return "".join(parts)
```

**Adjacent traps:**

- `msg.content[0]["text"]` crashes when block 0 is `thinking` or `tool_use`. Iterate and filter — never index.
- Streaming deltas have the same shape — `chunk.content` is a `list[dict]` on Claude, so your token handler must filter too.
- In a chain, `prompt | llm | StrOutputParser()` silently swallows non-text blocks. Use `| RunnableLambda(extract_text)` if you need to preserve them for observability.

---

## E08 — `KeyError: 'question'` (or `'input'`, `'context'`) inside LCEL runnable internals

**Pain:** P06

**Where you see it:** Immediately after wiring a new `.pipe()` chain, or after adding a step that changes the dict shape mid-chain.

**Example traceback:**

```
Traceback (most recent call last):
  File ".../runnables/passthrough.py", line 451, in assign
    **step.invoke(input, config, **kwargs),
KeyError: 'question'
```

The stack trace names the key but **not** the upstream step that was supposed to produce it.

**Cause:** LCEL `RunnablePassthrough.assign()` and `{...}` dict compositions operate on dict inputs. If the upstream runnable returns a string, a list, or a dict with a different key, the error surfaces at the next `assign` or dict consumer — not where the shape was wrong.

**Fix — add a debug probe between stages:**

```python
from langchain_core.runnables import RunnableLambda
import logging

log = logging.getLogger(__name__)

def _probe(label):
    def _inner(x):
        log.warning("probe %s: type=%s keys=%s", label,
                    type(x).__name__,
                    list(x.keys()) if isinstance(x, dict) else "<not-dict>")
        return x
    return RunnableLambda(_inner).with_config({"run_name": f"probe::{label}"})

chain = (
    retriever
    | _probe("post-retrieve")
    | {"context": format_docs, "question": RunnablePassthrough()}
    | _probe("pre-prompt")
    | prompt
    | llm
    | StrOutputParser()
)
```

**Fix — enable LangChain global debug:**

```python
from langchain.globals import set_debug
set_debug(True)  # logs every intermediate value; very verbose, use locally
```

**Fix — type the chain:**

```python
from langchain_core.runnables import RunnableSerializable
chain: RunnableSerializable[dict, str] = prompt | llm | StrOutputParser()
```

Typing does not catch shape mismatches at runtime, but it forces you to declare the expected input shape and surfaces it in review.

---

## E09 — `KeyError: 'username'` when calling `prompt.invoke()` on user-supplied text containing `{` / `}`

**Pain:** P57

**Where you see it:** User pastes a code snippet, JSON blob, or CSS selector into a chat input. The chain crashes instead of responding.

**Example traceback:**

```
Traceback (most recent call last):
  File ".../prompts/chat.py", line 384, in format
    return self.prompt.format(**kwargs)
KeyError: 'username'
```

…when the user's message contained `"CREATE TABLE users ({username VARCHAR})"`.

**Cause:** `ChatPromptTemplate.from_messages([...])` defaults to f-string template parsing. User-provided text containing `{var}` markers is treated as a template variable and crashes the format call. Literal braces in Markdown, JSON, code, regexes, Jinja, and CSS all trigger this.

**Fix — for variable content, use `MessagesPlaceholder`:**

```python
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder

prompt = ChatPromptTemplate.from_messages([
    ("system", "You are a helpful assistant."),
    MessagesPlaceholder("history"),       # chat history — safe, not f-string-parsed
    ("human", "{question}"),               # bare template variable
])

prompt.invoke({"history": past_messages, "question": user_text})
```

`MessagesPlaceholder` inserts messages verbatim without f-string parsing. This is the right default for any variable-length or user-controlled content.

**Fix — for truly free-text templates, use jinja2:**

```python
prompt = ChatPromptTemplate.from_messages(
    [("human", "Summarize: {{ text }}")],
    template_format="jinja2",
)
prompt.invoke({"text": "function foo() { return {a:1}; }"})  # literal braces are fine
```

**Fix — to preserve f-string syntax but allow literal braces, escape them:**

```python
prompt = ChatPromptTemplate.from_messages([
    ("system", "Return JSON like {{\"key\": \"value\"}}."),  # {{ and }} escape to { and }
    ("human", "{question}"),
])
```

This is the lowest-risk path for system messages that must contain literal braces (e.g., describing JSON output).

**Testing:** Add a unit test that feeds the prompt a string with unbalanced `{`:

```python
def test_prompt_safe_on_braces():
    prompt.invoke({"question": "SELECT * FROM t WHERE j = '{\"a\":1}'"})  # must not raise
```

Run it on every prompt revision. If it raises, your prompt is not safe for user input.

## Sources

- Pain catalog: `docs/pain-catalog.md` (P02, P06, P57, P58)
- [`AIMessage` API](https://python.langchain.com/api_reference/core/messages/langchain_core.messages.ai.AIMessage.html)
- [Content blocks reference](https://python.langchain.com/docs/concepts/messages/#content-blocks)
- [`ChatPromptTemplate` docs](https://python.langchain.com/docs/concepts/prompt_templates/)
- [LCEL concepts](https://python.langchain.com/docs/concepts/lcel/)
- [Debugging chains](https://python.langchain.com/docs/how_to/debugging/)
