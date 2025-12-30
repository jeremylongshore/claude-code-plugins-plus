---
name: klingai-upgrade-migration
description: |
  Migrate and upgrade Kling AI SDK versions safely. Use when updating dependencies or migrating
  configurations. Trigger with phrases like 'klingai upgrade', 'kling ai migration',
  'update klingai', 'klingai breaking changes'.
allowed-tools: Read, Write, Edit, Grep
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
---

# Kling AI Upgrade & Migration

## Overview

This skill guides you through SDK version upgrades, API migrations, configuration changes, and handling breaking changes safely in Kling AI integrations.

## Prerequisites

- Existing Kling AI integration
- Version control for rollback capability
- Test environment available

## Instructions

Follow these steps for safe upgrades:

1. **Review Changes**: Check release notes for breaking changes
2. **Update Dependencies**: Upgrade SDK packages
3. **Update Code**: Adapt to API changes
4. **Test Thoroughly**: Validate all functionality
5. **Deploy Gradually**: Use canary or blue-green deployment

## Version Compatibility Matrix

```
API Version | SDK Version | Status      | EOL Date
------------|-------------|-------------|------------
v1          | 1.x         | Current     | N/A
v1-beta     | 0.x         | Deprecated  | 2025-06-01

Model Versions:
- kling-v1     -> kling-v1 (stable)
- kling-v1.5   -> kling-v1.5 (stable)
- kling-pro    -> kling-pro (stable)
```

## Breaking Changes by Version

### v1.0.0 → v1.1.0
```python
# No breaking changes
# New features:
# - Added camera_motion parameter
# - Added negative_prompt support
```

### v0.x → v1.0 (Major)
```python
# Breaking: Response structure changed

# Old (v0.x):
response = {
    "id": "job123",
    "state": "complete",  # Changed to "status"
    "result_url": "..."   # Changed to "video_url"
}

# New (v1.0):
response = {
    "job_id": "job123",   # "id" -> "job_id"
    "status": "completed", # "state" -> "status", "complete" -> "completed"
    "video_url": "..."     # "result_url" -> "video_url"
}

# Migration helper:
def migrate_response(old_response: dict) -> dict:
    """Convert v0.x response to v1.0 format."""
    return {
        "job_id": old_response.get("id"),
        "status": "completed" if old_response.get("state") == "complete" else old_response.get("state"),
        "video_url": old_response.get("result_url")
    }
```

## Migration Scripts

### Detect Current Version

```python
import requests
import os

def detect_api_version() -> str:
    """Detect which API version is being used."""
    try:
        # Try v1 endpoint
        response = requests.get(
            "https://api.klingai.com/v1/account",
            headers={"Authorization": f"Bearer {os.environ['KLINGAI_API_KEY']}"}
        )
        if response.status_code == 200:
            return "v1"
    except:
        pass

    return "unknown"

print(f"Current API version: {detect_api_version()}")
```

### Configuration Migration

```python
import json
from pathlib import Path

def migrate_config_v0_to_v1(config_path: str) -> dict:
    """Migrate configuration from v0.x to v1.0 format."""

    with open(config_path) as f:
        old_config = json.load(f)

    new_config = {
        "version": "1.0",
        "api": {
            "base_url": old_config.get("base_url", "https://api.klingai.com/v1"),
            "timeout": old_config.get("timeout", 30),
            "max_retries": old_config.get("retries", 3)
        },
        "defaults": {
            "model": old_config.get("default_model", "kling-v1.5"),
            "duration": old_config.get("default_duration", 5),
            "aspect_ratio": old_config.get("aspect_ratio", "16:9"),
            "resolution": old_config.get("resolution", "1080p")
        },
        "rate_limiting": {
            "requests_per_minute": old_config.get("rpm_limit", 60),
            "max_concurrent": old_config.get("max_concurrent", 10)
        }
    }

    # Backup old config
    backup_path = config_path + ".v0.backup"
    Path(config_path).rename(backup_path)
    print(f"Backed up old config to {backup_path}")

    # Write new config
    with open(config_path, "w") as f:
        json.dump(new_config, f, indent=2)
    print(f"Wrote new config to {config_path}")

    return new_config
```

### Code Migration

