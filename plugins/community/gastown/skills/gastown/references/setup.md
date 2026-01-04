# Gas Town Setup Guide

**Internal Reference for Claude Code** - You run all these commands for the user.

## Core Principle

The user never types commands. When they say "install gastown" or "set up my workshop":
1. Check prerequisites
2. Run the installation commands
3. Report results in a warm, in-world voice
4. Offer ⚡ Auto or ✋ Approve mode

## Prerequisites

Before installing, check these are available:

| Tool | Version | Check Command | Purpose |
|------|---------|---------------|---------|
| **Go** | 1.24+ | `go version` | Build and install gt and bd binaries |
| **Git** | 2.20+ | `git --version` | Worktree support for polecats |

If Go isn't installed, help the user install it first.

## Installation Commands (You Run These)

### Install Go Binaries

```bash
go install github.com/steveyegge/gastown/cmd/gt@latest
go install github.com/steveyegge/beads/cmd/bd@latest
```

**Note**: There is NO npm installation. Gas Town is Go-only.

### Check PATH

If `gt` isn't found after install, the user needs Go's bin in PATH.
You can help them by suggesting they add this to their shell config:

```bash
export PATH="$PATH:$HOME/go/bin"
```

Then run `source ~/.bashrc` or `source ~/.zshrc`.

### Verify Installation

Run these to confirm everything's working:

```bash
gt version
bd version
```

## Workspace Initialization

### Create the Workshop

```bash
gt install ~/gt
```

This creates the following structure:

```
~/gt/
├── CLAUDE.md          # Mayor role context
├── mayor/             # Mayor config and state
│   ├── town.json      # Town configuration
│   ├── rigs.json      # Rig registry
│   └── state.json     # Mayor state
└── .beads/            # Town-level issue tracking (gm- prefix)
```

## Git Initialization

Initialize git tracking for the workshop:

```bash
cd ~/gt
gt git-init
```

This creates a proper `.gitignore` and initializes the repo.

### Create Initial Commit

```bash
cd ~/gt
git add .
git commit -m "Initial Gas Town HQ"
```

### Create GitHub Repository (Optional)

If the user wants to back up their town to GitHub:

```bash
gt git-init --github=username/my-gastown-hq
# Or private:
gt git-init --github=username/my-gastown-hq --private
```

## Adding Rigs (Projects)

### Understanding Rigs

**CRITICAL**: A rig is a CONTAINER, not a git clone. When you add a rig, Gas Town creates a directory structure that holds:
- Multiple clones/worktrees for different roles (mayor, refinery, polecats)
- Project-level beads configuration
- Role-specific state

### Add a Rig

```bash
# MUST use GitHub URL - local paths are not supported
gt rig add myproject https://github.com/you/repo.git
```

This creates (rigs go directly under `~/gt/`, NOT inside `~/gt/rigs/`):

```
~/gt/myproject/                # Rig container (NOT a clone itself)
├── config.json                # Rig configuration
├── .repo.git/                 # Shared bare repo for refinery+polecats
├── .beads/                    # Project issue tracking
├── plugins/                   # Rig-level plugins
├── mayor/rig/                 # Mayor's working clone
├── refinery/rig/              # Refinery worktree (sees polecat branches)
├── crew/                      # Human workspaces (add with 'gt crew add')
├── witness/                   # Witness agent directory
└── polecats/                  # Worker worktrees (created on demand)
```

### Rig Add Requirements

- **GitHub URL required**: Use `https://github.com/owner/repo.git` format
- **SSH URLs supported**: `git@github.com:owner/repo.git`
- **Local paths NOT supported**: Cannot use `/path/to/local/repo`

### Post-Rig Verification (CRITICAL)

**After every `gt rig add`, run these verification steps:**

```bash
# 1. Verify rig exists
gt rig list

# 2. Run BOTH health checks
gt doctor
bd doctor

# 3. Check prefix routing is configured
cat ~/gt/.beads/routes.jsonl  # Should have entry for new rig's prefix

# 4. Verify patrol molecules exist
bd list --prefix <rig-prefix>  # Should show Deacon, Witness, Refinery patrols

# 5. Start the Refinery
gt refinery start

# 6. Verify Refinery is running
gt refinery status
```

**BLOCKERS - Fix before slinging work:**

| Check | Command | What to Look For |
|-------|---------|------------------|
| Prefix routing | `cat ~/gt/.beads/routes.jsonl` | Entry for rig's prefix |
| Patrol molecules | `bd list --prefix <prefix>` | Deacon, Witness, Refinery patrols |
| Refinery running | `gt refinery status` | Status: running |
| No doctor errors | `gt doctor && bd doctor` | No critical errors |

**If patrols are missing:**
```bash
gt doctor --fix
```

**If prefix routing is missing:**
The rig's prefix needs to be added to routes.jsonl. Run `gt doctor --fix` or manually add:
```json
{"prefix":"<rig-prefix>-","path":"<rig-name>/mayor/rig"}
```

### Common Post-Rig Issues

