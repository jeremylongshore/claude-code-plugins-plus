---
name: drive-automation-session
description: >-
  Drive an already-reserved Kobiton device from a natural-language intent.
  Opens an automation Appium session directly against the Kobiton WebDriver
  hub, runs an observe-decide-act loop with one action per iteration, pauses
  to ask the user when stuck (same-action repetition, screen unchanged, or
  model self-declared blocker), and returns the session id. Use when the
  user says "drive the device to X", describes a flow they want exercised
  on a reserved device, or asks to "automate this intent on Kobiton".
  Complements run-interactive-cli-session (which uses the CLI session type) by
  using the automation session type so the resulting session is consumable
  by saveTestCase and the existing test-run authoring flow.
allowed-tools: >-
  Read, Edit,
  Bash(node:*),
  Bash(bash:*), Bash(pwsh:*),
  Bash(mkdir:*), Bash(mv:*), Bash(date:*), Bash(echo:*), Bash(printf:*),
  Bash(jq:*),
  Bash(open:*), Bash(xdg-open:*)
version: 1.0.0
author: Kobiton Inc.
license: MIT
compatibility: >-
  Cross-platform — talks WebDriver HTTP directly via Node's built-in
  node:https; no platform-specific binary dependency. Requires Node.js
  >= 18 and an authenticated Kobiton MCP connection (or, as a fallback,
  ~/.kobiton/.credentials written by /automate:setup).
tags: [mobile, testing, appium, natural-language, intent, automation, kobiton]
---

# Drive from Intent

## Overview

Drive a Kobiton device from a natural-language intent. The caller provides:

1. An intent string (e.g. "open Settings, enable Bluetooth, then go back to home").
2. A UDID for a device the caller has already reserved.
3. An app reference (`kobiton-store:vXXXXX`) or a browser name for web sessions.

The skill opens an **automation-type** Appium session (with `appium:newCommandTimeout: 1800` so the session survives pauses while the model asks for guidance), runs an observe-decide-act loop, and returns the session id. The returned session is consumable by the Kobiton MCP tools `getSession`, `getSessionArtifacts`, and `saveTestCase` exactly like any other automation session.

> **Tool naming.** This doc refers to Kobiton MCP tools by their bare names (`getSession`, `reserveDevice`, `terminateSession`, …). The exact registered name depends on how the host loaded the MCP server (e.g. Claude Code as a plugin exposes `mcp__plugin_automate_kobiton__getSession`; a repo-local `.mcp.json` or `claude mcp add` exposes `mcp__kobiton__getSession`; other hosts differ). Models fuzzy-match on the bare name, so use it and let the host resolve the prefix.

This skill complements — and does NOT replace — `run-interactive-cli-session`. They serve different session types:

| Skill | Session type | Best for |
|-------|--------------|----------|
| `run-interactive-cli-session` | CLI session (`~/.kobiton/bin/kobiton`) | Human-driven exploration, ad-hoc inspection |
| `drive-automation-session` | Automation session (direct Appium HTTP) | AI-driven flows, saveable as a test case |

## Prerequisites

- **Credentials available.** The skill reads credentials from the Kobiton MCP `getCredential` tool by default — no `/automate:setup` prerequisite. If MCP is unavailable, the skill falls back to `~/.kobiton/.credentials` (written by `/automate:setup`). If neither source produces credentials, the skill stops with a helpful message.
- **A device.** Either the user provides one (UDID, deviceName, platformVersion) or the skill helps pick + reserve one (see Step 0 below).
- **An app** (for app testing) — a Kobiton-store reference like `kobiton-store:vXXXXX`, an `.apk` / `.ipa` to upload, or a browser name (for web testing). The skill helps locate or upload it in Step 0.

## Step 0: Device + app selection (ask before picking)

Before reserving anything, the skill clarifies what the user wants. **Do NOT auto-pick a device unless the user's intent unambiguously implies a platform AND the user did not constrain the choice.**

