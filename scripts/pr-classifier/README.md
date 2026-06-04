# pr-classifier — File-level PR component detection

Given a list of files changed in a PR, emit a structured JSON object describing the contribution: which plugins, skills, agents, MCP servers, hooks, workflows, scripts, and docs are affected, plus any catalog or sources additions parsed from the diff.

Deterministic. Same input → same output, always. No network, no LLM, no I/O beyond `--file` / `--diff-file` reads and stdout JSON emission.

## Why this exists

The previous prescreen pipeline used a coarse `awk -F/ '{print $1"/"$2"/"$3}'` extractor at depth 3, which surfaced the plugin directory of any changed file. That caused doc-only PRs touching `plugins/saas-packs/<pack>/000-docs/foo.md` to drag in every skill in the pack for validator scoring — including unrelated skills that already had pre-existing C grades, which were then incorrectly attributed to the new PR as blockers. PR #823 hit this exactly.

The classifier cuts at depth 4 for skills (`plugins/<cat>/<plugin>/skills/<skill>/SKILL.md`) and only surfaces the SPECIFIC skill whose SKILL.md was modified. Pack-level changes still surface as `plugin_paths`, but the prescreen no longer fans out into every skill in the pack by default.

## Usage

### From stdin (typical CI)

```bash
git diff --name-only origin/main..HEAD | \
    python3 scripts/pr-classifier/detect_components.py --stdin
```

### From a file list

```bash
python3 scripts/pr-classifier/detect_components.py --file /tmp/pr-files.txt
```

### With diff for catalog/sources detection

```bash
python3 scripts/pr-classifier/detect_components.py \
    --stdin --diff-file /tmp/pr-diff.patch
```

### Positional

```bash
python3 scripts/pr-classifier/detect_components.py \
    plugins/security/penetration-tester/skills/auditing-npm-dependencies/SKILL.md \
    .github/workflows/validate-plugins.yml
```

### Pretty-print

```bash
... --pretty
```

## Output JSON shape

```json
{
  "contribution_types": ["plugin", "skill"],
  "plugin_paths": ["plugins/saas-packs/databricks-pack"],
  "affected_skills": ["databricks-incident-runbook"],
  "affected_agents": [],
  "affected_mcp": [],
  "affected_hooks": [],
  "catalog_additions": [
    { "name": "aomi", "source": "./plugins/crypto/aomi", "category": "crypto" }
  ],
  "sources_additions": [],
  "file_categories": { "md": 4, "json": 2 },
  "touches_workflows": false,
  "touches_frontend": false,
  "touches_scripts": false,
  "touches_tests": false,
  "unknown": false,
  "unmatched": []
}
```

All top-level lists are sorted; the dict is JSON-serializable and stable across runs.

## Contribution types

| Type          | Trigger                                                             |
| ------------- | ------------------------------------------------------------------- |
| `skill`       | A `plugins/<cat>/<plugin>/skills/<skill>/SKILL.md` file             |
| `agent`       | A `plugins/<cat>/<plugin>/agents/<agent>.md` file                   |
| `mcp`         | A `plugins/mcp/<name>/**` file, or `.mcp.json`, or `mcpServers/**`  |
| `hook`        | A `plugins/<cat>/<plugin>/hooks/hooks.json` file                    |
| `plugin`      | ANY file inside `plugins/<cat>/<plugin>/`                           |
| `catalog`     | A touch of `.claude-plugin/marketplace.{,extended.}json`            |
| `catalog_add` | An ADDITION to `marketplace.extended.json` (requires `--diff-file`) |
| `sources`     | A touch of `sources.yaml`                                           |
| `sources_add` | An ADDITION to `sources.yaml` (requires `--diff-file`)              |
| `ci`          | A `.github/workflows/*.yml`/`.yaml` file                            |
| `frontend`    | A `marketplace/src/**` file                                         |
| `script`      | A `scripts/**` file                                                 |
| `test`        | A `test_*.py` file OR anything under a `tests/` directory           |
| `doc`         | A standalone `*.md` or `*.mdx` outside any plugin                   |

A single PR can hit many types simultaneously. The output's `contribution_types` is the sorted set of types matched.

## When to extend the ruleset

Edit `rules.py`. Three steps:

1. Add a row to `RULE_DESCRIPTIONS` describing the new rule.
2. Add the detection logic to `classify_files()`.
3. Add a unit test in `tests/pr-classifier/test_classifier.py`.

Don't add detection logic without a corresponding rule description — the description IS the audit trail for why a file got classified.

## Tests

Unit + snapshot tests live at `tests/pr-classifier/test_classifier.py`. **46 tests, all deterministic.**

Run from the repo root:

```bash
python3 -m pytest tests/pr-classifier/ -v
```

Snapshot regression: real PR diffs captured at `tests/pr-classifier/fixtures/pr-<num>.{files,diff,expected.json}`. To regenerate after an intentional behavior change:

```bash
python3 scripts/pr-classifier/detect_components.py \
    --file tests/pr-classifier/fixtures/pr-823.files \
    --diff-file tests/pr-classifier/fixtures/pr-823.diff \
    --pretty > tests/pr-classifier/fixtures/pr-823.expected.json
```

The commit message must explain why the snapshot changed.

## Downstream consumers

This module is the foundation for two follow-up pieces (separate PRs):

- **PR 2** — Split `validate-plugins.yml` into per-domain workflow files with native `paths:` filters. The classifier's `contribution_types` informs which checks need to fire for any given PR.
- **PR 3** — Prescreen rewrite as single coordinator. The classifier's `affected_skills` becomes the input to the prescreen's grader, eliminating the depth-3 false-positive fan-out.
