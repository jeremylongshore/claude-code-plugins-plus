# Session handoff (two-session execution)

The portable contract for **two-session** runs: one session plans (Brain routing + amplify + spec + scope), a
**second session in a different environment** builds (dispatch), and the user returns to the first session to review
(`/hyperflow:audit`). Because `.hyperflow/` is gitignored / machine-local, the build artefact cannot travel to the
other environment on its own — so the planning session writes a **git-committed handoff package** that the build
session pulls.

Set by the Step 0 session gate: `session=one` runs the whole chain in place (today's behavior); `session=two` stops
scope at the dispatch boundary and writes this package. The follow-up `handoff=review|deploy` decides whether the
build session returns for review (default) or continues to deploy on its own.

## Package layout

Committed at the **repo root** as a sibling of the gitignored `.hyperflow/` (so it travels via git). Directory name
is configurable via `handoff.packageDir` (default `.hyperflow-handoff`).

```
.hyperflow-handoff/
└── <slug>/
    ├── HANDOFF.md          # manifest written by the planning session
    ├── STATUS              # one word: planned | built | reviewed
    ├── artefact/           # COMMITTED COPY of the gitignored original
    │   ├── tasks/<slug>.md          # flat single-phase task file
    │   └── features/<slug>/…        # OR the whole multi-phase feature tree
    ├── context/            # standalone snapshot so the build env needs no scaffold
    │   ├── conventions.md
    │   ├── profile.md
    │   ├── architecture.md
    │   └── memory-index.md          # optional (.hyperflow/memory/index.md)
    └── COMPLETION.md       # written BACK by the build session (absent until built)
```

- `artefact/` mirrors the exact `.hyperflow/tasks|features/` shape — dispatch rehydrates by copying it back.
- `context/` lets the second environment build without re-running `/hyperflow:scaffold`.
- `STATUS` is a single grep-cheap token the session-start hook reads without parsing markdown.

## STATUS state machine

```
scope Step 7 (session=two)   → write + commit + push package         STATUS=planned
build session: dispatch <slug> → rehydrate artefact/ → run batches    (planned until done)
dispatch Step 5 (all PASS)   → write COMPLETION.md, commit + push     STATUS=built
   ├─ on_complete=deploy → build session runs /hyperflow:deploy (terminal; STATUS stays built)
   └─ on_complete=review → planning session returns
planning session: /hyperflow:handoff review <slug>
   → /hyperflow:audit <base>..<head> → deploy gate                    STATUS=reviewed
```

**Side-awareness comes from STATUS alone:** `planned` ⇒ build here; `built` ⇒ review here; `reviewed` ⇒ archivable.

**Edge transitions:**
- `planned` + build crash → STATUS stays `planned`, no `COMPLETION.md`; re-pickup resumes via `dispatch --from-batch`.
- `built` partial → `COMPLETION.md` `Result: partial (<done>/<total>)`; audit still runs over the existing range.
- `reviewed` → `/hyperflow:handoff complete <slug>` archives to `.hyperflow-handoff/.archive/<slug>/`. No auto-archival.

## `HANDOFF.md` template

```markdown
# Handoff — <slug>

## Manifest

| Field                | Value                                                       |
|----------------------|-------------------------------------------------------------|
| Slug                 | `<slug>`                                                    |
| Artefact type        | flat \| feature                                             |
| Artefact path        | `artefact/tasks/<slug>.md` \| `artefact/features/<slug>/`   |
| Chain args           | `commit=… branch=… push=… triage=<base64> mode=…`           |
| on_complete          | review \| deploy                                            |
| Originating provider | claude-code \| codex \| opencode \| antigravity            |
| Originating commit   | `<sha>` (HEAD when the package was committed)               |
| Specialists          | `<Brain-decided roster from the artefact status block>`    |
| Created              | `<YYYY-MM-DD HH:mm>`                                        |

## TL;DR
<2–3 sentences: what this build does + the single most important design decision.>

## Target instruction (build session)
Run `/hyperflow:dispatch <slug>` (or `/hyperflow:handoff pickup <slug>`). Dispatch rehydrates `artefact/` into
`.hyperflow/`, runs `/hyperflow:scaffold` if the cache is absent, builds the batches, then:
- on_complete=review  → stop after build; write COMPLETION.md; commit + push; print "return to session 1 and run /hyperflow:audit".
- on_complete=deploy  → continue to /hyperflow:deploy after the build.

## How to start the build session
1. In the other environment / machine, `git pull` this branch (checkout `feat/<slug>` if `branch=new`).
2. Run `/hyperflow:dispatch <slug>` — it auto-detects this handoff package.

## Return path (planning session)
When STATUS flips to `built`, the session-start hook surfaces it. Run `/hyperflow:handoff review <slug>`
(→ `/hyperflow:audit <base>..<head>`), then the deploy gate.
```

## `COMPLETION.md` template (written back by the build session)

```markdown
# Completion — <slug>

| Field        | Value                                  |
|--------------|----------------------------------------|
| Built by     | claude-code \| codex \| opencode \| …  |
| Built at     | `<YYYY-MM-DD HH:mm>`                    |
| Base commit  | `<sha>` (the originating commit)       |
| Head commit  | `<sha>` (after the last build commit)  |
| Diff range   | `<base>..<head>`                       |
| Commits      | <n> per-sub-task commits               |
| Branch       | `<branch>`                             |
| Result       | built \| partial (<done>/<total>)      |

## Notes
<one-line build summary or partial-stop reason>
```

## Rehydration (build session)

On a handoff pickup, before dispatch Step 1:
1. Read `HANDOFF.md` → artefact type, chain args, `on_complete`.
2. If `.hyperflow/` cache is absent → run `/hyperflow:scaffold` (so workers get Layer-0 context). If scaffold cannot
   run, fall back to the package's `context/` copies.
3. Copy `artefact/tasks/<slug>.md` → `.hyperflow/tasks/<slug>.md` (flat), or `artefact/features/<slug>/` →
   `.hyperflow/features/<slug>/` (feature), if not already present.
4. Leave `STATUS=planned` until the build completes.

## Provider notes

The build session may run under any provider (Codex, Antigravity, OpenCode). The chain args (triage, flow
profile, commit/branch/push, Brain specialist roster) travel inside `HANDOFF.md`, so the build runs structurally —
no Q1/Q2 gate fires on the build side. All agents inherit the session model of the build environment.
`HANDOFF.md` records the originating provider for traceability.

## Transport & config

- `handoff.autoPush` (default `true`) — push the package commit after writing it (and the completion commit). On
  failure the orchestrator surfaces the exact `git push -u origin <branch>`; the commit always lands locally.
- `handoff.remote` (default `origin`) — the remote to push/pull.
- `handoff.packageDir` (default `.hyperflow-handoff`) — the committed package directory.
- Never `--no-verify`; never force-push `main`/`master`.

The package directory is the **one committed exception** to the file-first banned-locations rule — it is a transport
artefact, not a plan document, and git is the required cross-environment channel.
