---
title: "An Anti-Slop Framework Found Three Bugs Inside Itself on Day One"
description: "A 41-gate anti-slop framework shipped v0.1.0, then found three silent failure modes inside its own gates within hours of release."
date: "2026-05-03"
tags: ["oss-contribution", "bash", "gh-cli", "yaml", "silent-failures", "release-engineering", "claude-code-skills"]
featured: false
---
A framework whose entire purpose is to catch silent failures in AI-generated OSS contributions is the worst possible place to host silent failures. That tension is the spine of this case study. The framework in question is `contributing-clanker`, an installable Claude Code skill that walks an OSS contribution lifecycle through 41 deterministic gates spanning seven phases and 62 enumerated AI-slop failure modes. It shipped at v0.1.0 around 20:20 local time. By the end of the same day it was at v0.1.2 — because the first real qualifying flow against a third-party upstream (`secureblue/secureblue#2138`) surfaced **three categorically named bash/CLI silent-failure modes** inside the framework itself, plus a minor scoping bug already patched in v0.1.1.

The three bash failure modes are the focus of this article. They are independently useful to anyone who writes shell, ships CLIs, or maintains release tooling. The thesis is not "we shipped buggy software." The thesis is that a gate framework's correctness has to be exercised against real upstreams, not synthetic fixtures, and that the act of doing so on day one is itself the framework working — at meta-level.

## What the framework is supposed to do

`contributing-clanker` is a `/contribute` skill in the Claude Code marketplace. It is a workflow that takes an operator from "I want to find OSS work to contribute to" to "the PR merged" without producing the kind of low-signal AI noise that maintainers have started rejecting on sight. The state machine for any candidate contribution is:

```
open → shortlist → claimed → working → submitted → merged
```

Between those states sit 41 deterministic gates organized into phases A through G. Each gate addresses one of 62 enumerated AI-slop failure modes — things like "PR body restates the diff instead of explaining the why," "claim comment uses a `@-mention` of an unrelated maintainer," "tests added but never executed," "unrelated formatting churn in the diff." The gates are bash scripts that exit 0 (PASS), 1 (BLOCK), or 2 (WARN), and the framework refuses to advance the state machine past any phase with an open BLOCK.

Per-repo dossiers live at `~/.contribute-system/research/<owner>__<repo>.md`. They are built by an `@researcher` subagent that probes for CLA presence, AI policy, branch convention, draft-first norms, the active review-bot list, issue templates, project pet peeves, and a failure log of past rejected contributions. The dossier becomes the input to a draft-writer subagent that knows, before generating any prose, what the repo's house style is.

