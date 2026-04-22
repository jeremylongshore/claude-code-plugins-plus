# Loader Selection Matrix

Per-format loader reference for LangChain 1.0. Each row: preferred loader, alternatives, strengths, gotchas, and cost characteristics.

## Matrix

| Format | Preferred loader | Alternatives | Strengths | Gotchas | Cost |
|---|---|---|---|---|---|
| PDF with tables | `PyMuPDFLoader` | `UnstructuredPDFLoader`, `PDFPlumberLoader` | Table detection via `page.find_tables()`; preserves layout; fast (C backend) | OCR for scanned PDFs requires Tesseract; > 5 MB risks OOM | Free (local); ~100ms per page |
| PDF text-only | `PyPDFLoader` | `PDFMinerLoader` | Simple; stdlib-compatible; splits per page | Tears tables (P49); loses layout | Free (local); ~20ms per page |
| PDF scanned (image) | `UnstructuredPDFLoader(mode="elements", strategy="hi_res")` | `AzureAIDocumentIntelligenceLoader` | OCR built in; element-typed output | Slow (~2-5s per page); Tesseract dependency | Free local / paid cloud |
| Web page (public) | `WebBaseLoader` with custom UA | `AsyncHtmlLoader`, `PlaywrightURLLoader` | Fast; minimal deps; BeautifulSoup parse | Cloudflare 403 with default UA (P50); no JS execution | Free; respect rate limits |
| Web page (JS-rendered) | `PlaywrightURLLoader` | `SeleniumURLLoader` | Runs JavaScript; handles SPAs | ~2-5s per page; browser install required | Free; heavy (~200MB browser) |
| Sitemap / RSS | `SitemapLoader`, `RSSFeedLoader` | — | Structured, cacheable; site-owner-sanctioned | Requires the site to publish one | Free; courteous |
| Markdown (docs site) | `UnstructuredMarkdownLoader` | `TextLoader` | Front-matter extraction; heading metadata | Element mode (`mode="elements"`) changes chunk shape | Free (local) |
| HTML long-form | `WebBaseLoader` + `HTMLHeaderTextSplitter` | `UnstructuredHTMLLoader` | Header hierarchy as metadata | Custom CSS selectors need `bs_kwargs` | Free (local) |
| Code repo | `GenericLoader.from_filesystem(..., parser=LanguageParser(Language.PYTHON))` | `DirectoryLoader` as text | Per-function chunks; language-aware | Language parser list is finite; polyglot repos need multiple passes | Free (local) |
| Corpus (many files) | `DirectoryLoader(glob=...)` | One-by-one in a loop | Parallel via `use_multithreading=True`; progress bar | `loader_cls` must match all files; mixed formats need conditional logic | Free; I/O bound |
| Office docs | `UnstructuredWordDocumentLoader`, `UnstructuredPowerPointLoader` | `Docx2txtLoader` | Table + image awareness | Unstructured is heavy (~500MB deps) | Free (local) |
| CSV / Excel | `CSVLoader`, `UnstructuredExcelLoader` | `pandas` → custom Document | One row per Document; column-as-metadata | Header row handling differs; large files OOM | Free (local) |
| JSON / JSONL | `JSONLoader(jq_schema=...)` | — | Flexible field extraction via `jq` | `jq_schema` is required; typos fail silently | Free (local) |
| S3 / GCS / Azure blob | `S3FileLoader`, `GCSFileLoader`, `AzureBlobStorageFileLoader` | — | Cloud-native; IAM-authed | Double data transfer if you then re-upload to vector store | Egress $ |
| Google Drive | `GoogleDriveLoader` | — | OAuth-authed; mime-aware | Requires service account + shared folder | Free (API quota) |
| YouTube transcripts | `YoutubeLoader` | `YoutubeAudioLoader` + Whisper | Fast; free when captions exist | Captions may be auto-generated (noisy); no captions → audio loader + STT $ |

## Selection Rules

1. **Know the worst content you'll hit.** If the corpus contains any PDF with tables, use `PyMuPDFLoader` everywhere — don't mix loaders inside a single index unless you tag chunks with the loader source.
2. **Always set a User-Agent.** Web loaders default to bot-looking UAs. Sites with Cloudflare, Akamai, or Cloudfront bot protection return 403 or interstitial HTML (P50). Use a realistic desktop UA.
3. **Check `robots.txt` before crawling.** `urllib.robotparser` takes 3 lines. See [Crawler Hygiene](crawler-hygiene.md).
4. **Prefer structured sources.** Sitemap > RSS > paginated HTML > full crawl. Each step down is more fragile, more expensive, and ruder to the site owner.
5. **For mixed-format corpora, write a dispatcher.** A small function that routes each file path to the right loader beats `DirectoryLoader` with a single `loader_cls` for polyglot inputs.

## Validation Pattern

After loading, before splitting, sanity-check:

```python
for doc in docs:
    assert doc.page_content.strip(), f"empty content in {doc.metadata}"
    assert len(doc.page_content) > 100, f"suspiciously short: {doc.metadata}"
    # Cloudflare interstitial detection
    assert "checking your browser" not in doc.page_content.lower()
    assert "access denied" not in doc.page_content.lower()[:500]
```

If any of these fail, the loader is not giving you what you think it is.

## Cost and Latency Summary

- **Local loaders** (PyMuPDF, Unstructured, BeautifulSoup): free, ~10-100ms per document, I/O bound at scale.
- **Browser loaders** (Playwright, Selenium): free but ~2-5s per page and ~200 MB of browser runtime.
- **Cloud OCR** (Azure Document Intelligence, AWS Textract): $1-10 per 1000 pages, ~500ms-2s per page, best for scanned PDFs at scale.
- **LLM-based extraction** (e.g., GPT-4o vision for PDF): ~$0.01-0.10 per page; use only when structure is too variable for deterministic parsers.

## Pain Catalog Anchors

- **P49** — `PyPDFLoader` tears tables. Preferred loader: `PyMuPDFLoader`.
- **P50** — `WebBaseLoader` default UA gets 403 on Cloudflare. Fix: `header_template={"User-Agent": "Mozilla/5.0 ..."}`.
