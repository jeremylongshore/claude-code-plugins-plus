---
name: run-automation-suite
description: >-
  Run local Appium test scripts against Kobiton devices. Guides through app
  upload, device selection, capability parsing, and local execution. Use when
  the user asks to run mobile tests, validate an APK or IPA on Kobiton
  devices, or kick off an Appium suite from a local script directory.
  Trigger with "run kobiton tests" or "execute appium on kobiton".
allowed-tools: >-
  Read, Edit,
  Bash(node:*), Bash(npm:*), Bash(npx:*), Bash(yarn:*), Bash(pnpm:*),
  Bash(python:*), Bash(python3:*), Bash(pytest:*),
  Bash(java:*), Bash(mvn:*), Bash(gradle:*), Bash(./gradlew:*),
  Bash(dotnet:*),
  Bash(ruby:*), Bash(bundle:*), Bash(rspec:*),
  Bash(open:*), Bash(xdg-open:*), Bash(sleep:*),
  Bash(bash:*), Bash(pwsh:*), Bash(osascript:*)
version: 1.0.2
author: Kobiton Inc.
license: MIT
compatibility: >-
  Compatible with any MCP-aware AI coding assistant. Requires Node.js >= 18
  and Appium 2.x. Test scripts must use Appium WebDriver protocol.
tags: [mobile, testing, appium, automation, devices, kobiton]
---

# Run Automation Suite

## Overview

Execute Appium-based mobile test automation suites on Kobiton's device cloud. Given a local Appium test script, this skill identifies the target app, selects an available device, parses and reconciles capabilities, runs the script in the background, and surfaces the resulting session URL plus artifacts (video, logs, screenshots, reports).

Use this skill when the user asks to run mobile tests, validate an APK or IPA across real devices, or trigger a Kobiton-hosted automation run from a local script directory.

## Prerequisites

Before invoking this skill, ensure:

- **Kobiton MCP connection** - the Kobiton MCP server is reachable (default `api.kobiton.com/mcp`; check `.mcp.json` for the configured endpoint).
- **Local Appium test script** - a runnable Appium WebDriver script (`.js`, `.ts`, `.py`, `.java`, `.kt`, `.cs`, `.rb`) referencing desired capabilities for the target platform.
- **Runtime installed locally** - Node.js + npm/npx, Python + pip, Java + mvn/gradle, .NET SDK, or Ruby + bundle, whichever your test script uses.
- **App build (or store reference)** - either a local `.apk` / `.ipa` / `.zip` build artifact for upload, or a `kobiton-store:vXXXXX` reference for an existing upload.
- **Kobiton account** - credentials with device access for the target platform (Android / iOS) and remaining session quota.

## Authentication

This skill calls tools served by the Kobiton MCP server at `api.kobiton.com/mcp`. Two authentication configurations ship with the plugin; one of them must be active before any MCP tool will respond:

| Config file | Auth mechanism | When to use |
|---|---|---|
| `.mcp.json` (default) | OAuth 2.1 browser flow | Interactive AI-CLI session for an end user |
| `.mcp.apikey-example.json` | Basic auth header — `Authorization: Basic base64(username:apikey)` from the `KOBITON_AUTH` env var | CI / headless / scripted invocations; copy this file over `.mcp.json` |

If the skill is invoked and no MCP connection is established, abort step 1 and surface a clear error: the user needs to authenticate the Kobiton MCP server in their AI CLI before any device or session call can succeed. The exact invocation depends on the host (e.g. `/mcp` in Claude Code, `/mcp auth kobiton` in GitHub Copilot CLI and Gemini CLI, automatic browser flow on first tool call in Codex CLI, `/mcp list` then Login in Cursor CLI — see the plugin README for current per-CLI commands). Do NOT attempt to recover by retrying — the auth context is fixed at session start.

## Instructions

### 1. Identify the app

**IMPORTANT: Always ask the user this question, even if they already provided an app file path. Do NOT skip ahead or start uploading automatically.**

Ask the user:

> "Would you like to:"
> 1. Upload a new app build
> 2. Use an existing app from Kobiton Store or a provided URL

Wait for their response before proceeding. Do not call any upload or app-related tools until the user responds.

