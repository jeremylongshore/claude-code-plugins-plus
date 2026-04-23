# Sanitization Checklist

A debug bundle is effectively public the moment it leaves your machine —
uploaded to Slack, attached to a Discord bug report, forwarded to a support
ticket, pasted into a chat with a colleague. Every bundle MUST pass the
sanitization pass below before it is packaged.

This list is a cross-reference to the forthcoming `langchain-security-basics`
skill's redaction patterns. Use that skill for the production-grade upstream
middleware — this checklist is the last-mile guard before `tar.gz`.

## What must be redacted

### Tier 1 — credential material (blockers; bundle is unsafe to share)

| Class | Example pattern | Regex |
|---|---|---|
| OpenAI API key | `sk-proj-...`, `sk-...` | `sk-[A-Za-z0-9_-]{16,}` |
| Anthropic API key | `sk-ant-api03-...` | `sk-ant-[A-Za-z0-9_-]{16,}` |
| Google API key | `AIza...` | `AIza[A-Za-z0-9_-]{35}` |
| LangSmith key | `lsv2_pt_...`, `lsv2_sk_...` | `lsv2_(pt|sk)_[A-Za-z0-9]{32,}` |
| Bearer token (HTTP header) | `Authorization: Bearer <token>` | `(?i)bearer\s+[A-Za-z0-9._~+/=-]{20,}` |
| AWS access key | `AKIA...` | `AKIA[0-9A-Z]{16}` |
| AWS secret | 40-char base64-ish | `(?i)aws(.{0,20})?['\"][0-9a-zA-Z/+]{40}['\"]` |
| GitHub token | `ghp_...`, `ghs_...`, `gho_...` | `gh[pous]_[A-Za-z0-9]{36}` |
| Slack token | `xox[abpsr]-...` | `xox[abpsr]-[A-Za-z0-9-]{10,}` |
| Private key block | `-----BEGIN ... PRIVATE KEY-----` | `-----BEGIN [A-Z ]*PRIVATE KEY-----[\s\S]*?-----END [A-Z ]*PRIVATE KEY-----` |
| JDBC / DB URI with password | `postgres://user:pass@host/db` | `[a-z]+://[^:/]+:[^@]+@[^/\s]+` |

### Tier 2 — session / auth material

| Class | Example |
|---|---|
| Cookie header | `Cookie: session=abc123; csrf=...` |
| Set-Cookie response | `Set-Cookie: sid=...` |
| OAuth refresh token | usually long base64 string in JSON `refresh_token` field |
| SAML assertion | XML `<saml:Assertion>` blobs |
| JWT | three base64 segments joined by dots; redact if found in URLs or headers |

### Tier 3 — PII (caller's responsibility to declare)

PII is domain-specific. The bundle tool ships with *no default PII regexes*
because false positives cost more than false negatives here — you configure
them. The canonical classes are:

| Class | Pattern | Notes |
|---|---|---|
| Email | `[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}` | Enable for customer-facing apps |
| US phone | `\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}` | Many false positives on order IDs — tune |
| SSN | `\d{3}-\d{2}-\d{4}` | Enable for health/financial |
| Credit card | Luhn-valid 13-19 digits | Enable for payments; prefer upstream tokenization |
| IP address | `\b\d{1,3}(\.\d{1,3}){3}\b` | Often load-bearing for debugging — redact only last octet |

### Tier 4 — internal URLs and hostnames

Internal hostnames and VPN-only URLs leak infrastructure shape. Configure a
redaction list:

```yaml
internal_url_patterns:
  - "https?://[^/\\s]*\\.corp\\.example\\.com[^\\s]*"
  - "https?://10\\.\\d+\\.\\d+\\.\\d+[^\\s]*"
  - "https?://10\\.\\d+[^\\s]*"
```

## Where to apply the pass

Sanitization runs **after** all files are written to the bundle staging dir
and **before** the tar.gz is created. Order:

1. `manifest.yaml` — env-var names only (see env-manifest-template.md); still
   run the pass in case a value leaked via `notes:`.
2. `events.jsonl` — highest-risk file; every `on_chat_model_start` / `on_tool_start`
   contains raw inputs. Redact line-by-line.
3. `callbacks.txt` — records have `input`/`output_snippet` fields, capped at
   500 chars each; still redact.
