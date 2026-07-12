---
title: "Liveness Without Health Is Theater"
description: "A heartbeat that fires on every run proves a job ran, never that it succeeded — the fix is two markers plus meta-monitoring the watchers."
date: "2026-07-10"
tags: ["monitoring", "reliability", "devops", "observability", "cron"]
featured: false
---
Every team that runs scheduled work eventually ships the same bug, and it does
not look like a bug. A cron job, a nightly workflow, a backup timer — something
that is supposed to run on a clock and quietly do useful work. To keep an eye on
it, someone adds a heartbeat: each time the job runs, it touches a file, pings a
status endpoint, or emits a "still alive" event. A sweep watches those beats and
pages when one goes stale. The dashboard is green. Everyone moves on.

Then one morning the useful work has not happened for three weeks, and the
dashboard is still green.

## The monitor that lies

Liveness proves a scheduled job *ran*. Health proves it *succeeded*. A
liveness-only heartbeat fires on every invocation regardless of outcome, so it
hides the one failure that matters most: a job that runs on schedule and
silently does nothing useful. Two independent markers restore the missing
distinction — is the system stopped, failing, or actually working?

The failure is structural, not incidental. A heartbeat that fires on *every*
invocation — before the work runs, or regardless of how the work exits —
collapses two very different facts into one signal:

- **The job ran** (the scheduler fired, the process started).
- **The job succeeded** (the work it exists to do actually happened).

A liveness-only heartbeat attests only to the first. So the single worst failure
mode of any scheduled system — *a job that runs forever while silently doing
nothing useful* — is precisely the mode it is blind to: the process starts on
schedule, the beat fires like clockwork, and inside it the real work is throwing,
short-circuiting, or writing to the wrong place. Liveness is perfect, health is
zero, and the monitor reports the metric it can measure while staying silent on
the one that matters.

This is not a monitoring gap. A gap implies something is unwatched. This is
worse: the thing is watched, the watch is green, and the green is a lie. That is
theater — the *appearance* of oversight standing in for the substance of it.

## Why heartbeats lie

The flaw is in *where* the beat is written. Touch the heartbeat first and
unconditionally — `touch job.heartbeat; do_the_work`, with nobody checking `$?` —
and the beat is decoupled from the outcome. The exit code, the one piece of
information that distinguishes "worked" from "ran," is thrown away. To the sweep,
a job that succeeds and a job that fails emit the identical signal. Writing the
beat in a `finally` block, or last thing before exit, has the same effect.

The fix is not a better heartbeat. It is a *second* marker.

## Two markers, not one

Separate the two facts into two files. Emit a **liveness beat** on every
invocation. Write a **health mark** only when the work exits clean.

```sh
#!/bin/sh
# run-job.sh — wrap any scheduled job with a two-marker protocol.
STATE_DIR="${STATE_DIR:-/var/lib/job-markers}"
job="$1"; shift

beat="$STATE_DIR/$job.beat"
ok="$STATE_DIR/$job.ok"

# Liveness: fires on EVERY run, before we know the outcome.
date -u +%s > "$beat"

# Do the actual work and capture its verdict.
"$@"; rc=$?

# Health: refreshed ONLY when the work truly succeeded.
if [ "$rc" -eq 0 ]; then
  date -u +%s > "$ok"
fi

exit "$rc"
```

The sweep no longer reads a single file — it reads the **pair**, and the
relationship between the two ages is the diagnosis:

```sh
# For each job, the two ages TOGETHER are the verdict (stale = older than one hour).
beat_age=$(( now - $(cat "$job.beat") ))
ok_age=$(( now - $(cat "$job.ok" 2>/dev/null || echo 0) ))

if   [ "$beat_age" -gt "$stale" ]; then verdict=STOPPED   # not running at all
elif [ "$ok_age"   -gt "$stale" ]; then verdict=FAILING   # running, not succeeding
else                                    verdict=HEALTHY    # ran AND worked
fi
```

The whole point lives in that state table:

| Beat marker | Health marker | Verdict | Meaning |
|---|---|---|---|
| stale | (any) | **STOPPED** | The scheduler is not firing the job at all. |
| fresh | stale | **FAILING** | The job runs on schedule but keeps exiting non-zero. |
| fresh | fresh | **HEALTHY** | It ran *and* it worked. |

