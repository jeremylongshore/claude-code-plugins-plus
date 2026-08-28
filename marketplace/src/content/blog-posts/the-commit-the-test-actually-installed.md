---
title: "Bind the Receipt to the Commit It Installed"
description: "An E2E test receipt that carries the installed commit hash makes provenance checkable. Six commits on one lane, three of them asserting a literal string."
date: "2026-08-27"
tags: ["testing", "ci-cd", "devops", "automation", "release-engineering", "architecture"]
featured: false
canonical: "https://startaitools.com/posts/the-commit-the-test-actually-installed/"
---
An end to end lane that installs your plugin from GitHub is testing whatever GitHub happened to
serve. That is usually your latest push. It is sometimes a push from twenty minutes ago, a cached
object, or a branch you forgot you were on. The lane passes either way, and the receipt it writes
looks identical either way.

That is the gap I closed on the Foundry rig lane. The receipt now carries the commit hash of the
artifact that was actually installed, and the harness refuses to write the file unless that hash
equals local `HEAD`. Test provenance is now checkable, not decorative.

## How do you verify an E2E test installed the correct commit?

Read `HEAD` out of the installed tree on the rig, put it on the receipt line, parse that line on the
local side with an anchored regex, and compare the captured hash against local `HEAD`. The receipt
must carry both commits and pass both checks before the proof file is written. A fixed string
receipt proves only that `echo` works.

## What Foundry is, so the test makes sense

`omarchy-foundry-entry` is a new repo, created this day, twelve commits on first parent. It is an
Omarchy plugin that generates a starter plugin tree for a small bar widget: manifest, QML entry
point, a pure data `Model.js`, an offline test, README, license, SVG banner.

The README is blunt about the boundary. Foundry is "intentionally a scaffold and proof surface,
not an autonomous shell agent, plugin store, or publisher," and it "never installs, enables,
commits, pushes, sends telemetry, or files a marketplace issue." Runtime dependencies are `bash`
and `jq`. Node is development only. It runs the generated test suite and is never needed by the
widget at runtime. Until a validation lane runs, Foundry reports its proof state as `UNPROVEN`,
which is not the same word as failing.

The initial commit was 2,614 insertions across 32 files, including nine gate scripts under
`scripts/gates/` (`c28-voice-no-dashes`, `c29-private-names`, `c30-md-strikethrough`,
`c31-omarchy-qml-security`, `c34-omarchy-exec-injection`, `c35-omarchy-runtime-dependency`,
`c36-omarchy-qml-overflow`, `c38-omarchy-ssrf-host-allowlist`, `c40-omarchy-panel-design`) plus a
293 line `minimax-review.yml`. The scaffold itself landed in `43e5b11`: `bin/omarchy-foundry` at
+135, `tests/foundry.test.js` at +72, `Panel.qml` at +66/-124, `Model.js` at +23/-32.

## The receipt that could not fail

`scripts/rig-e2e.sh` arrived at +45 lines in `615e61b`, got hardened to +44/-36 in `ae779f9`, and
grew the real runtime certification at +81/-31 in `8b009f5`. Its whole job is to prove something
`rig-render.sh` cannot: `rig-render` tests Foundry's own panel, `rig-e2e` tests the artifact
Foundry generates.

The first two of those had no receipt line at all, just a PASS echo. `8b009f5` introduced one,
and for three commits it was a fixed string:

```bash
echo "E2E_RECEIPT foundry=github generated=file-git node=shadowed hostile_id=refused shell=loaded"
```

and the local side matched it against the same fixed string. Read that line as an assertion and it
says nothing. `foundry=github` is not a measurement of where the plugin came from. It is a literal
I typed, reprinted back to me by a shell that would have printed it regardless. Every field on the
line was load bearing except the two that described provenance, and those were decorative.