### Device

If the user didn't specify a device in their intent:

1. Ask: *"Which device or platform? (e.g., 'a Pixel running Android 14', 'an iPhone 15 Pro', or pick any available Android)."* Wait for the response.
2. If they name a class (e.g., "any Pixel", "any iOS phone"), call `listDevices` with the relevant platform filter and present the top 3-5 options with name + OS version + availability.
3. If they name a specific device, verify availability via `getDeviceStatus` before reserving.
4. Reserve via `reserveDevice`. Capture the UDID, deviceName, platformVersion, automationName for Step 2's caps render.

If the user's intent strongly implies a platform (e.g., "test the iOS App Store flow", "open Chrome on Android"), it's OK to auto-pick — but state which device you're picking and why in one line before reserving, so the user can redirect.

### App

For an `app` testing session:

- If the user referenced a build (`@build.apk`, "the latest staging build", `kobiton-store:vXXXXX`), use it. Verify the store reference exists via `listApps` if uncertain.
- If they didn't reference one, ask: *"Which app should the session install? (path to a local `.apk`/`.ipa`, an existing `kobiton-store:vXXXXX` reference, or none if the intent is browser-only)."*
- Upload local files via `uploadAppToStore` → `confirmAppUpload` → poll `getAppParsingStatus` until the state is terminal (`OK` = ready; stop on a `FAILURE_*` value). `confirmAppUpload` only kicks off async parsing on the backend — it does NOT guarantee the app is ready, so the session can fail to install if you skip the poll.

For a `web` testing session, skip the app step — `--testingType web --browserName chrome|safari` is enough.

### Live view

If the user didn't say how they want to observe the session, ask before creating it:

> *"Open the device live view to watch the agent drive (foreground), or run the session in the background?"*

Two options:

- **Open in foreground** — after the session is created, build the device-only URL `<portal>/devices/launch?id=<deviceId>&view=device-only` (same shape as `run-automation-suite` Step 5; the `<deviceId>` is the one captured during Step 0 reservation) and launch it via the chromeless launcher chain (see Step 3b for the chromeless-vs-default-browser branching). The URL is also surfaced as text so the user can click manually if the launcher can't open Chrome and no default-browser fallback applies.
- **Run in background** — proceed straight to the loop. The user can still inspect artifacts (XML/PNG/video) after the cycle ends.

Remember the choice; act on it in Step 3 right after the session is created. Do NOT auto-open without asking — some users prefer silent runs, especially on shared screens.

## Inputs

| Input | Required | Notes |
|-------|----------|-------|
| `intent` | yes | One to a few sentences describing what the user wants done on the device |
| `udid` | yes | The device the caller has reserved |
| `platformName` | yes | `Android` or `iOS` (look up via `getDeviceStatus` if unknown) |
| `platformVersion` | yes | from `getDeviceStatus` |
| `deviceName` | yes | from `getDeviceStatus` |
| `automationName` | recommended | `UiAutomator2` (Android) or `XCUITest` (iOS) |
| `app` OR `browserName` | yes | `kobiton-store:vXXXXX` for app testing, browser name for web testing |
| `testingType` | no | `app` (default) or `web` |
| `MAX_ITERS` | no | env var override; default 100. Hard ceiling on iteration count — pure safety net against runaway cycles, not a stuck-detection mechanism. |

## Steps

### 1. Verify credentials are available

`appium.js` reads `~/.kobiton/.credentials` directly on every invocation. If the file is missing, tell the user to run `/automate:setup` and stop:

```bash
if [ ! -s ~/.kobiton/.credentials ]; then
  echo "Credentials not found. Run /automate:setup first." >&2
  exit 1
fi
```

### 2. Render desired capabilities

Reuse `run-automation-suite`'s renderer. The `--newCommandTimeout 1800` flag is the key piece for this skill.

