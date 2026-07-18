---
title: "A Green Recovery Drill Can Still Be Lying"
description: "A recovery drill that passes green can still be lying. Learn four false-pass traps in disaster recovery and backup restore verification."
date: "2026-07-18"
tags: ["observability", "clickhouse", "disaster-recovery", "backup", "signoz", "testing", "opentelemetry", "restore-verification"]
featured: false
---
We had a backup mechanism for a SigNoz staging stack. What we did not have was a *proven* restore. Those are different claims, and the gap between them is where outages become permanent.

SigNoz is open-source observability backed by ClickHouse. The staging deployment on our self-hosted VPS ran the usual set: ClickHouse for telemetry, clickhouse-keeper for coordination, and Postgres for stack metadata. Snapshots existed. Nobody had ever restored one and confirmed the data came back queryable. A backup you have never restored is a hypothesis, not a safety net.

So the job was to build a real drill: seed known telemetry, back the stack up hot, restore it somewhere safe, and verify the exact seeded data survives. The interesting part is not that we built it. The interesting part is what stood between a drill that runs and a drill that means something: four traps, found in the order below. Two failed loudly and honestly, and fixing them taught us the setup. The other two went green while proving nothing, and one of those would have lied silently forever. The loud ones you catch by running the drill. The silent ones you catch only by auditing the proof.

## The shape of the work

Three scripts, each with one job.

**Hot backup.** Tar the ClickHouse, clickhouse-keeper, and Postgres state trees while the stack keeps running. Read-only, zero downtime. Staging never stops serving.

**Isolated restore.** Unpack the backup into a *disposable*, network-isolated ClickHouse plus keeper pair. Guaranteed teardown at the end. It never shares a network with live and never touches the production containers.

**Recovery drill.** Seed synthetic telemetry through the live ingest gateway, run the backup, run the restore, and verify the seeded signals come back by run id. Every signal we push goes through a disclosure-filter gateway (we call it C8) that strips prohibited content before anything reaches storage. That filter is a governance requirement, and as you will see, it is also the source of two of the four traps.

The target scorecard was concrete: a specific seeded run recovers as a trace and a metric and a log, a planted prohibited phrase is *absent* after restore, all six SigNoz databases come back queryable, and live staging stays healthy the entire time.

Green on that scorecard sounds like proof. Getting there honestly took four corrections.

## Trap 1: the macros trap

The first failure was honest and loud, which is the good kind.

ClickHouse ReplicatedMergeTree tables encode their coordination path using `{shard}` and `{replica}` macros. Those macros resolve against server config. On restore into the disposable container, the tables refused to attach:

```
Code: 36. DB::Exception: No macro 'shard' in config
```

The macros live in the `config.yaml` we mounted into the container. So why were they missing? Because ClickHouse does not read every config file you hand it. It selects one primary config file, and the image default `config.xml` won that selection over our mounted `config.yaml`. The macros were present in a file the server never treated as primary.

You can fight ClickHouse over which primary file wins. Or you can stop fighting. ClickHouse *always* merges everything under `/etc/clickhouse-server/config.d/`, regardless of which primary file it picked. So the fix was a tiny drop-in:

```xml
<!-- /etc/clickhouse-server/config.d/macros.xml -->
<clickhouse>
    <macros>
        <shard>01</shard>
        <replica>replica-restore</replica>
    </macros>
</clickhouse>
```

Mount that into `config.d/`, and the macros are guaranteed present no matter which primary config the server elects to load. Tables attached on the next run.

**Lesson:** for configuration that *must* be present, use the always-merged drop-in directory, not the primary file that some other layer might override. Do not depend on winning a precedence fight you do not control.

## Trap 2: the vacuous canary

With tables attaching, the disclosure filter needed proving. The assertion is negative: after restore, a prohibited string must be *absent*, showing the filter's clean state survived the round trip.

To prove a thing is absent, you first have to put a candidate in. So the drill seeds a canary through the gateway, then checks it is gone after restore. The first canary was a random marker string, something like `CANARY-7f3a91`.

It passed. It also proved nothing.

The gateway's filter does not strip arbitrary text. It matches a specific set of prohibited phrases. A random marker is not on that list, so the gateway correctly passed it straight through to storage. The canary was present in the backup, present in the restore, and the "absent after restore" check was reading the wrong signal entirely. Worse, if the check had been written to expect absence, it would have failed for the right-looking wrong reason, and we would have chased a filter bug that did not exist.

The canary has to be a phrase the filter actually targets. Only then does its absence mean the filter did its job through backup and restore.

**Lesson:** a negative-space test, proving something is absent, is only meaningful if the thing would otherwise be present. An absence assertion over data that was never going to be there is vacuous. It is green by construction and tells you nothing.

## Trap 3: the poisoned run

Fixing the canary broke a different check, and the way it broke is instructive.

The synthetic producer stamps the canary into three places in a run: the span name, the run's one metric name, and its one log body. Once the canary became a *real* prohibited phrase, the gateway did exactly what it is built to do. It dropped the whole signals that carried it. The span survived in altered form, but the metric and the log were filtered out completely.