`9d6cfc8` fixed it in +9/-3 on the harness and +15 on `bin/omarchy-foundry`. The remote side now
reads the installed tree's HEAD, the generated tree's HEAD, and puts both on the wire:

```bash
foundry_commit=$(git -C "$foundry" rev-parse HEAD)
# ...
generated_commit=$(git -C "$generated" rev-parse HEAD)
echo "E2E_RECEIPT installed_foundry=$foundry_commit generated_tree=$generated_commit node=shadowed hostile_id=refused shell=loaded"
```

The local side stopped comparing strings and started parsing:

```bash
[[ "$LINE" =~ ^E2E_RECEIPT\ installed_foundry=([0-9a-f]{40})\ generated_tree=([0-9a-f]{40})\ node=shadowed\ hostile_id=refused\ shell=loaded$ ]] || {
  echo "rig-e2e: missing or malformed receipt line" >&2
  exit 1
}
INSTALLED_COMMIT="${BASH_REMATCH[1]}"
GENERATED_COMMIT="${BASH_REMATCH[2]}"
[[ "$INSTALLED_COMMIT" == "$COMMIT" ]] || { echo "rig-e2e: installed GitHub artifact ($INSTALLED_COMMIT) does not match local commit ($COMMIT)" >&2; exit 1; }
```

The anchored regex matters as much as the equality check. A receipt that can be matched loosely is
a receipt that can be matched by a partial line, and the failure mode of a partial line is a pass.

Only after both checks does `jq` write `.rig-e2e-proof.json`. Here is what landed:

```json
{
  "commit": "9d6cfc8316b4e58695057027bdd16cb0a891c5ff",
  "installedFoundryCommit": "9d6cfc8316b4e58695057027bdd16cb0a891c5ff",
  "generatedTreeCommit": "0d4a667e408a4aac56ce91c9ef490fe348dacfe3",
  "rig": "intent-ops-buzz/omarchy-rig",
  "foundryOrigin": "github",
  "generatedOrigin": "file-git",
  "node": "shadowed",
  "hostileId": "refused",
  "generatedShell": "loaded",
  "completedAt": "2026-08-28T04:13:20Z"
}
```

Two fields with the same forty characters. That repetition is the entire assertion, and it is
visible in the artifact instead of buried in the harness. A reader can check it without reading
the script. Being honest about the sequence: the first receipt landed in `f7be14d` without an
`installedFoundryCommit` field at all, and the version above was refreshed into place three commits
later in `1ccaa75`. The proof got the field before the proof was correct.

`.rig-proof.json` sits alongside it, written by a different script for a different reason.
`scripts/rig-verify.sh` does its own round trip to the rig and records
`omarchyPluginValidate: 0`, `qmllintErrors: 0`, and fingerprint `913620eb`. Its header explains
why it has to exist: gates C32 and C33 in the shared runner (not among the nine in this repo) call `gate_skip` when `omarchy-plugin-validate` and
`qmllint` are not on the local box, and they never are, because they live on the rig. The gate
runner counts SKIP as pass, so the submission lane "happily printed verdict PASS, 0 BLOCK for a
plugin that had never run on Omarchy at all." That is the same failure the E2E receipt had, one
layer down. (`rig-render.sh` is a third lane again: it screenshots the panel and writes
`preview.png`.)

## What the lane actually does on the rig

It SSHes to a real Omarchy rig (`intent-ops-buzz`, container `omarchy-rig`) and runs a chain where
each step's failure is a real exit:

1. Installs the plugin from its GitHub URL, not from the local working tree.
2. Reads the installed commit and compares it to local HEAD.
3. Generates a starter plugin and runs its offline tests, `omarchy-plugin-validate`, and `qmllint`.
4. Git commits the generated tree and installs that via `file://`, then confirms it reports
   enabled in `omarchy plugin list --json`.
5. Shadows Node and boots the real Quickshell session headless under sway.
6. Greps the shell log for load errors, filtering known headless noise.
7. Screenshots with `grim` and asserts the PNG is at least 4000 bytes.
8. Asserts a hostile plugin id is refused.

