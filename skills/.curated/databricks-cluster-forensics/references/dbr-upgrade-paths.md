# DBR Upgrade Breaking Changes — Per-Hop Forensics

A Databricks Runtime (DBR) upgrade is not a version-number bump — it is a set of
_behavioral_ changes that either refuse to start a cluster (loud, easy) or silently
change what your jobs compute (quiet, expensive). This reference catalogs the four
breaking changes that bite hardest on the common LTS-to-LTS hops (13.3 LTS → 14.3
LTS → 15.4 LTS), each with the exact version it landed in, whether it surfaces as a
**cluster-start failure** or a **silent runtime regression**, how to detect it
_before_ you cut over, and the single mitigation.

Read the failure-mode tag on each section first. A cluster-start failure is cheap:
the cluster never comes up, you see the error, you fix it. A silent runtime
regression is the dangerous class — the cluster starts green, the job "succeeds,"
and the numbers are wrong (or a file is quietly written somewhere new). Those are the
ones the bundled scanners exist to catch.

Two scanners ship with this skill and are referenced below:

- `find-cwd-writes.py` — AST-scans notebooks and `.py` sources for relative-path
  file writes that the 14.x CWD move will relocate or fail.
- `scan-jar-jdk.sh` — `javap` bytecode-version inventory of every JAR, for the 15.1
  JDK 17 hop.

---

## DBR 14.x — Default working directory moved to the workspace filesystem

**What changed.** The default current working directory (CWD) for Python and shell
code moved from the driver's ephemeral local disk (`/databricks/driver`) to the
**workspace directory containing the notebook** (a `/Workspace/...` path on the
workspace filesystem). Relative-path file I/O, `os.getcwd()`, and `%sh` commands now
resolve against that workspace path instead of local disk.

**Version.** Landed in **DBR 14.0**; the prior behavior held through **DBR 13.3 LTS
and below**. So the break is introduced on any hop that crosses the 13.3 → 14.x line.

**How it manifests — a silent runtime regression, with one hard-failure edge.** The
cluster starts fine. Two things then go wrong at job runtime:

- Workspace files are capped at **500 MB per file**. A job that wrote a >500 MB
  intermediate to a relative path (or the CWD) — a staged Parquet, a model
  checkpoint, a shuffled CSV — now **fails at the moment of the write** with a
  file-size error, not at cluster start.
- Below the cap, the write _succeeds silently at a new location_: intermediates land
  in the workspace filesystem (and persist until explicitly deleted) instead of
  vanishing with the ephemeral disk, and downstream relative reads resolve to the
  workspace dir. Behavior changes with no error at all.

**Detect before upgrading.** Inventory every relative-path write and CWD-relative
read before cutover. The bundled AST scanner does this deterministically:

```bash
# Bundled: find-cwd-writes.py — flags relative-path I/O that the CWD move relocates
python3 find-cwd-writes.py --path ./repo --dbr-target 14.3
# Flags: open('out.parquet','w'), df.to_csv('stage.csv'), *.to_parquet('x'),
#        os.getcwd()-relative paths, and %sh redirects into the CWD
```

**Mitigation.** There is no Spark config that reverts this — it is a code fix. Pin
intermediates to explicit ephemeral local disk (`/local_disk0` or `/tmp`), either by
`os.chdir` in the first cell or by writing absolute paths:

```python
# First cell — send intermediates to ephemeral local disk, not the workspace FS
import os
os.chdir("/local_disk0/tmp")
# ...or write absolute paths explicitly and skip chdir entirely:
df.to_parquet("/local_disk0/tmp/stage.parquet")
```

---

## DBR 15.1 — DBFS-root library storage removed

**What changed.** Storing cluster libraries in the **DBFS root** was deprecated and
**disabled by default**. A cluster configured to install a JAR/wheel/egg from a
`dbfs:/...` path can no longer do so under the default configuration.

**Version.** **DBR 15.1.** (This is the same runtime that also removed JDK 11 —
next section — so a single 15.1 hop carries two independent breaks.)

**How it manifests — a cluster-start / library-install failure (loud).** The cluster
provisions, then the library install step fails because the `dbfs:/` artifact path is
rejected; any job depending on that library fails to run. It surfaces at
start/attach time, not deep in a job — which makes it the easier of the two 15.1
breaks to catch, provided you inventory library sources first.

**Detect before upgrading.** Enumerate every cluster library and init script still
pointing at `dbfs:/`:

```bash
# Inventory cluster libraries whose source is still a dbfs:/ path
databricks libraries cluster-status <cluster_id> \
  | jq '.library_statuses[].library
        | select((.jar // .whl // .egg // "") | test("^dbfs:/"))'
```

