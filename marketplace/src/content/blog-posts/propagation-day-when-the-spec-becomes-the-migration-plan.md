---
title: "Propagation Day: When the CLAUDE.md Spec Becomes the Migration Plan"
description: "Three CLAUDE.md spec entries hit critical mass on the same day across nine repos. The lesson is not the volume — it is that writing the spec first turned propagation from toil into a script run."
date: "2026-04-30"
tags: ["claudecode", "engineering-management", "secrets", "testing", "infrastructure"]
featured: false
---
On April 30, three patterns that had been written into `~/.claude/CLAUDE.md` weeks or months earlier as "TO-DO: propagate to all repos, then delete this section" all reached critical mass on the same day. The bd-sync three-layer mirror got its first real-world execution against 24 beads at the Braves Booth repo. The SOPS+age secrets standard flipped on in six repos via one idempotent helper script. The marketplace `compatible-with` → `compatibility` rename swept across 2,849 skills in one batch run. The numbers add up to the kind of graph that looks impressive in a screenshot — 3,000+ files changed, 45 PRs merged, 9 repos touched.

The numbers are not the lesson.

The lesson is operational and unsexy. Writing the spec text first is what made every one of those propagations tractable. Each spec entry was load-bearing in a way that conventional documentation is not: the spec text *was* the migration plan. The validator *was* the gate. The "delete this section when 100% comply" line *was* the success criterion. Without that discipline up front, multi-repo propagation is hand-rolled toil — bespoke scripts, missed repos, drift four months later. With it, propagation is a script run.

This is a post about what that looks like in practice across three different propagations on a single day, what it cost, and what it owes back. The counterweight at the end is not optional reading — one of the propagations was reactive, not proactive, and a separate audit on the same day handed back a D grade on the very methodology powering this kind of week. The discipline eats its own dogfood. The food is sometimes bitter.

## Spec entry #1: bd-sync three-layer mirror

The first propagation is the cleanest illustration of the pattern because it is the youngest. The spec entry was written less than a week earlier in `~/.claude/CLAUDE.md` under the heading "Bead ↔ GitHub Issue ↔ Plane three-layer mirror (MANDATORY)." It is roughly 80 lines long. It defines a rule, a tool, a data model, and a success criterion, in that order.

The rule: every tracked unit of work has three correlated records — a bead (local source of truth), a GitHub issue (code-anchored, public), and (when the project uses Plane) a Plane issue (cross-project portfolio view). Every record carries the IDs of the other two. Every state change in any layer fans out to the others.

The tool: a single bash script at `~/bin/bd-sync` (~250 LOC, dependencies `bd`, `gh`, `jq`, `curl`, `pass`). Four subcommands.

```bash
bd-sync link <bead> --gh OWNER/REPO#N [--plane PROJECT-N]   # one-shot link
bd-sync note <bead> "message"                               # mirrors note → GH comment → Plane comment
bd-sync close <bead> --reason "..." [--also-close-gh] [--also-close-plane]
bd-sync status [<bead>]                                     # show linkage / drift
```

The data model: cross-references live in the bead's notes as plain `GitHub: <owner>/<repo>#<N>` and `Plane: <project>-<N>` lines. The IDs themselves are the synchronization substrate — even if a single mirror operation is missed, the linkage is permanent. Drift is *detectable and recoverable* because every layer carries the other two IDs.

The success criterion: `bd-sync status` exits non-zero when the IDs claimed in a bead don't match the records they point at.

That is the spec. It was committed to `~/.claude/CLAUDE.md` and then nothing happened with it for several days, which is the correct behavior. Specs without an execution context are documents; specs with an execution context become migration plans the first time the right work shows up.

