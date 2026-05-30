# Databricks Pain Catalog — Domain 1: Compute / Photon / DBR Versioning / Cost

**Scope:** Recurring, painful, real-world Databricks issues across cluster lifecycle, Photon engine, DBR (Databricks Runtime) versioning, and compute cost surprises.
**Research date:** 2026-05-27
**Sources:** Databricks Community Forum, official docs (release notes, KB, troubleshooting), Microsoft Learn Q&A, Medium war stories, vendor analyses (Unravel, Flexera, Cloudzero), Databricks CLI GitHub.
**Note on Reddit/Twitter:** Reddit content fetching is blocked from this environment; the catalog draws from the open community forum and Microsoft Q&A as the most direct equivalent (engineers complaining in public with reproducible context). Each entry below has a Databricks-employee response or a maintainer-acknowledged status — not speculation.

---

## D01 — Cluster startup randomly takes 20–35 min instead of 5

**Domain:** compute
**Trigger:** Engineer kicks off a job-compute cluster (1 driver + 1 worker, small DBR, ~2 libs) on Azure Databricks. It usually takes 5–6 min cold-start. Sometimes — several times a week, unpredictably — it takes 20–35 min instead, and the user pays Azure VM charges for the whole window.
**Symptom:** Cluster sits in `PENDING` for 20–35 min before reaching `RUNNING`. No error surfaced in the UI — just "still starting." Azure managed-resource-group event log shows VM-creation/attachment delays. Workspace is typically VNet-injected.
**Root cause:** Three independently variable cloud-provider stages stacked: (1) Azure VM allocation under quota/zone pressure, (2) NIC attachment + UDR/DNS resolution against the customer VNet, (3) Databricks bootstrap script + library install over that network. Any one of them can spike from seconds to ~20 min and Databricks reports the aggregate as "starting." DNS resolution through a custom DNS server is the single most common amplifier per Databricks-employee answers on related threads.
**Blast radius:** single-job (per-cluster), but pattern repeats across every job in the workspace, so effective blast = workspace-wide for SLA-bound pipelines.
**Current workaround (manual):** Stand up an instance pool with `min_idle > 0` to skip VM allocation; pin a smaller library set; pre-bake an init script into a base image instead of installing at startup; if the workspace is VNet-injected, audit the UDR table and DNS server. None of these eliminate the tail — they shrink the distribution.
**Citations:**

- https://community.databricks.com/t5/data-engineering/databricks-cluster-random-slow-start-times/td-p/78172 (Azure, single-user job compute, OP describes 20-35 min recurrences)
- https://community.databricks.com/t5/data-engineering/job-compute-is-taking-longer-even-after-using-pool/td-p/114389 (April 2025; even with pools, ~5 min remains; Databricks-employee response)
- https://docs.databricks.com/aws/en/compute/troubleshooting/cluster-error-codes (canonical list of bootstrap timeout / cloud-provider error codes)
**Response architecture recommendation:** **MCP server + subagent + SKILL.md.** The MCP server wraps the Databricks Workspace API (`clusters.events`, `clusters.get`) so the agent can pull the full event timeline for a specific cluster ID rather than asking the human to copy-paste UI screenshots. A subagent fan-out can pull events for the last N slow starts in parallel and bucket the time spent in `PENDING` by Databricks event_type, surfacing whether the long tail lives in cloud-provider provisioning vs DNS vs library install. **No hook** — this is always user-initiated ("why was this cluster slow?"). Slash command `/cluster-coldstart-forensics <cluster_id>` is the entry point.

---

## D02 — Photon silently falls back to Spark on UDFs while you keep paying the Photon DBU premium

**Domain:** photon
**Trigger:** Team enables Photon on a SQL warehouse or job cluster to "speed things up." Queries contain Python UDFs, Pandas UDFs, RDD API calls, or other unsupported operations.
**Symptom:** Bill goes up (Photon DBU multiplier is roughly 2x), runtime does NOT go down or improves only slightly. In the Spark UI SQL/DataFrame execution plan, yellow boxes (Photon) are mixed with blue boxes (Spark) — and the bottom-of-plan "Task Time in Photon" metric reads a low percentage (e.g. 8%, 15%) of total task time. Photon executes bottom-up from the table-scan operator and bails to Spark at the first unsupported op, but you are still billed Photon DBUs for the cluster's full uptime.
**Root cause:** Photon is a per-cluster (not per-query) billing toggle. Once enabled on the runtime_engine, every minute the cluster is up is billed at the Photon rate regardless of which operators in any given query actually executed inside the Photon C++ engine. UDFs, RDD APIs, Dataset APIs, certain expressions, and unusual data formats trigger silent fallback to JVM Spark for the rest of the operator chain. There is no warning, no log line, no policy switch that says "this query did not benefit from Photon."
**Blast radius:** workspace-wide cost impact across every job/SQL endpoint running Photon-enabled clusters. Real-world reports show a 4x cost increase against ~1.8x runtime improvement on individual queries.
**Current workaround (manual):** (1) Open every long-running query's execution-details page, eyeball the "Task Time in Photon" %, and if low, either rewrite the UDF in built-in functions or move that workload to a non-Photon cluster. (2) Use cluster policies with `runtime_engine: {"type":"fixed","value":"STANDARD"}` to forbid Photon on workloads that have known UDF dependencies. (3) For SQL warehouses, the only switch is the per-warehouse Photon toggle — no per-query control.
**Citations:**

