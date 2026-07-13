# Lokalise CI Integration -- Implementation Reference

## Overview

Automate Lokalise translation sync in CI/CD pipelines using GitHub Actions,
including pull-from-Lokalise on build, push-to-Lokalise on merge, and
branch-based project switching.

## Prerequisites

- Lokalise API token with read/write access
- lokalise2 CLI installed
- GitHub Actions or similar CI platform

## GitHub Actions: Pull Translations on Build

```yaml
# .github/workflows/pull-translations.yml
name: Pull Translations from Lokalise

on:
  workflow_dispatch:
  schedule:
    - cron: '0 6 * * 1-5'  # Weekdays at 6am UTC

jobs:
  pull:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - name: Install lokalise2 CLI
        run: |
          curl -sfL https://raw.githubusercontent.com/lokalise/lokalise-cli-2-go/master/install.sh | sh
          echo "$HOME/.lokalise" >> $GITHUB_PATH

      - name: Pull translations
        env:
          LOKALISE_API_TOKEN: ${{ secrets.LOKALISE_API_TOKEN }}
          LOKALISE_PROJECT_ID: ${{ secrets.LOKALISE_PROJECT_ID }}
        run: |
          lokalise2 file download \
            --token="${LOKALISE_API_TOKEN}" \
            --project-id="${LOKALISE_PROJECT_ID}" \
            --format=json \
            --original-filenames=true \
            --directory-prefix="%LANG_ISO%" \
            --dest=src/locales/

      - name: Commit updated translations
        run: |
          git config user.name "lokalise-bot"
          git config user.email "bot@ci.example.com"
          if git diff --quiet; then
            echo "No translation changes"
          else
            git add src/locales/
            git commit -m "chore: sync translations from Lokalise"
            git push
          fi
```

## GitHub Actions: Push Translations on Merge

```yaml
# .github/workflows/push-translations.yml
name: Push Source Strings to Lokalise

on:
  push:
    branches: [main]
    paths:
      - 'src/locales/en/**'

jobs:
  push:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - name: Install lokalise2 CLI
        run: |
          curl -sfL https://raw.githubusercontent.com/lokalise/lokalise-cli-2-go/master/install.sh | sh
          echo "$HOME/.lokalise" >> $GITHUB_PATH

      - name: Push source strings
        env:
          LOKALISE_API_TOKEN: ${{ secrets.LOKALISE_API_TOKEN }}
          LOKALISE_PROJECT_ID: ${{ secrets.LOKALISE_PROJECT_ID }}
        run: |
          lokalise2 file upload \
            --token="${LOKALISE_API_TOKEN}" \
            --project-id="${LOKALISE_PROJECT_ID}" \
            --file="src/locales/en/translation.json" \
            --lang-iso=en \
            --replace-modified \
            --include-path \
            --tag-inserted-keys \
            --tag-skipped-keys-with-unchanged-value
```

## Python API-Based Sync

```python
import os
import json
import time
import urllib.request
import urllib.error

LOKALISE_API_TOKEN = os.environ["LOKALISE_API_TOKEN"]
PROJECT_ID = os.environ["LOKALISE_PROJECT_ID"]
BASE_URL = "https://api.lokalise.com/api2"


def lokalise_request(method: str, path: str, payload: dict = None) -> dict:
    headers = {
        "X-Api-Token": LOKALISE_API_TOKEN,
        "Content-Type": "application/json",
    }
    body = json.dumps(payload).encode() if payload else None
    req = urllib.request.Request(
        f"{BASE_URL}{path}",
        data=body,
        headers=headers,
        method=method,
    )
    with urllib.request.urlopen(req) as resp:
        return json.loads(resp.read())


def trigger_export(format: str = "json") -> str:
    """Request a file export and return the download URL."""
    result = lokalise_request("POST", f"/projects/{PROJECT_ID}/files/export", {
        "format": format,
        "original_filenames": True,
        "bundle_structure": "%LANG_ISO%/%FILENAME%.%FORMAT%",
    })
    # Poll for export completion
    process_id = result.get("process", {}).get("process_id")
    if not process_id:
        return result.get("bundle_url", "")

    for _ in range(30):
        time.sleep(2)
        status = lokalise_request("GET", f"/projects/{PROJECT_ID}/processes/{process_id}")
        proc = status.get("process", {})
        if proc.get("status") == "finished":
            return proc.get("details", {}).get("files", [{}])[0].get("url", "")
    raise TimeoutError("Export did not complete in time")


def get_project_languages() -> list:
    result = lokalise_request("GET", f"/projects/{PROJECT_ID}/languages")
    return result.get("languages", [])


if __name__ == "__main__":
    langs = get_project_languages()
    print(f"Project has {len(langs)} languages:")
    for lang in langs:
        print(f"  {lang['lang_iso']}: {lang['lang_name']}")
```

## lokalise.yml Config File

```yaml
# lokalise.yml -- checked into repo root
token: "${LOKALISE_API_TOKEN}"
project-id: "${LOKALISE_PROJECT_ID}"

upload:
  file: "src/locales/en/translation.json"
  lang-iso: en
  replace-modified: true
  include-path: true

download:
  format: json
  original-filenames: true
  directory-prefix: "%LANG_ISO%"
  dest: src/locales/
```

## Resources

- [Lokalise CLI Docs](https://developers.lokalise.com/reference/lokalise-cli)
- [Lokalise API Reference](https://developers.lokalise.com/reference)
- [GitHub Actions Secrets](https://docs.github.com/en/actions/security-guides/encrypted-secrets)

---
*[Tons of Skills](https://tonsofskills.com) by [Intent Solutions](https://intentsolutions.io) | [jeremylongshore.com](https://jeremylongshore.com)*
