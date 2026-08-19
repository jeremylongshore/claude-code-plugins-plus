---
name: run-interactive-session
description: >-
  Perform interactive testing on Kobiton devices using natural language.
  Translates user intents into CLI commands - WebDriver actions (find
  elements, type, click, swipe), device operations (adb shell, screen
  capture, port forwarding), file management (push/pull), app
  management, and test execution. Use when the user wants to interact
  with a mobile device on Kobiton, run exploratory tests, inspect device
  state, manage files on a device, or execute test sessions - even if
  they don't say "interactive test" explicitly. Trigger with "interact
  with kobiton device", "explore on kobiton", or "tap/swipe on device".
allowed-tools: >-
  Read, Edit,
  Bash(~/.kobiton/bin/kobiton:*),
  Bash(mkdir:*), Bash(date:*), Bash(base64:*), Bash(echo:*),
  Bash(cat:*), Bash(grep:*), Bash(head:*), Bash(tail:*),
  Bash(jq:*), Bash(xmllint:*),
  Bash(timeout:*), Bash(perl:*),
  Bash(open:*), Bash(xdg-open:*)
version: 1.0.0
author: Kobiton Inc.
license: MIT
compatibility: >-
  macOS (Apple Silicon), Linux (x64), and Windows (x64, under Git
  Bash). The Kobiton CLI is downloaded on install: the plugin pins a
  build version (skills/run-interactive-session/CLI_VERSION) and the
  install script fetches the matching platform build from
  public.kobiton.download, sha256-verified and cached under
  ~/.kobiton/cli/. Intel Macs are not supported (no macos-x64 build
  is published) - there, use run-automation-suite or
  drive-automation-session, or the Kobiton MCP tools directly.
  Requires local file access for the cached binary and
  ~/.kobiton/.credentials. Run /automate:setup once before first use
  to install the CLI wrapper and write credentials.
tags: [mobile, testing, interactive, webdriver, devices, kobiton]
---

# Run Interactive Test

## Overview

Drive a Kobiton device interactively from natural-language intent. Given a request like "find the Login button and tap it" or "pull the latest log file from this Pixel", this skill creates (or resumes) a session, translates the intent into the right CLI command - WebDriver action, `adb shell`, file transfer, app launch, test run - captures the response, saves artifacts (screenshots, page source) under the workspace, and reports back in plain language.

Use this skill whenever the user wants to interact with a mobile device on Kobiton, run exploratory tests, inspect device state, manage files on a device, or execute test sessions - even if they don't say "interactive test" explicitly.

## Prerequisites

**Runs on macOS (Apple Silicon), Linux (x64), and Windows (x64 under Git Bash), and needs a local filesystem** — it executes a locally cached CLI binary and reads `~/.kobiton/.credentials`. On Intel Macs or other unsupported architectures, or anywhere a local filesystem isn't available, don't invoke this skill: route to `run-automation-suite` (user already has a test script) or `drive-automation-session` (describe the flow instead), both cross-platform. Check this *before* reserving a device, so a doomed run doesn't burn device minutes. See the Skill compatibility matrix in `CLAUDE.md`.

Before invoking this skill, ensure:

