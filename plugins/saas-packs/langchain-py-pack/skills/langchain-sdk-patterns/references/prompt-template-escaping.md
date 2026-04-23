# Prompt Template Escaping

`ChatPromptTemplate.from_messages` defaults to `template_format="f-string"`.
The f-string parser treats every `{` in every string as a variable marker —
so the moment a user pastes JSON, code, or a Markdown block with `{...}`, the
chain raises `KeyError` at invoke time (pain-catalog P57).

## The failure mode

```python
from langchain_core.prompts import ChatPromptTemplate

template = ChatPromptTemplate.from_messages([
    ("system", "Reply with a one-line summary"),
    ("human", "Error: {user_message}"),
])

template.invoke({"user_message": "Server returned {\"error\": \"oops\"}"})
# KeyError: '"error"'
```

The template parser reads `{"error"` in the rendered string as a variable
named `"error"` — which does not exist in the input dict.

## Fix 1: Switch to Jinja2

Jinja2 uses `{{ var }}` for substitution and treats bare `{` as literal:

```python
template = ChatPromptTemplate.from_messages(
    [
        ("system", "Reply with a one-line summary"),
        ("human", "Error: {{ user_message }}"),
    ],
    template_format="jinja2",
)

template.invoke({"user_message": 'Server returned {"error": "oops"}'})
# OK — renders correctly
```

**Use jinja2 whenever a template variable can contain user-provided free text.**
Support tickets, transcripts, code blocks, JSON payloads, logs, chat history —
anything not authored by you.

## Fix 2: Escape braces in f-string mode

If you need to keep f-string format (for example because the rest of the codebase
uses it), escape literal braces by doubling them:

```python
template = ChatPromptTemplate.from_messages([
    ("system", "Output JSON matching the schema {{'name': str, 'age': int}}"),
    ("human", "{user_message}"),
])
```

Only the `{var}` sites remain as variables; `{{` and `}}` render as literal
`{` and `}`. This works for **instructions you write** but not for **user
input at runtime** — if the user's text contains `{`, it is still parsed.

## Fix 3: `MessagesPlaceholder` for chat history

A chat history is a `list[BaseMessage]`, not a string. Never render it with
f-string substitution. Use `MessagesPlaceholder`:

```python
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder

template = ChatPromptTemplate.from_messages([
    ("system", "You are a helpful assistant."),
    MessagesPlaceholder("history"),
    ("human", "{{ question }}"),
], template_format="jinja2")

template.invoke({
    "history": [prior_human, prior_ai],   # list[BaseMessage]
    "question": "What did I just ask?",
})
```

`MessagesPlaceholder("history")` inserts the message list at that position
without running either template engine over its contents.

## When f-string is correct

For **trusted, template-author-written** instructions, f-string is fine and
faster. Rule of thumb: if every `{var}` corresponds to a dict key whose value
is a fixed-shape ID, number, or short identifier that cannot contain `{`,
f-string is the right choice. If any value is free text from a user, an LLM
output, a log, or a document, switch to jinja2.

## Jinja2 side effects

Jinja2 supports control flow:

```python
tmpl = """
{% if tier == "enterprise" %}
You have access to advanced features.
{% else %}
Standard tier response.
{% endif %}

User question: {{ question }}
"""
```

Handy for conditional system prompts. Keep logic simple — complex branching
belongs in a `RunnableBranch`, not in a template.

## Testing prompt templates

Always unit-test templates against adversarial inputs:

```python
def test_template_survives_json_input():
    rendered = template.invoke({
        "user_message": '{"nested": {"json": true}}',
    })
    assert "nested" in str(rendered)

def test_template_survives_code_block():
    rendered = template.invoke({
        "user_message": "def f(x): return {x: 1}",
    })
    assert "return" in str(rendered)
```

If these pass, your template is brace-safe. If they throw `KeyError`, flip to
jinja2 or escape the braces.

## Migration checklist

1. Grep for `ChatPromptTemplate.from_messages`
2. Identify which templates have variables that can contain user input
3. Add `template_format="jinja2"` and change `{var}` to `{{ var }}` in those
4. Leave trusted internal templates on f-string for speed
5. Add an adversarial-input unit test per template
