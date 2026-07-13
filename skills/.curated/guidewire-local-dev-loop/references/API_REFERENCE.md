# Guidewire Local Dev Loop — Tooling Reference

Configuration values, ports, file locations, and gradle task surface that informed the workflow in `SKILL.md`.

## Gradle task surface (most-used)

| Task | When | Notes |
|---|---|---|
| `runServer` | start the local InsuranceSuite instance | accepts `-Pdebug=true -PdebugPort=N`, `-Dgw.servermode=dev` |
| `dropAndCreateDatabase` | wipe + rebuild the local H2/Postgres dev database | required after schema changes; `runServer` reuses the existing database otherwise |
| `loadSampleData` | populate the dev database with checked-in fixture sets | `-PsampleData=<set>` repeatable |
| `compileGosu` | compile Gosu without starting the server | useful for fast syntax-only validation |
| `test` | run all GUnit tests | supports `--tests <pattern>` and `--continuous` |
| `clean` | wipe build outputs | does NOT drop the dev database |
| `check` | full CI gate locally — compile + test + lint | use before pushing |

Combine with `--continuous` for any task with file inputs to get watch-mode behavior.

## JVM debug agent

```
-agentlib:jdwp=transport=dt_socket,server=y,suspend=n,address=0.0.0.0:8088
```

`runServer -Pdebug=true -PdebugPort=N` injects the agent string above with the chosen port. `suspend=n` is critical: with `suspend=y`, runServer waits for the debugger to attach before booting, which adds 30+ seconds and breaks scripted starts.

| Port | Purpose |
|---|---|
| 8080 | InsuranceSuite HTTP UI |
| 8088 | JDWP remote debug (configurable via `-PdebugPort`) |
| 8181 | InsuranceSuite admin console |

In a multi-developer machine, give each runServer its own port range to avoid collisions.

## File locations (relative to config zone root)

| Path | Holds |
|---|---|
| `modules/configuration/gsrc/` | Gosu source — rules, classes, plugins |
| `modules/configuration/config/` | XML configuration — entity model, plugin registry, server.xml |
| `modules/configuration/test/` | GUnit tests + test fixtures |
| `modules/configuration/test/data/` | Sample data XML for `loadSampleData` |
| `logs/<Product>.log` | runServer runtime logs — first stop for any "weird behavior" |
| `gradle.properties` | per-developer JVM tuning (`-Xmx`, GC flags) |
| `build/runServer/` | runServer working directory; database files live here |

## Hot-reload reference (extended)

The table in `SKILL.md` covers the high-frequency cases. Edge cases:

| Edit | Behavior |
|---|---|
| Add a new method to an interface and implement it in one class | partial: existing implementations are not retroactively required to implement; runServer will throw `AbstractMethodError` on the next call into them — restart |
| Change a `@Returns` annotation on a Gosu method | hot-reloads, but only the metadata; if business logic depends on the annotation reflectively, restart |
| Edit a `Web Service` resource definition (REST or SOAP exposed) | restart — the service registry binds at boot |
| Add a localization key | hot-reloads on browser refresh |
| Edit `tsconfig.json` or build configuration | not Guidewire-side; rebuilds outside runServer |
| Change a Gosu enum constant | restart — enum identity is JVM-level |

When uncertain, fall back to the empirical test: set a breakpoint, exercise the path, confirm line numbers match the new source. The JVM is authoritative; tooling is informational.

## GUnit specifics

GUnit is JUnit-style for Gosu. Tests live in `modules/configuration/test/gtest/` and follow the convention `*Test.gs`.

```gosu
package com.acme.policycenter.rules

uses gw.api.test.TestBase
uses gw.testharness.TestSubject

@TestSubject(UnderwritingIssueRules)
class UnderwritingIssueRuleTest extends TestBase {

  function testHighValueAccountFlagsForReview() {
    var policy = createTestPolicy({ totalPremium: 50000 })
    var issues = UnderwritingIssueRules.evaluate(policy)
    assertContains(issues, "high-value-review")
  }
}
```

`TestBase` provides transactional rollback per test (no fixture pollution), entity construction helpers, and timer mocking. Use `@TestSubject` so the test framework can scope rule evaluation; without it, GUnit may run the rule against the full ambient database.

## Memory and runServer tuning

Default `-Xmx2g` is too small once sample data and a real config zone are loaded. Recommended for a 16 GB dev machine in `gradle.properties`:

```
org.gradle.jvmargs=-Xmx4g -XX:+UseG1GC -XX:MaxMetaspaceSize=1g
runServer.jvmArgs=-Xmx6g -XX:+UseG1GC -XX:MaxMetaspaceSize=2g -XX:+HeapDumpOnOutOfMemoryError
```

`HeapDumpOnOutOfMemoryError` is non-negotiable — when runServer OOMs (it will), the heap dump is the only way to figure out what loaded too many entities.

## Containerized dev environments

For consistent multi-developer behavior, a Devcontainer / GitHub Codespace setup that pre-provisions JDK 17, Gosu support, and the sample dataset cuts new-engineer onboarding from a day to an hour. The pattern is out of scope here — see the project's `.devcontainer/` if one exists, or the Guidewire Cloud Platform developer guide on remote development environments.

## Related references

- `references/implementation-guide.md` — extended walkthrough
- Sibling `guidewire-install-auth/references/API_REFERENCE.md` — auth side once local code calls Cloud API outbound
- Sibling `guidewire-ci-cd-pipeline` — same GUnit + sample-data pattern runs in CI gates
