---
name: obsidian-cost-tuning
description: |
  Optimize Obsidian resource usage, sync storage, Publish hosting, and
  third-party plugin API costs. Use when managing vault size, reducing
  Sync bandwidth, controlling Publish costs, or optimizing external API
  consumption from community plugins.
  Trigger with phrases like "obsidian costs", "obsidian sync storage",
  "optimize obsidian", "reduce obsidian costs", "obsidian publish costs".
allowed-tools: Read, Write, Edit, Bash(du:*), Bash(find:*), Grep
version: 2.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code, codex, openclaw
tags: [obsidian, cost-optimization, sync, publish, storage]

---
# Obsidian Cost Tuning

## Overview
Optimize costs across Obsidian's paid services and third-party plugin API usage. Covers Obsidian Sync storage management ($4-$10/mo), Publish hosting optimization ($8/mo per site), vault size reduction strategies, plugin API cost control with caching and quotas, and self-hosted alternatives for zero-cost sync.

## Prerequisites
- Understanding of your Obsidian subscription tier
- Terminal access to the vault directory
- Knowledge of which community plugins make external API calls

## Cost Structure

| Service | Price | Storage | Cost Driver |
|---------|-------|---------|-------------|
| Obsidian (core) | Free | N/A | None |
| Catalyst (early access) | $25 one-time | N/A | One-time |
| Sync (Standard) | $4/mo | 1 GB | Vault size, attachment count |
| Sync (Plus) | $8/mo | 10 GB | Large vaults with media |
| Publish | $8/mo per site | N/A | Published page count, bandwidth |
| Plugin API costs | Varies | N/A | Per-call pricing (AI, translation, etc.) |

## Instructions

### Step 1: Audit Vault Size and Storage Usage
```bash
set -euo pipefail
VAULT_PATH="${1:-$HOME/MyVault}"

echo "=== Vault Storage Audit ==="
echo "Total vault size: $(du -sh "$VAULT_PATH" 2>/dev/null | cut -f1)"
echo ".obsidian size: $(du -sh "$VAULT_PATH/.obsidian" 2>/dev/null | cut -f1)"
echo ""

# File counts by type
echo "=== Files by Type ==="
command find "$VAULT_PATH" -type f -not -path '*/.obsidian/*' -not -path '*/.trash/*' \
  | sed 's/.*\.//' | sort | uniq -c | sort -rn | head -15

echo ""
echo "=== Top 20 Largest Files ==="
command find "$VAULT_PATH" -type f -not -path '*/.obsidian/*' \
  -exec du -h {} + 2>/dev/null | sort -rh | head -20

echo ""
echo "=== Plugin Cache Sizes ==="
for dir in "$VAULT_PATH/.obsidian/plugins"/*/; do
  [ -f "$dir/data.json" ] || continue
  size=$(du -h "$dir/data.json" 2>/dev/null | cut -f1)
  echo "  $(basename "$dir")/data.json: $size"
done
```

### Step 2: Reduce Sync Storage — Exclusion Patterns
Obsidian Sync respects `.obsidian/sync-exclude.json` for excluding paths:

```json
{
  "patterns": [
    "*.pdf",
    "*.mp4",
    "*.mov",
    "*.zip",
    "*.tar.gz",
    "attachments/archives/**",
    "node_modules/**",
    ".git/**"
  ]
}
```

For manual file-level control:
```bash
# Find files over 5MB that consume sync bandwidth
command find "$VAULT_PATH" -type f -size +5M -not -path '*/.obsidian/*' \
  -exec du -h {} + | sort -rh

# Count sync-heavy file types
echo "PDF count: $(command find "$VAULT_PATH" -name '*.pdf' | wc -l)"
echo "Image count: $(command find "$VAULT_PATH" \( -name '*.png' -o -name '*.jpg' -o -name '*.jpeg' \) | wc -l)"
echo "Total attachments: $(du -sh "$VAULT_PATH/attachments" 2>/dev/null | cut -f1)"
```

Strategies to stay under the 1 GB Sync Standard tier:
- Move PDFs to a local folder outside the vault, link with `file:///` URIs
- Compress images before adding: `pngquant --quality=65-80 *.png` or ImageOptim
- Use external image hosting (Cloudinary free tier: 25 credits/mo, ~25K transforms)
- Exclude `.obsidian/plugins/*/data.json` — plugin caches regenerate on launch