The middle row is the whole point: `fresh beat + stale ok` is the silent failure
made loud — a job running forever doing nothing, now a first-class alert. The
same signal-pair instinct shows up wherever automation has to police itself: a
[circuit breaker for a runaway bot loop](https://startaitools.com/posts/bot-loop-circuit-breaker-multi-agent-slack/)
trips on the gap between "still active" and "still making progress."

### The seeding gotcha

One rollout trap: the day the protocol ships, every job has a beat file but no
`.ok` yet, so the first sweep reads every health age as infinite and flags
*everything* FAILING — a wall of false alarms that trains everyone to ignore the
new alert on day one. Seed each health marker from the beat that already exists
(`[ -f "$ok" ] || cp "$beat" "$ok"`), on the assumption that currently-live jobs
are healthy until proven otherwise.

## Watch the watchers

Two markers fix the job. But the sweep, the alert path, and the dashboard are
themselves software — usually written once and never touched again. An unwatched
watcher is not oversight; it is a more expensive blind spot. Meta-monitoring —
observability turned on the watchers themselves — means treating every layer of
the stack as something that can also fail silently.

### Canary the alert path

The most dangerous single point of failure is the notification channel, because
its failure is invisible by construction: a broken alert path produces *no
alerts*, which is indistinguishable from *nothing wrong*. The only way to know a
page can get out is to send one and require proof it arrived. Probe the
credentials, POST to the chat webhook, and demand a real `200`:

```sh
#!/bin/sh
# alert-canary.sh — prove a page can actually get out.
# Run this UNDER run-job.sh, so its own success/failure is two-marked.
: "${WEBHOOK_URL:?alert webhook not configured}"

code=$(curl -s -o /dev/null -w '%{http_code}' \
  -X POST "$WEBHOOK_URL" \
  -H 'Content-Type: application/json' \
  --data '{"text":"alert-path canary — ignore"}')

if [ "$code" != "200" ]; then
  echo "alert path DOWN (HTTP $code)" >&2
  exit 1   # non-zero → run-job.sh leaves .ok stale → the sweep sees a dead path
fi
```

The recursion is deliberate. The canary is wrapped by the same two-marker
runner, so a failed canary refuses to refresh its own health mark, and the sweep
that watches everything else now watches the watcher. On platforms with a service
manager, back it with a native failure hook so a crash that never reaches the
canary still escalates:

```ini
# backup.service.d/onfailure.conf — escalate straight from the service manager.
[Unit]
# alert@%n.service is a templated oneshot unit that runs the notifier.
# NOTE: systemd has no inline comments — everything after '=' is the value,
# so this explanation must live on its own line, never trailing the directive.
OnFailure=alert@%n.service
```

### Reconcile the registry

A sweep can only watch jobs it knows about, and the list of "everything that
should be running" is itself state that drifts as jobs get added, renamed, and
retired. A reconcile job closes the gap: diff the live inventory against the
declared registry and report orphans both ways — things running that nobody
registered, and things registered that no longer run.

A healthy first run is *ugly*. One such diff, run against a live fleet, surfaced
61 orphaned jobs among 138 live automations — things executing for months with
no registry entry, watched by nothing. That is the normal starting state, not an anomaly;
driving it to zero is what makes "the sweep watches everything" true instead of
assumed. The same instinct grows the sweep over time — one system's check count
climbed from 19 to 32 as each new class of silent failure earned its own
assertion.

### Assert log freshness

A status dashboard that `cat`s a log and renders it is another liveness-only lie:
it proves the log *exists*, not that it is *current*. A pipeline can wedge at
2 a.m. and the dashboard will display yesterday's final line forever. Assert the
log's freshness, not merely its contents:

```sh
# A dashboard must prove the log is CURRENT, not just that it has bytes.
log=/var/log/pipeline.log
max_age=900   # 15 minutes

age=$(( $(date -u +%s) - $(stat -c %Y "$log") ))
if [ "$age" -gt "$max_age" ]; then
  echo "STALE: newest log line is ${age}s old — the dashboard is quoting a corpse"
  exit 1
fi
```

## Two root causes worth naming

Two independent production incidents made the abstract argument concrete, and
both traced to causes that generalize well beyond any one system.

### Deploy-by-reference into mutable working trees

Both incidents shared one mechanism: a cron job executed *whatever branch a
shared git working tree happened to be parked on* — a bare symlink into a
directory that humans and other automation also checked out and reset. In one, a
customer-facing uptime monitor ran an old, unarmed version of itself and posted
false positives every day, because the tree sat on a stale branch — and it
exited zero the whole time, so both a liveness beat *and* an exit-code health
mark would have called it perfectly healthy while it lied to users. In another, a
static-site publishing pipeline only *appeared* to run nightly — its lone
"heartbeat" was the tree being parked on a feature branch overnight; the run it
seemed to complete never happened. A missed run that was never missed, because
the signal proving it ran was an artifact of the deploy mechanism, not the work.

The rule that falls out is blunt: **crons run deployed copies or
verified-main paths — never a bare symlink into a working tree.** A working tree
is mutable by definition; anything that reads code from one has no idea what code
it is about to run.

### Inherited file descriptors are state

The second cause is subtler and produced weeks of silent underperformance with
zero errors. A push job serialized itself with `flock` on a lock file held open
as a file descriptor, then spawned a long-lived daemon that *inherited that
descriptor* — and with it the lock, held for the daemon's entire multi-hour
lifetime. A job scheduled every 20 minutes was throttled to roughly once every
two hours — a sixfold collapse in cadence — silently, for weeks. Nothing failed:
every blocked run exited cleanly on "another run holds the lock." The fix is one
character of intent — close the fd on the child:

```sh
#!/bin/sh
# push-cron.sh — serialize with flock, but DON'T leak the lock to children.
exec 9>/var/lock/push.lock
flock -n 9 || { echo "another run holds the lock; exiting" >&2; exit 0; }

# The daemon must NOT inherit fd 9, or it holds the lock for its whole
# lifetime and throttles every future run of this cron.
long_lived_daemon 9>&-
```

The lesson is the thesis restated from a different angle: **silence is not
success.** A job that exits zero on a lock it should never have been blocked by
looks identical, to a liveness monitor, to a job doing perfect work — and a
health mark keyed only to the exit code has the very same blind spot here, since
every throttled run's `rc` was zero. Catching this one needs the third leg from
the last section: assert that the *work product* is fresh — that the push
actually landed — not merely that the process exited clean. It is the same
discipline behind [durable replies that survive a crash](https://startaitools.com/posts/crash-durable-replies-loss-proof/):
prove the work persisted; never infer it from a clean return code.

## The discipline

None of this is exotic — it is one idea applied consistently across every layer:

- **Monitoring is software.** It has bugs, it rots, and it fails silently like
  any other code. Test it, canary it, and give it the same
  [adversarial skepticism](https://startaitools.com/posts/adversarial-review-before-team-rollout/)
  you would aim at the systems it watches.
- **Every layer must distinguish *ran* from *succeeded*.** One marker answers
  "did it run?" A second, written only on a clean exit, answers "did it work?"
  The gap between them is where the expensive failures hide.
- **Monitor the monitors.** Canary the alert path so a dead pager pages itself.
  Reconcile the registry so the sweep watches everything, not just what someone
  remembered to register. Assert log freshness so a dashboard cannot quote a
  corpse.

Do this and the word *green* changes meaning. It stops saying "the cron fired"
and starts saying "the work happened." That is the only definition of green
worth trusting — and the only one a heartbeat, alone, can never give you.

<script type="application/ld+json">
{
  "@context": "https://schema.org",
  "@type": "BlogPosting",
  "headline": "Liveness Without Health Is Theater",
  "description": "A heartbeat that fires on every run proves a job ran, never that it succeeded — the fix is two markers plus meta-monitoring the watchers.",
  "url": "https://startaitools.com/posts/liveness-without-health-is-theater/",
  "datePublished": "2026-07-10T08:00:00-05:00",
  "author": { "@type": "Person", "name": "Jeremy Longshore" },
  "publisher": { "@type": "Organization", "name": "Start AI Tools" },
  "mainEntityOfPage": {
    "@type": "WebPage",
    "@id": "https://startaitools.com/posts/liveness-without-health-is-theater/"
  },
  "articleSection": "DevOps",
  "keywords": "monitoring, reliability, devops, observability, cron"
}
</script>
