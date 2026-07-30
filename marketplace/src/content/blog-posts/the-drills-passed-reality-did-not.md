---
title: "The Drills Passed. Reality Did Not."
description: "Three times in one day, hermetic tests passed while production failed: Docker container naming, a mocked CLI probe, and an image missing its binary."
date: "2026-07-29"
tags: ["devops", "docker", "testing", "debugging", "ci-cd"]
featured: false
canonical: "https://startaitools.com/posts/the-drills-passed-reality-did-not/"
---
A question at 00:36 about Nostr got a flat no. Two minutes later, a question about Buzz got a qualified yes. By 23:31 there was a production relay with backups, a proven restore, and a wrapped update lane. Somewhere in those 23 hours, hermetic test drills passed. Reality did not.

## Two Decentralized Questions, Two Different Answers

The Nostr question was first. Should the system use Nostr for cross-repository continuity? The answer was no, and the reasoning was simple. Nostr's killer properties: censorship resistance, decentralized identity, no central owner. A single operator with one dev box and one VPS does not have those problems. Git commits plus Dolt per-operation history already give signed append-only events. The cross-session log already gives the cross-context bus. Nostr solves nothing the system actually needs.

Buzz came an hour later. Jack Dorsey's open-source Slack replacement, 8 days old, Apache-2.0, built for teams of humans and AI agents. The question: could it get a 49-person bench off WhatsApp, away from Slack's expense? The honest answer was "not yet." Mobile apps and push notifications are the whole game, still incomplete in developer preview. Adoption proceeded anyway. The reason was pragmatic: WhatsApp is the constraint. Slack is too expensive. Buzz is free and open, runs on a box we already own, and agents get cryptographic keys and audit trails.

By 01:09 there were dossiers on three upstream repositories, built in parallel, to judge whether contributing upstream was realistic: `block/buzz`, `element-hq/synapse`, and `element-hq/element-web`. The verdicts were sobering in a useful way. Outsider merges are rare and small almost everywhere (roughly 5 to 7 on Buzz during launch week, 9 in 90 days on Element Web beneath the renovate-bot noise), and the gates are real: Buzz requires DCO with CI enforcement, both Element repos require a signed CLA on top of it.

By 01:37 there was a plan. The relay landed on a dedicated VPS. Backups ran. The update lane was wrapped with the estate's already-drilled watchtower gate.

