---
title: "From Tool to Platform: IntentCAD Ships Five EPICs in One Day"
description: "cad-dxf-agent becomes IntentCAD. Multi-user auth, intent routing, region Q&A, repeated-condition detection, and diff hardening — five EPICs shipped in a single day."
date: "2026-03-06"
tags: ["ai-agents", "architecture", "python", "authentication", "full-stack"]
featured: false
---
The DXF comparison tool is dead. Long live IntentCAD.

What started as [cad-dxf-agent](https://github.com/jeremylongshore/cad-dxf-agent) — a deterministic comparison engine for engineering drawings — grew past its name. It's not just comparing files anymore. It's interpreting markup, answering questions about drawing regions, detecting repeated conditions, and managing multi-user sessions with Google auth. Calling it "cad-dxf-agent" was underselling it by a factor of five.

So it's IntentCAD now. And the rebrand wasn't cosmetic. It came with five EPICs landing in a single day across PRs #73–#82.

## The Intent Router: EPIC-CAD-02

The architectural centerpiece is the intent router (#74). Users describe what they want in natural language. The router maps that to a capability.

This isn't a chatbot wrapper. It's a contract-driven pipeline with explicit stages:

```python
class IntentRouter:
    """Maps natural language requests to registered capabilities."""

    def route(self, user_input: str, context: DrawingContext) -> RoutedIntent:
        # 1. Parse intent from natural language
        parsed = self.parser.parse(user_input)

        # 2. Match against registered capability contracts
        candidates = self.registry.match(parsed.intent_type, parsed.parameters)

        # 3. Validate preconditions (does the session have the required state?)
        viable = [c for c in candidates if c.preconditions_met(context)]

        if not viable:
            return RoutedIntent.unresolvable(parsed, reason="no matching capability")

        # 4. Select highest-priority match
        selected = max(viable, key=lambda c: c.priority)
        return RoutedIntent(capability=selected, parsed_intent=parsed)
```

Each capability declares a contract: what intent types it handles, what preconditions it requires, what it produces. The router doesn't hardcode any domain logic. Add a new capability, register its contract, and the router picks it up.

PR #75 immediately tightened these contracts against the spec. Loose type hints became strict schemas. Optional fields that should have been required got fixed. The contracts were a day old and already needed hardening — which is exactly why you write them as explicit schemas instead of implicit method signatures.

## Multi-User Workspaces: Google Auth + Allowlist

EPIC-CAD-02 also delivered multi-user support (#80). The comparison engine was built for single-user CLI sessions. A platform needs authentication, authorization, and workspace isolation.

The stack:

- **Google OAuth** for identity — no password management, no forgot-password flows
- **Firestore** for user records and workspace metadata
- **Email allowlist** for beta access control

```python
class UserManager:
    def authorize(self, google_token: str) -> User:
        # Verify token with Google
        identity = self.google_client.verify_id_token(google_token)

        # Check allowlist
        if identity.email not in self.allowlist:
            raise Unauthorized(f"{identity.email} not in beta allowlist")

        # Upsert user record
        user = self.firestore.upsert_user(
            email=identity.email,
            name=identity.display_name,
            last_login=datetime.utcnow(),
        )
        return user
```

The allowlist is the simplest access control that works for a beta. No roles, no permissions matrix, no admin panel. You're on the list or you're not. When IntentCAD goes wider, the allowlist becomes a row in Firestore with a role field. The authorization check point doesn't change.

The login page got a rebrand pass too — IntentCAD branding, clean Google sign-in button, no clutter.

## Selection + Markup Interpretation: EPIC-CAD-03

Here's where it gets interesting. PR #77 added the ability to interpret user markup on drawings.

A user circles something on a drawing. Draws an arrow. Highlights a region. EPIC-CAD-03 interprets those markup gestures as selection intents. A freehand circle around a group of entities? That's a region selection. An arrow pointing to a specific entity? That's a single-entity focus.

This is the input layer for everything downstream. You can't ask questions about a region until you can identify what the user selected. You can't detect repeated conditions until you know which condition the user is pointing at.

## Region Q&A: EPIC-CAD-04

With selection working, PR #78 delivered the vertical slice: ask questions about specific regions of a drawing.

Select a region. Ask "what fasteners are used here?" or "how many holes are in this pattern?" The system extracts entities within the selected region, builds a context from their geometry and attributes, and generates an answer.

This is the first capability that flows through the intent router end-to-end. User markup → selection interpretation → region extraction → Q&A generation. Four stages, each with its own contract, each testable in isolation.

## Text Geometry + Provenance: SIDEQUEST-CAD-67

A sidequest that turned out to matter more than expected (#79). DXF TEXT and MTEXT entities have position, but the comparison engine wasn't tracking positional accuracy with provenance.

Text in engineering drawings isn't decoration. It's dimensions, tolerances, part numbers, revision notes. If a dimension label moves from one entity to another between revisions, that's a meaningful change — not just "text moved 2 inches." The provenance tracking links text entities to the geometry they annotate, so downstream analysis knows *what* the text refers to, not just *where* it sits.

## Repeated-Condition Detection: EPIC-CAD-05

PR #81 shipped pattern detection. Engineering drawings are full of repeated elements — bolt patterns, identical cutouts, repeated detail views. When a condition changes in one instance, you need to know if it changed in all instances.

The detector identifies groups of geometrically similar entities, clusters them by spatial proximity and attribute similarity, and flags inconsistencies. If a drawing has twelve identical mounting holes and revision B changes the diameter of one, the detector flags that one as divergent from the pattern.

This is the kind of analysis that takes a human reviewer twenty minutes of careful counting. The detector does it in milliseconds and never miscounts.

## Diff Service Hardening: EPIC-CAD-06

The original comparison engine was correct but not production-hardened. PR #82 added the defensive engineering: better error messages when alignment fails, graceful handling of malformed DXF entities, timeout protection for pathological inputs, and structured logging throughout the diff pipeline.

Not glamorous. Absolutely necessary. A comparison engine that panics on a corrupted CIRCLE entity is a demo. One that logs the corruption, skips the entity, and tells you what it skipped is a product.

## The Day's Scorecard

| Metric | Value |
|--------|-------|
| PRs merged | 10 (#73–#82) |
| EPICs delivered | 5 (CAD-02 through CAD-06) |
| Sidequests | 1 (text geometry provenance) |
| Auth system | Google OAuth + Firestore + allowlist |
| New capabilities | Intent routing, markup selection, region Q&A, pattern detection |
| Rebrand | cad-dxf-agent → IntentCAD |

## Meanwhile: Braves Gets AI Narratives

Parallel track: the braves app (MLB game day dashboard) shipped three PRs of its own.

PR #19 added a pre-game intelligence view. PR #20 overhauled the AI narrative system — Gemini 2.5 Pro now generates broadcast-style game narratives with full career baseball cards for each player. PR #21 fixed a timezone bug: the schedule was using UTC for date calculation, which meant after 6 PM Central the app would show tomorrow's games instead of today's. Classic off-by-one, timezone edition.

## Also: Burning Actions Minutes

Housekeeping that had been overdue for weeks. Disabled all GitHub Actions cron schedules across 12+ repos — ai-devops-intent-solutions, git-with-intent, intent-blueprint-docs, intent-catalog, intent-genai-project-template, intent-mail, intentvision, irsb-monorepo, jeremylongshore.com, kilo, nixtla, stci.

These were scheduled workflows — daily syncs, weekly health checks, periodic builds — that ran whether anyone needed them or not. Burning Actions minutes on autopilot. Every one got a `schedule` trigger removed or the entire workflow disabled. CI still runs on push and PR. Nothing lost except the invoice.

## Also: Hustle Auth Finally Unblocked

The OTel deadlock saga from the [comparison engine post](/posts/deterministic-dxf-comparison-engine-one-day-build/) finally resolved. PRs #36–#39 merged, fixing the OpenTelemetry instrumentation that was deadlocking Firebase Auth login. And the Gemini code review setup got upgraded from a custom script to the official CLI with inline PR comments.

## From Tool to Platform

The jump from cad-dxf-agent to IntentCAD isn't a rename. It's a change in what the software *is*.

A tool compares two files. A platform lets multiple authenticated users express intent in natural language, interprets their markup on drawings, answers questions about specific regions, detects patterns across entities, and routes all of this through a contract-driven pipeline that any new capability can plug into.

Five EPICs in one day sounds aggressive. It's possible because each EPIC builds on the contracts from the one before. The intent router (EPIC-02) defines how capabilities register. Selection (EPIC-03) is a capability. Region Q&A (EPIC-04) consumes selections. Pattern detection (EPIC-05) reuses the same entity clustering. Diff hardening (EPIC-06) protects everything underneath.

Stack the contracts right and velocity compounds.

---

*Related posts:*

- [Building a Deterministic DXF Comparison Engine in One Day](/posts/deterministic-dxf-comparison-engine-one-day-build/) — the E1-E4 engine layers that IntentCAD's diff service hardens
- [Engine to Product: Three Interfaces, One Codebase](/posts/engine-to-product-three-interfaces-one-codebase/) — the CLI, API, and frontend wizard that preceded the platform pivot
- [PDF Extraction Sweep: Day of 42 Commits](/posts/pdf-extraction-sweep-day-42-commits/) — another high-velocity build day shipping a complete pipeline