```python
import ast
import re

def find_deprecated_patterns(source_code: str) -> list:
    """Find deprecated API patterns in source code."""

    deprecated_patterns = [
        (r'\.state\b', 'Use .status instead of .state'),
        (r'result_url', 'Use video_url instead of result_url'),
        (r'"id":', 'Use "job_id" instead of "id"'),
        (r"'id':", 'Use "job_id" instead of "id"'),
        (r'\.complete\b', 'Use "completed" instead of "complete"'),
    ]

    issues = []
    lines = source_code.split('\n')

    for line_num, line in enumerate(lines, 1):
        for pattern, message in deprecated_patterns:
            if re.search(pattern, line):
                issues.append({
                    "line": line_num,
                    "code": line.strip(),
                    "issue": message
                })

    return issues

def scan_project_for_deprecations(project_path: str):
    """Scan project for deprecated patterns."""
    from pathlib import Path

    issues_by_file = {}

    for py_file in Path(project_path).rglob("*.py"):
        content = py_file.read_text()
        issues = find_deprecated_patterns(content)
        if issues:
            issues_by_file[str(py_file)] = issues

    return issues_by_file

# Run scan
issues = scan_project_for_deprecations("./src")
for file, file_issues in issues.items():
    print(f"\n{file}:")
    for issue in file_issues:
        print(f"  Line {issue['line']}: {issue['issue']}")
        print(f"    {issue['code']}")
```

## Upgrade Procedure

```python
class UpgradeProcedure:
    """Structured upgrade procedure with rollback capability."""

    def __init__(self, backup_dir: str = "./upgrade_backup"):
        self.backup_dir = Path(backup_dir)
        self.backup_dir.mkdir(exist_ok=True)
        self.rollback_steps = []

    def backup_file(self, filepath: str):
        """Backup a file before modification."""
        source = Path(filepath)
        if source.exists():
            dest = self.backup_dir / source.name
            import shutil
            shutil.copy2(source, dest)
            self.rollback_steps.append(("restore_file", str(source), str(dest)))
            print(f"Backed up {filepath}")

    def upgrade_dependency(self, package: str, version: str):
        """Upgrade a Python package."""
        import subprocess

        # Record current version for rollback
        result = subprocess.run(
            ["pip", "show", package],
            capture_output=True, text=True
        )
        if result.returncode == 0:
            for line in result.stdout.split("\n"):
                if line.startswith("Version:"):
                    old_version = line.split(":")[1].strip()
                    self.rollback_steps.append(("downgrade", package, old_version))
                    break

        # Perform upgrade
        subprocess.run(["pip", "install", f"{package}=={version}"], check=True)
        print(f"Upgraded {package} to {version}")

    def rollback(self):
        """Rollback all changes."""
        print("\nRolling back changes...")

        for step in reversed(self.rollback_steps):
            action = step[0]

            if action == "restore_file":
                _, dest, source = step
                import shutil
                shutil.copy2(source, dest)
                print(f"Restored {dest}")

            elif action == "downgrade":
                _, package, version = step
                import subprocess
                subprocess.run(["pip", "install", f"{package}=={version}"])
                print(f"Downgraded {package} to {version}")

        print("Rollback complete")

    def verify_upgrade(self) -> bool:
        """Run verification tests."""
        # Import test module and run
        try:
            # Run basic connectivity test
            response = requests.get(
                "https://api.klingai.com/v1/account",
                headers={"Authorization": f"Bearer {os.environ['KLINGAI_API_KEY']}"}
            )
            return response.status_code == 200
        except Exception as e:
            print(f"Verification failed: {e}")
            return False

# Usage
upgrade = UpgradeProcedure()

try:
    upgrade.backup_file("config.json")
    upgrade.upgrade_dependency("klingai-sdk", "1.1.0")

    if not upgrade.verify_upgrade():
        upgrade.rollback()
        print("Upgrade failed - rolled back")
    else:
        print("Upgrade successful!")

except Exception as e:
    print(f"Error during upgrade: {e}")
    upgrade.rollback()
```

## Output

Successful execution produces:
- Updated SDK and dependencies
- Migrated configuration
- Updated code patterns
- Verified functionality
- Rollback capability if needed

## Error Handling

Common errors and solutions:
1. **Import Errors**: Check package version compatibility
2. **API Errors**: Verify endpoint URLs updated
3. **Response Parsing**: Update response field names

## Examples

See code examples above for complete, runnable implementations.

## Resources

- [Kling AI Changelog](https://docs.klingai.com/changelog)
- [Migration Guide](https://docs.klingai.com/migration)
- [API Versioning](https://docs.klingai.com/versioning)
