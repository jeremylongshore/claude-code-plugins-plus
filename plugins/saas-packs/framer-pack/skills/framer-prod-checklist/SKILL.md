---
name: framer-prod-checklist
description: |
  Execute Framer production deployment checklist and rollback procedures.
  Use when deploying Framer integrations to production, preparing for launch,
  or implementing go-live procedures.
  Trigger with phrases like "framer production", "deploy framer",
  "framer go-live", "framer launch checklist".
allowed-tools: Read, Bash(curl:*), Grep
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
tags: [saas, framer]
compatible-with: claude-code
---

# Framer Production Checklist

## Overview

Checklist for deploying Framer plugins, code components, and Server API integrations to production.

## Checklist

### Plugin Production
- [ ] Plugin tested in Framer editor with real data
- [ ] No `console.log` calls remaining
- [ ] Error states handled (network failures, API errors)
- [ ] Loading states shown during async operations
- [ ] Plugin UI responsive at configured width/height
- [ ] All property controls have default values

### Code Components
- [ ] `export default` on all components
- [ ] `addPropertyControls` on all components
- [ ] Responsive at all viewport sizes
- [ ] No hardcoded data (use property controls or CMS)
- [ ] Error boundaries for data-fetching components
- [ ] Performance tested with large datasets

### Server API (CMS Sync)
- [ ] API key in secrets vault (not `.env`)
- [ ] CMS collection schema matches source data
- [ ] Incremental sync (not full replace every run)
- [ ] Error handling with notifications
- [ ] Publish step tested
- [ ] Rate limiting for batch operations

### Site Publishing
- [ ] Custom domain configured
- [ ] SEO meta tags on all pages
- [ ] CMS collections populated
- [ ] Code components rendering correctly in preview
- [ ] Code overrides working in published site

## Output

- Verified plugin, components, and CMS sync
- Production API key secured
- Site published and accessible

## Resources

- [Framer Publishing](https://www.framer.com/help/articles/publishing/)
- [Custom Domains](https://www.framer.com/help/articles/custom-domain/)

## Next Steps

For version upgrades, see `framer-upgrade-migration`.
