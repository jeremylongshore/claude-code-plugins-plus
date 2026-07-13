# langchain-common-errors — One-Pager

Paste-match catalog of real LangChain 1.0 / LangGraph 1.0 tracebacks — find the named cause and the named fix before you speculate.

## The Problem

Twelve-plus LangChain 1.0 and LangGraph 1.0 exceptions show up every week in production: `ImportError: cannot import name 'ChatOpenAI' from 'langchain.chat_models'`, `AttributeError: 'list' object has no attribute 'lower'`, `GraphRecursionError: Recursion limit of 25 reached`, `TypeError: Object of type datetime is not JSON serializable`, `KeyError: 'question'` deep in LCEL internals, and more. Stack traces are ambiguous, docs sprawl across 0.2/0.3/1.0 eras, and engineers lose 30–90 minutes per incident re-deriving the fix each time.

## The Solution

This skill is a consolidated index of 14 LangChain 1.0 / LangGraph 1.0 errors grouped into 5 categories (imports, content-shape, chains, agents, graphs), with a triage decision tree that routes any paste-in traceback to the right reference file. Each catalog entry opens with the exact error message string, names the cause in one sentence with a pain-catalog code (P02, P06, P09, P10, P16, P17, P38, P39, P40, P41, P42, P55, P56, P57, P66), and gives a one-line fix plus a reference-file pointer for the deep walk-through.

## Who / What / When

| Aspect | Details |
|--------|---------|
| **Who** | Any Python engineer holding a LangChain 1.0 or LangGraph 1.0 traceback and looking for a named fix — not more speculative documentation |
| **What** | 14-entry paste-match catalog, triage decision tree, 4 deep reference files (import-migration, content-shape, graph-traps, triage-decision-tree), and 2 worked walk-throughs (0.2 → 1.0 import migration and `GraphRecursionError` triage) |
| **When** | During incident response, on a 0.3 → 1.0 upgrade when tests explode, or any time a stack trace mentions `langchain_`, `langgraph`, `OutputParserException`, `GraphRecursionError`, `AIMessage`, or `ChatPromptTemplate` |

## Key Features

1. **Exact-match catalog** — Every entry opens with the literal exception class and message string you see in your terminal, so Ctrl-F on the traceback lands on the fix in under 10 seconds
2. **Triage decision tree** — Routes any traceback by first line (`ImportError` → import-migration, `AttributeError` on `.content` → content-shape, `GraphRecursionError` → graph-traps) so you never read the whole catalog
3. **Pain-catalog anchored** — Every error cites a P## code from `docs/pain-catalog.md`, verifiable against LangChain 1.0.x and LangGraph 1.0.x pinned versions (2026-04-21)

## Quick Start

See [SKILL.md](../SKILL.md) for full instructions.
