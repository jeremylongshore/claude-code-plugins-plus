---
title: "Do Not Blindly Restart: Designing a Self-Healing Watchdog That Stays Honest"
description: "A burn-in watchdog latched on a phantom io spike. The fix: fail-closed self-healing that restarts an allowlist, latches everything else, and never trusts one sample."
date: "2026-07-20"
tags: ["observability", "devops", "automation", "architecture"]
featured: false
---
A self-healing system that restarts blindly is an outage generator with extra steps.

On 2026-07-20 a burn-in watchdog guarding the SigNoz observability stack hard-latched and paged. The stack was fine. The breach was a phantom. That failure exposed two design defects that show up in almost every monitoring system built in a hurry: a watchdog that restarts blindly, and a monitor that lies about its own success. Both come back to the same rule: infrastructure that watches for failure has to be more honest about failure than the thing it watches.

## The problem: a phantom latch

The burn-in watchdog exists to prove a freshly deployed container is stable before promotion. It polls pressure-stall (PSI) metrics for memory and io, and if a resource crosses a ceiling it stops the burn-in, latches, and pages a human. That last part matters: a latch is a hard stop. Nothing recovers on its own after a latch. Someone gets woken up.

The 2026-07-20 page fired on io PSI. Root cause: a ClickHouse background-merge io burst, sub-10-seconds long, against a baseline io of roughly 0.00. The check that caught it looked like this:

```bash
# The bad check: single sample, no duration, hard ceiling
psi_io=$(read_psi_io_avg10)
if awk "BEGIN{exit !($psi_io >= 1.0)}"; then
  latch "io PSI breach: ${psi_io}%"   # hard stop + page
fi
```

One sample. One threshold. No sense of time. A transient merge that lasted less than ten seconds tripped a hard stop on a stack that was never in trouble. The watchdog was not measuring saturation. It was measuring a spike and calling it saturation.

## Why not just raise the threshold

The obvious fix is to bump `1.0` to something higher and move on. That is the wrong fix, and it is worth being precise about why.

A blanket raise trades one failure mode for a worse one. Raise the io ceiling high enough that a merge burst no longer trips it, and you have also raised it past the point where a real, sustained io saturation would trip it. You do not get fewer false pages. You get false pages replaced by missed real incidents, which is the failure mode a watchdog exists to prevent. Raising the number makes the monitor quieter, not more correct. A quiet monitor that misses saturation is worse than a noisy one, because you trust it.

The actual problem was never the height of the ceiling. It was that the check had no concept of duration. A spike and a sustained load produce the same instantaneous PSI reading. The only thing that separates them is time. So the fix is time, applied per resource:

```bash
# Duration-tolerant io check: a spike is logged and ignored,
# sustained pressure confirms and trips.
psi_io_avg10=$(read_psi_io_avg10)
psi_io_avg60=$(read_psi_io_avg60)
if awk "BEGIN{exit !($psi_io_avg10 >= 15.0)}" \
   && awk "BEGIN{exit !($psi_io_avg60 >= 5.0)}"; then
  breach "io PSI sustained: avg10=${psi_io_avg10}% avg60=${psi_io_avg60}%"
else
  log "io PSI transient ignored: avg10=${psi_io_avg10}%"
fi
```

The io ceiling now requires `avg10 >= 15%` AND `avg60 >= 5%`. Yes, the avg10 number itself moved from 1.0 up to 15, and that is not the blanket raise the last section warned against. The 1.0% single-sample line was never a saturation boundary in the first place, it sat down in the noise floor where a routine merge lives, so it was destined to fire on nothing. Raising it alone would still miss a real event. The avg60 term is what makes the higher ceiling honest instead of just quieter: it is the confirmation window. A sub-10-second merge cannot move a 60-second average past 5%, so it gets logged and ignored. A genuine io saturation holds both windows and trips. The fix was never a bigger number, it was a bigger number that a spike cannot reach.

Memory PSI kept its single-sample `avg10 < 1.0%` rule on purpose. Memory baseline is 0.00 and a memory floor breach is the kind of thing you want to latch fast, so the fast latch there is deliberate, filed as an advisory item rather than "fixed." That is the point of per-resource ceilings: io needs duration tolerance, memory does not, and a blanket policy would get one of them wrong.

## The redesign: classify, then bound, then latch

Raising thresholds was never going to be enough, because the deeper defect was structural. The old watchdog had exactly one response to any breach: stop and page. It could not tell a recoverable hiccup apart from a permanent fault, so it treated everything as permanent. The redesign gives it a decision: classify the breach, restart if it is on a known-safe allowlist, latch if it is anything else, and stop restarting before restarting becomes the outage.

Four conditions landed, each closing a specific way a self-healer can hurt you.

### C1: Fail-closed classifier

RECOVERABLE is an allowlist, not a denylist. Exactly two reasons are recoverable: `c8-unhealthy` and `staging-restart-anomaly`. Everything else latches immediately: a RAM floor, disk, the data tree, a memory-PSI breach, a prod-unhealthy signal, an unexpected listener (that is a security event), and critically any reason the classifier has never seen.

```bash
classify_breach() {
  case "$1" in
    c8-unhealthy|staging-restart-anomaly) echo "RECOVERABLE" ;;
    *)                                    echo "NON_RECOVERABLE" ;;
  esac
}
```

The default arm is the whole design. A denylist would restart on anything it forgot to name. This allowlist latches on anything it does not explicitly bless. When someone adds a new breach reason next quarter and forgets to classify it, the watchdog latches and pages instead of restarting into an unknown state. That is fail-closed: the unknown path is the safe path. Do not blindly restart.

### C2: Slow-flap guard

