---
name: guidewire-local-dev-loop
description: Iterate on Gosu rules and configuration without paying the full 5–15 minute runServer rebuild every time. Use when standing up Guidewire Studio against a local InsuranceSuite instance, attaching an IntelliJ remote debugger to runServer, distinguishing changes that hot-reload from changes that force restart, or building a GUnit-driven TDD cycle for rule logic. Trigger with "guidewire studio", "gosu hot reload", "gosu debugger", "gunit", "guidewire runServer".
allowed-tools: Read, Write, Edit, Bash(gradle:*), Bash(java:*), Bash(jdb:*), Grep, Glob
version: 2.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatibility: Designed for Claude Code, also compatible with Codex and OpenClaw
tags:
  - guidewire
  - gosu
  - studio
  - hot-reload
  - gunit
  - debugging
---

# Guidewire Local Dev Loop

## Overview

Run a local InsuranceSuite instance and iterate on Gosu rule logic in seconds, not minutes. The single biggest productivity killer in Guidewire development is paying the 5–15 minute `gradle runServer` cold-start cost on every change because the developer does not know which edits hot-reload and which force a restart.

Three production problems this skill prevents:

1. **Restart cascade** — developer changes a Gosu rule, restarts runServer, waits 8 minutes, finds the rule was wrong, repeats. A full day disappears in restarts.
2. **Silent stale code** — Studio claims it hot-reloaded a class but the running JVM is still executing the old bytecode (common when interfaces change). Tests pass against stale code.
3. **GUnit drift** — unit tests for Gosu rules diverge from the rules themselves because the cycle to run a single test through Studio is too slow; developers stop writing them.

## Prerequisites

- JDK 17 (for Cloud release `202503`+)
- Guidewire Studio installed (IntelliJ-based, distributed by Guidewire)
- Local InsuranceSuite configuration zone (PolicyCenter, ClaimCenter, or BillingCenter)
- ≥16 GB RAM on the dev machine — runServer + Studio + the JVM debug agent need headroom
- Sample data loader configured for the chosen product (e.g., `PersonalAuto` for PC)

## Instructions

Build the inner loop in this order. Every step targets one of the three productivity killers above.

### 1. Start runServer once, keep it warm

Cold start takes 5–15 minutes; treat it as a session investment.

```bash
# Start in dev mode with debug agent on 8088, leaves the server attached to the terminal
./gradlew runServer -Pdebug=true -PdebugPort=8088 -Dgw.servermode=dev
```

`gw.servermode=dev` enables the hot-reload paths inside the JVM. `debugPort=8088` exposes the JDWP debug agent — attach IntelliJ to it once and leave it. Restart only when the **what hot-reloads** table below says you must.

### 2. What hot-reloads, what does not

Memorize this table — it determines whether the next edit costs 0 seconds or 8 minutes.

| Change type | Hot-reload? | Action |
|---|---|---|
| Gosu method body in an existing class | yes | save in Studio; runServer detects via `Reload Plugin` |
| Gosu rule (entity, validation, UW) body | yes | save; rule fires on next entity event |
| New Gosu class added to an existing package | yes | save; class is picked up on first reference |
| Gosu **interface** signature change | **no** | restart runServer (binary-incompatible class load) |
| New Gosu **plugin** registered | **no** | restart runServer (plugin registry is built once at boot) |
| PCF (Page Configuration Format) layout edit | yes | save; refresh the browser |
| New PCF page added to the navigation | partial | restart usually; `Reload Plugin` sometimes works in dev mode |
| Database schema change (new column, new entity) | **no** | restart with `gradle dropAndCreateDatabase runServer` |
| Localization bundle | yes | save; refresh browser |
| Messaging destination / App Event plugin | **no** | restart (plugin registry) |
| `config/server.xml` or `config/plugin/registry/*.xml` | **no** | restart |

When in doubt, **trust the JVM, not Studio**. Open the IntelliJ debugger, set a breakpoint on the changed method, trigger the code path, and confirm the breakpoint hits the new line numbers. Studio's "reloaded" status is informational, not authoritative.

### 3. Attach the IntelliJ debugger once per session

```
Run > Edit Configurations > + > Remote JVM Debug
  Host: localhost
  Port: 8088
  Module classpath: <your-config-module>
  Save → run with the bug icon
```

Once attached, breakpoints survive Gosu hot-reloads. The connection drops only on full runServer restart. Use conditional breakpoints (`policy.totalPremium.compareTo(BigDecimal("10000")) > 0`) for production-shaped data — never trust toy values.

### 4. GUnit cycle for rule TDD

Gosu rules are testable without a running server. GUnit tests run in seconds and should drive every non-trivial rule change.

```bash
# Run a single GUnit test class
./gradlew test --tests "com.acme.policycenter.rules.UnderwritingIssueRuleTest"

# Run all rule tests in a package, with continuous re-run on change
./gradlew test --tests "com.acme.policycenter.rules.*" --continuous
```