```bash
SKILL_DIR=$(dirname "$0")   # this skill's directory
RENDER=$(realpath "$SKILL_DIR/../run-automation-suite/scripts/render-capabilities.js")

# Unique temp file — two concurrent sessions (two terminals / conversations)
# must not clobber each other's rendered caps before Step 3 reads them.
CAPS_TMP=$(mktemp "${TMPDIR:-/tmp}/drive-automation-session-caps.XXXXXX.json")

node "$RENDER" \
  --platformName "$PLATFORM_NAME" \
  --udid "$UDID" \
  --deviceName "$DEVICE_NAME" \
  --platformVersion "$PLATFORM_VERSION" \
  --automationName "$AUTOMATION_NAME" \
  --app "$APP" \
  --testingType "${TESTING_TYPE:-app}" \
  --newCommandTimeout 1800 \
  --scriptlessCapture \
  > "$CAPS_TMP"
```

`appium.js` reads `~/.kobiton/.credentials` on each invocation. No flags, no env vars.

### 3. Create the session

```bash
SESSION_ID=$(node "$SKILL_DIR/scripts/appium.js" \
  --method POST --url /session \
  --req-body "@$CAPS_TMP" \
  | jq -r '.value.sessionId // .sessionId')

SESSION_DIR=".kobiton/sessions/$SESSION_ID"
mkdir -p "$SESSION_DIR"
mv "$CAPS_TMP" "$SESSION_DIR/caps.json"
printf '%s session=%s started intent=%q\n' "$(date -u +%FT%TZ)" "$SESSION_ID" "$INTENT" > "$SESSION_DIR/session.log"

trap 'cleanup' EXIT INT TERM
cleanup() {
  [ -z "$SESSION_ID" ] && return 0
  # DELETE /wd/hub/session/<id> ends the WebDriver session cleanly; Kobiton
  # records state=COMPLETE. appium.js already treats 404 as idempotent success
  # (the session was already gone). appium.js always exits 0 by policy, so we
  # check stderr instead of $? to detect a real failure.
  delete_err=$(node "$SKILL_DIR/scripts/appium.js" \
    --method DELETE --url "/session/$SESSION_ID" 2>&1 >/dev/null)
  if [ -z "$delete_err" ]; then
    printf '%s session=%s end-via-trap status=COMPLETE\n' "$(date -u +%FT%TZ)" "$SESSION_ID" >> "$SESSION_DIR/session.log"
  else
    printf '%s session=%s end-via-trap delete-failed (session will time out per appium:newCommandTimeout) err=%s\n' "$(date -u +%FT%TZ)" "$SESSION_ID" "$delete_err" >> "$SESSION_DIR/session.log"
  fi
}
```

### 3b. Act on the live-view choice from Step 0

Build the device-only URL from the device id captured during Step 0 reservation and the portal base URL (e.g., `https://portal.kobiton.com`) — the AI host has the portal value from earlier MCP responses in the conversation context. Same URL shape as `run-automation-suite` Step 5.

```bash
LIVE_VIEW_URL="<portal>/devices/launch?id=<deviceId>&view=device-only"
printf 'Live view: %s\n' "$LIVE_VIEW_URL"
```

(The post-run replay URL is `<portal>/sessions/<kobiton-session-id>/explorer` — a different page, NOT the live view. Surface that one only after the session completes if the user wants to review the recording.)

If the user chose **background** in Step 0, stop here — the URL is logged and the loop proceeds. They can paste it into a browser later if they get curious.

If the user chose **foreground**, reuse `run-automation-suite`'s launcher chain instead of re-implementing it. The pattern (chromeless Chrome for users who haven't expressed a preference or prefer Chrome; default-browser fallback otherwise) is identical to `run-automation-suite` Step 5.

**Launch via the chromeless helper (default — gated on saved browser preference).** Check auto memory for a saved browser preference:

- **No preference saved**, OR **preference is Google Chrome** → invoke the chromeless launcher below.
- **Preference is Safari, Firefox, or Default browser** → skip the launcher; go straight to the default-browser fallback table.

