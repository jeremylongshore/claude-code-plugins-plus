---
title: "The Third State: When Your Checkout, Image, and Docker Volume All Disagree"
description: "A rebuild succeeded and nothing changed. How Docker named volumes shadow your image, and how to write a deploy smoke check that asserts on the served bytes."
date: "2026-07-26"
tags: ["deployment", "docker", "ci", "devops", "named-volumes", "smoke-testing", "verification"]
featured: false
---
A rebuild succeeded. Docker reported healthy. The site served the same bytes it had been serving for weeks.

That was July on `now-lms`, a fork of an open source Flask learning management system that Intent Solutions runs in production at `learn.intentsolutions.io` (Contabo VPS, Docker Compose, PostgreSQL 16, Caddy in front). Fork issue #14 recorded the actual problem: nobody could answer "what is deployed?" without shelling into the running container and hashing files by hand. Three artifacts each claimed a different answer.

The git checkout on the server said one commit. The Docker image had been built from a second. The theme actually being served came from a third state that someone had hand copied into the Docker volumes at some earlier point, and which no commit anywhere described.

36 commits landed on 2026-07-26 aimed at closing that gap. This is what the failure was, what the measurement said, and what is still unproven.

## Why the rebuild changed nothing

A Docker named volume shadows the image's copy of the files it holds, so the rebuilt image updates while the container keeps serving stale bytes out of the volume that outlived the rebuild.

Two environment variables carry more weight than they look like they do.

`NOW_LMS_THEMES_DIR` (`/app/themes`) is not a themes folder. It is Flask's entire template root. `NOW_LMS_DATA_DIR` (`/app/data`) serves every static asset. Both are Docker named volumes.

Upstream's code populates those directories only when they are empty. It is effectively a `copytree(dirs_exist_ok=True)` gated on an emptiness check. That guard is reasonable on first boot and actively harmful on every boot after it. Once the volumes have content, a rebuild picks up your new templates, bakes them into the image, starts the container, and the container reads templates from the volume instead. The image updates. The served bytes do not.

Nothing errors. `docker compose up -d --build` exits zero. The health check passes, because the app is genuinely healthy: it is serving old files correctly.

This is the shape of the bug worth generalizing. The stateful layer is where the identity chain breaks, because it is the only layer that survives the thing you replaced.

## Fix one: the image knows its own commit

Commit `ecb2388` closed three P0 beads. The first one gives every image a name it cannot lie about.

```dockerfile
ARG BUILD_SHA
RUN test -n "${BUILD_SHA}" && echo "${BUILD_SHA}" > /app/BUILD_SHA
LABEL io.intentsolutions.commit="${BUILD_SHA}"
```

```yaml
build:
  context: .
  args:
    BUILD_SHA: ${BUILD_SHA:?run the deploy via scripts/deploy-vps.sh, which sets BUILD_SHA}
```

There is no default value, on purpose. A build that forgets `BUILD_SHA` fails instead of minting one more unidentifiable image. That was verified in both directions: `docker compose config` succeeds with the variable set, and fails with that exact guard message without it.

Two read paths, because they answer different questions. The file is readable at runtime by the app or by an operator who is already inside the container. The label is queryable by Docker without starting anything, which is what you want when you are triaging a stopped container.

## Fix two: an explicit refresh, not a delete

The volume trap needs a step that runs every deploy, not a guard that runs once. In `scripts/deploy-vps.sh`, after the build and after the container reports healthy:

```bash
docker compose exec -T app sh -c \
  'cp -a /app/now_lms/templates/. /app/themes/ && cp -a /app/now_lms/static/. /app/data/'
```

The trailing `/.` matters. `cp -a src/. dest/` has merge semantics: files present in the image overwrite their stale copies in the volume, and anything that exists only in the volume (user uploads living under `/app/data`) is left alone. The script then restarts the app so Jinja drops its compiled template caches.

The alternative was deleting the volume copies to force the empty only guard to repopulate them. That was rejected for two reasons. Deletion destroys anything that exists only in the volume, which includes real user data. And it makes correctness depend on the empty only guard firing at exactly the right moment in the boot sequence, which is a timing argument rather than a guarantee. The sync is deterministic and idempotent. Run it twice and nothing changes.

The same script refuses to deploy a dirty checkout: `git diff --quiet` against both the worktree and the index, exit 1 with `git status --short` printed if either is dirty. If the checkout is not a commit, the deploy cannot claim to be one.

## The mailto link that no mail client would send

While assembling the response body assertions that fix three's smoke check would need, one of them caught a live bug that had been shipping to users.

The theme built its access request link like this:

```jinja
href="{{ 'mailto:' ~ (contact_email | urlencode) }}"
```