Five subagents do the heavy lifting: `scout`, `researcher`, `draft-writer`, `test-runner`, and `repo-analyzer`. The framework is distributed both as a vendored skill at `skills/contribute/` and as a marketplace plugin at `claude-code-plugins-plus-skills/plugins/community/contributing-clanker/`. Per the [Intent Solutions Testing SOP](/blog/audit-harness-v010-enforcement-travels-with-code/), [`@intentsolutions/audit-harness@v0.1.0`](https://www.npmjs.com/package/@intentsolutions/audit-harness) is vendored at `.audit-harness/` for hash-pinning, escape-scanning, CRAP analysis, and architecture lint. An end-to-end install test covers 26 sha256-verified assertions on install, user-data preservation, and uninstall.

That is the artifact whose first real flow found three bugs inside itself.

## The path to v0.1.0

The day's release sequence is worth recording, because each step is a precondition for the bugs that surface later.

- **15:42** — Repo renamed from the previous bounty-platform-adjacent name to `jeremylongshore/contributing-clanker`. All Algora, Gumroad, and Cortex framing removed. The skill is no longer about getting paid; it is about not producing slop.
- **15:57–16:23** — Governance fill via `/repo-dress`. A 10-document enterprise documentation set seeded, tied to a 10-epic beads structure so each governance area has a tracked work item.
- **16:39–17:00** — Test infrastructure installed at L1+L2+L3: `shellcheck`, `pre-commit`, `bats`, and the harness `features` lint. `TEST_AUDIT.md` and `tests/TESTING.md` skeleton committed. The 26-assertion install integration test (`tests/integration/test-plugin-install.sh`) is the first artifact that exercises the install/uninstall hooks end-to-end.
- **17:21** — Bats coverage expanded to 41 cases plus 3 regression suites, one per category of historical failure.
- **18:07** — Closed 9 epics plus the Slice 2 umbrella. Full slate.
- **18:24** — Subagents bundled inside the skill itself per the canonical skill-creator location convention. Moved from `~/.claude/agents/` (operator-side) into `skills/contribute/agents/` (packageable). This matters because the install flow can now ship subagents alongside the skill rather than relying on the operator to have them in their global config.
- **19:45** — Vendored skill into `skills/contribute/`: the workflow, scripts, references, agents, and assets. The marketplace package is now self-contained.
- **20:20 — v0.1.0 ships.** Plugin distribution via `bin/release-plugin.sh` (semver-validated, idempotent rsync). Install/uninstall hooks at `release/hooks/install.sh` and `release/hooks/uninstall.sh` preserve user data: the `candidates/`, `research/`, `log.jsonl`, and `profile.md` files survive across upgrades.

The framework now exists. It has tests. It has hooks. Its CI is green. Its 26-assertion E2E install test passes. There is nothing left to do except point it at a real upstream and run it.

## The first qualifying flow

The first repo selected for a real `/contribute` run is `secureblue/secureblue`, a security-hardened immutable Linux distribution with active issue traffic. Issue `#2138` is the candidate. The flow proceeds as designed: scout selects, researcher builds the dossier, draft-writer drafts the claim comment.

Within the first hour of that flow, three things go wrong. None of them are visible from the gate exit codes alone. All three are silent failures — the kind of bug that produces wrong output without producing an error.

That phrase, "wrong output without an error," is the thread that connects all three. It is also the central category that the framework was designed to detect. Finding three of them inside the framework on day one is either embarrassing or instructive depending on how you frame it.

## v0.1.1 — Step 0 PR scoping

Before the three bash bugs, a smaller bug surfaced first and shipped as v0.1.1. It is included for completeness because it is a useful scoping pattern to remember.

**Symptom.** Step 0 of the `/contribute` flow asks "what's already in flight?" and lists the operator's open PRs. In the first run, the list contained the operator's *own-repo* PRs — work in `jeremylongshore/claude-code-plugins`, `intent-solutions-io/nixtla`, `jeremylongshore/braves-booth` — alongside the upstream contribution PRs. From the framework's perspective those should be invisible. They are not contributions. They are house work.

**Root cause.** The original SKILL.md instructed `gh pr list --json repository` followed by post-filter on repository URL. That syntax is deprecated in recent `gh` versions and the URL-prefix filter did not cleanly exclude the operator's own organizations.

**Fix.** Switch to `gh search prs --author=@me --state=open` and exclude by `OWN_ORGS` prefix:

```bash
OWN_ORGS=("jeremylongshore/" "intent-solutions-io/")
gh search prs --author=@me --state=open --json repository,number,title,url \
  | jq -r --argjson own "$(printf '%s\n' "${OWN_ORGS[@]}" | jq -R . | jq -s .)" '
      .[] | select(.repository.nameWithOwner as $r |
        ($own | map(. as $p | $r | startswith($p)) | any) | not)'
```

The fix also added an explicit "Scope rule (non-negotiable)" paragraph to SKILL.md so future edits would not silently drift the scoping logic back. v0.1.1 shipped at 20:42, twenty-two minutes after v0.1.0.

That is the small bug. The interesting bugs are next.

## Three bash silent-failure modes inside a framework that exists to catch them

The remaining three bugs all shipped as v0.1.2 once the secureblue flow had progressed far enough to exercise the dossier builder, the state-transition machinery, and the gate runner against real input. Each one corresponds to a named, generalizable bash failure mode worth carrying into your own mental model.

### Mode 1 — `gh api` stdout/stderr conflation on 404

This is the bug that fabricated dossier data, which is the worst possible bug for a research-backed framework to have.

**Symptom.** The `researcher-build.sh` script was producing `policy_files` inventories that claimed every probed file existed in every repo. LICENSE present. CODE_OF_CONDUCT present. CONTRIBUTING present. SECURITY present. `.github/CODEOWNERS` present. Every probe registered as a hit, even on repos that obviously did not have the file. The dossiers looked exhaustive and were silently lying.

The implication is severe. The dossier is the input to draft-writer. If the dossier claims a CONTRIBUTING file exists, the draft-writer will reference its conventions in the claim comment. If the file does not exist, the draft references conventions that do not exist. The framework's research layer is fabricating, and the prose layer is consuming the fabrication as ground truth.

**Root cause.** The probe was implemented as:

```bash
result=$(gh api "repos/$OWNER/$REPO/contents/$path")
if [ -n "$result" ]; then
  echo "exists"
fi
```

The intent is plain: if the GitHub API returns content, the file exists. The bug is that `gh api`, when it gets an HTTP 404, does not return an empty string. It prints the GitHub API's error JSON to **stdout**, not stderr. Something like:

```json
{"message":"Not Found","documentation_url":"https://docs.github.com/rest/..."}
```

That JSON is non-empty. `result` captures it. `[ -n "$result" ]` evaluates true. Every probe wins. Every file is reported present.

This is a category of bash bug that bites anyone who treats CLI tools as if they obey strict POSIX stream conventions. They often do not. `gh` in particular has [historically printed error payloads to stdout under various conditions](https://github.com/cli/cli/issues/5209), and the only safe contract is the exit code.

**Why does `gh api` print errors to stdout instead of stderr?** Because the GitHub CLI streams the API response body verbatim, regardless of HTTP status — a 404 returns an error-shaped JSON body, and that body is the response. The cleanest defense is to gate on exit codes (0 success, non-zero failure) and discard both streams entirely.

**Fix.** Switch to exit-code-based probing and discard both streams:

```bash
if gh api "repos/$OWNER/$REPO/contents/$path" >/dev/null 2>&1; then
  echo "exists"
fi
```

Now the conditional is gated on `gh api`'s exit code (0 on success, non-zero on 404 or any other error). Both streams are discarded so the script does not accidentally consume or emit the error JSON.

A second improvement landed in the same patch: the script now also probes `docs/` subpaths. Some projects, including secureblue itself, house policy documents in `docs/CODE_OF_CONDUCT.md` rather than at the repo root. The original script would have correctly reported "no CODE_OF_CONDUCT" at the root and missed the actual file in `docs/`. The probe-set now includes both common locations.

**Caveat that propagated.** Twelve dossiers were built before this patch landed. Their `policy_files` entries are fabricated. The intuitive remedy is "run `@researcher refresh <repo>` on each one and re-probe honestly." That works in principle, but the existing `researcher-build.sh` overwrote engineer-curated body sections on refresh — the dossier body had been hand-augmented after the initial machine pass, and a naive refresh would clobber that work. So a separate "smart refresh" follow-up shipped at 23:11 the same day, splitting the dossier into machine-owned sections (top of file, refreshable) and engineer-owned sections (bottom of file, preserved across refresh).

That follow-up is its own small example of a useful pattern: when an automated probe and a hand-edit share a file, you need an explicit ownership boundary or one will silently destroy the other.

### Mode 2 — `awk -v RS='---'` plus `sed -i` against YAML frontmatter

This is the bug that turned legitimate state transitions into corrupted candidate files.

**Symptom.** When the operator runs `transition.sh` to move a candidate forward through the state machine — typically with one or more `--override-gate <gate-id>:<reason>` flags to record a deliberate override — the script was supposed to append override entries to the YAML frontmatter's `overrides:` array. Instead:

- The opening `---` delimiter became `------` after the first transition.
- Override entries were landing as sibling top-level YAML keys rather than as items inside the `overrides:` array.
- Multi-line reasons broke indentation in unpredictable ways.

The candidate file is the source of truth for the state machine. Corrupting its frontmatter means the next gate run cannot parse the file. Cascade failure.

**Root cause.** The original implementation tried to use bash native tools to surgically modify YAML:

```bash
awk -v RS='---' 'NR==2' "$CANDIDATE"   # extract frontmatter
sed -i "/^overrides:/a\\  - gate: ${GATE}\\n    reason: ${REASON}" "$CANDIDATE"
```

Two compounding problems.

First, `awk -v RS='---'` sets the record separator to the three-dash delimiter. On gawk this is [treated as a regex and produces multi-character record splitting](https://www.gnu.org/software/gawk/manual/html_node/awk-split-records.html); on strict POSIX awk and on mawk, only the *first* character of `RS` is honored, so `RS='---'` silently degrades to `RS='-'` and produces entirely different splits. The calling script here was running on gawk and was reassembling the file by concatenating `---` + frontmatter-record + `---` + body-record. That is correct only if the frontmatter record is stripped of any leading or trailing `---` fragment. It was not. The result was `------` at the top of the file after the first transition. The portability hazard is independently bad: a script that works on a developer machine with gawk and silently corrupts files on a CI runner with mawk is exactly the failure mode you do not want at the bottom of your gate framework.

**Is `awk -v RS='---'` portable across awk implementations?** No. Multi-character `RS` is a gawk extension; POSIX awk and mawk honor only the first character. The same script can split records differently on different systems. For structured data, never rely on multi-char `RS` — shell out to a real parser instead.

Second, `sed -i` insertion ignores YAML structure. The `/^overrides:/a\\` instruction appends after a line matching `overrides:` at column 0. If the YAML has `overrides:` indented under another key, the insertion lands at the wrong indent depth. If the override block has a multi-line `reason:` field with embedded newlines (escaped via `\n` in the sed expression), sed's line-oriented model breaks the structure. The fix space here is not "be more careful with sed." The fix space is "stop using line-oriented tools on structured data."

**Fix.** Round-trip through [Python's `yaml.safe_dump`](https://pyyaml.org/wiki/PyYAMLDocumentation). The transition script now writes overrides to a NUL-separated pairs file, then invokes Python to parse, mutate, and re-serialize the frontmatter:

```bash
# write pairs (gate, reason) NUL-separated so reasons can contain : or "
PAIRS_FILE=$(mktemp)
for override in "${OVERRIDES[@]}"; do
  gate="${override%%:*}"
  reason="${override#*:}"
  printf '%s\0%s\0' "$gate" "$reason" >> "$PAIRS_FILE"
done

python3 -c '
import sys, yaml
with open(sys.argv[1]) as f:
    fm, _, body = f.read().partition("---\n")[2].partition("\n---\n")
data = yaml.safe_load(fm) or {}
data.setdefault("overrides", [])
with open(sys.argv[2], "rb") as p:
    pairs = p.read().split(b"\0")
for i in range(0, len(pairs)-1, 2):
    data["overrides"].append({"gate": pairs[i].decode(), "reason": pairs[i+1].decode()})
print("---")
yaml.safe_dump(data, sys.stdout, default_flow_style=False, sort_keys=False)
print("---")
print(body, end="")
' "$CANDIDATE" "$PAIRS_FILE" > "$CANDIDATE.new"

mv "$CANDIDATE.new" "$CANDIDATE"
rm -f "$PAIRS_FILE"
```

The NUL separator matters. Override reasons routinely contain colons (`fixture-only:test-data`), quoted strings (`"see issue #1234"`), and occasionally newlines. NUL is the only byte that cannot legally appear in a YAML scalar, so it is safe as a delimiter for arbitrary text. Splitting on `\0` round-trips every reason without quoting drama.

The lesson generalizes beyond YAML. Any time a bash script needs to surgically modify structured data — JSON, YAML, TOML, XML — the right move is to shell out to a parser, mutate the parsed data structure, and serialize back. `sed -i` and `awk` field-record manipulation are pattern-matching tools, not structural editors. Treating them as structural editors is a category error that produces silent corruption rather than loud failure.

### Mode 3 — `set -uo pipefail` plus empty `grep` fail-closed BLOCK

This is the most generalizable of the three. It bites every shell engineer at least once. It is the bug that turned a passing draft into a BLOCKed gate.

**Symptom.** Gate `a09-mention-routing.sh` returns BLOCK on every claim comment or PR draft that does not already contain an `@-mention`. The gate is supposed to validate that any `@-mentions` that do appear are not in an exclusion list (irrelevant maintainers, drive-by mentions, accidental email-style addresses). On a draft with zero `@-mentions`, the correct outcome is PASS. The gate was returning BLOCK.

**Root cause.** The repo enforces [`set -uo pipefail`](https://www.gnu.org/software/bash/manual/bash.html#The-Set-Builtin) everywhere. That is the right default for production bash — it prevents unset-variable bugs and prevents pipeline failures from being silently swallowed. But it interacts badly with `grep` returning non-zero on no-match.

```bash
#!/usr/bin/env bash
set -uo pipefail

EXCLUDE_REGEX='^@(github-actions|dependabot|renovate)$'
mentions=$(grep -oE '@[a-zA-Z0-9_-]+' "$DRAFT" | grep -viE "$EXCLUDE_REGEX" | wc -l)
```

The intent reads cleanly: extract all `@mention` tokens, drop the ones in the exclusion list, count what remains. The bug is that when `$DRAFT` contains no `@-mentions` at all, the first `grep -oE` matches nothing and exits with code 1. Under `pipefail`, a non-zero exit anywhere in a pipeline propagates to `$?` of the whole pipeline. The command-substitution assignment to `mentions` therefore returns non-zero. The gate's caller then inspects the script's overall exit status and treats any non-zero as fail-closed — BLOCK. There is no need to invoke `set -e` to explain it: `pipefail` makes the pipeline's exit non-zero, the script returns non-zero, and the gate runner reads that as failure.

The crucial point: this is not a bug in `grep`. It is doing exactly what [POSIX says it should](https://pubs.opengroup.org/onlinepubs/9699919799/utilities/grep.html): exit 1 on no-match, exit 2 on error. It is not a bug in `pipefail`. It is also doing exactly what it should: surfacing failures rather than swallowing them. The bug is in the engineer's mental model, which assumed "grep produces empty output on no-match" without inspecting the exit code. The combination of `pipefail` and `grep` is precisely how silent-failure-by-omission turns into noisy failure-by-presence, and the gate writer wanted the wrong one.

**How does `pipefail` interact with `grep` returning no-match?** Under `pipefail`, a no-match exit (status 1) from `grep` propagates to the pipeline's exit code. A pipeline like `grep PATTERN file | wc -l` will fail on empty input even though `wc -l` itself always succeeds. Replace the pipeline with `awk` (which exits 0 on empty input) or guard each `grep` with `|| true`.

**Fix.** Replace the chained `grep | grep | wc -l` pipeline with a single `awk` pass that handles empty input gracefully:

```bash
mentions=$(awk -v exclude_re='^@(github-actions|dependabot|renovate)$' '
  {
    line = $0
    while (match(line, /@[a-zA-Z0-9_-]+/)) {
      m = substr(line, RSTART, RLENGTH)
      gsub(/[.,;:!?]+$/, "", m)
      if (m !~ exclude_re) print m
      line = substr(line, RSTART + RLENGTH)
    }
  }
' "$DRAFT" | wc -l)
```

`awk` returns 0 on empty input. The pipeline survives `pipefail`. `wc -l` always produces a count, even if its input is empty. The assignment to `mentions` succeeds. As a bonus, the single-pass parsing is faster than the two-grep chain, and the trailing-punctuation strip (`[.,;:!?]+$`) handles cases where `@username,` or `@username.` appear at the end of a sentence.

There is a more idiomatic patch worth knowing about. If you need to keep `grep`, you can guard the no-match exit code:

```bash
mentions=$(grep -oE '@[a-zA-Z0-9_-]+' "$DRAFT" || true)
mentions=$(printf '%s\n' "$mentions" | grep -viE "$EXCLUDE_REGEX" || true)
count=$(printf '%s\n' "$mentions" | grep -c . || true)
```

`|| true` swallows the no-match exit and keeps the pipeline non-zero from propagating. This works but is brittle: each `grep` needs its own guard, and you lose the ability to detect actual errors (bad regex, missing file). The `awk` approach is cleaner because the failure semantics are inherent to the tool rather than papered over with `|| true`.

This bug is so common that it is worth memorizing as a rule: **a bash pipeline that contains `grep` and runs under `pipefail` will fail-closed on no-match unless explicitly guarded.** The day every engineer learns this is the day they stop writing one class of intermittent gate bug.

## Why the framework's own bugs surfacing in its first run is the framework working

A reasonable response to "your anti-slop framework had three slop-class bugs in itself on day one" is "then why should I trust it." The honest counter-argument is that the alternative — a framework that exists and looks polished but has never been pointed at a real upstream — is strictly worse, because its bugs are still there and are now invisible.

Three things make the meta-irony useful rather than damning.

**The bugs were in production-shaped code paths, not in test fixtures.** The 26-assertion E2E install test passed. The 41 bats cases passed. The shellcheck and pre-commit gates passed. None of them exercised the specific interaction between `gh api` and a 404 response on a real public repo, the specific interaction between `awk -v RS='---'` and round-tripping a real candidate file through the state machine, or the specific interaction between `pipefail` and an empty grep on a real first-draft input. Synthetic test fixtures cannot generate "the upstream returned a 404 because the file does not exist" with the same authority as a real upstream's actual 404. They can simulate it, but the simulation is the engineer's mental model of what 404 looks like, which is exactly the model that contained the bug.

**The bugs were named, categorical, and fixable.** All three reduce to one-sentence rules that any engineer can carry forward: "exit codes, not stdout, are the contract for CLI probes." "Don't do structural edits to YAML/JSON with line-oriented tools." "Bash pipelines with `grep` under `pipefail` need to handle no-match." The fixes shipped in the same day. They are preserved as regression tests. They are documented in CHANGELOG with the failure mode named.

**The framework's gate-runner architecture is exactly the right shape to detect these classes of bug going forward.** A new gate could probe for the exact stdout-vs-exit-code conflation pattern across all probe scripts in the bundle. A new gate could static-check any script that pipes `grep` under `pipefail`. A new gate could refuse YAML-mutating scripts that don't shell out to a parser. Three days from now, the framework will have gates that catch the very bugs it shipped with. That feedback loop is the architectural purpose.

The point of having 41 gates plus a real qualifying flow is precisely that the framework can find its own bugs in production. A framework that cannot be falsified is not trustworthy. One that surfaces three of its own failures within hours of release is.

## Side narratives, briefly

Two other things shipped on the same day and are mentioned only to set the context: [**nixtla v1.10.0**](/blog/five-releases-fifteen-minutes-mandy-cutover-and-freeze-break/) rolled 12 plugins to v1.0 alongside two honest-PoC and six v0.1.0-wip scaffolds; **lilly-75-holy** is a brand-new habit-tracker repo whose first day ended in an 18-iteration CI debug marathon that fell back to a Tailscale auth-key path after the OIDC trust route did not work as expected. Both are their own forthcoming case studies. The relevant point for *this* article is only that day-one debugging on contributing-clanker happened against an active multi-repo backdrop, which kept the "ship the fix today, named, with a regression test" discipline in operator muscle memory — the same discipline that landed [yesterday's five-release sprint](/blog/five-releases-fifteen-minutes-mandy-cutover-and-freeze-break/) and the [VPS-as-the-home eight-iteration deploy](/blog/vps-as-the-home-day-1-eight-deploy-iterations/) the day before.

## Three bash rules to carry into the next script

Compressed for the file you keep in your head:

1. **Exit codes, not stdout, are the contract for CLI probes.** When checking whether something exists via `gh`, `kubectl`, `aws`, `gcloud`, or any networked CLI, gate on the exit code and discard both streams. Treat any non-empty stdout from a probe as advisory, never authoritative.
2. **Don't do structural edits to YAML/JSON/TOML/XML with `sed`, `awk -v RS`, or shell string manipulation.** Shell out to a parser. Round-trip the data structure. Preserve quoting and indentation invariants by letting the parser re-emit them. Yes, it's slower. The speed cost is rounding error compared to the maintenance cost of a structural-corruption bug shipped to production.
3. **Bash pipelines containing `grep` under `pipefail` will fail-closed on no-match unless explicitly guarded.** Either replace the pipeline with a tool that returns 0 on empty input (`awk`, `python -c`), or add `|| true` guards on the no-match boundaries, or check for the specific exit code 1 versus other failure codes before propagating.

Any one of these rules will save someone an afternoon. Together they describe a single discipline: assume your tooling has hidden contracts about what success and failure look like at the byte and exit-code level, and design your scripts to make those contracts explicit at the boundaries between processes.

## Closing

The architecture of trust in an OSS contribution framework depends on actually running it against real upstreams. Synthetic fixtures will not surface the kinds of bugs that real upstream repos surface. The three bash silent-failure modes that v0.1.2 patched — exit-code-vs-stdout conflation on `gh api` 404, line-oriented `awk -v RS` and `sed -i` against structured YAML, and `pipefail` with a no-match `grep` returning fail-closed — are independently useful to anyone who writes shell or maintains release tooling. The minor scoping fix shipped as v0.1.1 hardened the SKILL.md against future drift.

The framework that catches AI slop has now been falsified by its own first real run, in three independently useful ways, and is stronger for it. The next qualifying flow against the next upstream will surface a different category of bug. That is the architectural intent. Frameworks earn trust by being run, not by being shipped.

<script type="application/ld+json">
{
  "@context": "https://schema.org",
  "@type": "BlogPosting",
  "headline": "An Anti-Slop Framework Found Three Bugs Inside Itself on Day One",
  "url": "https://startaitools.com/posts/anti-slop-framework-found-three-bugs-inside-itself/",
  "datePublished": "2026-05-03T08:00:00-05:00",
  "author": { "@type": "Person", "name": "Jeremy Longshore" },
  "keywords": "bash, silent failures, gh-cli, yaml, oss-contribution, release-engineering, claude-code-skills",
  "articleSection": "Technical Deep-Dive",
  "about": [
    { "@type": "Thing", "name": "gh CLI 404 stdout conflation" },
    { "@type": "Thing", "name": "awk RS YAML mutation" },
    { "@type": "Thing", "name": "pipefail empty grep fail-closed" }
  ]
}
</script>
