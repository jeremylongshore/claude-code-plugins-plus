---
title: "Locked Out Of A Free Course: The Bug The Test Suite Could Not See"
description: "A Flask authorization bug locked every member out of free courses while tests stayed green. Status code asserts cannot see rendered state on a 200 page."
date: "2026-07-28"
tags: ["debugging", "testing", "python", "ci-cd", "devops"]
featured: false
canonical: "https://startaitools.com/posts/locked-out-of-a-free-course/"
---
Every founding member was locked out of both courses.

Intent Solutions Learn runs on a hard fork of NOW-LMS. We had just onboarded the first cohort of paying founding members, and the same night, an upstream v2.0.0 release was landing through a rehearsed cherry-pick branch. Into that, this: a member logs in, opens a course, and sees a link-less outline plus an Enroll button. The page returns 200. Clicking Enroll stacks a duplicate enrollment row. One member hit that loop three rows deep. The cohort showed zero progress rows across the board, which is what made it read as systemic rather than a one-off.

## The gate that demanded a payment that never exists

Root cause lived in `now_lms/db/tools.py`, in an access control helper called `verifica_estudiante_asignado_a_curso`. It required a completed or audit `pago` (payment) record unconditionally:

```python
# Before: regitro.pago is NULL, so the Pago lookup finds nothing
# and the function falls straight through to False.
if regitro:
    pago = database.session.execute(
        database.select(Pago).filter(Pago.id == regitro.pago)
    ).scalars().first()
    if pago:
        if pago.estado == "completed" or pago.audit:
            return True
        return False
    return False
```

The provisioning path creates `EstudianteCurso` rows with `pago=NULL`. So a free course, enrolled by an operator, was denied to the enrolled student. And this helper is THE gate. The take template sets `permitir_estudiante` from it on line 3, which overrides anything the route passes, and every resource route runs through it. One authorization helper, whole platform.

This was an upstream bug. It existed before the v2.0.0 sync. That matters later.

The fix shipped as three changes together (commit 8b43165):

```python
# After: the enrollment lookup also filters vigente=True,
database.select(EstudianteCurso).filter(
    EstudianteCurso.usuario == current_user.usuario,
    EstudianteCurso.curso == id_curso,
    EstudianteCurso.vigente == True,  # noqa: E712
)

# and an enrollment with no payment record is valid on a FREE course.
curso = database.session.execute(
    database.select(Curso).filter(Curso.codigo == id_curso)
).scalars().first()
if curso is not None and not curso.pagado:
    return True
return False
```

1. `db/tools.py`: an enrollment with `pago=NULL` now grants access when the course is free, and the SQLAlchemy lookup filters `vigente=True`.
2. `courses/enrollment.py`: `tomar_curso` passes `permitir_estudiante` explicitly and `moderar_curso` passes True. Harmless today under the template override, correct if upstream ever drops the template-side set.
3. `cache.py`: `cache_key_with_auth_state` now includes the user identity in the key, not just an auth-or-anon bucket.

### The bug nobody was hunting: shared cache keys

That third change deserves its own paragraph. Redis went live the same night. With a shared auth bucket, one member's cached course-take page, evaluation attempts included, would have been served to every other authenticated member. Nobody was hunting for a cache bug. The lockout was the thing that sent someone into that file. The worst incident of the night is the one that did not happen.

Verification, on a copy of live production: before the fix, the take page rendered 0 resource links and 1 enroll button. After, CCA-F rendered 10 resource links and 0 enroll buttons, IS-START rendered 4 and 0, and the first lesson of each opened 200.

Those counts are the receipt. Not "the fix looks right", not "tests pass": the exact broken page, reproduced, then re-rendered correct.

The duplicate enrollment rows those members stacked stayed where they were. They are inert once the gate reads correctly, and the same reasoning that rejected the data fix applies to cleaning them up mid-onboarding.

## Why not the obvious approach?

The obvious fix was to backfill synthetic `pago` rows on production for the affected members. One SQL statement, cohort unblocked, everyone moves on.

Rejected, for two reasons. First, the helper is wrong for every admin or bulk enrollment any operator will ever make. Patching the data leaves the trap armed for the next cohort, and the one after that. Second, mutating production data in the middle of onboarding is exactly when you should be mutating production data least. Fix the gate, not the rows.

