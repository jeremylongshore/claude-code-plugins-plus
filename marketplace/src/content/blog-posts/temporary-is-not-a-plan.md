---
title: "Temporary Is Not a Plan: Fork Discipline for an Adopted LMS"
description: "Adopting an open source LMS got us live in days. What keeps a fork from becoming a private product: a named upstream path and a written retirement condition."
date: "2026-07-21"
tags: ["architecture", "devops", "docker", "open-source", "debugging"]
featured: false
---
Calling a patch temporary is not a plan. A retirement condition written into the commit is.

Every change your fork carries against someone else's core gets a named upstream path and the condition under which it dies. Otherwise the fork quietly becomes the product you swore you would not build.

That rule got written down on 2026-07-21, after a day of paying for the decision that made it necessary.

## The problem: an LMS is bigger than it looks

The Claude Partner Network cohort needs one training platform. The question was whether to extend an existing lightweight study-notes and question-bank hub into a full LMS, or adopt a mature open source one.

An LMS is a deceptively large surface. Course and lesson modeling, enrollment, progress tracking, certificates, evaluations, roles and permissions, auth, sessions, payments, email, forums, coupons, uploads, PDF generation, multi-database support, i18n, admin dashboards, reporting, a public API. Four items on that list are code you should not hand-roll under any circumstance: auth, payments, uploads, sessions. Four out of nineteen, and they carry nearly all of the breach risk. They are also the parts a two-person team has the least business owning.

So the call was adopt, not build. Decision record 032 puts it in one line: you don't build a POS system to open a restaurant, you buy Aloha and put your energy into the menu.

NOW-LMS (`bmosoluciones/now-lms`, Apache-2.0, Flask and Babel) ships all of it. Fork it, deploy it, put the scarce time into content and branding.

The record also names the costs honestly, because "adopt" is not free:

- You inherit someone else's architecture and someone else's bugs, which is [the supply chain problem](/posts/software-supply-chain-security/) wearing a different hat. Seven deployment bugs surfaced getting it live.
- NOW-LMS is Spanish-first. The English catalog is empty.
- Single-maintainer bus factor.
- Customization discipline is mandatory, because deep custom behavior is a merge tax forever.

The bugs are the visible cost. They are not the real risk. The real risk is that the fixes quietly become a private fork nobody can ever merge back, and eighteen months later you are maintaining an LMS after all, except now it is a divergent one with no upstream and no community.

## Seven bugs, none of them fork-local

Between 10:43 and 12:46 the deployment bugs got root-caused, five of the seven paired with a named regression test. The test is not ceremony. It is what makes the fix legible to a maintainer who has no reason to trust a stranger's diff, and it is the difference between a fix and [a green check that gates nothing](/posts/when-green-ci-proves-nothing/):

| Fix | Root cause |
|---|---|
| `fix(wsgi)` | `ProxyFix` referenced an undefined `app` instead of `flask_app`, crash-looping startup whenever `FORCE_HTTPS` was set |
| `fix(wsgi)` | Waitress did not trust a reverse proxy until `NOW_LMS_TRUSTED_PROXY` was honored |
| `fix(assets)` | Bundled frontend assets were not populated when `node_modules` was missing |
| `fix(docker)` | `package-lock.json` was copied after `npm ci` instead of before, so the lockfile never applied |
| `fix(db)` | A fresh PostgreSQL database did not bootstrap correctly on first boot |
| `fix(db)` | The Alembic stamp used a cached connection instead of a scoped one |
| `fix(db)` | The Alembic stamp ran for apps never registered with the extension |

The first one is the cheapest to understand and the most instructive:

```python
# broken: the local variable is flask_app, so `app` is undefined here
flask_app.wsgi_app = ProxyFix(app.wsgi_app, x_for=1, x_proto=1, x_host=1, x_port=1)

# fixed
flask_app.wsgi_app = ProxyFix(flask_app.wsgi_app, x_for=1, x_proto=1, x_host=1, x_port=1)
```

The assignment target was already right. Only the argument reached for a name that does not exist in `create_app()`, and the whole block is guarded by `if FORCE_HTTPS:`, so it never runs until you deploy behind a TLS-terminating proxy. Then it is `NameError: name 'app' is not defined` and a crash loop at startup. A one-token bug that only fires behind a reverse proxy, which is exactly the configuration nobody runs during local development. That is the shape of most of the seven: correct on the maintainer's machine, broken the first time somebody deploys it the way a real deployment looks.

