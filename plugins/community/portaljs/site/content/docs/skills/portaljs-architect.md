---
metatitle: /portaljs-architect – Recommend a Data-Portal Architecture from Your Needs
metadescription: The /portaljs-architect skill interviews you about what you're building, what your data is, and what it's for, then recommends a concrete stack — storage, compute, catalog, access, hosting, metadata — and hands off to the build skills.
title: /portaljs-architect
description: The advisory entry point — turns three questions about your needs into a concrete, scaffoldable architecture, then hands off to the build skills.
---

`/portaljs-architect` is the **advisory** skill. Before you scaffold anything, it works out
*what* to build: from what you're building, what your data is, and what it's for, it
recommends a concrete architecture across six slots — storage, catalog, compute, access,
hosting, and metadata — then hands off to the build skills like
[`/portaljs-new-portal`](/docs/skills/portaljs-new-portal). It **decides**; it doesn't build.

It's interactive: if your brief is thin it interviews you in short rounds, echoes an
architecture brief back for confirmation, and never dead-ends on missing input — every
question has a sensible default. See the
[architecture decision framework](/docs/architecture/decision-framework) for the full
model it encodes.

## When to use it

Run it **first**, when you're unsure how to set up a portal — especially the data
infrastructure underneath it (files vs Git-LFS vs a lakehouse vs a warehouse; static vs
runtime; which metadata standard). If you already know what you want, skip straight to
[`/portaljs-new-portal`](/docs/skills/portaljs-new-portal).

## Inputs

| Input | Required | Notes |
| ----- | -------- | ----- |
| What you're building | No | Kind of portal + one or many publishers. Asked if missing. |
| Your data | No | Size, shape, update cadence, count, sensitivity. Point at files and it inspects them. |
| What it's for | No | Publishing, analytics, redistribution/harvesting, compliance. |
| Constraints | No | Team/budget, cloud preference (default Cloudflare), existing backend. |

Nothing is required — with no input it runs the four-round interview.

## What it produces

- An **architecture brief** filling six slots, with one-line reasoning per slot and any
  deviations from the opinionated default called out. The default stack is
  `git + giftless/R2 + Parquet + DuckLake + DuckDB`, static on Cloudflare Pages, with
  Frictionless metadata — kept S3-compatible so R2 is never a hard lock-in.
- An `ARCHITECTURE.md` written to your project documenting the decision.
- A **handoff**: the exact next commands (`/portaljs-new-portal` with the inferred namespace mode,
  `/portaljs-add-dataset`, `/portaljs-connect-ckan`, `/portaljs-deploy`, …), and an offer to run the first one.

## Example

```
/portaljs-architect We're a national statistics office. ~200 datasets, mostly large CSVs
(some GBs), updated quarterly, all public, and we must publish DCAT-AP for the EU
data portal.
```

It infers a multi-publisher open-data portal with analytics-grade data and harvesting
needs, and recommends **Parquet on R2 + DuckLake + DuckDB**, static on **Cloudflare
Pages**, **Frictionless + DCAT-AP** metadata, and an `owner` namespace — flagging the
DCAT export and Git-LFS ingest as designed-in but built later — then hands off to
[`/portaljs-new-portal`](/docs/skills/portaljs-new-portal).