**If uploading a new app:** Look for .apk, .ipa, .zip files in the project context, or ask the user for the file path. Upload via `uploadAppToStore` (permanent, visible in app repository). This is a four-step process: call the tool to get a pre-signed URL, upload the file via PUT, confirm the upload via `confirmAppUpload`, then poll `getAppParsingStatus` with the returned `versionId` until the state is terminal - `OK` means ready to use; a `FAILURE_*` state means parsing failed. `confirmAppUpload` may return `appId: null` for a brand-new upload - `getAppParsingStatus` resolves the real `appId`.

**If reusing an existing app:** Check `appium:app` field of capabilities in the test script. Call `listApps` with that app version as keywork to check uploaded or not. Let the user pick the version to use (e.g., `kobiton-store:v72107`) if needed

### 2. Select a device and ask how to observe the run

Ask the user which device or platform to target.

Call `listDevices` with the relevant platform filter to show available options.

If the user has a specific device in mind, confirm its availability with `getDeviceStatus`.

Reserve the device with `reserveDevice` if needed.

**In the same exchange, ask how they want to observe the run** — don't wait until the script is already running to raise it:

> "Open the device live view in a browser window to watch the run, or run it in the background?"

Remember the choice; act on it in Step 5 (which happens right after the script launches in Step 4). Do NOT auto-open a window without asking — some users prefer silent runs, especially on shared screens. If the user's request already made the preference clear (e.g. "just run it in the background", "open it so I can watch"), skip the question and honor what they said.

### 3. Identify script & parse capabilities

Ask the user for the path to their local Appium test script.