Jinja's `urlencode` is `quote(value, safe="/")`. The `@` is not in the safe set, so it came out as `mailto:hello%40intentsolutions.io`. RFC 6068 section 2 defines the text between `mailto:` and any `?` as an addr-spec, which carries a literal `@`. Mail clients parse the percent encoded version as a local part with no domain and refuse to send it. Every "request access" click on the live site opened a compose window that could not be sent.

The fix was dropping `| urlencode` from the address while keeping it on the subject, where percent encoding is correct.

## Fix three: the smoke check refuses to lie

`scripts/deploy-smoke.sh` is the artifact from this day most worth stealing. It fails the deploy unless all of the following hold.

First, identity. `docker compose exec -T app cat /app/BUILD_SHA` must equal `git rev-parse HEAD` on the checkout. If the file is absent at all, it fails with "image predates the provable deploy work" rather than skipping the check.

Second, liveness. The container health status must be `healthy`. That check is necessary and nowhere near sufficient, for [the reason a health endpoint is not a correctness signal](/posts/liveness-without-health-is-theater/): this container was healthy the entire time it served the wrong files.

Third, and this is the one that changes how the whole thing behaves: the served page must carry markers that only the current commit can produce. It is fetched through the same loopback and header path that Caddy uses, so the assertion runs against the real request path:

```bash
curl -fsS -H 'X-Forwarded-Proto: https' http://127.0.0.1:8080/
```

Four assertions on that response body:

1. The front door actually renders (`isl-hero-copy` is present).
2. The mailto address contains a literal `@` and not `%40`.
3. The Credly badge iframe marker `embedded_badge` is present. This one specifically proves the volume refresh landed, because the stale volume copy predates the badge entirely.
4. Neither `unpkg.com` nor `cdn.jsdelivr.net` appears anywhere in the response.

The first two checks, identity and liveness, are about the container. This third check, the four assertions above, is about the bytes on the wire. A deploy check that only asks the orchestrator whether it is happy cannot detect a volume shadowing an image, because from the orchestrator's point of view nothing is wrong. You have to assert on what the user receives, and the assertion has to name a marker that only the new commit can produce. "The page returned 200" would have passed happily for the entire period the site was stale. A check that runs is not the same thing as a check that [validates something](/posts/passing-is-not-validating/).

## The gate that failed its own first run

Commit `fb8b5b9` added a CI test gate for the deploy line. Its first run, on PR #18, failed with `no such table: ad_sense` across a large slice of the suite.

The root cause was not the new code. `tests/conftest.py` falls back to `sqlite:///:memory:` when `DATABASE_URL` is unset. Each in memory SQLite database lives only for the connection that opened it. SQLAlchemy's default pool for `sqlite:///:memory:` keeps one connection alive per thread specifically to paper over that, but the fork's rewritten conftest still ends up handing `initial_setup()` and the tests that follow different connections, so the schema `initial_setup()` creates is invisible to the connection the test actually runs against. Upstream's conftest survives this arrangement. The fork's rewritten one does not. The same failure reproduced locally, which is what proved it was the fork's conftest and not the CI runner.

The fix (commit `9e19ee3`) was to run the gate against real PostgreSQL 16, mirroring the existing `release.yml` recipe verbatim: the runner's built in postgresql service, the same role and database grants, the same pg8000 driver. A file backed SQLite workaround was measured first and rejected, because it trades the missing table errors for roughly 100 UNIQUE constraint collisions between fixtures. Production runs Postgres 16, so the honest gate tests the engine that is actually deployed.

Fixing `conftest.py` itself was ruled out of scope. It is shared test infrastructure that the pending v2.0.0 upstream sync replaces wholesale, so patching it now buys a merge conflict and nothing lasting. An interim commit (`b7264a0`) makes the Postgres test step advisory until that sync repairs the suite. The gate is real but not yet blocking, and saying otherwise would be the same category of lie the smoke check exists to prevent.

## Measuring the fork sync instead of estimating it

The same deploy discipline applies here: trust the artifact, not the claim about it, whether the artifact is a running container or a merge plan. The same day, the v2.0.0 upstream sync got mapped with measured data rather than the previous plan's estimates. Divergence: 41 ahead, 100 behind, with 35 of the 41 non merge.

A test merge, run with `git merge-tree --write-tree --name-only`, produces 61 conflicted files. The earlier plan assumed 84. More useful than the correction: 60 of those 61 are files touched by four retired i18n commits, a fork local Spanish to English translation layer that upstream's own i18n work has since superseded. The only non i18n conflict is the Dockerfile, from a commit already fixed upstream.

So the conflict count for the work actually worth keeping is zero.

"Merge, then revert the dead commits" was tried and does not work. Three of the four conflict on revert, because later fork commits build on them. That route leaves 56 files to hand resolve.

