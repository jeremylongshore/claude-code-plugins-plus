---
name: obsidian-multi-env-setup
description: |
  Configure multiple Obsidian environments for development, testing, and production.
  Use when managing separate vaults, testing plugin versions,
  or establishing a proper development workflow with isolated environments.
  Trigger with phrases like "obsidian environments", "obsidian dev vault",
  "obsidian testing setup", "multiple obsidian vaults".
allowed-tools: Read, Write, Edit, Bash(mkdir:*), Bash(ln:*)
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code, codex, openclaw
---
# Obsidian Multi-Environment Setup

## Overview
Configure separate development, testing, and production vaults for Obsidian plugin work. Covers vault templates for team onboarding, environment-specific plugin settings, sync strategies, and `.obsidian/` directory management across environments.

## Prerequisites
- Obsidian desktop app installed
- Node.js 18+ and npm/pnpm for plugin builds
- Git for version control (recommended)
- Basic understanding of symlinks and file system operations

## Instructions

### Step 1: Create the Environment Structure

Set up three isolated vaults -- dev, test, and prod:

```bash
# Base directory for all environments
mkdir -p ~/obsidian-envs/{dev,test,prod}

# Dev vault: your working vault with symlinked plugin source
mkdir -p ~/obsidian-envs/dev/.obsidian/plugins/your-plugin
mkdir -p ~/obsidian-envs/dev/sandbox  # scratch notes for testing

# Test vault: clean environment for QA
mkdir -p ~/obsidian-envs/test/.obsidian/plugins/your-plugin
mkdir -p ~/obsidian-envs/test/test-data

# Prod vault: mirrors real user setup
mkdir -p ~/obsidian-envs/prod/.obsidian/plugins/your-plugin
```

### Step 2: Symlink Plugin Source for Development

In the dev vault, symlink your plugin's build output so changes appear immediately:

```bash
# Remove the empty plugin directory in dev
rm -rf ~/obsidian-envs/dev/.obsidian/plugins/your-plugin

# Symlink to your plugin's repo (contains manifest.json, main.js, styles.css)
ln -s /path/to/your-plugin ~/obsidian-envs/dev/.obsidian/plugins/your-plugin
```

