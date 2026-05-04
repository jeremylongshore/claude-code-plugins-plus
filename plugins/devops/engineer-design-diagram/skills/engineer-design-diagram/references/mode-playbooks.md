# Mode Playbooks

Per-mode workflows for engineer-design-diagram. Each playbook covers input contract, steps, output contract, and failure modes.

## Table of Contents

- [generate](#generate)
- [diff](#diff)
- [trace](#trace)
- [watch](#watch)

## generate

Produce an architecture view of the current repository.

**Input contract:**
- Current working directory is a git repo (or has discoverable manifests)
- Optional: `$ARGUMENTS[1]` = path to scope (default: repo root)

**Steps:**
1. Read DCI block output from SKILL.md activation.
2. Build node set from docker-compose services, k8s Deployments/Services, terraform resources, package manifest names.
3. Build edge set from `depends_on`, exposed ports + HTTP client imports (via Grep), k8s Service selectors, terraform resource references.
4. Classify each node's role per [drawing-rules.md § Role inference](drawing-rules.md#role-inference).
5. Fill `templates/base.html` per [drawing-rules.md](drawing-rules.md). Write to `$CWD/.arch/generate-<timestamp>.html`.
6. Write fingerprint via `scripts/fingerprint.py write`.
7. Run `scripts/validate_html.py` on output. If ARIA or no-externals check fails, re-fill template.
8. Echo Mermaid equivalent to chat.
9. Open HTML via `scripts/open_in_browser.sh`.

**Output contract:**
- `$CWD/.arch/generate-<ISO-timestamp>.html` — single-file HTML, offline-capable
- Mermaid text block in chat
- Updated `${CLAUDE_PLUGIN_DATA}/arch-state.json`

**Failure modes:**
- No manifests detected → ask user to describe system in prose, render prose-only diagram
- >50 nodes → auto-switch to `templates/mermaid-fallback.html`
- Layout collision detected → retry with Mermaid

## diff

Produce a before/after architecture view with delta highlighting, for PR review.

**Input contract:**
- Current branch is NOT the default branch
- Default branch discoverable via `origin/HEAD`, `main`, `master`, or `trunk`

**Steps:**
1. Probe default branch: `git symbolic-ref refs/remotes/origin/HEAD` → fallback chain.
2. Read prior fingerprint from `${CLAUDE_PLUGIN_DATA}/arch-state.json` if it exists, else generate from default branch checkout.
3. Re-run DCI on working tree (current branch).
4. Compute diff: `added_nodes`, `removed_nodes`, `changed_nodes` (role change), `added_edges`, `removed_edges`.
5. Fill `templates/base.html` with all nodes from the NEW state. Apply `class="delta-added"` / `delta-removed` / `delta-changed` per [drawing-rules.md § Delta Markers](drawing-rules.md#delta-markers-diff-mode).
6. Write output to `$CWD/.arch/diff-<timestamp>.html`.
7. Update fingerprint to reflect the new state.
8. Emit summary line: `Added N nodes, M edges. Removed X nodes, Y edges.`

**Output contract:**
- `$CWD/.arch/diff-<ISO-timestamp>.html` with delta classes on changed elements
- Mermaid text block
- One-line delta summary in chat
- Updated fingerprint

**Failure modes:**
- No default branch found → use `HEAD~1` as base, warn user
- Both branches have identical structure → output "No structural changes detected" and exit without writing

## trace

Render a sequence diagram from a stack trace, log span, or incident event.

**Input contract:**
- `$ARGUMENTS[1]` = path to trace file (required)
- Supported formats: Sentry JSON, OpenTelemetry span JSON, raw stack trace text

**Steps:**
1. Detect format by file shape: `.json` → inspect top-level keys; `.txt` or no extension → assume raw stack trace.
2. Parse using appropriate parser:
   - **Sentry**: extract `exception.values[].stacktrace.frames[]` + `spans[]`
   - **OTel**: parse `resourceSpans[].scopeSpans[].spans[]` by `parentSpanId` for call order
   - **Raw**: regex `at ServiceName.methodName(file.ext:line)` lines
3. Collapse frames into lifelines (one per service/module).
4. Build message list with timestamps where available.
5. Fill `templates/sequence.html`. Mark the final/error arrow with `class="error"`.
6. Write to `$CWD/.arch/trace-<timestamp>.html`.
7. **Do not write fingerprint** (trace mode doesn't alter architectural state).

**Output contract:**
- `$CWD/.arch/trace-<ISO-timestamp>.html` with sequence diagram
- Mermaid `sequenceDiagram` text block
- No fingerprint write

**Failure modes:**
- Unknown format → emit Mermaid-only sequence with best-effort parsing, flag for user review
- <2 lifelines parseable → output "Trace too shallow for sequence diagram" with raw trace excerpt

## watch

Detect architectural drift by comparing current repo state against last stored fingerprint.

**Input contract:**
- `${CLAUDE_PLUGIN_DATA}/arch-state.json` exists (from a prior generate/diff run)

**Steps:**
1. Load prior fingerprint.
2. Re-run DCI on current working tree.
3. Build new node/edge graph.
4. Compute structural diff (same algorithm as diff mode, Step 4).
5. For each delta, cite the source file + line that justifies it (from DCI output and Grep).
6. Emit markdown report — **no HTML render** in watch mode.

**Output contract:**
- Markdown report with sections `Added`, `Removed`, `Changed`
- Each bullet cites `source:file:line`
- Final line: `New graph_fingerprint: <sha256>`
- Updated fingerprint (optional — ask user before overwriting if drift is significant)

**Failure modes:**
- No prior fingerprint → output "No baseline found. Run `/design:generate` first to establish a fingerprint."
- Schema version mismatch → output "Fingerprint schema drift. Run `/design:generate` to re-baseline."
- No drift detected → output "No structural drift since <prior timestamp>."
