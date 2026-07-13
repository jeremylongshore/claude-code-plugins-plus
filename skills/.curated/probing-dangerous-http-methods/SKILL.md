---
name: probing-dangerous-http-methods
description: |
  Probe a target for HTTP methods that should not be enabled in
  production — TRACE (XST attack), unrestricted PUT/DELETE,
  DEBUG/CONNECT, WebDAV (PROPFIND/MKCOL/COPY/MOVE), and Allow header
  enumeration.
  Use when: penetration test rules of engagement include HTTP method
  testing, OR a load balancer change went live and you suspect default
  methods were exposed.
  Threshold: TRACE returns 200 on any path (XST), PUT/DELETE returns
  anything other than 405/403/404 on a non-API endpoint, OPTIONS Allow
  header lists DEBUG/CONNECT/PROPFIND, or WebDAV methods succeed.
  Trigger with: "audit http methods", "trace check", "options
  enumeration", "webdav probe".
allowed-tools:
  - Read
  - Bash(python3:*)
  - Bash(curl:*)
disallowed-tools:
  - Bash(rm:*)
  - Edit(/etc/*)
version: 3.0.0-dev
author: Jeremy Longshore <jeremy@intentsolutions.io>
license: MIT
compatibility: Designed for Claude Code
tags:
  - security
  - http-methods
  - xst
  - webdav
  - pentest
---

# Probing Dangerous HTTP Methods

## Overview

Most HTTP methods beyond GET/POST/HEAD are vestigial — leftover from
WebDAV authoring stacks of the early 2000s, debugging features in
legacy servers, or default-enabled methods nobody disabled at install
time. Each enabled method that the application doesn't use is an
attack surface: TRACE enables Cross-Site Tracing (XST), PUT enables
arbitrary file upload to unprotected paths, CONNECT enables proxy
abuse against internal services, WebDAV enables directory manipulation.

This skill probes the canonical method set and grades each based on
its presence and response.

## When the skill produces findings

| Finding | Severity | Threshold | Affected control |
|---|---|---|---|
| TRACE method enabled | **HIGH** | TRACE returns 200 with request echo | OWASP A05:2021, CWE-693 |
| PUT method enabled outside API path | **HIGH** | PUT returns 200/201/204 on non-API path | CWE-434 |
| DELETE method enabled outside API path | **HIGH** | DELETE returns 200/204 on non-API path | CWE-285 |
| CONNECT method enabled | **CRITICAL** | CONNECT returns 200 (proxy abuse open) | CWE-441 |
| DEBUG method enabled | **HIGH** | DEBUG returns response (legacy IIS / dev servers) | CWE-489 |
| WebDAV methods enabled (PROPFIND/MKCOL/COPY/MOVE) | **HIGH** | Any return 207 or 201 | CWE-538 |
| Allow header discloses unused methods | **LOW** | OPTIONS Allow includes methods app doesn't use | CWE-200 |
| OPTIONS returns full method enumeration | **LOW** | Allow:* or broad list | CWE-200 |

## Prerequisites

- Python 3.9+
- Authorization for non-local targets

## Instructions

### Step 1 — Confirm authorization

```text
"Do you have authorization to perform HTTP method probing on this
 target? I need confirmation before proceeding."
```

### Step 2 — Run the scanner

```bash
python3 ${CLAUDE_PLUGIN_ROOT}/skills/probing-dangerous-http-methods/scripts/probe_methods.py \
    https://example.com \
    --authorized
```

Options:

```
Usage: probe_methods.py URL [OPTIONS]

Options:
  --authorized      Attest authorization (required)
  --output FILE
  --format FMT      json | jsonl | markdown (default: markdown)
  --min-severity SEV (default: info)
  --timeout SECS
  --is-api          Treat URL as API endpoint (relaxes PUT/DELETE checks)
```

By default the scanner treats the URL as a non-API endpoint where
PUT/DELETE should return 405. With `--is-api`, those methods are
expected and don't trigger findings — only the auth checks behind them
matter (delegated to other skills).

### Step 3 — Interpret findings

CRITICAL CONNECT-open = your reverse proxy is letting external clients
connect to arbitrary internal hosts (e.g., metadata endpoints in
AWS/GCP). Ship same-hour fix.

HIGH TRACE = XST attack open. Combined with any XSS, attacker can
read HttpOnly cookies via XHR. Ship-within-sprint fix.

HIGH WebDAV = file upload + manipulation surface. Audit `references/
PLAYBOOK.md` § disabling WebDAV.

### Step 4 — Cross-skill chaining

After this skill, suggest:

- `auditing-cors-policy` (#3) if Allow-Methods:* surfaced
- `detecting-debug-endpoints` (#7) for the broader exposed-feature
  audit if DEBUG/TRACE both fired

## Examples

### Example 1 — Post-deploy method audit

User: "We rolled out a new ALB config. Audit the method surface."

```bash
python3 ${CLAUDE_PLUGIN_ROOT}/skills/probing-dangerous-http-methods/scripts/probe_methods.py \
    https://api.example.com \
    --authorized --is-api --min-severity high
```

### Example 2 — TRACE / XST audit after XSS finding

User: "Found XSS on /search; checking if XST chain is possible."

```bash
python3 ${CLAUDE_PLUGIN_ROOT}/skills/probing-dangerous-http-methods/scripts/probe_methods.py \
    https://example.com \
    --authorized
```

If TRACE-enabled finding fires, the XST chain works: attacker XSS
issues a TRACE request via XHR, the server echoes the request
(including HttpOnly cookies that XHR-set-cookies access can't normally
read), JavaScript reads the response body, full session theft.

### Example 3 — WebDAV legacy audit on a recently-acquired domain

User: "We just acquired example.io — quick method-surface check before
we re-point DNS."

```bash
python3 ${CLAUDE_PLUGIN_ROOT}/skills/probing-dangerous-http-methods/scripts/probe_methods.py \
    https://example.io \
    --authorized --min-severity medium
```

Often surfaces decade-old WebDAV / DEBUG defaults that nobody disabled
on the previous owner's stack.

## Output

JSON / JSONL / Markdown. Exit 0 / 1 / 2 per `lib/report.py`.

## Error Handling

- **Method returns 405** → expected behavior, no finding
- **Method returns 403** → access-controlled (acceptable), no finding,
  but INFO note recorded
- **Method returns 500** → INFO finding flagging error-handling concern
- **Connection error** → exit 2

## Resources

- `references/THEORY.md` — Per-method attack semantics
- `references/PLAYBOOK.md` — How to disable each method per server type
- `../analyzing-tls-config/references/AUTHORIZATION.md` — Active-scan
  authorization
