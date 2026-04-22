# Table Preservation in PDF RAG

Tables are **not** text. A 5-row financial table rendered as text-chunked content loses the column meanings when a single row is retrieved. A question like "what was Q3 revenue" returns a row like `2,457 | 2,891 | 3,104 | 3,456` with no idea which number is Q3. The fix is to detect tables, extract them as structured records, and index them **separately** from the prose.

## The P49 Failure Mode

`PyPDFLoader` splits a PDF into one `Document` per page. A table that spans a page break (common in financial filings, product specs) is literally torn in half. Page 1 has the header and rows 1-3; page 2 has rows 4-5 with no header. The chunks that end up in the vector index look like:

**Chunk from page 2 (no context):**
```
Q3 2025 | 3,104 | 28.4% | 892
Q4 2025 | 3,456 | 31.2% | 1,043
```

The LLM sees numbers with no column names. It hallucinates that the second column is "users in thousands" when it's actually "revenue in millions."

## The Fix: Table-Aware Loader + Structured Indexing

### Step 1 — Use `PyMuPDFLoader` for prose

```python
from langchain_community.document_loaders import PyMuPDFLoader

prose_docs = PyMuPDFLoader("10-Q-filing.pdf").load()
```

`PyMuPDFLoader` does NOT tear tables across pages the way `PyPDFLoader` does — it uses PyMuPDF (fitz) which handles layout better. But it still puts tables into the prose text, which is the next problem.

### Step 2 — Extract tables separately with `fitz.find_tables()`

```python
import fitz  # pymupdf

def extract_table_records(pdf_path: str) -> list[dict]:
    """Return one record per row, with column headers attached."""
    doc = fitz.open(pdf_path)
    records = []
    for page_num, page in enumerate(doc):
        tables = page.find_tables()
        for table_idx, table in enumerate(tables.tables):
            rows = table.extract()
            if not rows or len(rows) < 2:
                continue
            headers = [h.strip() if h else f"col_{i}" for i, h in enumerate(rows[0])]
            for row_idx, row in enumerate(rows[1:], start=1):
                cells = [(str(v).strip() if v else "") for v in row]
                # Render as key-value pairs — LLM-friendly, retrieval-friendly
                content = " | ".join(f"{h}: {v}" for h, v in zip(headers, cells))
                records.append({
                    "page_content": content,
                    "metadata": {
                        "source": pdf_path,
                        "page": page_num,
                        "table_idx": table_idx,
                        "row_idx": row_idx,
                        "record_type": "table_row",
                        "headers": headers,
                        **dict(zip(headers, cells)),
                    },
                })
    doc.close()
    return records
```

Each row becomes its own record with:
- `page_content`: `"Quarter: Q3 2025 | Revenue: 3,104 | Margin: 28.4% | EBITDA: 892"`
- `metadata`: preserves column values AND page number for citation

### Step 3 — Remove tables from prose chunks (avoid double-indexing)

After extracting tables, strip them from the prose to avoid indexing both:

```python
def strip_tables_from_text(page_text: str, tables: list) -> str:
    """Remove table bounding-box text from the page text."""
    # fitz tables have bbox; use page.get_text("blocks") and filter
    # Simpler: mark table rows with a sentinel and skip during splitting
    for table in tables:
        for row in table.extract() or []:
            row_text = " ".join(str(c) for c in row if c)
            if row_text:
                page_text = page_text.replace(row_text, "")
    return page_text
```

Or keep tables in prose AND index as records — but then tag prose chunks with `record_type="prose"` and filter during retrieval if you get duplicates.

### Step 4 — Index prose and tables together with hybrid retrieval

```python
from langchain_core.documents import Document

# Prose — language-aware splitter (see language-aware-splitters.md)
prose_chunks = md_splitter.split_documents(prose_docs)
for c in prose_chunks:
    c.metadata["record_type"] = "prose"

# Tables — one document per row
table_records = extract_table_records("10-Q-filing.pdf")
table_chunks = [
    Document(page_content=r["page_content"], metadata=r["metadata"])
    for r in table_records
]

# Index both together
store.add_documents(prose_chunks + table_chunks)
```

Retrieval on "what was Q3 revenue" returns:

1. The matching table row: `"Quarter: Q3 2025 | Revenue: 3,104 | Margin: 28.4% | EBITDA: 892"`
2. Prose chunks that mention Q3

The LLM has the number with its column meaning attached. No more hallucinated units.

## Alternative: `UnstructuredPDFLoader` with Element Mode

`UnstructuredPDFLoader(mode="elements", strategy="hi_res")` returns typed elements including tables:

```python
from langchain_community.document_loaders import UnstructuredPDFLoader

loader = UnstructuredPDFLoader(
    "10-Q-filing.pdf",
    mode="elements",
    strategy="hi_res",
)
elements = loader.load()

tables = [e for e in elements if e.metadata.get("category") == "Table"]
prose = [e for e in elements if e.metadata.get("category") != "Table"]
```

Trade-offs:
- **Pro**: no custom `fitz` code; handles scanned PDFs via OCR.
- **Con**: `hi_res` strategy is slow (~2-5s per page); ~500 MB of dependencies.

Use Unstructured for mixed scanned/digital corpora; use `fitz` directly for digital-only PDFs at scale.

## Querying a Table-Indexed Corpus

When the LLM needs numeric precision, inject the table row directly into the prompt:

```python
from langchain_core.prompts import ChatPromptTemplate

template = ChatPromptTemplate.from_messages([
    ("system", "Answer using ONLY the provided context. Cite page numbers."),
    ("human", "Question: {question}\n\nContext:\n{context}"),
])

# Filter retrieved docs to prefer table_row records for numeric questions
def prefers_table_for_numeric(question: str, docs: list) -> list:
    if any(kw in question.lower() for kw in ["revenue", "how much", "percent", "%", "margin"]):
        table_docs = [d for d in docs if d.metadata.get("record_type") == "table_row"]
        prose_docs = [d for d in docs if d.metadata.get("record_type") == "prose"]
        return table_docs[:3] + prose_docs[:2]
    return docs
```

## Validation

For a filing with known answers, check retrieval recall on numeric questions:

```python
EVAL_QUESTIONS = [
    ("What was Q3 2025 revenue?", "3,104"),
    ("What was the Q4 margin?", "31.2%"),
    # ...
]

for question, expected in EVAL_QUESTIONS:
    docs = store.similarity_search(question, k=5)
    found = any(expected in d.page_content for d in docs)
    assert found, f"missed: {question} → expected to find {expected}"
```

A healthy table-indexed corpus should hit > 90% recall on numeric questions. A prose-only index typically sits at 40-60%.

## Pain Catalog Anchors

- **P49** — `PyPDFLoader` tears tables by page. Fix: `PyMuPDFLoader` + `fitz.find_tables()` + structured records.