The chosen strategy is to branch from `upstream/main` and cherry pick only the must survive set. The dead i18n commits are never replayed, so their 60 conflicts cannot occur by construction. That is a categorically different guarantee than resolving them 60 times by hand, where every manual resolution is one more chance to reinstate a Spanish string or silently drop an upstream fix.

Two corrections surfaced during the mapping, both of which would have caused production regressions:

- One commit was on the "dies in the sync" list and must survive. Upstream v2.0.0 still hardcodes Spanish in `now_lms/auth.py` and `now_lms/static/js/paypal.js` with no gettext wrapper, and a catalog cannot translate an unwrapped string. Dropping that commit reverts production to Spanish.
- A fresh PostgreSQL bootstrap fix. Upstream PR #179 reports `merged=true`, and its commits did land in `upstream/main`. A later, unrelated squash merge for a different feature was cut from an older snapshot of the same file, and it silently reverted the fix on the way back in. `alembic.stamp()` appears nowhere in upstream's current tree, and the test file that #179 added is absent upstream. The fix was merged, then overwritten by a later merge. Dropping this commit from the fork would reintroduce a bootstrap failure that originally crash looped the deployment.

The second one is the transferable lesson, and it is sharper than it first looks. "The PR says merged" is not the same claim as "the code is in main today". Ancestry is not enough either: those commits really are ancestors, and the code is still gone, because a squash merge cut from a stale snapshot can revert a landed fix without a single conflict and without anything in the PR's status changing. The only claim worth trusting is the current tree. Grep for the symbol.

Migration risk was read rather than assumed. The live production database is stamped at a revision inside upstream's chain, so six migrations will run. Production was built by `create_all()` from models and then stamped behind several of those migrations, which is normally the exact setup where `alembic.upgrade()` dies on "already exists". All six were read line by line: each one inspects the schema and returns early when its change is already present, so a clean upgrade is expected. A snapshot gate stays mandatory regardless, because one migration moves a live `csrf_seed` value and a bad rename there invalidates every session. Idempotence against a `create_all()` schema is a property to demonstrate, not one to assume.

## The same failure class, a different repo

The identity chain breaks the same way in any system that reports a verdict without checking whether its own inputs resolved. Here is that same shape of failure, one repo over. `claude-code-plugins` has a version coupling drift watch at `scripts/kernel-vendor-hash.mjs`. It was printing a green check for a check that never ran.

Three faults, found together (commit `713955a3d`). `KERNEL_REPO_PKG` resolved two directories up instead of one, to a path that does not exist, so the kernel identity never resolved locally and two of the check's legs were silently skipped. With that input unresolved and no violations recorded, the CLI printed a checkmark and "ordering + staleness OK (or skipped where inputs absent)": absence of a violation rendered identically to a pass, and a real 17 day staleness breach read as clean on every local run. The report footer was a string literal asserting that the kernel pin tracked the latest published version, which went false the moment the next version shipped.

Fixes: a candidate path list instead of one guessed path; skipped legs now report "INCONCLUSIVE ... This is NOT a pass" and name which input failed to resolve; the footer is derived from live values each run.

The decision that matters most moved the verdict out of the printer into an exported pure function, `verdictFor()`. A verdict that lives only in the presentation layer is untestable, which is precisely how the original fail open survived for as long as it did. Tests went from 20 to 25, and the fix was mutation verified: reintroducing the fail open by changing `if (missing.length > 0)` to `if (false)` flips exactly 2 of the 5 new tests.

A follow up the same day (`ddec6a195`), prompted by an automated reviewer note, closed a worse hole in the fix itself. `verdictFor` read `report.identities.V_vendored.version` directly, so a report carrying no `identities` key would throw a TypeError in the middle of printing. A guard that crashes is not a guard, and it is a strictly worse failure mode than the fail open it replaced. Optional chaining lets a malformed report degrade to a named missing leg. Tests 25 to 26.

## What is still open

- The deploy work has not been proven end to end. Its real proof is the first production deploy, which runs the smoke check as its final step. Local verification so far is `bash -n` plus shellcheck clean on both scripts, and `docker compose config` validated with and without `BUILD_SHA`.
- The Postgres CI step is advisory, not blocking, until the v2.0.0 sync repairs the test suite.
- The v2.0.0 sync is planning only. Nothing in the migration map has been executed.

## The rule

Every layer in your deploy must be able to state which commit it is, out loud, without you hashing anything: the checkout, the image, and above all the stateful layer that outlives both. Then verify by asking the layer that cannot be faked. Fetch the page a user would get, and assert on a marker that only the commit you just shipped could have produced. An orchestrator reporting healthy is a claim about the container. The bytes on the wire are the only claim about the deploy.