**Mitigation.** Move artifacts to **workspace files** (`/Workspace/...`) or a **Unity
Catalog volume** (`/Volumes/...`). If you need a temporary bridge during migration,
re-enable the old behavior with the real config flag (do not leave it on):

```text
# Bridge only (temporary) — re-enable DBFS-root library installation:
spark.databricks.driver.dbfsLibraryInstallationAllowed true

# Real fix — relocate the artifact off DBFS root:
#   dbfs:/FileStore/jars/foo.jar  ->  /Volumes/main/default/artifacts/foo.jar
```

---

## DBR 15.1 — JDK 11 removed; JDK 17 is the target

**What changed.** **JDK 11 was removed** from the runtime; Databricks recommends
upgrading to **JDK 17**, which becomes the effective compile/runtime target from this
version forward. (This hop also moves the default Python from 3.10 to **3.11** — call
it out separately when planning; C-extension wheels and pickles are ABI-sensitive.)

**Version.** **DBR 15.1** removes JDK 11; **JDK 17 is the target on DBR 15.1 and
above.**

**How it manifests — mixed; mostly a runtime/library-load failure.** The JVM is
backward-compatible with older bytecode, so most JDK-11-targeted JARs load and run
unchanged — do not assume "recompiled for 11" equals "broken." The real breakage is
narrower and shows up when a class loads or a code path executes:

- A JAR compiled for a target _newer_ than 17 (bytecode major version > 61) throws
  `UnsupportedClassVersionError` — a hard load failure.
- Libraries that reflect into **strongly-encapsulated JDK internals** (`sun.misc.Unsafe`,
  reflective access into `java.*`), permitted on JDK 11 with `--illegal-access`, now
  throw `InaccessibleObjectException` under JDK 17's strong encapsulation (JEP 403).
- Code depending on **modules removed between 11 and 17** — Nashorn (removed JDK 15),
  the Java EE / CORBA modules (JEP 320) — fails with `NoClassDefFoundError`.

**Detect before upgrading.** Take a bytecode-version inventory of every JAR you ship,
so you can flag both too-new bytecode and ancient JARs most likely to touch removed
internals:

```bash
# Bundled: scan-jar-jdk.sh — javap bytecode-major-version inventory across all JARs
scan-jar-jdk.sh /path/to/artifacts/*.jar
# Under the hood, per class:
javap -verbose Foo.class | grep -m1 'major version'
#   52 = Java 8    55 = Java 11    61 = Java 17
# Flags: major > 61 (UnsupportedClassVersionError on JDK 17) and legacy 52/55 JARs
#        whose deps may reach JDK internals removed/encapsulated by JDK 17 (JEP 403).
```

**Mitigation.** Recompile or upgrade the offending library against JDK 17 and replace
any dependency on a removed module. The JVM is selected by the cluster env var
`JNAME` — but the JDK 11 value is gone from 15.1, so a pin to it no longer resolves:

```text
# Pre-15.1 you could pin the JVM via a cluster env var:
#   JNAME=zulu11-ca-amd64      # JDK 11 — REMOVED in DBR 15.1, no longer resolves
#   JNAME=zulu17-ca-amd64      # JDK 17 — the 15.1+ target
# Real fix: rebuild the library for JDK 17; drop deps on Nashorn / Java EE (JEP 320)
#           and on reflective access into java.* internals.
```

---

## DBR 15.4 LTS — JDBC TIMESTAMP calendar default flipped

**What changed.** The default of `spark.sql.legacy.jdbc.useNullCalendar` **flipped to
`true`**. When true, the JDBC driver is handed a null `Calendar` instead of a default
proleptic-Gregorian calendar while materializing `TIMESTAMP` (and `DATE`) values —
changing how timestamps are interpreted across the pre-Gregorian range (dates before
the 1582 Julian-to-Gregorian cutover) and across driver timezone handling on JDBC
reads and Lakehouse Federation sources.

**Version.** **DBR 15.4 LTS.** Prior LTS/runtime lines defaulted it to `false`.

**How it manifests — a silent runtime regression, with a hard-error edge on some
drivers.** For most workloads the read still "succeeds," but pre-1582 and
timezone-edge `TIMESTAMP` values shift — a correctness bug in federated reads that no
exception announces. Some drivers reject a null calendar outright: DB2, for example,
fails with `Invalid parameter calendar: Parameter cannot be null.` on `TIMESTAMP`
columns after the upgrade.

**Detect before upgrading.** Inventory every JDBC read of `TIMESTAMP`/`DATE` columns
and A/B the same rows across runtimes before cutover:

