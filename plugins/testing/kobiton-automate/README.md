# <img src="./assets/logo.svg" width="35" align="center" alt="Kobiton Logo" /> Kobiton Automate

[![Discord](https://img.shields.io/discord/1486036652685267055?color=7289DA&label=Discord&logo=discord&logoColor=white)](https://discord.gg/uHvBFDZVP)
[![Cloud](https://img.shields.io/badge/Cloud-☁️-blue)](https://kobiton.com)
[![Twitter Follow](https://img.shields.io/twitter/follow/KobitonMobile?style=social)](https://x.com/KobitonMobile)

Plugin for the [Kobiton](https://kobiton.com) mobile testing platform. Works with [Claude Code](https://docs.anthropic.com/en/docs/claude-code/overview), [GitHub Copilot CLI](https://docs.github.com/en/copilot/github-copilot-in-the-cli), [Gemini CLI](https://github.com/google-gemini/gemini-cli), [Codex CLI](https://github.com/openai/codex), and [Cursor](https://cursor.com) (CLI and IDE). Manage devices, upload apps, run automation sessions, and view test results directly from your AI coding assistant.

## Contents

- [Before You Begin](#before-you-begin)
- [Installation](#installation)
  - [Claude Code](#claude-code)
  - [GitHub Copilot CLI](#github-copilot-cli)
  - [Gemini CLI](#gemini-cli)
  - [Codex CLI](#codex-cli)
  - [Cursor CLI](#cursor-cli)
  - [Cursor IDE](#cursor-ide)
  - [Other MCP Clients](#other-mcp-clients)
  - [Claude Surface Compatibility](#claude-surface-compatibility)
- [Login](#login)
  - [API Key Authentication (Alternative)](#api-key-authentication-alternative)
- [Getting Started](#getting-started)
- [What You Can Do](#what-you-can-do)
- [Tools](#tools)
- [Skills](#skills)
- [Commands](#commands)
- [Running Automation Tests](#running-automation-tests)
- [Interactive Device Testing](#interactive-device-testing)
- [Examples](#examples)
- [Troubleshooting](#troubleshooting)
- [Privacy & Data](#privacy--data)
- [Development](#development)
- [License](#license)

## Before You Begin

Make sure you have:

- **A Kobiton account** - sign up at [kobiton.com](https://kobiton.com) if you don't have one
- **A supported AI assistant** - install [Claude Code](https://docs.anthropic.com/en/docs/claude-code/overview), [Copilot CLI](https://docs.github.com/en/copilot/github-copilot-in-the-cli), [Gemini CLI](https://github.com/google-gemini/gemini-cli), [Codex CLI](https://github.com/openai/codex), or [Cursor](https://cursor.com) (CLI or IDE)
- **A project directory** - your AI assistant must launch from a workspace, not from your home folder

## Installation

### Claude Code

Open your project and start a Claude Code session:

```bash
cd my-project
claude
```

Inside the session, add the Kobiton marketplace and install the plugin:

```
/plugin marketplace add kobiton/automate
/plugin install automate@kobiton
```

### GitHub Copilot CLI

Open your project and start a Copilot CLI session:

```bash
cd my-project
copilot
```

Inside the session, add the Kobiton marketplace and install the plugin:

```
/plugin marketplace add kobiton/automate
/plugin install automate@kobiton
```

### Gemini CLI

From your project directory, install the extension directly from GitHub:

```bash
cd my-project
gemini extensions install https://github.com/kobiton/automate
```

Then launch Gemini CLI:

```bash
gemini
```

The `kobiton` MCP server and bundled skills are auto-discovered. Confirm the extension is active with `/extensions list` and the MCP server with `/mcp`.

### Codex CLI

Add the Kobiton marketplace and install the plugin from the in-session browser. Codex opens a browser for Kobiton OAuth login on the first tool call.

```bash
codex plugin marketplace add kobiton/automate
codex
```

Inside Codex:

1. Type `/plugins` to open the plugin browser
2. Select the **kobiton** marketplace, then install the **automate** plugin
3. The system browser should open for Kobiton OAuth login. After sign-in, tokens are cached in the OS keychain (macOS Keychain / Linux Secret Service / Windows Credential Manager) with automatic refresh.
4. Run `/mcp` to confirm `kobiton` is **Connected**.

<details>
<summary><strong>Fallback: manual <code>config.toml</code> setup</strong></summary>

If you prefer not to use the marketplace, register the MCP server directly in `~/.codex/config.toml`:

```toml
[mcp_servers.kobiton]
url = "https://api.kobiton.com/mcp"
```

Then copy `AGENTS.md` into your workspace so Codex picks up the tool list and skill reference:

```bash
curl -sLO https://raw.githubusercontent.com/kobiton/automate/main/AGENTS.md
```

Launch `codex` and run `/mcp` to confirm. The OAuth flow still applies on the first tool call.
</details>

### Cursor CLI

Open your project and start a Cursor CLI session:

```bash
cd my-project
agent
```

Inside the session, add the Kobiton marketplace:

```
/plugin marketplace add github.com/kobiton/automate
```

Cursor parses the repository for a few seconds; when the **automate** entry appears, press <kbd>Enter</kbd> to install (pick the installation scope that suits you). The installation brings in the bundled skills, the `kobiton` MCP server, and the slash commands.

Then exit and relaunch `agent`. Cursor CLI currently loads plugin skills only at session start, so the skills won't appear until a fresh session.

Run `/mcp list`, select **Kobiton**, and choose **Login** to complete Kobiton OAuth in the browser.

Run `/setup` once to install the `~/.kobiton/bin/kobiton` CLI wrapper used by the `run-interactive-cli-session` skill. Cursor registers plugin commands without a namespace prefix, so the plugin's setup and doctor commands appear as `/setup` and `/doctor` — pick the one with the Kobiton description to tell them apart from Cursor's built-ins.

If you also use the Cursor IDE, install the plugin only once. Installs are shared between the CLI and the IDE (see the note in the next section).

### Cursor IDE

The Cursor desktop editor installs the plugin from its built-in plugin browser:

1. Open **Cursor Settings** > **Plugins** and paste `https://github.com/kobiton/automate` into the search box
2. Click the **automate** result, then **Add to Cursor**, then **Install**

To authenticate with the Kobiton MCP server: open **Tool & MCPs**, search for **kobiton**, click **Connect**, and complete the OAuth login in the browser.

> **Using both Cursor CLI and the Cursor IDE?** They share plugin installs: a plugin installed from the `agent` CLI shows up in the IDE, and vice versa. Install the plugin **once** in either one, installing it in both registers the skills, commands, and MCP server twice.

<details>
<summary><strong>Alternative: project-only MCP config (MCP server only, no skills or commands)</strong></summary>

For a lightweight per-project setup that registers just the `kobiton` MCP server, drop `.cursor/mcp.json` from this repo into your project's `.cursor/` directory:

```bash
cd my-project
mkdir -p .cursor
curl -sLO --output-dir .cursor https://raw.githubusercontent.com/kobiton/automate/main/.cursor/mcp.json
```

Works for both the Cursor IDE and the `agent` CLI. You won't get the bundled skills, the setup and doctor commands, or the CLI wrapper.
</details>

### Other MCP Clients

Kobiton's MCP server is built on the open [Model Context Protocol](https://modelcontextprotocol.io), so **any MCP-compatible client can connect to it**. Same endpoint (`https://api.kobiton.com/mcp`), same browser-based OAuth login as the clients above.

> **Good to know:** End-to-end tested only on Claude Code, Copilot CLI, Gemini CLI, Codex CLI, Cursor CLI, and the Cursor IDE; entries below are configs we expect to work but have not yet validated. Please [open an issue](https://github.com/kobiton/automate/issues/new?template=bug_report.md) if any do not work for your setup. We're happy to help.

#### ChatGPT (Apps SDK)

ChatGPT consumes MCP servers via an HTTPS endpoint registered in ChatGPT developer mode. Point ChatGPT at:

```
https://api.kobiton.com/mcp
```

The Apps SDK does not require a separate manifest file; tool descriptors, OAuth flow, and `_meta.ui` widget hints flow through the MCP protocol itself. Reference: [developers.openai.com/apps-sdk/build/mcp-server](https://developers.openai.com/apps-sdk/build/mcp-server).

#### Continue / Cline / other generic MCP clients

Register the `kobiton` server in your client's MCP config. Most clients read a JSON block like:

```json
{
  "mcpServers": {
    "kobiton": {
      "url": "https://api.kobiton.com/mcp"
    }
  }
}
```

Adjust to your client's specific format. The server URL and OAuth handshake are the same; if your client doesn't support OAuth, fall back to the API-key auth path (see [API Key Authentication](#api-key-authentication-alternative) below) - most clients accept custom `headers` blocks.

### Claude Surface Compatibility

Every Claude surface that supports MCP can call the Kobiton [tools](#tools). The guided [skills](#skills) install automatically only in Claude Code today; other surfaces need a manual skill upload.

| Claude surface | [Atomic MCP tools](#tools) | [Orchestrated skills](#skills) ¹ | How to connect |
|---|:--------------------------:|:--------------------------------:|---|
| **Claude Code** (CLI / IDE) |           ✅ Yes            |              ✅ Yes               | [Install the plugin](#claude-code) |
| **Claude Cowork** (macOS / Windows) |           ✅ Yes            |        ⚠️ Manual upload ²        | Add `https://api.kobiton.com/mcp` as a connector under **Connectors** |
| **claude.ai web · Claude Desktop · Claude mobile** |           ✅ Yes            |        ⚠️ Manual upload ²        | Add `https://api.kobiton.com/mcp` as a Custom Connector at [claude.ai](https://claude.ai); for mobile, configure it on the web first and it syncs to the app |

¹ `run-interactive-cli-session` also requires the bundled `kobiton` CLI binary (macOS Apple Silicon only) - see the [platform support note](#skills).
² This plugin is not listed in the [Claude directory](https://support.claude.com/en/articles/14328846-browse-skills-connectors-and-plugins-in-one-directory) yet, so these surfaces can't install it as a plugin. As a workaround, zip a skill folder from this repo (e.g. `skills/run-automation-suite/`) and upload it as a [custom skill](https://support.claude.com/en/articles/12512198-how-to-create-custom-skills).

## Login

The first time your AI assistant calls a Kobiton tool, a browser window opens for OAuth login. Sign in with your Kobiton credentials, tokens are then managed automatically by the assistant.

You can also trigger or inspect authentication explicitly:

- **Claude Code**: type `/mcp` and select **kobiton** to start the OAuth flow
- **GitHub Copilot CLI**: type `/mcp auth kobiton` to start the OAuth flow; use `/mcp` (or `/mcp show`) to inspect server status
- **Gemini CLI**: type `/mcp auth kobiton` to start the OAuth flow; use `/mcp` to inspect server status
- **Codex CLI**: browser opens automatically on the first MCP tool call (e.g. *"List my Kobiton devices"*) after plugin install. Tokens are cached in the OS keychain with automatic refresh. Use `/mcp` (or `/mcp verbose`) to inspect server status
- **Cursor CLI**: run `/mcp list`, select **kobiton**, and choose **Login** to start the OAuth flow; tokens are stored by Cursor in the OS keychain
- **Cursor IDE**: open **Cursor Settings** > **Tool & MCPs**, search for **kobiton**, and click **Connect** to start the OAuth flow

Behind the scenes, `.mcp.json` points to the Kobiton MCP server and authentication uses OAuth 2.1:

```json
{
  "mcpServers": {
    "kobiton": {
      "type": "http",
      "url": "https://api.kobiton.com/mcp"
    }
  }
}
```

After login, verify the plugin loaded by asking your assistant: *"List my Kobiton devices"*. If tools aren't recognized, see [Troubleshooting](#troubleshooting).

<a id="api-key-authentication-alternative"></a>
<details>
<summary><strong>API Key Authentication (Alternative)</strong></summary>

For CI/CD pipelines or headless environments that cannot open a browser, use API key auth instead:

1. Copy `.mcp.apikey-example.json` to `.mcp.json`
2. Generate an API key at **Kobiton Portal > Settings > API Keys**
3. Set the environment variable:

   ```bash
   # Add to ~/.zshrc, ~/.bashrc, or ~/.bash_profile
   export KOBITON_AUTH="Basic $(echo -n 'username:apikey' | base64)"
   ```

4. Reload your shell and restart your AI CLI.

> **Note:** OAuth and API key auth cannot coexist in a single `.mcp.json` (the API key config sets an `Authorization` header that OAuth must not have). To switch, replace `.mcp.json` with the appropriate format from `.mcp.apikey-example.json`.
>
> **Gemini CLI:** API key auth requires editing `gemini-extension.json` instead of `.mcp.json`. Add a `headers` block under `mcpServers.kobiton` with `"Authorization": "${KOBITON_AUTH}"`.
>
> **Codex CLI:** OAuth is the default. For CI/headless environments where a browser cannot open, switch to API key auth by adding an `env_http_headers` block to the plugin's `.mcp.json`, then export `KOBITON_AUTH` in the shell that launches `codex`:
>
> ```
> "env_http_headers": { "Authorization": "KOBITON_AUTH" }
> ```
>
> **Recommended:** maintain a fork of `kobiton/automate` with this change committed, then install from your fork - survives plugin reinstalls and Codex upgrades. **Last resort:** edit the installed copy under `~/.codex/.tmp/marketplaces/kobiton/.codex/.mcp.json` directly (this is Codex cache; the edit is overwritten on every reinstall).

</details>

## Getting Started

After installation, run setup to fetch your credentials and write them to `~/.kobiton/.credentials`:

```
/automate:setup
```

The plugin uses your already-authenticated MCP session (OAuth) to fetch your username and API key - no manual file editing required.

To verify everything is wired correctly, run the diagnostic:

```
/automate:doctor
```

`/automate:doctor` is read-only. It checks the CLI installation (symlink + target), the credentials file, the active profile, and required fields, and prints actionable remediation hints for any failures.

> **On Cursor (CLI and IDE)** the plugin's commands carry no `automate:` prefix. Run `/setup` and `/doctor` instead, picking the entry with the Kobiton description next to it to tell it apart from Cursor's built-in command of the same name.

**CLI symlink install behavior across CLIs:** The `run-interactive-cli-session` skill depends on a `~/.kobiton/bin/kobiton` symlink.

- **Claude Code, Codex CLI**: recreated automatically by a bundled SessionStart hook on every session start. On Codex CLI, the first session prompts you to trust the hook once via `/hooks`; subsequent sessions run it silently. Running `/automate:setup` also recreates the symlink on demand.
- **GitHub Copilot CLI, Gemini CLI, Cursor CLI**: no SessionStart hook runs, so create the symlink manually by running the setup command once after install: `/automate:setup` on Copilot and Gemini, `/setup` (the one with the Kobiton description) on Cursor (Copilot reads Claude-format Markdown commands; Gemini reads bundled TOML at `commands/automate/setup.toml`). Re-run it if the symlink goes missing.

Manual fallback - if the SessionStart hook was denied on Codex, or you need to install without an active session:

```bash
bash "$(find ~/.codex -name install-cli.sh -path '*automate*' 2>/dev/null | head -1)"
```

The script is idempotent - safe to re-run.

## What You Can Do

**Ask your assistant naturally:**

- "List my available Android devices"
- "Upload my-app.apk and run tests on the Pixel 6"
- "Show me the results for session 502"
- "Run my Appium test script on the Pixel 6"

## Tools

29 MCP tools across 5 domains.

### Devices

| Tool | Description |
|------|-------------|
| `listDevices` | List available devices filtered by platform, availability, or group |
| `getDeviceStatus` | Get real-time status of a specific device |
| `reserveDevice` | Reserve a device for exclusive testing |
| `terminateReservation` | Release a reserved device by terminating its reservation |

### Sessions

| Tool | Description |
|------|-------------|
| `listSessions` | List test sessions with filters for status, device, platform |
| `getSession` | Get session details including commands, capabilities, metadata |
| `getSessionArtifacts` | Get download URLs for video, logs, screenshots, reports |
| `getUserInputEvents` | Get the touch/swipe gestures a human made on the device-only live view during a session |
| `terminateSession` | Stop a running test session |

### Apps

| Tool | Description |
|------|-------------|
| `listApps` | List uploaded app builds in your organization |
| `uploadAppToStore` | Upload an app to Kobiton Store (permanent, visible in portal) |
| `confirmAppUpload` | Confirm an uploaded file so Kobiton creates the app record (parsing runs asynchronously) |
| `getAppParsingStatus` | Check the async parse status of an uploaded app version until it reaches a terminal state |
| `getApp` | Get app details and version history |

### Test Management

| Tool | Description |
|------|-------------|
| `saveTestCase` | Convert a finished manual session into a reusable test case |
| `listTestCases` | List test cases with team and keyword filters |
| `getTestCase` | Get test case details including its steps |
| `updateTestCase` | Update a test case's metadata and steps |
| `deleteTestCase` | Delete a test case |
| `createTestRun` | Create a test run from a test suite or selected test cases |
| `listTestRuns` | List test runs with team, keyword, and platform filters |
| `getTestRun` | Get test run details including its sessions |
| `terminateTestRun` | Stop a running test run |
| `listTestSuites` | List test suites with team and keyword filters |
| `getTestSuite` | Get test suite details including member test cases |
| `createTestSuite` | Create a test suite from existing test cases |
| `updateTestSuite` | Update a test suite's metadata and membership |
| `deleteTestSuite` | Delete a test suite (member test cases are kept) |

### Account

| Tool | Description |
|------|-------------|
| `getCredential` | Return the authenticated user's username, API key, and portal URL — backs `/automate:setup` |

## Skills

| Skill | Description |
|-------|-------------|
| **run-automation-suite** | Guided workflow for app upload, device selection, local Appium script execution (Node.js, Python, .NET, Java), and result collection. |
| **run-interactive-cli-session** | Guided workflow for interactive testing using natural language. WebDriver actions, device operations (adb shell, logs, screen), file management (push/pull), and more. |
| **drive-automation-session** | Drives an already-reserved device from a natural-language intent via a direct Appium HTTP session (observe-decide-act loop). Returns a session id consumable by `saveTestCase`. Complements `run-interactive-cli-session` — it uses the automation session type rather than the CLI. |
| **create-test-run** | Creates a test run from a test case or suite — fills sensible defaults from the `createTestRun` schema when details are omitted, confirms a summary, then offers to monitor it and hands off to `monitor-test-run`. |
| **monitor-test-run** | Watches a running test run and narrates it: reads the live-remediation flag up front, surfaces the live-remediation URL the moment an execution is blocked (optionally auto-opening the window), and post-mortems so a `BLOCKER_ENCOUNTERED` execution is never reported as passed. Quiet between real state changes. |

> **Platform support note:** all MCP tools and the `run-automation-suite` skill work on every platform the host CLI supports. The `run-interactive-cli-session` skill ships a CLI binary for **macOS Apple Silicon** only. On other platforms, use `run-automation-suite` or the MCP tools directly.

## Commands

| Command | Description |
|---------|-------------|
| `/automate:setup` | Fetch credentials from the authenticated MCP server and write them to `~/.kobiton/.credentials` |
| `/automate:doctor` | Read-only diagnostic for CLI installation, credentials file, active profile, and required fields |

On Cursor (CLI and IDE) these register without the `automate:` prefix — as `/setup` and `/doctor`, distinguishable from Cursor's built-ins by the Kobiton description.

## Running Automation Tests

Use the **run-automation-suite** skill to run local Appium test scripts. Your AI assistant reads your script, extracts capabilities, confirms the target device, and executes the script locally. Supports Node.js (`.js`), Python (`.py`), .NET (`.cs`), and Java (`.java`) scripts.

## Interactive Device Testing

Use the **run-interactive-cli-session** skill to interact with devices using natural language. Describe what you want — "tap the login button", "type hello in the search field", "swipe down" — and your assistant translates your intent into CLI commands.

Beyond WebDriver, the skill also supports device operations (adb shell, logs, screen capture), file management (push/pull files to device), and app management.

## Examples

See [docs/examples.md](docs/examples.md) for prompt examples covering every tool and skill - device management, session management, app management, automation, and interactive testing.

## Troubleshooting

### Updating the Plugin

After the plugin is updated upstream, pull the latest version:

- **Claude Code / Copilot CLI:** run `/plugin install automate@kobiton` again
- **Gemini CLI:** run `gemini extensions update kobiton-automate` from your shell
- **Codex CLI:** run `codex plugin marketplace upgrade` to refresh the marketplace catalog, then reinstall the plugin from the browser to pull the latest manifest
- **Cursor CLI:** re-run `/plugin marketplace add github.com/kobiton/automate` and reinstall the **automate** plugin - Cursor CLI has no dedicated update command yet (`/plugin marketplace list` only lists what's installed). Restart `agent` so the new manifest is picked up.

To make sure the assistant picks up the changes with no stale cache, reload per CLI:

- **Claude Code:** run `/reload-plugins` in-session. If tools still behave unexpectedly, `/clear` resets the session context.
- **GitHub Copilot CLI:** exit and relaunch the session (`exit`, then `copilot`). No in-session reload command.
- **Gemini CLI:** exit and relaunch (`exit`, then `gemini`). Confirm with `gemini extensions list`.
- **Codex CLI:** exit and relaunch. Confirm with `codex plugin list`.

If the issue persists after relaunch, quit the terminal entirely and start a fresh session.

### Common Issues

<details>
<summary><strong>MCP server doesn't appear in <code>/mcp</code> after install</strong></summary>

All four CLIs cache plugin state when the session starts. After installing or updating the plugin, the `kobiton` MCP server may not show up in the server list immediately. Force a reload:

**Claude Code** — reload plugins in the current session:

```
/reload-plugins
```

**GitHub Copilot CLI** — exit and relaunch the session:

```bash
exit
copilot
```

**Gemini CLI** — exit and relaunch; if still missing, verify the extension is enabled:

```bash
exit
gemini extensions list
gemini
```

**Codex CLI** — exit and relaunch; if still missing, verify the marketplace was added and the plugin was installed:

```bash
exit
codex plugin marketplace list
codex plugin list
codex
```

If using the manual fallback config, also check `grep -A 4 "mcp_servers.kobiton" ~/.codex/config.toml`.

Then check the server list (`/mcp` in Claude Code, Gemini CLI, and Codex CLI, `/mcp show` in Copilot CLI). `kobiton` should now appear.
</details>

<details>
<summary><strong>"Device not found"</strong></summary>

The device may be offline, reserved by another user, or no longer in your device list. Use `listDevices` with `available: true` to find currently online devices.
</details>

<details>
<summary><strong>"Upload timeout"</strong></summary>

Large app files or slow connections can cause uploads to time out. Retry the upload — pre-signed URLs expire after 30 minutes, so a new URL will be generated automatically.
</details>

### Claude Code

<details>
<summary><strong>Plugin features not working or behaving unexpectedly</strong></summary>

Some older versions of Claude Code don't support the plugin features this plugin relies on. Make sure you're on the latest version:

```bash
npm install -g @anthropic-ai/claude-code@latest
```

Then restart Claude Code and try again.
</details>

<details>
<summary><strong>"It keeps asking me to open a folder"</strong></summary>

Claude Code requires a working directory. Launch it from inside a project folder:

```bash
cd my-project
claude
```

If you see this prompt repeatedly, make sure you are not running `claude` from your home directory or root (`/`).
</details>

<details>
<summary><strong>"Plugin not found in marketplace"</strong></summary>

The Kobiton marketplace must be added before installing:

```bash
/plugin marketplace add kobiton/automate
/plugin install automate@kobiton
```

If it still isn't found, check your internet connection and ensure you're running the latest version of Claude Code (`claude update`).
</details>

<details>
<summary><strong>"claude: command not found"</strong></summary>

Claude Code is not installed or not in your PATH.

- **Install:** follow the [official install guide](https://docs.anthropic.com/en/docs/claude-code/overview)
- **PATH issue:** if you installed via npm, make sure your npm global bin directory is in your PATH:

  ```bash
  npm install -g @anthropic-ai/claude-code
  ```

  Then open a new terminal window and try `claude` again.
</details>

<details>
<summary><strong>"Nothing happens after install"</strong></summary>

The plugin installed but tools don't appear or Claude doesn't recognize Kobiton commands.

1. Run `/reload-plugins` to force Claude to pick up the new plugin
2. Try asking: *"List my Kobiton devices"*
3. If still not working, quit Claude Code entirely and start a fresh session
4. Verify `.mcp.json` exists in the plugin directory — it tells Claude where the Kobiton MCP server lives
</details>

### Copilot CLI

<details>
<summary><strong>MCP tools not available after plugin install</strong></summary>

Verify the plugin is installed and the MCP server is configured:

```bash
# Check installed plugins
copilot plugin list

# Check MCP server status
/mcp show
```

If the `kobiton` MCP server doesn't appear, add it manually by running `/mcp add` and entering the following when prompted:

- **Server name:** `kobiton`
- **Type:** `http`
- **URL:** `https://api.kobiton.com/mcp`

Alternatively, edit `~/.copilot/mcp-config.json` directly:

```json
{
  "mcpServers": {
    "kobiton": {
      "type": "http",
      "url": "https://api.kobiton.com/mcp"
    }
  }
}
```
</details>

<details>
<summary><strong>Tool calls are blocked</strong></summary>

Copilot CLI requires explicit tool permissions. Allow Kobiton tools:

```bash
# Allow all Kobiton MCP tools
copilot --allow-tool='kobiton'

# Or allow specific tools
copilot --allow-tool='kobiton(listDevices)' --allow-tool='kobiton(getSession)'
```
</details>

### Gemini CLI

<details>
<summary><strong>Extension installed but tools or skills don't appear</strong></summary>

Verify the extension is registered and enabled:

```bash
gemini extensions list
```

If `kobiton-automate` is missing, reinstall:

```bash
gemini extensions install https://github.com/kobiton/automate
```

If listed but disabled, enable it:

```bash
gemini extensions enable kobiton-automate
```

Then relaunch `gemini` and check `/mcp` for the `kobiton` server. The `run-automation-suite` skill is auto-discovered from `skills/` at the extension root, no separate registration needed.
</details>

<details>
<summary><strong><code>/mcp</code> shows <code>kobiton</code> as Disconnected (OAuth not authenticated)</strong></summary>

The extension is installed but you haven't completed OAuth yet. Trigger the flow manually:

```
/mcp auth kobiton
```

A browser window opens for Kobiton login. After signing in, run `/mcp` again — the status should change to 🟢 Connected.

Note: `kobiton` here is the **MCP server name** (declared inside the extension), not the extension name `kobiton-automate`. `/mcp` commands always take the server name.
</details>

<details>
<summary><strong>OAuth doesn't open a browser on first tool call</strong></summary>

Gemini CLI's extension uses dynamic OAuth discovery by default. The Kobiton MCP server advertises OAuth metadata at a standard well-known endpoint, so the browser flow should kick in automatically the first time a tool needs auth.

If nothing happens, try `/mcp auth kobiton` to trigger it explicitly. Check that your terminal can launch a browser. For headless environments, switch to API key auth by editing `gemini-extension.json` directly (see the **API Key Authentication** section above).
</details>

### Codex CLI

<details>
<summary><strong>Tools not appearing or "MCP server kobiton not initialized"</strong></summary>

Verify each step:

1. **Plugin installed** — open `/plugins` inside Codex and confirm `automate` is listed under the `kobiton` marketplace as **Installed**. If missing, run `codex plugin marketplace add kobiton/automate` and reinstall from the plugin browser.
2. **Codex version recent enough** — update with `npm install -g @openai/codex@latest`.

After fixing, exit Codex and relaunch; the server should show in `/mcp` (or `/mcp verbose`).
</details>

<details>
<summary><strong>Browser does not open for OAuth login</strong></summary>

Codex tries to launch your system browser when Kobiton requires sign-in. If nothing opens, check:

1. **Default browser is set** — your OS needs a default browser. SSH sessions without X forwarding cannot open one.
2. **Localhost ports not blocked** — Codex listens on a local port to receive the login callback. Firewall rules that block all localhost ports will break the flow.
3. **Headless environment** — switch to API key auth (see the **API Key Authentication** section above). Easiest: fork this repo, commit the `env_http_headers` change to `.codex/.mcp.json`, install from your fork.
</details>

<details>
<summary><strong>OAuth login completes but <code>/mcp</code> still shows Disconnected</strong></summary>

This usually means the cached token is stale and refresh failed. Force a re-login by clearing the OS keychain entry and reconnecting:

- **macOS:** open Keychain Access, search for `codex-mcp` or `kobiton`, delete the entry, then trigger a tool call to re-run OAuth.
- **Linux:** `secret-tool clear service codex-mcp` (or use Seahorse to remove the entry).
- **Windows:** open Credential Manager, find the Codex entry under Generic Credentials, remove it.

After clearing, run any Kobiton tool prompt; the browser should reopen for fresh login.
</details>

### Cursor CLI

<details>
<summary><strong>Skills or slash commands don't appear (or show stale names) after install</strong></summary>

Cursor CLI caches plugin state per session, and older builds didn't load plugin-bundled skills at all:

1. **Fully restart the session** — exit and re-run `agent`. Right after an install or update, the command list can render stale entries from the previous install; a fresh launch fixes it.
2. **Update the CLI** — plugin skills only register in CLI builds from `2026.05.05` onward. Run `agent update`, then relaunch.
3. **Reinstall if still missing** — `/plugin marketplace add github.com/kobiton/automate`, wait for the **automate** entry to appear, then press <kbd>Enter</kbd> to install.
</details>

<details>
<summary><strong><code>kobiton</code> shows Disconnected or MCP tool calls silently fail</strong></summary>

- **Not logged in yet** — run `/mcp list`, select **kobiton**, and choose **Login** to start the browser OAuth flow. Tokens are stored in the OS keychain.
- **Known CLI regressions** — a few CLI builds listed MCP tools but never executed the calls. Run `agent update` to get the latest build, then relaunch `agent`.
</details>

<details>
<summary><strong><code>~/.kobiton/bin/kobiton</code> CLI wrapper missing (interactive testing fails)</strong></summary>

Cursor CLI does not run the plugin's SessionStart hook, so the CLI wrapper isn't created automatically like on Claude Code or Codex. Run `/setup` (the plugin's command with the Kobiton description, not Cursor's built-in) once after install; re-run it if the symlink goes missing.
</details>

### Still Stuck?

For additional help, open an issue at [github.com/kobiton/automate/issues](https://github.com/kobiton/automate/issues/new?template=bug_report.md) or ask in [#general-discussion](https://discord.com/channels/1486036652685267055/1488189710248710327) on Discord. Feel free to share [feature requests](https://github.com/kobiton/automate/issues/new?template=feature_request.md). We welcome product feedback and will consider it as we continue to improve the platform.

## Privacy & Data

This plugin connects to the Kobiton cloud API (`api.kobiton.com`) over HTTPS (TLS 1.2+).

**Authentication:**

- **OAuth 2.1 (default):** Your AI assistant opens a browser for Kobiton login. Short-lived access tokens are stored securely in the system keychain. No credentials are stored in the project.
- **API Key (alternative):** The `KOBITON_AUTH` environment variable is sent via the `Authorization` header on each request. The value is stored only in your shell profile, never committed to the repo.

**Data handling:**

- The plugin does not store any data locally beyond what your AI assistant retains in its conversation context.
- Tool responses (device lists, session details, test results) pass through your assistant's context window and are subject to [Anthropic's Privacy Policy](https://www.anthropic.com/privacy), [GitHub Copilot's Privacy Statement](https://docs.github.com/en/site-policy/privacy-policies/github-general-privacy-statement), [Google's Gemini Privacy Notice](https://ai.google.dev/gemini-api/terms), or [OpenAI's Privacy Policy](https://openai.com/policies/privacy-policy), depending on which assistant you use.
- App binaries uploaded via `uploadAppToStore` are sent directly to Kobiton's pre-signed S3 URLs, not through your AI assistant.

For details on how Kobiton handles your data, see the [Kobiton Privacy Policy](https://kobiton.com/privacy-policy) and [Trust Center](https://kobiton.com/trust-center/).

## Development

The `tools/` directory contains reference YAML schemas that mirror the MCP server's tool definitions. They are published to S3 for the backend but are not consumed by the plugin at runtime.

```bash
# Install dependencies
pnpm install

# Validate manifests and schemas
pnpm run validate

# Run tests
pnpm test

# Refresh the .codex/ mirror after editing skills/ or assets/
pnpm run build:codex

# Build combined tool definitions (for S3 publishing)
pnpm run build
```

## License

[MIT](https://opensource.org/license/mit)
