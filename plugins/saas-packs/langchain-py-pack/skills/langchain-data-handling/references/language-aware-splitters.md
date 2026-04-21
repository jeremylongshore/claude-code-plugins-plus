# Language-Aware Splitters

`RecursiveCharacterTextSplitter.from_language(Language.X)` swaps the default separator list for a language-specific list that respects structural boundaries. This is the P13 fix — the default separators break inside code fences in Markdown; the `MARKDOWN` variant treats fences as atomic.

## Supported Languages (LangChain 1.0)

From `langchain_text_splitters.Language`:

| Enum value | Separator priority (first = most preferred split point) |
|---|---|
| `Language.CPP` | `\nclass `, `\nvoid `, `\nint `, `\nfloat `, `\nif `, `\nfor `, `\nwhile `, `\nswitch `, `\ncase `, `\n\n`, `\n`, ` `, `""` |
| `Language.GO` | `\nfunc `, `\nvar `, `\nconst `, `\ntype `, `\nif `, `\nfor `, `\nswitch `, `\ncase `, `\n\n`, `\n`, ` `, `""` |
| `Language.JAVA` | `\nclass `, `\npublic `, `\nprotected `, `\nprivate `, `\nstatic `, `\nif `, `\nfor `, `\nwhile `, `\nswitch `, `\ncase `, `\n\n`, `\n`, ` `, `""` |
| `Language.JS` / `Language.TS` | `\nfunction `, `\nconst `, `\nlet `, `\nvar `, `\nclass `, `\nif `, `\nfor `, `\nwhile `, `\nswitch `, `\ncase `, `\ndefault `, `\n\n`, `\n`, ` `, `""` |
| `Language.PHP` | `\nfunction `, `\nclass `, `\nif `, `\nforeach `, `\nwhile `, `\ndo `, `\nswitch `, `\ncase `, `\n\n`, `\n`, ` `, `""` |
| `Language.PROTO` | `\nmessage `, `\nservice `, `\nenum `, `\noption `, `\nimport `, `\nsyntax `, `\n\n`, `\n`, ` `, `""` |
| `Language.PYTHON` | `\nclass `, `\ndef `, `\n\tdef `, `\n\n`, `\n`, ` `, `""` |
| `Language.RST` | `\n=+\n`, `\n-+\n`, `\n\*+\n`, `\n\n.. *\n\n`, `\n\n`, `\n`, ` `, `""` |
| `Language.RUBY` | `\ndef `, `\nclass `, `\nif `, `\nunless `, `\nwhile `, `\nfor `, `\ndo `, `\nbegin `, `\nrescue `, `\n\n`, `\n`, ` `, `""` |
| `Language.RUST` | `\nfn `, `\nconst `, `\nlet `, `\nif `, `\nwhile `, `\nfor `, `\nloop `, `\nmatch `, `\nconst `, `\n\n`, `\n`, ` `, `""` |
| `Language.SCALA` | `\nclass `, `\nobject `, `\ndef `, `\nval `, `\nvar `, `\nif `, `\nfor `, `\nwhile `, `\nmatch `, `\ncase `, `\n\n`, `\n`, ` `, `""` |
| `Language.SWIFT` | `\nfunc `, `\nclass `, `\nstruct `, `\nenum `, `\nif `, `\nfor `, `\nwhile `, `\ndo `, `\nswitch `, `\ncase `, `\n\n`, `\n`, ` `, `""` |
| `Language.MARKDOWN` | `\n#{1,6} `, ` ```\n`, `\n\*\*\*+\n`, `\n---+\n`, `\n___+\n`, `\n\n`, `\n`, ` `, `""` |
| `Language.LATEX` | `\n\\\\chapter{`, `\n\\\\section{`, `\n\\\\subsection{`, `\n\\\\subsubsection{`, `\n\\\\begin{enumerate}`, ... |
| `Language.HTML` | `<body`, `<div`, `<p`, `<br`, `<li`, `<h1` ... `<h6`, `<span`, `<table`, `<tr`, `<td`, `<th`, `<ul`, ... |
| `Language.SOL` | `\npragma `, `\nusing `, `\ncontract `, `\ninterface `, `\nlibrary `, `\nconstructor `, `\nfunction `, ... |
| `Language.CSHARP` | `\ninterface `, `\nenum `, `\nimplements `, `\ndelegate `, `\nevent `, `\nclass `, `\nfunction `, ... |
| `Language.COBOL` | `\nIDENTIFICATION DIVISION.`, `\nENVIRONMENT DIVISION.`, `\nDATA DIVISION.`, `\nPROCEDURE DIVISION.`, ... |

## Why Markdown Needs Its Own Variant (P13)

The default `RecursiveCharacterTextSplitter` separator order is:

```python
["\n\n", "\n", " ", ""]
```

Given this Markdown:

````markdown
### The `trim_messages` function

Trim message history to fit a token budget.

```python
def trim_messages(messages, max_tokens, strategy="last"):
    total = 0
    kept = []
    for msg in reversed(messages):
        total += count_tokens(msg)
        if total > max_tokens:
            break
        kept.append(msg)
    return list(reversed(kept))
```

The `strategy="last"` argument keeps newer messages.
````

With `chunk_size=200` and default separators, the splitter sees the blank line inside the code fence as a valid split point. The resulting chunks look like:

**Chunk 1:**
````
### The `trim_messages` function

Trim message history to fit a token budget.

```python
def trim_messages(messages, max_tokens, strategy="last"):
    total = 0
    kept = []
````

**Chunk 2:**
````
    for msg in reversed(messages):
        total += count_tokens(msg)
        if total > max_tokens:
            break
        kept.append(msg)
    return list(reversed(kept))
```

The `strategy="last"` argument keeps newer messages.
````

The closing triple-backtick is in chunk 2; chunk 1 has an orphan opening fence. Retrieval on "how does `trim_messages` work" returns chunk 1, the LLM sees a function signature and a broken code block, and hallucinates the body.

### The Markdown variant fix

```python
from langchain_text_splitters import RecursiveCharacterTextSplitter, Language

md_splitter = RecursiveCharacterTextSplitter.from_language(
    Language.MARKDOWN,
    chunk_size=1000,
    chunk_overlap=100,
)
```

The `MARKDOWN` separator list includes `` ` ```\n` `` (the closing fence) **before** `\n\n`, so the splitter prefers to split on fence boundaries. A chunk will contain a complete fence or none at all.

## Python Language Variant

For Python source files:

```python
py_splitter = RecursiveCharacterTextSplitter.from_language(
    Language.PYTHON,
    chunk_size=1500,
    chunk_overlap=150,
)
```

The `PYTHON` list puts `\nclass `, `\ndef `, `\n\tdef ` first. A chunk will start at a class or function boundary when possible. Imports and module docstrings end up in their own chunk — tag them with metadata (`chunk_type="imports"`) for higher-precision retrieval on "where is X imported" queries.

## Custom Separators (When a Language Variant Doesn't Exist)

For formats with no enum variant (e.g., YAML, Dockerfile, custom DSLs):

```python
yaml_splitter = RecursiveCharacterTextSplitter(
    chunk_size=800,
    chunk_overlap=80,
    separators=[
        "\n\n",           # document separator
        "\n- ",           # list item (root-level)
        "\n  - ",         # nested list item
        "\n",
        " ",
        "",
    ],
)
```

Rule: order separators from **most structural to least**. The splitter tries each in order; if a chunk still exceeds `chunk_size`, it falls to the next separator.

## Code-Fence Regex (When You Must Custom-Detect)

If you're building a custom splitter and need to preserve triple-backtick fences:

```python
import re

FENCE_RE = re.compile(r"^```[\w\-\+]*\s*$", re.MULTILINE)

def fence_aware_split(text: str, chunk_size: int) -> list[str]:
    """Split text on blank lines but never inside a triple-backtick fence."""
    chunks = []
    buf = []
    in_fence = False
    size = 0
    for line in text.splitlines(keepends=True):
        if FENCE_RE.match(line.strip()):
            in_fence = not in_fence
        buf.append(line)
        size += len(line)
        if not in_fence and line.strip() == "" and size >= chunk_size:
            chunks.append("".join(buf))
            buf = []
            size = 0
    if buf:
        chunks.append("".join(buf))
    return chunks
```

Use this only when the built-in `Language.MARKDOWN` is insufficient (e.g., nested fences in MDX).

## HTMLHeaderTextSplitter for Long HTML

For long-form HTML with heading hierarchy:

```python
from langchain_text_splitters import HTMLHeaderTextSplitter

splitter = HTMLHeaderTextSplitter(
    headers_to_split_on=[
        ("h1", "Header 1"),
        ("h2", "Header 2"),
        ("h3", "Header 3"),
    ],
)
chunks = splitter.split_text(html_string)
# Each chunk has metadata like {"Header 1": "Introduction", "Header 2": "Motivation"}
```

Headers become `metadata` fields — retrieval can filter on section, and the LLM gets the section context in the prompt.

## Verification

After splitting, verify code fences are intact:

```python
for chunk in chunks:
    open_fences = chunk.page_content.count("```")
    assert open_fences % 2 == 0, f"orphan fence in chunk: {chunk.metadata}"
```

If this fails, you're on the default splitter and P13 is biting. Swap to `from_language(Language.MARKDOWN)`.

## Pain Catalog Anchors

- **P13** — Default separators break inside code fences. Fix: `from_language(Language.MARKDOWN)` for Markdown, `Language.PYTHON` for Python source.