**Pick width and height from the reserved device's form factor** (the device name from Step 0):

| Device class | Detect by name (case-insensitive) | Portrait `W × H` | Landscape `W × H` |
|---|---|---|---|
| Tablet | `iPad`, `Galaxy Tab`, `Pixel Tablet`, `Surface`, `MatePad`, or any model with `Tab` / `Pad` | `780 × 920` | `920 × 780` |
| Fold (unfolded) | `Fold`, `Z Fold`, `Pixel Fold` | `880 × 920` | `920 × 880` |
| Phone (default) | none of the above | `540 × 920` | `920 × 540` |

Swap width and height if `getSession` / rendered caps report `orientation=LANDSCAPE` — default is portrait.

Invoke per host OS. **Run in the background** (Claude Code: `Bash` tool with `run_in_background: true`; other hosts: append `&` and `disown`) so the resize-polling loop doesn't block iteration 1. The launcher's stdout/stderr will surface later when it completes; the URL printed above is the user's fallback if the launcher silently fails.

| OS | Command |
|----|---------|
| macOS | `bash $SKILL_DIR/../run-automation-suite/scripts/chromeless-launcher.sh --url "$LIVE_VIEW_URL" --width <W> --height <H>` |
| Windows | `pwsh $SKILL_DIR/../run-automation-suite/scripts/chromeless-launcher-windows.ps1 -Url "$LIVE_VIEW_URL" -Width <W> -Height <H>` |
| Linux | `bash $SKILL_DIR/../run-automation-suite/scripts/chromeless-launcher.sh --url "$LIVE_VIEW_URL" --width <W> --height <H>` (launch-only on Linux — no auto-resize) |

**Launcher exit codes** (surface in the background-task completion event):

- `0` — Chrome was launched (resize may or may not have succeeded; the warning is informational).
- `2` — Chrome / Chromium is not installed. The user already has `$LIVE_VIEW_URL` from the `printf` above; they can paste it into their default browser, or you can offer the default-browser fallback table below as a follow-up.
- `64` — usage error in the launcher invocation. Surface to the user.

**Default-browser fallback** (when the saved preference is Safari/Firefox/Default, or chromeless exited 2). Ask the user once which browser to use (save to auto memory):

| Choice | Command |
|--------|---------|
| Google Chrome | `open -na "Google Chrome" --args --new-window "$LIVE_VIEW_URL"` |
| Safari | `open -a "Safari" "$LIVE_VIEW_URL"` |
| Firefox | `open -a "Firefox" "$LIVE_VIEW_URL"` |
| Default browser | `open "$LIVE_VIEW_URL"` |

