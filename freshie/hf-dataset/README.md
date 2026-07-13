---
license: mit
pretty_name: Tons of Skills — Claude Code Skills + Quality Grades
size_categories:
  - 1K<n<10K
task_categories:
  - text-generation
  - text-classification
tags:
  - claude-code
  - agent-skills
  - prompts
  - code
  - developer-tools
configs:
  - config_name: default
    data_files: skills.jsonl
---

# Tons of Skills — Claude Code Skills + Quality Grades

A browsable corpus of **~3,000 Claude Code / Agent Skills** from the
[Tons of Skills](https://tonsofskills.com) marketplace, each joined with its **quality
grade and behavioral-eval verdict** from the Freshie compliance CMDB.

One row per skill: the skill's content and frontmatter **plus** its letter grade
(A–F), numeric score, and JRig behavioral-eval pass flag.

## Why the grades are here

Most "awesome skills" lists are unranked. This dataset ships the **quality signal**
alongside the content, so you can filter to A-grade skills, study what separates an A
from an F, or train/evaluate against a graded corpus. The grades come from the same
system-of-record that versions them publicly:

- **System of record:** the grades, compliance scores, and JRig verdicts are produced
  by an in-house validator + behavioral-eval harness and versioned in **Dolt**, pushed
  to the public DoltHub database
  [`jeremylongshore/freshie-inventory`](https://www.dolthub.com/repositories/jeremylongshore/freshie-inventory)
  (one tagged run per inventory pass).
- **This dataset is a regenerated *view*, not a hand-curated copy.** It is rebuilt from
  the same inventory run + the marketplace catalog every time, so it never drifts from
  the source of truth. Think of it as a published export (like a CSV snapshot), joined
  with the skill content that the compliance DB itself does not store.

## Schema

| field | description |
|-------|-------------|
| `name`, `slug`, `category`, `parent_plugin` | identity + where the skill lives |
| `description` | the skill's trigger/summary frontmatter |
| `author`, `license`, `version` | authoring metadata (per-skill license — mostly MIT) |
| `allowed_tools`, `visibility` | the tool allow-list + any visibility gating |
| `content_html` | the rendered skill body (HTML) |
| `grade`, `score` | Freshie letter grade (A–F) + numeric compliance score |
| `jrig_passed`, `jrig_tier_blocked` | JRig behavioral-eval pass flag / tier block |
| `is_stub` | flagged as a stub (thin/placeholder) by the validator |
| `inventory_run_id` | the Freshie inventory run this snapshot came from |

## Snapshot stats (this run)

- **3,008 skills**, **2,996 graded** (12 personal-prefix/edge skills ungraded).
- Grade histogram: **A 795 · B 1,033 · C 993 · D 168 · F 7**.
- Inventory run: **9**.

## Regenerate

The dataset is deterministic from the marketplace catalog + `freshie/inventory.sqlite`:

```bash
python3 freshie/scripts/build-hf-dataset.py
```

## License

Dataset tooling + the compilation: **MIT**. Per-skill content carries its own `license`
field — 2,999 of 3,008 are MIT (the rest Apache-2.0 or MIT-variant). The underlying
skill content is already publicly browsable at [tonsofskills.com](https://tonsofskills.com).

## Source

Marketplace: <https://tonsofskills.com> · Repo:
[`jeremylongshore/claude-code-plugins-plus-skills`](https://github.com/jeremylongshore/claude-code-plugins-plus-skills)
· Grades: [DoltHub `jeremylongshore/freshie-inventory`](https://www.dolthub.com/repositories/jeremylongshore/freshie-inventory).
