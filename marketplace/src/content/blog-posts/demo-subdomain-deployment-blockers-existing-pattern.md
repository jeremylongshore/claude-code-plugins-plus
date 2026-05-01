---
title: "Five Deployment Blockers, One Breakthrough: When to Check Memory Before Reaching for New Infrastructure"
description: "Hit 5 blockers deploying a demo subdomain. Fixed them all by remembering the infrastructure already existed."
date: "2026-04-24"
tags: ["deployment", "devops", "claude-code", "automation", "infrastructure"]
featured: false
---
## The Problem

I needed to share a dental-billing MCP architecture diagram with stakeholders. Not tomorrow. Now. It was a static HTML file — should be five minutes to get it online.

Instead, I hit five sequential blockers. Each one seemed independent. Each one cost time. By the fifth, I was deep in DNS cache debugging, TTY/GPG authentication issues, and wondering if I should just build a new demo subdomain from scratch.

The breakthrough? Stop building. The subdomain already existed. Memory had it configured. I just hadn't checked my own infrastructure before jumping to solutions.

## The Setup

We'd scaffolded a private `dental-billing-mcp-demo` repo via `/repo-dress`, generated an architecture diagram as HTML, and now needed a public URL. The diagram itself was solid — nine issues in the rendering (orange line routing, mobile horizontal scroll, code blocks breaking), but that's content polish. First: get it live.

### Why Not GitHub Pages?

Normal answer: static site + GitHub Pages + done. We tried:

```bash
cd dental-billing-mcp-demo
git push
# repo settings → Pages → deploy from gh-pages branch
```

It worked. `jeremylongshore.github.io/dental-billing-mcp-demo/` was live in minutes. But the URL had GitHub branding, and stakeholders expected `*.intentsolutions.io` — our company domain. GitHub Pages is great for open-source portfolios, less so for shared infrastructure within an org.

So I pivoted: "Let me deploy this to `demo.intentsolutions.io` properly."

## The Five Blockers

### Blocker 1: GPG / TTY Lock

The Porkbun API key lives in `pass` (password-manager). To retrieve it:

```bash
pass show porkbun/api-key
```

But `pass` uses GPG, and GPG refuses to unlock keys without an interactive terminal (TTY). This Claude session runs headless. No TTY.

```
gpg: waiting for lock...
gpg: (there may be other `gpg' processes using the home directory)
```

Recovery: "Run `pass show porkbun/api-key` once in your own terminal to warm the GPG agent, then I can pick it up."

Time cost: ~30 minutes waiting for the user to manually unlock pass.

### Blocker 2: GitHub Pages 404 Cache

After generating the first demo URL (`jeremylongshore.github.io/dental-billing-mcp-demo/`), we tried upgrading the diagram. Pushed new HTML, refreshed the browser, got a 404.

GitHub Pages had cached the URL routing. The subdirectory didn't exist yet in the gh-pages branch because we hadn't finalized the structure. The cache stayed stale for 10 minutes.

Recovery: Adding a query string (`?v=2`) forced a cache-bust. Ugly, but it worked.

Time cost: ~10 minutes of "is it deployed yet?" checks.

### Blocker 3: Porkbun A-Record + Caddy + Let's Encrypt

Once the TTY issue resolved, I tried to create a new Porkbun A-record for `demo.intentsolutions.io`:

```bash
curl -X POST https://api.porkbun.com/api/json/v3/dns/create \
  -d '{
    "domain": "intentsolutions.io",
    "type": "A",
    "name": "demo",
    "content": "194.113.67.242",
    "apikey": "'$PORKBUN_API_KEY'",
    "secretapikey": "'$PORKBUN_SECRET_KEY'"
  }'