A container that restarts, looks healthy, then breaches again an hour later can loop for days, each cycle a small outage. `BI_MAX_LIFETIME_RECOVERIES=3` caps lifetime recoveries per burn-in. After the cap, a recoverable breach latches instead of restarting forever. Recovery is bounded, not infinite.

### C3: Health poll, not snapshot

A restarted container is not healthy the instant it comes up. Verifying health with a single snapshot can latch a container that is still starting. `verify_healthy` polls up to `BI_HEALTH_TIMEOUT=120s`, requiring staging active AND C8 healthy, before it decides anything.

```bash
verify_healthy() {
  local deadline=$((SECONDS + BI_HEALTH_TIMEOUT))
  while (( SECONDS < deadline )); do
    if staging_active && c8_healthy; then return 0; fi
    sleep 5
  done
  return 1   # never latched on a single still-starting snapshot
}
```

### C4: Reset hygiene and honest outcome

A new `burn-in-reset.sh` clears `recovery.json` and `incident.json`. RECOVERED is logged only after a verified-healthy poll passes, never optimistically at restart time. The first breach is preserved exactly once in `incident.json`, so the original signal survives even after a successful recovery. `recovery_count` is surfaced in `status.json`, and recovery pages carry severity `info`, because a recovery is not an incident and should not read like one.

## Verification is the product

A self-healer is only as trustworthy as the failures you can prove it survives. The redesign shipped with four planted scenarios, each run 20 times, 20 for 20:

- **transient-recovery**: breach, restart, verify healthy, log RECOVERED.
- **persistent-failure**: breach latches immediately, zero restarts.
- **notification-failure**: recovery proceeds, logs an honest "receipt non-zero," fires no false page.
- **retry-exhaustion**: exactly MAX_RESTARTS attempts, then latch, no infinite loop.

The two that matter most are the ones that assert the watchdog does nothing. Persistent-failure must latch with zero restarts, because a fault that restarting cannot fix must never be restarted. Retry-exhaustion must stop at the cap and latch, because the whole point of a bound is that it holds under a fault that never clears. A test that only proves the happy path (breach, restart, healthy) proves nothing about safety. The proof that a self-healer is safe is the set of scenarios where it correctly refuses to act.

All three scripts are shellcheck clean. The scenarios are wired into `validate:signoz-staging`, and `pnpm check` exits 0. Guardian review returned approve-with-conditions, and the four conditions above are those blocking conditions, landed.

## The parallel honesty story

The same day, a second system taught the same lesson from a different angle. The governed alert chain went live on both hosts, and the trap was sitting in plain sight: `notify.sh` exits 0 unconditionally. It always reports success. Reuse it as the alert transport and you recreate a prior defect where 108 alerts were false-delivered: reported sent, never sent.

An alert transport that always exits 0 is not a monitor. It is a monitor-shaped object that lies. The fix was a new `vps-slack-transport.sh` that does an honest webhook POST, classifying the HTTP status and treating a non-2xx as a real failure instead of trusting the exit code. `notify.sh` was left untouched for its other callers, so the honesty lives in the transport that needs it.

That verification was as ruthless as the watchdog's: six drills, a bidirectional rollback rehearsal that succeeded in each direction, and a 26-case proof covering 22 failure modes plus 4 non-delivered outcomes, with live green sweeps captured on both hosts. The dev box also got the migrated scorecardecho uptime producer, replacing a stale pre-adoption copy that cron had been quietly running since 07-16, a real docs-versus-reality gap, plus an external dead-man's-switch ping. The guardian loop stayed honest too: round one blocked on an untracked liveness-bypass exclusion, which became a filed follow-up, and round two approved.

Both systems converge on one rule. A monitor that always reports success is worse than no monitor, because no monitor at least tells you nothing is watching. A lying monitor tells you everything is fine. The watchdog's fail-closed classifier and the transport's 2xx check are the same idea wearing different clothes: make the honest outcome the default outcome.

## Also shipped

Outside the watchdog incident, three smaller things landed the same day.

- **diagnostic-pro (PR #23)**: added the in-repo MiniMax advisory PR-review workflow (defect lane plus adversarial-claims lane), the same reviewer already running in claude-code-plugins and intent-os. Runs on `pull_request` (never `pull_request_target`), same-repo head guard so fork PRs never see the API key, gated behind an `ENABLE_MINIMAX_REVIEW` kill switch, advisory only. Enforcement travels with the code.
- **claude-code-plugins**: fixed a heredoc bug in the MiniMax A-grade-coach lane. A `head -c 16000` byte cut landed mid-line, leaving no trailing newline, so the closing `__MINIMAX_EOF__` delimiter fused onto the last content line and GitHub Actions aborted the step with "Matching delimiter not found." Fix: force a trailing newline plus a per-run random delimiter. Only triggered on PRs big enough to fill the 16KB cap.
- **learn-intent-solutions-hub**: ported the CPN cohort hub off Cloudflare onto Intent Solutions infra. Four runtime seams swapped: Workers `export default app` to `@hono/node-server`; D1 `drizzle(c.env.DB)` to a `better-sqlite3` file; `c.env.ASSETS.fetch()` to Caddy `file_server`; `c.env.EXPORT_TOKEN` to `process.env`. Added `/api/health` for a real post-deploy smoke. Product behavior, schema, and routes unchanged.

## Related posts

- [Exit 0 Is Not Success](/posts/exit-0-is-not-success/)
- [A Green Recovery Drill Can Still Be Lying](/posts/a-green-recovery-drill-can-still-be-lying/)
- [Liveness Without Health Is Theater](/posts/liveness-without-health-is-theater/)
