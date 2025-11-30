# prettier-markdown-hook

Automatically format markdown files with [prettier](https://prettier.io/) when Claude stops responding, with configurable organization and path exclusions.

## Overview

This Claude Code plugin provides a **Stop hook** that automatically formats markdown files in your workspace using prettier. It runs asynchronously in the background after every conversation, ensuring consistent markdown formatting without interrupting your workflow.

### Features

- ✅ **Zero-Config Default**: Works immediately after installation with sensible defaults
- ✅ **Organization Exclusions**: Skip formatting for specific GitHub organizations (e.g., company repos)
- ✅ **Path Exclusions**: Exclude specific directories or file patterns
- ✅ **AI Commit Messages**: Optional AI-generated commit messages (opt-in)
- ✅ **Fire-and-Forget**: Async execution (<10ms hook exit time)
- ✅ **XDG Compliant**: Cross-platform default paths
- ✅ **Comprehensive Logging**: All operations logged for debugging

### How It Works

1. **Stop Hook**: Triggers after Claude finishes responding
2. **Workspace Check**: Verifies you're in a git workspace
3. **Exclusion Check**: Skips excluded organizations/paths
4. **Format Files**: Runs prettier on modified markdown files
5. **Auto Commit**: Creates a conventional commit (optional AI message)
6. **Background Execution**: All processing happens asynchronously

## Installation

### Prerequisites

Ensure these dependencies are installed and available in your `PATH`:

```bash
# Check dependencies
prettier --version  # 2.0 or higher
jq --version        # 1.6 or higher
git --version       # 1.8.5 or higher
```

**Installation commands:**

```bash
# macOS (Homebrew)
brew install prettier jq git

# npm/yarn (prettier)
npm install -g prettier
# or
yarn global add prettier

# Linux (Ubuntu/Debian)
apt-get install jq git
npm install -g prettier
```

### Plugin Installation

**Via Claude Code Marketplace:**

```bash
# Add marketplace (if not already added)
/plugin marketplace add https://github.com/jeremylongshore/claude-code-plugins

# Install plugin
/plugin install prettier-markdown-hook
```

**Manual Installation:**

```bash
# Clone marketplace repository
git clone https://github.com/jeremylongshore/claude-code-plugins

# Copy plugin to Claude Code plugins directory
cp -r claude-code-plugins/plugins/productivity/prettier-markdown-hook \
      ~/.claude/plugins/prettier-markdown-hook
```

### Verification

After installation, the hook will run automatically after Claude stops responding. Check the log file to verify:

```bash
# View log file (XDG-compliant path)
tail -f ~/.local/state/prettier-hook/format-markdown.log

# Or custom log location (if configured)
tail -f $PRETTIER_LOG_DIR/format-markdown.log
```

## Configuration

### Zero-Config (Default)

**No configuration needed!** The plugin works out-of-the-box with sensible defaults:

- Formats all markdown files in workspace
- Skips `node_modules`, `.git`, `.github`, `.claude/skills`, `skills`, `plugins`, `file-history`
- Uses standard prettier formatting
- Conventional commit messages
- Logs to `~/.local/state/prettier-hook/`

### Custom Configuration

Create `~/.prettierrc-hook.json` to customize behavior:

```json
{
  "excludeOrgs": ["Eon-Labs", "CompanyName"],
  "excludePaths": ["docs/archive", "legacy/**/*.md"],
  "logDir": "~/.local/state/prettier-hook"
}
```

**Configuration options:**

| Field | Type | Description | Default |
|-------|------|-------------|---------|
| `excludeOrgs` | `string[]` | GitHub organizations to skip formatting | `[]` |
| `excludePaths` | `string[]` | Paths/patterns to exclude from formatting | `[]` |
| `logDir` | `string\|null` | Custom log directory path | `${XDG_STATE_HOME}/prettier-hook` |

**Example configuration file** is provided at `config/.prettierrc-hook.json.example`.

### Environment Variables

Override configuration with environment variables (highest precedence):

```bash
# Custom config file location
export PRETTIER_CONFIG=~/my-custom-config.json

# Enable AI-generated commit messages (requires `claude` CLI)
export PRETTIER_ENABLE_AI_COMMITS=true

# Custom log directory
export PRETTIER_LOG_DIR=~/logs/prettier
```

**Precedence**: `Environment Variables > Config File > Built-in Defaults`

### Organization Exclusions

Skip formatting for specific GitHub organizations (e.g., employer/client repos):

```json
{
  "excludeOrgs": ["Eon-Labs", "MyCompany", "ClientOrg"]
}
```

**Important**: Organization names are **case-sensitive** and must match exactly:
- ✅ Correct: `"Eon-Labs"` (matches `github.com/Eon-Labs/repo`)
- ❌ Wrong: `"eonlabs"` (will not match)

### Path Exclusions

Exclude specific directories or file patterns:

```json
{
  "excludePaths": [
    "docs/archive",
    "legacy/**/*.md",
    "vendor",
    "third-party"
  ]
}
```

Path exclusions are **additive** to built-in defaults (not replacements).

### AI Commit Messages (Opt-In)

Enable AI-generated commit messages via environment variable:

```bash
# In your shell profile (~/.zshrc, ~/.bashrc)
export PRETTIER_ENABLE_AI_COMMITS=true
```

**Requirements:**
- `claude` CLI installed and in PATH
- Environment variable set to `true`

**Default behavior** (AI disabled):
```
style: format markdown files with prettier
```

**AI-generated example**:
```
docs: standardize markdown formatting across user guides

Applied prettier formatting to 12 markdown files in docs/ to ensure
consistent code block indentation and list formatting.
```

## Usage

### Automatic Formatting (Default)

**No action required!** The hook runs automatically after every conversation:

1. You interact with Claude
2. Claude finishes responding (Stop event)
3. Hook executes in background
4. Markdown files formatted
5. Changes committed (if any modifications)

### Monitoring Hook Execution

**Check log file:**

```bash
# View recent activity
tail -20 ~/.local/state/prettier-hook/format-markdown.log

# Watch live (follow mode)
tail -f ~/.local/state/prettier-hook/format-markdown.log

# Search for errors
grep -i error ~/.local/state/prettier-hook/format-markdown.log
```

**Example log output:**

```
[2025-11-15 18:30:42] Starting prettier markdown formatting
[2025-11-15 18:30:42] Workspace: /Users/terry/projects/my-app
[2025-11-15 18:30:42] Remote: git@github.com:myuser/my-app.git
[2025-11-15 18:30:42] Exclusion check: NOT excluded (no matching org)
[2025-11-15 18:30:43] Found 5 modified markdown files
[2025-11-15 18:30:45] Formatted 5 files successfully
[2025-11-15 18:30:46] Created commit: style: format markdown files with prettier
[2025-11-15 18:30:46] Prettier formatting completed successfully
```

### Disabling the Hook

**Temporary disable** (per workspace):

```bash
# Navigate to workspace
cd /path/to/workspace

# Disable plugin temporarily
/plugin disable prettier-markdown-hook
```

**Permanent uninstall:**

```bash
/plugin uninstall prettier-markdown-hook
```

### Manual Formatting (Alternative)

While the plugin uses the Stop hook (automatic), you can manually run the script:

```bash
# From plugin directory
~/.claude/plugins/prettier-markdown-hook/scripts/format-markdown.sh

# Or add to your PATH
export PATH="$PATH:~/.claude/plugins/prettier-markdown-hook/scripts"
format-markdown.sh
```

## Troubleshooting

### Hook Doesn't Run

**Symptom**: No formatting happens after Claude stops

**Diagnosis:**

```bash
# Check dependencies
prettier --version
jq --version
git --version

# Check plugin installed
/plugin list | grep prettier

# Check hook configuration
cat ~/.claude/plugins/prettier-markdown-hook/hooks/hooks.json
```

**Solutions:**

1. **Missing dependencies**: Install prettier, jq, git
2. **Plugin not enabled**: Run `/plugin enable prettier-markdown-hook`
3. **Not in git workspace**: Hook only runs in git repositories

### Files Not Formatted

**Symptom**: Hook runs but files remain unformatted

**Diagnosis:**

```bash
# Check log file for errors
tail -50 ~/.local/state/prettier-hook/format-markdown.log

# Check if workspace excluded
grep -i "excluded" ~/.local/state/prettier-hook/format-markdown.log

# Check git status
git status
```

**Solutions:**

1. **Workspace excluded**: Check `excludeOrgs` in config
2. **No modified files**: Hook only formats files with uncommitted changes
3. **Prettier errors**: Check log for prettier syntax errors

### Organization Exclusion Not Working

**Symptom**: Files formatted in organization that should be excluded

**Diagnosis:**

```bash
# Check config file
cat ~/.prettierrc-hook.json

# Check organization name (case-sensitive!)
git remote -v
```

**Solutions:**

1. **Case mismatch**: Organization names are case-sensitive
   - ✅ Correct: `"Eon-Labs"` (capital E, L, hyphen)
   - ❌ Wrong: `"eonlabs"`, `"eon-labs"`, `"EonLabs"`

2. **Config not loaded**: Verify JSON syntax with `jq empty ~/.prettierrc-hook.json`

3. **Wrong remote format**: Hook checks `github.com/<org>/<repo>` pattern

### Permission Errors

**Symptom**: `Permission denied` errors in log

**Solutions:**

```bash
# Fix script permissions
chmod +x ~/.claude/plugins/prettier-markdown-hook/scripts/format-markdown.sh

# Fix log directory permissions
mkdir -p ~/.local/state/prettier-hook
chmod 755 ~/.local/state/prettier-hook
```

### Timeout Errors

**Symptom**: Hook times out before completing

**Solutions:**

1. **Increase timeout** in `hooks/hooks.json`:
   ```json
   {
     "hooks": [
       {
         "timeout": 60000  // 60 seconds (default: 30000)
       }
     ]
   }
   ```

2. **Reduce workspace size**: Exclude large directories in `.prettierrc-hook.json`

### AI Commit Messages Not Working

**Symptom**: Commit messages remain generic even with env var set

**Diagnosis:**

```bash
# Check environment variable
echo $PRETTIER_ENABLE_AI_COMMITS

# Check claude CLI
which claude
claude --version
```

**Solutions:**

1. **Env var not set**: Add to shell profile (~/.zshrc, ~/.bashrc)
2. **Claude CLI not installed**: Install claude CLI tool
3. **Claude CLI not in PATH**: Add to PATH or use full path

## Dependencies

### System Dependencies

| Dependency | Version | Purpose | Installation |
|------------|---------|---------|--------------|
| **prettier** | 2.0+ | Markdown formatting | `npm install -g prettier` |
| **jq** | 1.6+ | JSON parsing | `brew install jq` (macOS) |
| **git** | 1.8.5+ | Version control | System default |

### Optional Dependencies

| Dependency | Purpose | Installation |
|------------|---------|--------------|
| **claude CLI** | AI commit messages | See Claude docs |

### Platform Support

- ✅ **macOS**: Full support (tested)
- ✅ **Linux**: Full support (XDG paths)
- ❌ **Windows**: Not supported (Unix-only paths)

## Architecture

### Hook Execution Flow

```
1. Claude Stop Event
   ↓
2. Hook Trigger (hooks.json)
   ↓
3. format-markdown.sh (background process)
   ↓
4. Check Dependencies (prettier, jq, git)
   ↓
5. Load Configuration (~/.prettierrc-hook.json)
   ↓
6. Workspace Validation (git repo check)
   ↓
7. Exclusion Check (organizations, paths)
   ↓
8. Find Modified Files (git status)
   ↓
9. Format with Prettier
   ↓
10. Create Commit (conventional or AI)
    ↓
11. Log Results
```

### Configuration Precedence

```
Environment Variables (highest)
   ↓
Config File (~/.prettierrc-hook.json)
   ↓
Built-in Defaults (lowest)
```

### File Structure

```
prettier-markdown-hook/
├── .claude-plugin/
│   └── plugin.json           # Plugin metadata
├── hooks/
│   └── hooks.json            # Stop hook configuration
├── scripts/
│   └── format-markdown.sh    # Main formatting script
├── config/
│   └── .prettierrc-hook.json.example  # Config example
├── README.md                 # This file
└── LICENSE                   # MIT license
```

## Related Documentation

- **ADR-0002**: [Prettier Marketplace Plugin Refactoring](https://github.com/user/repo/blob/main/docs/decisions/0002-prettier-marketplace-plugin-refactoring.md)
- **ADR-0003**: [Prettier Marketplace Plugin Creation](https://github.com/user/repo/blob/main/docs/decisions/0003-prettier-marketplace-plugin-creation.md)
- **Specification**: [Prettier Workspace Exclusion v2.0.0](https://github.com/user/repo/blob/main/specifications/prettier-workspace-exclusion.yaml)

## Contributing

Contributions welcome! Please:

1. Fork the repository
2. Create a feature branch
3. Follow conventional commit messages
4. Submit pull request

## License

MIT License - see [LICENSE](LICENSE) file for details.

## Support

**Issues**: [GitHub Issues](https://github.com/jeremylongshore/claude-code-plugins/issues)

**Marketplace**: [claudecodeplugins.io](https://claudecodeplugins.io/)

## Changelog

### 1.0.0 (Initial Release)

**Features:**
- Stop hook for automatic markdown formatting
- JSON-based configuration system
- Organization exclusion support
- Path exclusion support
- AI commit message generation (opt-in)
- XDG-compliant default paths
- Comprehensive error handling
- Extensive logging

**Dependencies:**
- prettier (2.0+)
- jq (1.6+)
- git (1.8.5+)

---

**Version**: 1.0.0
**Author**: Terry Li
**License**: MIT
**Plugin Type**: Hooks (Stop)
**Category**: Productivity
