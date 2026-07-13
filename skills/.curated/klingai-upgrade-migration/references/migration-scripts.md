# Migration Scripts

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
