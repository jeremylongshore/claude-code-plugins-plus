# Prerequisites — detailed checks

Reference for the `install` mode's Step 0. Three checks; each has a
deterministic detection command and a copy-pasteable recovery.

## 1. Bun ≥ 1.0

**Detect:**

```bash
bun --version
```

Expected: `1.x.x` or higher. If the command is not found, Bun is not
installed.

**Install:**

```bash
curl -fsSL https://bun.sh/install | bash
```

After install, restart your shell (or `source ~/.bashrc` / `source ~/.zshrc`)
and re-run `bun --version` to confirm.

### Node.js fallback

If the user prefers Node.js (or Bun install fails on their platform):

```bash
node --version    # need ≥ 20.x
```

Then edit `.mcp.json` in the repo root to change the runner:

```diff
- "command": "bun",
- "args": ["server.ts"]
+ "command": "npx",
+ "args": ["tsx", "server.ts"]
```

Run `npm install` (instead of `bun install`) on the next install step.
Performance is ~2× slower than Bun but functionally identical.

### Docker fallback

If neither Bun nor a recent Node is available:

```bash
docker --version  # need ≥ 24.x
docker build -t claude-slack-channel .
```

Edit `.mcp.json`:

```diff
- "command": "bun",
- "args": ["server.ts"]
+ "command": "docker",
+ "args": ["run", "--rm", "-i", "-v", "~/.claude/channels/slack:/state", "claude-slack-channel"]
```

## 2. Claude Code ≥ v2.1.80

**Detect:**

```bash
claude --version
```

Channels require **v2.1.80** at minimum (Research Preview floor). Older
versions silently fail to load the plugin with non-obvious errors.

**Upgrade:**

Follow the official install / upgrade path at https://docs.claude.com/claude-code/install.
On most systems:

```bash
# macOS / Linux
curl -fsSL https://claude.ai/install.sh | bash

# Or if installed via npm
npm install -g @anthropic-ai/claude-code@latest
```

Re-check with `claude --version` after upgrading.

## 3. `claude.ai` login (NOT API-key-only)

**Detect:**

```bash
claude auth status
```

(Or whatever the current command surface is — the exact subcommand has
evolved across Claude Code versions. Look for indication of an active
`claude.ai` session in the output.)

If the output shows only `ANTHROPIC_API_KEY` set with no `claude.ai`
session, Channels will fail to load. **This is a Research Preview
constraint** — API-key-only auth does not work for Channels.

**Fix:**

```bash
claude login
```

Complete the browser flow. After login completes, `claude auth status`
should show an active `claude.ai` session.

### Why this matters

Channels uses features that gate on `claude.ai` session identity (per
the Research Preview constraint). When the only auth signal is
`ANTHROPIC_API_KEY`, the plugin loader rejects the channel registration
with a non-obvious error in `~/.claude/logs/`. The user sees "the bot
just doesn't work."

## Optional: `jq` (only needed for `doctor` / `repair` modes)

The `doctor` and `repair` modes use `jq` for JSON parsing of Slack API
responses and `access.json` validation. The `install` mode itself does
not need it — skip this if you're only doing a fresh install.

```bash
command -v jq    # confirm whether jq is installed
```

If missing:

```bash
# macOS
brew install jq

# Debian / Ubuntu
sudo apt install jq

# Fedora / RHEL
sudo dnf install jq

# Other: https://jqlang.org/download/
```

## All three green? Proceed to Step 1

When `bun --version`, `claude --version`, and `claude auth status` all
report acceptable values, you have the prerequisites in place. Continue
to the Slack app creation step.
