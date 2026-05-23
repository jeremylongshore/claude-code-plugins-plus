# Update Locations

## Update Locations

### 1. Plugin JSON

```json
// .claude-plugin/plugin.json
{
  "name": "plugin-name",
  "version": "1.2.4",  // ← Update here
  ...
}
```

### 2. Marketplace Extended

```json
// .claude-plugin/marketplace.extended.json
{
  "plugins": [
    {
      "name": "plugin-name",
      "version": "1.2.4",  // ← Update here
      ...
    }
  ]
}
```

### 3. Sync CLI Catalog

```bash
npm run sync-marketplace
# Regenerates marketplace.json with new version
```