`--continuous` reruns the matching tests every time a file changes. Pair with the rule under test in a split editor — feedback loop drops to <5 seconds per save.

### 5. Sample data isolation per session

Every developer needs a deterministic fixture set, not whatever junk is in the shared dev database. Load a per-session sample at runServer start:

```bash
# Load the standard sample, then a project-specific overlay
./gradlew loadSampleData -PsampleData=default -PsampleData=acme-uat-fixtures runServer
```

Project-specific sample sets live in `modules/configuration/test/data/` and are checked in. Treat the dev database as ephemeral — never store work-in-progress data only in it; it dies on the next `dropAndCreateDatabase`.

## Output

A working local dev loop ships with all of the following:

- `gradle runServer` running in dev mode with `debugPort=8088` exposed; remote-debug connection attached from IntelliJ.
- The hot-reload-vs-restart table internalized and applied — at least 80% of edits cost zero restart time.
- A `gradle test --continuous` watcher running in a side terminal for GUnit-driven TDD on the current rule.
- Sample data loaded from a checked-in fixture set, reproducible across team members.
- A breakpoint validation habit: every non-trivial rule change is confirmed hot-reloaded by hitting a breakpoint in the new line, not by trusting Studio's reload indicator.

## Examples

### Example 1 — Pure rule edit, zero restart

```
1. Edit rule body in modules/configuration/gsrc/.../UnderwritingIssueRules.gs
2. Save (Ctrl-S)
3. Trigger the rule (issue a quote in the running PC instance)
4. Breakpoint hits the new line numbers; rule fires with new logic
5. Total time from save to confirmation: <10 seconds
```

### Example 2 — Interface change, controlled restart

```
1. Modify interface in modules/configuration/gsrc/.../IPolicyCalculator.gs
2. Recognize this is in the no-hot-reload row of the table
3. Stop runServer (Ctrl-C); start ./gradlew runServer -Pdebug=true -PdebugPort=8088
4. Wait ~8 minutes; reattach debugger
5. Resume work — accept the cost rather than chasing phantom bugs from stale bytecode
```

### Example 3 — TDD cycle on a new validation rule

```bash
# Terminal 1: continuous test runner
./gradlew test --tests "com.acme.policycenter.validation.HighValueAccountValidatorTest" --continuous

# Editor: write the failing test first, watch it fail in <5s
# Implement the rule, watch the test pass in <5s
# Commit when green; do not run the full server until the rule is locked
```

## Error Handling

| Symptom | Cause | Solution |
|---|---|---|
| Code change "saved" but breakpoint fires on old line numbers | hot-reload silently failed (interface change, plugin registry edit) | restart runServer; do not chase phantom bugs |
| `gradle runServer` hangs at `Starting server` for >20 min | full database rebuild from a recent schema change | check logs in `logs/PolicyCenter.log`; if schema migration is running, wait it out; if hung, `dropAndCreateDatabase` |
| GUnit test passes locally, fails in CI | dev database carries stale data the test depends on | tests must self-fixture (`@Before` loads needed entities); never trust ambient sample data |
| IntelliJ debugger drops every few minutes | runServer crashed and auto-restarted under a launcher | check `logs/PolicyCenter.log` for OOM; raise `-Xmx` in `gradle.properties` |
| Hot reload works on Day 1, stops working after a `git pull` | merged change touched the plugin registry without your local picking it up | restart; rebase pulls do not always invalidate the plugin cache |
| `ClassCastException` on a class you just edited | binary-incompatible change to a non-interface class (e.g., changed a public field type) | restart; field-type changes are interface-equivalent for the JVM |
| Breakpoint set in Gosu, never hits | the rule path is not actually exercised by the test action | verify in `logs/PolicyCenter.log` that the rule fired; common cause is rule conditions filtering out the test data |
| Studio shows red error markers everywhere after pulling main | dependency cache stale | `./gradlew clean compileGosu` (don't `clean` the whole project — it nukes runServer's database) |

For deeper coverage (containerized dev environments, multi-developer shared servers, plugin debug logging, custom datasource hooks), see [implementation guide](references/implementation-guide.md) and [API reference](references/API_REFERENCE.md).

## See Also

- `guidewire-install-auth` — once your local runServer integrates outbound to a Cloud tenant, auth layer applies the same as production
- `guidewire-sdk-patterns` — when local code calls Cloud API, the same client patterns apply
- `guidewire-ci-cd-pipeline` — promotion of locally-developed config through GCC slots; GUnit gates run there too
- `guidewire-core-workflow-a` — PolicyCenter workflows that local dev cycles target

## Resources

- [Guidewire Developer Portal](https://developer.guidewire.com/)
- [Gosu language reference](https://gosu-lang.github.io/)
- [JDWP — Java Debug Wire Protocol](https://docs.oracle.com/en/java/javase/17/docs/specs/jdwp/jdwp-spec.html)
- [Gradle continuous build](https://docs.gradle.org/current/userguide/continuous_builds.html)
