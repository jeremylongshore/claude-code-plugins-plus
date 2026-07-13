# Step 1: Token Leak Prevention

Deep-dive reference for the `figma-policy-guardrails` skill — extracted from the 'Step 1: Token Leak Prevention' step of the workflow.

```bash
# .pre-commit-config.yaml -- catch Figma tokens before commit
repos:
  - repo: local
    hooks:
      - id: no-figma-tokens
        name: Check for Figma PAT leaks
        entry: bash -c '
          if git diff --cached --diff-filter=ACM -z -- . |
             xargs -0 grep -lP "figd_[a-zA-Z0-9_-]{20,}" 2>/dev/null; then
            echo "ERROR: Figma PAT found in staged files"
            echo "Store tokens in .env files (which should be in .gitignore)"
            exit 1
          fi
        '
        language: system
        pass_filenames: false
```

```yaml
# GitHub Actions secret scanning
# .github/workflows/figma-security.yml
name: Figma Security Check
on: [push, pull_request]

jobs:
  security:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - name: Scan for Figma tokens
        run: |
          if grep -rP "figd_[a-zA-Z0-9_-]{20,}" \
            --include="*.ts" --include="*.js" --include="*.json" \
            --exclude-dir=node_modules .; then
            echo "::error::Figma PAT found in source code"
            exit 1
          fi

      - name: Check .env files not committed
        run: |
          if git ls-files --cached | grep -E '^\.(env|env\.local|env\.production)$'; then
            echo "::error::.env file committed to repository"
            exit 1
          fi
```

---
*[Tons of Skills](https://tonsofskills.com) by [Intent Solutions](https://intentsolutions.io) | [jeremylongshore.com](https://jeremylongshore.com)*