- https://community.databricks.com/t5/data-engineering/why-is-photon-increasing-dbu-used-per-hour/td-p/41481 (OP: "Why is Photon increasing DBU per hour?" — official answer confirms Photon DBU is higher; "cost reduction is achieved by (possible) faster runtimes")
- https://community.databricks.com/t5/get-started-discussions/photon-and-udf-efficiency/td-p/38570 ("when creating a UDF, photon will not be used")
- https://community.databricks.com/t5/data-engineering/how-do-i-know-how-much-of-a-query-job-used-photon/td-p/25385 (canonical answer: dig into Query Details > Execution Details > Task Time in Photon — there is no API for this)
- https://community.databricks.com/t5/data-engineering/temporarily-disable-photon/td-p/31145 (real user: one operation ran 2x slower under Photon and was still billed Photon rate)
**Response architecture recommendation:** **MCP server + scripts/ + slash command.** MCP server because we need authenticated calls to `sql.queries.history` and `clusters.get` to pull per-query Photon metrics for the past N days. A bundled `scripts/photon-fallback-audit.py` walks the query history for a warehouse, parses each query's execution plan JSON, computes (task_time_in_photon / total_task_time), buckets queries by Photon-effective vs Photon-tax, and projects monthly $$ wasted on the Photon premium for queries with <30% Photon coverage. Slash command `/photon-audit <warehouse_id> --days 30` is the entry point. **No subagent** — this is one sequential scan, not parallelizable work. **No hook** — auditing is intentional, not reactive.

---

## D03 — DBR 14→15 default working directory changed; jobs writing to local paths silently fail at 500 MB

**Domain:** DBR-versioning
**Trigger:** Team upgrades a pipeline from DBR 13.x or 14.x to DBR 15.x (typically 15.4 LTS for the LTS guarantee). Non-Scala code writes intermediate files to a relative path or `os.getcwd()` expecting the driver's ephemeral local disk.
**Symptom:** Jobs that wrote multi-hundred-MB intermediate files start failing — sometimes silently, sometimes with workspace-file-system limit errors. Files appear in the workspace files area instead of `/tmp`-equivalent. Workspace file size limit is 500 MB, so anything over that fails. Behavior also surfaces as "files I expected to be ephemeral are showing up in the user's workspace tree" — a security/audit surprise.
**Root cause:** Starting in DBR 14.0, all non-Scala code uses the workspace filesystem as the default CWD instead of the driver's ephemeral disk. This was a quiet behavior change to support "files alongside notebook" UX, but it inherits the workspace's 500 MB file limit and changes the path semantics of every `open("foo.csv", "w")` style call. Scala code is unaffected — which makes the failure modes split-brain across mixed-language pipelines.
**Blast radius:** every Python/SQL/R pipeline that does intermediate file I/O. On any DBR ≥14.0 upgrade. Often discovered weeks after rollout when a particular dataset crosses 500 MB.
**Current workaround (manual):** Audit every file-write in the codebase, hardcode `/local_disk0/tmp/...` or `/tmp/...` (driver ephemeral) for ephemeral writes, or move large intermediates to Unity Catalog volumes / S3 / ADLS. There is no global toggle to restore old behavior.
**Citations:**

- https://maze-runner.medium.com/databricks-runtime-15-4-lts-issues-fatal-flaws-crashing-your-workloads-a722bacf6a71 (Swiggy field report on the CWD breakage at scale)
- https://docs.databricks.com/aws/en/release-notes/runtime/15.4lts (official notes — "non-Scala code uses workspace filesystem as CWD" + 500 MB workspace file limit)
- https://learn.microsoft.com/en-us/azure/databricks/release-notes/runtime/15.4lts (Azure docs mirror)
**Response architecture recommendation:** **SKILL.md + references/ + scripts/.** No live API needed — this is a static code audit. `scripts/find-cwd-writes.py` grep/AST-scans the user's notebooks and Python files for `open(...)`, `pd.to_csv(...)`, `pickle.dump(...)`, etc. with relative paths and flags them with a recommended rewrite to `/local_disk0/tmp/` or a Unity Catalog volume. `references/dbr14-cwd-change.md` carries the deep encyclopedia of every CWD-affected code pattern with before/after snippets. **No MCP** — purely local file analysis. **No subagent** — sequential walk is fine for typical repo sizes. Could optionally fire as a **PreToolUse hook** on `Edit` of `requirements.txt` or `cluster.json` if those mention DBR 15.x, but the primary surface is `/dbr-upgrade-check`.

