---
title: "A Path Is Not Proof of Identity"
description: "A file descriptor binds you to an object. A path does not. Why a stat check plus a later write still loses to a same-UID directory swap."
date: "2026-08-28"
tags: ["security", "testing", "debugging", "devops", "ci-cd"]
featured: false
canonical: "https://startaitools.com/posts/a-path-is-not-proof-of-identity/"
---
Five marketplace submissions rejected simultaneously for the same security defect class. Every one created local state under the default umask, checked permissions with `[[ -f ]]`, then wrote to the name later. Between the check and the write, a same-UID attacker could plant a symlink at that path, and the open would follow it. The first remediation looked like the textbook answer: `umask 077`, `stat -c %s` for size, `timeout 2` on jq, and `mktemp + mv` for atomic writes. The reviewer rejected that too.

The reason is this: `[[ -f ]]` resolves the path, `stat` resolves it again, and `write_session()` resolves it a third time. Nothing binds those three calls to the same inode. A path is a name. A name is resolved fresh on every syscall. Checking a name and then acting on it is a race condition, specifically a TOCTOU (time-of-check-time-of-use) bug. You cannot fix that bug in a language whose only handle is a name.

## The defect class: a symlink race in local state

Five Omarchy plugin submissions hit this defect simultaneously (marketplace issues #2899 through #2903). Each plugin's shell helper:

- created `~/.local/state/<plugin>/` under the default umask, so it was group/world readable during creation
- wrote to a state file via `> "$file"` or `>> "$file"`, which follows a pre-existing symlink
- read the whole mutable file into jq with no regular-file check, no byte ceiling, and no timeout

A symlink planted at the state path redirects the write to any file the user owns. That is a plain symlink attack, and nothing in the helper was positioned to notice it. A FIFO or oversized file at the path hangs the jq that the QML side polls every five seconds.

The contributing-clanker lane (the shared security gate suite) told itself those places were safe. It enforced gates on network input, on QML rendering, on command construction. It never modeled filesystem object identity. A gate lane's blind spot is exactly where threat lives.

## Round one: the rejection

The first remediation shipped what looked like a complete answer. Quiet Queue's round-one attempt (commit 5c7a817):

```bash
umask 077
root="${XDG_STATE_HOME:-$HOME/.local/state}/omarchy-quiet-queue"
session="$root/session.json"
mkdir -p "$root"

session_max_bytes=4096
read_session() {
  local filter="$1" default="$2" size
  if [[ ! -f "$session" || -L "$session" ]]; then printf '%s' "$default"; return; fi
  size="$(stat -c %s "$session" 2>/dev/null || printf 0)"
  if ! [[ "$size" =~ ^[0-9]+$ ]] || (( size > session_max_bytes )); then printf '%s' "$default"; return; fi
  timeout 2 jq -r "$filter" "$session" 2>/dev/null || printf '%s' "$default"
}

write_session() {
  local tmp
  tmp="$(mktemp "$root/.session.XXXXXX")"
  cat > "$tmp"
  mv -f "$tmp" "$session"
}
```

That closes a descriptor and then reopens a mutable pathname. The `[[ -f ]]` check, then `stat`, then `jq` are three separate path resolutions. Nothing binds them to the same inode. Between `stat` and `jq`, a same-UID competitor swaps the file for a symlink. The `write_session` function creates a temp file inside the private directory, but `mktemp` and `mv` each re-resolve `$root`. Rename `$root` to `.parked`, plant a symlink at `$root` pointing anywhere, and both calls land inside the attacker's target. The reviewer said no.

## Why not the obvious approach?

The obvious move was to keep the helpers in bash and add more checks. Bash already powers every other plugin helper. The linting infrastructure already knew how to read it. Adding `[[ -f ]]`, `stat`, and `timeout` is cheap.

It lost because bash has no way to hold a file descriptor across operations. There is no `fstat`, no `O_NOFOLLOW`, no `O_DIRECTORY`. Every check bash can express is a check on a name, not on an object. You cannot fix a TOCTOU bug in a language whose only handle is a name. Leaving bash meant a rewrite of six helpers, a tool orthogonal to the rest of the codebase, and an interpreter that immediately tripped an existing gate banning Perl shebangs as a non-guaranteed runtime (resolved below, in the same commit that taught C41 to see the new helpers). That cost is real. But it is the only honest fix.

Every round-one control has a round-two replacement, and the difference is always the same one thing: whether the check and the use touch the same object.

| Round one, resolved by name | Round two, bound to a descriptor | What changes |
| --- | --- | --- |
| `[[ -f "$session" ]]` then read | `sysopen($fh, ...)` then `stat($fh)` | The thing checked is the thing read |
| `mkdir -p` plus `umask 077` | `sysopen(O_DIRECTORY, O_NOFOLLOW)` then `chdir` | The parent cannot be swapped after the check |
| `mktemp` then `mv` | `sysopen(O_CREAT, O_EXCL, O_NOFOLLOW)` then `rename` | No window to adopt a file you did not create |
| `stat -c %s` then `jq` | byte ceiling taken from `stat($fh)` | The size checked is the size read |
| `timeout 2 jq` | `O_NONBLOCK` at open, then the `-f` test on `stat($fh)` | A FIFO cannot stall the open, and the regular-file check rejects it |

## Descriptor-bound lifecycles

Round two (commit 229d6d4) rewrote the runtime helpers from bash to Perl. The key move: hold the state directory open from the start and never let it go.

```perl
umask 0077;
my $root = File::Spec->catdir($base, "omarchy-quiet-queue");
make_path($root, { mode => 0700 }) unless -d $root;
my $dir;
sysopen($dir, $root, O_RDONLY | O_DIRECTORY | O_NOFOLLOW) or die "unsafe state directory\n";
my @ds = stat($dir);
die "unsafe state directory\n" unless @ds && -d _ && $ds[4] == $<;
chmod 0700, $dir;
chdir $dir or die "cannot pin state directory\n";
```

`O_NOFOLLOW` refuses a planted symlink at open time instead of after. `O_DIRECTORY` means the kernel will not open this if it is not a directory. `O_RDONLY` is the minimum. `stat($dir)` on the open filehandle (the `$dir` object you hold, not the name) proves you own it. `chdir $dir` pins the parent so later relative opens like `session.json` resolve inside the object you hold, not inside a path an attacker swapped.

The read side stats the open descriptor, not the name:

```perl
sub read_session {
  return { until => 0, owned => JSON::PP::false() } unless -e $session;
  my $fh;
  return { until => 0, owned => JSON::PP::false() } unless sysopen($fh, $session, O_RDONLY | O_NONBLOCK | O_NOFOLLOW);
  my @st = stat($fh);
  unless (@st && -f _ && $st[4] == $< && $st[7] > 0 && $st[7] <= $max_bytes) { close $fh; return { until => 0, owned => JSON::PP::false() } }
  # read from $fh...
}
```

`stat($fh)` interrogates the object you actually hold. `O_NONBLOCK` means a FIFO cannot stall the open, which a blocking `O_RDONLY` on a FIFO would do until a writer showed up. It does not reject the FIFO by itself. The `-f _` test against `stat($fh)` on the next line does that. The `$st[4] == $<` check verifies you own this inode. The byte ceiling is enforced against the object, not a name that could be swapped between the check and the enforcement.

The write side uses `O_EXCL`:

```perl
sub open_temp {
  for (1 .. 32) {
    my $name = sprintf ".session.%d.%08x", $$, int(rand(0xffffffff));
    my $fh;
    return ($name, $fh) if sysopen($fh, $name, O_WRONLY | O_CREAT | O_EXCL | O_NOFOLLOW, 0600);
  }
  die "cannot create private session temp\n";
}

sub write_session {
  my ($data) = @_;
  my ($temp, $fh) = open_temp();
  my $payload = encode_json($data) . "\n";
  my $offset = 0;
  while ($offset < length $payload) {
    my $n = syswrite($fh, substr($payload, $offset));
    die "session write failed\n" unless defined($n) && $n > 0;
    $offset += $n;
  }
  $fh->sync or die "session fsync failed\n";
  close $fh or die "session close failed\n";
  rename $temp, $session or die "session replace failed\n";
  chmod 0600, $session;
}
```

`O_EXCL` means you created it or you failed. There is no window where you adopt someone else's file. `fsync` guarantees the data hits disk. `rename` is atomic. Every flag is load-bearing.

## Proving it with an adversary

This is the second time this bug class has come up here. [CodeQL caught the race I dismissed](https://startaitools.com/posts/codeql-caught-the-race-i-dismissed/) covers the same shape in TypeScript, where the fix was a same-descriptor `openSync`, `fstatSync`, `writeSync` chain. Different language, identical lesson.

A unit test that asserts "the file has mode 0600 and valid JSON" does not catch this bug. The bash version would pass that assertion while remaining vulnerable. The test had to become an attacker.

Tests acquired a fixture that races the helper in a tight loop:

```javascript
const fs = require("node:fs")
const [dir, victim] = process.argv.slice(2)
const parked = `${dir}.parked`
for (;;) {
  try {
    fs.renameSync(dir, parked)
    fs.symlinkSync(victim, dir)
    fs.unlinkSync(dir)
    fs.renameSync(parked, dir)
  } catch {
    try { if (fs.existsSync(parked) && !fs.existsSync(dir)) fs.renameSync(parked, dir) } catch {}
  }
}
```

This racer swaps the parent directory itself. The helper opens a relative path inside the state directory; if that directory is suddenly a symlink to somewhere else, the relative open lands elsewhere. The suite asserts the Perl helper holds under it. The bash version would not, by construction: nothing in it survives losing the parent, because everything in it is a fresh path lookup.

## Encoding the lesson so it cannot recur

Two gates joined the contributing-clanker lane on the same day (commit a3ab4eb):

**C41: Fail-closed mutable state lifecycle** (204 lines). It blocks any helper that persists mutable state without a descriptor-bound primitive, testing for `openat`, `renameat`, `O_NOFOLLOW` or a declared secure-state helper. `mktemp + mv` and pathname `-f` checks stop counting as proof, which is the whole point: they were the round-one answer. It separately refuses the lane unless the test corpus carries hostile final-entry, temp-entry, parent-swap and FIFO coverage. The gate blocks, it is not advisory, and its own regression case proves a state helper that trusts mutable pathnames after `mktemp` now fails.

**C42: Bounded local recurring scans** (134 lines). It targets the second class in the same review: a scan on a 5 or 20 second timer that buffers or sorts local input before applying its cap. `find | sort -z | head -25` looks safe because the final output is capped, but `sort` has already enumerated the whole directory. C42 warns rather than blocks, so it flags the shape without failing a submission on it.

Widget template commit 516ccd8 vendored both gates so new plugins inherit them. The `/omarchy-ship` submission auditor now refuses CLEAN status without descriptor-bound lifecycle evidence and hostile parent-swap, temp-entry, final-entry, FIFO, and oversized-input proofs.

Then the new gate had to be debugged against the code it had just forced into existence.

Commit 6d924f3: C41 selected runtime files by `.sh`/`.bash` extension or by a shell shebang, which covered the extensionless bash helpers fine. Then the helpers stopped being shell. A `#!/usr/bin/perl` first line matches neither test, so the newly rewritten helpers were invisible to the gate written to check them. The fix extended the shebang match to `#!/usr/bin/perl`. The same commit had to settle a second collision. C35 (runtime-dependency, an older gate) banned Perl shebangs outright as an interpreter a stock Omarchy install does not guarantee, so the safe rewrite tripped a different gate. Perl was unbanned there because it is a base dependency on the Buzz image, but only with an absolute system shebang, never `env`, so the session PATH cannot swap the interpreter.

Commit c9c52ed: C41's redirect heuristic was `>>?\s*"?\$\w+`, matching `> $file` and `>> $file`. It also matched Perl's fat comma `key => $value` as a shell redirection. A negative lookbehind fixed it: `(?<!=)>>?\s*"?\$\w+`. Do not flag `=>`.

Commit 7d22a5c: That lookbehind was then replaced with a simpler rule. The heuristic was being ported to Perl, and porting a regex to a second language keeps its syntax assumptions. `@items > $limit` is not a redirection either. The honest fix was to scope the heuristic: run the redirect check on shell helpers only. Perl lifecycle safety is established by the descriptor checks themselves, not by a regex that keeps collecting exceptions.

## The audit that refused the claim

The gate work has a mirror at the estate level, and it ran the same night. A gate that passes on a file it never opened and a green CI badge for a check that never ran are the same error: a name standing in for the thing itself. Late the same evening came a 168-line estate readiness audit (omarchy `000-docs/004-AA-AUDT-omarchy-estate-readiness-2026-08-29.md`). It found:

- 16/16 worktrees clean, git fsck clean, 444/444 local tests pass across 16 repos, all hosted gates green
- but: CI proves static and unit tests, NOT a running Omarchy shell. No repo's GitHub workflow executes `rig-verify.sh` or `rig-render.sh`. A green hosted workflow does not prove a plugin loads. Current-source rig proof exists only for Desk Transition, Foundry, and Crew Chief. Widget Template has no proof receipt at all.
- 9 live listings, but only Listening Post's validated commit matches its current head. The other eight reference older snapshots.
- None of the 16 mains has branch protection. 15/16 use mutable action tags. Six repos declare coverage thresholds but invoke raw `node --test`, bypassing the threshold command.

The audit explicitly refused a "best in class" or "fully production certified" claim. It prescribed the honest public status instead: "16 maintained Omarchy plugin repositories; 9 live marketplace listings; all local suites currently green; marketplace verification and production-render certification are tracked per exact commit."

## Also shipped

- claude-code-plugins ed4765e43: enforce marketplace compliance metric ratchets in CI
- intent-blueprint-docs b9297e0: model-neutral documentation platform; 29c2fd8 made package validation race-free (another race, same week)
- omarchy-desk-transition-entry 2e06d94: capture desk transition with active outputs
- omarchy-crew-chief-entry 0ef344e: harden process arguments, proven on the real rig, validator and QML-lint receipts both zero-error, local suite 25/25
- omarchy-workspace-storyboard-entry e597cdc: pin current Node 24 actions
- omarchy-widget-template 868d0f5: land governance scaffolding (editorconfig, gitattributes, issue and PR templates, dependabot, CODE_OF_CONDUCT, CONTRIBUTING, SECURITY)
- omarchy 6f2e2b7 and bfdabf5: refresh live marketplace metrics from scripts/refresh-metrics.sh
- github-profile 6630095 and 23f4930: swap in the cityscape avatar, remove dead embeds, drop a Projects badge GitHub already renders
- comehomealabama 4dea5f5: a journal post shipped through the sibling pipeline

None of those touched a descriptor. The ones that did were the six helpers a reviewer had already sent back twice, and the gate that had to be taught to see them.

## Related Posts

- [Gate the Statement, Not the Tool Name](https://startaitools.com/posts/gate-the-statement-not-the-tool-name/)
- [Every Safety Gate Has a Failure Direction](https://startaitools.com/posts/every-safety-gate-has-a-failure-direction/)
- [Honor the Gate When the Verdict Is Inconvenient](https://startaitools.com/posts/honor-the-gate-when-the-verdict-is-inconvenient/)