Step 5 is the one I like. The README claims Node is development only. That claim is cheap to write
and easy to be wrong about, because a machine that has Node installed will never tell you when
something quietly reached for it. So the lane makes the claim expensive:

```bash
# A stock graphical session does not need Node. Put a failing node first on the
# path and prove the generated plugin still loads in a real shell.
mkdir -p /tmp/foundry-nonode
printf '#!/bin/sh\nexit 127\n' >/tmp/foundry-nonode/node
chmod 755 /tmp/foundry-nonode/node
# ... conditional headless sway launch, then pkill any running qs ...
PATH=/tmp/foundry-nonode:/root/omarchy/bin:/usr/bin:/bin qs -p /root/omarchy/shell >/tmp/foundry-generated-qs.log 2>&1 &
```

A fake `node` that exits 127, first on PATH, and then a real shell session on top of it. If the
widget touches Node at runtime, the session tells you. The hostile id (`io.github.e2e.bad;dispatch`)
gets the same treatment: the test passes only when the create call fails.

Step 6 deserves an honest note. The noise filter is the one place where this lane can quietly stop
failing. `c033583` is a single changed line that added `pw_loop_new` and `pw.loop` to the exclude
list and made that second grep case insensitive, because pipewire on a headless rig emits errors
that have nothing to do with the plugin. That is a correct fix and also a widening of the blind
spot. Every entry in that exclude list is a category of real error the lane will now swallow, and
the list only ever grows. I would rather write that down than pretend the filter is free.

`926835f` on the same day is 0 insertions and 0 deletions: a mode change restoring the executable
bit on the harness. A test that cannot execute is not a failing test, it is an absent one.

The obvious alternatives all lose for the same reason. Installing from the local working tree is
the easiest lane to write and it tests the wrong artifact: nobody installs your working tree.
Trusting the git ref you just pushed proves what you intended to publish, not what the remote
served back. And comparing the receipt against a fixed string, which is what this lane did for
three commits, proves that `echo` works. Only reading HEAD out of the installed tree and comparing
it locally closes the loop.

## The badge that was allowed to be wrong

The day's other decision was on the GitHub profile README, and it went the other way for the same
reason.

Session one: seven stargazer badges rendering broken. The obvious guess is that repos went private
or got renamed, so that got checked first. All seven were public with stars (2,679 / 0 / 37 / 5 /
12 / 1 / 27), which eliminated the repo hypothesis and pointed at the URL. Root cause was a raw
star emoji in the shields.io query string. Unencoded it returns HTTP 400 and zero bytes. As
`%E2%AD%90` it returns HTTP 200 and renders. One character, seven badges. Two hero counts were also
understating, so they were bumped to 3k+ and 150+ (stars read 2.5k+ against 3,016 actual,
projects read 125+ against 151), and every
badge in the file got re-fetched afterward, not just the changed ones: 27 OK, 0 broken.

Session two, the ask was to make both hero badges dynamic. Only one of them became dynamic.

Stars has a shields built in account level endpoint, `github/stars/jeremylongshore?affiliations=OWNER`,
served from shields' own authenticated GitHub tokens. Six consecutive fetches, six returned 3.1k.
That is a different number from session one's 3,016 for two reasons: the non-fork count had
ticked to 3,017 by then, and the account level endpoint also counts forks, which takes it to
3,076.
Projects has no built in equivalent. The only route is the generic `dynamic/json` badge pointed at
`api.github.com`, which proxies the unauthenticated GitHub API: 60 requests per hour, shared across
everyone on the internet using it. Five consecutive fetches of that exact URL returned
`invalid / 151 / 151 / 151 / invalid`. Two of five failed.

So Projects stayed hardcoded at 150+ against an actual 151. `ce4d1b3`, one line changed, and the
commit message argues the case under a heading that says which of the two went live and why the
other did not.