The load-bearing part is not the fixes. It is that none of them became fork-local. Each was authored on a branch off `upstream/main`, one branch per defect or per tight cluster of the same defect, matching upstream's conventional-commit and lint and test conventions. Not one squashed "fix deployment" patch sitting on a deploy branch.

Worth being precise about what that means today, because "seven fixes" does not mean seven open PRs. The seven land on five branches, and exactly one of those is an open PR. The three fresh-database defects are one tight cluster and go up together as [#179](https://github.com/bmosoluciones/now-lms/pull/179). The assets fix, the docker lockfile-ordering fix, and the two wsgi fixes are authored and staged behind it, deliberately: the first merge banks identity with a maintainer who has never seen this contributor before, and opening five PRs at a stranger at once is how you get all five ignored.

The operator direction on this was blunt and repeated: "I don't want you to patch anything, I want root cause fixes," and later "fix it, no shortcuts." Root-causing costs more on the day. It is the only version of the work that is upstreamable, because a maintainer will not take a patch that papers over a symptom in someone else's deployment.

## The healthcheck that hung on its own redirect

The best bug of the day landed at 17:20 and it is worth telling properly, because the symptom pointed at the wrong system entirely.

The container flapped `unhealthy`. Meanwhile `learn.intentsolutions.io/health` returned 200 from the outside, continuously. A container reporting sick while the site it serves is demonstrably fine is the kind of contradiction that gets explained away as flakiness.

It was not flaky. The same `docker-compose.yml` that defined the healthcheck also set `NOW_LMS_FORCE_HTTPS="1"`. So a plain-http request inside the container did this:

```
GET http://127.0.0.1:8080/health  ->  301  ->  https://localhost/health
```

Nothing listens on 443 inside the container. TLS terminates at Caddy, upstream. The old probe used `urllib.request.urlopen`, which follows redirects by default, so it chased the 301 to a port that was never going to answer. Measured from inside the container: the old command ran over 120 seconds, well past the 10 second healthcheck timeout that killed it every interval.

One honest gap worth naming, because the post's whole argument is about root cause rather than symptom. A connection to a closed port on loopback normally returns an immediate RST, which would fail fast rather than stall. A stall over 120 seconds looks much more like a SYN that never got answered at all, which is roughly Linux's default TCP connect timeout. The likely mechanism is `localhost` resolving to `::1` first and the SYN being silently dropped rather than refused inside the container's network namespace, which is exactly what turns a fast failure into a full connect timeout. That last step was not proven, and the commit message does not prove it either. What was proven is the redirect, the hang, and the fix.

Either way the healthcheck was inconsistent with the app's own configuration, set four lines above it in the same file.

The fix sends exactly what Caddy sends:

```yaml
healthcheck:
  test: ["CMD-SHELL", "python3.12 -c \"import urllib.request,sys; req=urllib.request.Request('http://127.0.0.1:8080/health', headers={'X-Forwarded-Proto': 'https'}); sys.exit(0 if urllib.request.urlopen(req, timeout=5).status==200 else 1)\""]
  interval: 30s
  timeout: 10s
  retries: 5
  start_period: 60s
```

Result: 200 in 0.137 seconds. Docker health flipped to `healthy`, FailingStreak 0.

### Why not exempt /health from FORCE_HTTPS

The obvious alternative is to special-case `/health` in application code so the HTTPS redirect skips it. That is a worse fix for two reasons.

First, it edits the global HTTPS-redirect path, which is security-posture code, to satisfy a probe. Second, and more important, it makes the probe test something the real traffic never does. This app is only ever reached through Caddy, loopback-bound, TLS terminated upstream. `NOW_LMS_TRUSTED_PROXY="*"` already trusts the forwarded header. So the probe should simulate the real path exactly, not carve out an exception that hides a class of production-only behavior from the healthcheck forever.

The `timeout=5` is belt and suspenders. If some future redirect or stall reappears, the probe fails fast, well under the 10 second healthcheck timeout, instead of hanging the whole interval.

That fix is fork-local and stays fork-local, and FORK.md classifies it that way on purpose: it is deploy manifest wiring, not core source, so there is nothing to upstream and nothing to retire. That classification is itself the discipline, and the rule set below is precise about why.

## The i18n bridge: the thesis in miniature

NOW-LMS is Spanish-source with an empty English catalog, so the site renders Spanish through msgid fallback. The cohort is English-speaking. That is a hard blocker, not a polish item.

The tempting move is obvious: complete the English catalog, commit it to the fork, ship, done. That move is exactly how a fork becomes a private product. Upstream routes translation through Crowdin (project 815986), so a permanently fork-carried `.po` file is a merge conflict on every single upstream sync, forever, in a file that grows every time upstream adds a string.

So the work split into two paths on purpose.

The bridge (fork, temporary). The bridge commit itself landed early, at 13:02, before most of the translation work existed. The bulk of the conversion followed between 18:20 and 19:35 on `deploy/now-lms-fixed`:

- 18:20, the English catalog completed plus the hardcoded Spanish chrome strings fixed: 3 files, 1806 insertions.
- 19:22, 62 authoring templates and forms wrapped in `_()` and `_l()`: 64 files, 2097 insertions, of which `messages.po` is +1301.
- 19:35, 27 view files of hardcoded Spanish flash and return messages: 28 files, 920 insertions.

The last two are the interesting ones. Roughly 500 Spanish strings were hardcoded in templates and views, which means they were not extractable by Babel at all. No amount of catalog work translates a string that never enters the catalog. Making them extractable is a prerequisite for anyone, upstream included, to ever translate this project properly.

The permanent path (upstream). Issue [#181](https://github.com/bmosoluciones/now-lms/issues/181) offers the completed English through the maintainer's Crowdin project, plus the `_()` and `_l()` wrapping as its own PR if wanted. Disclosure first, routed through the pipeline upstream already chose.

There was a real temptation to skip Crowdin and just PR the `.po` file. The operator shut that down with one question: "why would we assume they want to change from crowdin." Overriding a maintainer's existing pipeline because your path is faster is not contribution, it is a rejected PR with extra steps.

And the commit that carried the bridge says what it is. Not in a planning doc, not in a body paragraph someone has to expand. In the subject line:

```
chore(i18n): TEMPORARY English catalog bridge for our deploy.
Retire when upstream English lands via Crowdin (issue #181)
```

That is one subject line, wrapped here for width. It is the whole thesis in a single string: the temporariness and its exit condition are attached to the change itself, in the first thing anyone sees running `git log --oneline` in two years, not an intention that lives in someone's head until they leave.

The ordering is the part worth stealing. That commit is timestamped 13:02, hours before the 62 templates and the 27 view files. The retirement condition was written when the change was still small enough to abandon, not retrofitted onto three thousand lines that had already become too expensive to throw away. Retirement conditions written after the fact are just regret with better formatting.

The reasoning behind carrying it at all was a probability judgment, stated plainly at the time: what are the odds a single upstream maintainer does the translation work, and how soon? Not an assumption that he would. Not an assumption that he would not. A bridge exists because the answer is uncertain and the cohort needs English today. That is a different thing from assuming upstream will never act, which is the assumption that justifies permanent forks.

## Branding is data, not code

Theme work ran from 13:41 to 16:53: front door, mobile header and hero, the `/course/explore` catalog, auth pages, course-detail page. All of it through `NOW_LMS_THEMES_DIR`, which is a first-class extension point upstream already supports. Zero core edits.

The alternative that a lot of teams reach for is renaming the package or editing core views to get the branding they want. That single decision converts every future `git merge upstream/main` into a conflict-resolution session. It is not a one-time cost, it is a subscription. Branding through the theme layer costs more up front, precisely once, and then costs nothing on every sync afterward.

## The rule set

FORK.md and CODEOWNERS landed on fork `main` at 10:45, and the deploy branch got dressed with the same governance at 20:22. This is the transferable part, and it is short enough to copy:

1. **We do not build custom.** Use the project's native features. Where something is missing or broken, fix it upstream as a real contribution rather than carrying a private patch.
2. **Branding is data, not code.** Name, logo, and colors come from the theme and config layer. Never rename the package. Never edit core views for branding.
3. **`main` is a thin tracking mirror of upstream.** Fixes branch off it. Fork-local governance files live there and nothing else does.
4. **Every fork-local change is classified in writing, and anything touching core source carries a named upstream path and a retirement condition.** A change that touches core and cannot say where it is going and when it dies does not get carried.

Rule 4 is the one that does the work, and the scoping in it is a correction being made here rather than something already committed. The version that actually landed in FORK.md that night is simpler and absolute: every fork-local change has an upstream path and retires once upstream accepts it. That version does not survive contact with the table three paragraphs down, where two of the three rows are permanent by design. Writing this post is what surfaced the gap, so the scoped wording above is what FORK.md should say and currently does not.

FORK.md carries one row per fork-local change: what it is, which layer it touches, and how it resolves. Three rows today, and they resolve three different ways:

| Change | Layer | Resolution |
|---|---|---|
| `intent_learn` theme | Native theme layer, no core edit | Permitted permanently. Branding is data. |
| English i18n wrapping and catalog | Core source, the one intentional core patch | Retire once upstream accepts it via #181. |
| Healthcheck `X-Forwarded-Proto` | Deploy manifest | Fork-local deploy wiring, not core. Stays. |

Only the middle row is divergence. The theme is upstream's own extension point being used as intended, and the healthcheck is a deploy manifest that upstream has no opinion about. Neither one makes the next `git merge upstream/main` harder, which is the only thing a retirement condition is actually protecting against.

That distinction is the rule. Not "everything is temporary," which is unenforceable theater, but "permanent is a classification you have to write down and defend, and core divergence is the only kind that gets a death clock." A fork with three classified rows is a fork. A fork with an unbounded pile of "we needed this" patches, none of them classified, is a product you did not decide to build.

The other half of that discipline is procedural, and it took repeated correction during the day: which branch, which repo. Upstream fixes branch off `upstream/main` and PR to `bmosoluciones/now-lms`. Fork-local work sits on `deploy/now-lms-fixed`. Governance goes to fork `main`. Getting that wrong once produces a PR that a maintainer cannot merge and will not spend time untangling.

## How the day actually went

The whole day ran with **Claude Opus 4.8**, and late in the evening **MiniMax-M3** went in as an advisory reviewer on the deploy line (fork PR #8, the same reviewer pattern already running in the other repos). The interesting part is not the roster. It is the three corrections that shaped the output more than any prompt did.

The first was refusing patches. Twice, explicitly, when a symptom-level fix would have unblocked the deploy faster. The second was fork and upstream hygiene, asked repeatedly and specifically: are you on the right branch, are you opening the issue in the fork or the owner's repo, how does that work. The third was refusing to override Crowdin.

There was also a genuine surprise. Mid-day, evidence appeared of Docker and Caddy work moving in a tree nobody in this session had touched. The read at the time was correct: another human, working somewhere else. It was the upstream maintainer, pushing concurrently on the same area the fork was fixing. That is a good problem to discover early. It is also the strongest argument against the private-patch path, since a fork that diverges silently discovers those collisions at merge time instead.

## The same move, twice in one day

The morning had already made the same argument in a different repo.

The intent-os CI workflow ran roughly 28 jobs, one gate per job. That repo logged 862 GitHub Actions runs in 30 days while every other private repo logged between 0 and 13. GitHub bills a one-minute-per-job minimum, so each run billed about 28 minute-floors, plus 28 redundant checkouts and installs, for about five minutes of real work. That spend is what billing-locked the org's Actions.

The consolidation collapsed it to 4 jobs (gates, drills, secret-scan, advisory), all deriving from the same `package.json` aggregators the local `pnpm check` already runs. A CI matrix was the obvious alternative and it loses, because a matrix reintroduces one job per gate, which is the cost problem. A single chain is roughly 7x cheaper in billed floors and it makes local and CI the same thing.

Two threads, one instinct: refuse to own a surface you do not have to own, then install something that makes divergence visible instead of silent. For CI that is `scripts/validate-ci-parity.sh`, wired into `check` and break-tested by adding an orphan gate and watching it fail closed. For the fork it is the classification table.

The two mechanisms are not the same thing, and it is worth being precise about the difference. The parity script is an alarm: it detects drift that already happened. The retirement condition is an expiration date: it declares in advance when a thing should stop existing. One catches you after the fact, the other tries to make the fact impossible to forget. What they share is the assumption that neither discipline nor good intentions survive a busy quarter, so the check has to live in the repo rather than in a person.

## Takeaway

Adoption is cheaper than building right up until the fixes start piling up locally, and then it is quietly more expensive than building, because you get the maintenance burden of a custom product plus the constraint of somebody else's architecture.

The line between those two outcomes is not intent. Everyone intends to upstream it later. The line is whether each carried change is classified the day it lands: permanent and defensible because it sits at an extension seam, or temporary against core with a written date of death.

Classify it when it is small, or accept that you now own an LMS.

## Related Posts

- [Copying Files Is Not Installing](/posts/copying-files-is-not-installing/)
- [Passing Is Not Validating: A Green Check With No Teeth](/posts/passing-is-not-validating/)
- [Every Safety Gate Has a Failure Direction](/posts/every-safety-gate-has-a-failure-direction/)
