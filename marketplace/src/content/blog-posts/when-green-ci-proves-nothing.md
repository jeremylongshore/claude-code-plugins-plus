---
title: "Green CI Proves Nothing: Why Your Tests Gate Zero Calls"
description: "CI dogfood for AI-agent governance went green while gating zero tool calls. Here's why a passing test proving nothing is worse than a red one."
date: "2026-06-11"
tags: ["ci-cd", "ai-agents", "testing", "claude-code", "docker", "devops"]
featured: false
---
Your test passed. It gated zero tool calls. It proved nothing.

## What the Dogfood Had to Prove

The agent-governance-plane (AGP) is a Slack-native, OSS (Apache-2.0) governance gate for Claude Code. It runs the agent inside a Docker sandbox, checks every tool call against a policy engine, gates suspicious ones through human approval in Slack, and writes each decision to an Ed25519-signed, hash-chained audit journal you can verify offline with `agp verify`. It holds no credentials. It fails closed on anything unverified. Phase B, pre-1.0.

The live-dogfood task was straightforward: prove that a REAL Claude Code harness actually obeys the gate end-to-end, not in a mock test. Three increments, each independently shippable.

Increment 1 wired the gate. A `hook-bridge.ts` parses Claude Code's PreToolUse hook (the real measured contract), asks AGP's gate over a Unix socket, and translates the verdict back. Allow = exit 0. Deny = exit 2 + reason on stderr. Fail-closed by construction: a missing verdict is never an allow.

```typescript
// allow → exit 0; deny → exit 2 with the reason on stderr (the measured contract).
const ALLOW: BridgeResult = { exitCode: 0 };
const deny = (reason: string): BridgeResult => ({ exitCode: 2, stderr: reason });

// Fail-closed: connection failure, timeout, a deny verdict, or any non-allow
// response all return a deny. A missing verdict is never an allow.
if (res.kind === "policy_verdict" && res.verdict.decision === "allow") {
  return ALLOW;
}
return deny(`AGP gate denied: ${reason}`);
```

Increment 2 placed the harness in a network-enabled Docker container with real FS/process isolation. The hook still gated every call through the host control-plane gate over a bind-mounted Unix socket. The image was hardened: `--cap-drop ALL`, `--security-opt no-new-privileges`. API key passed by name, never in argv. Live validation on a real task: Read allowed, Bash denied.

Increment 3 was the reproducible CI dogfood. A `.github/workflows/dogfood.yml` workflow runs the harness and assembles an evidence bundle: journal, pubkey, `agp verify` output, event timeline, filled AAR. All artifact, cryptographic proof — no service dependency, since the signed hash-chained journal verifies offline. Run by hand first against an actual flake in the claude-code-slack-channel repo, it worked: 95 journal events, 47 tool calls gated — Claude tried Agent, Bash, and ToolSearch (denied), then dozens of Reads (allowed). `agp verify` confirmed chain, signatures, and signed head.

## Why Not Run Claude Inside the Sandbox?

The obvious design is to run the harness inside AGP's own sandbox. That sandbox is `--network none` — an actively-verified, fail-closed default. But real Claude needs network egress to reach the model API. "Claude inside a `--network none` sandbox" is self-contradictory: the harness can't start.

So Topology B puts the harness in a *network-enabled* container with real FS and process isolation of tool execution, while every tool call still gates through the host control plane over the bind-mounted socket. The honest limitation: that container has full egress, not a model-only allowlist. A model-only egress allowlist (Topology C) is the north star — a real networking subsystem, filed as its own work, not a v0 blocker. Same class of honest limit as "Docker, not Firecracker."

The proof never depends on any of it. AGP's proof of what a governed run did is the signed, hash-chained journal, verifiable offline with the published key. No model provider, no hosted log, no third party is ever in the trust path. That independence is the moat — make provability depend on an external service and you weaken it.

## Why the Green Run Proved Nothing

The first CI dogfood run went green. It was hollow.

Zero tool calls gated. The containerized intendant — AGP's per-harness adapter, the thing that actually runs Claude under the gate — could not connect to the host-process gate socket. The bind-mounted socket existed (`ls` confirmed it), but `connect()` returned ENOENT. The run completed. The workflow passed. It had exercised nothing. Note what did *not* happen: the gate's own fail-closed guarantee never fired, because the harness never reached the gate. The hollow green lived in the CI evidence path, one layer above the policy gate.

This reproduced on a clean CI runner. That mattered. An earlier ADR (037) had blamed the dev sandbox's filesystem virtualization for the same symptom; a clean-runner repro falsified that — there was no dev sandbox left to blame. It was a real socket-sharing bug: a single process, Bun, spawning Docker and multi-mounting one Unix socket. We corrected the ADR to name the real cause, reopened the tracking issue for the container socket bug (it had been closed prematurely on the false diagnosis), and made `evidence-bundle.sh` fail closed when the gate was never exercised.