The transferable part is the shape of the two wrongnesses. A hardcoded badge rounded down is wrong
in a bounded, known direction, and it drifts slowly. A badge that renders the word "invalid" two
times in five is wrong in an unbounded direction on the most viewed page you own, and it fails
loudest in front of strangers. "Make it live" sounds like a preference. It is a request to add a
dependency, and the answer to it is a measurement, not an opinion.

## The version number that refused to move

**intent-outreach v0.2.0**, `1b5b444d`, merged as PR #34. A 2026-08-19 consistency audit had found
the changelog two months stale. The release backfilled it, bumped 0.1.0 to 0.2.0 across
`package.json`, both plugin manifests, and the MCP server identity, regenerated the bundle so the
CI freshness check holds, added a missing doc index entry, and corrected a README architecture
diagram that omitted the `list_connectors` MCP tool. Verified with a clean typecheck, 244/244
vitest, and a passing offline eval gate.

The decision there is the same refusal in a different costume: it cut a fresh 0.2.0 rather than
amending the untagged 0.1.0, and gave 0.1.0 a retroactive tag at `ee6a2149`, the real end of day
June 16 commit. Reasoning from the commit body: 0.1.0's content shipped June 16, and rewriting its
section to absorb two more months would falsify the release history. Version numbers are a claim
about when something happened.

## Also shipped

**intent-outreach** also merged PR #33 three minutes earlier, unrelated to the release: it gated
OpenAI (gpt-4o) into `SUPPORTED_PROVIDERS` through the eval harness.

**omarchy-desk-transition-entry**: `9383567` covered the monitor commands (`tests/helper.test.js`
+72), and `02c8814` made the transition scenes previewable (`Panel.qml` +155/-20, plus render and
preview PNGs).

**omarchy**: `455e292` started tracking submitted plugins in the README (+20/-5), and `496fcb2`
refreshed the live marketplace table (+10/-10).

**claude-code-plugins**: `9b57c6502` gated exports before Dolt identity setup in
`freshie/scripts/dolt-sync.py` (+6/-1).

## On the models

Worth naming only because the split was clean. Claude Opus 5 ran both github-profile badge
sessions, including the hypothesis test that eliminated repo visibility before anyone touched the
URL. Claude Fable 5 ran the intent-outreach release. Claude Sonnet 5 was also in the day's roster.

Zero course corrections in the transcript, which is not a boast. It means the day had one real
investigation in it, the badge one, and the rest was building things that worked. The recorded
failures on the dev box number nine in the digest, and the ones with a legible cause were shell
alias papercuts (`command not found: eza`, `command not found: bat`). The rest were bare
exit codes, a Python traceback, a Reddit fetch the harness could not make, and the harness
refusing a `sleep 45`. None of that is a story, which is why it gets a sentence rather than a section.

## Related Posts

- [A Green Result Only Covers What It Ran](https://startaitools.com/posts/a-green-result-only-covers-what-it-ran/)
- [The Skip That Counted as a Pass](https://startaitools.com/posts/the-skip-that-counted-as-a-pass/)
- [The Green Badge Came Back Through a Hyphen](https://startaitools.com/posts/the-green-badge-came-back-through-a-hyphen/)

<script type="application/ld+json">
{
  "@context": "https://schema.org",
  "@type": "BlogPosting",
  "headline": "Bind the Receipt to the Commit It Installed",
  "description": "An E2E test receipt that carries the installed commit hash makes provenance checkable. Six commits on one lane, three of them asserting a literal string.",
  "author": {"@type": "Person", "name": "Jeremy Longshore"},
  "datePublished": "2026-08-27T10:00:00-06:00",
  "url": "https://startaitools.com/posts/the-commit-the-test-actually-installed/",
  "inLanguage": "en-US",
  "wordCount": 2246
}
</script>