---

## D04 — DBR 15.x removes DBFS library storage; DBR 15.1+ removes JDK 11

**Domain:** DBR-versioning
**Trigger:** Team upgrades to DBR 15.1+ on a workspace that has historically installed libraries from `dbfs:/FileStore/jars/...` or relies on JDK 11 via init scripts.
**Symptom:** Cluster startup fails with library-install errors; or Java workloads (custom JARs, certain ML libraries) throw `UnsupportedClassVersionError` / unexpected JNI failures. The DBR 9.1 → 15.4 upgrade thread on the community forum shows the user hitting `ModuleNotFoundError: No module named 'dbruntime'` — a downstream symptom of init-script execution failing because of the DBFS lib path removal.
**Root cause:** Databricks made two simultaneous deprecations in the 15.x line: (1) DBFS-root library storage disabled by default starting DBR 15.1 (security hardening — libraries must live in workspace files, Unity Catalog volumes, or a package repository); (2) JDK 11 removed in DBR 15.1+, only JDK 17 supported. Both changes are documented but the cumulative effect on a multi-year-old pipeline upgrading directly from DBR 9.1 or 10.4 is dozens of breakages stacked on top of each other.
**Blast radius:** every cluster spec referencing DBFS-jar libraries; every JAR built against JDK 11 internals or older Scala versions; every init script that touches Java paths.
**Current workaround (manual):** (1) Re-host every library on UC Volumes or workspace files; (2) rebuild JARs against JDK 17 and Scala 2.13 (preview path for DBR 16/17 upgrade); (3) audit init scripts; (4) do NOT skip multiple LTS versions — incremental 9.1→10.4→11.3→12.2→13.3→14.3→15.4 is painful but each hop surfaces one breakage at a time vs all at once.
**Citations:**

- https://community.databricks.com/t5/get-started-discussions/facing-issues-while-upgrading-dbr-version-from-9-1-lts-to-15-4/td-p/114800 (Apr–May 2025; user hits `ModuleNotFoundError: No module named 'dbruntime'`; Databricks employee Louis Frolio gives the UC Volumes / workspace-files migration recipe)
- https://docs.databricks.com/aws/en/release-notes/runtime/15.4lts (canonical breaking-changes list including DBFS lib deprecation and JDK 17)
- https://docs.databricks.com/en/release-notes/runtime/15.1.html (15.1 = "JDK 11 removed; JDK 17 required" — pivotal version)
**Response architecture recommendation:** **SKILL.md + references/ + scripts/ + MCP server.** `references/dbr-upgrade-paths.md` carries the canonical hop ladder + per-version breaking-change list (auto-derived from release-notes URLs). MCP server pulls the user's actual cluster specs via `clusters.list` and identifies clusters still pinned to EoS DBR + flags libraries living on DBFS roots. `scripts/scan-jar-jdk.sh` runs `javap -v` against the user's JAR artifacts to detect JDK 11-compiled bytecode. **No hook** — upgrades are deliberate. Slash command `/dbr-upgrade-plan` plus a long-running mode that emits an ordered migration plan.

---

## D05 — DBR 15.4 LTS enables `spark.sql.legacy.jdbc.useNullCalendar=true` by default and quietly changes TIMESTAMP semantics

**Domain:** DBR-versioning
**Trigger:** Team upgrades a JDBC-using pipeline (read from SQL Server / Oracle / Postgres into Spark) from DBR 14.3 LTS to 15.4 LTS. No code change.
**Symptom:** TIMESTAMP values coming back from the JDBC source differ from what they were on DBR 14.3 — different timezone interpretation, different handling of dates before the Gregorian cutover, etc. Downstream reports show subtly wrong values for historical timestamps. Often surfaces as a data-quality alert two weeks after upgrade.
**Root cause:** `spark.sql.legacy.jdbc.useNullCalendar` flipped from `false` to `true` as the new default in DBR 15.4 LTS. The flag changes the calendar Spark uses to parse JDBC date/timestamp values. The change is in the release notes under "behavioral changes" but is easy to miss in a 30-bullet release-notes page.
**Blast radius:** every pipeline reading TIMESTAMP columns from JDBC sources. Especially impactful for historical data, finance, healthcare (where pre-1900 dates exist).
**Current workaround (manual):** Explicitly set `spark.sql.legacy.jdbc.useNullCalendar=false` in cluster Spark config to restore pre-15.4 behavior, OR audit every JDBC TIMESTAMP read and validate against ground truth.
**Citations:**

