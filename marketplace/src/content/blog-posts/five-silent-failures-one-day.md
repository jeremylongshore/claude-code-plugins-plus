---
title: "Five Silent Failures in One Day"
description: "Five tools said PASS without doing the work — pr-prescreen, .gitignore, prettier, SSH deploy, and a regex. Each silent failure and the guard that catches it."
date: "2026-05-16"
tags: ["ci-cd", "debugging", "devops", "claude-code", "release-engineering"]
featured: false
---
**A silent failure is when a tool reports PASS without doing the work it was supposed to do — the legitimate empty-set case and the broken-but-silent case produce identical output, and nothing downstream can tell them apart.**

A green check is not evidence of work. It is evidence that whatever ran did not raise an error. Those are different claims, and on 2026-05-16 the difference surfaced five times in five unrelated systems before lunch.

The pattern is the same in all five: a tool reported PASS without doing the work it was supposed to do. Not a wrong answer — no answer, dressed up as a correct one. The legitimate empty-set case and the broken-but-silent case produced identical output. CI was green. Reviewers saw nothing to push back on. The signal that something was wrong came from downstream consumers noticing the work was missing.

The five instances, in the order they were found:

1. A CI prescreen that ran on zero plugins and called itself green
2. A `.gitignore` rule that silently dropped plugin configs from every commit
3. Prettier that reformatted an 11,000-line catalog and exited 0
4. An SSH deploy that succeeded by doing nothing
5. A regex that quietly skipped matches because the `/g` flag left state behind

Each one shipped past code review. Each one was caught by a downstream user, not by the gate that was supposed to catch it. Each one has now been re-armed with a guard whose job is to assert the work actually happened — not to assert that the command exited zero.

## 1. The prescreen that ran on zero plugins

Repo: `claude-code-plugins`, PR #730.

The `pr-prescreen.yml` workflow's "Compute changed plugin paths" step combined `gh api --paginate` with `--jq` in a single pipe:

```yaml
- name: Compute changed plugin paths
  run: |
    gh api --paginate \
      "/repos/${{ github.repository }}/pulls/${{ github.event.pull_request.number }}/files" \
      --jq '.[].filename' \
      | grep -E '^plugins/[^/]+/' \
      | cut -d/ -f1-2 \
      | sort -u > changed-plugins.txt || true
```

This works on every local shell. On the GitHub Actions runner, the `--paginate` + `--jq` combination silently produced empty stdout. No error. No exit code. Just nothing on the pipe. The downstream `grep | cut | sort -u` happily processed zero lines and wrote an empty file. The trailing `|| true` swallowed any failure that might have escaped the pipeline.

The classifier then read `changed-plugins.txt`, saw zero entries, and emitted `PASS: no plugin paths matched the PR diff`. Two external PRs — #726 and #728, the first contributions through the new pipeline — both landed false PASS verdicts on PRs that obviously added new plugin directories.

The fix is two changes and a guard:

```yaml
- name: Fetch changed files
  run: |
    gh api --paginate \
      "/repos/${{ github.repository }}/pulls/${{ github.event.pull_request.number }}/files" \
      > pr-files.json

- name: Extract plugin paths
  run: |
    jq -r '.[].filename' pr-files.json \
      | grep -E '^plugins/[^/]+/' \
      | cut -d/ -f1-2 \
      | sort -u > changed-plugins.txt

- name: Sanity guard
  run: |
    if jq -r '.[].filename' pr-files.json | grep -qE '^plugins/'; then
      if [ ! -s changed-plugins.txt ]; then
        echo "HARD_BLOCK: PR touches plugins/ but extraction produced zero dirs"
        exit 1
      fi
    fi
```

Splitting `gh api --paginate` from `jq` removes the pipe-buffering interaction that ate stdout. Dropping the blanket `|| true` lets real errors propagate. The third step is the actual fix: it asserts that *if* the PR diff touched any plugin path, the extraction must have produced at least one row. "I found nothing" becomes "I would have found something — fail loud."

## 2. The gitignore that ate plugin configs

Repo: `claude-code-plugins`, PR #733.

The root `.gitignore` contained one line that was never meant to apply globally:

```text
.mcp.json
```

The original intent was dev-local — devs sometimes drop a `.mcp.json` at the repo root for personal MCP servers. The pattern matched everywhere. Three plugins — `slack-channel`, `pr-to-spec`, `x-bug-triage` — had a `.mcp.json` on disk because the mirror sync wrote them, and git silently never tracked any of the three. The mirror produced the file. The working tree showed the file. `git status` showed it as ignored. Nothing red anywhere.

Plugins without their `.mcp.json` fail the MCP handshake at install time. Claude Code can't determine how to spawn the server. The plugin loads, registers nothing, and the user sees commands that do nothing.

A second silent failure lived in the same PR. The mirror's `sources.yaml` listed source files explicitly:

