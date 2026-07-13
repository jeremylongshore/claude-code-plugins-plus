# langchain-prompt-engineering — One-Pager

Manage LangChain 1.0 prompts like code — LangSmith hub versioning, Claude-native XML tag conventions, semantic few-shot selection, and A/B-testable extraction schemas.

## The Problem

A team has 47 prompt strings embedded as f-string literals across 12 Python files — nobody knows which version is live, rollback requires a deploy, and A/B tests require shipping code. A user pastes a JSON snippet containing `{` and the whole chain throws `KeyError` deep inside `ChatPromptTemplate.from_messages` (pain catalog entry P57). On Claude specifically, prompts that perform on GPT-4o underperform because persona instructions are buried in the user message instead of the top-level `system` field (P58), and user-provided documents are not wrapped in `<document>` tags so the model can't tell instructions from data.

## The Solution

Move prompts into a `prompts/` module as `ChatPromptTemplate` objects, version them in the LangSmith prompt hub with `Client.push_prompt`/`pull_prompt`, pin production to specific commit hashes, switch `template_format="jinja2"` so literal `{` in user input stops breaking, apply Claude XML conventions (`<document>`, `<example>`, `<context>` tags + system-field persona), and select few-shot examples dynamically with `SemanticSimilarityExampleSelector`. A/B tests become two `pull_prompt()` calls gated by a feature flag.

## Who / What / When

| Aspect | Details |
|--------|---------|
| **Who** | Senior engineers, researchers, and PhDs who write prompts daily and need version control, provider portability, and A/B testability rather than hardcoded f-strings |
| **What** | Prompts-as-code module, LangSmith hub push/pull/pin workflow, jinja2 templates that survive `{` in user input, Claude XML-tag conventions, semantic/MMR few-shot selectors, discriminated-union Pydantic extraction schemas, A/B test wiring, 4 references (LangSmith hub, Claude conventions, few-shot selectors, extraction schemas) |
| **When** | After `langchain-model-inference` is in place and before scaling to more than 5 prompts — the refactor from scattered f-strings to a versioned prompt library gets exponentially more painful the longer you wait |

## Key Features

1. **LangSmith prompt hub with commit-pinned production pulls** — `Client.push_prompt("name", object=template)` on merge; `Client.pull_prompt("name:abc12345")` (8-char commit hash) for production pinning; rollback is a one-line commit swap, not a deploy
2. **Claude-native conventions baked in** — XML-tag wrappers (`<document>`, `<example>`, `<context>`) for user-provided content, system persona in the top-level `system` field (not a `HumanMessage`), extended-thinking prompting patterns, and jinja2 template format that survives literal `{` in user input
3. **Dynamic few-shot selection, not glued-in examples** — `SemanticSimilarityExampleSelector` picks 3-10 relevant examples per query from an embedded corpus; `MaxMarginalRelevanceExampleSelector` adds diversity for ambiguous inputs; static list only for tiny fixed sets

## Quick Start

See [SKILL.md](../SKILL.md) for full instructions.