- **Kobiton CLI wrapper** - `~/.kobiton/bin/kobiton` (a symlink to this plugin's `run.sh` wrapper on macOS/Linux, a bash exec-shim on Windows) must exist and resolve to an executable. Claude Code and Codex CLI both recreate it automatically via a bundled SessionStart hook; on Codex, the user trusts the hook once via `/hooks` after install. `/automate:setup` re-installs the wrapper on demand on any host. GitHub Copilot CLI and Gemini CLI load `/automate:setup` (Copilot via Claude-format `.md`, Gemini via bundled TOML at `commands/automate/setup.toml`) but have no SessionStart hook - run `/automate:setup` once after install. The CLI binary itself is **downloaded, not bundled**: the install script fetches the build pinned in `CLI_VERSION` (sha256-verified) into `~/.kobiton/cli/` on first run. `run.sh` reports a missing binary or missing credentials with the right remedy, so surface its error rather than pre-flighting your own checks.
- **Credentials file** - `~/.kobiton/.credentials` must contain a valid INI-formatted profile with `KOBITON_USER`, `KOBITON_API_KEY`, and `KOBITON_PORTAL`. Created by `/automate:setup`. The active profile is `$KOBITON_PROFILE` if set, otherwise `default`.
- **Kobiton MCP connection** - useful for `listDevices` / `getDeviceStatus` calls when picking a device. Default `api.kobiton.com/mcp`; check `.mcp.json` for the configured endpoint.
- **Kobiton account** - credentials with device access for the target platform (Android / iOS) and remaining session quota.

If a command fails with a credentials error or missing-binary error, direct the user to run `/automate:doctor` for diagnostics, then `/automate:setup` to repair.

## How It Works

All CLI calls go through a single wrapper at `~/.kobiton/bin/kobiton` that automatically handles:

- **CLI binary resolution** - resolves the pinned CLI build from the version cache at `~/.kobiton/cli/<version>/` (falling back to the newest cached build with a drift warning).
- **Portal URL** - from `KOBITON_PORTAL` in credentials, or derived from `.mcp.json` as fallback.
- **Credentials** - loaded from `~/.kobiton/.credentials` using AWS-style profiles (`$KOBITON_PROFILE`, default `default`).
- **Session token** - loaded by the CLI from `~/.kobiton/.session` once a session exists.

Every command is self-contained - no env vars to manage between calls:

    ~/.kobiton/bin/kobiton <cli-args>

`$KOBITON_BIN` is used as shorthand throughout this document. In every Bash command, substitute it with the literal path `~/.kobiton/bin/kobiton` - the variable does not persist between Bash calls.

## Conventions

### Argument order

Global flags must come **before** the subcommand:

    $KOBITON_BIN [global-flags] <subcommand> [subcommand-flags]

Example: `$KOBITON_BIN -u <udid> session create` (NOT `$KOBITON_BIN session -u <udid> create`).

### Help-first discovery

The CLI has built-in help at every level. **Always check `--help` before running a command you haven't used before or when unsure about arguments:**

    $KOBITON_BIN --help                    # list all top-level commands
    $KOBITON_BIN session --help            # session create, ping, end
    $KOBITON_BIN session create --help     # show create flags and usage
    $KOBITON_BIN wd --help                 # webdriver post/get commands
    $KOBITON_BIN device --help             # list, adb-shell, forward, ps, screen
    $KOBITON_BIN device adb-shell --help   # run adb shell commands on device
    $KOBITON_BIN file --help               # list, push, pull files on device
    $KOBITON_BIN file push --help          # push local file to device
    $KOBITON_BIN test --help               # test run with built-in framework
    $KOBITON_BIN test run --help           # show test run flags and usage
    $KOBITON_BIN app --help                # app management commands
    $KOBITON_BIN app run --help            # show app run flags and usage

**Rule:** if a command fails with "unexpected argument" or "unknown flag", run `--help` on that command to discover the correct syntax before retrying. Do not guess - the help output is authoritative.

### Artifacts storage

All session artifacts (screenshots, page source) **must** be saved under the current workspace at:

    .kobiton/sessions/<session-id>/

This keeps artifacts organized per session, easy to review, and version-controllable. Never save artifacts to `/tmp/` or other locations outside the workspace.

**Workspace vs home.** This `.kobiton/` is **workspace-relative** (your CWD when running the skill) - do not confuse with `~/.kobiton/` in the user's home, which holds the CLI symlink, credentials, and session JWT (managed by `/automate:setup`). Workspace `.kobiton/` only contains per-session artifacts the skill creates.

Before writing the first artifact in a session, ensure the directory exists with `mkdir -p .kobiton/sessions/<session-id>`. It's idempotent, so include it defensively whenever you're about to write - especially when resuming an existing session, where Instructions § 2 may have been skipped.

## Instructions

### 1. Pick a device

Ask the user which device or platform to target. If they haven't specified one, call the MCP tool `listDevices` to surface available options, optionally filtered by platform / OS version.

If the user already has a specific device in mind, confirm its availability with `getDeviceStatus` before proceeding.

Capture both the **UDID** (used for session creation) and the device **id** (the separate numeric ID used to build portal launch URLs).

### 2. Create or resume a session

If there is no active session yet, create one:

    $KOBITON_BIN -u <udid> session create

The output contains a line like `kobitonSessionId: 12345`. Capture it:

1. Parse the session ID from the output.
2. Create the artifacts directory: `mkdir -p .kobiton/sessions/<session-id>`.
3. Store the session ID for use in screenshot and page source commands.

The JWT is saved automatically to `~/.kobiton/.session`. All subsequent commands use it - no flags needed.

If a session may already exist (e.g., the user is continuing earlier work), check first:

    $KOBITON_BIN session ping

Exit code 0 -> session alive, reuse it. Non-zero -> expired; create a fresh one.

### 3. Interact with the device

Translate the user's natural-language intent into one or more CLI commands using the [Command Reference](#command-reference) below.

For each command:

1. Run it via Bash using the literal path `~/.kobiton/bin/kobiton`.
2. Parse the response (JSON envelope, plain text, or exit code) to extract values - see [Output § Per-command response shapes](#per-command-response-shapes) for the summary rules and [`references/response-shapes.md`](references/response-shapes.md) for the full per-command table.
3. Report results in plain language to the user.

**Chaining.** Multi-step intents require chaining the output of one command into the next. Example - "find the Name field and type Hello":

1. Find the element:

       $KOBITON_BIN wd post element '{"using":"id","value":"com.app:id/etName"}'

   The response is JSON; extract the element ID from the `value` field.

2. Type into it (substituting the captured element ID):

       $KOBITON_BIN wd post element/<ELEMENT_ID>/value '{"text":"Hello"}'

Always extract the element ID from the response before using it in subsequent commands. Element IDs **do not survive page transitions** - re-find on each new screen instead of caching.

### 4. Capture artifacts

Ensure the artifacts directory exists first (idempotent, safe to repeat):

    mkdir -p .kobiton/sessions/<session-id>

**Screenshot.** The CLI emits the base64-encoded PNG directly on stdout; decode and save in one pipe:

    $KOBITON_BIN wd get screenshot \
      | base64 -d \
      > .kobiton/sessions/<session-id>/screenshot-$(date +%s).png

Then use the `Read` tool on the saved file to display it inline, and report the file path to the user.

**Page source.** The CLI emits raw XML (Android UIAutomator2) or hierarchy markup (iOS XCUITest) on stdout:

    $KOBITON_BIN wd get source > .kobiton/sessions/<session-id>/source-$(date +%s).xml

Read the saved file for element inspection, or use `grep` / `xmllint` to extract specific nodes (see [Example 3](#example-3-inspection-only---dump-page-source-list-clickable-elements-android)).

### 5. End the session

When the user is done:

    $KOBITON_BIN session end

This terminates the Kobiton-side session and frees the device. The local artifacts directory at `.kobiton/sessions/<session-id>/` is preserved for later review and version control.

## Command Reference

### WebDriver commands

| Intent | Command |
|--------|---------|
| Find element by ID | `$KOBITON_BIN wd post element '{"using":"id","value":"<id>"}'` |
| Find element by XPath | `$KOBITON_BIN wd post element '{"using":"xpath","value":"<xpath>"}'` |
| Find element by class | `$KOBITON_BIN wd post element '{"using":"class name","value":"<class>"}'` |
| Click element | `$KOBITON_BIN wd post element/<elementId>/click '{}'` |
| Type text | `$KOBITON_BIN wd post element/<elementId>/value '{"text":"<text>"}'` |
| Clear text | `$KOBITON_BIN wd post element/<elementId>/clear '{}'` |
| Get element text | `$KOBITON_BIN wd get element/<elementId>/text` |
| Get page source | `$KOBITON_BIN wd get source` |
| Get orientation | `$KOBITON_BIN wd get orientation` |
| Set orientation | `$KOBITON_BIN wd post orientation '{"orientation":"LANDSCAPE"}'` |
| Get window size | `$KOBITON_BIN wd get window/rect` |
| Take screenshot | `$KOBITON_BIN wd get screenshot` |
| Accept alert | `$KOBITON_BIN wd post execute '{"script":"kobiton:alerthandler","args":{"auto":"accept"}}'` |
| Dismiss alert | `$KOBITON_BIN wd post execute '{"script":"kobiton:alerthandler","args":{"auto":"dismiss"}}'` |
| Go to URL | `$KOBITON_BIN wd post url '{"url":"<url>"}'` |
| Get current URL | `$KOBITON_BIN wd get url` |
| Swipe | `$KOBITON_BIN wd post actions '{"actions":[{"type":"pointer","id":"finger1","parameters":{"pointerType":"touch"},"actions":[{"type":"pointerMove","duration":0,"x":<startX>,"y":<startY>},{"type":"pointerDown","button":0},{"type":"pointerMove","duration":500,"x":<endX>,"y":<endY>},{"type":"pointerUp","button":0}]}]}'` |
| Tap at coordinates | `$KOBITON_BIN wd post actions '{"actions":[{"type":"pointer","id":"finger1","parameters":{"pointerType":"touch"},"actions":[{"type":"pointerMove","duration":0,"x":<x>,"y":<y>},{"type":"pointerDown","button":0},{"type":"pointerUp","button":0}]}]}'` |
| Press back (Android) | `$KOBITON_BIN wd post execute '{"script":"mobile: pressKey","args":{"keycode":4}}'` |
| Press home (Android) | `$KOBITON_BIN wd post execute '{"script":"mobile: pressKey","args":{"keycode":3}}'` |
| Ping session | `$KOBITON_BIN session ping` |

### adb-shell commands (Android only)

`device adb-shell` forwards everything after it to `adb shell <...>` on the device. Three failure modes account for most AI-agent mistakes - read these before composing a command.

**Restricted sessions (public cloud and trial devices).** On Kobiton public cloud devices and for trial users, every invocation is checked against a deny-by-default whitelist before it reaches the device. Dedicated devices (private cloud / on-premise) are unrestricted; everything in this block applies only to restricted sessions. The interactive shell is unavailable on restricted sessions - every invocation must name a command.

Rejected on restricted sessions:

- Any command not in the whitelist below, and command lines longer than 1024 characters.
- Control characters, and these shell metacharacters anywhere in the input: `` & ; | $ ` ( ) > < \ " ' * ? ~ { } # ! `` - so no pipes, redirection, command or variable substitution, backgrounding, globbing, or **quoting**. Arguments may not contain whitespace.

Whitelisted commands, by category:

| Category | Commands |
|----------|----------|
| Device information | `getprop`, `dumpsys`, `df`, `free` |
| Diagnostics | `logcat`, `ps`, `top`, `netstat`, `printenv`, `uptime`, `id`, `whoami`, `date` (flags only) |
| Applications | `pm`, `am`, `monkey` (`pm install` may name an APK inside the allowed directories below) |
| Text tools | `grep`, `egrep`, `fgrep`, `head`, `tail`, `wc`, `sort`, `uniq`, `nl`, `cut` - they read files, not stdin (pipes are rejected), and pattern arguments are limited to letters, digits, dot, underscore, hyphen |
| File inspection | `ls`, `cat`, `stat`, `du`, `md5sum`, `sha1sum` |
| Screen and input | `screencap`, `input` |
| Settings | `settings` - one key only, see below |

File-path arguments must stay inside `/sdcard/Download/`, `/sdcard/Documents/`, or `/data/local/tmp/`, plus the individually allowed read-only file `/proc/version`; paths containing `..` are rejected. To list a directory outside that allowlist, use `$KOBITON_BIN file list <path>` instead of `adb-shell ls`. The same directories bound `file push` / `file pull`.

Settings: only `settings get secure enabled_accessibility_services` and `settings put secure enabled_accessibility_services <value>` are permitted. Every other settings namespace, key, and subcommand (including `list` and `delete`) is rejected.

A rejected invocation prints one of these messages on stdout and - gotcha - **exits 0**, so check the first line of output rather than `$?`:

- `Input contains a forbidden character: '<c>'.`
- `Command is not on the whitelist: '<cmd>'.`
- `Argument is not permitted for '<cmd>': '<arg>'.`
- `Only get/put of secure enabled_accessibility_services is permitted for 'settings'.` (the settings rule has its own message)

The whitelist evolves with CLI releases; `$KOBITON_BIN device adb-shell --help` carries the full current policy - trust it over this snapshot.

**Quoting rules.** The local shell parses pipes, redirects, globs, and variable expansion *before* the wrapper sees them. Anything you wrap in quotes survives to the device's shell; anything outside is interpreted on your laptop.

- **Plain command, no shell metacharacters** - pass args separately (works on restricted and unrestricted sessions alike; `/sdcard/Download/` is inside the restricted path allowlist):

      $KOBITON_BIN device adb-shell ls -la /sdcard/Download/
      $KOBITON_BIN device adb-shell getprop ro.build.version.release

- **Pipes, redirects, globs, `&&`, `$VAR`, or quotes inside the command** - **unrestricted (dedicated) devices only**: wrap the entire remote command in one quoted string so it runs on the device's shell, not your local shell:

      $KOBITON_BIN device adb-shell "dumpsys window | grep mCurrentFocus"
      $KOBITON_BIN device adb-shell 'pm list packages -3 | wc -l'
      $KOBITON_BIN device adb-shell "logcat -d -t 200 > /sdcard/log.txt"

  On a **restricted session** this form is rejected outright - the quotes and the metacharacters inside them are all forbidden characters, so there is no on-device composition form at all. Compose locally instead (next bullet).

- **Restricted sessions: compose locally.** Run the bare whitelisted command, bound its output, redirect *locally* into the session artifact directory, then filter the file locally:

      $KOBITON_BIN device adb-shell dumpsys window \
        > .kobiton/sessions/<session-id>/window-$(date +%s).txt
      grep mCurrentFocus .kobiton/sessions/<session-id>/window-*.txt

  On unrestricted devices prefer the quoted on-device form - filtering locally on the full output is slower and can overflow the 25k-token MCP limit if it isn't routed through an artifact file. On restricted sessions the local route is the only one: always bound the command (`-d -t N`, `-n 1`) and go through an artifact file, never paste raw output to chat.

**Platform guard.** `adb` is Android-only. If the active session targets iOS, do **not** call `device adb-shell`. Refuse and reach for the WebDriver equivalent (`wd post execute '{"script":"mobile: ..."}'`) or a different inspection path.

**Device logs on iOS.** `logcat` is Android-only; the cross-platform log path is `$KOBITON_BIN device log`, which **streams until killed** — always bound it and expect the bound's exit code, which means success here, not failure:

    timeout 45 $KOBITON_BIN device log > .kobiton/sessions/<session-id>/device-log.txt   # exit 124 = bound fired (coreutils)
    # stock macOS has no `timeout` - use the perl-alarm equivalent (exit 142 = SIGALRM, same meaning):
    perl -e 'alarm shift; exec @ARGV' 45 ~/.kobiton/bin/kobiton device log > .kobiton/sessions/<session-id>/device-log.txt

The **Restricted** column says what changes on a restricted session; `ok` means the command runs as written.

| Intent | Command | Restricted |
|--------|---------|------------|
| Get OS / build property | `$KOBITON_BIN device adb-shell getprop <key>` | ok |
| Get screen resolution | `$KOBITON_BIN device adb-shell wm size` | rejected (`wm` not whitelisted) - use `$KOBITON_BIN wd get window/rect` instead |
| Get foreground app/activity | `$KOBITON_BIN device adb-shell "dumpsys window \| grep mCurrentFocus"` | quoted pipe rejected - run bare `dumpsys window`, filter locally |
| Open a URL (Android Chrome) | UI-driven: launch Chrome via `monkey -p com.android.chrome -c android.intent.category.LAUNCHER 1`, then `wd post element '{"using":"id","value":"com.android.chrome:id/url_bar"}'` → `wd post element/<id>/click '{}'` → `wd post element/<id>/value '{"text":"<url>"}'` → `input keyevent 66` | this recipe IS the restricted path - a URL argument to `am start` is rejected (`Argument is not permitted for 'am'`); on unrestricted devices `am start -a android.intent.action.VIEW -d <url>` also works |
| Open a URL (iOS Safari) | `wd post execute '{"script":"mobile: launchApp","args":[{"bundleId":"com.apple.mobilesafari"}]}'` → `wd post element '{"using":"accessibility id","value":"TabBarItemTitle"}'` → `wd post element/<id>/click '{}'` → `wd post element/<id>/value '{"text":"<url>\n"}'` — the trailing `\n` submits (iOS has no keyevent); `click` requires a body, `'{}'` works | n/a - WebDriver path, not adb-shell |
| List running processes | `$KOBITON_BIN device adb-shell ps -A` | ok |
| List user-installed packages | `$KOBITON_BIN device adb-shell pm list packages -3` | ok |
| Find APK path of a package | `$KOBITON_BIN device adb-shell pm path <pkg>` | ok |
| Launch app by package | `$KOBITON_BIN device adb-shell monkey -p <pkg> -c android.intent.category.LAUNCHER 1` | ok |
| Force-stop app | `$KOBITON_BIN device adb-shell am force-stop <pkg>` | ok |
| Clear app data | `$KOBITON_BIN device adb-shell pm clear <pkg>` | ok |
| Battery level + charging state | `$KOBITON_BIN device adb-shell dumpsys battery` | ok |
| Memory snapshot for a package | `$KOBITON_BIN device adb-shell dumpsys meminfo <pkg>` | ok |
| Storage free on /sdcard | `$KOBITON_BIN device adb-shell df -h /sdcard` | ok |
| Press hardware key (home=3, back=4, power=26) | `$KOBITON_BIN device adb-shell input keyevent <code>` | ok |
| Type text into focused field | `$KOBITON_BIN device adb-shell input text "<text>"` | quotes/whitespace rejected - a single token works (`%s` encodes a space); for real text entry prefer `wd post element/<id>/value` |
| Tap at coordinates | `$KOBITON_BIN device adb-shell input tap <x> <y>` | ok |
| Swipe (ms = duration) | `$KOBITON_BIN device adb-shell input swipe <x1> <y1> <x2> <y2> <ms>` | ok |
| Read recent logs (Android only) | `$KOBITON_BIN device adb-shell logcat -d -t 500 > <local-file>` — on iOS use `device log` (see "Device logs on iOS" above) | ok (no quotes needed - the args carry no metacharacters; the redirect is local) |
| Screenshot via shell | `$KOBITON_BIN device adb-shell screencap -p /sdcard/Download/shot.png` | ok - retrieve with `file pull` (or use `device screen` directly) |
| Read system setting | `$KOBITON_BIN device adb-shell settings get system <key>` | rejected - only the `secure enabled_accessibility_services` key is readable/writable |
| Write system setting | `$KOBITON_BIN device adb-shell settings put system <key> <value>` | rejected - same single-key rule |
| Read/write enabled accessibility services | `$KOBITON_BIN device adb-shell settings get secure enabled_accessibility_services` / `... put secure enabled_accessibility_services <value>` | ok - the one permitted settings key (`<value>` is colon-separated components, or `null` to clear) |
| Read file content | `$KOBITON_BIN device adb-shell cat <path>` | path allowlist applies (allowed dirs + `/proc/version`) |
| List directory | `$KOBITON_BIN device adb-shell ls -la <path>` | path allowlist applies - outside it, use `$KOBITON_BIN file list <path>` |
| Current IME | `$KOBITON_BIN device adb-shell "dumpsys input_method \| grep mCurId"` | quoted pipe rejected - run bare `dumpsys input_method`, filter locally |

**Big-output commands.** `dumpsys`, `logcat`, `pm list -f`, and full process dumps can blow past the 25k-token MCP limit. For these, redirect to an artifact file first, then read/grep only what you need (the redirect is your *local* shell's, so this exact pattern also works on restricted sessions - it is the same local-composition idiom from the quoting rules):

    $KOBITON_BIN device adb-shell logcat -d -t 1000 \
      > .kobiton/sessions/<session-id>/logcat-$(date +%s).txt
    grep -E 'FATAL|AndroidRuntime' \
      .kobiton/sessions/<session-id>/logcat-*.txt | head -20

Never paste full dumpsys/logcat output to chat - surface a summary + the file path.

**Long-running commands.** Streaming commands like `logcat` (no `-d`), `device log`, `tcpdump`, or `top` (no `-n 1`) run forever. Either bound them (`-d -t N`, `-c N`, `-n 1`, or the `timeout`/perl-alarm wrapper for `device log`) or launch with `run_in_background: true` and kill explicitly.

**adb-shell vs WebDriver overlap.** Both can press keys, type, and tap. Tie-breakers:

- If the target is a known element ID -> WebDriver (`wd post element/<id>/click`, `.../value`).
- If the target is a hardware key, a blind coordinate tap, or a system-level action -> `adb shell input` / `am` / `pm`.

**Web content visibility differs by platform.** iOS exposes web page content to the automation hierarchy — `wd get source` on a Safari page includes the page's text, links, and buttons, so in-page elements (cookie dialogs, page buttons) are findable and clickable with native locators. Android's UiAutomator does **not** see inside a WebView: the same dialog that is clickable on iOS is invisible on Android — fall back to coordinate taps or handle it outside the WebView. Locator tip for iOS web content: when an `accessibility id` lookup misses (or an XPath by `@label` does), check `wd get source` for the element's actual `XCUIElementType` — web controls often surface as `Link` or `StaticText` rather than `Button`, and the type in your XPath must match.
- For inspection (foreground app, processes, build props, settings) -> adb shell only; there is no WebDriver equivalent.

Default: prefer adb-shell for system-level work, WebDriver for UI element-level work.

### Beyond WebDriver

These commands require an active session. Run `$KOBITON_BIN <command> --help` to discover the exact flags before using them - argument order and required flags vary.

| Domain | Command | What it does |
|--------|---------|-------------|
| Device | `$KOBITON_BIN device screen` | Capture device screen as jpg |
| Device | `$KOBITON_BIN device forward <local> <remote>` | Forward local port to device. Runs in the foreground until interrupted and holds the local port for the lifetime of the forward - launch with `run_in_background: true` and kill explicitly, like the long-running adb-shell commands above |
| Device | `$KOBITON_BIN device ps` | List processes on device |
| File | `$KOBITON_BIN file list <path>` | List files on device |
| File | `$KOBITON_BIN file push <local> <remote>` | Push file to device |
| File | `$KOBITON_BIN file pull <remote> <local>` | Pull file from device |
| App | `$KOBITON_BIN app run <app-id>` | Launch an app |
| Test | `$KOBITON_BIN test run` | Execute a test session |

## Output

The skill produces two kinds of output: **per-command responses** that Claude parses inline during the session, and **persistent session artifacts** that accumulate on disk and remain after the session ends.

### Per-command response shapes

The common parsing patterns:

- **Most WebDriver responses** are JSON envelopes `{"value": <result>}`. Null/empty `.value` means success; a non-null `.value` is the result (string, rect object, script return).
- **Find element** (`wd post element`) hides the element ID under `.value`, but the exact path varies (`.value.ELEMENT`, `.value["element-6066-11e4-a52e-4f735466cecf"]`, or a bare string). Use a tolerant extractor like `jq -r '.value.ELEMENT // .value["element-6066-11e4-a52e-4f735466cecf"] // .value'`.
- **Screenshot and page source** (`wd get screenshot`, `wd get source`) are special-cased — the CLI unwraps the WebDriver JSON envelope and emits raw base64 PNG / raw XML on stdout. Pipe straight into a file.
- **Session commands** mix text + exit code. `session create` prints a `kobitonSessionId: <id>` line; `session ping` signals liveness through exit code (0 = alive).
- **`device` / `file` / `app` / `test`** emit plain text and signal failure through exit code. Long-running ones (`test run`, future streaming commands) should be launched with `run_in_background: true` and tailed.

For the full per-command table (response on stdout, exact parsing recipe per command), see [`references/response-shapes.md`](references/response-shapes.md). Consult it when the response shape isn't obvious from these summary rules.

### Persistent session artifacts

After (and during) a session, the workspace and home directory contain:

- **`.kobiton/sessions/<session-id>/screenshot-<unix-ts>.png`** - every screenshot captured during the session, named by Unix timestamp so they sort chronologically.
- **`.kobiton/sessions/<session-id>/source-<unix-ts>.xml`** - every page-source dump captured during the session.
- **`~/.kobiton/.session`** - the JWT for the most recently created session. The CLI uses this implicitly; treat it as opaque. It's overwritten by the next `session create`.

The Kobiton portal also hosts a live session view at:

    <portal-base>/sessions/<session-id>

Where `<portal-base>` is derived from the `KOBITON_PORTAL` value in the active profile by replacing the `api` host prefix with `portal` (e.g., `https://api.kobiton.com` -> `https://portal.kobiton.com`, `https://api-test.kobiton.com` -> `https://portal-test.kobiton.com`). Surface this URL when summarizing a finished session so the user can review the recorded video and logs.

## Error Handling

- **Unexpected argument / unknown flag**: run `$KOBITON_BIN <command> --help` to discover the correct syntax, then retry with the right arguments. Never guess flags.
- **`wd` errors exit 0**: WebDriver failures (e.g. no such element) return exit code 0 with a JSON error body - check the response JSON, not `$?`. A bounded `device log` exiting 124 (`timeout`) or 142 (perl-alarm) is the bound firing, not a failure.
- **Session create failed**: device may be offline, already reserved, or the UDID is wrong - verify availability with the `listDevices` MCP tool before retrying.
- **Session expired / auth error mid-flow**: `session ping` fails or a command returns auth error - offer to create a new session.
- **Element not found**: suggest getting page source first (`wd get source`) to inspect the UI hierarchy, then try a different locator strategy (xpath instead of id, or vice versa).
- **Stale element reference** after navigation: re-find the element on the new screen; element IDs do not survive page transitions.
- **Binary not found**: no cached CLI build exists under `~/.kobiton/cli/` - run `/automate:setup` (or re-open the session so the SessionStart hook downloads the pinned build). If the platform is unsupported (Intel Mac, non-x64), recommend `run-automation-suite` or the MCP tools instead.
- **Checksum mismatch during install**: the download was corrupted or tampered with - the installer discards it and keeps any existing cache. Retry `/automate:setup`; if it persists, report it on the plugin repo.
- **Version drift warning from `run.sh`**: the pinned build is not cached (usually pruned upstream) and a different cached build is being used - run `/automate:doctor` to see pinned vs installed vs latest, and update the automate plugin to its latest version (newer releases pin a validated build).
- **Missing credentials**: direct the user to run `/automate:doctor` first to see what's missing; if the credentials file is missing or incomplete, run `/automate:setup` to fetch and write fresh credentials.

## Examples

### Example 1: Open Settings -> Display -> screenshot (Android)

> "Take an Android Pixel device, open the Settings app, tap Display, then screenshot what's on screen."

The skill walks through:

1. Query MCP `listDevices` filtered to Android Pixel and pick the first AVAILABLE one - say UDID `9B211FFAZ0017F`, device id `4218`.
2. Create the session:

       ~/.kobiton/bin/kobiton -u 9B211FFAZ0017F session create

   Output includes `kobitonSessionId: 12345`. Capture it.

3. Prepare the workspace:

       mkdir -p .kobiton/sessions/12345

4. Press Home (in case another app was foregrounded), then launch Settings:

       ~/.kobiton/bin/kobiton wd post execute \
         '{"script":"mobile: pressKey","args":{"keycode":3}}'
       ~/.kobiton/bin/kobiton app run com.android.settings

5. Find the "Display" row by visible text:

       ~/.kobiton/bin/kobiton wd post element \
         '{"using":"xpath","value":"//*[@text=\"Display\"]"}'

   Response is a JSON envelope; extract the element ID from `.value` (see [`references/response-shapes.md`](references/response-shapes.md#webdriver-commands) for the exact extraction recipe).

6. Click it (substituting the captured `ELEMENT_ID`):

       ~/.kobiton/bin/kobiton wd post element/<ELEMENT_ID>/click '{}'

7. Capture the screenshot:

       ~/.kobiton/bin/kobiton wd get screenshot \
         | base64 -d \
         > .kobiton/sessions/12345/screenshot-$(date +%s).png

8. Read the file with the `Read` tool to display it inline, then report:

   > "Done. Screenshot saved to `.kobiton/sessions/12345/screenshot-1747612345.png`. Live session: `https://portal.kobiton.com/sessions/12345`."

9. If the user is finished, end the session:

       ~/.kobiton/bin/kobiton session end

### Example 2: Push a file, verify it landed, pull logs back (Android)

> "Push `./test-data.json` to `/sdcard/Download/` on the Pixel I'm already using, verify with `ls`, then pull the latest `logs.txt` from the device back into my project."

The skill walks through:

1. Check whether the existing session is still alive:

       ~/.kobiton/bin/kobiton session ping

   Exit 0 -> reuse it. Non-zero -> create a new one as in Example 1.

2. Push the file:

       ~/.kobiton/bin/kobiton file push ./test-data.json /sdcard/Download/test-data.json

3. Verify with adb shell:

       ~/.kobiton/bin/kobiton device adb-shell ls -la /sdcard/Download/test-data.json

   Expect a line like `-rw-rw---- 1 root sdcard_rw 1234 2026-05-19 09:30 /sdcard/Download/test-data.json`. Surface that line to the user.

4. Pull logs into the workspace:

       ~/.kobiton/bin/kobiton file pull /sdcard/logs.txt ./logs.txt

5. Read `./logs.txt` and report a one-line summary plus the file path. Do **not** echo the entire log to chat - it's likely large; instead `head -50` it or grep for keywords the user cares about.

### Example 3: Inspection-only - dump page source, list clickable elements (Android)

> "What clickable things are on screen right now? Save the page source so I can grep it later."

Assumes a session is already active (run `session ping` first; if expired, create a new one).

1. Dump the source - ensure the artifacts directory exists first:

       mkdir -p .kobiton/sessions/12345
       ~/.kobiton/bin/kobiton wd get source \
         > .kobiton/sessions/12345/source-$(date +%s).xml

2. Extract clickable nodes - quick `grep` pass:

       grep -oE 'clickable="true"[^/]{0,200}resource-id="[^"]+"' \
         .kobiton/sessions/12345/source-*.xml \
         | head -20

   For a structured pass, use `xmllint --xpath '//*[@clickable="true"]/@resource-id' .kobiton/sessions/12345/source-*.xml` (Android) or an equivalent XPath for the iOS hierarchy markup.

3. Report a deduplicated list of resource IDs (or fall back to `content-desc` / `text` for nodes that have no `resource-id`), and the path to the full XML for further inspection.

## Resources

- [Appium 2.x documentation](https://appium.io/docs/en/2.0/) - driver-specific docs (UiAutomator2 for Android, XCUITest for iOS) for the WebDriver endpoints called via `wd post` / `wd get`.
- [`kobiton/automate` plugin source](https://github.com/kobiton/automate) - issue tracker and source for the CLI wrapper (`skills/run-interactive-session/scripts/run.sh`), the install script, and the `CLI_VERSION` pin.
- [`run-automation-suite`](../run-automation-suite/SKILL.md) - sister skill for non-interactive runs of an existing Appium script. Use it when the user wants to execute a full test suite rather than drive the device step-by-step, or when the host platform has no published CLI build (e.g. Intel Macs).
- `/automate:setup` - install / refresh the CLI symlink and the credentials profile at `~/.kobiton/.credentials`.
- `/automate:doctor` - read-only health check for CLI symlink, credentials file, active profile, and required fields.