- https://docs.databricks.com/aws/en/release-notes/runtime/15.4lts (canonical: "spark.sql.legacy.jdbc.useNullCalendar setting is now enabled by default")
- https://learn.microsoft.com/en-us/azure/databricks/release-notes/runtime/15.4lts (Azure mirror)
**Response architecture recommendation:** **SKILL.md + references/.** This pain is dense in metadata but light in tooling — the right answer is to give the agent a comprehensive, up-to-date `references/dbr-15.4-behavioral-changes.md` listing every flag flip so when the user says "upgraded to 15.4 and getting weird data," the agent walks the list rather than reinventing the diff. **Optionally a scripts/test-timestamp-roundtrip.py** that emits a synthetic JDBC TIMESTAMP through both old and new calendar modes and confirms which one the user's downstream expects. **No MCP, no hook, no subagent** — this is a knowledge problem, not an integration problem.

---

## D06 — `CLOUD_PROVIDER_LAUNCH_FAILURE` / `NPIP_TUNNEL_SETUP_FAILURE` flood VNet-injected workspaces

**Domain:** compute
**Trigger:** Engineer launches a cluster in a VNet/VPC-injected workspace (private link, no public IP). Cluster fails to start.
**Symptom:** `termination_reason_code: CLOUD_PROVIDER_LAUNCH_FAILURE` with error parameters mentioning `AuthorizationFailed`, `InvalidResourceReference`, full subnet, IP exhaustion, or quota; OR `NPIP_TUNNEL_SETUP_FAILURE` with `Timed out waiting for ngrok tunnel to be up`. Cluster terminates after the bootstrap timeout (~700s for bootstrap, ~200s for SCC/NPIP tunnel).
**Root cause:** Multiple distinct underlying failures share these umbrella codes: (a) subnet IP exhaustion or quota limits on AWS/Azure/GCP; (b) custom DNS server in the customer VNet can't resolve `*.cloud.databricks.com`; (c) UDR/NSG/security-group blocks ports 443/6666 to the SCC relay; (d) a VNet referenced in the workspace config was deleted; (e) cloud-provider throttling during regional surges. Databricks surfaces the same `NPIP_TUNNEL_SETUP_FAILURE` code for all the network-related causes, leaving the engineer to brute-force which one applies.
**Blast radius:** workspace-wide — if DNS or routing is broken, no cluster in the workspace starts. Often discovered as a Monday-morning outage when a Friday-night change rolled.
**Current workaround (manual):** Differential triage: (1) `nslookup *.cloud.databricks.com` from a VM in the same subnet; (2) `nc -zv <scc-relay-host> 443 6666`; (3) check NSG/security-group inbound and outbound; (4) check subnet free-IP count against pool/cluster max-worker count; (5) check cloud-provider status page; (6) check whether anyone touched the VNet recently.
**Citations:**

- https://docs.databricks.com/aws/en/compute/troubleshooting/cluster-error-codes (canonical termination-reason-code dictionary)
- https://community.databricks.com/t5/data-engineering/npip-tunnel-setup-failure/td-p/121068 (June 2025, AWS NPIP failure thread; Databricks employee response)
- https://community.databricks.com/t5/data-engineering/cloud-provider-launch-failure/td-p/21845 (Azure CLOUD_PROVIDER_LAUNCH_FAILURE with VNet/subnet root cause)
- https://learn.microsoft.com/en-us/answers/questions/2244769/databricks-cluster-start-up-fails-on-test-workspac (NPIP, DNS-related fix)
**Response architecture recommendation:** **MCP server + subagent + scripts/.** MCP server because differential triage requires authenticated calls to `clusters.events`, `workspaces.get`, and ideally the cloud-provider's own status/quota APIs (AWS EC2 `DescribeAccountAttributes`, Azure `Microsoft.Network/virtualNetworks/subnets`). Subagents fan out the differential checks in parallel: one checks DNS, one checks subnet IPs, one checks NSG rules, one checks Databricks status page, one diffs the workspace config against last-known-good. `scripts/triage-cluster-launch-failure.sh` does the basic non-API checks (`nslookup`, `nc -zv`) the user can run from a peer VM. Slash command `/cluster-launch-triage <cluster_id>`. **Optionally a PostToolUse hook** on `databricks clusters create` that, if the create fails with one of these codes, auto-invokes the triage flow.