### Step 3: Optimize Plugin API Costs
Plugins that call external APIs (AI assistants, translation, image generation) can incur per-call costs. Implement caching in your plugin:

```typescript
// src/services/api-cache.ts
import { Plugin } from 'obsidian';

interface CacheEntry<T> {
  result: T;
  timestamp: number;
}

export class APICache<T> {
  private cache = new Map<string, CacheEntry<T>>();
  private ttlMs: number;

  constructor(ttlMinutes: number = 60) {
    this.ttlMs = ttlMinutes * 60 * 1000;
  }

  get(key: string): T | null {
    const entry = this.cache.get(key);
    if (!entry) return null;
    if (Date.now() - entry.timestamp > this.ttlMs) {
      this.cache.delete(key);
      return null;
    }
    return entry.result;
  }

  set(key: string, result: T) {
    this.cache.set(key, { result, timestamp: Date.now() });
    // Prevent unbounded growth
    if (this.cache.size > 1000) {
      const oldest = this.cache.keys().next().value;
      if (oldest) this.cache.delete(oldest);
    }
  }

  /** Wrap an API call with cache-first logic */
  async getOrFetch(key: string, fetchFn: () => Promise<T>): Promise<T> {
    const cached = this.get(key);
    if (cached !== null) return cached;
    const result = await fetchFn();
    this.set(key, result);
    return result;
  }

  clear() { this.cache.clear(); }
  get size() { return this.cache.size; }
}

// Usage in plugin
const aiCache = new APICache<string>(24 * 60); // 24-hour TTL

async function getSummary(noteContent: string): Promise<string> {
  const hash = simpleHash(noteContent);
  return aiCache.getOrFetch(hash, async () => {
    // Only calls API if not cached
    const response = await requestUrl({ url: 'https://api.openai.com/...', ... });
    return response.json.choices[0].message.content;
  });
}
```

### Step 4: Rate Limiting for External Calls
```typescript
// Prevent runaway API costs with a quota counter
class APIQuota {
  private calls = 0;
  private resetTime = 0;
  private maxCallsPerHour: number;

  constructor(maxPerHour: number) {
    this.maxCallsPerHour = maxPerHour;
  }

  canCall(): boolean {
    const now = Date.now();
    if (now - this.resetTime > 3600000) {
      this.calls = 0;
      this.resetTime = now;
    }
    return this.calls < this.maxCallsPerHour;
  }

  recordCall() { this.calls++; }

  remaining(): number {
    return Math.max(0, this.maxCallsPerHour - this.calls);
  }
}

// Usage
const quota = new APIQuota(100); // max 100 API calls per hour

async function callExternalAPI() {
  if (!quota.canCall()) {
    new Notice('API quota exceeded. Try again later.');
    return;
  }
  quota.recordCall();
  // ... make API call
}
```

### Step 5: Optimize Obsidian Publish Costs
Publish at $8/mo per site. Minimize what you publish to reduce bandwidth:

```yaml
# In each note's frontmatter, control what gets published
---
publish: true          # Include this note on Publish site
permalink: custom-url  # Custom URL path
---
```

Cost reduction strategies:
- Use `publish: true` frontmatter selectively instead of publishing entire folders
- Compress images before embedding (target < 200KB per image)
- Use lazy-loading for heavy media: `![alt](image.png)` with external hosting
- Monitor page count — each additional page adds build time and bandwidth
- Use Obsidian's built-in image compression in Publish settings

### Step 6: Self-Hosted Sync Alternatives (Free)
```yaml
# Decision matrix for $0/month sync
obsidian_git:
  cost: Free
  setup: Install Obsidian Git plugin, configure repo
  pros: Full version history, unlimited storage, branch per device
  cons: Manual setup, no conflict resolution UI, requires Git knowledge
  best_for: Developers, technical users

syncthing:
  cost: Free
  setup: Install on each device, share vault folder
  pros: Real-time sync, no cloud dependency, encrypted
  cons: Devices must be online simultaneously (or have relay), no web access
  best_for: Privacy-focused users, LAN-only setups

icloud_drive:
  cost: Free (with Apple devices)
  setup: Move vault to ~/Library/Mobile Documents/iCloud~md~obsidian/Documents/
  pros: Zero config on Apple ecosystem, transparent to Obsidian
  cons: .obsidian/ conflicts common, slow on large vaults, Apple-only
  best_for: Apple-only users with small vaults

remotely_save:
  cost: Free (with existing S3/WebDAV)
  setup: Install Remotely Save plugin, configure backend
  pros: Works with S3, Dropbox, OneDrive, WebDAV
  cons: Plugin manages sync (no native integration), manual conflict handling
  best_for: Users with existing cloud storage
```

