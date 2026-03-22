---
name: framer-common-errors
description: |
  Diagnose and fix Framer common errors and exceptions.
  Use when encountering Framer errors, debugging failed requests,
  or troubleshooting integration issues.
  Trigger with phrases like "framer error", "fix framer",
  "framer not working", "debug framer".
allowed-tools: Read, Grep, Bash(curl:*)
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
tags: [saas, framer]
compatible-with: claude-code
---

# Framer Common Errors

## Overview

Diagnostic reference for common Framer plugin, component, and Server API errors with actionable fixes.

## Error Reference

### Plugin Not Appearing in Editor

**Cause:** Dev server not running or plugin not registered.

**Fix:**
```bash
npm run dev  # Start Vite dev server
# Then in Framer: Plugins > Development > select your plugin
```

---

### `framer is not defined`

**Cause:** Calling `framer` API outside the Framer editor iframe context.

**Fix:** The `framer` global from `framer-plugin` only works inside the editor. For server-side access, use `framer-api` package instead.

```typescript
// Plugin (editor): import { framer } from 'framer-plugin';
// Server (headless): import { framer } from 'framer-api';
```

---

### Component Renders Blank on Canvas

**Cause:** Runtime error in component code (swallowed by Framer).

**Fix:** Open Framer's browser console (right-click > Inspect) and check for errors. Common causes:
- Missing `export default` on component
- Undefined props without defaults
- Fetch errors from blocked CORS requests

---

### `addPropertyControls` Not Showing

**Cause:** Called on wrong component or wrong import.

**Fix:**
```tsx
// Must import from 'framer', not 'framer-plugin'
import { addPropertyControls, ControlType } from 'framer';

// Must be called AFTER the component definition
export default function MyComponent(props) { /* ... */ }
addPropertyControls(MyComponent, { /* ... */ });
```

---

### Code Override Not Applying

**Cause:** Override function not returning correct shape.

**Fix:** Overrides must return an `Override` type object (Framer Motion props):
```tsx
import { Override } from 'framer';

// Correct — returns Override
export function MyOverride(): Override {
  return { whileHover: { scale: 1.1 } };
}

// Wrong — missing return type, or returning JSX
```

---

### Server API `WebSocket connection failed`

**Cause:** Invalid API key, wrong site ID, or network blocking WSS.

**Fix:**
```bash
# Verify API key is valid
echo $FRAMER_API_KEY | head -c 20  # Should start with 'framer_sk_'

# Verify site ID
echo $FRAMER_SITE_ID

# Test WebSocket connectivity
curl -s https://api.framer.com/health || echo "Cannot reach Framer API"
```

---

### `CMS Collection field type invalid`

**Cause:** Using unsupported field type string.

**Fix:** Valid types: `string`, `formattedText`, `number`, `boolean`, `date`, `link`, `image`, `color`, `enum`, `slug`

---

### CORS Errors in Code Components

**Cause:** Fetch API in components blocked by browser CORS policy.

**Fix:** Use a CORS proxy or ensure your API returns proper `Access-Control-Allow-Origin` headers. Framer components run in the browser — same CORS rules apply.

## Quick Diagnostic

```bash
# Check if Framer API is reachable
curl -s https://api.framer.com/health

# Verify npm packages
npm list framer-plugin framer-api framer

# Check for common issues in code
grep -r "from 'framer'" src/ --include="*.tsx" | head -10
```

## Resources

- [Framer Developer Docs](https://www.framer.com/developers/)
- [Plugin Troubleshooting](https://www.framer.com/developers/plugins-introduction)
- [Framer Changelog](https://www.framer.com/developers/changelog)

## Next Steps

For debugging tools, see `framer-debug-bundle`.
