---
title: "AGENTS.md as a Cross-Tool Plugin Brief: A Case Study from kobiton/automate"
description: "A 5-device parity sweep against kobiton/automate showed iOS screenshot capture ~17% faster than Android — but the more interesting finding is what an AGENTS.md file would close. A worked example of cross-tool plugin briefs done right."
date: "2026-05-11"
tags: ["claude-code", "mcp", "agents-md", "plugins", "mobile-testing", "kobiton", "parity", "devops", "appium"]
featured: false
---
# AGENTS.md as a Cross-Tool Plugin Brief: A Case Study from kobiton/automate

**TL;DR** — I ran a 5-device parity sweep against Kobiton's real-device cloud through the `kobiton/automate` Claude Code plugin. iOS screenshot capture came in ~17% faster than Android in this run. The interesting part isn't the gap — it's that the plugin doesn't document the gap, or the post-`deleteSession` cooldown, or which Appium log endpoints actually work. That's what an `AGENTS.md` file is for, and PR #10 on the repo is starting to add one. This is a worked example of what should go in it.

---

I spent last week poking at [`kobiton/automate`](https://github.com/kobiton/automate), the Claude Code plugin that fronts Kobiton's real-device cloud. Five devices, two pools, both major mobile platforms, one small WebDriverIO harness. The numbers showed something plugin authors rarely publish: iOS screenshot capture was about 17% faster than Android across the sample.

That gap isn't a bug. It's platform variance. But it's the kind of variance you want surfaced before your CI bill quietly compounds it — and surfacing things like this is exactly what a cross-tool agent brief like `AGENTS.md` is for.

## The plugin

`kobiton/automate` is a thin Claude Code plugin pointing at a remote MCP server (`https://api.kobiton.com/mcp`). The repo holds manifests, one skill, schemas, and docs. Appium still runs the driver loop once a session opens. That's the right boundary. The plugin doesn't pretend to be Appium; it just helps the agent get into a working session and back out cleanly.

The public repo currently exposes 12 MCP tools:

| Area | Tools |
|---|---|
| Devices | `listDevices`, `getDeviceStatus`, `reserveDevice`, `terminateReservation` |
| Sessions | `listSessions`, `getSession`, `getSessionArtifacts`, `terminateSession` |
| Apps | `listApps`, `uploadAppToStore`, `confirmAppUpload`, `getApp` |

Last week the team opened [PR #10](https://github.com/kobiton/automate/pull/10), which adds GitHub Copilot CLI support and an `AGENTS.md` file. Five files changed, 75 lines added. As of writing it's open and marked in testing. Most of the diff is portability work — declaring skill and MCP paths, swapping Claude-specific phrasing for neutral language, and adding the agent-facing instructions file itself.

That PR is what made me want to write this up. It's a real example of a plugin moving from "works in Claude Code" to "any reasonable coding agent can read this and behave."

## The parity sweep

The harness is small. Open an Appium session, take five screenshots, record boot wall-clock and per-screenshot p50, terminate cleanly. Five devices:

| Device pool | OS | Model | Boot ms | Screenshot p50 |
|---|---|---|---:|---:|
| PRIVATE | Android 13 | Galaxy A52s 5G | 4,206 | 353 |
| CLOUD   | Android 9  | moto g(7) play | 5,451 | 297 |
| PRIVATE | iOS 17.5.1 | iPhone XR | 5,091 | 242 |
| CLOUD   | iOS 18.6   | iPhone 14 Plus | 4,490 | 306 |
| CLOUD   | iOS 18.6.2 | iPad 9th Gen | 5,259 | 256 |

In this run:

- Boot times spread ~30%.
- Screenshot p50 spread ~46%.
- Android averaged ~325ms per screenshot.
- iOS averaged ~268ms — about 17% faster.

Five devices is not a fleet study, so don't read this as "iOS wins." What's worth noticing is that platform mattered more than pixel count. The fastest screenshot in the run came off an iPhone XR at 828×1792; the slowest came off a Galaxy A52s 5G at 1080×2400. Resolution alone didn't predict the spread.

That gap matters in CI. A 57ms screenshot delta sounds trivial until you compound it. At 100 tests × 50 runs/day × 3 screenshots per test, you've spent ~855 seconds a day, or ~7 hours a month, on the slower path. Push that to five screenshots per test and you're at ~12 hours/month. Not a redesign-the-suite number. But it's real queue time — enough that a routing decision ("send the screenshot-heavy suite to iOS first") starts paying for itself.

## Two findings an AGENTS.md would close

Two things came up that an agent-facing brief would have closed before I started.

### Endpoint compatibility

`driver.getLogs('logcat')` didn't return usable data through the endpoint my client tried. Appium's docs distinguish between `/session/:sessionId/log` and `/session/:sessionId/se/log`, and which one works depends on the driver and server. A plugin like this should just say up front which log endpoints it supports, which it rejects, and what the agent should do when log retrieval fails.

Without that, a test ported in from a vanilla Appium setup can silently lose its logs. The test still passes. The evidence is just gone. Worst kind of failure — the kind that smiles and waves while stealing your evidence.

### Lifecycle invisibility

After `deleteSession`, devices entered a brief cooldown. During the window `getDeviceStatus` reported them as `ACTIVATED` with `is_online=true` — but they couldn't actually accept a new session yet. A naive scheduler sees "ready," queues the next job, and waits.

The fix is a documented lifecycle. Names like `ready` / `reserved` / `active` / `cleanup-required` / `cooldown-required` / `offline` / `unknown`. The wording matters less than having one. If `is_online=true` doesn't mean session-ready, the plugin needs to say that out loud.

Both gaps are documentation, not code.

## Where Claude Code conventions meet AGENTS.md

If you've authored a Claude Code plugin you already know about `CLAUDE.md` (Claude-specific repo guidance) and `SKILL.md` (skill frontmatter and workflow). Neither replaces `AGENTS.md`.

`AGENTS.md` is the tool-agnostic instruction file. A briefing packet any coding agent can read: setup, conventions, testing rules, operational caveats. `SKILL.md` belongs to a different model entirely — the open AgentSkills.io spec defines its structure for reusable skills. Related, not interchangeable.

The four files compose:

| File | Purpose |
|---|---|
| `README.md` | For humans — overview and install |
| `CLAUDE.md` | Claude Code-specific guidance |
| `SKILL.md` | Skill trigger and workflow |
| `AGENTS.md` | Cross-tool operational guidance for any agent |

A strong `AGENTS.md` for an MCP-backed testing plugin should cover capabilities (what it does), costs and latency (p50/p95, screenshot timing, upload constraints, platform variance), lifecycle states (what "ready" actually means), compatibility boundaries (which Appium endpoints work, when to fall back to artifact APIs), and orchestrator requirements (what CI systems and agent runtimes need to know).

When a plugin documents that, a cost-conscious agent can make decisions instead of guessing. "This suite goes to the faster capture path." "This device needs cooldown." "This log endpoint isn't available, use artifacts." Without the spec you're guessing. With it, you're routing.

## What kobiton/automate got right

The plugin is a clean implementation of the thin-plugin / remote-MCP pattern that the AI agent ecosystem is converging on. MCP server config points to Kobiton's hosted endpoint. OAuth 2.1 is the default; API keys exist for headless CI. App uploads go through pre-signed storage URLs rather than routing binaries through the assistant. Tool schemas live as reference YAML. The `run-automation-suite` skill stays focused on guided Appium execution and doesn't try to become a test framework.

That's the right scope. A Claude Code plugin shouldn't pretend to be Appium. It should help the agent pick a target, prepare inputs, run the test, collect evidence, and report out.

PR #10 adds the cross-tool layer on top of that. It isn't a complete operational spec yet, but it's pointed in the right direction.

## What's still open

The gaps the parity sweep exposed are exactly what I'd document next:

- Supported and unsupported Appium log endpoints.
- Platform-specific log retrieval guidance.
- Device lifecycle states between "online" and "session-ready."
- Cooldown behavior after `deleteSession`.
- Retry/backoff rules for schedulers.
- Error shapes for partial success, timeout cleanup, and artifact failures.
- Latency expectations for screenshot capture and session boot.

The file doesn't have to be exhaustive on day one. It has to be honest — the operational facts an agent would otherwise learn the expensive way.

## Method note

The matrix wasn't a vibe check. Before any device touched the harness, I had three Claude sub-agents review the script in parallel — `code-reviewer`, `test-automator`, `security-auditor`. They caught:

- Orphaned cleanup on timeout.
- Partial success counted as full success in the fallback chain.
- A timing bug where a 30-second log capture window could skid by ~1.5 seconds per device under load.

Any one of those would have polluted the measurement. The cadence is reusable: specify the experiment, multi-review it, fix the harness, run the sweep, publish with caveats. Skipping the review step is how a 10-minute validation turns into a two-hour bug archaeology dig.

## A test you can run this week

If you author or consume a real-device testing plugin, run something like this against your own pool:

```python
for device in pool:
    t0 = now()
    session = create_session(device)
    wait_for_ready()
    boot_ms = now() - t0

    shots = []
    for _ in range(5):
        s = now()
        take_screenshot()
        shots.append(now() - s)

    delete_session(device)
    results[device] = {"boot": boot_ms, "shots": shots}

print_percentiles(results)
```

Five devices, five screenshots, one table. That's the baseline you can re-run whenever your pool changes — and the evidence you need to decide whether screenshot-heavy, log-heavy, or cold-start-sensitive tests should route differently.

If your platform vendor's docs don't tell you which Appium endpoints work, what session cleanup actually does, or what "online" means — that's not a docs gap. That's operational risk wearing a friendly UI.

## The takeaway

Cross-tool plugin standards aren't abstract architecture. They're the difference between

> "We picked Android arbitrarily and paid for the variance silently."

and

> "We routed the screenshot-heavy suite based on measured platform behavior."

`kobiton/automate` is moving in the right direction. Clean remote-MCP shape, focused skill design, sensible auth boundaries — and now PR #10 starts the cross-tool instruction surface.

If you author a plugin: `README.md` for humans, `CLAUDE.md` for Claude-specific bits, `SKILL.md` for skill workflow, `AGENTS.md` for everything any agent runtime needs to know. They compose; none of them replaces another.

If you consume plugins from a real-device cloud — or any AI-orchestratable platform — ask your vendor whether they publish an `AGENTS.md` or equivalent. Then ask what's in it.

If the answer is "what's that?", you found the gap.

---

**Postscript (2026-05-07).** While this post was being finalized, the `kobiton/automate` team merged Copilot CLI support ([PR #10](https://github.com/kobiton/automate/pull/10)) and opened a Phase 1 Gemini CLI extension PR ([PR #28](https://github.com/kobiton/automate/pull/28)). Both reuse the same `AGENTS.md`, the same MCP server endpoint via OAuth dynamic discovery (RFC 9728), and the same `skills/<name>/SKILL.md` convention — three CLIs against one source of truth, zero server-side code change.

The Gemini PR description is the working reference for anyone trying this pattern: `AGENTS.md` carries the cross-tool load (no separate `GEMINI.md` needed), dynamic-discovery OAuth lets the install flow piggyback off plumbing already deployed, and skills auto-discover from the canonical path so they don't need explicit manifest references. If you're authoring a plugin in 2026 and want to ship it across Claude Code, Copilot CLI, and Gemini CLI with one source tree, read those two PRs.

OpenAI Codex CLI is the natural fourth runtime in this space and fits the same pattern — `AGENTS.md` is read natively, MCP servers are declared in `~/.codex/config.toml` under `[mcp_servers.<name>]`, and the OAuth dynamic-discovery flow is identical. The only delta is the config format (TOML rather than JSON), which means a Codex extension to a multi-CLI plugin is typically just a documentation snippet — no new manifest, no new build step. Four agentic CLIs, one cross-tool surface, one MCP server. That's the convergence the AGENTS.md convention was hinting at all along.