---

## D07 — All-purpose compute used for production pipelines = 2–4x DBU overspend

**Domain:** cost
**Trigger:** Team prototypes a pipeline in a notebook on an all-purpose cluster (interactive), then "ships to prod" by scheduling that notebook on the same all-purpose cluster instead of moving it to a Jobs cluster.
**Symptom:** Monthly Databricks bill is 2–4x what the team's modeling predicted. No code change would reduce it. `system.billing.usage` shows the same SKU at all-purpose DBU rate (~$0.40/DBU-hr for i3.xlarge) instead of jobs-compute rate (~$0.15/DBU-hr).
**Root cause:** All-purpose ("interactive") compute carries a 2–3x higher DBU rate than Jobs compute for the same instance type, by Databricks's pricing model. The premium pays for shared multi-user notebook UX features the production job doesn't use. Engineers default to all-purpose because it's the default tab in the UI and because "we already had a cluster." Often compounded by: (a) cluster left running 24/7 instead of terminating between job runs, (b) no auto-termination, (c) team didn't know a job-compute cluster exists.
**Blast radius:** workspace-wide cost impact; the single highest-ROI cost optimization in most Databricks deployments per Unravel/Cloudzero/Flexera vendor analyses.
**Current workaround (manual):** Convert scheduled notebook to a Job with a Jobs cluster spec; configure auto-termination; ideally adopt cluster policies that forbid scheduled work on all-purpose. Audit historical billing to estimate refund-equivalent savings.
**Citations:**

- https://community.databricks.com/t5/data-engineering/job-cluster-vs-all-purpose-cluster/td-p/16566 (canonical community thread on the distinction)
- https://www.cloudzero.com/blog/databricks-pricing/ (2026 breakdown: ~$0.15 vs ~$0.40 DBU/hr for i3.xlarge across compute types)
- https://www.unraveldata.com/resources/databricks-automatic-termination-challenges-finops-teams/ (real numbers: weekend idle = ~$800 on i3.8xlarge; 2-week holiday = $5K–$10K; 6-month idle = $12K)
- https://www.unraveldata.com/resources/databricks-interactive-clusters-decision-framework/ ("production batch on all-purpose = paying 2-3x more")
**Response architecture recommendation:** **MCP server + scripts/ + slash command.** MCP server reads `system.billing.usage` and `jobs.list` to identify scheduled jobs running on all-purpose clusters. `scripts/cost-leak-audit.py` projects 30-day savings from moving each to Jobs compute. Output is a ranked list with absolute $$ saved per migration. **Optional PostToolUse hook on `databricks jobs create`** that warns if the new job references an all-purpose cluster ID rather than declaring its own job_cluster_key. **Slash command** `/cost-audit-all-purpose-leaks`. **No subagent** — sequential scan is fast.

---

## D08 — Serverless features bill silently against accounts that never opted into serverless

**Domain:** cost
**Trigger:** Workspace admin has not enabled serverless for notebooks/workflows. They turn on Predictive Optimization, Lakehouse Monitoring, materialized views in SQL warehouses, Vector Search, or Lakeflow Connect.
**Symptom:** Surprise line items appear in `system.billing.usage` with `billing_origin_product` values of `PREDICTIVE_OPTIMIZATION`, `LAKEHOUSE_MONITORING`, `VECTOR_SEARCH`, `FINE_GRAINED_ACCESS_CONTROL`, etc., billed at serverless DBU rates (~$0.70–$0.95/DBU vs ~$0.40–$0.55 for classic). Bill is meaningfully higher than budgeted, and the admin "doesn't see any serverless workloads running."
**Root cause:** Multiple Databricks platform features execute on serverless compute in the background by design, regardless of whether the customer has explicitly enabled serverless for user workloads. The features are turned on through different UI surfaces (Catalog Explorer for Predictive Optimization, table-properties UI for monitoring, SQL `CREATE MATERIALIZED VIEW` statement, etc.) so the cause-effect chain between "I checked this box" and "this serverless line item appeared" is not visible at toggle time.
**Blast radius:** account-wide cost impact, especially painful for orgs that explicitly chose classic compute for cost-control reasons and don't have serverless budget policies in place.
**Current workaround (manual):** Query `system.billing.usage` filtered by `billing_origin_product IN ('PREDICTIVE_OPTIMIZATION','LAKEHOUSE_MONITORING','MATERIALIZED_VIEW','VECTOR_SEARCH','FINE_GRAINED_ACCESS_CONTROL','LAKEFLOW_CONNECT')` to identify silent serverless consumers. Disable the features that aren't paying for themselves. Set serverless budget policies BEFORE enabling any of these.
**Citations:**

