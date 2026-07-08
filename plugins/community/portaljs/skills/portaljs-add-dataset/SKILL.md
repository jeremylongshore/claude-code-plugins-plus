---
name: portaljs-add-dataset
description: Add a dataset (CSV, TSV, JSON, or GeoJSON) to an existing PortalJS portal. Appends an entry to datasets.json so the catalog and showcase render it automatically; routes the data by source (local file vs remote URL) — R2 via Git LFS by default, remote URLs by passthrough.
---

# PortalJS — Add Dataset

Add a dataset (CSV, TSV, JSON, or GeoJSON) to an existing PortalJS portal. Appends an entry to datasets.json so the catalog and showcase render it automatically; routes the data by source (local file vs remote URL) — R2 via Git LFS by default, remote URLs by passthrough.

## Usage

Invoke as the `/portaljs-add-dataset` slash command in Claude Code, or ask your agent to run the **portaljs-add-dataset** skill. The skill interviews you for any missing input rather than erroring.

## Instructions

The canonical, full step-by-step workflow for this skill lives in
[`.claude/commands/portaljs-add-dataset.md`](../../.claude/commands/portaljs-add-dataset.md) in this repository —
that file is the single source of truth. When executing this skill, read and follow it.
