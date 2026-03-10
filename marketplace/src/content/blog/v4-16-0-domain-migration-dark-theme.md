---
title: "v4.16.0: Domain Migration to tonsofskills.com + Dark Theme Redesign"
description: "New primary domain, Braves Booth-inspired dark theme, production E2E tests, research page, and trading strategy backtester improvements."
date: "2026-03-07"
version: "4.16.0"
tags: ["release", "infrastructure", "design", "testing"]
featured: true
---

## What's New in v4.16.0

This release marks a major milestone: **tonsofskills.com** is now the primary domain for the marketplace, with a brand-new dark theme and production E2E testing infrastructure.

### Domain Migration

The marketplace is now live at **tonsofskills.com** with Firebase hosting and 301 redirects from the previous domain. All existing links continue to work.

### Dark Theme Redesign

The homepage received a full visual overhaul inspired by the Braves Booth design system — dark surfaces, gold accents, and a clean, modern layout built with DM Sans, Bebas Neue, and DM Mono fonts.

### Production E2E Tests

New Playwright test suite validates the live tonsofskills.com deployment across chromium, webkit, and mobile viewports.

### Research Page

A new `/research` page features 6 data-driven analysis documents covering plugin ecosystem trends and usage patterns.

### Trading Strategy Backtester Fixes

8 quality gaps addressed in the trading strategy backtester (#314):
- Stop-loss and take-profit enforcement
- Short position support for RSI, MACD, Bollinger, and MeanReversion strategies
- Settings.yaml loading with CLI override support
- Full test suite with 31 pytest tests

### Bug Fixes

- Axiom submodule converted to regular directory (fixing CI on forks)
- Mobile horizontal overflow on `/explore` page
- Badge text size and cowork plugin overflow on mobile
- Skills link to cowork page updated

### Metrics

- 50 commits since v4.15.0
- 183 files changed (+25,792 / -1,584 lines)
- Contributors: Jeremy Longshore, intentsolutions.io, clowreed, Eugene Aseev
