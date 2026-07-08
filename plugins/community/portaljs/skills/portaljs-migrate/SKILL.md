---
name: portaljs-migrate
description: Migrate (harvest) datasets between open-data platforms. Reads CKAN, a DCAT-US /data.json catalog (DKAN, ArcGIS Hub, data.gov), a DCAT / DCAT-AP RDF feed (JSON-LD, Turtle, or RDF/XML — data.europa.eu, national DCAT-AP portals, GeoDCAT-AP), Socrata, OpenDataSoft, or an ArcGIS FeatureServer, and writes them to a static PortalJS catalog (datasets.json, link-by-URL or download data files into Cloudflare R2 via Git LFS / Giftless) or pushes them into a CKAN instance over its API.
---

# PortalJS — Migrate

Migrate (harvest) datasets between open-data platforms. Reads CKAN, a DCAT-US /data.json catalog (DKAN, ArcGIS Hub, data.gov), a DCAT / DCAT-AP RDF feed (JSON-LD, Turtle, or RDF/XML — data.europa.eu, national DCAT-AP portals, GeoDCAT-AP), Socrata, OpenDataSoft, or an ArcGIS FeatureServer, and writes them to a static PortalJS catalog (datasets.json, link-by-URL or download data files into Cloudflare R2 via Git LFS / Giftless) or pushes them into a CKAN instance over its API.

## Usage

Invoke as the `/portaljs-migrate` slash command in Claude Code, or ask your agent to run the **portaljs-migrate** skill. The skill interviews you for any missing input rather than erroring.

## Instructions

The canonical, full step-by-step workflow for this skill lives in
[`.claude/commands/portaljs-migrate.md`](../../.claude/commands/portaljs-migrate.md) in this repository —
that file is the single source of truth. When executing this skill, read and follow it.