```yaml
plugins/x-bug-triage:
  sources:
    - server.ts
    - lib.ts
```

`server.ts` imports `journal.ts`, `manifest.ts`, `policy.ts`, `supervisor.ts` — none of which were in the allow-list. The mirror shipped a non-functional server, not because anything errored, but because the include list silently skipped the missing files. No "file not in sources" warning. No diff check. Just a partial build that compiled because the imports themselves were valid module references at type-check time but missing at runtime.

The fix:

```text
# .gitignore
.mcp.json
!plugins/**/.mcp.json
```

```yaml
plugins/x-bug-triage:
  sources:
    include: "*.ts"
    exclude: ["*.test.ts", "*.spec.ts"]
```

The negation rule re-tracks plugin configs. The glob-with-exclude replaces named-file allow-lists with a pattern that can't silently miss a new file. The three affected `.mcp.json` files were force-added in the same commit.

## 3. Prettier that reformatted 11,000 lines and exited 0

Repo: `claude-code-plugins`, PR #730 (same PR as the prescreen failure).

`.claude-plugin/marketplace.extended.json` is the canonical plugin catalog — eleven thousand lines, hand-formatted with deliberate multi-line `keywords` arrays for git-diff hygiene:

```json
{
  "name": "example-plugin",
  "keywords": [
    "ci",
    "validation",
    "marketplace"
  ]
}
```

A contributor's format-on-save action ran prettier across the catalog. Prettier collapsed every keyword array to a single line:

```json
{
  "name": "example-plugin",
  "keywords": ["ci", "validation", "marketplace"]
}
```

The JSON was still valid. Prettier exited 0. The `validate-plugins.yml` workflow loaded the catalog, parsed it, ran every entry through the schema — all green. The actual diff was +1 plugin entry, -1,200 lines of reformatted catalog. Every other in-flight PR's merge base was now unrecoverable without rebase-and-reformat.

The fix has two parts. First, `.prettierignore`:

```text
.claude-plugin/marketplace.extended.json
```

Second, an active line-budget guard at `scripts/check-catalog-format.py`:

```python
def expected_line_delta(base_catalog, head_catalog):
    with open(base_catalog) as f:
        base = json.load(f)
    with open(head_catalog) as f:
        head = json.load(f)
    base_by_name = {p["name"]: p for p in base["plugins"]}
    head_by_name = {p["name"]: p for p in head["plugins"]}

    added = set(head_by_name) - set(base_by_name)
    removed = set(base_by_name) - set(head_by_name)
    modified = {n for n in head_by_name & base_by_name
                if head_by_name[n] != base_by_name[n]}

    # Average plugin block is ~30 lines.
    return (len(added) + len(removed) + len(modified)) * 30

actual_delta = abs(file_line_count(head) - file_line_count(base))
expected = expected_line_delta(base, head)
budget = expected + 300  # slack for inline edits

if actual_delta > budget:
    sys.exit(f"FAIL: catalog diff {actual_delta} lines, budget {budget}")
```

The guard parses both catalogs structurally, computes the expected line delta from the actual content changes, and rejects PRs where the file delta exceeds that by more than 300 lines. "The file is still valid" becomes "the diff is the size we expected from the work that was claimed."

## 4. The SSH deploy that succeeded by doing nothing

Repo: `hustle`, PR #40. Documented in the `intentsolutions-vps-runbook` AAR for Phase 2.5 of the VPS migration.

The new Hustle VPS deploy workflow merged green. The first auto-deploy reported success. The container on the VPS was untouched.

The canonical reusable VPS deploy workflow is one SSH call:

```yaml
- name: Deploy
  run: ssh ${{ env.DEPLOY_USER }}@${{ env.DEPLOY_HOST }}
```

There is no command argument. The whole architecture relies on a `command="..."` force-command directive in `authorized_keys` to bind the deploy key to a specific script. Connect with the key, the forced command runs, deploy happens, connection closes.

The `hustle-deploy` user's `authorized_keys` had no force-command. Plain `ssh user@host` with no command and no force-command opens an interactive session. The runner has no TTY. The session sits idle for a moment, the server times out the silent connection, exit 0. From the runner's perspective: SSH connected, SSH closed cleanly, deploy step SUCCESS. From the VPS's perspective: a key authenticated, nothing happened, the session ended.

The fix is a deploy script and a force-command lock:

```bash
# /usr/local/sbin/deploy-hustle
#!/bin/bash
set -euo pipefail
cd /srv/hustle
git fetch origin
git reset --hard origin/main
docker compose pull
docker compose up -d --remove-orphans
docker compose ps
```

```text
# /home/hustle-deploy/.ssh/authorized_keys
command="/usr/local/sbin/deploy-hustle",no-port-forwarding,no-X11-forwarding,no-pty ssh-ed25519 AAAA... deploy@github
```

