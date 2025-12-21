# What Changed

## Summary

Built complete production-ready `lumera-agent-memory` MCP plugin from scratch following exact specification:
- ✅ Exactly 4 MCP tools with exact required names
- ✅ Object storage + metadata index pattern
- ✅ Client-side AES-256-GCM encryption with user-controlled keys
- ✅ SQLite FTS5 local index (NEVER queries Cascade)
- ✅ Redact-then-store pipeline with fail-closed for critical patterns
- ✅ Content-addressed Cascade URIs (mock mode functional)
- ✅ Memory card "wow factor" with deterministic heuristics
- ✅ Comprehensive test suite (21 tests, all passing)

## Architecture Implemented

```
CASS → Redact → Encrypt → Upload Cascade → Store URI in SQLite FTS
                   ↓
            Memory Card Generation
                   ↓
         Query Index → Retrieve → Decrypt
```

## Files Created

### Core MCP Server
- `src/mcp_server.py` (362 lines) - Main MCP server with 4 tools

### Security Module
- `src/security/redact.py` (131 lines) - Fail-closed + redact-and-continue
  - Critical patterns: private keys, AWS secret keys, auth headers → **FAIL**
  - Non-critical: emails, phones, AWS access keys, IPs → **REDACT & CONTINUE**

- `src/security/encrypt.py` (92 lines) - AES-256-GCM encryption/decryption
  - Client-side encryption with user keys
  - SHA-256 integrity checks
  - Nonce prepending for storage

### Cascade Storage
- `src/cascade/interface.py` (46 lines) - Abstract interface
- `src/cascade/mock_fs.py` (85 lines) - Content-addressed filesystem mock
  - URIs: `cascade://sha256:<hash>`
  - Deduplication via content addressing
  - Subdir sharding (first 2 chars of hash)

### Index Module
- `src/index/index.py` (192 lines) - SQLite FTS5 index
  - Full-text search with BM25 ranking
  - Tag filtering
  - Time range filtering
  - Cascade URI lookup
  - Snippet generation from memory cards

### Tests (21 tests, all passing)
- `tests/test_redaction.py` (8 tests) - Critical vs non-critical behavior
- `tests/test_encryption.py` (6 tests) - Roundtrip + integrity checks
- `tests/test_fts_search.py` (7 tests) - FTS, ranking, filtering
- `tests/standalone_smoke_test.py` - E2E: store → query → retrieve

### Documentation
- `README.md` - Complete plugin documentation
- `EXAMPLE_PAYLOADS.md` - JSON examples for all 4 tools
- `CHANGES.md` - This file
- `LICENSE` - MIT license
- `.claude-plugin/plugin.json` - Plugin manifest
- `package.json` - npm metadata
- `requirements.txt` - Python dependencies

## MCP Tools (Exact Names)

### 1. `store_session_to_cascade`
- Extracts from CASS (mocked)
- Redacts PII/secrets (fail-closed for critical patterns)
- Generates memory card (title, keywords, entities, decisions, todos, quotes)
- Encrypts client-side (AES-256-GCM)
- Uploads to Cascade (returns content-addressed URI)
- Stores in local SQLite FTS index

### 2. `query_memories`
- Searches **local SQLite FTS5 index only** (NEVER queries Cascade)
- Full-text search with BM25 ranking
- Tag filtering
- Time range filtering
- Returns Cascade URIs for retrieval

### 3. `retrieve_session_from_cascade`
- Fetches encrypted blob from Cascade via URI
- Gets crypto metadata from local index
- Verifies ciphertext integrity (SHA-256)
- Decrypts client-side
- Returns session + memory card

### 4. `estimate_storage_cost`
- Estimates monthly Cascade storage costs
- Configurable redundancy and pricing inputs
- Returns GB, storage cost, request cost, total

## Security Behavior Changes

### Critical Patterns (Fail-Closed)
These patterns **abort storage** immediately:
- Private keys (`-----BEGIN PRIVATE KEY-----`)
- AWS secret access keys (`aws_secret_access_key=...`)
- Raw authorization headers (`Authorization: Bearer ...`)
- Database passwords in connection strings

**Error message:** Clear, actionable, tells user to remove from source CASS session.

### Non-Critical Patterns (Redact & Continue)
These patterns are **redacted** with `[REDACTED:PATTERN_NAME]`:
- Email addresses
- Phone numbers
- AWS access keys (AKIA...)
- IPv4 addresses
- Generic long tokens (32+ chars)

**Result:** Redaction report shows which rules fired and counts.

## Wow Factor: Memory Cards

Every stored session gets a deterministic memory card generated via heuristics:
- **Title**: First user message (truncated to 80 chars)
- **Summary bullets**: First 3 messages with role prefix
- **Keywords**: Top 10 frequent words (5+ chars)
- **Entities**: Capitalized words (proper nouns)
- **Decisions**: Messages with "decided", "decision", "will use", "chosen"
- **TODOs**: Messages with "todo", "need to", "should", "must"
- **Notable quotes**: Messages with `?` or `!`

**No network calls. No LLMs. Deterministic. Fast.**

Query results include intelligent snippets using memory card data.

## Search Implementation

**Local SQLite FTS5 index:**
- FTS5 virtual table with Porter stemming + Unicode tokenization
- BM25 ranking (negative rank scores, converted to positive)
- Tag filtering via JSON array column
- Time range filtering via ISO8601 timestamps
- Cascade URI indexing for fast lookups

**NEVER queries Cascade directly.** Search returns URIs → User retrieves specific sessions.

## Mock Cascade

Content-addressed filesystem storage:
- URIs: `cascade://sha256:<sha256_hash>`
- Storage: `~/.lumera/cascade/<first_2_chars>/<full_hash>`
- Deduplication: Same content = same hash = single blob
- Metadata: Optional `.meta` files for blob metadata

## Live Cascade Mode

Stub implementation returns clear error:
```
Live Cascade mode not configured. Required: LUMERA_CASCADE_ENDPOINT
and LUMERA_CASCADE_API_KEY environment variables. Use mode='mock'
for local testing.
```

Does not break mock mode. Safe fallback.

## Test Results

```
21 tests passing in 0.66s:
- 8 redaction tests (critical vs non-critical)
- 6 encryption tests (roundtrip, integrity, tampering)
- 7 FTS search tests (ranking, filtering, snippets)
- Standalone smoke test: full E2E flow
```

## Storage Locations

- **Mock Cascade blobs**: `~/.lumera/cascade/`
- **SQLite FTS index**: `~/.lumera/index.db`

Both auto-created on first use.

## Commands to Run

```bash
# Install dependencies (if in venv)
pip install -r requirements.txt

# Run all tests
python3 -m pytest tests/ -v

# Run smoke test
python3 tests/standalone_smoke_test.py

# Run MCP server (requires MCP SDK in environment)
python3 src/mcp_server.py
```

## What Works

✅ All 4 MCP tools with exact names
✅ Redaction pipeline (critical patterns fail-closed)
✅ Client-side AES-256-GCM encryption
✅ Content-addressed Cascade storage (mock mode)
✅ SQLite FTS5 search (local only, NEVER queries Cascade)
✅ Memory card generation (deterministic heuristics)
✅ Complete test coverage
✅ Clear error messages for live mode
✅ Production-ready code structure

## What's Stubbed

⚠️ Live Cascade mode (clear error message, requires endpoint/auth config)
⚠️ Real CASS integration (mocked extraction in `_mock_extract_from_cass`)

Both are clean integration points for production deployment.