On Linux, fall back to `xdg-open "$LIVE_VIEW_URL"` (browser selection isn't supported).

If neither path is available, the URL is already on stdout from the `printf` above — the user can copy-paste it.

### 4. Per-turn iteration pattern (three branches)

There is no Bash `while`. The skill is **turn-based**: each turn, you (the AI host) increment `ITER` and pick **exactly one** of three branches:

| Branch | Command | When to pick |
|---|---|---|
| **screen** | `node appium.js screen --session-id $SID --session-dir $DIR` | The screen state has likely changed (after a successful act, or at session start, or to verify mid-flow). |
| **act** | `node appium.js <argv> --session-dir $DIR` | You know what to do based on the most recent `iter-K.xml` you observed. |
| **control** | `node appium.js control --done\|--blocked --reason "..." --session-dir $DIR` | Goal reached, or you're genuinely stuck. Ends the cycle. |

Each branch consumes one ITER. The script always exits 0; the host detects failures by checking whether `iter-N.error.json` was written.

```bash
export ITER=$((ITER + 1))

# Pick ONE of the three. Credentials inherit from env (Step 1).

# Branch A: observe — captures BOTH iter-N.xml and iter-N.png by default.
#   Native overlays / OS dialogs only show in the PNG (the webview source
#   XML doesn't see them). --xml-only skips the screenshot to save tokens
#   when you trust the XML is complete; --png-only skips the source when
#   you're verifying layout / image rendering only.
node "$SKILL_DIR/scripts/appium.js" screen \
  --session-id "$SESSION_ID" --session-dir "$SESSION_DIR"
# Stdout: {"hash":"<sha256>","xmlBytes":N,"pngBytes":M}
# Track the hash across turns in your conversation context — repetition is a
# signal, never a forced stop. See references/loop-discipline.md "Stuck patterns".

# Branch B: act — execute an Appium call. Writes iter-N.request.json + either
#   iter-N.response.json (success) or iter-N.error.json (any failure). The
#   error file contains the raw Appium body or {error, message} for usage
#   errors; the host reads it to decide what to do next turn.
node "$SKILL_DIR/scripts/appium.js" <YOUR-ARGV> --session-dir "$SESSION_DIR"
# Examples of <YOUR-ARGV>:
#   --method POST --url /session/$SESSION_ID/element --req-body '{"using":"xpath","value":"//Button"}'
#   actions --session-id $SESSION_ID --type swipe --from-x 540 --from-y 1800 --to-x 540 --to-y 600
#   touch-perform --session-id $SESSION_ID --steps @/tmp/steps.json
#   --method POST --url /session/$SESSION_ID/element/$EL_ID/clear --req-body '{}'

# Branch C: end the cycle.
node "$SKILL_DIR/scripts/appium.js" control \
  --done --reason "Settings reached and Bluetooth toggled" \
  --session-dir "$SESSION_DIR"
# OR --blocked --reason "Two modals stacked; cannot dismiss"

# ---- Per-turn bookkeeping (runs after the chosen branch) ----

# Log failures so session.log has a timeline. appium.js writes iter-N.error.json
# on any failure — Appium HTTP error, network blip, usage error like missing
# flag or malformed JSON. The host reads the file next turn and re-plans.
ITER_PAD=$(printf '%03d' "$ITER")
if [ -f "$SESSION_DIR/iter-$ITER_PAD.error.json" ]; then
  printf 'iter=%d error\n' "$ITER" >> "$SESSION_DIR/session.log"
fi

# Iteration ceiling — safety net only. Not a stuck-detection mechanism.
if [ "$ITER" -ge "${MAX_ITERS:-100}" ]; then
  printf 'iter=%d max-iters-reached limit=%d\n' "$ITER" "${MAX_ITERS:-100}" >> "$SESSION_DIR/session.log"
  exit 0
fi
```

#### Branch decision guide

What to pick next turn depends on what just happened:

- **Successful act** → next turn `screen` (the screen probably changed).
- **`screen` just ran** → next turn `act` (you have a fresh observation).
- **`act` returned `no such element` / `invalid selector` / `bad-input`** → next turn `act` again with a corrected call. The screen didn't change (the action didn't fire), so the most recent `iter-K.xml` is still valid; re-read it from disk if you need to, but don't burn an ITER on a fresh `screen`.
- **`act` returned `stale element reference`** → next turn `screen` (the element id is from a prior state; you need a fresh observation to get current element ids).
- **`act` returned HTTP 5xx / network timeout** → next turn `act` again with the same call (retry). If it fails twice, `control --blocked`.
- **Goal reached** → `control --done`.
- **Genuinely stuck** (per the patterns in `loop-discipline.md` "Stuck patterns") → `control --blocked`.

The host is responsible for tracking which `iter-K.xml` represents the current screen state. After a successful act, the previous `iter-K.xml` is stale until the next `screen`. After a failed act, the previous `iter-K.xml` is still current.

#### Building act calls from the XML

