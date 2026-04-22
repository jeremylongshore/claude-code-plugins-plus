# Migration Detection — grep-based Pre-flight

Run these commands from the repo root before starting the upgrade. Each command pairs to a pain code and a codemod pattern. Collect the hits into a file — it is the migration work list.

## The Eight Checks

```bash
# P38 — Provider import paths (chat models, llms, embeddings, vectorstores)
grep -rn "from langchain\.chat_models" --include="*.py" .
grep -rn "from langchain\.llms" --include="*.py" .
grep -rn "from langchain\.embeddings" --include="*.py" .
grep -rn "from langchain\.vectorstores" --include="*.py" .

# P39 — LLMChain and siblings
grep -rn "from langchain\.chains\b" --include="*.py" .
grep -rn "\bLLMChain\b" --include="*.py" .
grep -rn "\bConversationChain\b" --include="*.py" .
grep -rn "\bSequentialChain\b" --include="*.py" .
grep -rn "\bRetrievalQA\b" --include="*.py" .

# P40 — Memory classes
grep -rn "from langchain\.memory" --include="*.py" .
grep -rn "ConversationBufferMemory\|ConversationBufferWindowMemory\|ConversationSummaryMemory" --include="*.py" .

# P41 — Legacy agent constructors
grep -rn "initialize_agent\|AgentType\." --include="*.py" .

# P42 — AgentAction field access
grep -rn "\.tool_input\b\|AgentAction\." --include="*.py" .
grep -rn "intermediate_steps" --include="*.py" .

# P66 — Peer-pin drift between langchain-anthropic and anthropic
grep -rn "langchain-anthropic" requirements*.txt pyproject.toml 2>/dev/null
grep -rn "^anthropic" requirements*.txt pyproject.toml 2>/dev/null

# P67 — Soft-deprecated streaming API
grep -rn "astream_log\b" --include="*.py" .
```

## Bundled one-shot script (one-liner, not a committed script)

For a single run of all of the above piped into a work-list:

```bash
{ \
  grep -rn "from langchain\.chat_models\|from langchain\.llms\|from langchain\.embeddings\|from langchain\.vectorstores" --include="*.py" . ; \
  grep -rn "from langchain\.chains\b\|LLMChain\|ConversationChain\|SequentialChain\|RetrievalQA" --include="*.py" . ; \
  grep -rn "from langchain\.memory\|ConversationBufferMemory\|ConversationBufferWindowMemory\|ConversationSummaryMemory" --include="*.py" . ; \
  grep -rn "initialize_agent\|AgentType\." --include="*.py" . ; \
  grep -rn "\.tool_input\b\|intermediate_steps" --include="*.py" . ; \
  grep -rn "astream_log\b" --include="*.py" . ; \
} > langchain-0.3-hits.txt
wc -l langchain-0.3-hits.txt
```

The line count is a rough lower bound on the number of call sites to touch. Typical outcomes:

| Line count | Interpretation |
|---|---|
| 0 | Already on 1.0 patterns. Only the version bump and peer-pin (P66) remain. |
| 1–20 | Small codebase or isolated usage. One afternoon of codemod work. |
| 21–100 | Typical mid-sized service. Plan a two-day migration with staged commits per module. |
| 100+ | Multiple teams own parts of the code. Do Phase 2 of the playbook per team, not per file. |

## Reading the Output

Each hit is `path:line_no:matched_line`. Group by `path`, then by pain code, then assign each file to the codemod pattern in [codemod-patterns.md](codemod-patterns.md):

| Matched on | Pain | Apply pattern |
|---|---|---|
| `from langchain.chat_models` etc. | P38 | Pattern 1 |
| `LLMChain`, `RetrievalQA`, `SequentialChain` | P39 | Pattern 2 |
| `initialize_agent`, `AgentType.` | P41 | Pattern 3 |
| `ConversationBufferMemory` etc. | P40 | Pattern 4 |
| `astream_log` | P67 | Pattern 5 |
| `.tool_input`, `intermediate_steps` | P42 | Pattern 6 |
| `langchain-anthropic` in requirements without `anthropic >= 0.40` | P66 | Pattern 7 |

## Re-running After the Codemod

Run the same block after Phase 2 of the playbook. Every check should return zero hits except intentional test fixtures that pin 0.3 for comparison. Any non-test hit is unfinished migration work.

## False Positives to Expect

- Third-party code vendored into `.venv/` or `node_modules/` — exclude with `--exclude-dir`. On most setups, grep already skips these by default if they are gitignored.
- Documentation strings that reference the old API for context. Flag these for the prose update but do not treat them as code migrations.
- Tests that intentionally assert 0.3 backwards-compat shims (rare). Annotate with `# noqa: langchain-migration` and exclude from the recount.
