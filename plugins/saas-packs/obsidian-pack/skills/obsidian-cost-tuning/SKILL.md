---
name: obsidian-cost-tuning
description: |
  Optimize Obsidian plugin resource usage and external service costs.
  Use when managing API quotas, reducing storage usage,
  or optimizing sync and external service consumption.
  Trigger with phrases like "obsidian resources", "obsidian quota",
  "optimize obsidian storage", "reduce obsidian costs".
allowed-tools: Read, Write, Edit
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code, codex, openclaw
---

# Obsidian Cost Tuning

## Overview
Optimize costs related to Obsidian usage, including Sync subscription ($4/mo personal, $8/mo for 10GB), Publish hosting ($8/mo per site), and third-party plugin API costs. The main cost drivers are: Obsidian Sync storage (1-10GB depending on tier), Publish bandwidth, and external API calls from community plugins (AI assistants, translation services, image hosting). Vault size management is the single biggest lever.

## Prerequisites
- Understanding of your Obsidian subscription tier (free, Catalyst, Sync, Publish)
- Access to vault storage metrics
- Knowledge of which community plugins make external API calls

## Instructions

### Step 1: Audit Vault Size and Storage Usage
```bash
# Check total vault size
du -sh /path/to/vault/

# Find largest files consuming sync bandwidth
find /path/to/vault/ -type f -exec du -h {} + | sort -rh | head -20

# Count files by type
find /path/to/vault/ -type f | sed 's/.*\.//' | sort | uniq -c | sort -rn | head -10
```

### Step 2: Reduce Sync Storage Costs
```yaml
# .obsidian/sync-exclusions.md - Exclude from Obsidian Sync
# Large binary files that don't need cloud sync
*.pdf
*.mp4
*.zip
attachments/archives/**
node_modules/**
.git/**

# Generated content that can be recreated
.obsidian/plugins/*/data.json   # Plugin caches (regenerated on launch)
.trash/**                        # Deleted files in vault trash
```

### Step 3: Optimize Plugin API Costs
```typescript
// For plugins that call external APIs (AI assistants, translation, etc.)
// Implement caching to reduce API calls
class PluginCostOptimizer {
  // Cache AI responses to avoid re-querying for identical prompts
  private responseCache = new Map<string, { result: string; timestamp: number }>();
  private cacheTTL = 24 * 60 * 60 * 1000; // 24 hours

  async getCachedOrFetch(prompt: string, apiFn: () => Promise<string>): Promise<string> {
    const cached = this.responseCache.get(prompt);
    if (cached && Date.now() - cached.timestamp < this.cacheTTL) return cached.result;
    const result = await apiFn();
    this.responseCache.set(prompt, { result, timestamp: Date.now() });
    return result;
  }
}
```

### Step 4: Choose the Right Sync Tier
```yaml
# Sync tier decision matrix
personal_4_per_month:
  storage: 1GB
  best_for: Text-only vaults, <5000 notes
  tip: Exclude images from sync, use relative links to local folders

standard_8_per_month:
  storage: 10GB
  best_for: Vaults with images and PDFs
  tip: Compress images before adding to vault (tinypng or ImageOptim)

self_hosted_free:
  storage: Unlimited
  options: [Obsidian Git plugin, Syncthing, iCloud Drive]
  tradeoff: Manual setup, no version history UI, but $0/month
```

### Step 5: Optimize Publish Costs
If using Obsidian Publish ($8/mo per site), minimize what you publish:
- Use `publish: true` frontmatter selectively instead of publishing entire folders
- Compress images before embedding (aim for <200KB per image)
- Use external image hosting (Cloudinary free tier) for heavy media

## Error Handling
| Issue | Cause | Solution |
|-------|-------|----------|
| Sync storage full | Large attachments | Exclude binary files from sync, compress images |
| Plugin API costs high | No caching in plugin | Implement response caching or switch to local models |
| Vault backup too large | Accumulated trash | Empty .trash folder, purge version history |
| Publish site slow | Large uncompressed images | Compress images, lazy-load media |

## Examples
```bash
# Quick vault cost audit
echo "=== Vault Size ==="
du -sh /path/to/vault/
echo "=== Top 10 largest files ==="
find /path/to/vault/ -type f -exec du -h {} + | sort -rh | head -10
echo "=== Estimated sync usage ==="
find /path/to/vault/ -not -path '*/.git/*' -not -path '*/.trash/*' -type f -exec du -ch {} + | tail -1
```

```bash
# Compress all PNG images in vault to reduce storage
find /path/to/vault/ -name "*.png" -exec pngquant --quality=65-80 --skip-if-larger --ext .png --force {} \;
```
