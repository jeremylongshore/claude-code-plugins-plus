---
title: "Stop Crying Wolf: A 3-Strike Gate for Uptime Monitors"
description: "Fix uptime monitor alert fatigue with a 3-strike debounce gate and real per-probe diagnostics. Stops false positives, keeps real outages visible."
date: "2026-06-08"
tags: ["devops", "monitoring", "ops", "automation"]
featured: false
---
The uptime monitor for scorecardecho.com had been screaming since April 30th. **101 state-changes logged. Roughly 70% of them were sub-60-second flaps** — transients that a single TCP probe shouldn't page the on-call for. The on-call had learned to swipe the alert away.

The noise problem was one thing. Worse: the alert told the on-call to run `docker compose up -d`. That command doesn't even apply anymore. Scorecardecho runs on the VPS now — systemd services, Caddy routing, GitHub Actions deploys. The monitor was both flapping AND wrong.

And the monitor script itself? Living in `~/bin/` on the dev box with zero version control. Next person who inherits this alert has no idea why it works that way.

## The Fix

PR intentsolutions-vps-runbook#37 shipped a straightforward set of changes:

**Move it under version control.** The script now lives at `scripts/scorecardecho-uptime-monitor.sh` in the repo. The dev box's `~/bin/` copy is a symlink. An operator reading the cron log can now find the code.

**3-strike consecutive-failure gate.** Before paging UP→DOWN, the monitor needs to fail three times in a row (roughly 3 minutes at 60-second probe intervals). A single flap or two-second timeout won't trigger the alarm. Recovery still pages on the first success.

**Real diagnostics in the alert body.** Instead of "000" when curl fails, map the exit code to a label: `dns-resolve-fail`, `tcp-connect-fail`, `request-timeout`, `tls-handshake-fail`. The on-call reads the alert and knows exactly where the fault is.

```bash
# 3-strike gate: increment FIRST, then check — so the count reflects this run's failure
failures=$((failures + 1))
echo "$failures" > "$state_file"

if (( failures >= 3 )); then
  if [[ "$prev_state" != "DOWN" ]]; then
    send_alert "$host is DOWN — ${failure_reason}" "severity=critical"
    echo "DOWN" > "$state_file"   # overwrites the count; prev_state guard stops re-alerting
  fi
fi
```

**Fix the "000000" nonsense.** Curl was printing "000" on error, and the shell fallback appended another "000". Now it prints once.

**Drop the wrong remediation.** No more `docker compose up -d`. Point to `docs/scorecardecho-outage.md` instead — a new runbook that walks the actual architecture: confirm from three vantage points, then route through backend-container / Caddy routing / VPS-down / false-positive sections.

**Document the deliberate design choice.** `docs/alert-routing.md` now explains why this monitor uses public ntfy.sh for egress. A VPS-wide outage shouldn't blind the alerting channel that reports it.

## The Smoke Test

Isolated state dir, fake TCP-refused endpoint. Confirmed: 1–2 failures never alert. 3+ failures alert exactly once. Recovery flips state cleanly. Caught a first-draft silent bug where steady-state UP didn't write the state file.

## What Didn't Ship

Phase 2–5 hardening (off-prem probe, frontend + TLS-expiry checks, final publish channel, Netdata correlation) lives under OPS-5zk / GH issue #36. Deliberately out of scope. Ship the bleeding-stopper, defer the work that needs design.

## Also Shipped

**braves** and **coastal-realty-ops** onboarded the new DevOps lead (Ope) as a SOPS age recipient — `.env.sops` re-keyed in both repos to 3 recipients (Jeremy + VPS host + Ope). No plaintext change, just the encrypted data key re-wrapped.

**claude-code-plugins** registered docs 014–016 in the databricks-pack index.

---

## Related Posts

- [Self-Expiring Report-Only CI Gates: From Advisory to Enforced](/posts/self-expiring-report-only-ci-gates/)
- [Nine Days Silent: When the Blog's Own Pipeline Stopped Publishing Itself](/posts/the-automation-that-stopped-publishing-itself/)
- [Five Silent Failures in One Day](/posts/five-silent-failures-one-day/)