Then the drills lied. Three separate times. This is a recurring theme around here: two days earlier, [a CI drift watch printed a green check for a check it had silently skipped](https://startaitools.com/posts/the-day-the-green-checks-were-lying/).

## Three Failures. Same Pattern.

Every failure followed the same shape: a hermetic mock passed; the live system failed.

### Why Do Hermetic Tests Pass When Production Fails?

A hermetic test controls its own environment by replacing external dependencies with test doubles. That makes it fast and repeatable, and it is why hermetic suites are worth having. It also means the test never exercises the boundary it replaced. When the double and the real dependency disagree about a container name, a CLI flag, or the contents of an image, the test still reports green, because the disagreement lives in the seam the double was standing in for. This is a dev/prod parity problem wearing a passing test as a disguise.

Each of the three failures below is that seam, in a different place.

### Failure One: Container Names and Missing Paths

PR #284 landed the deploy updater lane. The hermetic drill passed. On the host, the scripts looked for a container named `buzz-relay`. Docker had named it `buzz-relay-1`. The repo-relative path for the notify script did not exist on the host. Estate dependency paths, same problem.

The script expected this:

```bash
docker exec buzz-relay buzz-admin stats
```

What was actually on the host:

```bash
docker ps --format '{{.Names}}' | grep buzz-relay
# buzz-relay-1
```

Compose builds a container name from the project name plus the service key plus an instance index. The project is `buzz` and the service is `relay`, so the container is `buzz-relay-1`. The string `buzz-relay` is a name nothing actually has. The mock never modeled that, because the mock was handed a container name rather than deriving one.

The same shape hit the paths. The scripts resolved the notify helper and the estate dependencies relative to the repo, which is correct on the dev box and meaningless on the host, where there is no repo. The fix was configurable paths plus a host installer, rather than vendoring the estate scripts into the Buzz lane and creating a second copy to drift.

### Failure Two: Six Bugs in the Probe

PR #288 rewrote the functional probe to use the real `nak` NIP-42 flow. The hermetic drill mocked the probe's hooks, so the actual CLI integration was never exercised. It carried six latent bugs discovered only against the live relay.

1. `--sec` must be passed explicitly. Without it, `nak` prefers its machine-default key. The probe was silently testing the wrong identity and still passing.
2. The public `wss://` path through Caddy was required. Loopback `ws://127.0.0.1:3004` returned 404.
3. Readback requires `--force-pre-auth` plus the member key. A closed relay authenticates on `REQ`.
4. `buzz-admin add-member` and `remove-member` take `--pubkey` as a flag, while `nak key public` takes the nsec as a positional argument. Piping the nsec instead fights with the `</dev/null` guard on every other call.
5. `keygen` has to emit a trailing newline. Without one, `read < <(keygen)` hits EOF and returns nonzero, which misfires the caller's "keygen failed" guard even though the key was generated fine.
6. An EXIT-trap cleanup referenced a local variable from `main()`. Under `set -u`, the variable was unbound in trap scope. Member state leaked.

Here is what the corrected probe invocation looks like:

```bash
keygen() {
  local nsec npub
  nsec="$(nak key generate </dev/null)" || return 3
  npub="$(nak key public "$nsec" </dev/null)" || return 3   # arg form, not piped
  # Trailing newline is load-bearing: `read < <(keygen)` returns nonzero at EOF
  # without it, which would misfire the caller's "keygen failed" guard.
  printf '%s %s\n' "$nsec" "$npub"
}

add_member() { docker exec "$RELAY_CONTAINER" buzz-admin add-member --pubkey "$1"; }
publish() { nak event -k 1 -c "$2" --sec "$1" --auth "$RELAY_WS" </dev/null; }
readback(){ nak req -i "$2" --sec "$1" --auth --force-pre-auth "$RELAY_WS" </dev/null; }
```

The first one is the worst, and it is worth sitting with. Without an explicit `--sec`, `nak` signs with its own machine-default key rather than the member key the probe just created. The probe was authenticating as the wrong identity and reporting green. A test that passes for the wrong reason is more dangerous than one that fails, because it spends its whole life telling you a thing you never actually verified. [The same root cause has produced false positives here before](https://startaitools.com/posts/two-false-positive-fixes-same-root-cause/).

### Failure Three: Missing Binary in the Image

PR #291 deployed the mobile pairing sidecar on production. The pinned relay image `relay-v0.2.0` ships `buzz-admin` and `buzz-relay` only. It does not contain `buzz-pair-relay`. The overlay ran the sidecar from `${BUZZ_IMAGE}`, which did not have the binary. The error was predictable: `executable file not found in $PATH`.

Because a shared `docker compose up` recreates the relay alongside the failing sidecar, an earlier attempt briefly took the production relay down. Teammates hit `WebSocket connection failed: 404 Not Found` on the mobile-QR step.

The broken compose looked like this:

```yaml
name: buzz
services:
  relay:
    image: ${BUZZ_IMAGE}
  pair-relay:
    image: ${BUZZ_IMAGE}          # BUG: this image has no buzz-pair-relay
    entrypoint: buzz-pair-relay
```

The fix: a separate image pin plus an absolute entrypoint:

```yaml
name: buzz
services:
  pair-relay:
    image: ${BUZZ_PAIR_RELAY_IMAGE:?set BUZZ_PAIR_RELAY_IMAGE to a pair-relay-capable image digest}
    entrypoint: ["/usr/local/bin/buzz-pair-relay"]
```

The regression test now fails if `BUZZ_PAIR_RELAY_IMAGE` is empty or resolves to the relay image. The container came back. The lessons stayed.

## What the Drills Actually Got Right

Not everything lied, and the difference is instructive. There were two drills that day, and they are not the same thing.

The first was the restore drill behind the backup work. It took the actual production recovery point, archive `intent-ops-buzz-prod-2026-07-29T183641Z`, and restored it into an isolated scratch project on the dev box. The `postgres.dump` file was 167 KB in `pg_dump -Fc` custom format, inside an encrypted borg repo so the estate's existing B2 off-site adapter consumes it unchanged. Every artifact carried a sha256 in the manifest. What came back:

- 40 tables restored
- The exact prod-published event `9717ccaa…` physically present in the events table
- `relay_members=1`, matching the live relay
- Media restored intact
- Relay identity stable, the same key deriving public key `35cd57ab…`
- An uninvited key still refused after restore
- Persistence surviving a container bounce

RTO came in around 3 minutes, and production stayed 4/4 healthy throughout because nothing was ever restored over it.

The second drill was a non-destructive restore verification, added later so recoverability can be proven on a schedule rather than once. It is hermetic, and it is honest about being hermetic: it resolves a borg archive, verifies every artifact against the manifest sha256s, asserts the dump is a valid `PGDMP` custom-format file, restores into a throwaway Postgres, and walks a sample of events looking for dangling media or git references. Its test suite plants the failures it claims to catch: 4/4, covering a clean restore, a tampered artifact, a planted dangling reference, and a missing archive.

That is the distinction worth taking away. The drills that lied mocked the seam under test, so the seam was never tested. The drills that told the truth ran the real `pg_dump` output through a real restore. Being hermetic was never the problem. Mocking the thing you are claiming to verify is.

## The Decisions Behind the Stack

Dedicated prod VPS over shared host. A fast-moving pre-1.0 stack must not share a failure domain with revenue workloads. The shared-host stack became permanent staging with fresh secrets, not promoted keys. Staging cannot decrypt prod's SOPS file.

`pg_dump -Fc` over copying the live datadir. A file copy of a running Postgres restores torn. Borg consumed the backup unchanged, same B2 off-site adapter.

Wrapping the updater with the estate's already-drilled watchtower gate and deploy wrapper rather than writing bespoke auto-pull logic. The auto-revert path is proven code.

CORS composed in-compose, not in SOPS. When `BUZZ_CORS_ORIGINS` is empty, the packaged Tauri desktop client fails (blocked `tauri://localhost`). This setup makes it non-empty by construction:

```yaml
environment:
  BUZZ_CORS_ORIGINS: "https://${BUZZ_DOMAIN:?set BUZZ_DOMAIN},tauri://localhost,http://tauri.localhost"
```

One change closes two gaps: the Tauri allowlist and the latent `CorsLayer::permissive()` fallback.

In-place DB restore stays human-gated on purpose. Auto-dropping a prod Postgres on every probe failure is the wrong hammer. The image auto-revert covers the common case. A bad migration is rare. An unattended destructive restore on a stale recovery point could itself lose data.

Pairing via a `/pair` path route over a dedicated subdomain. The sidecar accepts the WS upgrade on any path. A path avoids a new DNS record and cert. The base compose never advertises pairing. The overlay adds sidecar plus advertisement together. Invariant enforced.

Naming record ordered first. Two assets deliberately share the string `intent-ops-buzz`: the VPS host that runs the production relay, and a GitHub repository. The fork itself is a third thing (`intent-solutions-io/buzz`), and the contribution lab a fourth. Early planning had blurred the code fork, the lab, and the live ops lane into one bucket. That confusion is how prod credentials leak into a PR runner. Track B drew a bright line: the host is for ops, the repository is for code, and they get separate secrets, separate deploy gates, and separate audit trails. Documented first so the architecture docs could not rationalize around it.

## The Collaboration Arc

Roughly 3 sessions on intent-os, 598 turns, 985 tool calls, 54 errors recovered. Claude Fable 5 and Claude Opus 4.8 shipped 17 merged PRs on the relay stack and 6 on the fork (23 total across the two Buzz repos). Collaboration score 0.93. Separately, Claude Opus 5 ran approximately 5 sessions on claude-code-plugins, landing 7 PRs, 235 turns, 294 tool calls, score 0.72.

Two course-corrections shaped the work visibly.

19:01: "hold on on the naming." That became Track B, an authoritative naming and boundaries record ordered ahead of all architecture docs. The naming decision is in the expanded Decisions section above.

21:51: "hey man hold on are u reading the code review comments and fixing." PR #12 exists solely because of this. CodeRabbit found four findings on the merged PR #11, unread before merge. One was a security finding: the public fork's `.beads/issues.jsonl` carried prod public IP, tailnet address, prod domain, and the host age recipient. Judged not true secrets (age recipient is a public key; the IP is internet-facing; the tailnet address needs tailnet auth; domains are DNS-public), so no rotation warranted. But they did not belong in a public fork. They were removed. Dolt was re-synced so the pre-commit export cannot re-inject them. The residual (prior git history still carries them) was accepted explicitly.

The models shipped 23 merged PRs across the Buzz repos in a day. The two things that most needed a human were not code. They were a naming boundary and the discipline to read a review before merging.

Which is the same lesson as the drills, one level up. An automated gate reports on what it was pointed at. The updater drill was pointed at a mock instead of a container, so it never saw the name. The merge was gated on CI instead of on the review, so it never saw the finding. In both cases the check was green and the check was real. It was just aimed slightly to the left of the thing that mattered. Green is a claim about coverage, not about correctness, and it is worth asking what a passing check actually touched before believing it.

## Also Shipped

intent-solutions-landing added the demos site to the Resources menu. bobs-big-brain-umbrella installed audit-harness v1.3.0 with a docs-honesty linter gate plus refreshed git-sync hook shims. claude-code-slack-channel reconciled its module, test, and CI-gate counts to the actual codebase. now-lms recorded the v2.0.0 landing. claude-code-plugins continued its 127-dead-link repair and 11-internal-doc repoint work (see the 2026-07-27 post for the full story) plus a CI gate so dead paths cannot accumulate unnoticed.

---

## Related Posts

- [The Day The Green Checks Were Lying](https://startaitools.com/posts/the-day-the-green-checks-were-lying/)
- [Two False Positive Fixes, Same Root Cause](https://startaitools.com/posts/two-false-positive-fixes-same-root-cause/)
- [Stop Crying Wolf: A 3-Strike Uptime Monitor Gate](https://startaitools.com/posts/stop-crying-wolf-3-strike-uptime-monitor-gate/)

<script type="application/ld+json">
{
  "@context": "https://schema.org",
  "@type": "BlogPosting",
  "headline": "The Drills Passed. Reality Did Not.",
  "description": "Three times in one day, hermetic tests passed while production failed: Docker container naming, a mocked CLI probe, and an image missing its binary.",
  "author": { "@type": "Person", "name": "Jeremy Longshore" },
  "publisher": { "@type": "Organization", "name": "Start AI Tools", "url": "https://startaitools.com/" },
  "datePublished": "2026-07-29T09:00:00-05:00",
  "mainEntityOfPage": { "@type": "WebPage", "@id": "https://startaitools.com/posts/the-drills-passed-reality-did-not/" },
  "url": "https://startaitools.com/posts/the-drills-passed-reality-did-not/",
  "articleSection": "Technical Deep-Dive",
  "keywords": "hermetic tests, mocking, integration testing, docker compose, container naming, backup restore drill, deployment, CI/CD, debugging"
}
</script>
