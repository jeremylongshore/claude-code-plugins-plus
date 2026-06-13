---
title: "The Wrong Product, Built Perfectly"
description: "A new site was scaffolded, deployed, and live with valid TLS in under an hour — then declared the wrong product. The decoupling made the reversal cheap."
date: "2026-06-05"
tags: ["architecture", "devops", "claude-code", "hugo", "deployment"]
featured: false
---
A clean pipeline faithfully amplifies a requirements-level error all the way to production. Nothing in a good build process catches a misread spec. The process makes the misread arrive faster, signed, and TLS-valid.

On June 5 we stood up a new site, deployed it through the canonical VPS-as-the-home pattern, and watched it go green — valid Let's Encrypt cert, `healthz` returning 200, the whole chain — in under an hour. Then it was declared the wrong product. The entire premise was inverted in one sentence.

Here is the part worth keeping: the reversal was cheap. Not because the process was good — it was, but that's not the reason. It was cheap because the expensive, durable infrastructure had been decoupled from the product frame we'd read wrong. A 100% inversion of the product cost us content, not a rebuild. That's the thesis, and it's the only insurance that paid off.

## The build that worked

The request arrived around 09:35 local: stand up `learn.intentsolutions.io` as a "learning hub, open to public," with links out to the owner's other properties so it's "easy to know where to click for what." Deploy it the usual way.

We read "learning hub, open to public" as an outward-facing marketing property — a hub where the public comes to learn. That reading drove everything downstream.

The plan was complete and specific: an information architecture of hero → four-role audience triage → property cards → featured content → FAQ → footer. Charcoal Slate and Zinc color tokens with brutalist CTA accents. Full SEO: `<title>`, OpenGraph and Twitter meta, JSON-LD `Organization` + `WebSite` + `FAQPage` schema. The option to fan out five design subagents was on the table and declined as process theater — the IA was already specified, so the build went direct. Hold that detail; it matters later, and not in the direction you'd guess.

The execution was clean and fast. The error was entirely upstream of it.