There is a coda to this decision. Mid-thread, the steering instruction was blunt: "act as cto do the right thing that will not only help us but help the creator as well please due diligience is required check yourself with auditors." The bug is upstream's, present in NOW-LMS before our fork diverged. So the fix gets offered back upstream, not hoarded in the fork. That course-correction turned a local patch into a contribution.

## The whole suite was blind, and the reason is structural

The repo's own test audit records it plainly: 51 test files green, smoke green, deploy green, through the entire lockout.

That is not sloppiness. It is structural. The failing surface was rendered state: a 200 response carrying an outline with no links and an enroll button the member should never see. A Flask test-client assertion on `resp.status_code == 200` passes on the broken page and on the fixed page identically. The tests pass because the status code is the wrong surface to assert on. No amount of additional status-code tests would have caught it.

So the fix was a new layer, not more of the old one: a browser end-to-end layer (commit a203d3c).

1. An `e2e/` directory using Playwright plus pytest.
2. Conftest boots the real app as a waitress subprocess against a seeded scratch database.
3. Six browser tests: login, panel, course take shows lessons and no enroll CTA, lesson opens, plus the anonymous gating boundary.
4. The seeded member carries the exact production shape that broke.

Item 4 is the detail that makes this a real regression pin rather than a smoke test.

```python
# e2e/conftest.py
# THE U12 SHAPE: enrollment with no pago row. Must grant access on a
# free course. This is the founding-member lockout regression pin.
s.add(
    EstudianteCurso(
        curso=E2E_COURSE,
        usuario=E2E_MEMBER,
        vigente=True,
        pago=None,
        creado_por="e2e-admin",
    )
)
```

The bug is pinned where members would feel it, not where the code happens to be convenient to test.

And it was [mutation-checked](/posts/coverage-vs-mutation-testing-rules-engine/), which is the part most teams skip. Restore the pre-fix `db/tools.py`, run the pin test: it fails exactly the way members experienced it, link count zero, enroll button present. Restore the fix: green. A test that has never failed for the right reason is not yet a test.

Deps live in `e2e/requirements.txt` outside the hash-pinned `test.lock`, because playwright wheels are platform-variant. The job shipped advisory, labelled that way in the workflow, which mattered a few hours later.

## Flipping the CI gate, and the bug the flip immediately found

Commit daf35ce flipped the PostgreSQL suite and the browser E2E job from advisory to blocking. `continue-on-error` removed from both.

Each had its own reason for being advisory, and both reasons had just expired. The PostgreSQL suite was advisory to avoid gating on roughly 40 inherited failures that the v2.0.0 sync repaired, and that sync landed the same night. The browser job was advisory because it was hours old and unproven, and it had just proven itself by pinning the lockout.

The flip caught its first real find while being prepared. Bare `pytest` had been collecting `e2e/` and dying at collection since the E2E commit landed, which meant the PostgreSQL job had been failing at collection and reporting nothing, invisible precisely because it was still advisory. Fixed by scoping default collection:

```ini
# pytest.ini
[pytest]
testpaths = tests
```

Chosen over installing playwright in the unit job, because the E2E layer deliberately stays outside the hash-pinned lock. One more deterministic failure got repaired in the same pass: v2.0.0 added `alembic.stamp()` to `initial_setup`, and one test's bare mock app was never `alembic.init_app`'d, so its alembic collaborator is now mocked like every other one. Docs were updated in the same commit so no file still claimed the test half was advisory.

The pattern is worth one sentence: an advisory gate hides its own breakage, because it reports on code while silently failing to run.

## Landing v2.0.0, and two regressions no test could see

The landing used `git merge -s ours` of the deploy line into the sync branch (commit bf19e1d). It records ancestry so the landing PR fast-forwards cleanly, and changes zero bytes of the sync tree. Every deploy-line commit was already represented there, 12 as v2.0.0-adapted equivalents and five as that night's cherry-picks, so a textual merge could only have introduced states the rehearsal never saw. The rehearsed tree is the artifact being landed.

The conflict surface behind that call was measured, not estimated, using `git merge-tree --write-tree` so no working-tree merge was needed: 82 conflicts, 80 of them from a droppable i18n layer, leaving a residue of exactly two files that were already planned for.

What the rebuild broke, it broke silently.

First, `docker-compose.yml` lost `NOW_LMS_LANG=en` and `NOW_LMS_TRUSTED_PROXY`. Without the first, the app defaults to Spanish and the whole production UI flips language on deploy. Without the second, the app distrusts Caddy's forwarded headers, breaking per-IP rate-limiter keying and scheme detection. Caught by a pre-landing branch diff, not by any test, because compose env is outside the suite's reach. Same lesson as the lockout wearing different clothes: the failure surface sits where the assertions do not.

