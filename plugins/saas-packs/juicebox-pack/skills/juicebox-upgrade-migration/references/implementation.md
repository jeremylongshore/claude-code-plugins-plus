# Juicebox Upgrade Migration -- Implementation Reference

## Overview

Manage Juicebox SDK version upgrades and API migrations, including breaking change
identification, parallel testing, and incremental rollout.

## Prerequisites

- Current Juicebox SDK version documented
- Test environment with copy of production data
- Rollback plan in place

## Pre-Upgrade Audit Script

```python
#!/usr/bin/env python3
import os, glob, re, subprocess, json


def get_installed_version() -> str:
    try:
        with open("package.json") as f:
            pkg = json.load(f)
        deps = {**pkg.get("dependencies", {}), **pkg.get("devDependencies", {})}
        for k in deps:
            if "juicebox" in k.lower():
                return f"{k}@{deps[k]}"
    except FileNotFoundError:
        pass
    try:
        result = subprocess.run(["pip", "show", "juicebox"], capture_output=True, text=True)
        for line in result.stdout.splitlines():
            if line.startswith("Version:"):
                return line.split(": ", 1)[1].strip()
    except Exception:
        pass
    return "unknown"


def audit_api_usage() -> dict:
    patterns = {
        "auth_calls": r"juicebox\.auth\s*\(",
        "project_refs": r"juicebox\.project\s*\(",
        "embed_refs": r"juicebox\.embed\s*\(",
        "workspace_param": r"workspace_id",
    }
    results = {k: [] for k in patterns}
    source_files = glob.glob("**/*.py", recursive=True) + glob.glob("**/*.ts", recursive=True)
    for filepath in source_files:
        if "node_modules" in filepath or ".venv" in filepath:
            continue
        try:
            with open(filepath) as f:
                for i, line in enumerate(f, 1):
                    for name, pattern in patterns.items():
                        if re.search(pattern, line):
                            results[name].append(f"{filepath}:{i}")
        except Exception:
            pass
    return {k: v for k, v in results.items() if v}


if __name__ == "__main__":
    print(f"Installed: {get_installed_version()}")
    usage = audit_api_usage()
    if usage:
        for p, locs in usage.items():
            print(f"  {p}: {len(locs)} occurrences")
    else:
        print("No Juicebox API calls found")
```

## Feature Flag Migration

```python
import os

JUICEBOX_API_VERSION = os.environ.get("JUICEBOX_API_VERSION", "v1")


def get_projects(workspace_id: str) -> list:
    if JUICEBOX_API_VERSION == "v2":
        return _get_projects_v2(workspace_id)
    return _get_projects_v1(workspace_id)


def _get_projects_v1(workspace_id: str) -> list:
    import json, urllib.request
    req = urllib.request.Request(
        f"https://api.juicebox.com/v1/workspaces/{workspace_id}/projects",
        headers={"Authorization": f"Bearer {os.environ['JUICEBOX_API_KEY']}"},
    )
    with urllib.request.urlopen(req) as resp:
        return json.loads(resp.read()).get("projects", [])


def _get_projects_v2(workspace_id: str) -> list:
    import json, urllib.request
    req = urllib.request.Request(
        f"https://api.juicebox.com/v2/workspaces/{workspace_id}/projects",
        headers={"Authorization": f"Bearer {os.environ['JUICEBOX_API_KEY']}"},
    )
    with urllib.request.urlopen(req) as resp:
        return json.loads(resp.read()).get("data", {}).get("projects", [])
```

## Rollback Script

```bash
#!/bin/bash
PREVIOUS="${1:?Usage: $0 <previous-version>}"
npm install "juicebox@${PREVIOUS}" 2>/dev/null || pip install "juicebox==${PREVIOUS}"
export JUICEBOX_API_VERSION=v1
echo "Rolled back to Juicebox ${PREVIOUS}. Restart your app."
```

## Migration Checklist

```markdown
Before:
- [ ] Current version documented
- [ ] API usage audit run
- [ ] Test environment mirrors production
- [ ] Rollback version pinned and tested

After:
- [ ] All traffic on new version, no errors
- [ ] Remove v1 compatibility code
- [ ] Update documentation
```

## Resources

- [Juicebox API Changelog](https://developers.juicebox.com/changelog)