```python
# Find JDBC reads the flip can silently shift, then diff 13.3/14.x vs 15.4 output:
#   spark.read.format("jdbc")...    df.write/read .jdbc(url, table, props)
#   Lakehouse Federation queries against DB2 / Oracle / SQL Server
# Compare pre-Gregorian (< 1582-10-15) and DST-edge TIMESTAMP rows side by side.
```

**Mitigation.** Restore the prior semantics explicitly at cluster or session scope
(and only adopt the new default once you have validated it against your data):

```text
# Restore pre-15.4 JDBC timestamp semantics at cluster or session scope:
spark.sql.legacy.jdbc.useNullCalendar false
```

---

## Version-accuracy anchors (what senior practitioners test for)

Pin these to the correct version — they are the details a reviewer uses to check
whether an upgrade plan was written from the release notes or from memory:

- **Liquid Clustering** was introduced in **preview in DBR 13.3** and reached
  **GA in DBR 15.2** (announced May 2024). It is _not_ GA in 13.3 — a plan that
  treats 13.3 Liquid Clustering as production-grade is wrong. On Delta tables it is
  GA on 15.2+; the 15.4 LTS notes also state GA, since 15.4 LTS is the first LTS that
  carries the GA feature.
- **JDK 17** is the target from **DBR 15.1 and above** (JDK 11 removed in 15.1). Do
  not attribute the JDK 17 move to a later runtime.
- **The JDBC calendar flip** is `spark.sql.legacy.jdbc.useNullCalendar`, default
  **`true` from DBR 15.4 LTS**. The key name and the direction of the flip both
  matter — the default became `true`, and you set it `false` to get the old behavior.
- **The 500 MB cap** is per **workspace file**, tied to the **DBR 14.0** CWD move —
  not a cluster-wide or DBFS limit.

Anything below the LTS granularity above (exact maintenance-release patch numbers,
per-cloud endpoint strings) drifts — _(verify against the release notes for your
exact runtime and cloud)_.

## Upgrade decision table

Each hop introduces only the landmines new to that span; a double hop inherits every
row it crosses. Plan the highest-risk jump (13.3 LTS → 15.4 LTS) as if all four
breaks fire at once, because they do.

| From (source DBR) | To (target DBR) | Landmines introduced on this hop |
| --- | --- | --- |
| 13.3 LTS | 14.3 LTS | CWD moves to the workspace filesystem + 500 MB per-file write cap (14.0). Silent-regression class — run `find-cwd-writes.py`. Liquid Clustering is still **preview**, not GA. Python stays 3.10. |
| 14.3 LTS | 15.4 LTS | DBFS-root library storage disabled + JDK 11 removed / JDK 17 target + Python 3.10 → 3.11 (all **15.1**); JDBC `useNullCalendar` default flips to `true` (**15.4**). Liquid Clustering reaches GA (15.2). Run `scan-jar-jdk.sh`; A/B JDBC timestamps. |
| 13.3 LTS | 15.4 LTS | Double hop — **every** landmine above at once: CWD + 500 MB cap, DBFS libraries, JDK 17, Python 3.11, JDBC calendar flip. Highest-risk single jump; stage it in pre-prod and run both scanners plus a JDBC timestamp diff before cutover. |
| 15.4 LTS | 16.x+ | JDK 17 remains the target; re-verify any library that was bridged via `dbfsLibraryInstallationAllowed` is now on Workspace/UC volumes. Spark 4.x-era changes apply — _(out of scope here; read the 16.x notes)_. |

## Sources

- Databricks — _What is the default current working directory?_ (DBR 14.0 CWD move,
  workspace-file behavior), docs.databricks.com `/files/cwd-dbr-14`.
- Databricks — _What are workspace files?_ (500 MB per-file limit),
  docs.databricks.com `/files/workspace`.
- Databricks — _Databricks Runtime 15.1_ release notes (JDK 11 removed / JDK 17
  recommended; DBFS-root library storage deprecated and disabled by default, re-enable
  via `spark.databricks.driver.dbfsLibraryInstallationAllowed`; default Python 3.11),
  docs.databricks.com `/release-notes/runtime/15.1`.
- Databricks — _Databricks Runtime 15.4 LTS_ release notes
  (`spark.sql.legacy.jdbc.useNullCalendar` default set to `true`; JDBC TIMESTAMP
  impact), docs.databricks.com `/release-notes/runtime/15.4lts`.
- Databricks — _Announcing General Availability of Liquid Clustering_ (GA on DBR
  15.2, May 2024) and _Use liquid clustering for tables_ (GA on Delta tables, DBR
  15.2 / 15.4 LTS and above), databricks.com/blog + docs.databricks.com
  `/tables/clustering`.
- OpenJDK — JEP 320 (remove Java EE / CORBA modules) and JEP 403 (strongly
  encapsulate JDK internals), for the JDK 11 → 17 library-break classes.