That Spanish default even showed up inside the test suite as friction. One failure was a language assertion, not a logic bug: `assert 'Debe aprobar todas las evaluaciones' in 'You must pass all evaluations. 1 of 1 evaluations not passed.'` The test was asserting Spanish output against an app running in English. The assertion is not wrong: the app defaults to Spanish under testing mode and English otherwise, so that expectation only breaks when the suite runs outside test mode.

Second, a full-site redirect loop, observed live immediately after the v2.0.0 deploy. Upstream's entrypoint puts its own Caddy in front of the app, and its Caddyfile does `header_up X-Forwarded-Proto {scheme}`, overwriting the host Caddy's `https` with `http` on the loopback hop. The app then 301s every request, its own healthcheck included, to https, which arrives as http again. Fixed by flipping `NOW_LMS_FORCE_HTTPS` to 0, chosen over rebuilding the image with a patched Caddyfile because it restores service in one container recreate and keeps the upstream image byte-identical.

## Security hardening, shipped separately on purpose

This is adjacent work that shipped the same day, and the sequencing decision is the part worth keeping. Commit 0e2f219 landed four fixes from a security audit on the current deploy line, deliberately not on the sync branch. They harden a live public form and a live CI pipeline, so they should not wait behind the sync, and stacking two high-blast-radius changes on one day destroys the signal about which one broke something.

The best of the four: the intake's rate-limit bucket sweep ran on every request and walked every bucket while holding the lock. An attacker holding N live buckets (one IPv6 /64 is enough) made every later POST an O(N) critical section. The anti-spam control becomes the amplifier. Now it sweeps on a 60 second interval with a hard 10k-bucket cap and oldest-first eviction.

Also shipped in that commit: an https scheme check before `urlopen` (the `# nosec B310` there was suppressing exactly the check that would catch a misconfigured `file://` webhook), gitleaks pinned to a digest and the review action pinned to a commit SHA (that action receives a secret and holds `pull-requests: write`, so a moved tag is the worst case), and `deploy-smoke.sh` dropped its 404 arm, because a missing course 302s identically, so a 404 could only mean the blueprint stopped registering, which is the exact regression the smoke exists to catch and the arm was swallowing. That last one belongs with the lockout: [a check that accepted the failure it was written to detect](/posts/every-safety-gate-has-a-failure-direction/).

## Three failures, one shape: surfaces the checks could not see

The now-lms work ran with Claude Fable 5 and Claude Opus 5 across about 5 sessions: 345 turns, 892 tool calls, roughly 1200 minutes end to end. It was not frictionless. Two tool calls got rejected outright mid-flight with "STOP", and the CTO course-correction above is what pointed the fix upstream instead of leaving it a private patch. The steering was blunt, and the output was better for it.

The transferable lesson sits in one place: the lockout, the compose regression, and the advisory-gate breakage are the same bug at three altitudes. Each one lived on a surface the existing checks structurally could not see: rendered state behind a 200, env vars outside the suite, a CI step that reported without running. The fix each time was not more assertions of the old kind. It was a new layer aimed at the surface that actually failed.

## Also shipped

- intent-os: an estate-owned CI executor plus a gitleaks fingerprint allowlist, the estate runner fleet registered (then narrowed, two repos skipped per owner), and the merge-lock re-anchored on a dispatch-free head. PRs #274 through #276.
- buzz: Intent Solutions fork infrastructure stood up for the adoption (Phase 1), the update-lane spec hardened per review findings, and the contribution lane consolidated onto the org fork. PRs #2, #3, #5.
- claude-code-plugins: the `canonical` prop added the day before finally got wired, so 186 syndicated blog posts now point at their canonical home on startaitools.com instead of competing with it (PR #1136). Plus npm downloads surfaced in the marketplace hero (PR #1137).

## Related Posts

- [When LLM Output Lies Instead of Crashing](/posts/when-llm-output-lies-instead-of-crashing/) : another failure class that returns success while being wrong
- [Two False-Positive Fixes, Same Root Cause](/posts/two-false-positive-fixes-same-root-cause/) : checks that pass for the wrong reason
- [Verify the System Map Against Live Infra](/posts/verify-system-map-against-live-infra/) : measuring reality instead of trusting the document
