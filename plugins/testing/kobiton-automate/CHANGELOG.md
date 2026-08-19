# Changelog

## 1.10.1 - 2026-08-12

### Fixed: adb-shell guidance now carries the full restricted-session policy

1.10.0 introduced basic restricted-shell guidance (bare-command + local-filter, the forbidden-character rejection). This release replaces it with the complete policy for restricted sessions (public cloud and trial devices): the deny-by-default command whitelist by category, the full forbidden-character set (pipes **and quotes** — there is no on-device composition form at all), the file-path allowlist, the single permitted `settings` key (`secure enabled_accessibility_services`), the four rejection message shapes — incl. the settings-specific message, verified live on restricted devices — with the exit-0 gotcha (rejections print on stdout and exit 0, so scripts must string-match the first line rather than `$?`), and a pointer to `kobiton device adb-shell --help` as the always-current authority.

The quoted on-device form is scoped to dedicated (unrestricted) devices; the command table gains a **Restricted** column covering every row — including `ls`/`cat` path limits, the `input text` single-token limit, `wm size` → `wd get window/rect`, a new `screencap` row, and the accessibility-services settings key. `device forward` is documented as a foreground command that holds the local port until killed, and `references/response-shapes.md` and `AGENTS.md` carry the same facts so no host is left with the old guidance.

The whitelist entries describe the current deviceConnect sanitizer; on environments running an older deviceConnect a few expanded entries (`cat /proc/version`, `screencap`, `input`, the settings key) may still be rejected — the `--help` pointer is the always-current authority.

No binary change ships with this release: the CLI is downloaded per the 1.10.0 pin model, and the pinned build already carries the file-transfer status fix this branch originally bundled.

## 1.10.0 - 2026-08-11

### Changed: the CLI binary is downloaded on install, no longer committed to the repo

`skills/run-interactive-session/bin/kobiton` (an 11.8 MB x86_64 macOS binary that required a manual re-commit on every CLI release) is gone. Instead, the plugin pins a CLI build version in `skills/run-interactive-session/CLI_VERSION`, and `scripts/install-cli.sh` — the same script the SessionStart hook and `/automate:setup` already run — downloads that build from `public.kobiton.download` on first run, verifies its published sha256, and caches it under `~/.kobiton/cli/<version>/`. Cache hits perform no network I/O, so session start stays fast; offline sessions keep working from the cache. The pin advances with plugin releases, after the skill docs are validated against that build — the docs and the binary move in lockstep, the same guarantee bundling gave, without megabytes of binary in git history.

If the pinned build is no longer published (the download server prunes old versions), the installer keeps a cached build with a drift warning, or — with no cache at all — falls back to the newest published build with a loud warning telling the user to update the plugin (newer releases pin a validated build). A corrupted download (checksum mismatch) is discarded and never replaces a working cache. `run.sh` itself never touches the network: it resolves the pinned version from the cache, falls back to the newest cached build with a warning, and otherwise points at `/automate:setup`.

### New: `run-interactive-session` on Linux and Windows

