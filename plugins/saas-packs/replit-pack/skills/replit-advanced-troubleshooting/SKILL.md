---
name: replit-advanced-troubleshooting
description: |
  Debug hard Replit issues: container lifecycle, Nix build failures, deployment crashes, and memory leaks.
  Use when standard troubleshooting fails, investigating intermittent failures,
  or diagnosing complex Replit platform behavior.
  Trigger with phrases like "replit hard bug", "replit mystery error",
  "replit impossible to debug", "replit intermittent", "replit deep debug".
allowed-tools: Read, Grep, Bash(curl:*), Bash(node:*), Bash(python3:*)
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code, codex, openclaw
tags: [saas, replit, debugging, advanced]

---
# Replit Advanced Troubleshooting

## Overview
Deep debugging techniques for complex Replit issues that resist standard troubleshooting. Covers container lifecycle problems, Nix environment failures, deployment crash loops, memory leaks in constrained containers, and isolating Replit platform vs application issues.

## Prerequisites
- Shell access in Replit Workspace
- Understanding of Replit container lifecycle
- Ability to read deployment logs
- Familiarity with `.replit` and `replit.nix`

## Instructions

### Step 1: Systematic Issue Isolation
```bash
#!/bin/bash
set -euo pipefail
# replit-diagnose.sh — Layer-by-layer diagnosis

echo "=== Replit Diagnostic ==="

# Layer 1: Platform status
echo -n "1. Platform: "
curl -s https://status.replit.com/api/v2/summary.json | \
  python3 -c "import sys,json;print(json.load(sys.stdin)['status']['description'])" 2>/dev/null || \
  echo "UNKNOWN (check status.replit.com)"

# Layer 2: Nix environment
echo -n "2. Nix: "
if [ -f replit.nix ]; then
  echo "configured"
  nix-env -qaP 2>/dev/null | head -3 || echo "(nix-env not in path)"
else
  echo "NO replit.nix found"
fi

# Layer 3: Runtime
echo -n "3. Node: "
node --version 2>/dev/null || echo "N/A"
echo -n "   Python: "
python3 --version 2>/dev/null || echo "N/A"

# Layer 4: Dependencies
echo "4. Dependencies:"
npm list --depth=0 2>/dev/null | head -10 || echo "   npm: N/A"
pip list 2>/dev/null | head -5 || echo "   pip: N/A"

# Layer 5: Environment
echo "5. Environment:"
echo "   REPL_SLUG=$REPL_SLUG"
echo "   REPL_OWNER=$REPL_OWNER"
echo "   NODE_ENV=${NODE_ENV:-unset}"
echo "   DATABASE_URL=${DATABASE_URL:+SET}"
echo "   REPLIT_DB_URL=${REPLIT_DB_URL:+SET}"

# Layer 6: Resource usage
echo "6. Resources:"
echo "   Disk: $(df -h / 2>/dev/null | tail -1 | awk '{print $3 "/" $2 " (" $5 ")"}')"
echo "   Memory: $(free -m 2>/dev/null | head -2 | tail -1 | awk '{print $3 "MB / " $2 "MB"}' || echo 'N/A')"
echo "   Processes: $(ps aux 2>/dev/null | wc -l) running"

# Layer 7: Network
echo "7. Network:"
echo -n "   replit.com: "
curl -s -o /dev/null -w "%{http_code} (%{time_total}s)\n" https://replit.com
echo -n "   Database: "
if [ -n "${DATABASE_URL:-}" ]; then
  node -e "const{Pool}=require('pg');new Pool({connectionString:process.env.DATABASE_URL,ssl:{rejectUnauthorized:false}}).query('SELECT 1').then(()=>console.log('OK')).catch(e=>console.log('FAIL:',e.message)).finally(()=>process.exit())" 2>/dev/null || echo "pg not installed"
else
  echo "NOT CONFIGURED"
fi
```

### Step 2: Nix Build Failure Debugging
```bash
# When replit.nix changes cause build failures:

# 1. Check what channel provides
nix-env -qaP 2>/dev/null | grep nodejs
# Shows available Node.js package names

# 2. Common naming issues:
# pkgs.nodejs      → WRONG (ambiguous)
# pkgs.nodejs-20_x → CORRECT
# pkgs.python3     → WRONG (use pkgs.python311)
# pkgs.python311   → CORRECT

# 3. Verify current channel
grep channel .replit
# channel = "stable-24_05" is current

# 4. After fixing replit.nix, reload shell:
# Exit Shell tab, re-enter it
# Or: exec $SHELL

# 5. If packages won't install, try clearing Nix cache:
# Remove generated Nix store symlinks
rm -rf .config/nixpkgs 2>/dev/null
```

### Step 3: Container Crash Loop Debugging
```markdown
When deployment keeps crashing and restarting:

1. Check deployment logs (Deployment Settings > Logs)
   Look for:
   - "JavaScript heap out of memory" → increase VM size or fix leak
   - "Cannot find module" → dependency not installed in build step
   - "EACCES" → file permission issue
   - "EADDRINUSE" → port conflict

2. Test locally first:
   - Click "Run" in Workspace
   - Check Console tab for errors
   - Fix before deploying

3. Isolate the crash:
```

