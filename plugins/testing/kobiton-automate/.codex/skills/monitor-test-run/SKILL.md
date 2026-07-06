---
name: monitor-test-run
description: >-
  Watch a running Kobiton test run and narrate it to the user: read the org's
  live-remediation flag up front, poll the run until every execution is
  terminal, surface the live-remediation URL the moment an execution is blocked,
  and give a correct post-mortem so a COMPLETED-with-BLOCKER_ENCOUNTERED
  execution is never reported as passed. Quiet on passes, loud on blockers and
  the final summary; suite runs are grouped by test case. When live remediation
  is enabled, it asks up front whether to auto-open the live-remediation browser
  window when a blocker hits. Use when the user asks to "watch", "monitor",
  "track", or "follow" a test run, or as the natural follow-up right after
  createTestRun returns a testRunId. The watch runs a bundled poller that emits
  only on real state changes (no per-poll chatter); uses getOrgSettings up front
  and terminateTestRun on request, plus the shared chromeless launcher — it does
  not drive or resolve the blocker itself.
allowed-tools: >-
  Read,
  Monitor, TaskStop,
  Bash(node:*),
  Bash(bash:*), Bash(pwsh:*),
  Bash(open:*), Bash(xdg-open:*)
version: 1.0.0
author: Kobiton Inc.
license: MIT
compatibility: >-
  Uses the Kobiton MCP tools getOrgSettings (up front) and terminateTestRun
  (on request); requires an authenticated Kobiton MCP connection, and
  getOrgSettings requires the automate plugin release that ships it. The watch
  loop runs the bundled scripts/poll-test-run.js (Node 18+; reads
  ~/.kobiton/.credentials, same file /automate:setup writes) which polls run
  state over REST and emits only on change. The optional live-remediation
  window (Step 4a) reuses run-automation-suite's chromeless-launcher scripts
  (Chrome; resize on macOS/Windows, launch-only on Linux) — if Chrome is absent
  the skill falls back to printing the URL.
tags: [testing, test-run, monitoring, live-remediation, blocker, kobiton]
---

## Overview

Given a `testRunId`, watch the run and narrate it. The skill:

1. Reads `live_remediation_enabled` **once** via `getOrgSettings`, so it can explain deterministically
   what happens when an execution is blocked.
2. Runs the bundled `scripts/poll-test-run.js` in the background — it watches the run and emits a line
   **only when an execution's state changes** (the model never hand-polls).
3. Reacts to those emitted lines: surfaces a blocker (with the live-remediation URL) when one appears,
   stays silent in between.
4. On the poller's `DONE`, does a post-mortem so a blocker is never mistaken for a pass.

The skill is conversational: its "output" is the messages it posts to the user (events + final
summary), not a value returned to a caller. It changes nothing server-side except, optionally,
`terminateTestRun` if the user asks to stop the underlying run.

> **Tool naming.** This doc refers to Kobiton MCP tools by their bare names (`getOrgSettings`,
> `terminateTestRun`). The registered name depends on how the host loaded the MCP server (Claude Code as
> a plugin exposes `mcp__plugin_automate_kobiton__getOrgSettings`; a repo-local `.mcp.json` exposes
> `mcp__kobiton__getOrgSettings`; other hosts differ). Use the bare name and let the host resolve the
> prefix. (Run state is read by the bundled poller over REST, not via the MCP `getTestRun` tool — a
> background process can't call MCP tools.)

## Prerequisites

- **An authenticated Kobiton MCP connection.** All three tools resolve the caller's org/user from the
  OAuth context.
- **A `testRunId`** — usually the one `createTestRun` just returned, or one the user names.
- **`getOrgSettings` available.** If the host can't find it, fall back to the flag-OFF branch (see
  Step 1) rather than failing the watch.

## Inputs

| Input | Required | Notes |
|-------|----------|-------|
| `testRunId` | yes | The run to watch. Numeric/string id as returned by `createTestRun` / shown in the portal. Passed to the poller as `--run-id`. |
| poll cadence | no | The poller defaults to a 3 s base interval backing off to a 30 s cap. Override via its `--interval` / `--max-interval` flags (Step 2) only if needed. |

## Status vocabulary (read before Step 3)

`getTestRun` returns `revisit_executions[]`, each with:
`{ id, test_case_id, status, failure_type, execution_session_id, assigned_device_id, execution_error }`.
`assigned_device_id` is the device the execution runs on — use it directly to build the live-remediation
URL (Step 4); no separate session lookup is needed.