4. `langsmith.url` — safe, but verify URL does not embed an API key parameter.
5. `notes.txt` (free-form engineer notes) — human-provided; redact.

## Implementation — streaming redaction

For JSONL, redact per-line; for YAML/text, read, redact, write. A single
regex pass with `re.compile` caches patterns:

```python
import re
from pathlib import Path

DEFAULT_PATTERNS: list[tuple[str, str]] = [
    # (name, regex) — order matters: specific before generic
    ("openai_key",    r"sk-proj-[A-Za-z0-9_-]{16,}|sk-[A-Za-z0-9_-]{32,}"),
    ("anthropic_key", r"sk-ant-[A-Za-z0-9_-]{16,}"),
    ("google_key",    r"AIza[A-Za-z0-9_-]{35}"),
    ("langsmith_key", r"lsv2_(?:pt|sk)_[A-Za-z0-9]{32,}"),
    ("gh_token",      r"gh[pousr]_[A-Za-z0-9]{36,}"),
    ("slack_token",   r"xox[abpsr]-[A-Za-z0-9-]{10,}"),
    ("bearer",        r"(?i)bearer\s+[A-Za-z0-9._~+/=-]{20,}"),
    ("db_uri",        r"[a-z]+://[^:/\s]+:[^@\s]+@[^/\s]+"),
    ("private_key",   r"-----BEGIN [A-Z ]*PRIVATE KEY-----[\s\S]*?-----END [A-Z ]*PRIVATE KEY-----"),
]

def sanitize_text(text: str, patterns=None) -> tuple[str, dict[str, int]]:
    """Redact matches, return (cleaned_text, counts_by_pattern)."""
    patterns = patterns or DEFAULT_PATTERNS
    counts: dict[str, int] = {}
    for name, pat in patterns:
        compiled = re.compile(pat)
        new, n = compiled.subn(f"[REDACTED:{name}]", text)
        if n:
            counts[name] = n
            text = new
    return text, counts

def sanitize_file(path: Path, patterns=None) -> dict[str, int]:
    text = path.read_text()
    cleaned, counts = sanitize_text(text, patterns)
    path.write_text(cleaned)
    return counts
```

## Pre-upload scan

After the tar.gz is written, **extract it to a temp dir and scan once more**.
This is the safety net that catches formats the redactor missed (e.g., a
base64-encoded secret that happened to land inside an `on_tool_end` output):

```bash
tmp=$(mktemp -d)
tar -xzf bundle-*.tar.gz -C "$tmp"
# High-signal greps
grep -RInE "sk-[A-Za-z0-9_-]{20,}" "$tmp" && echo "UNSAFE: OpenAI key pattern found" && exit 1
grep -RInE "sk-ant-" "$tmp"                && echo "UNSAFE: Anthropic key pattern found" && exit 1
grep -RInE "AKIA[0-9A-Z]{16}" "$tmp"       && echo "UNSAFE: AWS key pattern found" && exit 1
grep -RInE "-----BEGIN .*PRIVATE KEY" "$tmp" && echo "UNSAFE: private key found" && exit 1
rm -rf "$tmp"
echo "clean"
```

If any of these fire, the bundle is **not safe to share**. Re-run the
sanitization pass with the missing pattern added to `DEFAULT_PATTERNS`, or
delete the offending file from the bundle and re-archive.

## False-positive management

The most common false positive is `sk-` appearing in a JSON Schema description
("sk- prefix indicates OpenAI credentials" — ironically, explaining the regex).
Two mitigations:

1. Require a minimum length suffix (`[A-Za-z0-9_-]{32,}` instead of `{16,}`).
2. Negative lookbehind for `"description"` context (regex gets complex; often
   easier to hand-inspect the match and add a `--allow-substring` flag).

## Logging the redactions

The bundle's `MANIFEST.yaml` index (separate from `manifest.yaml` env snapshot)
records how many patterns matched, so a reviewer knows whether the bundle was
"clean at capture" or "aggressively scrubbed":

```yaml
sanitization:
  ran_at: "2026-04-21T18:42:19Z"
  pattern_counts:
    openai_key: 3
    anthropic_key: 1
    bearer: 2
  files_scanned: ["events.jsonl", "callbacks.txt", "manifest.yaml", "notes.txt"]
```
