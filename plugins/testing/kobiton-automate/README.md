# <img src="./assets/logo.svg" width="35" align="center" alt="Kobiton Logo" /> Kobiton Automate

[![Discord](https://img.shields.io/discord/1486036652685267055?color=7289DA&label=Discord&logo=discord&logoColor=white)](https://discord.gg/uHvBFDZVP)
[![Cloud](https://img.shields.io/badge/Cloud-☁️-blue)](https://kobiton.com)
[![Twitter Follow](https://img.shields.io/twitter/follow/KobitonMobile?style=social)](https://x.com/KobitonMobile)

Claude Code plugin for the [Kobiton](https://kobiton.com) mobile testing platform. Manage devices, upload apps, run automation sessions, and view test results directly from your AI coding assistant.

## Before You Begin

Make sure you have:

- **A Kobiton account** — sign up at [kobiton.com](https://kobiton.com) if you don't have one
- **Claude Code installed and working** — verify by running `claude` in your terminal ([install guide](https://docs.anthropic.com/en/docs/claude-code/overview))
- **A workspace folder opened** — Claude Code must be launched from a project directory (e.g. `cd my-project && claude`)

## Installation

### From Claude Code Marketplace

```bash
# add kobiton marketplace
/plugin marketplace add kobiton/automate

# then install the automate plugin
/plugin install automate@kobiton
```

### Login

1. In Claude Code, type `/mcp` to open the MCP server list
2. Select the **kobiton** server — a browser window will open for Kobiton login
3. Sign in with your Kobiton credentials. Tokens are managed automatically.

The `.mcp.json` points to the Kobiton MCP server. Authentication is handled via OAuth 2.1 — when you connect to the server through `/mcp`, Claude Code opens a browser for login.

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
After installation and authentication, verify the plugin loaded by asking Claude: *"List my Kobiton devices"*. If tools aren't recognized, see [Troubleshooting](#troubleshooting).

### API Key Authentication (Alternative)

For CI/CD pipelines or headless environments that cannot open a browser, use API key auth instead:

1. Copy `.mcp.apikey-example.json` to `.mcp.json`
2. Generate an API key at **Kobiton Portal > Settings > API Keys**
3. Set the environment variable:

```bash
# Add to ~/.zshrc, ~/.bashrc, or ~/.bash_profile
export KOBITON_AUTH="Basic $(echo -n 'username:apikey' | base64)"
```

1. Reload your shell and restart Claude Code.

> **Note:** OAuth and API key auth cannot coexist in a single `.mcp.json`. The default config (no `headers` block) uses OAuth via browser login. The API key config uses a `headers` block with `${KOBITON_AUTH}`. To switch, replace `.mcp.json` with the appropriate format.

## What You Can Do

**Ask Claude naturally:**

- "List my available Android devices"
- "Upload my-app.apk and run tests on the Pixel 6"
- "Show me the results for session 502"
- "Run my Appium test script on the Pixel 6"

## Tools (12)

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
| `terminateSession` | Stop a running test session |

### Apps

| Tool | Description |
|------|-------------|
| `listApps` | List uploaded app builds in your organization |
| `uploadAppToStore` | Upload an app to Kobiton Store (permanent, visible in portal) |
| `confirmAppUpload` | Confirm uploaded app for tracking record |
| `getApp` | Get app details and version history |

## Skills

- **run-automation-suite** -- Guided workflow that walks you through app upload, device selection, local Appium script execution (Node.js, Python, .NET, Java), and result collection.


## Running Automation Tests

Use the **run-automation-suite** skill to run local Appium test scripts. Claude reads your script, extracts capabilities, confirms the target device, and executes the script locally. Supports Node.js (`.js`), Python (`.py`), .NET (`.cs`), and Java (`.java`) scripts.

## Troubleshooting

### Updating the Plugin

After the plugin is updated upstream, pull the latest version:

```bash
/plugin install automate@kobiton
```

To make sure Claude picks up the changes with no stale cache:

1. Run `/reload-plugins` to reload all plugins in the current session
2. If tools still behave unexpectedly, run `/clear` to reset the session context
3. As a last resort, quit Claude Code and start a new session

### Common Issues

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

<details>
<summary><strong>"Device not found"</strong></summary>

The device may be offline, reserved by another user, or no longer in your device list. Use `listDevices` with `available: true` to find currently online devices.
</details>

<details>
<summary><strong>"Upload timeout"</strong></summary>

Large app files or slow connections can cause uploads to time out. Retry the upload — pre-signed URLs expire after 30 minutes, so a new URL will be generated automatically.
</details>

### Still Stuck?

For additional help, open an issue at [github.com/kobiton/automate/issues](https://github.com/kobiton/automate/issues/new?template=bug_report.md) or ask in [#general-discussion](https://discord.com/channels/1486036652685267055/1488189710248710327) on Discord. Feel free to share [feature requests](https://github.com/kobiton/automate/issues/new?template=feature_request.md). We welcome product feedback and will consider it as we continue to improve the platform.

## Privacy & Data

This plugin connects to the Kobiton cloud API (`api.kobiton.com`) over HTTPS (TLS 1.2+).

**Authentication:**

- **OAuth 2.1 (default):** Claude Code opens a browser for Kobiton login. Short-lived access tokens are stored securely in the system keychain by Claude Code. No credentials are stored in the project.
- **API Key (alternative):** The `KOBITON_AUTH` environment variable is sent via the `Authorization` header on each request. The value is stored only in your shell profile, never committed to the repo.

**Data handling:**

- The plugin does not store any data locally beyond what Claude Code retains in its conversation context.
- Tool responses (device lists, session details, test results) pass through Claude Code's context window and are subject to [Anthropic's Privacy Policy](https://www.anthropic.com/privacy).
- App binaries uploaded via `uploadAppToStore` are sent directly to Kobiton's pre-signed S3 URLs, not through Claude Code.

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

# Build combined tool definitions (for S3 publishing)
pnpm run build
```

## License

[MIT](https://opensource.org/license/mit)
