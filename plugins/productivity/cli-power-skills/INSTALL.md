# CLI Tool Installation Guide (macOS)

Install the CLI tools needed by each skill. You can install per-skill or all at once.

---

## Per-Skill Install

### data-processing
```bash
brew install jq yq gron miller xsv duckdb
```

### security-scanning
```bash
brew install trivy shellcheck sops
```

### api-testing
```bash
brew install hurl
brew install projectdiscovery/tap/httpx
```

### web-crawling
```bash
# Katana (Homebrew)
brew install katana

# Playwright, Puppeteer, Crawlee (Node.js 18+)
npm install -g playwright puppeteer crawlee
npx playwright install chromium

# Scrapy (Python, isolated env)
pipx install scrapy
```

### web-research
```bash
# Homebrew
brew install yt-dlp

# newspaper4k (Python, isolated env — needs --include-deps)
pipx install newspaper4k --include-deps
```

### python-tooling
```bash
brew install uv ruff
```

### ci-automation
```bash
brew install gh just act git-cliff restic
gh auth login
```

---

## All Tools at Once

```bash
# 1. Homebrew — core tools
brew install jq yq gron miller xsv duckdb \
  trivy shellcheck sops \
  hurl projectdiscovery/tap/httpx \
  katana \
  yt-dlp \
  uv ruff \
  gh just act git-cliff restic

# 2. Node.js (requires Node 18+)
npm install -g playwright puppeteer crawlee
npx playwright install chromium

# 3. Python (requires pipx)
pipx install scrapy
pipx install newspaper4k --include-deps

# 4. Post-install
gh auth login
```

---

## Prerequisites

| Requirement | Check | Install |
|------------|-------|---------|
| Homebrew | `brew --version` | `/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"` |
| Node.js 18+ | `node --version` | `brew install node` |
| Python 3.10+ | `python3 --version` | `brew install python` |
| pipx | `pipx --version` | `brew install pipx && pipx ensurepath` |

## Notes

- **xsv** is deprecated upstream but still installable via Homebrew. It will be disabled on 2026-04-27. Consider using `mlr` or `duckdb` as alternatives for CSV work.
- **Playwright chromium download** may fail behind corporate proxies with TLS certificate errors. Workaround: `NODE_TLS_REJECT_UNAUTHORIZED=0 npx playwright install chromium`
