---
title: "Design Tokens and Validator Parity: Marketplace Foundations"
description: "Replacing scattered CSS values with design tokens and realigning the SKILL.md validator with Anthropic's official spec. Two unglamorous changes that prevent real problems."
date: "2026-03-12"
tags: ["web-development", "claude-code", "architecture", "ci-cd"]
featured: false
---
Five commits today. No new features. Just foundations.

The claude-code-plugins marketplace has over 900 plugins now. At that scale, inconsistency compounds. A hardcoded color here, a drifted validator there — small gaps that widen into real problems. Today was about closing two of them.

## The Design Tokens Problem

The marketplace UI had grown organically. Every time I added a component, I'd pick a color value, a spacing value, a font size. Sometimes I'd match existing components by eyeballing the hex code. Sometimes I wouldn't.

The result: dozens of components with scattered CSS values. The same blue appeared as `#1a73e8` in one place and `#1a74e8` in another. Spacing jumped between `12px`, `14px`, and `16px` with no pattern. Want to tweak the primary color? Find-and-replace across every file and hope you caught them all.

PR #342 extracted everything into CSS custom properties:

```css
:root {
  --color-primary: #1a73e8;
  --color-primary-hover: #1557b0;
  --color-surface: #ffffff;
  --color-surface-elevated: #f8f9fa;
  --spacing-xs: 4px;
  --spacing-sm: 8px;
  --spacing-md: 16px;
  --spacing-lg: 24px;
  --font-size-sm: 0.875rem;
  --font-size-base: 1rem;
  --font-size-lg: 1.125rem;
  --radius-sm: 4px;
  --radius-md: 8px;
}
```

One file controls the entire visual language. Change `--color-primary` and every button, link, and accent updates. The contributors section got a redesign in the same PR — first real consumer of the token system.

This isn't exciting work. Nobody writes blog posts about CSS custom properties in 2026. But the alternative is a codebase where visual consistency is a manual discipline, and manual disciplines fail at scale.

## Validator Parity with Anthropic's Spec

The marketplace validates every plugin's SKILL.md before accepting it. The validator checks structure, required fields, formatting. The problem: it had drifted from Anthropic's official specification.

Fields that Anthropic required were optional in our validator. Fields we required didn't exist in the spec. Plugins could pass marketplace validation and still fail when Claude Code loaded them. Or worse — a valid plugin could fail our checks and get rejected.

This commit realigned the validator exactly with Anthropic's SKILL.md specification. Required fields match. Optional fields match. Validation errors reference the same field names the spec uses.

The practical impact: if the marketplace validator says your plugin is valid, Claude Code will accept it. That guarantee didn't exist before.

The same commit fixed edge cases in enterprise skill handling — skills with custom auth flows and scoped permissions that the base validator wasn't designed for.

## Deploy Pipeline Fixes

Two smaller commits cleaned up the Cloud Functions deployment:

**`--force` flag for artifact cleanup.** Cloud Functions accumulates old deployment artifacts. The `--force` flag on deploy now cleans them up automatically instead of letting storage costs creep.

**Non-blocking Firestore deploy.** The Firestore deploy step would fail hard if secrets weren't configured yet — a problem for fresh environments and new contributors. Now it logs a warning and continues. Secrets get configured, deploy runs again, everything connects. Graceful degradation instead of a wall.

## Skill Creator v5.0.0

The Skill Creator — the skill that creates skills — hit v5.0.0 and got a featured spotlight in the marketplace. Meta, but useful. It's consistently one of the most-installed plugins because the barrier to writing a well-structured SKILL.md from scratch is high enough that automation pays for itself immediately.

## What's Next

The design token system is a foundation. Dark mode, theme variants, accessibility improvements — all become one-file changes instead of full-codebase sweeps. The validator parity means the plugin submission pipeline is now trustworthy end-to-end. Neither change is visible to users today. Both prevent problems they'd notice tomorrow.

---

**Related Posts:**

- [Verified Plugins Program: Building a Quality Signal for the Marketplace](/blog/verified-plugins-program-quality-signal-for-the-marketplace/)
- [Scaling AI Batch Processing: Enhancing 235 Plugins with Vertex AI Gemini on the Free Tier](/blog/scaling-ai-batch-processing-enhancing-235-plugins-with-vertex-ai-gemini-on-the-free-tier/)
- [Production Release Engineering: Shipping v4.5.0](/blog/production-release-engineering-v450/)