Now there is no path where the SSH channel can do nothing. The forced command runs or the key fails to authenticate. The second deploy ran the script end-to-end, recreated the container, and produced visible log output the runner could grep.

The generalization matters more than the fix. Every Docker-variant deploy in the fleet that depends on a force-command and doesn't have one is silently broken in the same way. `lilly-75-holy` and `braves-booth` are flagged for audit; `partner-portals` and `claude-code-plugins-plus-skills` are safe — both have the force-command directive in place. The fleet sweep is tracked as a follow-up bead off the P7 Stage C epic, not folded into this post.

## 5. The regex that skipped matches because `/g` left state behind

Repo: `intentional-cognition-os`, PR #67 (a Gemini review followup on E10-B03).

Two module-level constants:

```typescript
const SOURCE_RE = /\[\^src:([^\]]+)\]/g;
const WIKILINK_RE = /\[\[([^\]]+)\]\]/g;
```

Used in two back-to-back `RegExp.exec` loops to iterate citation markers in a body of text:

```typescript
export function extractCitations(body: string): Citation[] {
  const out: Citation[] = [];
  let m;
  while ((m = SOURCE_RE.exec(body)) !== null) {
    out.push({ kind: "source", id: m[1] });
  }
  while ((m = WIKILINK_RE.exec(body)) !== null) {
    out.push({ kind: "wikilink", id: m[1] });
  }
  return out;
}
```

`RegExp` instances with the `/g` flag carry a mutable `lastIndex` between calls. The `exec` loop is supposed to walk it to the end and let the final non-match reset it to 0 — but any code path that exits the loop early, throws mid-iteration, or runs concurrently on the same regex object leaves `lastIndex` mid-string. The next call to `extractCitations` starts searching from wherever the last one stopped.

The citation handler kept reporting "verified" because the missed citations were not checked at all — not flagged as missing, not flagged as wrong. They were invisible. Whichever entries fell before the carried-over `lastIndex` were skipped silently, every time.

The fix:

```typescript
export function extractCitations(body: string): Citation[] {
  // Required: SOURCE_RE and WIKILINK_RE are module-level /g regexes.
  // Reset lastIndex on entry so prior loop state cannot cause this call
  // to start mid-string and silently skip matches.
  SOURCE_RE.lastIndex = 0;
  WIKILINK_RE.lastIndex = 0;

  const out: Citation[] = [];
  let m;
  while ((m = SOURCE_RE.exec(body)) !== null) {
    out.push({ kind: "source", id: m[1] });
  }
  while ((m = WIKILINK_RE.exec(body)) !== null) {
    out.push({ kind: "wikilink", id: m[1] });
  }
  return out;
}
```

The comment is load-bearing. Without it, the next refactor pulls the resets out as "redundant" and the silent skip comes back. Six regression tests pin the invariant: prebuilt-index honored, batch aggregation correct, 100 sequential calls return identical output, two interleaved bodies (one long, one short) stay independent of each other.

## The shape of a silent failure

All five share the same anatomy. There exists a legitimate no-op outcome — no plugin paths matched, no files to include, no formatting changes needed, no command to run, no remaining matches in the string. The error path produces an observable state identical to the legitimate no-op. The downstream consumer cannot tell which one it got.

The fixes are not better error handling. The fixes are active assertions about the work that was claimed:

- **prescreen:** if files matched the trigger, the extraction must have produced rows
- **gitignore + allow-list:** plugin configs must reach the tree, not just the working directory — and source allow-lists must fail on missing imports, not silently ship a partial build
- **prettier:** the diff size must match the structural work
- **SSH deploy:** bind the command to the key — make it impossible for the channel to do nothing
- **regex:** reset state to a known precondition before every call, and pin that contract with a test

The common verb in every fix is *assert*, not *handle*. The bug was not that errors weren't caught. The bug was that there was no point in the pipeline where the system stated, in code, what counted as the work actually being done.

The hardest silent failures to catch are the ones where the tool's success state and its silent-failure state are observationally identical. That is the category. Once auditing for it begins, more keep surfacing — most CI pipelines have at least one step that exits 0 whether or not it did anything, and most of them are downstream of a step that *can* legitimately produce empty output.

Silent failures don't get worse over time. They get more confident. Each green check trains the audit instinct to skip them, and the audit instinct is the only thing standing between the build status and the truth.

## Related Posts

- [Deterministic-first, LLM-advisory CI](/posts/deterministic-first-llm-advisory-ci/) — the broader argument for keeping reject/accept decisions in code that can be reasoned about, with model output as advisory signal
- [Three guards against shipping slop](/posts/three-guards-against-shipping-slop/) — earlier examples of the same assert-the-work pattern in plugin merges
- [Two false-positive fixes, same root cause](/posts/two-false-positive-fixes-same-root-cause/) — when two unrelated bugs share an underlying shape