```bash
event_count=$(wc -l < "$OUT/events.txt" | tr -d ' ')
gated=$(grep -cE 'gate\.(allow|deny)' "$OUT/events.txt" 2>/dev/null || echo 0)

# ... assemble journal, pubkey, agp verify output, AAR ...

# A dogfood that gated nothing proves nothing — fail closed (no fake-green).
if [ "${gated:-0}" -eq 0 ]; then
  echo "evidence-bundle: FAIL — 0 tool calls gated; the governed run did not exercise the gate" >&2
  exit 1
fi
echo "evidence-bundle: wrote $OUT ($event_count events, $gated gated, verify rc=$verify_rc)"
```

## The Host-Path Pivot

We pivoted CI to the host path: Claude installed on the ephemeral runner, gated, signed. The runner itself is the isolation. That path works end-to-end and is genuinely reproducible. The container path (Topology B) stays the north star — the socket bug stays open, not papered over.

## Preventing Hung Runners in CI

The first host-path dogfood hung. A fresh-runner Claude produced no output before stalling — likely first-run, no-TTY behavior, not AGP. A CI dogfood must never hang. We wrapped the run in `timeout 360` and set the job `timeout-minutes: 20`, so a stuck harness fails fast instead of burning the runner.

```yaml
jobs:
  dogfood:
    timeout-minutes: 20      # a stuck harness fails the job, never burns the runner
    steps:
      # ...
      - name: Governed run
        run: |
          timeout 360 bun src/cli/index.ts run --intendant claude-code \
            --task "$TASK" --repo "$REPO"
```

## The Transferable Lesson: Assert the Work Was Done

**The transferable lesson:** an integration test that exercises zero of the thing under test is worse than a red one, because that fake-green reads as "covered" when it covered nothing. The fix is not "trust the green." It is to assert that the test did the work. For a governance gate, that assertion is `gated_count > 0`. A green check is a claim. The evidence bundle is the proof. This generalizes everywhere: any test whose green can be reached without exercising the property it claims should fail closed when the property was not exercised.

Also shipped: the sprite→intendant rename (ADR 038). Fly.io ships "Sprites" at sprites.dev—stateful sandboxes for AI agents with Claude Code as an explicit use case. A direct product/lane collision. "Intendant" is the agent-noun of Latin *intendere*, the root of *intent*, "one who executes on behalf of an authority." And the cross-repo echo: CCSC (AGP's substrate) shipped a "footgun-inversion" regression-test epic the same week, pinning fail-closed defaults (session isolation, "every policy decision is journaled—no gaps"). The same move as the no-fake-green guard: prove the safety property holds rather than trust it. This echoes the principle we follow in [honoring the gate when the verdict is inconvenient](/posts/honor-the-gate-when-the-verdict-is-inconvenient/) — the gate is only as good as your commitment to enforcing it even when it blocks your path.

**Related Posts:**

- [Honor the Gate When the Verdict Is Inconvenient](/posts/honor-the-gate-when-the-verdict-is-inconvenient/)
- [The Two Postgres Bugs the Tests Caught: A Real-DB Integration Test Case Study](/posts/postgres-approval-sink-bugs-the-tests-caught/)
- [Human-in-the-Loop Is a Delivery Guarantee, Not a UI Feature](/posts/hitl-delivery-is-a-fail-closed-exactly-once-problem/)

<script type="application/ld+json">
{
  "@context": "https://schema.org",
  "@type": "BlogPosting",
  "headline": "Green CI Proves Nothing: Why Your Tests Gate Zero Calls",
  "description": "CI dogfood for AI-agent governance went green while gating zero tool calls. Here's why a passing test proving nothing is worse than a red one.",
  "datePublished": "2026-06-11T09:00:00-05:00",
  "author": {
    "@type": "Person",
    "name": "Jeremy Longshore"
  },
  "publisher": {
    "@type": "Organization",
    "name": "Start AI Tools",
    "logo": {
      "@type": "ImageObject",
      "url": "https://startaitools.com/images/og-image.png"
    }
  },
  "articleBody": "Your test passed. It gated zero tool calls. It proved nothing. The agent-governance-plane (AGP) is a Slack-native, OSS (Apache-2.0) governance gate for Claude Code. This post explores why a passing test that exercises zero of the thing under test is worse than a red one, and how to prevent fake-green dogfood runs in CI.",
  "keywords": ["ci-cd", "ai-agents", "testing", "claude-code", "docker", "devops"]
}
</script>