```

This worked. DNS record created. But now I need Caddy to serve it with TLS. Caddy config for `demo.intentsolutions.io`:

```
demo.intentsolutions.io {
  root * /home/jeremy/dental-billing-mcp/
  file_server
}
```

Caddy auto-provisions Let's Encrypt. But the provisioning only happens after DNS resolves. Which leads to:

### Blocker 4: DNS Cache Propagation

After creating the Porkbun A-record, my local DNS cache thought `demo.intentsolutions.io` didn't exist yet. Caddy couldn't verify domain ownership for the Let's Encrypt challenge.

```
error obtaining certificate: failed to verify certificate for demo.intentsolutions.io
```

Recovery: Wait 2–5 minutes for DNS to propagate to the server's resolver. Then retry.

Time cost: ~5 minutes of waiting + re-triggering Caddy.

### Blocker 5: DNS Propagation Still Incomplete

I shared the URL with stakeholders: "Visit https://demo.intentsolutions.io/dental-billing-mcp-architecture.html"

They pinged back: "404 — could not be resolved."

Typo? No. I had created the singular `demo.intentsolutions.io`. But the Porkbun DNS propagation was still slow. They hit a DNS server that hadn't cached the new record yet.

I tried hitting the URL myself and got the same thing: "demo.intentsolutions.io's server IP address could not be found."

Recovery: Swap to the plural form. `demos.intentsolutions.io` already existed in Porkbun — old infrastructure from months ago. It was already wired to Caddy, already had a Let's Encrypt cert. I just needed to drop the HTML file in the right directory.

## The Breakthrough

```bash
# This already existed from prior work
ls -la /home/jeremy/demos/
# -rw-r--r-- 1 jeremy jeremy ... dental-billing-mcp-architecture.html

# Caddy config (already live, auto-serving)
cat /etc/caddy/Caddyfile | grep -A 3 demos.intentsolutions.io
# demos.intentsolutions.io {
#   root * /home/jeremy/demos
#   file_server browse
# }

# DNS already pointed here
dig demos.intentsolutions.io +short
# 194.113.67.242
```

The pattern was already set up. From memory. All five blockers dissolved the moment I stopped trying to build and checked what already existed.

**Live URL:**

```
https://demos.intentsolutions.io/dental-billing-mcp-architecture.html
```

No new Porkbun records. No Caddy restart. No DNS wait. Just drop and serve.

## The Meta-Lesson

Each blocker felt independent. The TTY issue felt like a security/GPG problem. The GitHub Pages cache felt like a CDN problem. DNS propagation felt like "that's just how the internet works." The typo felt like a user error.

But they were all symptoms of the same mistake: reaching for new infrastructure (building `demo.*` from scratch) instead of checking existing infrastructure first.

When you're operating across multiple environments — headless servers, local dev machines, GitHub, DNS providers, Caddy configs — it's easy to forget what's already running. You see a new problem and build a new solution. You don't audit memory.

The fix: before scaffolding, search. Ask: "Have I done this before? What's already configured?"

```bash
# Audit what's already running on a server
ls -la /var/log/caddy/
ps aux | grep -E 'caddy|nginx|proxy'
dig $(hostname) +short

# Check your memory / prior sessions
grep -r 'demo' ~/.cache/
cat ~/.env | grep -i domain
```

This one sentence would have saved 45 minutes: "Remember, `demos.intentsolutions.io` already exists."

## Also Shipped

While the demo URL issue resolved itself, we also shipped a legal footer rollout across four sites using GetTerms.io embeds:

- `demos.intentsolutions.io` — privacy + terms + acceptable use
- `dixieroad.org` — added legal footer
- `jeremylongshore.com` — swapped manual terms to GetTerms.io embed
- `intentsolutions.io` — privacy + terms redirects

GetTerms.io auto-updates legal docs when regulations change. We don't have to maintain them per-site. One integration, four sites covered.

## Related Posts

- [Caching Strategies for Static Sites on Netlify](/posts/netlify-cache-busting/)
- [DNS Propagation Debugging: When `dig` Lies to You](/posts/dns-propagation-debugging/)
- [Caddy Auto-HTTPS: Let's Encrypt Provisioning at Scale](/posts/caddy-auto-https-lets-encrypt/)