The download model unlocks the other published CLI builds: the skill now runs on **macOS (Apple Silicon), Linux (x64), and Windows (x64 under Git Bash)**. On Windows, the installer writes a bash exec-shim at `~/.kobiton/bin/kobiton` instead of a symlink (MSYS `ln -sf` copies files, which would break the wrapper's path resolution). Apple Silicon Macs now get the native arm64 build instead of running x86_64 under Rosetta 2.

**Intel Macs are no longer supported** — no macos-x64 build is published. The previous release (1.9.0 and earlier) bundled an x86_64 binary that ran natively there; Intel-Mac users should stay on 1.9.0 or use `run-automation-suite` / `drive-automation-session`, which remain fully cross-platform.

### New: `/automate:doctor` reports CLI version drift

A fifth check reports the plugin's pinned version, the installed binary's version, the newest published build, and whether the pinned build is still downloadable — all via HEAD-only requests, nothing downloaded. Drift between installed and pinned is flagged with the remedy; a newer build existing upstream is informational, never a failure.

### Fixed: findings from live Windows (Git Bash) verification

- `/automate:setup` no longer requires Python: the credentials-file probe and atomic write now use Node, which every supported host CLI already runs on. Windows commonly has no Python — the Microsoft Store `python3` stub exits without running anything, which broke setup outright.
- `/automate:doctor` Check 2 tries GNU `stat -c` before BSD `stat -f` — on Git Bash/Linux the old order dumped a filesystem-info blob into the reported mode string (verdict was unaffected).
- `run-interactive-session` documents the restricted device shell honestly: on the common cloud-device policy the CLI rejects on-device pipes (`Input contains a forbidden character`) and URL arguments to `am`; the skill now teaches the bare-command + local-filter pattern and a UI-driven open-a-URL recipe instead of piped commands that fail there.
- Windows note added to setup: POSIX `0600` doesn't map onto NTFS ACLs, so the credentials file may report `644` there; doctor reports it informationally.

The compatibility matrix (`CLAUDE.md`), each affected skill's Prerequisites and `compatibility:` frontmatter, `AGENTS.md`, and README were updated together per the matrix's own update rule. No tool YAML or MCP server contract changed.

## 1.9.0 - 2026-07-29

### New: per-skill compatibility matrix

`CLAUDE.md` gains a **Skill compatibility matrix** — for each of the 5 skills: whether it needs a persistent local filesystem, whether it needs the `~/.kobiton/.credentials` file that `/automate:setup` writes, any local-binary/OS constraint, whether it needs a streamed-watch affordance, and whether it is pure MCP glue that runs with none of those. Every cell is checkable against that skill's `allowed-tools` **plus what its bundled scripts actually do** — `allowed-tools` grants a superset, so a declared tool is not proof the skill uses it. It sits under Cross-tool surface, extending the existing host→config table rather than replacing it. `AGENTS.md` carries a prose summary that links to the matrix instead of duplicating it, so the two cannot drift apart.

Columns are keyed on capabilities rather than product names, because "has a filesystem" is not the same as "can run this skill": a chat surface with code execution has both a filesystem and Node, yet still cannot run the credential-dependent skills, since nothing there can execute `/automate:setup`. Naming the specific missing capability tells a user what to do next in a way that naming a host class does not.

`create-test-run` is the only pure-MCP skill — it needs nothing but an authenticated MCP connection — and it now confirms it can actually monitor before offering to, since `monitor-test-run` runs a local poller that reads the credentials file.

Each skill's `compatibility:` frontmatter was brought in line with the matrix, so a skill file can no longer contradict itself about where it runs.

### Changed: each skill states its host, platform, and file-access requirements up front

All 5 `SKILL.md` files now open their existing `## Prerequisites` with the host/platform/file-access requirement and the route to take when it isn't met — instead of burying it mid-body (the CLI platform limit was ~43 lines in; the `Monitor` substitution ~169 lines in). One requirements list per skill, not a parallel block restating it.

### Fixed: the bundled CLI is x86_64, not "Apple Silicon only"

`bin/kobiton` is a single-slice **x86_64** Mach-O with no arm64 slice (`file` / `lipo -info`), so it runs **natively on Intel Macs** and on Apple Silicon **under Rosetta 2**. It had been documented as "macOS Apple Silicon only" — which both excluded Intel Macs, where it runs natively, and implied a native arm64 build that does not exist. Corrected in `CLAUDE.md`, `AGENTS.md`, and `README.md`. (The 1.8.0 entry below repeats the old wording; it is left as written for history.)

Also corrected: the setup command claimed binaries ship for "only macOS arm64 and Linux x64" — no Linux binary ships and the installer does no per-platform selection; and `drive-automation-session`'s `compatibility` field described MCP `getCredential` with the credentials file as a fallback, when `appium.js` reads `~/.kobiton/.credentials` directly and never calls that tool, making the file required.

Platform and credential enforcement remains in `scripts/run.sh`, which already reports a missing binary or missing credentials with the `/automate:setup` and `/automate:doctor` remedies; the skill docs state the constraint and route the user rather than re-implementing the check.

No tool YAML or MCP server contract changed.

## 1.8.0 - 2026-07-21

### Renamed: `run-interactive-cli-session` → `run-interactive-session`

The interactive testing skill is now named `run-interactive-session`. Behavior is unchanged — same CLI wrapper, same workflow, same macOS-Apple-Silicon binary. The skill directory, frontmatter, and every docs reference use the new name; only this changelog keeps the old one for history.

### New: Getting Started onboarding section

README's Getting Started now walks a first-time Kobiton user from install to a saved test case: a narrated first-session path, an intent-based skill-routing table covering all 5 skills, a concepts glossary (session, session type, test case, revisit, test run, suite, reservation, UDID, live remediation), and a prerequisites checklist with one copy-pasteable end-to-end example. `CLAUDE.md` carries a condensed version and `AGENTS.md` mirrors the substance for non-Claude hosts.

### New: ambiguous-prompt routing + Kobiton session model for agents

The agent context files (`AGENTS.md`, `CLAUDE.md`) now document how to route prompts that name a goal but not a method ("test the login screen of app ABC"): route by signal when one exists, otherwise ask one short question with `drive-automation-session` as the recommended default (its sessions stay saveable via `saveTestCase`). An intent-synonym table maps phrasing like "rerun / revisit / replay a test case" → `create-test-run`, "rerun a session" → save it as a test case first, and "replay the recording" → session artifacts, not a new run. A session-model section promotes cross-skill platform knowledge into one place: session types (`AUTOMATION` / `CLI` / `MANUAL`, and `MIXED` when a human interacts in the live view during an automation session), test cases being session-based, test runs as per-device revisit executions, `COMPLETE` vs `TERMINATED` end states, and rerun-scoped live-remediation resolutions.

## 1.7.1 - 2026-07-03

### Fix: `run-automation-suite` launches the chromeless launcher in the background

Step 5 now instructs the host to invoke the chromeless launcher in the background (Claude Code: `Bash` with `run_in_background: true`; other hosts: `&` + `disown`), matching `drive-automation-session`. Previously the synchronous invocation let the launcher's resize-polling loop block the skill from reaching Step 6 (session/result collection). Launcher exit codes now arrive in the background-task completion event rather than synchronously.

### `run-automation-suite` asks how to observe the run up front

The "open the live view or run in the background?" question now happens in Step 2 alongside device selection (mirroring `drive-automation-session`'s Step 0), instead of after the script has already launched in the old Step 5. Step 5 acts on the remembered choice without re-asking. `AGENTS.md` mirrors the reordering for non-Claude hosts.

## 1.7.0 - 2026-06-24

KOB-53297 (Epic): the `getOrgSettings` tool plus the `create-test-run` and `monitor-test-run` skills for creating and watching test runs with live remediation.

### New `getOrgSettings` tool (`tools/user.yaml`)

Read-only MCP tool that returns the calling user's organization settings block — org-level feature flags and preferences, including `live_remediation_enabled` (governs whether a blocked test-run execution pauses for interactive live remediation or auto-fails with `BLOCKER_ENCOUNTERED`). Resolves the org from the OAuth context; `userIntent`-only input. Full 4-hint annotation block (`readOnlyHint: true`, `destructiveHint: false`, `openWorldHint: false`); `getCredential` upgraded to the same 4-hint shape in passing. Server handler ships in `kobiton/api` (the MCP server) — see KOB-53298.

### New `create-test-run` skill (`skills/create-test-run/`)

`automate:create-test-run` turns a "run this" request into a created test run with minimal friction, then offers to watch it. When details are omitted it fills defaults from the `createTestRun` schema (1 device matching the target platform via `INDIVIDUAL_DEVICES`, latest test-case version, the case's app, `CROSS_DEVICE`), shows a one-screen summary, and asks to proceed or customize before creating. After creation it offers monitoring in a **single** prompt — monitor + auto-open live remediation (only when the org flag is ON), monitor only, or don't monitor — and delegates the watch to `monitor-test-run` (passing the auto-open choice so that skill doesn't re-ask). The summary shows human-readable allocation labels matching the Portal dropdown (`CROSS_DEVICE` → "All Permutations — run each test case on each device"; `SINGLE_DEVICE` → "Random Allocation — run each test case once, randomly chosen from the selected devices"), never the bare enum. Conversational glue over `createTestRun` / `getOrgSettings` / `listDevices`; no local runtime.

### `createTestRun` tool schema — exact enum values

`tools/test-management.yaml` now declares the real `enum`s for `createTestRun`, fixing a recurring first-call rejection where the model used the documented lower-case examples (`test_case`, `specific_devices`). Authoritative values: `testSelection.type` ∈ `TEST_CASE`/`TEST_SUITE`, `deviceSelection.type` ∈ `INDIVIDUAL_DEVICES`/`DEVICE_BUNDLE`, `deviceAllocationStrategy` ∈ `CROSS_DEVICE`/`SINGLE_DEVICE`.

### New `monitor-test-run` skill (`skills/monitor-test-run/`)

`automate:monitor-test-run` watches a running Kobiton test run and narrates it: reads the live-remediation flag once via `getOrgSettings`, watches the run via a bundled poller until every execution is terminal, surfaces the live-remediation URL the moment an execution is blocked, and post-mortems so a `COMPLETED` execution with `failure_type = BLOCKER_ENCOUNTERED` is never reported as passed. Quiet on passes, loud on blockers and the final summary; suite runs grouped by test case. Uses `getOrgSettings` (up front) and `terminateTestRun` (on request); the watch is the bundled script. See KOB-53299.

- **Execution-status model** follows the revisit-execution contract: terminal status is `COMPLETED`, with the outcome carried by `failure_type` (`NONE` = passed, `BLOCKER_ENCOUNTERED`, `TERMINATED_BY_USER`/`TERMINATED_BY_SYSTEM` = terminated, others = failed). The blocked moment is flag-dependent — with live remediation **on** the execution pauses in a blocked-waiting state and waits; with it **off** it ends immediately as `COMPLETED + BLOCKER_ENCOUNTERED`.
- **Device id + live-remediation window.** Reads `assigned_device_id` straight off each execution to build the live-remediation URL (paired with an `api` change that passes `assigned_device_id` through the `getTestRun` MCP response). The portal base is derived from the MCP server's env (`api-{env}` → `portal-{env}`), not hardcoded to production. When live remediation is on, the skill asks **up front** (before monitoring) whether to auto-open the live-remediation window on a blocker; if yes, it opens the view via the shared chromeless launcher when a blocker hits — full default view in a wider-than-phone 1400×900 window — falling back to the printed URL otherwise or if Chrome is absent.
- **Bundled emit-on-change poller** (`scripts/poll-test-run.js`). The watch loop is a Node script (no deps; reads `~/.kobiton/.credentials` for auth, skipping commented/INI lines) that polls run state over REST and prints a line **only when an execution's state changes** (dispatched / blocked / resumed / terminal), backing off during quiet stretches and exiting on `DONE`. (A background process can't call the MCP `getTestRun` tool, hence REST.) The host must **stream** the poller's stdout so each line re-engages it: on Claude Code via the `Monitor` tool (not `run_in_background`, which doesn't stream back — a real prior failure); other hosts use their native streamed-shell / watch / loop affordance, falling back to a foreground loop rather than a silent detached process.
- **Blocked-waiting is treated as an open ask of the user, not a passive watch.** A flag-ON blocker is on a resolution countdown, so the skill frames it urgently ("action needed now — will auto-fail on timeout") and the poller emits a throttled `WAITING blocked=<n>` heartbeat (default 60 s, `--waiting-heartbeat 0` disables) while executions stay blocked, so the host keeps nudging instead of going silent until the timeout. A blocked execution that ends `BLOCKER_ENCOUNTERED` is reported as **timed out / unresolved**, never as a pass.
- `.codex/` mirror included.

## 1.6.0 - 2026-06-12

### New `drive-automation-session` skill

`automate:drive-automation-session` drives an already-reserved Kobiton device from a natural-language intent. Opens an **automation-type** Appium session directly against the Kobiton WebDriver hub (the first direct-Appium-HTTP path in this plugin), runs a turn-based observe-act cycle, and returns a session id consumable by `getSession`, `getSessionArtifacts`, and `saveTestCase` unchanged. Complements `run-interactive-cli-session` (CLI session type) — does not replace it. Sessions open with `appium:newCommandTimeout: 1800` (30 min) so they survive human-in-the-loop pauses, and `kobiton:scriptlessCapture: true` so the result is `saveTestCase`-consumable.

- **`scripts/appium.js`** — Node `node:https`-only Appium HTTP client; no package dependencies. Generic mode (`--method`/`--url`/`--req-body`) for raw Appium calls, plus `screen` / `actions` / `touch-perform` / `control` helpers. Reads `~/.kobiton/.credentials` (written by `/automate:setup`) directly each invocation — credentials never appear in argv, env, or the AI host's transcript. `screen` captures both `iter-N.xml` and `iter-N.png` by default (`--xml-only` / `--png-only` to skip one); webview `/source` is stripped before write (see below). Exits 0 for every outcome and writes `iter-N.error.json` on failure, leaving recoverable-vs-fatal classification to the host.
- **`scripts/strip-webview-dom.js`** — pure-regex strip that drops `<script>`/`<style>`/`<head>`/`<noscript>` blocks, base64 `<img>`, and attributes outside an agent-driving whitelist. Cuts webview source ~10× (558KB → ~50KB on the pilot YouTube run) so the host can read `iter-N.xml` whole; the raw body is kept as `iter-N.full.xml` as an escape hatch.
- **Per-turn pattern (`SKILL.md`)** — each turn the host picks exactly one of three branches: `screen` (observe), an Appium call (act), or `control` (end). The script enforces no blocker thresholds; the host watches the screen-state hash and emits `control --blocked` when stuck. `MAX_ITERS=100` (overridable) is the only programmatic safety net.
- **Cleanup** — a Bash `trap` issues `DELETE /wd/hub/session/{id}` on exit, so Kobiton records the session `COMPLETE`. `terminateSession` is not called by default (it would mark the session `TERMINATED`); reserved for force-kill.
- **Live view** — Step 0 asks device + foreground/background preference before session create. Foreground reuses `run-automation-suite`'s chromeless-launcher; URL shape `<portal>/devices/launch?id=<deviceId>&view=device-only`.
- **`references/`** — `endpoint-reference.md` (allowlisted endpoints + selector-construction guide), `loop-discipline.md` (per-turn pattern + stuck patterns + reading errors), `capabilities.md` (desired-caps payload + credentials model).

### Renamed: `run-interactive-test` → `run-interactive-cli-session`

The CLI-session skill is renamed to make the `<verb>-<session-type>-session` naming consistent with the new `drive-automation-session` (automation session type). Skill behavior is unchanged. `/automate:setup`, `scripts/install-cli.sh`, `AGENTS.md`, `README.md`, and `CLAUDE.md` updated to the new path.

### Cross-skill: `run-automation-suite/scripts/render-capabilities.js`

Two new optional flags, both default-off (existing callers unaffected); `drive-automation-session` passes both:
- `--newCommandTimeout <seconds>` — emits `appium:newCommandTimeout`.
- `--scriptlessCapture` — emits `kobiton:scriptlessCapture: true` (KOB-41142), gating platform-side capture for `saveTestCase`.

The shared chromeless launcher's resize-polling budget is raised 10s → 30s (poll interval 0.5s → 1s) to cover Chrome cold starts.

### Test surface

176 vitest cases total (up from 105): `appium.test.js` (53 — generic mode + auto-wrap of flat caps on `POST /session` + `screen` modes + webview-strip/native detection + credentials file-source + injection safety), `strip-webview-dom.test.js` (14), and `render-capabilities.test.js` (+5).

## 1.5.0 - 2026-06-11

- New `getAppParsingStatus` MCP tool — checks the async parse status of an uploaded app version by `versionId`. After `confirmAppUpload` the app is created in state `PARSING`; poll this tool until the state is terminal (`OK` or a `FAILURE_*` value) before reserving devices or starting sessions. Also resolves the real `appId` when `confirmAppUpload` returned `appId: null` for a brand-new upload.
- `confirmAppUpload` description now documents the async parsing flow and points to `getAppParsingStatus` for polling.
- `docs/examples.md` gains an upload-then-poll example covering the new tool.

## 1.4.3 - 2026-06-02

- New `getUserInputEvents` MCP tool — surfaces the touch/swipe gestures a human makes on the device-only live view so an agent-driven session can be redirected mid-run. The user's tap reaches the device in real time AND is reported to the agent as an observation to react to ("the user just tapped Settings → pivot the test plan to Settings"). Keystroke / right-click / pinch / drag-off-canvas remain suppressed.
- `run-automation-suite` skill now polls `getUserInputEvents` between scripted commands.

## 1.4.2 - 2026-06-02

- **Fix Copilot CLI command loading:** the `name: "automate:setup"` / `name: "automate:doctor"` frontmatter in `commands/*.md` is now plain `name: "setup"` / `name: "doctor"` — Copilot CLI validates the `name` field and rejects colons ("Command name must contain only letters, numbers, hyphens, underscores, dot"), which broke command loading. Claude Code and Copilot CLI derive `/automate:setup` and `/automate:doctor` from the filename + plugin namespace as before; Gemini CLI (bundled TOML) and Codex CLI are unaffected.
- **Cursor CLI command names:** as a consequence, Cursor CLI now registers the commands as `/setup` and `/doctor` (Cursor applies no plugin namespace). They coexist with Cursor's built-in `/setup` — the plugin's entries are distinguishable by their Kobiton descriptions. README and command bodies updated accordingly.
- **Docs (Cursor CLI):** install steps describe the actual marketplace flow (repo parsing, Enter to install, restart `agent` so skills load), and a new Cursor CLI troubleshooting section covers stale/missing skills and commands, MCP disconnects, and the missing `~/.kobiton/bin/kobiton` wrapper.

## 1.4.1 - 2026-06-02

- **chromeless-launcher (mac):** detect Chrome / Chromium / Chrome Canary / Brave at their standard `/Applications/` paths instead of hardcoding only `Google Chrome.app`. Users running Chromium or Canary now get the chromeless window instead of silently falling through to the default-browser path. Linux already had this behaviour via `command -v` over a candidate list.
- **chromeless-launcher (all OSes):** validate `--width` / `--height` / `--x` / `--y` as positive integers at argument-parse time. Non-numeric, zero, or negative dimensions now exit `64` with a clear "must be a positive integer" message, instead of either tripping `set -e` on later arithmetic or producing an invalid window size.
- **Test surface:** 19 new vitest cases — numeric-validation rejection (9 cases across dispatcher / mac / linux shims), codex-mirror existence (5 cases), and codex-mirror byte-identity (5 cases). The new mirror-parity tests assert that `.codex/skills/run-automation-suite/scripts/` carries byte-identical copies of every launcher script — closing the gap where unit tests only covered the `skills/` tree.

## 1.4.0 - 2026-06-01

- New **chromeless launcher** for `run-automation-suite` Step 5: when the skill resolves the device-only view URL and the user's saved browser preference is Google Chrome (or no preference is saved), launch Chrome in `--app` window mode (no tab strip, no URL bar, no bookmarks bar) and resize the window to a device-shaped frame at runtime. Per-OS shims:
  - **macOS:** `osascript` resize loop with 10s poll, URL-substring window match, per-window `try`/`on error` so a stray window does not abort the iteration. Requires a one-time **Automation** grant for the host process to control Google Chrome (System Settings → Privacy & Security → Automation). Apple Events error `-1743` (Automation denied) is fail-open: the window opens at Chrome's default size, the launcher logs a hint, and the skill continues.
  - **Windows:** PowerShell + `Add-Type` `SetWindowPos`; matches the new window via a snapshot-before / diff-after over visible top-level Chrome windows (works whether Chrome was already running and `chrome.exe --app=` delegated to it, or started fresh).
  - **Linux:** launches Chrome `--app` + `--window-size` hint; no runtime resize (no portable cross-WM hook).
- **Device-class sizing heuristic** in `SKILL.md` Step 5. The skill picks launcher dimensions from the resolved device name (case-insensitive): tablet (`iPad`, `Galaxy Tab`, `Pixel Tablet`, `Surface`, `MatePad`, names containing `Tab` or `Pad`) → `780 × 920`; fold (`Fold`, `Z Fold`, `Pixel Fold`) → `880 × 920`; phone (default) → `540 × 920`. Landscape orientation swaps width and height. All three presets share the same `920 px` height so the chromeless window's vertical footprint stays consistent across device classes.
- Falls back gracefully when chromeless isn't appropriate: Chrome / Chromium not installed (launcher exits `2`), the URL branch is the manual-interaction form (no `?view=device-only`), or the user has explicitly saved Safari / Firefox / Default browser as their preference. In those cases the existing browser-preference open path is used (`open -a "Safari" <url>`, `xdg-open <url>`, etc.); Chrome is never spawned and no macOS Automation prompt appears.
- URL validation rejects bash-quoting-breaking metacharacters (`"`, backtick, `$`, `\`) and non-`http(s)` schemes at every launcher entry point. URL-syntax characters (`&`, `?`, `=`, `;`, `|`, `<`, `>`, single-quote) are accepted — Kobiton portal URLs need `&` between query params.
- `SKILL.md` Step 5 restructured: launcher invocation is the first action on the device-only branch when the gate allows; the existing "Which browser should I open the session in?" prompt + `open` / `xdg-open` table become the fallback path.
- `allowed-tools` extended to include `Bash(bash:*)`, `Bash(pwsh:*)`, `Bash(osascript:*)` (needed by the launcher shim invocations).
- 32 new vitest cases in `skills/run-automation-suite/scripts/chromeless-launcher.test.js` covering arg parsing, exit-code sentinels (`64` usage / `2` Chrome-absent fallback / `0` fail-open), URL metacharacter rejection, and positive-path acceptance for real `?id=…&view=device-only` URLs.
- `scripts/sync-version.js`: drive-by fix — the CHANGELOG regex `(\d+\.\d+\.\d+)\b` over-matched `1.4.0` against pre-release versions like `1.4.0-dev.0`. Now accepts SemVer 2.0 pre-release suffixes. Regression test added.

## 1.3.0 - 2026-05-28

- Multi-CLI support extended: install on [Cursor CLI](https://cursor.com/cli) in addition to the existing four hosts (Claude Code, GitHub Copilot CLI, Gemini CLI, Codex CLI)
- New `.cursor-plugin/plugin.json` + `.cursor-plugin/marketplace.json` following the [cursor/plugins](https://github.com/cursor/plugins) convention — install in-session with `/plugin marketplace add https://github.com/kobiton/automate`, or drop just `.cursor/mcp.json` into any project for an MCP-only setup
- New `.cursor/hooks/hooks.json` declaring a `sessionStart` event for the `~/.kobiton/bin/kobiton` CLI wrapper; Cursor CLI does not currently run plugin sessionStart hooks, so run `/automate:setup` once after install to create the wrapper (same as Copilot and Gemini)
- MCP requests originating from Cursor carry `X-AI-Tool-Name: Cursor` for adoption analytics (KOB-52724)
- Documented install paths for additional generic MCP clients — ChatGPT (Apps SDK) and Continue / Cline / other Streamable-HTTP clients — in a new "Other MCP Clients" README subsection (configs derived from each client's published documentation; not yet end-to-end validated)
- `/automate:setup` and `/automate:doctor` are now wired for Cursor CLI too — the `.cursor-plugin/plugin.json` `commands` field points at the shared `commands/*.md` set, which Cursor reads in the same Markdown + YAML-frontmatter format


## 1.2.2 - 2026-05-25

- Added 14 Test Case Management MCP tool schemas in `tools/test-management.yaml` — test cases (`saveTestCase`, `listTestCases`, `getTestCase`, `updateTestCase`, `deleteTestCase`), test runs (`createTestRun`, `listTestRuns`, `getTestRun`, `terminateTestRun`), and test suites (`listTestSuites`, `getTestSuite`, `createTestSuite`, `updateTestSuite`, `deleteTestSuite`)
- Updated bundled `kobiton` CLI binary in `run-interactive-test` skill to the latest version
- Expanded `run-interactive-test` adb-shell documentation for AI agents: quoting rules (local vs device shell parsing), platform guard (Android only), 22-row intent-to-command cookbook, big-output redirect pattern (to avoid 25k-token MCP overflow), long-running command guidance, and response parsing gotchas in `references/response-shapes.md` — notably that `adb` returns exit code 0 even when the inner command fails

## 1.2.1 - 2026-05-20

- `run-automation-suite` skill now defaults to the **device-only view URL** (`?view=device-only`) when surfacing the live session link, hiding the surrounding Kobiton UI for a cleaner watch-the-test experience. Falls back to the default-view URL only when the user explicitly asks to interact with the device.
- Portal URL mapping in the skill is now derivation-based (`api*.kobiton.com` → `portal*.kobiton.com`) instead of a hard-coded per-env table.


## 1.2.0 - 2026-05-18

- Multi-CLI support: install on GitHub Copilot CLI, Gemini CLI, and Codex CLI in addition to Claude Code
- New `run-interactive-test` skill — natural-language WebDriver/device/file commands powered by the bundled `kobiton` CLI wrapper (macOS Apple Silicon binary included)
- New `/automate:setup` command — bootstraps `~/.kobiton/.credentials` from the authenticated MCP session, no manual file editing
- New `/automate:doctor` command — read-only health checks for CLI install, credentials file, active profile, and required fields
- New `getCredential` MCP tool — backs `/automate:setup`; returns the OAuth user's username, API key (existing or freshly generated), and portal URL
- Session attribution: Appium sessions started via `run-automation-suite` now emit `kobiton:aiToolName`; MCP requests from Claude Code, Codex CLI, and Gemini CLI carry `X-AI-Tool-Name` (set to the originating tool) for adoption analytics (KOB-52724)
- Governance: CodeQL weekly scans + per-PR analysis, security issue routing template


## 1.1.0 - 2026-05-10

- Plugin now sends an `X-AI-Tool-Name: Claude` header on every MCP request so Kobiton can attribute sessions to Claude Code in adoption analytics. Set automatically in all three shipped configs (OAuth, API-key, dev-local) — no end-user action required (KOB-52724)


## 1.0.2 - 2026-04-02

- Improved the accuracy of fetching Appium capabilities supported by Kobiton
- Implemented a reliable method for correlating active sessions with their corresponding device IDs


## 1.0.1 - 2026-04-01

- Added a user confirmation prompt when selecting an app version for testing
- Enabled Claude to open active test sessions for live screen previews


## 1.0.0 - 2026-03-31

- Initial release with 12 MCP tools and 1 skill
- Authentication: OAuth 2.1 with automatic browser login (primary), API key auth for CI/headless (alternative)
- Device management: list, status, reserve, terminate reservation
- Session management: list, details, artifacts, terminate
- App management: list, details, upload to store, confirm to upload
- Skills: run-automation-suite to parse capabilities from local Appium scripts and execute them directly (supports Node.js, Python, .NET, Java)