**Execution `status` values:** `NEW`, `SCHEDULED`, `RUNNING`, `UPLOADING_IMAGE`, `COMPLETED`,
`TERMINATING`, `NETWORK_PAYLOAD_SCANNING`. **`COMPLETED` is the terminal status**; what kind of terminal
it is comes from `failure_type`.

**`failure_type` values** (the ones this skill keys on): `NONE` (clean), `BLOCKER_ENCOUNTERED`,
`TERMINATED_BY_USER`, `TERMINATED_BY_SYSTEM`, and several genuine failures (`NETWORK_ISSUE`,
`INIT_SESSION_FAILED`, `APP_CRASHED`, `TARGET_ELEMENT_NOT_FOUND`, `OTP_CODE_ENCOUNTERED`, …).

**The blocked moment depends on the flag — this is the key behavior:**

- **Live remediation ON:** when an execution hits a blocker it **pauses** in a blocked-waiting state
  (live status `BLOCKED_WAITING`, then `BLOCKED_RESUMING` once remediation is accepted) and waits for the
  user to resolve it interactively. It does **not** end yet.
- **Live remediation OFF:** there is **no waiting state**. The execution ends **immediately** —
  `status = COMPLETED`, `failure_type = BLOCKER_ENCOUNTERED` — and the user's later portal resolution
  applies on the **next** rerun.

So with the flag OFF you will typically never observe a blocked-waiting status: the first you see of the
blocker is the terminal `COMPLETED + BLOCKER_ENCOUNTERED`. With the flag ON you see the pause first, then
either a resume or (if the wait expires / is not resolved) a terminal `COMPLETED + BLOCKER_ENCOUNTERED`.

## Steps

### 1. Set up once: flag, portal base, and (if flag ON) the open-on-blocker preference

Do all of this **before** the watch loop, so when a blocker hits later there is nothing left to decide.

**1a. Read the live-remediation flag.** Call `getOrgSettings` a single time and cache
`settings.live_remediation_enabled` as `flagOn` for the rest of the run — do not re-read it on every
poll. Fallback (safer default): if `getOrgSettings` errors or has no `live_remediation_enabled`, treat
`flagOn = false` and tell the user once that you couldn't read the flag and are assuming OFF.

**1b. Derive the portal base URL** from the MCP server the run lives on — **do not hardcode
`https://portal.kobiton.com`**. Read the MCP server URL from `.mcp.json` and map the `api` host to its
`portal` equivalent (drop any trailing `/mcp`), same rule as `run-automation-suite`:

| MCP server | Portal base (`<portal>`) |
|------------|--------------------------|
| `https://api.kobiton.com/mcp` | `https://portal.kobiton.com` |
| `https://api-{env}.kobiton.com/mcp` | `https://portal-{env}.kobiton.com` (same `{env}` suffix) |

So a run watched through `api-test.kobiton.com` → `https://portal-test.kobiton.com`,
`api-test-green` → `portal-test-green`, etc. Cache this as `<portal>`. If the mapping can't be resolved,
fall back to `https://portal.kobiton.com`. **Use the MCP server that serves `getTestRun` for this run**
— i.e. the env the run and its devices live on — not the env any cross-org flag read happened to use.

**1c. State the flag state, and — if `flagOn = true` — settle the open-on-blocker preference up front.**

- `flagOn = false` → "Live remediation is not enabled for your org — a blocked execution ends
  immediately with `BLOCKER_ENCOUNTERED`, and a resolution you submit in the portal applies on the next
  rerun." (Nothing to pre-arrange; there is no live window to open. `autoOpen` is irrelevant.)
- `flagOn = true`:
  - **If `autoOpen` was already decided by the caller** (e.g. the `create-test-run` skill delegated here
    after the user chose "monitor + auto-open" → `autoOpen = yes`, or "monitor only" → `autoOpen = no`),
    **do not ask again** — just state it: "Live remediation is enabled; I'll {auto-open the
    live-remediation window on a blocker / surface the URL on a blocker}." Skip straight to Step 2.
  - **Otherwise** (invoked directly, no pre-set preference) → "Live remediation is enabled — if an
    execution hits a blocker it pauses and waits for interactive remediation." Then ask **now, once,
    before monitoring**: *"When a blocker hits, do you want me to automatically open the live-remediation
    window for the blocked device?"* Cache the answer as `autoOpen` (yes/no). Asked a single time up front
    — **not** per blocker mid-run.

### 2. Stream the bundled poller — do NOT hand-poll

**Do not write your own sleep/poll loop and do not narrate individual polls.** That is exactly what made
a prior run noisy — calling `getTestRun` over and over and posting "still NEW / still blocked, no change".
The bundled poller emits a line **only when an execution's state actually changes** and exits when the
run is done:

```
node $SKILL_DIR/scripts/poll-test-run.js --run-id <testRunId>
```

(`$SKILL_DIR` is this skill's directory. Optional: `--interval <sec>` base cadence (default 3),
`--max-interval <sec>` backoff cap (default 30), `--max-errors <n>` consecutive-error give-up (default 5),
`--waiting-heartbeat <sec>` blocked-heartbeat cadence (default 60, `0` disables).) The script reads run
state via REST using `~/.kobiton/.credentials` (a background process can't call the MCP `getTestRun` tool
— that's why this is a script). It diffs per execution, backs off during quiet stretches, and exits `0`
on `DONE`.

**Run it so each emitted line streams back to you as it happens — this is the whole point.** A plain
"background" launch is NOT enough: a backgrounded process's stdout does **not** re-engage you, so you'd
sit idle and miss the blocker window (this was a real failure). Use the host's *stream-a-command's-output*
mechanism so every line re-invokes you:

| Host | How to stream the poller |
|------|--------------------------|
| **Claude Code** | The **`Monitor` tool** — `command:` the `node …poll-test-run.js …` line above, `persistent: true` (a run can outlast the default timeout; stop it with `TaskStop` when done/cancelled). Each stdout line arrives as a notification that re-invokes you. **Do not** use `Bash` with `run_in_background` for this — it won't stream the lines back. |
| **Codex CLI** | Use its long-running/streamed-shell affordance (a foreground streamed exec) so each stdout line surfaces as it's printed; don't detach-and-forget. |
| **Gemini CLI / others** | Use the host's equivalent streamed/long-running shell or watch/loop tool. If the host has **no** way to stream a background command's stdout back, fall back to a **foreground loop**: run the poller foreground reading one batch, or re-invoke the skill's poll on an interval via the host's loop/cron tool — never a silent detached process. |

Whichever mechanism: **you react only to the lines it prints**. Stay silent between lines; there is no
value in reporting "no change". The lines:

| Line | Meaning → what you do |
|------|-----------------------|
| `READY portal=<base>` | The env-mapped portal base (Step 1b — the script derived it from the credentials' API host). Cache it as `<portal>` for the launch URL; don't derive it yourself. |
| `EVENT dispatched exec=… device=… session=… tc=… failure=…` | An execution started running. Quiet — optional one-liner at most; don't narrate every dispatch. |
| `EVENT blocked exec=… device=… …` | An execution hit a blocker and is paused (flag ON). **Loud** → Step 4. |
| `EVENT resumed exec=… …` | A previously blocked execution resumed. Post a concise "execution … resumed". |
| `EVENT terminal_passed \| terminal_blocker_encountered \| terminal_failed \| terminal_terminated exec=… …` | That execution reached a terminal state. Collect for the Step 5 summary; surface a blocker-encountered terminal as a blocker, **never** as a pass. |
| `DONE …` | All executions terminal → go to Step 5 (final summary). |
| `WAITING blocked=<n> …` | Throttled heartbeat (default every 60 s) emitted **while ≥1 execution sits blocked-waiting** and nothing else is changing. This is your cue to **re-nudge the user** that those executions are paused on a timeout — see Step 4b. Do not treat it as "no change, stay quiet". |
| `ERROR <code> <message>` | `NOT_FOUND`/`FORBIDDEN`/`UNRECOVERABLE` are fatal (script exits) — report and stop. A transient `poll` error is informational (the script keeps retrying) — stay quiet unless it escalates to `UNRECOVERABLE`. |

**Short-circuit:** if the run is already fully terminal, the script emits the terminal `EVENT`s then
`DONE` on the first poll — same path, no special-casing needed.

**The event kinds map to outcomes as follows** (the script applies this; it's here so you narrate
correctly): `terminal_passed` = `COMPLETED` + `failure_type NONE`; `terminal_blocker_encountered` =
`COMPLETED` + `BLOCKER_ENCOUNTERED` (a blocker, **never** a pass); `terminal_terminated` = `COMPLETED` +
`TERMINATED_BY_USER`/`TERMINATED_BY_SYSTEM`; `terminal_failed` = `COMPLETED` + any other `failure_type`.

### 4. Surface blockers (loud); stay quiet on passes

**On an `EVENT blocked` line** (flag ON, paused) **or an `EVENT terminal_blocker_encountered` line**
(flag OFF, already ended) from the poller — post a message containing:

- Which execution (`exec=`) and, for a suite, which test case (`tc=`) is blocked.
- The device — the `device=` field on the event line (the poller reads it from `assigned_device_id`).
- The live-remediation URL — built from `<portal>` (the base from the poller's `READY` line, env-mapped,
  **not** hardcoded to production) and `device=`. Note: **no `&view=device-only`** — the full default
  device-launch view is wanted here so the Kobi AI chat panel and controls are visible alongside the
  device:

  ```
  <portal>/devices/launch?id=<device>
  ```

- A deterministic explainer keyed on the cached `flagOn`:
  - `flagOn = true` → **this is an action request, not a status update — the execution is now waiting on
    the user, on a clock.** Say so plainly and urgently, e.g.: "⏳ **Action needed now** — this execution
    is paused on a blocker and waiting for **you**. It will **auto-fail with `BLOCKER_ENCOUNTERED` if the
    remediation window times out**, so resolve it promptly. {If `autoOpen = yes`: "I've opened the
    live-remediation window —" else: "Open the URL to"} chat with Kobi AI / drive the device to clear the
    blocker; the execution resumes automatically once it's cleared." Do **not** frame this as "I'll just
    wait and ping you when something changes" — by the time the next change arrives it may already be the
    timeout.
  - `flagOn = false` → "Live remediation isn't enabled for your org, so this execution ended with
    `BLOCKER_ENCOUNTERED`. Submit your resolution in the portal — it applies on the **next** rerun."

**If the event line shows `device=-`** (the device id is unexpectedly absent — it is part of the
`getTestRun` contract, so this points to a backend/state problem): surface the blocker text without a URL
and note `INVALID_EXECUTION_STATE` (missing `assigned_device_id`). Don't fabricate a device id.

#### 4a. Auto-open the live-remediation window (flag ON, per the up-front preference)

The decision was already made in Step 1c — **do not ask again per blocker mid-run.** On each
`EVENT blocked` line:

- If `autoOpen = no` → just post the URL (the user opens it themselves). Done.
- If `autoOpen = yes` → open the live-remediation window for the blocked device now, automatically, then
  carry on monitoring. (Still print the URL too, as a fallback.)

To open it, reuse `run-automation-suite`'s chromeless-launcher chain — the same chain
`drive-automation-session` uses — **do not re-implement it**. Two differences from that skill's
device-only live view:

1. **Full view, not device-only.** Use the URL **without** `&view=device-only` so the Kobi AI chat panel
   and the surrounding launch-view controls render, not just the phone screen.
2. **Bigger-than-phone window.** Size the window wide enough to fit the device **plus** the chat
   interface — default **1400×900** (vs the launcher's phone-shaped 540×920 default). The device sits on
   one side and the chat/controls on the other.

```
LIVE_REMEDIATION_URL="<portal>/devices/launch?id=<assigned_device_id>"
```

Invoke per host OS, **in the background** (Claude Code: `Bash` tool with `run_in_background: true`; other
hosts: append `&` and `disown`) so the launcher's resize-polling doesn't block the watch loop. `$SKILL_DIR`
is this skill's directory.

| OS | Command |
|----|---------|
| macOS | `bash $SKILL_DIR/../run-automation-suite/scripts/chromeless-launcher.sh --url "$LIVE_REMEDIATION_URL" --width 1400 --height 900` |
| Windows | `pwsh $SKILL_DIR/../run-automation-suite/scripts/chromeless-launcher-windows.ps1 -Url "$LIVE_REMEDIATION_URL" -Width 1400 -Height 900` |
| Linux | `bash $SKILL_DIR/../run-automation-suite/scripts/chromeless-launcher.sh --url "$LIVE_REMEDIATION_URL" --width 1400 --height 900` (launch-only — no auto-resize) |

Launcher exit codes (surface in the background-task completion event): `0` = Chrome launched (resize may
not have succeeded — informational); `2` = Chrome not found → fall back to telling the user to open the
URL manually (or their default browser); `64` = usage error → surface it. The URL is always printed too,
so a launcher failure never blocks the user.

This is **only** for the flag-ON branch — with the flag OFF the execution has already ended, so there's
no live window to open; just give the explainer and the portal URL.

**On a `resumed` event**, post a concise "execution [id] resumed" line.

Stay quiet on in-flight **passing** progress — don't narrate every poll. But "quiet" applies to running
executions, **not** to blocked-waiting ones: a `flagOn = true` blocker is the user's to clear against a
timeout, so silence there is wrong (it reads as "nothing for me to do" while the clock runs out).

#### 4b. While any execution is blocked-waiting, keep the pressure on (flag ON)

Track which executions are currently in the `blocked` state (entered on an `EVENT blocked`, cleared on
that execution's `resumed` or terminal event). The poller drives the nudging for you: while that set is
non-empty and nothing else changes, it emits a throttled **`WAITING blocked=<n>`** line (default every
60 s).

- **On each `WAITING` line, post a short standing reminder** naming what's still pending and that it will
  auto-fail on timeout — e.g.: "⏳ Still waiting on you: 2 executions paused on blockers (Pixel 8, Pixel
  4). They auto-fail with `BLOCKER_ENCOUNTERED` if not resolved soon — resolve them in the open windows."
  Don't treat `WAITING` as a no-op.
- When a previously-`blocked` execution goes terminal as `terminal_blocker_encountered`, say it **timed
  out / wasn't resolved in time** (not merely "ended with a blocker") so the cause is unambiguous.

The point: a blocked-waiting run is an **open ask of the user**, not a background watch. Keep it visible
until they act or it resolves.

### 5. Post-mortem + final summary

On the poller's `DONE` line, post a final summary from the terminal `EVENT` lines you collected. For each
execution, report by its terminal kind:

- `terminal_passed` → "execution [exec] passed".
- `terminal_blocker_encountered` → **Never** report this as passed.
  - If `flagOn = true` **and** this execution had been `blocked` (paused) → it **timed out**: "execution
    [exec] hit a blocker, paused for live remediation, and **timed out unresolved** → `BLOCKER_ENCOUNTERED`.
    The resolution you submit in the portal applies on the next rerun." (Flag this if the user could still
    have acted — it's the avoidable case.)
  - If `flagOn = false` → "execution [exec] ended with `BLOCKER_ENCOUNTERED` (live remediation not enabled
    for your org); the resolution you submit in the portal applies on the next rerun."
- `terminal_failed` → "execution [exec] failed: [failure=…]".
- `terminal_terminated` → "execution [exec] terminated ([failure=…])".

**Format:** group by `tc=` (test case) when the run is a suite; flat list per execution otherwise.

### 6. Lifecycle

- **Already terminal at invocation** → the poller emits the terminal `EVENT`s then `DONE` on its first
  poll; go straight to the final summary.
- **Natural exit** → the skill ends when the poller prints `DONE` (every execution `COMPLETED`); the
  monitor stream ends on the poller's exit. There is no arbitrary wall-clock cap; the test run's own
  lifecycle is the bound. (On Claude Code you may still `TaskStop` the monitor task after `DONE` to free
  it, though it has already exited.)
- **User cancels the watch** → stop the poller stream (Claude Code: `TaskStop` the monitor task; other
  hosts: terminate the streamed process) and end cleanly. The underlying run keeps going. If the user
  wants to actually stop the run (not just the watch), call `terminateTestRun(testRunId)` and confirm.

## Errors

| Condition | Handling |
|-----------|----------|
| Poller prints `ERROR NOT_FOUND` / `ERROR FORBIDDEN` | Run not found / not owned — the poller exits; report and stop. |
| Poller prints a transient `ERROR poll …` | Informational — the poller is backing off and retrying. Stay quiet unless it escalates to `ERROR UNRECOVERABLE` (it exits after `--max-errors`), then report. |
| `getOrgSettings` fails or flag missing | Fall back to the flag-OFF branch (`flagOn = false`); tell the user once. Do not abort the watch. |
| `ERROR no-credentials` from the poller | `~/.kobiton/.credentials` is missing/incomplete — tell the user to run `/automate:setup`, then restart the watch. |
| Event line shows `device=-` on a blocker | Device id unexpectedly absent (contract-guaranteed). Surface blocker text without URL; note `INVALID_EXECUTION_STATE`. |
| Live-remediation launcher fails (exit 2/64) | Inform the user and fall back to the printed URL (or their default browser). Never blocks the watch. |

## Notes

- This skill is additive conversational glue. It reads the org flag (`getOrgSettings`), runs the bundled
  `scripts/poll-test-run.js` to **watch** run state (REST, emit-on-change — it does not mutate the run),
  optionally **opens the live-remediation view in a browser** (the shared chromeless-launcher, Step 4a)
  when the user opted in, and optionally **stops the run** (`terminateTestRun`). It does not itself drive
  the device or resolve the blocker — the user does that in the opened view — and it does not implement
  the live-remediation experience.
- **The poller, not the model, owns the watch loop.** Never hand-poll `getTestRun` in a sleep loop or
  narrate no-change polls — the poller exists precisely so the watch is quiet between real state changes.
- It composes with the test-run tools: `createTestRun` (start) → `monitorTestRun` (watch) →
  `terminateTestRun` (stop, if asked).
- The status values, `failure_type` values, and the blocker rule above are the Kobiton platform's
  contract for a revisit execution; if the platform changes them, update this skill rather than diverging.