The deploy followed the VPS-as-the-home pattern — eleven steps, every one of them touching real, durable external state. A public GitHub repo, [`jeremylongshore/learn-intentsolutions`](https://github.com/jeremylongshore/learn-intentsolutions), with the Hugo scaffold pushed. An ed25519 deploy key whose public half lands on the VPS behind a [force-command lock](https://man.openbsd.org/sshd.8), so that key can do exactly one thing and nothing else:

```
# /home/deploy/.ssh/authorized_keys on the VPS
command="/usr/local/sbin/deploy-learn-intentsolutions",no-port-forwarding,no-pty ssh-ed25519 AAAA... learn-deploy
```

The key cannot open a shell. It cannot forward a port. It triggers one script and exits. The script is the entire deploy surface:

```bash
#!/usr/bin/env bash
# /usr/local/sbin/deploy-learn-intentsolutions
set -euo pipefail
cd /srv/learn-intentsolutions/checkout
git fetch --quiet origin main
git reset --hard --quiet origin/main
hugo --minify --gc
rsync -a --delete public/ /srv/learn-intentsolutions/dist/
test -f /srv/learn-intentsolutions/dist/healthz   # fail the deploy if the build is empty
```

Then the trust plumbing — Tailscale OIDC scoped to exactly this repo, deliberately not the org wildcard:

```hcl
# Tailscale ACL — OIDC subject scoped to ONE repo
"subject": "repo:jeremylongshore/learn-intentsolutions:*"
# NOT "repo:jeremylongshore/*:*" — a prior AAR's root-cause forbids the wildcard.
# A wildcard subject means any repo in the org can assume the deploy identity.
```

Four GitHub Actions secrets set with the direct-argument form, because a prior post-mortem found zsh corrupts secrets piped through stdin:

```bash
gh secret set TS_OAUTH_CLIENT_ID    --body "$CLIENT_ID"
gh secret set TS_OAUTH_SECRET       --body "$CLIENT_SECRET"
# --body "$VALUE", never `echo "$VALUE" | gh secret set` — stdin gets mangled.
```

A Caddy block for the subdomain, a Porkbun A-record at 60-second TTL for a fast cutover, and a `.github/workflows/deploy.yml` calling the reusable `vps-deploy.yml` with `variant: static`. Eleven steps, all of them the kind of state that's annoying to create and annoying to recreate.

By every operational metric, this was a flawless ship.

## The detour

The deploy didn't go clean on the first pass, and the failure is worth a paragraph because it relocated the blame correctly.

The Caddy reload hung. Two things were wrong at once, which is the worst kind. First, `systemctl reload caddy` was timing out mid-apply — the systemd unit wrapper, not Caddy itself, was the bottleneck. Second, Let's Encrypt's [HTTP-01 ACME challenge](https://letsencrypt.org/docs/challenge-types/) couldn't complete because the DNS A-record didn't resolve yet; there was no resolvable name for the challenge to hit.

The fix was two moves. Reorder, so the DNS record exists before the reload and the ACME challenge has something to resolve:

```bash
# WRONG order: reload first, then DNS — ACME challenge has no name to hit.
# RIGHT order: DNS first, let it propagate, then reload.
porkbun-cli dns create intentsolutions.io --type A --name learn --content "$VPS_IP" --ttl 60
# ...wait for resolution...
```

And when the systemd wrapper still timed out mid-apply — leaving Caddy half-configured, HTTP routes loaded but the TLS app missing the new subject — bypass the wrapper and talk to Caddy directly:

```bash
# systemctl reload caddy → hangs, half-applies, exit 1
# caddy reload directly → returns immediately
sudo -u caddy caddy reload --config /etc/caddy/Caddyfile --adapter caddyfile
# EXIT=0
# "certificate obtained successfully for learn.intentsolutions.io"
```

That returned `0` instantly and the cert came through. The lesson inside the lesson: the systemd unit was the slow part the whole time. Caddy reloads in well under a second; the wrapper was adding the timeout. End-to-end deploy SLA is around 22 seconds once the infrastructure exists.

Site live. Valid TLS. `healthz` green. Under an hour, start to finish.

## The reversal

The clarification, when it came, was one sentence. The site was meant to be a place for the owner to study — a personal reference and notebook for AWS, Claude, Bedrock, and enterprise AI — not a public destination for an audience to learn alongside them.

Wrong product. Not wrong execution — wrong product.

Read the original phrase again: "learning hub, open to public." It has two opposite readings. One is a hub where *the public* learns — outward-facing, audience-driven, the thing we built. The other is a hub where *the owner* learns — a private notebook that happens to live on the open web. The first reading made the public the protagonist. The second makes the owner the only reader who matters.

Everything we'd built assumed the first. The four-role audience triage sorted visitors who weren't coming. The property cards pitched to a reader who didn't exist for this site. The featured-content section curated for an audience of one who didn't want to be an audience. The `FAQPage` schema answered questions nobody was going to ask. The brutalist CTA called an action that had no taker. The product layer was internally coherent and pointed entirely the wrong way.

## What the reversal cost

The frame inversion was a single commit: **+436 / −687 across 16 files.** It deleted more than it added, which is the signature of a frame inversion rather than a feature change. You don't tweak a misread product; you demolish the part that encoded the misread.

Five partials came out — `role-triage.html`, `property-cards.html`, `featured.html`, `faq.html`, `hero.html` — along with the brutalist CTA that was the old `index.html`. In came reading-optimized layouts — a `list.html` topic landing and a `single.html` note page with prev/next navigation. The CSS was rebuilt for long-form reading: a real typography scale, code blocks, tables, blockquotes, breadcrumbs. The dark theme and Inter typeface stayed because they were never the problem. We seeded a `/aws/` section with canonical reference links and the first study note, "The AWS mental model," and rewrote the project's CLAUDE.md so the operating frame became "the owner studying," not "the owner teaching."

A second commit — **+212 / −3** — fleshed the home page into a curated link directory: 122 links across Anthropic & Claude (docs, cookbook, courses, MCP, prompt caching, vision, extended thinking, Trust Center, Privacy, Commercial Terms, AUP), Amazon Bedrock (Claude-on-Bedrock, Knowledge Bases, Agents, Guardrails, Prompt Management), AWS general, Enterprise AI (PrivateLink, HIPAA, Organizations, SCPs, Control Tower, Amazon Q), and a GDPR / EU data-protection section spanning both vendors — including the sharp note that Bedrock acting as an intermediate processor is *not* in Anthropic's sub-processor list, because that relationship lives in the AWS contract, not Anthropic's.

Now the ledger that explains why this didn't hurt:

| Survived the reversal at zero cost | Discarded |
|---|---|
| GitHub repo `learn-intentsolutions` | `role-triage.html` partial |
| VPS checkout + dist directory | `property-cards.html` partial |
| Force-command deploy key | `featured.html` partial |
| Tailscale OIDC trust (repo-scoped) | `faq.html` partial + `FAQPage` schema |
| Caddy subdomain block | `hero.html` partial |
| Porkbun DNS A-record | Brutalist CTA `index.html` |
| Let's Encrypt TLS cert | ~687 lines of layouts + CSS |
| `deploy.yml` CI workflow | The entire "audience" frame |

Every expensive, durable thing survived untouched. The deploy key didn't care that the product flipped. The TLS cert is for a domain, not a design. The CI workflow ships whatever is in `public/`. What got thrown away was the cheap, reversible layer — markup, partials, copy. The whole reversal was about an hour of content rework. Not a rebuild from zero.

## Why a clean pipeline can't save you

This is the structural point, and it's the reason the post exists.

The error lived at the requirements layer. The pipeline below it was faithful — and faithful is exactly the problem. A high-quality pipeline does not catch a misread spec. It executes the misread perfectly and hands you the wrong thing at production grade. We've watched the same shape from a different angle — [a React app whose container shipped the Vite dev server to every visitor](/posts/vite-dev-server-in-production-the-871-byte-tell/), green health checks and all. Every downstream step compounded the original reading: the plan assumed an audience, the IA sorted that audience, the schema described that audience, the deploy shipped it to that audience. Each step was correct relative to the one above it, and the one at the very top was wrong.

The five declined design subagents are the tell. People reach for "more process at the execution layer" as the fix for shipping the wrong thing. It isn't. Those five subagents would have made the *audience* version more beautiful — better triage copy, tighter property cards, a more polished FAQ. They would have polished the wrong product. Spending more at the execution layer when the defect is at the requirements layer just buys you a higher-fidelity mistake.

Declining them was the right call. It made the build fast, and the speed didn't cause the miss — the miss was already baked in before the first subagent could have run. Execution-layer process spends its budget improving an artifact you've already committed to. It pays off only when the artifact is the right one. The cheap save here was never available at the execution layer; it was one clarifying question at the spec layer, which costs a sentence.

## The principle: couple to what you trust

When you build something speculative — a new property, a first cut, anything where the spec might be a misread — the risk question is not "will I get the spec right?" You might not. The honest question is: **what did I couple to the part I might get wrong?**

Couple the expensive-and-durable to the cheap-and-reversible and a misread spec becomes a demolition — the blast radius is the whole system. Decouple them and the same misread is contained to the product layer: a content edit. That's the entire move:

- **Expensive and durable** — repo, deploy key, OIDC trust, domain, DNS, TLS, CI. Annoying to build, annoying to rebuild. Make it product-agnostic.
- **Cheap and reversible** — IA, layouts, partials, copy, schema, color. Easy to throw away and redo.

The VPS-as-the-home pattern is product-agnostic *by design* — it ships whatever is in `public/` to whatever domain you point it at. It never knew or cared whether the site was a marketing hub or a private notebook. That indifference is the feature. Because the durable layer didn't encode the product frame, flipping the frame couldn't damage it.

So the takeaway, stated flat: **decouple the parts you can't cheaply rebuild from the parts you might have read wrong.** Then being wrong costs you content, not infrastructure.

### Tradeoffs, honestly

Decoupling is not free. The generic VPS-as-the-home pattern is more ceremony than `scp -r public/ server:/var/www`. Force-command keys, repo-scoped OIDC, reusable workflows, DNS-before-reload ordering — that's real setup overhead, and most of it is invisible until the day you're wrong. If you're never wrong about a spec, you paid for insurance you didn't use. The payoff is asymmetric: small, constant cost; large, occasional save. On a speculative build, where "wrong spec" is a live possibility, the trade is worth it.

And don't draw the wrong conclusion about the five design subagents we declined in the planning stage. Building direct was correct. The fix for this miss is not "use more agents" or "add a design review stage." Both spend at the execution layer, which is the wrong layer. The fix is a cheap clarifying question at the spec layer — "open to public, meaning the public reads it, or meaning it's your notebook that's publicly visible?" — which was one sentence away the entire time. Heavier execution is the expensive cure for a cheap disease.

## Also shipped

**agent-governance-plane** released v0.1.44, anchored by a 546-line competitive-landscape analysis that did something most competitive docs don't: it corrected the project's own prior claims. A competitor's audit log turned out to be Merkle + HMAC — symmetric — not "merely tamper-evident" as we'd characterized it, which means the real differentiator isn't "they don't sign," it's that our signing is asymmetric and publicly verifiable via Ed25519. The doc also pinned the EU AI Act high-risk obligations to the date set by the [May 2026 Digital Omnibus agreement](https://www.consilium.europa.eu/en/press/press-releases/2026/05/07/artificial-intelligence-council-and-parliament-agree-to-simplify-and-streamline-rules/) — 2027-12-02, pending Official Journal publication — rather than the often-cited 2026 deadline. The discipline worth naming: a competitive document is more useful when it corrects your own marketing than when it flatters it.

**intentsolutions-vps-runbook** got its production alerting rebuilt ntfy-first. Six topics — health, uptime, backups, deploys, security, incidents — where routine alerts go to ntfy only and high/urgent plus every security event also hit Slack. The root cause of the old single-channel firehose was unglamorous: a `SLACK_WEBHOOK_FIREHOSE` variable was never set, so every alert fell back to one webhook. The rebuild added an `llm_normalize()` step (Groq → NVIDIA → raw passthrough fallback chain, hard 6-second timeout so it never blocks an alert) to render alerts in plain English, plus a 398-line operator handover packet for a new DevOps owner.

## Related posts

- [The Vite Dev Server in Production: The 871-Byte Tell](/posts/vite-dev-server-in-production-the-871-byte-tell/) — another story of shipping the wrong thing to production cleanly, and the small artifact that finally gave it away.
- [Server-Ops MCP: Safety Before Tools](/posts/server-ops-mcp-safety-before-tools/) — the same instinct as the force-command deploy key: constrain the blast radius before you hand anything the keys.
- [Self-Expiring, Report-Only CI Gates](/posts/self-expiring-report-only-ci-gates/) — on putting process spend where it actually pays instead of where it feels productive.

<script type="application/ld+json">
{
  "@context": "https://schema.org",
  "@type": "BlogPosting",
  "headline": "The Wrong Product, Built Perfectly",
  "description": "Why a misread specification arrives faithfully at production — and how decoupling durable infrastructure from the product frame makes a total reversal cost content, not a rebuild.",
  "author": { "@type": "Person", "name": "Jeremy Longshore" },
  "publisher": { "@type": "Organization", "name": "Start AI Tools" },
  "datePublished": "2026-06-05T08:00:00-05:00",
  "dateModified": "2026-06-05T08:00:00-05:00",
  "url": "https://startaitools.com/posts/the-wrong-product-built-perfectly/",
  "keywords": "architecture, devops, claude-code, hugo, deployment, requirements, infrastructure decoupling, blast radius"
}
</script>
