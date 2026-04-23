---
name: shipwright-projects
description: List and manage existing Shipwright projects
category: deployment
---

# /shipwright-projects

List and manage projects previously built with Shipwright.

## Steps

1. Scan the current directory and common project locations for Shipwright-generated projects (identified by `.shipwright` config or `product-agent` metadata).
2. Display a table of projects with name, stack, creation date, and status.
3. Offer actions: open, rebuild, enhance, or view build logs.
