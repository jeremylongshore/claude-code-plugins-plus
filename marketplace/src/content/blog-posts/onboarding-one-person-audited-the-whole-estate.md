---
title: "Onboarding One Person Audited the Whole Estate"
description: "Write down every grant for a new hire and the estate answers: grants that were not access, accounts we could not revoke, a fix that nearly broke a backup."
date: "2026-08-07"
tags: ["devops", "authentication", "architecture", "automation", "onboarding"]
featured: false
canonical: "https://startaitools.com/posts/onboarding-one-person-audited-the-whole-estate/"
---
A new lead software tech starts, and the first deliverable is not code. It is a list of every system he needs
to reach and the exact mechanism by which he reaches it. The new lead is taking the Buzz estate (our fork of
Block's open-source Buzz, on its own production VPS host) plus operator reach into intent-os, the control
plane the estate runs from. Writing that list meant enumerating every access grant, one at a time, and then
actually exercising each one.

The list grew while it was being written, from 6 grants to 9, because exercising one kept surfacing a second
thing that also had to be granted. Every grant that got written down returned something the checklist did not
already know. One of the repairs that followed came within a single cron cycle of breaking something that
already worked.

That is the finding, and it generalizes past this hire. **Documentation you write for yourself can stay wrong
indefinitely, because nothing ever executes it.** You know which sentence is aspirational and which step you
skip. The runbook and your head agree, and the agreement is never tested, because there is one reader and the
reader is the author. Hand the same document to a second person and every gap becomes a support ticket inside
an hour. Onboarding is the first time an estate's self-description runs against something that does not
already believe it.

Claude Opus 5 ran the intent-os onboarding and backup threads and the Buzz naming thread. Claude Sonnet 5
picked up the Bob's Big Brain umbrella thread mid-session, after a Claude Fable 5 limit was hit on a separate
thread. Day totals: 805 tool calls, 1,103 minutes of session span, 32 failure-to-fix arcs, one operator
course correction.

## Two grants that look like access and are not

Plane is the self-hosted project tracker. The new lead was invited at role Member, and the invitation is genuinely
there in the API: role 15, `accepted: false`. By every check a checklist would normally run, that grant is
done.

It is not. The Plane container has no SMTP configured, so the invitation email cannot be delivered, ever. The
row exists and the notification does not. That was found by inspecting the container environment rather than
by assuming the invite behaved the way invites behave. The checklist entry now says: sign up first, then
collect the pending invitation. Two steps instead of one, because the one-step version was fiction.

Twenty, the CRM, is the same class with a different cause. Its API exposes `workspaceMember` as a data CRUD
surface, but there is no real invitation mutation behind it. Creating the record would produce a ghost row
that looks like access and is not one. That grant is now labelled in the checklist as a UI action only, owned
by a human, precisely so nobody automates it into something plausible and dead.

Bob's Big Brain, the governed knowledge layer the estate searches before re-deriving anything, was the grant
that worked as designed. Token minted, actor `newlead`, role `member`, matching another teammate, because
promote and govern stay with two people. The value was not the mint but the three warnings documented next to
it, chosen because they are the three that bite. `tenantId` is required, and omitting it returns **empty
results with a valid token**, which reads exactly like a broken brain and is a config error. The plugin
marketplace is a public repo, so it installs before GitHub org access lands, and every other checklist item
blocks on org access. And it fails closed on bad permissions or invalid JSON, so nobody silently searches an
empty local brain and concludes the knowledge base is thin.

None of that is inferable from a token, so it was exercised against the live API before it went in the guide:

```bash
# no credential, then a fake one
curl -s -o /dev/null -w '%{http_code}\n' "$BRAIN_API/search?q=backup"                              # 401
curl -s -o /dev/null -w '%{http_code}\n' -H "Authorization: Bearer nope" "$BRAIN_API/search?q=x"   # 401

# the new lead's token WITH the tenant scope (drop tenantId and this is 200 with zero hits)
curl -s -H "Authorization: Bearer $NEWLEAD_TOKEN" \
  "$BRAIN_API/search?q=backup&tenantId=$TENANT" | jq '.results | length'                           # 6
```

Six real tenant-scoped hits, each with a `qmd://` citation. The registry was backed up before the edit, and
the plaintext token was never written to it (scrypt pre-hashed) or printed. The commit flagged its own
follow-up: the Plane API key sits in plaintext in `~/.claude.json` and was exposed in a session transcript
that day, so it needs rotating.

## The grants we could not have taken back

Two of the new lead's accounts, the partner-portal basicauth login and the NOW-LMS admin account, were provisioned
against `cgray@asqi.org`. That is his own company's domain. Intent Solutions does not control it.

Password resets, account recovery, and eventual offboarding would all have terminated at a mailbox we cannot
revoke. **Anything Intent Solutions grants must be revocable by Intent Solutions.** That is sharpest on the
LMS account, which is admin on a members-facing production service holding 47 real people's personal data.
Exactly the grant you must be able to withdraw unilaterally.

How it happened is the boring part and the important part. The address came out of the CRM record and got
used as given. `newlead@intentsolutions.io` **already existed**, one of the 65 mailboxes standing on the
domain since the MXroute cutover, and nobody checked. The roster is one authenticated GET away:

```text
GET /email-accounts                       -> 404   (no such endpoint; the flat path does not exist)
GET /domains/{domain}/email-accounts      -> 200   (65 accounts, the new lead's address among them)
```

That 404 is why an earlier probe read as an empty roster rather than a missing endpoint. A 404 on a collection
path is ambiguous between "no records" and "no route," and the probe resolved it in the direction that
required no further work.

The rule went into the guide as the same principle already stated twice in it: section 5's identity rule
(never take a copy of anyone's private key) and, in the operator-access section 6, the address rule (a grant
must be revocable by you alone). A third instance landed later that day. The new lead has to generate his **own**
`PLANE_API_KEY` rather than reuse the one in the estate's MCP config, because a Plane token carries the
permissions of whoever minted it, so a shared key destroys attribution on every write and cannot be revoked
without breaking the other holder. Three rules, one invariant: a grant you cannot withdraw alone is not a
grant you made.

## Why not just UPDATE the row

The obvious repair for a wrong username is one statement. Set `usuario` and `correo_electronico` to the right
address, done in a second, no tooling involved.

That was rejected. `usuario` is the login key that `estudiante_curso` enrollment rows reference, so a hand
UPDATE risks orphaning enrollments against a key that no longer exists, and it bypasses the contract of the
tool that created the account. The provisioner has its own undo. `--rollback` refuses any user with recorded
activity, the new lead had none, so the cheap and safe path was available: roll back, then re-provision clean. It
reported `deleted`, the database confirmed 0 rows for the old address, and after a dry run the live
re-provision put `usuario` and `correo_electronico` both at `newlead@intentsolutions.io`, admins 6 to 7,
students unchanged at 47.

Passwords were deliberately not rotated. Only the usernames moved. Rotating would have meant re-delivering
two secrets to fix a naming error, trading a clerical problem for a secret-handling problem.

The portal side moved the same way. The SOPS user key was updated through `sops set --value-stdin` so the
value never landed in a shell history or an argv, and the Caddyfile was re-keyed behind an
exact-occurrence-count guard that refuses on anything except a single match. Backup taken, `caddy validate`
clean, reload rather than restart. Live afterward: the new username returns 200 on the section and the PDF,
the old one returns 401, and isolation still holds (401 against both the kobiton and scott-porter sections).

The part doing real work is what came next. The new lead's LMS role is admin, and withholding it would have been
the easy-looking call. Section 6, the same section carrying that address rule, already grants full operator
parity: SSH to the host and SOPS decrypt of production secrets. Anyone holding those reaches the LMS database
directly, so withholding the app-level role is a control on paper and not in fact. What it earned instead is
a new section 6a, because this is the first grant where his access outruns his context. An LMS admin sees 47
real members' names, emails and progress, which the estate's [disclosure tiers](https://startaitools.com/posts/disclosure-gate-reject-pii-at-source/)
put off-limits on every surface including the governed brain. The access was already implied. The context around it was not, and only writing
the grant down made that visible.

## The backup the runbook swore existed

`RUNBOOK-backup-restore.md` for the Buzz estate asserted an off-site posture that could not be traced to a
mechanism. It got checked before the handover rather than after, on a simple principle: publishing "we have
not verified this" to the incoming operator is a deferral, not a handover.

Buzz production data reaches no off-site destination at all. Nothing on the `intent-ops-buzz` host pushes
off-host: zero matching systemd timers, an empty root crontab, and the only b2 or rclone string on disk is
inside a comment. But a chain of absences is an inference, and inference is not proof, so the newest archive
that physically reaches Backblaze B2 was listed in full:

```bash
borg list "$B2_REPO::$NEWEST" --format '{path}{NL}' > /tmp/b2-newest.txt
wc -l                       < /tmp/b2-newest.txt     # 499780
grep -c '^var/backups/buzz' < /tmp/b2-newest.txt     # 0
grep -c '^srv/buzz'         < /tmp/b2-newest.txt     # 14
```

Zero entries under `var/backups/buzz`, and the 14 hits under `srv/buzz` are the staging stack's config on the
shared VPS, not production data. That is the difference between "I could not find the mechanism" and "the
data is not in the destination."

It compounds. `backup.sh` initialises with `repokey-blake2`, which stores the encryption key **inside the
repository**, and no exported key exists anywhere. The only copy of the data and the only copy of its key are
the same bytes on the same disk. The runbook flagged that key export as a bold MUST. It was never done.

The coverage manifest was part of why this stayed hidden: it enumerated 16 assets and named Buzz in none of
them, which was fixed by adding the row. The harder half is that the state vocabulary had no way to say
"verified: there is none." The existing value `unknown_backup_posture` means nobody looked, which understates
a P0 as an open question. So the enum got widened rather than reused:

```json
{
  "schema_version": "0.2.0",
  "properties": {
    "backup_posture": {
      "enum": ["offsite_verified", "local_only", "unknown_backup_posture", "no_offsite_copy"]
    }
  }
}
```

Widening an enum is additive evolution and safe under the schema law here. Tightening one is forbidden
without a major bump, because tightening invalidates configs that were legal yesterday. Adding a value only
makes previously-invalid documents valid, which is why 0.1.0 to 0.2.0 is correct and why reusing the existing
value to dodge a schema change would have been the expensive shortcut.

### The near miss

Widening the enum in the repo schema left the **deployed** schema unwidened, and those are two different
files. `b2-offsite-push.sh` refuses to run on a config that fails validation, so the moment the deployed
config carried `no_offsite_copy` against a deployed schema that had never heard of it, that night's 04:00
push would have aborted. Documenting that one backup leg does not exist would have taken down the one leg
that does, as a side effect, silently, at four in the morning.

It was caught by running the real script against the real deployed paths instead of trusting the green tick
on the repo side:

```bash
# repo-side, where the edit was made: clean
bash ops/backup/validate-backup-config.sh ops/backup/offsite-backup.config.json

# the copy the 04:00 job actually reads, BEFORE the deployed schema caught up:
bash ~/bin/b2-offsite-push.sh --check prod
# -> config failed schema validation: backup_posture "no_offsite_copy" not permitted; refusing to push

# and after all three copies were reconciled:
bash ~/bin/b2-offsite-push.sh --check prod
# -> provisioned=true, source present, exit 0
```

A separate defect sits underneath, filed on its own. `validate-backup-config.sh` sets its live target to the
config sitting beside it in the repo, while cron validates the deployed copy under
`~/.config/intentsolutions/` against a **third** copy of the schema in `~/.local/lib/`. Those had drifted for
two days. All three were reconciled after confirming source, targets, `architecture_invariant` and engine
were byte-identical. The guard was then re-proven rather than assumed: the validator reports the live config
clean **and** both self-test fixtures still correctly reject (the drift fixture and the secret-laden one). An
enum widening that also widened what the guard accepts would have been worse than the missing row.

That distinction is the day's second through-line and it runs the other direction too. The new lead's onboarding
guide is not a file he opens. It is a partner-portal site regenerated from the intent-os sources, and it took
five PRs on the partner-portals repo (#7 through #11) to move both onboarding parts and their PDFs from
source to something he can read, each one carrying a secret scan verifying that none of his three credentials
(brain bearer token, portal basicauth password, LMS password) appear anywhere in the built output. The guide
carries the config **shape** with a placeholder; the secrets travel only by email. In both directions the
rule is the same: an edit in the repo is not a change to the system until the thing that reads it has the new
bytes.

None of the actual backup repair is done. Three beads carry it, all owner-gated: escrow the repokey off-box
(P0), which blocks building the leg and keeping the manifest honest (P0), plus fixing the validator's target
(P1). Key custody was deliberately not improvised. Where a production master key gets escrowed is a
blast-radius decision, and the decision log already carries a decided-but-not-executed re-homing of the B2
origin, so today's obvious destination may move next month.

## The repo that did not exist

The session opened with a question about a directory: what is `buzz-worktrees` and why do we have it. It was
a git worktree holding the branch for the Buzz fork's PR #16, the fork-contract breach whose 6 commits
touched 14 upstream-owned paths before being reverted by PR #18. The entire fork-gates system in CI exists
because of it. The worktree was removed after verifying a clean tree in sync with origin, 2 GB reclaimed, and
that exposed a parked design document, which produced the next question verbatim: "wait we have a third buzz
repo? wtf"

No. Ground truth, from the API rather than the docs: `block/buzz` (upstream) and `intent-solutions-io/buzz`
(the fork) are the only two Buzz repos that exist. `intent-ops-buzz` is a production VPS host, not a repo.
`intent-solutions-io/intent-ops-buzz`, the planned contributor lab, was never created, and
`intent-solutions-io/intent-ops-buzz-plugin` was deferred and never created. The root cause is that a repo
which does not exist was given the same string as a production host, and the naming standard papered over the
collision with a rule: "never use the bare phrase; a bare `intent-ops-buzz` is a defect, fix on sight."
**A name that needs a footnote on every mention is the defect.** That rule is fine for the person who wrote
it, who never needed it. It is a trap for the operator being handed the estate this week, who has to read
every mention of that string and guess which of two systems it means, in docs that are supposed to be how he
learns the place. Same gap as the runbook and the checklist, one layer up in the vocabulary.

The first framing of the cleanup was wrong and got corrected mid-stream. It looked like an 86-reference
rename. It is not. More than 80 of those references are the production host, a real VPS with real DNS,
systemd units and scripts, correctly named. Kill the phantom and the collision evaporates in about 8 files.
So the disambiguation rule was **deleted** rather than enforced.

## Also shipped

- **A fork-specific `REVIEW.md`** added to the Buzz fork and registered in all three gate surfaces in
  lockstep: the ALLOW array in `check-additive-only.sh`, the MUST_SURVIVE array in `check-must-survive.sh`
  (twelve paths to thirteen), and FORK.md's must-survive table, then hash-pinned (13 files to 14). The fork
  had no reviewer guidance at all, so the bot reviewed it as an ordinary repo, with no idea that touching an
  upstream-owned path is the defect that matters most there.
- **A combined operator-grade system analysis** across the Bob's Big Brain umbrella and 3 flagship repos, run
  as a 7-agent background workflow, then a consistency validation pass, then the umbrella's PR #80 with all 6
  checks green.
- **An HQ checkpoint** answered by leading with the fact that all three of its "new" asks had already been
  ratified two days earlier in the decision log, because HQ acting on an already-closed gap is the expensive
  outcome. It also recorded the two things that session got wrong, because a checkpoint that reports only
  wins is not a checkpoint.
- **A bug filed against the Twenty MCP server's `update_contact`**, found while correcting the CRM record
  that produced the wrong email address in the first place.

Failure arcs from the same day, for texture: a background workflow rejected with `Invalid workflow script:
Script parse error: Unterminated string constant (28:10)`; the consistency validator falling back to
bootstrap mode with every fact class unowned because `sot-map.yaml` was not at the expected path; the harness
refusing `Blocked: sleep 90 followed by: gh pr checks 80` and forcing an event-driven monitor instead; and a
global `ico` symlink left dangling by a repo rename, so the command was not-found while npm insisted it was
installed.

## The war story that was invented

The one operator course correction of the day is worth the space, because the corrected answer beat the
invention. A community member had asked how to segment a shared second brain so leadership-sensitive content
does not surface to everyone who asks the right question. Claude Sonnet 5 drafted a reply containing a war
story that did not happen. The correction, as typed: "the wqr story is wrong u need to update that repsonse
see all the team," then "mebera that have access to the brain," then "u need to do deep research" and "no
hash tags no ai slop shit."

The rewrite was verified from the plugin repo and the umbrella beads: real tokens for a 6-person team (2
admin, 4 member), 4 of the 5 non-founders had actually queried it, all 5 emailed and tokened as of
2026-07-28.

The real story is stronger than the fabricated one. **Admin versus member gates who can write, not who can
read.** The content classifier catches secrets and personal data on the way in, but has no concept of
"business-sensitive, not a credential," so anything promoted is visible to the whole team. That is an open,
unscheduled gap on a live system, not a hypothetical. The rest follows from the code: the sensitivity gate is
a binary block at capture and promotion time, not a per-viewer filter on the way out; tenant isolation is a
hard multi-tenant boundary carried by the bearer token; tags and prompt-level instructions do not hold as
security boundaries.

Same mechanism as the checklist. Answering an outsider honestly required auditing the live setup, and the
audit found the gap.

## Related Posts

- [Three Commits Between the Rule and the Violation](https://startaitools.com/posts/three-commits-between-the-rule-and-the-violation/) is the other side of the same coin: a rule written down and a violation that the writing did not prevent.
- [The Drills Passed. Reality Did Not.](https://startaitools.com/posts/the-drills-passed-reality-did-not/) covers the same gap between a documented posture and what the deployed copy actually does.
- [Nothing Read It, So Nothing Failed](https://startaitools.com/posts/nothing-read-it-so-nothing-failed/) is the backup fabric this Buzz finding sits next to, and why a manifest shaped like an inventory reads as complete.
