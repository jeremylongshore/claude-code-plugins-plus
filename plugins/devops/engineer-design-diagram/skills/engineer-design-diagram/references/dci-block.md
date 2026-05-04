# DCI Block Reference

Catalog of Dynamic Context Injection commands used at skill activation. Each entry lists the command, the expected output size, and the fallback strategy. Total inline DCI budget: **~4.5 KB**.

## Table of Contents

- [Inline DCI Commands](#inline-dci-commands)
- [Lazy Harvester (`collect_dci.sh`)](#lazy-harvester-collect_dcish)
- [Size Budgets](#size-budgets)
- [Output Truncation Strategy](#output-truncation-strategy)

## Inline DCI Commands

These run at skill activation, in order. Each ends with a fallback that handles the not-installed / not-found case cleanly.

| # | Command | Expected size | Purpose |
|---|---------|---------------|---------|
| 1 | `git rev-parse --show-toplevel` | ~60 B | Confirm git repo + root path |
| 2 | `git rev-parse --short HEAD; git branch --show-current` | ~100 B | SHA + branch for fingerprint metadata |
| 3 | `ls package.json pyproject.toml Cargo.toml go.mod requirements.txt docker-compose.yml Dockerfile` | ~200 B | Manifest presence probe |
| 4 | `jq -r '.name,.dependencies // {} | keys[]?' package.json` | ~800 B (capped) | Node dep list for role inference |
| 5 | `docker compose config --services` | ~400 B | Docker service enumeration |
| 6 | `find . -maxdepth 3 -type d -name k8s/kubernetes/manifests` | ~200 B | k8s manifest dir discovery |
| 7 | `find . -maxdepth 3 -name '*.tf'` | ~400 B | Terraform file discovery |

All commands have `2>/dev/null` + `|| echo "fallback message"` — the skill never sees an error, just a known string it can branch on.

## Lazy Harvester (`collect_dci.sh`)

When inline DCI signals that heavy data is available (manifests exist, k8s dir found, terraform present), the skill calls `scripts/collect_dci.sh` to fetch bounded extras. The harvester:

- Caps each section at its documented byte limit
- Outputs a single JSON document to stdout
- Respects `.gitignore` via `git ls-files`
- Skips binaries

Extras it collects:

| Section | Upstream command | Cap |
|---------|------------------|-----|
| `git_files` | `git ls-files '*.ts' '*.tsx' '*.js' '*.py' '*.go' '*.rs'` | 500 paths |
| `compose_full` | `docker compose config` (full YAML) | 40 KB |
| `k8s_resources` | Per file: `yq '.kind, .metadata.name'` | 20 resources |
| `terraform_state` | `terraform show -json` if state present | 80 KB |

Skill reads only the sections it needs for the current mode.

## Size Budgets

Stay under these caps to avoid context bloat:

| Surface | Budget |
|---------|--------|
| Inline DCI block (SKILL.md activation) | 4.5 KB total |
| Any single inline command | 1 KB |
| Lazy harvester JSON output | 128 KB total |
| Per-harvester-section | documented in table above |

If a section exceeds its cap, the harvester emits `{"section": "...", "truncated": true, "reason": "size cap"}` so the skill knows to treat results as a sample, not a complete list.

## Output Truncation Strategy

When DCI output is truncated:

1. **Don't retry with a higher limit** — caps exist to protect context.
2. **Treat the output as a sample** — "here are the first 500 source files; the full count is N".
3. **Surface truncation in the final diagram's legend** — e.g., "Showing 150 of 500 source files; see fingerprint for complete list."
4. **Fingerprint always stores the complete node/edge set** — even when the rendered SVG shows only the top-150 subset.
