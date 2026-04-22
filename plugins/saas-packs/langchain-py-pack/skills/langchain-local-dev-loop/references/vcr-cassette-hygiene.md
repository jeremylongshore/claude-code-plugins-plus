# VCR Cassette Hygiene Reference

Recording real API calls once and replaying forever is the fastest integration
test pattern we have. It is also the fastest way to leak an API key into a
public repo if you let `vcrpy` record headers by default. This reference is
the full playbook.

## The leak (P44)

`vcrpy` records request headers unless you tell it not to. Anthropic and OpenAI
send the key in `Authorization: Bearer ...` or `x-api-key: ...`. The cassette
is a YAML file committed with the test. PR review is the last line of defense
before the key hits a public branch — which is too late, because even a deleted
commit on a public repo is scraped by credential harvesters within minutes.

**The key is compromised the moment the commit is pushed.** Revoke immediately.

## Baseline `vcr_config` (safe defaults)

```python
# tests/conftest.py
import pytest

@pytest.fixture(scope="module")
def vcr_config():
    return {
        # Strip every header that carries a credential:
        "filter_headers": [
            "authorization",
            "x-api-key",
            "anthropic-version",
            "anthropic-beta",
            "openai-organization",
            "openai-project",
            "x-goog-api-key",
            "cookie",
            "set-cookie",
        ],
        # Strip query-string credentials (Google's ?key= pattern):
        "filter_query_parameters": ["api_key", "key", "access_token"],
        # Strip request-body fields that some providers accept in the body:
        "filter_post_data_parameters": ["api_key"],
        # Default: replay only. Recording requires --record-mode=once on CLI.
        "record_mode": "none",
        # Body matching is strong; headers vary run-to-run on the LLM side:
        "match_on": ["method", "scheme", "host", "port", "path", "query", "body"],
    }
```

## Recording flow (once, locally, with a real key)

```bash
# Preconditions:
# 1. conftest.py has filter_headers configured
# 2. .env or shell has ANTHROPIC_API_KEY / OPENAI_API_KEY etc.

# Record:
pytest --record-mode=once tests/integration/test_summarize.py

# Post-record audit — hard-grep for common key prefixes:
grep -REn '(sk-ant-[a-zA-Z0-9_-]+|sk-[a-zA-Z0-9]{20,}|Bearer\s+[a-zA-Z0-9_-]{20,}|AIza[0-9A-Za-z-_]{35})' tests/cassettes/
# Expected output: no matches. Any match → STOP, revoke key, re-record.

# Commit:
git add tests/cassettes/
git commit -m "test: record summarize cassette"
```

## Record modes (when to use each)

| Mode | Behavior | When |
|------|----------|------|
| `none` | Replay only. Missing cassette → test fails. | **Default in CI.** |
| `once` | Record if cassette missing, else replay. | First recording, local only. |
| `new_episodes` | Replay existing, record new interactions. | Adding a follow-up request to an existing cassette. |
| `all` | Re-record everything. | Provider changed the response shape. |

Never set `record_mode=all` in `vcr_config` — it will silently overwrite
cassettes and rotate in a fresh real key every CI run.

## Pre-commit hook — hard-gate against leaks

`.pre-commit-config.yaml`:

```yaml
repos:
  - repo: local
    hooks:
      - id: cassette-no-keys
        name: Block API keys in VCR cassettes
        entry: bash scripts/check-cassettes.sh
        language: system
        files: ^tests/cassettes/.*\.(yaml|yml)$
```

`scripts/check-cassettes.sh`:

```bash
#!/usr/bin/env bash
set -e
LEAKED=$(git diff --cached -U0 -- 'tests/cassettes/' | \
    grep -E '(sk-ant-[a-zA-Z0-9_-]+|sk-[a-zA-Z0-9]{20,}|Bearer\s+[a-zA-Z0-9_-]{20,}|AIza[0-9A-Za-z-_]{35})' || true)
if [ -n "$LEAKED" ]; then
    echo "ERROR: API key pattern in staged cassette:" >&2
    echo "$LEAKED" >&2
    exit 1
fi
```

## Per-test vs shared cassettes

- **Per-test (`pytest-recording` default)** — one `.yaml` per test function,
  stored at `tests/cassettes/<test_module>/<test_name>.yaml`. Cheap to
  regenerate individual tests. Preferred.
- **Shared** — multiple tests replay from one cassette. Brittle; one
  test-order change invalidates everything. Use only for expensive
  setup-shaped cassettes (auth exchange, initial embedding batch).

## Cassette drift — when replay fails

```
vcr.errors.CannotOverwriteExistingCassetteException:
  Can't overwrite existing cassette at ... in your current record mode ('none').
```

The test's request shape changed. Decide:

1. **Intentional change** → `pytest --record-mode=new_episodes` locally,
   inspect diff, commit.
2. **Unintentional (code regression)** → fix the request-building code;
   cassette is correct.

## PR review checklist for cassettes

- [ ] `filter_headers` includes `authorization`, `x-api-key`, every provider-specific key header
- [ ] `grep -E '(sk-|Bearer |AIza)' tests/cassettes/` returns zero matches
- [ ] Pre-commit hook `cassette-no-keys` is installed and passing
- [ ] `record_mode` default is `none` (no silent re-records)
- [ ] Cassette file sizes are reasonable (< 100KB each — a 10MB cassette usually means response body was not trimmed)
- [ ] Reviewer has confirmed at least one cassette replays by checking out the branch and running `pytest -m integration`
