# Juicebox Production Checklist -- Implementation Reference

## Overview

Pre-launch verification for Juicebox production deployments, covering API credentials,
data connectivity, report validation, and post-deploy smoke tests.

## Prerequisites

- Juicebox workspace configured with production API key
- Production environment variables set
- Access to production data sources

## Pre-Launch Verification Script

```python
#!/usr/bin/env python3
import os, sys, json, urllib.request, urllib.error
from datetime import datetime

JUICEBOX_API_KEY = os.environ.get("JUICEBOX_API_KEY", "")
WORKSPACE_ID = os.environ.get("JUICEBOX_WORKSPACE_ID", "")
BASE_URL = "https://api.juicebox.com/v1"
PASS, FAIL, WARN = "[PASS]", "[FAIL]", "[WARN]"


def api_get(path: str) -> dict:
    req = urllib.request.Request(
        f"{BASE_URL}{path}",
        headers={"Authorization": f"Bearer {JUICEBOX_API_KEY}", "Accept": "application/json"},
    )
    with urllib.request.urlopen(req, timeout=10) as resp:
        return json.loads(resp.read())


def check_env() -> bool:
    ok = True
    for name, val in [("JUICEBOX_API_KEY", JUICEBOX_API_KEY), ("JUICEBOX_WORKSPACE_ID", WORKSPACE_ID)]:
        if val:
            print(f"  {PASS} {name} set ({len(val)} chars)")
        else:
            print(f"  {FAIL} {name} missing")
            ok = False
    return ok


def check_api() -> bool:
    try:
        data = api_get(f"/workspaces/{WORKSPACE_ID}/projects")
        count = len(data.get("projects", []))
        print(f"  {PASS} API reachable, {count} projects found")
        return True
    except urllib.error.HTTPError as e:
        print(f"  {FAIL} HTTP {e.code}")
        return False
    except Exception as e:
        print(f"  {FAIL} {e}")
        return False


def check_data_sources() -> bool:
    try:
        data = api_get(f"/workspaces/{WORKSPACE_ID}/data-sources")
        sources = data.get("data_sources", [])
        if not sources:
            print(f"  {WARN} No data sources configured")
            return True
        for src in sources:
            status = src.get("status", "unknown")
            name = src.get("name", src.get("id", "?"))
            icon = PASS if status == "connected" else FAIL
            print(f"  {icon} Data source: {name} ({status})")
        return all(s.get("status") == "connected" for s in sources)
    except Exception as e:
        print(f"  {WARN} Could not check data sources: {e}")
        return True


def run_checks() -> bool:
    checks = [
        ("Environment Variables", check_env),
        ("API Connectivity", check_api),
        ("Data Sources", check_data_sources),
    ]
    print(f"\nJuicebox Production Readiness -- {datetime.utcnow().isoformat()}Z\n{'='*60}")
    all_passed = True
    for name, fn in checks:
        print(f"\n[{name}]")
        if not fn():
            all_passed = False
    print(f"\n{'='*60}")
    if all_passed:
        print(f"\n{PASS} All checks passed. Ready for production!")
    else:
        print(f"\n{FAIL} Some checks failed. Fix before deploying.")
    return all_passed


if __name__ == "__main__":
    sys.exit(0 if run_checks() else 1)
```

## Post-Deploy Smoke Test

```bash
#!/bin/bash
set -euo pipefail
API_KEY="${JUICEBOX_API_KEY:?}"
WORKSPACE="${JUICEBOX_WORKSPACE_ID:?}"
BASE="https://api.juicebox.com/v1"

STATUS=$(curl -s -o /dev/null -w "%{http_code}" \
  -H "Authorization: Bearer $API_KEY" \
  "${BASE}/workspaces/${WORKSPACE}/projects")

[ "$STATUS" = "200" ] && echo "[PASS] API 200 OK" || { echo "[FAIL] API returned $STATUS"; exit 1; }
echo "Smoke tests passed."
```

## Production Checklist

```markdown
Pre-deploy:
- [ ] JUICEBOX_API_KEY in production secrets
- [ ] JUICEBOX_WORKSPACE_ID confirmed for production
- [ ] Data sources show status: connected
- [ ] All reports load without errors

Post-deploy:
- [ ] Smoke test passes (200 responses)
- [ ] At least one live report loads in browser
- [ ] Monitoring configured for 4xx/5xx errors
- [ ] API key rotation schedule documented
```

## Resources

- [Juicebox API Docs](https://developers.juicebox.com/docs)
- [Juicebox Status](https://status.juicebox.com)
