# Communication templates

Copy-paste these. Fill in the bracketed fields. Don't customize beyond the brackets unless you've run an incident before — consistency across responders matters more than artistry.

## Internal — Slack

```
:red_circle: **P1 INCIDENT: [Brief Description]**

**Status:** INVESTIGATING
**Impact:** [What data/users are affected]
**Started:** [Time UTC]
**Current Action:** [What you're doing now]
**Next Update:** [+30 min]

**IC:** @[your-name]
```

Update cadence: every 30 minutes until resolved. If you can't update on time, post `Still investigating, next update [+30min]` — silence is worse than no-news.

## External — Status page

```
**Data Pipeline Delay**
We are experiencing delays in data processing.
Dashboard data may be up to [X] hours stale.
Started: [Time] UTC
Status: Actively investigating
Next update: [Time] UTC
```

External wording rules:

- No internal terminology (no "cluster", "job", "DBR version", "Photon")
- No root-cause speculation until verified — say "investigating", not "Spark OOM"
- Cite staleness in hours, not minutes, even if it's 15 min — minutes-precision implies recovery is closer than it is

## Executive escalation (when severity exceeds responder authority)

```
Subject: [P1] Databricks production data pipeline outage — [time started]

[Exec name],

P1 incident in progress. Production data is stale by [X hours]; impacted downstream: [list].
Mitigation in progress; ETA to resolution [time].
IC: [name]. Watching: #incident-databricks Slack.
Will email next update at [time].
```

Send this only when (a) ETA exceeds 1 hour OR (b) downstream impact spans more than one team.