**Prefix mismatch errors when slinging:**
```
Error: prefix mismatch: database uses 'X' but you specified 'Y'
```
This means routes.jsonl doesn't have an entry for the prefix being used.
Fix: `gt doctor --fix` or manually add the missing route.

**Patrol molecules not active:**
Patrols exist as templates but aren't "poured" (activated).
Fix: `gt doctor --fix` should activate them.

**Refinery not processing merges:**
The Refinery needs to be started explicitly after rig creation.
Fix: `gt refinery start`

## GitHub CLI Setup

The GitHub CLI (`gh`) enables creating repositories from the command line.

### Install GitHub CLI

```bash
# macOS
brew install gh

# Linux (Debian/Ubuntu)
sudo apt install gh

# Linux (Fedora)
sudo dnf install gh
```

### Authenticate

```bash
# Interactive authentication
gh auth login

# Choose:
# - GitHub.com
# - HTTPS (recommended)
# - Authenticate with browser
```

### Verify Authentication

```bash
gh auth status
```

## Verification Steps

Run these commands to verify your installation:

```bash
# 1. Check binaries
gt version
bd version

# 2. Check workspace
cd ~/gt
gt status

# 3. Run BOTH health checks
gt doctor
bd doctor

# 4. Verify rig setup (after adding a rig)
gt rig list
```

### Expected Doctor Output

```
Gas Town Health Check
=====================
[OK] Go version 1.24+
[OK] Git version 2.20+
[OK] Beads CLI installed
[OK] Workspace structure valid
[OK] .beads/ initialized
```

## Common Setup Errors and Fixes

### `gt: command not found`

**Cause**: Go bin directory not in PATH

**Fix**:
```bash
# Add to shell config
echo 'export PATH="$PATH:$HOME/go/bin"' >> ~/.bashrc
source ~/.bashrc

# Or for zsh
echo 'export PATH="$PATH:$HOME/go/bin"' >> ~/.zshrc
source ~/.zshrc
```

### `bd: command not found`

**Cause**: Beads not installed

**Fix**:
```bash
go install github.com/steveyegge/beads/cmd/bd@latest
```

### `go install` fails with module error

**Cause**: Go version too old

**Fix**:
```bash
# Check version
go version

# If below 1.24, upgrade Go
# macOS: brew upgrade go
# Linux: Download from https://go.dev/dl/
```

### `gt rig add` fails with "not a git repository"

**Cause**: Using local path instead of GitHub URL

**Fix**: Always use a remote URL:
```bash
# Correct
gt rig add myproject https://github.com/you/repo.git

# Wrong - local paths not supported
gt rig add myproject /path/to/local/repo  # FAILS
```

### `gt git-init --github` fails

**Cause**: GitHub CLI not installed or not authenticated

**Fix**:
```bash
# Install gh
brew install gh  # or apt install gh

# Authenticate
gh auth login
```

### `gt doctor` shows errors

**Fix**: Run auto-repair:
```bash
gt doctor --fix
```

For persistent issues:
```bash
gt doctor --verbose
```

### Git authentication issues when adding rigs

**Cause**: SSH keys or credentials not configured

**Fix for HTTPS**:
```bash
# Configure credential caching
git config --global credential.helper cache

# Or use gh for authentication
gh auth setup-git
```

**Fix for SSH**:
```bash
# Test SSH access
ssh -T git@github.com

# If fails, add SSH key to GitHub
# See: https://docs.github.com/en/authentication/connecting-to-github-with-ssh
```

### Local repository push failures

**Error**: When pushing to local test repos (not GitHub):
```
error: refusing to update checked out branch: refs/heads/main
```

**Cause**: Git's safety setting prevents pushes to non-bare repos with checked-out branches.

**Fix**: Configure the local repo to accept pushes:
```bash
cd /path/to/local/repo
git config receive.denyCurrentBranch ignore
```

**Note**: This is only needed for local test repositories. GitHub remotes work automatically.

### Beads sync issues across clones

**Fix**:
```bash
cd ~/gt/myproject/mayor/rig
bd sync --status
bd doctor
```

### Daemon not starting (full stack mode)

**Cause**: tmux not installed or not working

**Fix**:
```bash
# Install tmux
brew install tmux  # macOS
sudo apt install tmux  # Linux

# Test tmux
tmux new-session -d -s test && tmux kill-session -t test
```

## Updating Gas Town

```bash
# Update both binaries
go install github.com/steveyegge/gastown/cmd/gt@latest
go install github.com/steveyegge/beads/cmd/bd@latest

# Fix any post-update issues
gt doctor --fix
```

## Quick Reference (Commands You Run)

```bash
# Installation
go install github.com/steveyegge/gastown/cmd/gt@latest
go install github.com/steveyegge/beads/cmd/bd@latest

# Setup
gt install ~/gt
cd ~/gt
gt git-init
gt rig add <name> <github-url>

# Verification
gt version
gt doctor
gt status
```

## What to Tell the User

After successful setup, report warmly:
- "Your workshop is ready at ~/gt"
- "The engine is installed and verified"
- "What project shall we hook up first?"

If something fails, diagnose with `gt doctor` and help fix it.
