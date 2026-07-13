# Auto-capture hook (opt-in) — `hooks/`

The **automatic** counterpart of `/brain-save`: on a finished Claude Code session it
distills a few **durable** learnings and proposes them to your team's governed brain
(team mode → the remote inbox → governed + agent-reviewed overnight). It is the last
piece of "the whole team's daily work flows into the ONE brain," not just whoever
remembers to save.

## It is OFF by default and never auto-installed

This is **not** a plugin-declared hook. Installing the `governed-second-brain` plugin
does **not** turn it on. It runs only when *you* deliberately enable it — and the
enable flow makes you read exactly what it does, and does **not** do, and consent
first. (Design decision: `governed-second-brain` `000-docs/014-AT-DECR` +
`015-AT-RNBK`; bead `compile-then-govern-jfv.7`.)

## Files

| File | What it is |
|---|---|
| [`session-end-capture.mjs`](session-end-capture.mjs) | The Stop/SessionEnd hook. Three hard guards (opt-in marker · team mode configured · not a recursive child); any unmet → silent no-op. Never blocks or fails your session — the distiller runs **detached** in the background, errors to a log. |
| [`enable-autocapture.mjs`](enable-autocapture.mjs) | The **consent-gated** enable/disable flow. Prints the full disclosure, requires `I CONSENT`, then registers the hook in *your* `~/.claude/settings.json` (with a backup) + a marker. `--off` pauses, `--off --purge` also deletes local logs, `--status` shows state. |

## Enable / pause

```bash
node hooks/enable-autocapture.mjs            # disclosure → consent → enable
node hooks/enable-autocapture.mjs --status   # is it on? where are the logs?
node hooks/enable-autocapture.mjs --off      # pause (remove the hook + marker)
node hooks/enable-autocapture.mjs --off --purge   # pause AND delete local logs
```

Requires **team mode** (`TEAMKB_API_URL` + your `TEAMKB_API_TOKEN`) to actually run —
it no-ops otherwise.

## What it does NOT do

- It does **not** send your raw transcript anywhere — only the distilled, durable
  learnings the model judges worth keeping.
- It **never** captures secrets/tokens/credentials/PII (the distiller strips them;
  the server's deterministic gate blocks them as a backstop).
- It writes **nothing** durable — every proposal lands **quarantined** and is governed
  by deterministic code + reviewed by an agent (with a hash-chained receipt) before
  anything is remembered.

Full change-management + rollout doc: `governed-second-brain`
`000-docs/015-AT-RNBK-team-autocapture-consent-and-rollout.md`.