Detect the language and runtime from the file extension. See [references/capabilities.md](references/capabilities.md#runtime-detection) for the full extension -> runtime -> common commands lookup and the manifest-based runner selection guidance.

Read the script file and extract the [key capability fields](references/capabilities.md#capability-fields) used by Appium and Kobiton (`platformName`, `udid`, `app`, automation/browser names, vendor `kobiton:*` extensions, etc.).

Identify how the UDID is passed into the script (CLI argument, environment variable, or hardcoded) so it can be overridden with the selected device.

**Appium runtime:** Check if the script contains `'kobiton:runtime': 'appium'` or equivalent. If it does NOT, do not inject it - the default Kobiton runtime will be used. Only if the user explicitly asks to use the Appium runtime should you suggest adding `'kobiton:runtime': 'appium'` to the script's capabilities.

**Validate capabilities:** After parsing the script, run the render script to generate the correct capabilities for the selected device and app:

```
node skills/run-automation-suite/scripts/render-capabilities.js \
  --platformName <platform> \
  --udid <udid> \
  --deviceName "<deviceName>" \
  --platformVersion <version> \
  --automationName <automationName> \
  --app <app> \
  --testingType app
```

For web testing, replace `--app <app>` with `--browserName <browser> --testingType web`.

Compare the JSON output against the parsed script capabilities using the [reconciliation rules](references/capabilities.md#reconciliation-rules): must-match fields are autocorrected to the rendered values, suggested defaults require user confirmation before changing, and user-controlled capabilities are left untouched.

The rendered output also includes `kobiton:aiToolName: "<host>"` so Kobiton can attribute sessions started by this skill to the calling AI workspace in adoption analytics. Resolution order:

1. `--aiToolName <name>` CLI flag (always wins; `""` opts out entirely)
2. `KOBITON_AI_TOOL_NAME` env var (also accepts `""` to opt out)
3. Auto-detect from runtime markers, any non-empty value:
   - `CLAUDECODE` -> Claude
   - `COPILOT_CLI` -> Copilot
   - `GEMINI_CLI` -> Gemini
   - `CODEX_THREAD_ID` (or `CODEX_CLI`) -> Codex — Codex CLI sets the thread ID, not a generic `CODEX_CLI` flag; the latter is accepted for manual override only
4. If nothing matches, no `kobiton:aiToolName` capability is emitted.

This capability is treated as **must-match** during reconciliation (see `references/capabilities.md`): if the rendered output includes `kobiton:aiToolName`, always overwrite any existing value in the user's script with it. A stale value from a prior session run under a different CLI would mis-attribute adoption analytics. If the rendered output omits the capability (no runtime marker matched), leave the user's value untouched.

**The injection is non-interactive.** Edit the script silently using your `Edit` tool — mention the one-line change inline in your reply for transparency (e.g., *"Added `kobiton:aiToolName: 'Gemini'` to your capabilities for adoption analytics."*), but **do NOT ask the user to confirm** before editing. The value is deterministic (it matches the runtime env from auto-detect), there is nothing to negotiate. If the user objects, they can revert the edit themselves.

**Required: verify the injection landed before Step 4.** The `kobiton:aiToolName` capability must be present in the script's source code (e.g., the capabilities object/dict/map). If your reconciliation pass didn't write it to the script, Kobiton will never see it — there is no sidecar config that injects it at runtime. Confirm with a literal-string grep against the user's script:

```bash
grep -F 'kobiton:aiToolName' <path-to-user-script>
```

- **Match found** — injection succeeded, proceed to Step 4.
- **No match, rendered output had a value** — your edit was skipped. Use your `Edit` tool to add the capability to the script's capabilities block now (use the language-appropriate syntax for the script — JS/TS object literal, Python dict, Java `Map.of(...)` / `DesiredCapabilities`, .NET `AppiumOptions.AddAdditionalCapability(...)`, Ruby hash), then re-run the grep. **Do NOT proceed to Step 4 until the grep succeeds.**
- **No match, rendered output omitted the capability** — expected (no runtime marker matched, or user opted out via `--aiToolName ""` or `KOBITON_AI_TOOL_NAME=""`). Skip injection, proceed.

### 4. Confirm & execute

Present a summary to the user before running:

```
Language:     Node.js
Script:       /path/to/test.js
Platform:     Android
Device:       Pixel 4 (9B211FFAZ0017F)
App:          kobiton-store:v72107
Session Name: Verify Appium session
Command:      node /path/to/test.js 9B211FFAZ0017F
```

Wait for user confirmation, then execute the command **in the background** using your shell execution tool.

### 5. Open running session in browser

Act on the observation choice the user already made in Step 2 — do **not** re-ask here.

If they chose to **run in the background**, skip to Step 6.

If they chose to **open the live view**, wait **2 seconds** after the script was launched in Step 4 (to allow the session to initialize on Kobiton), then open the session in the user's browser.

**Determine the portal URL:** Read `.mcp.json` to get the MCP server URL, then derive the portal base URL by replacing the `api` host with the `portal` equivalent (drop any trailing `/mcp`):

| MCP Server | Portal Base URL |
|------------|----------------|
| `https://api.kobiton.com/mcp` | `https://portal.kobiton.com` |
| `https://api-*.kobiton.com/mcp` | `https://portal-*.kobiton.com` (same `*` suffix) |

For example, an `api-*.kobiton.com` host maps to its matching `portal-*.kobiton.com` host. If the mapping doesn't resolve, fall back to `https://portal.kobiton.com`.

**Build the launch URL.** Default to the **device-only view** — it shows just the device screen, no surrounding Kobiton UI, ideal for watching an automation run, sharing, or embedding:

```
<portal-base-url>/devices/launch?id=<deviceId>&view=device-only
```

Where `<deviceId>` is the ID of the selected device from Step 2 (returned by `listDevices`, `getDeviceStatus`, or `reserveDevice`).

The device-only view is also **interactive for redirection**: when the user taps or swipes on the device canvas, those gestures BOTH (a) reach the device in real time (just like a normal click-to-device tap) AND (b) are captured and made available to you via `getUserInputEvents` (see Step 6) so you can see what the user just did and adapt your plan.

**Fall back to the default view** (without `&view=device-only`) only when the user explicitly asks to interact with the device — e.g. "let me drive it manually", "open the full session view", "I want to tap on the screen", or similar interaction-implying language. The default view shows the full Kobiton UI around the device (sidebars, controls, action panels):

```
<portal-base-url>/devices/launch?id=<deviceId>
```

**Launch via the chromeless helper (default — gated on saved browser preference).** For the **device-only** URL branch above, check auto memory for a saved browser preference:

- **No preference saved**, OR **preference is Google Chrome** → invoke the chromeless launcher (the section below). On the very first run the launcher prompts the user to confirm Chrome via the macOS Automation grant; the choice is sticky.
- **Preference is Safari, Firefox, or Default browser** → skip the chromeless launcher entirely. The user has explicitly told us they prefer a non-Chrome browser, and a chromeless Chrome window would override that. Fall through to the **Default-browser fallback** section below — that path honors their saved preference.

When the chromeless launcher is invoked, it opens Chrome in `--app` mode (no tab strip, no URL bar, no bookmarks bar) and resizes the window to a device-shaped frame. **Pick width and height based on the reserved device's form factor** (the device name from Step 2 — `listDevices` / `getDeviceStatus` / `reserveDevice`):

| Device class | Detect by name (case-insensitive) | Portrait `width × height` | Landscape `width × height` |
|---|---|---|---|
| Tablet | `iPad`, `Galaxy Tab`, `Pixel Tablet`, `Surface`, `MatePad`, or any model with "Tab" or "Pad" in the name | **`780 × 920`** | `920 × 780` |
| Fold (unfolded) | `Fold`, `Z Fold`, `Pixel Fold` | **`880 × 920`** | `920 × 880` |
| Phone (default — Galaxy, Pixel, iPhone, OnePlus, Xiaomi, …) | none of the above patterns match | **`540 × 920`** | `920 × 540` |

All three presets share the same `920 px` height — only the width grows by device class — so the chromeless window's vertical footprint stays consistent.

If `getSession` / the rendered capabilities report `orientation=LANDSCAPE`, swap width and height (use the **Landscape** column above). Default is portrait.

Pick the right command for the host OS. **Run it in the background** (Claude Code: `Bash` tool with `run_in_background: true`; other hosts: append `&` and `disown`) so the launcher's resize-polling loop doesn't block Step 6's result collection. The launcher's stdout/stderr and exit code surface later when it completes; the session URL printed above is the user's fallback if the launcher silently fails.

| OS | Command |
|----|---------|
| macOS | `bash skills/run-automation-suite/scripts/chromeless-launcher.sh --url "<url>" --width <W> --height <H>` |
| Windows | `pwsh skills/run-automation-suite/scripts/chromeless-launcher-windows.ps1 -Url "<url>" -Width <W> -Height <H>` |
| Linux | `bash skills/run-automation-suite/scripts/chromeless-launcher.sh --url "<url>" --width <W> --height <H>` (launch-only — no auto-resize on Linux) |

`<W>` and `<H>` are the dimensions from the table above — substitute literally.

**On macOS, the very first run** triggers a system prompt: *"X wants to control Google Chrome.app"* — click OK. The grant lives under System Settings → Privacy & Security → **Automation** (NOT Accessibility) and persists per host process. Tell the user this once if you can see it's their first invocation.

**Launcher exit codes drive the fallback** (they arrive in the background-task completion event, not synchronously):

- `0` — Chrome was launched (resize may have logged a warning, but the session is fine). **Continue to Step 6.**
- `2` — Chrome / Chromium is not installed on the host. **Fall through** to the default-browser fallback table below.
- `64` — usage error (missing `--url` or unknown flag) — surface to the user; the launcher is buggy.

**Manual-interaction fallback URL.** When the URL branch above was the **manual-interaction** form (the user explicitly asked to drive the device, so the URL has no `?view=device-only`), skip the chromeless helper entirely and go straight to the default-browser fallback below — the user wants the full Kobiton UI around the device, so a chromeless `--app` window would defeat the point.

**Default-browser fallback** (used when (a) the saved browser preference is Safari/Firefox/Default, OR (b) chromeless exited 2 because Chrome is absent, OR (c) the URL branch is the manual-interaction form):

Check auto memory for a saved browser preference. If none exists, ask the user which browser to use:

> "Which browser should I open the session in?"
> 1. Google Chrome
> 2. Safari
> 3. Firefox
> 4. Default browser

Save their choice to auto memory so they are not asked again in future sessions.

| Choice | Command |
|--------|---------|
| Google Chrome | `open -na "Google Chrome" --args --new-window <url>` |
| Safari | `open -a "Safari" <url>` |
| Firefox | `open -a "Firefox" <url>` |
| Default browser | `open <url>` |

On Linux, use `xdg-open <url>` (browser selection is not supported — always opens the default).

### 6. Collect results

While the background script is running, call `listSessions` with `deviceId=<deviceId>` (from Step 2) and `state='START'` to find the session that just triggered. Use the most recent session (first result) as the match.

Call `getSession` with the matched session ID to get detailed results.

Call `getSessionArtifacts` with the session ID to retrieve:

- Video recording URL
- Device logs URL
- Screenshots
- Test reports

**Watch for user redirection (when the device-only view is open).** While the background script runs, poll `getUserInputEvents` with the matched `sessionId` between your scripted commands — no faster than once per second. Track the timestamp of the newest event you have seen and pass it as `sinceTimestamp` on the next call so you only get new gestures:

- On the first poll, omit `sinceTimestamp` to drain everything buffered. Each response is capped (default 50 events, max 200) — if you see exactly that many events in a single response there may be more behind them; re-poll immediately with `sinceTimestamp` set to the newest event's timestamp to page forward.
- If the response contains events, surface them as observations and let them steer your plan — e.g. a touch at `(0.42, 0.78)` near the bottom-right means "the user tapped there; they may want me to focus on whatever is at that position (looks like Settings)." A swipe (`xNorm/yNorm` → `xNorm2/yNorm2`) means they want you to scroll or navigate in that direction.
- Advance `sinceTimestamp` to the largest `timestamp` you received, so the next poll returns only newer gestures.
- The user's tap also reaches the device in real time, so by the time you read these gestures the device has already moved. Don't try to "replay" or undo them — they reflect what the human just did. Adapt your remaining script: pivot focus, re-orient, or pause for the next user signal. You are no longer the sole driver of the device while a human is watching the device-only view.

### 7. Summarize

Present a summary to the user:

- Pass/fail status
- Session link in Kobiton portal
- Video recording link
- Key error messages (if failed)
- Execution duration

## Output

On successful completion, the skill returns:

- **Live session URL**: `https://portal.kobiton.com/devices/launch?id=<deviceId>` — opened in a browser window once the session starts **only if** the user chose to watch the run at Step 2; background runs skip the window and just surface the URL as text.
- **Session metadata**: session ID, device ID, app version, start time, and final pass/fail status (via `getSession`).
- **Session artifacts**: video recording URL, device logs URL, screenshots, and test reports (via `getSessionArtifacts`).
- **Execution duration**: wall-clock time from script launch to completion.

On failure, the skill surfaces error output from the test runner, the session URL if the session reached Kobiton (useful for portal-side debugging), and suggested next steps drawn from the categories in `## Error Handling`.

## Error Handling

- `listDevices` returns empty: suggest broadening filters (remove platform/group constraints) or trying again later when devices free up.
- Upload fails or times out: retry the upload. Pre-signed URLs expire after 30 minutes - if expired, call the upload tool again to get a fresh URL.
- App parsing fails (`getAppParsingStatus` returns a `FAILURE_*` state): surface the state to the user and stop - do not reserve devices or start a session with that build.
- Session stuck in a non-terminal state: poll `getSession` with a reasonable timeout. If still running, offer to call `terminateSession` and retry.
- `reserveDevice` fails (device already taken): call `listDevices` again to find another available device.
- Script execution fails: check error output for missing dependencies (e.g. `wd`, `appium`), incorrect UDID, or network issues. Suggest fixes.

## Examples

### Run a single test on the first available Android device

> "Run `./tests/checkout.js` on a Pixel 7 - upload the latest APK from `./build/app.apk` first."

The skill detects the `.apk` build, uploads it via `uploadAppToStore`, queries `listDevices` filtered to Pixel 7, reserves the device with `reserveDevice`, parses the script's capabilities, confirms the launch summary with the user (asking at device selection whether to watch the run or run it in the background), runs `node ./tests/checkout.js <udid>` in the background, opens the live session URL in the user's browser if they chose to watch, and returns the session ID plus artifacts when the run completes.

### Run an attached IPA with an attached script on a specific iOS device

> "Test this app @TestApp.ipa by this script @automation.js on Kobiton iOS iPhone 15 Pro"

The skill resolves the two `@`-referenced files from the chat context, uploads `TestApp.ipa` via `uploadAppToStore`, queries `listDevices` filtered to iOS iPhone 15 Pro, reserves the matching device, parses `automation.js` for capabilities, reconciles them against the rendered defaults for the selected device, confirms the launch summary with the user (asking at device selection whether to watch the run or run it in the background), runs `node automation.js <udid>` in the background, opens the live session URL in the user's browser if they chose to watch, and surfaces the session ID plus artifacts when the run completes.

## Resources

- [Kobiton available capabilities reference](https://docs.kobiton.com/automation-testing/capabilities/available-capabilities) - canonical list of `kobiton:*` and supported `appium:*` capabilities the skill's `render-capabilities` step compares against.
- [Appium 2.x documentation](https://appium.io/docs/en/2.0/) - driver-specific capability docs (UiAutomator2, XCUITest) and Appium client libraries for each runtime.
- [`kobiton/automate` plugin source](https://github.com/kobiton/automate) - issue tracker, contribution guide, and the tool YAML schemas this skill orchestrates.
- [Sample prompt patterns](../../docs/examples.md) - natural-language prompt examples organized per MCP tool, useful for crafting requests that trigger this skill cleanly.