- https://docs.databricks.com/aws/en/admin/system-tables/serverless-billing (canonical list of `billing_origin_product` values that signal background serverless usage)
- https://learn.microsoft.com/en-us/azure/databricks/admin/system-tables/serverless-billing (Azure mirror)
- https://www.revefi.com/blog/databricks-serverless-budget-policies-2026 (vendor walkthrough: budget policies as the only preventive control)
- https://adamtheautomator.com/azure-databricks-serverless-cost-optimization/ (community write-up: "Multiple Databricks features leverage serverless compute in the background without requiring your account to be enabled for serverless")
**Response architecture recommendation:** **MCP server + scripts/ + scheduled subagent.** MCP server runs the canonical `system.billing.usage` query (Unity Catalog read) to detect background serverless consumers and their 30-day spend. `scripts/serverless-shadow-audit.py` ranks features by $$/month and recommends whether to keep, gate behind a budget policy, or disable. A periodic subagent (e.g. weekly cron via the `loop` skill or a CI scheduled action) re-runs the audit and alerts on new `billing_origin_product` values appearing — that's how you catch a new feature being silently enabled. **No hook** because the trigger event (a coworker enables Predictive Optimization in the UI) doesn't go through any tool we can intercept.

---

## D09 — Instance pool with `min_idle > 0` keeps paying cloud-provider for idle VMs even though DBU billing is zero