### Step 7: Ongoing Cost Monitoring Script
```bash
#!/bin/bash
# vault-cost-report.sh <vault-path>
VAULT="${1:-$HOME/MyVault}"
echo "=== Monthly Cost Estimate ==="

# Vault size
SIZE_MB=$(du -sm "$VAULT" 2>/dev/null | cut -f1)
echo "Vault size: ${SIZE_MB} MB"

if [ "$SIZE_MB" -lt 1024 ]; then
  echo "Sync tier needed: Standard ($4/mo) — under 1 GB"
elif [ "$SIZE_MB" -lt 10240 ]; then
  echo "Sync tier needed: Plus ($8/mo) — under 10 GB"
else
  echo "WARNING: Vault exceeds 10 GB — Sync Plus limit"
fi

# Published pages
PUB_COUNT=$(grep -rl 'publish: true' "$VAULT"/*.md "$VAULT"/**/*.md 2>/dev/null | wc -l)
echo "Published pages: $PUB_COUNT"
[ "$PUB_COUNT" -gt 0 ] && echo "Publish cost: \$8/mo" || echo "Publish cost: \$0"

# Plugin API costs (estimate by checking for network-calling plugins)
echo ""
echo "=== Plugins with potential API costs ==="
for dir in "$VAULT/.obsidian/plugins"/*/; do
  manifest="$dir/manifest.json"
  [ -f "$manifest" ] || continue
  name=$(python3 -c "import json; print(json.load(open('$manifest')).get('name','?'))" 2>/dev/null)
  # Check if plugin JS makes fetch/requestUrl calls
  if grep -q 'requestUrl\|fetch(' "$dir/main.js" 2>/dev/null; then
    echo "  $name — makes network requests"
  fi
done
```

## Output
- Vault storage audit with file type breakdown and largest files
- Sync exclusion patterns reducing bandwidth consumption
- API response cache with TTL and bounded size
- Rate limiter preventing runaway API costs
- Publish optimization with selective frontmatter and image compression
- Self-hosted sync comparison (Git, Syncthing, iCloud, Remotely Save)
- Monthly cost estimation script

## Error Handling
| Issue | Cause | Solution |
|-------|-------|----------|
| Sync storage full | Large binary attachments | Exclude PDFs/videos from sync, compress images |
| Plugin API costs spike | No caching or rate limiting | Implement APICache + APIQuota (Steps 3-4) |
| Vault backup too large | Accumulated .trash and plugin caches | Empty `.trash/`, exclude `plugins/*/data.json` from sync |
| Publish site slow | Large uncompressed images | Compress to < 200KB, use external image CDN |
| Git sync conflicts on .obsidian/ | Multiple devices editing config | Add `workspace.json` to `.gitignore` |
| iCloud sync corruption | Simultaneous edits on two Apple devices | Never edit same note on two devices at once |

## Examples

### Quick Storage Savings
```bash
# Compress all PNG images in vault (requires pngquant)
command find "$VAULT_PATH" -name '*.png' -exec pngquant --quality=65-80 --skip-if-larger --ext .png --force {} \;

# Move large PDFs to external folder
mkdir -p ~/VaultArchive
command find "$VAULT_PATH" -name '*.pdf' -size +10M -exec mv {} ~/VaultArchive/ \;
```

### Persistent API Cache Across Sessions
```typescript
// Save cache to plugin data.json on unload, restore on load
async onload() {
  const data = await this.loadData();
  if (data?.apiCache) this.apiCache.restore(data.apiCache);
}

onunload() {
  this.saveData({ ...this.settings, apiCache: this.apiCache.serialize() });
}
```

## Resources
- [Obsidian Sync](https://help.obsidian.md/Obsidian+Sync) — official docs
- [Obsidian Publish](https://help.obsidian.md/Obsidian+Publish) — official docs
- [Obsidian Git Plugin](https://github.com/denolehov/obsidian-git)
- [Syncthing](https://syncthing.net/) — open-source file sync
- [Remotely Save](https://github.com/remotely-save/remotely-save)
- [Cloudinary Free Tier](https://cloudinary.com/pricing) — image hosting

## Next Steps
For performance optimization, see `obsidian-performance-tuning`.
For data backup and recovery patterns, see `obsidian-data-handling`.