The right work showed up at the Braves Booth repo on April 30. A 7-layer test audit (issue #69) graded the dashboard at D (38/100) and filed 20 test-infrastructure gaps as beads. Six specialist findings from a live-streaming UX audit produced 35 fix findings labelled F-01 through F-35; eleven of them landed as PRs the same day:

- F-01 — mobile mode toggle
- F-04 — narrative cache key (fixing leakage between game days)
- F-06 — gumbo-poller liveness signal
- F-07 — per-LLM-call telemetry
- F-09 — per-call AbortController for stale-signal prevention
- F-10 — client-side heartbeat-ack watchdog
- F-11 — ID-based opponent detection with fade-in transitions
- F-12 + F-18 — dead `answerQuery` removal plus Vertex `VERTEX_ENABLED` gate
- F-14 — SSE client gauge plus 5xx error-rate counter
- F-17 — `game-lifecycle.ts` extraction giving game-over fan-out a single owner

The rest stayed open as scoped beads. The canonical first execution of bd-sync was deliberately narrow: 24 beads in two coherent clusters — 16 test-infrastructure gaps under one cluster, 8 highest-priority audit follow-ups under the other. The remaining beads from both audits stay in the backlog, partitioned across the same two clusters, awaiting later sweeps.

The pre-spec way to manage this would have been one of two losing options. Option A: file 24 GitHub issues, one per bead, drowning the issue tracker. Option B: file two GitHub issues with bullet lists in the body, losing per-bead granularity and traceability. The bd-sync spec defines option C, which is the one that actually works:

- One GitHub issue per logical cluster (`braves/#71` for the test-infra batch, `braves/#72` for the audit follow-ups).
- One Plane epic per cluster (`BRAVES-15` and `BRAVES-16`).
- Twenty-four beads, each cross-referenced into the same parent GH issue and Plane epic.

The first execution of `bd-sync link` looked like this for one bead:

```bash
bd-sync link bd-7c3f --gh jeremylongshore/braves#71 --plane BRAVES-15
# → wrote "GitHub: jeremylongshore/braves#71" + "Plane: BRAVES-15" into bd-7c3f notes
# → posted "Linked from bead bd-7c3f" comment on GH #71
# → posted "Linked from bead bd-7c3f" comment on Plane BRAVES-15
```

Repeated 24 times. After that, every `bd note` became a `bd-sync note`, every `bd close` became a `bd-sync close`. Comments on the GH issue or the Plane epic mirror back to the bead via `bd-sync note` runs. The PR auto-close convention falls out cleanly: PR descriptions include `Refs jeremylongshore/braves#71` while children remain, and `Closes jeremylongshore/braves#71` only on the PR that retires the last child bead. GitHub auto-close fires on `Closes`; the agent then runs `bd-sync close --also-close-plane` so all three layers settle into the same terminal state.

A concrete worked example: F-04, the narrative cache key fix. The bead carried the description ("cache key currently uses `gameId` only, leaks narrative across game days when MLB reuses gamePks"), the fix was implemented in PR #62, and the close ran:

```bash
bd-sync close bd-9a1c --reason "PR #62 merged: cache key now (gameDate, cohostId, gameId)" \
  --also-close-gh
# → bead closed with evidence
# → GH issue #71 stays OPEN (15 other beads still tied to it)
# → Plane BRAVES-15 stays OPEN (same reason)
# → mirrored close-comment to GH #71 + Plane BRAVES-15
```

Note the *not closed* part: GH #71 and Plane BRAVES-15 stay open because they cover 15 other beads still in flight. The close cascade only fires when the closing bead is the last child of its parent epic. That partitioning is what makes the three-layer mirror tractable at scale — cluster issues do not flap open and closed every time a constituent bead retires; they retire once when the entire cluster is done. The spec text answered the question of *when do close cascades fire* before the first cascade ever needed to be reasoned about.

What is interesting about this first execution is what *did not* happen. There was no bespoke "migrate beads to GitHub issues" script. There was no debate about granularity — the spec answered it (one GH issue per cluster, never per task bead). There was no post-hoc drift cleanup, because the IDs were planted at link-time. The cost was 24 invocations of a tool that already worked, plus reading the spec entry once at the start to remember the convention.

The granularity rule deserves a closer look because it is the part that is hardest to retrofit. The spec text says: *cluster beads by module / feature / audit batch; an epic bead maps 1:1 to a GH issue (label `epic`) and a Plane epic; a task bead inside that epic does NOT get its own GH issue.* That is one paragraph, but it answers a question that every multi-tracker workflow eventually trips on. Without it, the failure mode is predictable: a few weeks in, the GH issue tracker has 200 issues, half of them duplicate the bead they correspond to, and the human cost of skimming the issue list to find anything has gone exponential. The spec dodges the failure mode by writing the rule down before any execution exists to drift from.

The braves audit illustrated the cluster pattern at the right scale. Sixteen test-infrastructure beads — coverage gaps, missing E2E suite, no mutation testing — clustered cleanly under `braves/#71`. Eight audit follow-ups — observability gaps, performance findings — clustered under `braves/#72`. Splitting them across two issues kept each conversation thread coherent: the test-infra discussion lives in one place, the audit follow-ups in another. The Plane epics mirrored the same partitioning at `BRAVES-15` and `BRAVES-16`. A reader scanning Plane sees two epics with their own velocity numbers; a reader scanning GitHub sees two issues with their own comment threads; a reader scanning beads sees twenty-four task beads each pointing at exactly one cluster.

That is the propagation pattern when it works. The spec was the plan. The tool was already written. The execution was bookkeeping. There is one caveat in the spec text that deserves to be quoted because it is the part that does *not* automate cleanly: *if a comment originates on the GH issue or Plane issue (e.g., a human or bot replies), the agent must mirror it back via `bd-sync note <bead>` for every linked bead so the worktable stays current.* That reverse direction is currently manual. It is in the backlog as `bd-sync pull` — webhook or polling-based ingest of new GH/Plane comments back into beads. Until that ships, the discipline is human: when a reviewer comments on the GH issue, mirror it back. The IDs make that possible; the spec acknowledges that mirror is currently one-way; the backlog item names the gap. Honest specs name their gaps.

## Spec entry #2: SOPS+age secrets standard

The second propagation has more history. The spec entry was written into `~/.claude/CLAUDE.md` under "Initiative: SOPS+age secrets standard (TO-DO — propagate to all repos, then delete this section)." It still carries that "delete this section" line at the time of writing, which is the point — that line is the success criterion. When every active repo under `~/000-projects/` is compliant, the section disappears from the global CLAUDE.md. Until then it stays visible at the top of every session.

The spec defines a clean global-vs-per-project split:

| Layer | Where it lives | Already done |
|---|---|---|
| `sops` + `age` + `age-keygen` binaries | Global — `~/bin/` | yes |
| Jeremy's age private key | Global — `~/.config/sops/age/keys.txt` (mode 600) | yes |
| Jeremy's age public recipient | Global value, listed per-project in each repo's `.sops.yaml` | n/a |
| Bootstrap helper | Global — `~/bin/sops-init` (idempotent) | yes |
| `.sops.yaml` + `.env.sops` + `secrets.example.yaml` + `scripts/sops-env` | Per-project — copied in by `sops-init` | per-repo, in progress |

The bootstrap helper does the work. `sops-init` is idempotent, safe to re-run, and surgical. It writes only the four canonical files plus a fenced `.gitignore` block (only if `.env` is not already ignored — leaves hand-rolled `.gitignore` files alone). Never commits, never pushes. The engineer reviews the staged changes and commits.

The full one-command bootstrap, copied verbatim from the spec:

```bash
cd <target-repo> && sops-init           # idempotent; safe to re-run
sops-init --check                       # exit 0 if compliant, 1 if not
sops-init --recipient age1abc...        # add another engineer's recipient
```

Three subcommands cover the full lifecycle. `sops-init` (no flags) is the bootstrap. `--check` is the gate. `--recipient` is the team-onboarding move — adding another engineer's age public key to every `.sops.yaml` in the repo. There is no `sops-init --update`, on purpose: the four canonical files are not supposed to drift between repos, so updating the helper means updating every repo at once via re-running `sops-init` against each, not via patching individual files.

The reference implementation lived at `mandy-real-estate-skills` for two weeks before the propagation day. That is not accidental. Reference implementations are how you discover the unwritten parts of the spec — the awkward edges that only show up when you actually use the thing. The first run at mandy turned up two unwritten rules that got written into the spec before the propagation day: the `.gitignore` fenced block must be opt-in (some repos already have hand-tuned `.gitignore` rules that should not be touched), and the `secrets.example.yaml` template must be project-agnostic (the real values live encrypted in `.env.sops`; the example file is shape-only). Both rules now appear in the spec text, which is why the propagation day's six adoptions went without surprises.

On April 30, the helper got run against six repos in sequence. Each adoption is a single commit titled `Adopt SOPS+age secrets standard`:

1. braves
2. contributions
3. hybrid-ai-stack
4. intentvision
5. searchcarriers
6. the-county-line

Each invocation looks identical:

```bash
cd ~/000-projects/braves && sops-init
# → wrote .sops.yaml with recipient age1me3vkelljqe2u4...
# → wrote .env.sops (encrypted version of existing .env)
# → wrote secrets.example.yaml
# → wrote scripts/sops-env
# → appended fenced block to .gitignore (.env was not previously ignored)
# → reminder: review changes + remove plaintext .env after verifying decrypt round-trip

cd ~/000-projects/braves && sops-init --check
# → exit 0: compliant
```

The `--check` flag is the gate. It exits 0 if the four canonical files are present and the `.sops.yaml` recipient list is non-empty. It exits 1 otherwise. The failure mode it is designed to catch is the easy one: someone vendored the SOPS files months ago, then `git rm`'d a piece of them in a refactor, and now the repo is silently non-compliant. The check is one line of CI away from being a hard gate.

The spec text *is* the propagation plan. The spec lists the four files. The helper writes those four files. The check verifies those four files. The success criterion (delete the section when 100% comply) is testable because compliance is testable. None of this needs a meeting or a status update. It needs a list of repos and one shell loop.

What did *not* happen on propagation day for SOPS is also illustrative. There was no discussion about whether SOPS or sealed-secrets or doppler or 1Password CLI is the right tool. That decision was made when the spec was written. There was no per-repo customization — every repo got the same four files. There was no drift management because `--check` is the drift detector. The cost was six invocations of a helper that already worked, and engineer review of the resulting commits.

The remaining work is small and visible. A run of `sops-init --check` across every repo under `~/000-projects/` enumerates the holdouts. Each holdout is one `cd <repo> && sops-init` away from compliance. When the count hits zero, the section gets deleted from `~/.claude/CLAUDE.md`. The standard becomes implicit — no documentation, just the universal presence of the four files.

The anti-patterns section in the spec is worth quoting because it is the load-bearing piece for *new* repos rather than existing ones:

```markdown
### Anti-patterns — refuse on sight, regardless of migration status

- ❌ Plaintext `.env` in any commit
- ❌ Hardcoded API keys in source files "for testing" — use `tests/fixtures/`
- ❌ Decrypting SOPS files to disk for any reason (the wrapper uses `/dev/shm` tmpfs)
- ❌ Pasting secrets in chat: when it happens, encrypt to `.env.sops` immediately
  AND flag the leaked key for rotation (chat history is not erasable retroactively)
```

That last bullet is the one that gets quoted back the most often. The other three are hygiene; the secrets-in-chat clause is operational. It names a specific failure mode (the human pastes a real key into a Claude conversation), assigns a specific recovery (encrypt the leaked key into `.env.sops` so the new file is the canonical source, then rotate the leaked key out of every system that knows about it), and acknowledges a constraint (chat transcripts are not erasable retroactively, so containment is the only available move). Each propagation that flipped on April 30 inherits this clause for free, because the clause lives in the spec, and the spec is the propagation plan.

## Spec entry #3: `compatible-with` → `compatibility`

The third propagation is the one that requires the most candor. The spec discipline that powered it was real, but the *trigger* was reactive, not proactive. Three days earlier on April 28, a schema-validator debacle had torn down the IS marketplace's enterprise rubric on the wrong claim that the rubric should "realign to Anthropic's permissive spec floor." The full postmortem lives at [/posts/schema-debacle-rubric-on-spec-postmortem/](/posts/schema-debacle-rubric-on-spec-postmortem/) and the upshot is documented in a NON-NEGOTIABLES section now pinned at the top of `SCHEMA_CHANGELOG.md`.

What survived from that wrong direction was one genuinely correct rename. The [AgentSkills.io spec](https://agentskills.io/specification) — the open standard Claude Code follows — uses a free-text field called `compatibility`. The IS rubric had been using a CSV-formatted field called `compatible-with`. That divergence was a real bug, the kind that should be fixed. The validator's deprecation entry captures the rename:

```python
# scripts/validate-skills-schema.py
DEPRECATED_FIELDS = {
    'compatible-with': "Use `compatibility` (free-text per AgentSkills.io spec) "
                       "instead. Example: `compatibility: Designed for Claude Code`.",
}
```

A deprecation entry in a validator catches new violations. It does not migrate the existing 2,849 skills sitting in the marketplace catalog. That migration is what `batch-remediate.py --migrate-compatible-with` is for. The script translates the CSV-platform-list shape into the free-text shape: for input `compatible-with: claude-code, claude-desktop`, the renderer produces `compatibility: Designed for Claude Code, also compatible with Claude Desktop` — the first platform gets the `Designed for` prefix, additional platforms get folded into an `also compatible with` clause. Single-platform inputs collapse to just the prefix form.

```python
# scripts/batch-remediate.py (signature)
def migrate_compatible_with(content: str) -> Tuple[str, Optional[str]]:
    """Translate `compatible-with: claude-code, claude-desktop` (CSV) to
    `compatibility: Designed for Claude Code, also compatible with Claude Desktop`
    (free text per AgentSkills.io). Operates on raw file content; returns the
    rewritten content and a status string. Idempotent: skips files already
    using `compatibility`. See render_compatibility_value() for the renderer
    that produces the head/tail framing for multi-platform inputs."""
    ...
```

The script ran across the marketplace catalog in eight tranches on propagation day:

| PR | Scope | Skill count |
|---|---|---|
| #622 | 18 categories | 300 |
| #620 | ai-ml category | 34 |
| #623 | saas-packs 2/6 | 438 |
| #624 | saas-packs 1/6 | 422 |
| #625 | saas-packs 3/6 | 408 |
| #626 | saas-packs 4/6 | 433 |
| #627 | saas-packs 5/6 | 398 |
| #628 | saas-packs 6/6 | 416 |

Total: roughly 2,849 skills migrated in one day with no data loss, no partial states, no rollbacks needed. The migration is idempotent — running `batch-remediate.py --migrate-compatible-with` against the same tree twice produces the same result on the second run.

The CLI surface for the migration is intentionally narrow:

```bash
python3 scripts/batch-remediate.py --migrate-compatible-with --root packs/saas-1
# → scans packs/saas-1 recursively for SKILL.md files
# → for each: parses YAML frontmatter, applies migrate_compatible_with()
# → writes back only the files that changed
# → emits a summary: "Migrated 422 skills, 0 errors, 0 skipped"
```

A separate `--dry-run` flag prints the diff without writing anything, useful for CI gates. After the eight tranches landed, a single `--check` run across the entire marketplace catalog confirmed no `compatible-with` strings remained outside of test fixtures and migration documentation. That confirmation is the validator's job, not the migration tool's job — the validator at marketplace tier still rejects `compatible-with` as a deprecated field name, so any new submission carrying the old name will fail the marketplace gate before the migration tool ever needs to run again.

What earned the propagation tractability was the spec discipline that survived the debacle. The validator had a clear deprecation entry. The migration tool's signature was unambiguous. The CLAUDE.md "Claude Skills SOP" section pointed every future session at the canonical sources by path. The propagation step itself was a script run because the spec text — including the deprecation entry, the rationale, the migration helper invocation — had been committed three days earlier.

The dishonest version of this story would frame the migration as pure foresight: *we wrote the spec, the propagation followed, look how clean the system is.* The honest version is that the propagation tool existed because the spec text had been correctly written, and the propagation *trigger* was a self-inflicted wound — a reframe attempt that should never have happened. The discipline that survived contact with the wound is what made the recovery clean, not the absence of the wound.

The same propagation day shipped six other adjacent improvements in `claude-code-plugins` that ride on the same spec discipline:

- audit-harness installed at the marketplace repo with `tests/TESTING.md` and coverage thresholds (PR #621), bringing enforcement into the repo it audits.
- a11y for the marketplace site plus RTM/PERSONAS/JOURNEYS traceability and a CLI performance budget (PR #631).
- husky + lint-staged + commitlint + root ESLint/Prettier (PR #629), so quality gates run before every commit instead of in CI alone.
- Four ADRs declining specific audit-tests roadmap recommendations (PR #619), making the *no* decisions traceable in their own right.
- x-bug-triage: five SKILL.md files brought to marketplace compliance (PR #633).
- Catalog: orphaned `jeremy-google-adk` and `jeremy-vertex-ai` plugins exposed in the marketplace navigation (PR #634).

Plus five small PRs (#635–#639) stabilizing the `sync-external` workflow that produces auto-PRs into downstream repos: pnpm version conflict, `--no-frozen-lockfile`, install workspace deps, handle empty/submodule/partial failures, disable husky pre-commit in auto-PR. Each one is a small fix; together they harden the propagation tooling itself, which is how propagation patterns mature. The migration script that ran across 2,849 skills on April 30 was usable because the surrounding tooling had been hardening in the background for weeks.

## Counterweight

Three patterns that all worked in one day is exactly the shape of a story that should be eyed with suspicion. Three things deserve naming as direct counterweight.

**The Braves Booth dashboard scored a D (38/100) on its own 7-layer test audit on the same day.** Twenty gaps filed. The audit ran against the very methodology that the bd-sync mirror was about to demonstrate beautifully. The methodology eats its own dogfood and the food is sometimes bitter — there is no version of this where the propagation patterns are mature and the codebases they govern are also mature. They are independent variables. The bd-sync mirror worked perfectly to file the 24 beads documenting how badly the dashboard tested. That is success and indictment in the same artifact.

**The marketplace migration was reactive.** Three days earlier, a validator reframe had torn down the enterprise rubric on a wrong reading of the underlying spec. The `compatible-with` → `compatibility` rename was the one piece worth keeping out of an otherwise-discarded plan. The propagation tool existed because the spec text was clear. The propagation trigger was a self-inflicted wound. Anyone framing this as a triumph of foresight is reading the story upside down.

**Volume is not virtue.** 3,000+ files changed across 9+ repos in one day is the same shape as a system about to break under its own weight if the discipline behind it is not consistent. Three patterns worked because three specs had been written down. The fourth pattern that *should* have shipped on the same day — a `validate-consistency` policy across all client repos — did not, because the spec for it had not been written down clearly enough. The day is a snapshot of where the discipline holds and where it is still owed.

What is owed back, in order:

1. The Braves Booth has 20 test-infra gaps and 35 UX audit findings (F-01 through F-35) to retire over time. Eleven shipped on April 30; 24 are linked through the bd-sync mirror's first execution; the rest stay scoped under the same two clusters and will land in later sweeps. Each is its own bead. The bd-sync mirror is in place; the work is the work.
2. The SOPS+age propagation has roughly half the repos in `~/000-projects/` still on plaintext `.env`. The helper is idempotent. The remaining work is mechanical — one `cd <repo> && sops-init` per holdout, then engineer review.
3. The `validate-consistency` audit needs a written-down propagation spec before the next batch. Until then, the audits will land case-by-case rather than as a single propagation day.

Volume in the absence of these follow-throughs would be theatre. Volume *with* the follow-throughs is the shape of the system maturing.

There is a second-order counterweight worth naming. The `contributions` repo went through a major architectural pivot on the same day — the cloud-only bounty system was archived and replaced with a local-first, skill-only architecture. Ten phases of the rebrand from `bounty-system` to `contribute-system` landed across types, dashboard routes, orchestrator, docs, tracker, README, CLAUDE.md, INDEX, cloud + Firestore + GCS rebrand stage, log strings, and final cleanup. That work was structural enough that it could have eaten the entire day on its own. It did not, because the SOPS+age propagation was a single `sops-init` invocation against a repo that was already mid-pivot, and the bd-sync mirror does not care what the repo's architecture looks like internally. The propagation patterns are *orthogonal* to the projects they apply to. That orthogonality is a property of the spec discipline, not a coincidence — every one of the three specs was written specifically to be project-agnostic, so that propagation day work could happen across nine repos without nine project-specific conversations.

A third counterweight, smaller but worth flagging. Two new client-facing real-estate sites shipped placeholder pages on April 30 — `mandy-real-estate-skills` v0.0.3 and a brand-new `comehomealabama` (Astro 5 + Tailwind v4 + brand-token system, CNAME, dual licensure, IDX subdomain). Both sites adopted SOPS+age via the same `sops-init` invocation as every other repo. Both inherit bd-sync the moment their first beads get cross-linked. New repos are the easiest case for propagation patterns because they have no legacy to migrate from; the discipline is to onboard them on day one rather than retrofitting later.

## Also shipped

A handful of smaller propagation-adjacent items rounded out the day. `github-profile` got a one-line rename from "Bounties" to "Contributions" to match the architectural pivot in the `contributions` repo — the kind of naming consistency that is invisible until it isn't. `nixtla` dropped Python 3.9 support and reformatted `scaffold_plugin.py`, narrowing the support matrix in advance of the F1 SDK migration baseline that landed earlier in the week. `x-bug-triage-plugin` aligned its frontmatter with the agentskills.io spec and restructured several body sections, riding the same `compatible-with` → `compatibility` migration that the marketplace catalog had run minutes earlier.

The `mandy-real-estate-skills` repo cut three releases in 24 hours — v0.0.1, v0.0.2, v0.0.3 — as the release engineering for that placeholder site got tightened. The `comehomealabama` site shipped its first commit. An architecture diagram routing fix at mandy ensured the orange Twilio→Slack path no longer crossed the SendGrid path. None of these items are propagation patterns in their own right, but each rides on the same spec discipline: every one of those repos inherited SOPS+age via the same helper, and every one will inherit bd-sync the moment it has beads worth tracking.

## Closing — write the spec before the propagation

The transferable mental model is shorter than the post that surrounds it.

> Write the spec before the propagation. Make the spec text load-bearing. The validator becomes the gate. The "delete this section when done" line becomes the success criterion. Without this, multi-repo propagation is hand-rolled toil; with this, it is a script run.

Each clause in that paragraph maps to one of the three propagations.

*The validator becomes the gate.* The marketplace migration shipped 2,849 skills in one day because `validate-skills-schema.py` already had a deprecation entry for `compatible-with`. The validator was the gate. The migration tool was the propagation. The validator did not become the gate on April 30; it had been the gate for weeks, which is why the gate was usable on propagation day.

*The spec text becomes the migration plan.* SOPS+age propagated to six repos in one day because the spec text in `~/.claude/CLAUDE.md` named the four canonical files, the bootstrap helper, and the success criterion. There was nothing to invent on propagation day. There was a list of repos and a helper that already worked.

*The "delete this section when done" line becomes the success criterion.* This is the part that takes discipline because it requires writing the closing condition into the opening text. Most documentation does not do this — it accretes, it never deletes itself. A propagation spec that does not name its own deletion condition is a spec that will be in the document forever, drifting from reality, becoming a monument to itself. The SOPS section says *delete this whole section when 100% comply.* That is the only sentence in the section that matters more than the others, because it is the one that closes the loop.

The bd-sync mirror is the youngest of the three patterns and the one with the cleanest spec. Its first execution against 24 beads at the Braves Booth on April 30 was bookkeeping, not invention, because the spec text had answered the granularity question (one GH issue per cluster), the linkage question (IDs in bead notes), and the drift question (`bd-sync status` exits non-zero on mismatch) before a single execution had ever happened. The first run was not a pilot; it was a confirmation.

There is a fourth, quieter clause worth naming. *Do not skip the reference implementation.* SOPS+age sat at `mandy-real-estate-skills` for two weeks before the propagation. That was not delay. That was the reference implementation discovering the unwritten parts of the spec — the awkward edges that only show up under real use. By the time `sops-init` ran against the second repo, those edges were already documented and handled. By the time it ran against the sixth repo, the helper was boring. Boring is the goal state for a propagation tool.

A day that looked like chaos on a graph was actually three CLAUDE.md spec entries reaching critical mass simultaneously. The graph is not the story. The spec discipline is the story. Volume came for free once the specs were written down.

One last reflection on what the *next* propagation day will require. The patterns that worked on April 30 were the ones whose specs had been pressure-tested by reference implementations weeks or months in advance. The bd-sync mirror lived in `~/.claude/CLAUDE.md` for several days before its first 24-bead execution. SOPS+age lived at `mandy-real-estate-skills` for two weeks before propagating to six repos. The marketplace migration tool had been in `batch-remediate.py` long enough to have its own deprecation entry in the validator. None of these were written-and-shipped in the same day. Each one had a maturation period during which the spec text got refined against real use, and the helper got hardened against real edge cases, and the success criterion got named explicitly enough to be testable.

The patterns that did *not* propagate on April 30 are the ones whose specs are not yet pressure-tested. The `validate-consistency` audit policy is one. The unified `release` engineering standard across all client repos is another. Both have draft text in various places. Neither has been written down once, in one place, with the load-bearing structure of a propagation spec — global vs per-project split, idempotent helper, success criterion, anti-patterns. Until that text exists, those patterns will land case-by-case rather than as a single propagation day.

The mental model is the post. The volume on the graph was a side effect of the model. The next propagation day is whatever the next spec entry is, plus the helper that already works, plus a list of repos. That is the entire pipeline. When it works, it looks like chaos. When it does not work, it looks like a meeting calendar.

There is one final operational note worth preserving. Each of the three propagations on April 30 was effectively a single-engineer operation against many repos. There was no team coordination meeting, no shared spreadsheet of progress, no Slack channel for the migration. The spec text replaced all of those artifacts. A propagation that needs coordination overhead is a propagation whose spec was not written down clearly enough — every minute spent in a coordination meeting is a minute spent not editing the spec. The transferable rule that comes out of that observation is short: when a propagation feels like it needs a meeting, edit the spec instead.

The CLAUDE.md spec was the meeting agenda for a meeting that never had to happen. Three propagations, nine repos, one day, no coordination overhead. The graph in the screenshot is the receipt for picking the durable artifact over the urgent one, several weeks earlier, when nobody was watching.

A propagation pattern is not a graph of files changed. It is a sentence in a spec. When the sentence is load-bearing — when it names the helper, the success criterion, and the deletion condition — the graph follows for free.

When the sentence is decorative, the graph never materializes regardless of how many meetings get scheduled to push it along. The discipline of writing the load-bearing sentence first is the entire discipline. Everything else is propagation.

The next entry in `~/.claude/CLAUDE.md` that needs this treatment is already lined up. Whether it ships on a single propagation day or trickles in case-by-case is mostly a function of how clearly the sentence gets written down before the helper exists, not after.

## Related Posts

- [The Rubric Sits On Top Of The Spec: A Schema Validator Postmortem](/posts/schema-debacle-rubric-on-spec-postmortem/) — what happens when the spec layering breaks down, three days before this post's marketplace migration shipped.
- [Forty-Four Minutes Before First Pitch: An LLM Fallback Chain and a Live Probability Gauge in One Session](/posts/broadcast-day-llm-fallback-jchads-challenge/) — the same braves-booth dashboard, two days earlier, in incident-response mode.
- [audit-harness v0.10: Enforcement Travels With the Code](/posts/audit-harness-v010-enforcement-travels-with-code/) — the prior expression of the same mental model, applied to test enforcement infrastructure.