For hot reload during development, use the [Hot Reload plugin](https://github.com/pjeby/hot-reload):

```bash
# Clone hot-reload into dev vault's plugins
git clone https://github.com/pjeby/hot-reload.git \
  ~/obsidian-envs/dev/.obsidian/plugins/hot-reload
```

Then enable both your plugin and hot-reload in `.obsidian/community-plugins.json`:

```json
["your-plugin", "hot-reload"]
```

### Step 3: Environment-Specific Plugin Settings

Each vault gets its own `data.json` for your plugin. Create a config factory:

```typescript
// config/environments.ts
interface PluginConfig {
  debugMode: boolean;
  logLevel: 'debug' | 'info' | 'warn' | 'error';
  apiEndpoint: string;
  featureFlags: Record<string, boolean>;
}

const ENV_CONFIGS: Record<string, Partial<PluginConfig>> = {
  dev: {
    debugMode: true,
    logLevel: 'debug',
    apiEndpoint: 'http://localhost:3000',
    featureFlags: { experimentalEditor: true, betaSync: true },
  },
  test: {
    debugMode: true,
    logLevel: 'info',
    apiEndpoint: 'https://staging.api.example.com',
    featureFlags: { experimentalEditor: true, betaSync: false },
  },
  prod: {
    debugMode: false,
    logLevel: 'error',
    apiEndpoint: 'https://api.example.com',
    featureFlags: {},
  },
};

export function detectEnvironment(vaultPath: string): string {
  if (vaultPath.includes('obsidian-envs/dev')) return 'dev';
  if (vaultPath.includes('obsidian-envs/test')) return 'test';
  return 'prod';
}

export function getConfig(env: string): PluginConfig {
  const defaults: PluginConfig = {
    debugMode: false,
    logLevel: 'error',
    apiEndpoint: '',
    featureFlags: {},
  };
  return { ...defaults, ...ENV_CONFIGS[env] };
}
```

Use it in your plugin's `onload()`:

```typescript
async onload() {
  const vaultPath = (this.app.vault.adapter as any).basePath;
  const env = detectEnvironment(vaultPath);
  const config = getConfig(env);
  console.log(`[your-plugin] Running in ${env} mode`);

  if (config.debugMode) {
    // Register debug commands only in dev/test
    this.addCommand({
      id: 'dump-state',
      name: 'Dump Plugin State (debug)',
      callback: () => console.log(JSON.stringify(this.settings, null, 2)),
    });
  }
}
```

### Step 4: Vault Templates for Team Onboarding

Create a template vault that new team members clone:

```
vault-template/
  .obsidian/
    app.json              # Standard app settings
    appearance.json       # Theme and font settings
    hotkeys.json          # Team-standard keybindings
    community-plugins.json  # Approved plugin list
    plugins/              # Pre-configured plugin data.json files
      dataview/data.json
      templater-obsidian/data.json
  templates/              # Note templates (daily, meeting, project)
    daily.md
    meeting.md
    project-kickoff.md
  README.md               # Vault orientation guide
```

Script to provision a new team member's vault:

```bash
#!/bin/bash
# provision-vault.sh <username> <role>
USERNAME=$1
ROLE=${2:-editor}

VAULT_DIR=~/obsidian-team-vaults/$USERNAME
cp -r vault-template "$VAULT_DIR"

# Inject user-specific settings
cat > "$VAULT_DIR/.obsidian/plugins/rbac-plugin/data.json" <<EOF
{
  "userEmail": "${USERNAME}@company.com",
  "role": "${ROLE}"
}
EOF

echo "Vault provisioned at $VAULT_DIR for $USERNAME ($ROLE)"
```

### Step 5: Sync Strategies

Choose based on your team's needs:

**Git sync** (best for plugin developers):
```bash
cd ~/obsidian-envs/prod
git init
cat > .gitignore <<'EOF'
.obsidian/workspace.json
.obsidian/workspace-mobile.json
.obsidian/cache
.trash/
EOF
git add -A && git commit -m "Initial vault state"
```

Pair with the [Obsidian Git plugin](https://github.com/denolehov/obsidian-git) for auto-commit/push on a schedule.

**Obsidian Sync** (best for non-technical teams): Configure in Settings > Sync. Selective sync lets you exclude `.obsidian/plugins/` on certain devices to prevent config conflicts.

**iCloud/Dropbox** (simplest, most fragile): Place the vault inside the sync folder. Avoid editing on multiple devices simultaneously. `.obsidian/` conflicts are common -- keep a backup.

### Step 6: Managing .obsidian/ Across Environments

The `.obsidian/` directory holds all configuration. Key files and their sync behavior:

| File | Sync across envs? | Why |
|------|--------------------|-----|
| `app.json` | Yes | Core settings should be consistent |
| `appearance.json` | Yes | Theme consistency |
| `community-plugins.json` | Per-env | Dev may have debug plugins |
| `hotkeys.json` | Yes | Muscle memory matters |
| `workspace.json` | Never | Layout is per-device |
| `plugins/*/data.json` | Per-env | Settings differ by environment |

Script to sync safe configs from prod to other environments:

```bash
#!/bin/bash
# sync-config.sh -- copy safe configs from prod to dev/test
SAFE_FILES="app.json appearance.json hotkeys.json"
SRC=~/obsidian-envs/prod/.obsidian

for env in dev test; do
  DST=~/obsidian-envs/$env/.obsidian
  for f in $SAFE_FILES; do
    cp "$SRC/$f" "$DST/$f" 2>/dev/null && echo "Synced $f to $env"
  done
done
```

## Output
- Three isolated vaults (dev/test/prod) with independent plugin configurations
- Symlinked plugin source in dev vault with hot reload
- Environment detection and config switching in plugin code
- Vault template and provisioning script for team onboarding
- Sync strategy configured (Git, Obsidian Sync, or cloud)
- `.obsidian/` management scripts for consistent cross-env config

## Error Handling
| Issue | Cause | Solution |
|-------|-------|----------|
| Symlink not working | Permission denied on Windows | Run terminal as Administrator, or use `mklink /D` |
| Plugin not appearing in dev vault | Symlink target missing `manifest.json` | Run `npm run build` first; ensure `main.js` exists |
| Wrong config loaded | Vault path detection failed | Check `basePath` matches expected pattern |
| Hot reload not triggering | `.hotreload` file missing | Create empty `.hotreload` in plugin directory |
| Sync conflict on `workspace.json` | Multiple devices open same vault | Add `workspace.json` to `.gitignore` |
| Test vault has stale data | Forgot to refresh after plugin update | Copy latest build artifacts: `manifest.json`, `main.js`, `styles.css` |

## Examples

**Solo developer workflow**: Dev vault symlinked to plugin repo with hot reload. Test vault gets `npm run build` output copied in manually for final QA. Prod vault is your daily-driver vault with the released version from BRAT or community plugins.

**Team onboarding**: Run `provision-vault.sh alice editor` to create Alice's vault from the team template. She opens it in Obsidian, and all approved plugins with team-standard settings are pre-configured.

**CI testing across Obsidian versions**: Create a headless test vault with your plugin installed. Use `obsidian-cli` or Electron automation to open the vault, run plugin commands, and verify output. Repeat for each Obsidian version in your support matrix.

## Resources
- [Obsidian URI Protocol](https://help.obsidian.md/Extending+Obsidian/Obsidian+URI)
- [BRAT for Beta Testing](https://github.com/TfTHacker/obsidian42-brat)
- [Hot Reload Plugin](https://github.com/pjeby/hot-reload)
- [Obsidian Git Plugin](https://github.com/denolehov/obsidian-git)

## Next Steps
For monitoring and logging across environments, see `obsidian-observability`. For access control on shared vaults, see `obsidian-enterprise-rbac`.