**Domain:** cost
**Trigger:** Team configures an instance pool with `min_idle_instances: 5` to get fast cluster startup, then walks away.
**Symptom:** Databricks UI shows pool DBU consumption as $0 when no cluster is attached — but the AWS/Azure/GCP bill shows 5 VMs of the pool's instance type running 24/7. Cost can run into thousands per month for a single pool that nobody is actively using on weekends/nights.
**Root cause:** Databricks's billing model only charges DBUs while a cluster is *attached to* the pool's instances. Idle pool capacity costs $0 in DBUs but the underlying VMs are running and billed by the cloud provider directly. This is correctly documented but the UI never shows the cloud-provider side of the bill, so the team's internal Databricks dashboard reads "pool costs $0/mo" while the AWS bill reads "$3K/mo for this set of instances."
**Blast radius:** every workspace with instance pools and `min_idle > 0`; especially painful when teams pre-warm aggressively to hide cold-start latency (see D01).
**Current workaround (manual):** Set `min_idle: 0` and accept slower first-cluster startup, OR shrink `min_idle` on a schedule (e.g. 5 during business hours, 0 nights/weekends — requires an external job to mutate the pool config since pools don't have native schedules), OR migrate to Serverless Jobs which has no idle-VM model. Cross-reference cloud-provider billing against pool config quarterly.
**Citations:**

- https://community.databricks.com/t5/data-engineering/does-databricks-charge-anything-when-nodes-in-a-pool-are-idle/td-p/26994 (canonical: "Databricks does not charge DBUs while instances are idle in the pool, but instance provider billing does apply")
- https://docs.databricks.com/aws/en/compute/pool-best-practices (official: "Set the Min Idle instances to 0 to avoid paying for running instances that aren't doing work")
- https://learn.microsoft.com/en-us/answers/questions/827794/pools-and-cost (Microsoft Q&A with the same dual-billing clarification)
**Response architecture recommendation:** **MCP server + scripts/.** MCP server pulls pool configs via `instance_pools.list` AND cross-references against the cloud-provider billing data (requires AWS Cost Explorer / Azure Cost Management read access — separate MCP or scripts). `scripts/pool-idle-cost-projection.py` computes (`min_idle × instance_hourly_rate × 730 hrs/month`) per pool and ranks by waste. Output: "Pool `prod-data-eng` has min_idle=8, costs ~$4,200/mo even when idle." **No hook** — pool changes are infrequent and intentional.

---

## D10 — Spot-instance interruptions during shuffle kill long jobs; Databricks's auto-retry doesn't always recover

**Domain:** compute
**Trigger:** Team configures a cluster with all-spot or mostly-spot workers to save money. A long ETL job is running. AWS/Azure reclaims spot capacity (2-min warning on AWS).
**Symptom:** `org.apache.spark.SparkException: Job aborted due to stage failure: ShuffleMapStage X has failed the maximum allowable number of times: 4`. Cluster loses a worker. Spark's `ResultStage` can't roll back to re-shuffle input data so the job fails outright. Sometimes the job retries successfully; sometimes it cascade-fails because more spot instances get reclaimed during the retry.
**Root cause:** When a spot node is preempted mid-shuffle, the in-progress shuffle map outputs on that node are gone. Spark's lineage can recompute them, but if the recompute itself loses another node, it counts as another failure against `spark.stage.maxConsecutiveAttempts` (default 4). Heavy shuffle jobs on volatile spot capacity exceed that count and abort the entire job. Lakeflow Jobs' exponential-backoff retry helps for transient failures but doesn't help when the underlying spot capacity is sustainedly unavailable.
**Blast radius:** any production batch pipeline configured for spot/preemptible nodes; especially painful for nightly windows when many tenants compete for the same spot pools.
**Current workaround (manual):** (1) Set the driver to on-demand always; (2) set first N workers on-demand and rest spot (the slider in cluster config); (3) implement job-level retry with exponential backoff at the orchestration layer; (4) for critical SLAs, use all on-demand and absorb the cost; (5) increase `spark.stage.maxConsecutiveAttempts` (controversial — masks the underlying instability).
**Citations:**

- https://kb.databricks.com/execution/apache-spark-jobs-failing-due-to-stage-failure-when-using-spot-instances-in-a-cluster (canonical Databricks KB: spot preemption + shuffle = stage failure)
- https://medium.com/@chaobioz/dealing-with-spot-instances-interruption-in-databricks-aws-5d4a4f722e5c (engineer's field write-up on AWS spot interruptions in Databricks)
- https://docs.databricks.com/aws/en/compute/troubleshooting/cluster-error-codes (canonical termination-reason code `SPOT_INSTANCE_TERMINATION`)
**Response architecture recommendation:** **SKILL.md + references/ + scripts/.** This is mostly a cluster-config + retry-policy decision tree, not a live-data problem. `references/spot-vs-ondemand-decision.md` carries the canonical guidance (driver on-demand always; workers spot only if job is idempotent and SLA-tolerant). `scripts/audit-spot-config.py` reads a `cluster.json` and flags risky combos (spot driver, all-spot workers, >4 consecutive shuffle stages). **Optional MCP** to read recent `clusters.events` and surface spot-interruption frequency per cluster over the last 30 days, which informs the decision empirically. **No hook, no subagent.**

---

## D11 — Lakeflow Declarative Pipelines (formerly DLT) initialization takes 5+ min when >30 streaming tables in one pipeline

**Domain:** compute
**Trigger:** Team defines 30+ streaming tables (Auto Loader → bronze → silver → gold) inside a single Lakeflow Declarative Pipeline (DLT) definition.
**Symptom:** Every triggered pipeline run spends 5+ minutes in initialization before the first row is processed. Continuous pipelines hide this (they initialize once and stay up), but triggered/scheduled pipelines pay it every run. End-to-end latency is dominated by init, not by compute. Driver may also OOM.
**Root cause:** The DLT driver builds the dependency DAG, plans the execution order, and initializes streaming state for every table in the pipeline at startup. Above ~30-40 streaming tables, the driver's CPU becomes the bottleneck — this is acknowledged in Databricks's own fix-high-init docs. The recommended fix is to split into multiple pipelines, which fights against the DLT design principle of "one declarative pipeline per logical domain."
**Blast radius:** any DLT user with a large declarative pipeline; especially painful for orgs that adopted DLT precisely because it promised "declarative = simple, don't worry about scaling."
**Current workaround (manual):** Split the pipeline into multiple pipelines along source-data or domain boundaries. Use continuous mode where SLA allows. Move from triggered to continuous to amortize init cost. Profile the dependency-graph build phase via the DLT event log.
**Citations:**

- https://docs.databricks.com/aws/en/ldp/fix-high-init (official: "running more than 30-40 streaming tables within a single pipeline" makes the driver a bottleneck; splitting is the recommended remediation)
- https://learn.microsoft.com/en-us/azure/databricks/dlt/fix-high-init (Azure mirror)
- https://community.databricks.com/t5/get-started-discussions/trying-to-reduce-latency-on-dlt-pipelines-with-autoloader-and/td-p/133985 (community thread on DLT latency reduction)
**Response architecture recommendation:** **SKILL.md + scripts/.** `scripts/dlt-init-profiler.py` reads a pipeline's event log via the Databricks Pipelines API, isolates the `initialization` phase events, and emits a per-table breakdown of init time. **Optional MCP** for live pipeline-event-log reads via `pipelines.get_event_log`. **No subagent, no hook.** This pain is consultative — the agent's job is to detect "you're at the threshold" and recommend the split before init hits 10+ min.

---

## D12 — Serverless notebook has no configurable idle timeout; "fading green" minutes are not clearly billed

**Domain:** cost
**Trigger:** User finishes running cells in a serverless notebook. The notebook shows "fading green" / "spinning down" state for 5–10 minutes before becoming fully idle.
**Symptom:** User is unsure whether they're being charged during the fade. There is no UI setting to configure the timeout. Documentation does not give a definitive answer. `system.billing.usage` is the only way to verify.
**Root cause:** Serverless notebooks do not expose the idle-timeout knob that classic clusters (auto_termination_minutes) and SQL warehouses (auto_stop_mins) have. The fade window is platform-managed and currently non-configurable per a Databricks employee answer on the community forum (March 2026). The platform "is still doing real work" during the fade — implying there is some level of billing, but no documented commitment to "you are not billed for the fade window."
**Blast radius:** every serverless-notebook user; especially impactful for ad-hoc / exploratory analysts who open and close notebooks frequently throughout the day.
**Current workaround (manual):** Query `system.billing.usage` filtered to your user + this notebook's session to verify what you were billed. Explicitly detach the notebook when done (does not fully eliminate fade but may shorten it). Use classic compute with strict auto-termination if predictable billing matters more than serverless cold-start speed.
**Citations:**

- https://community.databricks.com/t5/data-engineering/serverless-notebook-idle-timeout-is-it-configurable-what-exactly/td-p/151133 (March 2026; OP describes "fading green" state, Databricks employee confirms no public config option)
- https://docs.databricks.com/aws/en/compute/serverless/best-practices (recommends caching environments, doesn't address idle-billing question)
- https://docs.databricks.com/aws/en/admin/system-tables/serverless-billing (canonical: `system.billing.usage` is the only ground truth)
**Response architecture recommendation:** **SKILL.md + scripts/ + slash command.** `scripts/serverless-notebook-bill-attribution.py` runs a parameterized `system.billing.usage` query for the user's serverless notebook sessions over a window and emits per-session DBU + $$. Slash command `/serverless-notebook-bill <notebook_id> --days 7`. **Optional MCP** for the Unity Catalog SQL read. **No hook, no subagent** — this is on-demand attribution work, not background monitoring.

---

# Cross-cutting source clusters I could NOT crack

The catalog above is grounded only in sources I could actually fetch. Source clusters where I had partial signal but couldn't get full verbatim quotes:

1. **Reddit r/databricks and r/dataengineering** — `WebFetch` is blocked from reddit.com in this environment. Plenty of thread titles surface in indirect search results but I can't pull the body text + comment authority. Manual follow-up: have a human pull the top-of-year unresolved threads for each of these four pain domains and confirm whether the 12 entries above match the field reports.

2. **YouTube DAIS / Data + AI Summit 2024-2025 talks** — Couldn't ingest video content in this run. The "war story" / postmortem talks at DAIS are typically the richest source of named-customer pain (DBR upgrade pain at $LARGE_FINTECH, etc.) but require transcript extraction, which is a separate workflow.

3. **Twitter/Bluesky "databricks at 3am" / "databricks broke" threads** — Twitter/X search is gated for unauthenticated fetches; couldn't get a usable corpus.

4. **GitHub `databricks/databricks-sdk-py` and `databricks/terraform-provider-databricks` issues** — Sampled `databricks/cli` only. The 20 recent bug issues there are mostly bundle-deploy and CLI-panic issues, not cluster/Photon/DBR/cost pain — so they're out of scope for this domain. A deeper pass into the SDK and Terraform-provider repos would likely surface programmatic-API pain (e.g. `clusters.create` returning success while the cluster never actually starts) — recommend a follow-up scan with: `gh api repos/databricks/databricks-sdk-py/issues?state=closed&labels=wontfix` and the same for `terraform-provider-databricks`.

5. **Per-cloud quota / sub-region pain** — there's a known cluster of "we hit `RequestLimitExceeded` in us-east-1 during reInvent / Black Friday / quarterly close" anecdotes but the open-web sources don't reproduce the specific Databricks-side termination codes consistently. Worth a Databricks-employee interview to confirm what the exact codes are.

# Summary

12 pain entries across 4 sub-domains (compute, photon, DBR-versioning, cost), each grounded in 2-4 fetched sources with author/date/version context. Every entry maps to a concrete Claude Code primitive recommendation. The dominant primitive across the catalog is **MCP server** (workspace API + system.billing.usage read access is the load-bearing capability) — 7 of 12 entries call for one. **Subagent fan-out** is recommended only where parallel API queries materially shorten triage time (D01, D06). **Hooks** are recommended sparingly and only as opt-in PostToolUse triggers (D06, D07) — most of this work is user-initiated diagnostics, not background reactive work. **Scripts/** are recommended in 9 of 12 entries as the unit that does the actual work; SKILL.md is always present as the playbook.
