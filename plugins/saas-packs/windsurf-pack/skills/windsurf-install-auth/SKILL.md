---
name: windsurf-install-auth
description: |
  Install Windsurf IDE and configure Codeium authentication.
  Use when setting up Windsurf for the first time, logging in to Codeium,
  or configuring API keys for team/enterprise deployments.
  Trigger with phrases like "install windsurf", "setup windsurf",
  "windsurf auth", "codeium login", "windsurf API key".
allowed-tools: Read, Write, Edit, Bash(npm:*), Bash(brew:*), Bash(curl:*), Grep
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code, codex, openclaw
tags: [saas, windsurf, codeium, authentication, ide-setup]

---
# Windsurf Install & Auth

## Overview
Windsurf is an AI-powered code editor by Codeium (now Cognition AI), built on VS Code. It features Cascade (agentic AI assistant), Supercomplete (intent-aware autocomplete), and deep codebase indexing. Authentication is handled through Codeium accounts, not raw API keys.

## Prerequisites
- macOS, Windows, or Linux (64-bit)
- 8GB RAM minimum (16GB recommended for large codebases)
- Internet connection for AI features

## Instructions

### Step 1: Install Windsurf

**macOS:**
```bash
brew install --cask windsurf
```

**Linux (Debian/Ubuntu):**
```bash
curl -fsSL https://windsurf.com/install.sh | bash
# Or download .deb from https://windsurf.com/download
```

**Windows:** Download installer from https://windsurf.com/download

### Step 2: Authenticate with Codeium

On first launch, Windsurf prompts for Codeium authentication:

1. Click "Sign In" in the welcome tab or Windsurf widget (bottom-right status bar)
2. Browser opens to Codeium auth page
3. Sign in with Google, GitHub, or email
4. Authorization token is stored locally at `~/.codeium/`

**Verify authentication:**
- Check the Windsurf widget in the status bar -- it should show a checkmark
- Open Cascade (Cmd/Ctrl+L) and send a test message

### Step 3: Configure for Enterprise / Team

For team deployments with centralized auth:

```json
// Settings > Windsurf Settings (or ~/.codeium/config.json)
{
  "codeium.apiServer": "https://codeium.yourcompany.com",
  "codeium.portal.url": "https://portal.yourcompany.com",
  "codeium.enterpriseMode": true
}
```

Enterprise API key (headless / CI environments):
```bash
# Set via environment variable for non-interactive use
export CODEIUM_API_KEY="your-enterprise-api-key"
```

### Step 4: Verify AI Features Are Working

```
1. Open any project folder in Windsurf
2. Type in a code file -- Supercomplete suggestions should appear
3. Press Cmd/Ctrl+L to open Cascade chat
4. Type "explain this project" -- Cascade should respond with codebase analysis
5. Check status bar widget shows model name (e.g., SWE-1, Claude, GPT)
```

### Step 5: Select Your AI Model

Cascade supports multiple models. Configure via the model selector dropdown in the Cascade panel:

| Model | Plan Required | Best For |
|-------|--------------|----------|
| SWE-1 Lite | Free | Basic coding tasks |
| SWE-1 | Pro ($15/mo) | Complex multi-file edits |
| SWE-1.5 | Pro | Frontier-level performance |
| Claude Sonnet | Pro | Nuanced reasoning |
| GPT-4o | Pro | General-purpose coding |
| Gemini Pro | Pro | Large context tasks |

## Error Handling
| Error | Cause | Solution |
|-------|-------|----------|
| "Sign in required" | Auth token expired | Click Windsurf widget > Sign In |
| Cascade not responding | Not authenticated | Check status bar for auth status |
| No completions appearing | Supercomplete disabled | Click status bar widget > enable autocomplete |
| Enterprise auth fails | Wrong API server URL | Verify `codeium.apiServer` setting |
| "Indexing failed" | Workspace too large | Add `.codeiumignore` to exclude large dirs |

## Examples

### Migrate Settings from VS Code
```bash
# Windsurf inherits VS Code extensions and settings
# Import on first launch or manually:
# Windsurf > Command Palette > "Import VS Code Settings"
```

### Verify Installation
```bash
# Check Windsurf CLI is available
windsurf --version

# Open project in Windsurf from terminal
windsurf /path/to/project
```

## Resources
- [Windsurf Download](https://windsurf.com/download)
- [Windsurf Documentation](https://docs.windsurf.com)
- [Codeium Account Portal](https://windsurf.com/account)
- [Windsurf Pricing](https://windsurf.com/pricing)

## Next Steps
After authentication, proceed to `windsurf-hello-world` for your first Cascade interaction.