```typescript
// Add to top of entry point — crash guard with logging
process.on('uncaughtException', (err) => {
  console.error('UNCAUGHT EXCEPTION:', err.message);
  console.error('Stack:', err.stack);
  // Log the crash, then exit cleanly so Replit can restart
  process.exit(1);
});

process.on('unhandledRejection', (reason: any) => {
  console.error('UNHANDLED REJECTION:', reason?.message || reason);
  console.error('Stack:', reason?.stack || 'no stack');
});

// Log startup time
const startTime = Date.now();
console.log(`Starting at ${new Date().toISOString()}`);

// ... your app code ...

app.listen(PORT, '0.0.0.0', () => {
  console.log(`Started in ${Date.now() - startTime}ms on port ${PORT}`);
});
```

### Step 4: Memory Leak Detection
```typescript
// Replit containers have fixed memory limits. Detect leaks early.

const SAMPLE_INTERVAL = 30000; // 30 seconds
const samples: number[] = [];

setInterval(() => {
  const heapMB = Math.round(process.memoryUsage().heapUsed / 1024 / 1024);
  samples.push(heapMB);

  // Keep last 60 samples (30 minutes)
  if (samples.length > 60) samples.shift();

  // Detect sustained growth
  if (samples.length >= 10) {
    const first5 = samples.slice(0, 5).reduce((a, b) => a + b) / 5;
    const last5 = samples.slice(-5).reduce((a, b) => a + b) / 5;
    const growth = last5 - first5;

    if (growth > 50) { // 50MB growth over observation window
      console.warn(`MEMORY LEAK SUSPECTED: +${growth.toFixed(0)}MB over ${samples.length * 30}s`);
      console.warn(`Current: ${heapMB}MB, Samples: ${samples.length}`);
    }
  }

  // Emergency: approaching container limit
  if (heapMB > 450) { // Assuming 512MB container
    console.error(`CRITICAL: Heap at ${heapMB}MB — approaching container limit`);
    // Force garbage collection if available
    global.gc?.();
  }
}, SAMPLE_INTERVAL);

// Expose via health endpoint
app.get('/debug/memory', (req, res) => {
  res.json({
    current: process.memoryUsage(),
    samples: samples.slice(-10),
    trend: samples.length >= 2 ? samples[samples.length - 1] - samples[0] : 0,
  });
});
```

### Step 5: Deployment vs Workspace Differences
```markdown
Common issues where code works in Workspace but fails in Deployment:

| Behavior | Workspace (Run) | Deployment |
|----------|-----------------|------------|
| Auth headers | NOT available | Available (X-Replit-User-*) |
| Database | Development DB | Production DB |
| Secrets | All visible | Auto-synced (2025+) |
| Filesystem | Persistent during session | Ephemeral (lost on restart) |
| Port | Any, mapped by Replit | Must use PORT env var |
| NODE_ENV | Usually unset | Set in .replit [env] |

Debugging steps:
1. Log process.env at startup to compare
2. Check if deployment has all required secrets
3. Verify build step produces correct output
4. Test with actual deployment URL, not Webview
```

### Step 6: Intermittent Failure Investigation
```typescript
// Track request patterns to find intermittent issues
const requestLog: Array<{
  timestamp: number;
  path: string;
  status: number;
  duration: number;
  error?: string;
}> = [];

app.use((req, res, next) => {
  const start = Date.now();
  const originalEnd = res.end;

  res.end = function (...args: any[]) {
    const entry = {
      timestamp: Date.now(),
      path: req.path,
      status: res.statusCode,
      duration: Date.now() - start,
    };

    if (res.statusCode >= 400) {
      (entry as any).error = (res as any)._errorMessage || 'unknown';
    }

    requestLog.push(entry);
    if (requestLog.length > 1000) requestLog.shift();

    return originalEnd.apply(res, args);
  };

  next();
});

// Debug endpoint — last 50 errors
app.get('/debug/errors', (req, res) => {
  const errors = requestLog
    .filter(r => r.status >= 400)
    .slice(-50);
  res.json({
    totalRequests: requestLog.length,
    errorCount: errors.length,
    errors,
  });
});
```

## Support Escalation
```markdown
When you need Replit support:

1. Collect: run replit-diagnose.sh
2. Document: steps to reproduce, expected vs actual
3. Screenshot: deployment logs, error messages
4. Submit: replit.com/support

Include:
- Repl URL (share link)
- Deployment URL
- Error messages (full text)
- When it started happening
- What changed before the issue
```

## Error Handling
| Issue | Cause | Solution |
|-------|-------|----------|
| Works locally, fails deployed | Missing build step or secret | Check build command and secrets |
| Intermittent 503 | Autoscale cold start | Switch to Reserved VM or add keepalive |
| Nix build infinite loop | Circular dependency | Simplify replit.nix, remove unused deps |
| Memory keeps growing | Leak in request handler | Profile with /debug/memory endpoint |
| Container won't start | Crash on import | Add crash guards, check dependency versions |

## Resources
- [Replit Support](https://replit.com/support)
- [Replit Status](https://status.replit.com)
- [Replit Community](https://ask.replit.com)
- [Nix on Replit](https://docs.replit.com/programming-ide/nix-on-replit)

## Next Steps
For load testing, see `replit-load-scale`.