Now look at what the full-signal verifier needs: a trace and a metric and a log, all sharing the run id. A canary-carrying run cannot supply that, because the metric and log it needs are precisely the signals the filter destroys. The two goals are in direct conflict. Proving the filter strips prohibited content requires data the filter will delete. Proving full-signal recovery requires data that survives untouched. One fixture cannot be both.

The fix is to stop asking one run to do two contradictory jobs. Seed two runs per drill:

- A **clean run** with no prohibited content, used to prove run-id recovery across trace, metric, and log.
- A **canary run** carrying a real prohibited phrase, used to prove the filter's round-trip fidelity by confirming the phrase is absent after restore.

Each run answers exactly one question, and neither question undermines the other.

**Lesson:** one synthetic fixture cannot serve two assertions that require opposite data conditions. When two checks demand contradictory inputs, that is a signal to split the fixture, not to weaken a check.

## Trap 4: the false-pass by default

The drill was green. Every check passing: containers up, queries answered, all databases back, clean run recovered by run id, canary absent. It looked done.

Then we ran an adversarial code review over the harness itself, and it found the trap that matters most, because this one would have lied silently forever.

The verifier script queries ClickHouse for the seeded run id. Its query target, the container it talks to, defaulted to the **live** container when an environment variable was unset. Read that again in context. In step one, the synthetic run is seeded *through the live gateway*. That means the run genuinely exists in live storage. So if any future call, any refactor, any copy-pasted invocation forgot to set the target variable, the verifier would query live, find the run that live legitimately holds, and report `PASS`.

The restore could recover absolutely nothing. The disposable container could be empty. The verifier would still go green, because it was quietly asking the wrong database, and the wrong database happened to have the answer. A broken restore would pass every single time, and the drill would keep congratulating itself.

The fix is to make the target impossible to omit:

```bash
# before: target falls back to live when unset
CH_CONTAINER="${CH_CONTAINER:-signoz-clickhouse}"

# after: explicit, required, no default to a happy source
restore-verify --container "$DISPOSABLE_CH" --run-id "$RUN_ID"
# the script exits non-zero if --container is not provided
```

Every restore-verify call now names its disposable target in code. There is no fallback, so there is no path where a forgotten variable routes the query to live. If you do not say where to look, the verifier refuses to run.

**Lesson:** a verifier that defaults to the happy source is a false-pass generator. If the thing you are trying to prove recovered is *also* present somewhere the verifier can silently reach, an unset default will find it there and lie. Make the target explicit and make omitting it a hard error.

## The collaboration beat

Worth being honest about how the fourth trap surfaced. The build ran on Claude Opus 4.8. The macros trap, the vacuous canary, and the poisoned run all came out through iteration: a check failed or passed suspiciously, we traced it, we fixed it. Normal engineering.

The false-pass-by-default was different. It did not fail. The drill was already green when we ran a dedicated code-reviewer subagent adversarially against the harness, with a narrow charge: can any verify step false-pass, and can any path touch live? That framing, aimed at the proof rather than the data, is what caught the live-default fallback. The drill had proved the data recovers. The adversarial review proved that the proof itself was not yet trustworthy. Those are two different audits, and passing the first does not grant the second.

## Result

The final drill passes eight of eight checks, and now each one means what it says. The eight, in order:

1. The disposable keeper container starts.
2. The disposable ClickHouse container starts.
3. The restored ClickHouse accepts queries.
4. All **six SigNoz databases** are present.
5. The seeded signal rows are recovered and queryable.
6. The **metadata tables** are recovered.
7. The **clean run** recovers by run id, as a trace, a metric, and a log.
8. The prohibited **canary is absent** in the restore, confirming filter round-trip fidelity.

Two measurements come out of the same run, **RTO about 30 seconds** and **RPO about 2 minutes**, and two invariants hold every time: the **disposable stack tears down**, and **live staging stays healthy and untouched**. RTO and RPO are now numbers from an exercised drill, not aspirations from a runbook nobody has run.

## Takeaway

Green is a claim, not evidence. A recovery drill is a program, and like any program it can be correct-looking and wrong. Two of these traps failed loudly, the macros error and the poisoned run, and that is the honest kind: the drill told us the setup was broken before it ever went green. The other two are the dangerous kind. The vacuous canary went green by construction, and the live-default verifier would have gone green over a completely empty restore, forever. You find loud failures by running the drill. You find silent false-passes only by auditing the proof itself.

For any recovery or verification harness, the question to ask is not "does it pass." It is "what would make this pass when it should fail," enumerated concretely, then tested one by one. Would an absent-by-default value satisfy an absence check? Does one fixture quietly serve two contradictory assertions? Can the verifier reach a source that holds the answer for the wrong reason?

None of these four are specific to ClickHouse or SigNoz. A config drop-in that must always merge, a negative test that needs its subject to actually exist, a fixture pulled between two goals, and a verifier that defaults to the happy source: those generalize to any recovery drill you will ever build. The stack was observability. The lesson is about trusting your own green.
