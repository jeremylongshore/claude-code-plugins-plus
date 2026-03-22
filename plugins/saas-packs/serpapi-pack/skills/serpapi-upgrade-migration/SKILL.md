---
name: serpapi-upgrade-migration
description: |
  Migrate between SerpApi client versions and handle package changes.
  Use when upgrading from google-search-results to serpapi package,
  or handling API response schema changes.
  Trigger: "upgrade serpapi", "serpapi migration", "serpapi new package".
allowed-tools: Read, Write, Edit, Bash(npm:*), Bash(pip:*), Bash(git:*)
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
tags: [saas, search, seo, serpapi]
compatible-with: claude-code
---

# SerpApi Upgrade & Migration

## Overview

The main migration path: `google-search-results` (legacy) to `serpapi` (current official package). The API itself is stable -- changes are in client library interfaces, not the REST API.

## Instructions

### Python: google-search-results to serpapi

```python
# BEFORE: Legacy package
from serpapi import GoogleSearch
search = GoogleSearch({"q": "test", "api_key": key})
result = search.get_dict()

# AFTER: New official package
import serpapi
client = serpapi.Client(api_key=key)
result = client.search(engine="google", q="test")
# Result is already a dict -- no get_dict() needed
```

```bash
# Migration steps
pip uninstall google-search-results
pip install serpapi

# Update imports across codebase
# OLD: from serpapi import GoogleSearch
# NEW: import serpapi
```

### Node.js: google-search-results-nodejs to serpapi

```typescript
// BEFORE: Legacy
import { GoogleSearch } from 'google-search-results-nodejs';
const search = new GoogleSearch('api_key');
search.json({ q: 'test', engine: 'google' }, (result) => { ... });

// AFTER: Current (Promise-based)
import { getJson } from 'serpapi';
const result = await getJson({ engine: 'google', q: 'test', api_key: key });
// No callbacks -- uses Promises natively
```

### Key Changes

| Aspect | Legacy | Current |
|--------|--------|---------|
| Python import | `from serpapi import GoogleSearch` | `import serpapi` |
| Python init | `GoogleSearch(params_dict)` | `serpapi.Client(api_key=key)` |
| Python search | `search.get_dict()` | `client.search(engine="google", q=...)` |
| Node import | `google-search-results-nodejs` | `serpapi` |
| Node pattern | Callback-based | Promise/async-await |
| Engine param | Via class name (GoogleSearch, BingSearch) | Via `engine` parameter |

### Migration Checklist

- [ ] Replace package: `pip install serpapi` / `npm install serpapi`
- [ ] Update all imports
- [ ] Replace class-per-engine with `engine` parameter
- [ ] Replace callbacks with async/await (Node.js)
- [ ] Remove `.get_dict()` calls (Python -- result is already dict)
- [ ] Test all search queries return expected structure
- [ ] Update CI dependencies

## Resources

- [serpapi Python](https://github.com/serpapi/serpapi-python)
- [serpapi Node.js](https://www.npmjs.com/package/serpapi)
- [Legacy Python](https://github.com/serpapi/google-search-results-python)

## Next Steps

For CI integration, see `serpapi-ci-integration`.