When the chosen branch is `act`, the argv body is constructed from the most recent `iter-K.xml` — selectors come from attributes you can see in the XML, not from guesses. See `references/endpoint-reference.md` "Building Appium calls from the observed XML" for the find-element → element-id workflow, selector-strategy preference order (accessibility id > id > relative xpath > css selector > class name), and the coordinates-from-bounds fallback for gestures with no element target.

The full loop discipline (artifact paths, error feedback, termination conditions) lives in `references/loop-discipline.md`. The endpoint catalog (allowlisted vs not, helpers vs generic) lives in `references/endpoint-reference.md`.

### 5. Cleanup

The Bash `trap` (set up in Step 3) issues `DELETE /wd/hub/session/$SESSION_ID` on exit (loop end, error, user stop). That's the **clean** way to end the session — Kobiton records the session state as `COMPLETE`, which is what `saveTestCase` and analytics expect.

Do **NOT** call the `terminateSession` MCP tool here. It ends the session via Kobiton's platform-side kill path, which marks the session state as `TERMINATED` — distinct from `COMPLETE` and treated as an abnormal exit by the recording pipeline. Reserve `terminateSession` for the genuinely-stuck case where the WebDriver `DELETE` is unreachable (network down, Appium hub unresponsive) AND the user explicitly asks to force-kill the session.

If the `DELETE` somehow fails silently, the session will time out on the Kobiton side per `appium:newCommandTimeout` (30 min, set in Step 2). Better to wait for that timeout than to mark the session `TERMINATED`.

### 6. Return

Emit the session id back to the caller. The session is now consumable by:

- `getSession({sessionId})` — session metadata, device info, results.
- `getSessionArtifacts({sessionId})` — video, logs, screenshots, reports.
- `saveTestCase({sessionId})` — persist as a re-runnable test case (sibling feature, out of scope here).

## Endpoint reference

See `references/endpoint-reference.md` for the full Appium endpoint catalog — allowlisted (capturable by `saveTestCase`) vs not, helpers (`actions`, `touch-perform`) vs generic mode. The AI host picks endpoints from that table when emitting `iter-N.call.json`.

## Stuck patterns — host decides when to pause

The script does not enforce blocker thresholds. The AI host tracks the `hash` from `screen` across turns in its conversation context and decides when to emit `control --blocked`. See `references/loop-discipline.md` "Stuck patterns" for concrete examples — same-call repetition, screen oscillation (A→B→A→B), credentials prompt, CAPTCHA, lazy load (use a no-op observe to wait), network spinner.

The only hard programmatic stop is `MAX_ITERS=100` (override per session), which is a safety net against runaway cycles — not a stuck-detection mechanism.

## Errors

| Symptom | Likely cause | Fix |
|---------|--------------|-----|
| `No credentials available...` | Kobiton MCP not connected AND no `~/.kobiton/.credentials` | Either authenticate the Kobiton MCP server, or run `/automate:setup` |
| `iter-N.error.json` has `status: 401` on session create | Credentials stale | Re-authenticate the MCP server (or re-run `/automate:setup` for the file fallback); check the portal URL |
| `iter-N.error.json` has a platform-cap message on session create | `newCommandTimeout: 1800` rejected by Kobiton | Lower the timeout in `references/capabilities.md` |
| `iter-N.error.json` body has `value.error: "no such element"` | Selector matched nothing | Re-plan next turn with a different strategy / selector |
| `iter-N.error.json` body has `value.error: "invalid session id"` | Kobiton platform-side session ended | Emit `control --blocked` (or just let MAX_ITERS catch it); trap cleans up |

## Notes

- The `kobiton:aiToolName` capability is auto-detected by `render-capabilities.js` (Claude / Codex / Copilot / Gemini). No flag needed.
- Artifacts live under `.kobiton/sessions/<session-id>/` — workspace-relative, not `/tmp` (consistent with `run-interactive-cli-session`).
- The skill writes nothing to `tools/*.yaml` and does not add any MCP tool. It only consumes existing MCP tools (`reserveDevice`, `getSession`, `terminateSession`, etc.).
