---
title: "Three Copies of the Key, None of the Passphrase"
description: "Borg backup encrypted across three hosts: each copy holds the repokey, none holds the passphrase. Why redundancy hid a single point of failure."
date: "2026-08-08"
tags: ["devops", "security", "architecture", "automation", "debugging", "backup"]
featured: false
canonical: "https://startaitools.com/posts/three-copies-of-the-key-none-of-the-passphrase/"
---
A new lead is taking over Buzz management. That is the whole reason this work happened, and it is worth being precise about why, because it is not an audit finding.

You do not hand someone a production system whose master decryption key exists in exactly one place, on one disk, with no export. Before the handover, a key loss is a bad day for the person who built the thing and knows where every copy is. After the handover, the same event is unrecoverable, because the new owner has no context to recover from. Responsibility moving is what converts a deferred decision into a live one.

Five items were already open on this. Three P0 beads (`spine-3fy`, `spine-9yg`, `spine-u1a.2.3`), one P1 (`spine-u1a.12.4`), and a set of home-server passphrases nobody had documented at all. Every one of them was blocked on the same missing choice: what is custody. The bead that would have surfaced this, `spine-u1a.12.1`, the secret inventory, is still open and was never run. So the audit did not find this. A personnel change did.

## Does replicating a borg repokey repository survive host loss?

No. With `repokey` encryption the key blob lives in the repository config, so replication carries the key to every copy. The repository passphrase does not travel with it, and `borg key export` output is itself passphrase-encrypted. Replicate the data without the passphrase and you hold three unopenable copies.

## The shape of the failure

The scoping document, `000-docs/151`, said the P0 was about the borg **key**. Export the repokey, escrow it, close the bead.

That would have closed a P0 while leaving the failure completely intact.

```text
buzz repo encryption:  repokey
  -> the key blob lives INSIDE the repository config
  -> `borg key export` produces a file that is ITSELF
     encrypted with the repository passphrase
  -> that passphrase: one 600-mode file, on the same host,
     no second copy anywhere

escrow the key alone  =>  an escrowed artifact nobody can open
```

Worse than that. The passphrase file on the host turned out to be a **different value** from the `borg_passphrase` already sitting in `secrets.prod.sops.yaml`. Verified by sha256 comparison, no values exposed. So there were two single points of failure on one disk, and the one that was already escrowed was the wrong one.

That is the local finding. The estate finding is the reason this post exists.

## The redundancy is what hid it

Executing the fix meant building a register, `ops/host/secrets/KEY-CUSTODY.md`: 13 key classes, each row carrying its live copy, its escrowed copy, and the command that proves the escrowed copy works. References only, never values. Writing that register surfaced three things no document in the estate held.

The first one is the thesis.

The dev box (`team-server`) runs its own borg repo. Also `repokey`. 1.93 TB of source data deduplicated down to 84 GB of archives, replicated to the VPS and from the VPS onward to the home server. Three copies, three machines, two physical locations.

Every one of those three copies carries the encryption key, because `repokey` puts the key in the repo and replication copies the repo. The passphrase did not ride along. It was a single 600-mode file on the dev box, and as far as any document in the estate was concerned, that was the only copy in existence.

Lose the dev box and you are holding three undecryptable copies of everything. The replication is exactly what made that look solved. A coverage table, a backup dashboard, a mental model of the estate, all of them read "backed up three ways", and all three were right about the bytes and wrong about the access. The insurance policy and the thing it insures failed together, because the value that opens the data was the one value that never got copied with it.

That turned out to be almost true rather than exactly true, and the exception is worth holding until the end of this post. Building the register found a copy of the dev-box passphrase in a place no document named. Which does not rescue the point. An undocumented file, on the least-monitored box in the estate, which is currently offline, is not a recovery plan. It is a coin flip you did not know you were holding.

Fixed by escrowing it as `devbox_borg_passphrase`, and proven the only way that counts: open the VPS-side replica using only that escrowed value. It extracted `etc/hostname` reading `team-server`, sha256 `82c0970220c9b48b...` identical to live, 17 archives listed.

The write into `secrets.prod.sops.yaml` was guarded, because a file holding 28 other production secrets is not a file you edit casually.

```bash
# <hash-each-value> is a placeholder: whatever you use to emit one
# "key -> sha256(value)" line per entry. The shape is the point.
sops -d secrets.prod.sops.yaml | <hash-each-value> > /dev/shm/before.txt
# ... add devbox_borg_passphrase ...
sops -d secrets.prod.sops.yaml | <hash-each-value> > /dev/shm/after.txt
diff /dev/shm/before.txt /dev/shm/after.txt
# expect: exactly one added line, zero changed lines, 3 recipients preserved
```

None of the 28 changed. One key added. Three age recipients preserved, one of which is a recipient nobody can identify. That comes back later, and it is the reason "nothing changed" is a weaker guarantee here than it sounds.

## Why not just put the key on another box?

The obvious move is to copy the key material to a second machine and call it redundant. That is what "escrow" sounds like it means.

It is wrong for a specific reason, and the reason earned its own decision number in `decision-log/049` (D174 through D180). Three rules came out of it:

**An escrow is never encrypted to its own subject.** Recovery material that is only readable from the machine whose destruction it insures against is not escrow, it is a second copy of the problem. So the Buzz escrow at `ops/buzz/secrets/buzz.borg-escrow.sops.yaml` is encrypted to the estate key and the shared VPS host key, and deliberately **not** to the dedicated Buzz host key.

That rule lives in `.sops.yaml`, at the exact point where someone would make the mistake, not in a paragraph of a document nobody opens while running a `sops` command. The real comment is longer; this is its shape, with the recipients redacted:

```yaml
creation_rules:
  # KEY ESCROW. Recipients are deliberately the estate key plus the
  # shared-VPS host key, and deliberately NOT the dedicated buzz host
  # key: encrypting a host's escrow to that same host is circular. It
  # would be readable only from the machine whose destruction it exists
  # to survive. See ops/host/secrets/KEY-CUSTODY.md and decision-log/049.
  - path_regex: ops/buzz/secrets/buzz\.borg-escrow\.sops\.yaml$
    age: >-
      <estate-key>,
      <shared-vps-host-key>
```

**The acceptance test is a backup verification drill: a restore using only the escrowed copy.** Never the existence of a file.

**The passphrase is escrowed with the key.** Which is the whole post.

## The drill, and the negative test that is the point

`ops/buzz/scripts/escrow-restore-drill.sh` runs on the host. The sequence matters more than any individual step:

```bash
# 1. baseline from the LIVE repo
borg extract ::"$ARCHIVE" postgres.dump      # 6,988,132 bytes, sha256 97021228c2...

# 2. copy the repo, strip the repokey blob from the COPY, prove it is dead
borg list "$COPY"                            # MUST FAIL. if this passes, the drill is a lie.

# 3. recover using ONLY escrowed key + escrowed passphrase
borg key import "$COPY" "$ESCROWED_KEY"
borg list "$COPY"                            # 11 archives
borg extract ...  postgres.dump              # byte-identical to step 1
pg_restore --list postgres.dump              # 421 restorable objects
```

Step 2 is the one people skip and it is the one that makes the rest mean anything. Without proving the stripped copy actually fails, step 3 proves only that borg found a key somewhere, which it very much will if you leave one lying around.

`pg_restore --list` is there for the same reason. Byte-identical says the extract worked. 421 restorable objects says the artifact is usable. Those are different claims and only the second one is what a restore is for.

One more detail that decides whether the drill tests anything: the escrowed material was re-derived from the **committed** SOPS file before the drill and confirmed byte-identical to the host's live key export. A drill against a copy sitting in a scratch directory tests the scratch directory. The point is to test what is in git. That is the same distinction as [the drills that passed while reality did not](https://startaitools.com/posts/the-drills-passed-reality-did-not/), where a documented posture and the deployed copy had quietly stopped agreeing.

## The drill broke live backup access, and that is the second finding

First run of the drill, live backup access broke. Nothing was lost. Future runs would simply have stopped.

Borg records where a repository id was last seen. Working on a copy re-pinned that location, so the next access to the live repo hit a relocation prompt and aborted. Inside `buzz-backup.timer`, with no TTY to prompt, that is not a visible failure. It is a **silent** one. The timer fires, borg aborts, and the next thing that notices is a restore attempt weeks later.

Caught and repaired the same session. Location re-pinned, then `borg info` and `backup.sh --dry-run` both verified clean with **no override environment variable set**, exactly as the timer runs it. Verifying with an override in your shell verifies your shell.

The script now forces its own state directories, with a comment saying why removing them is not an option:

```bash
# NOT removable. Without these, operating on a repo COPY re-pins borg's
# record of where the LIVE repo lives, and the next timer-driven backup
# aborts on a relocation prompt with no TTY. Silent backup failure.
export BORG_SECURITY_DIR="$DRILL_DIR/security"
export BORG_CACHE_DIR="$DRILL_DIR/cache"
```

Note the shape, because it is the same shape as the passphrase. Borg's location record is state that lives next to the data and gets stomped by touching a copy of it. The passphrase was state that lived next to the data and did not get copied with it. Both are the estate believing the repo carries everything the repo needs, and both fail quietly, which is why the drill has to run with no override set and why the guard is not optional.

Second defect, recorded in the evidence summary rather than quietly fixed: a `sed` redaction masked only the **first** line of a multi-line key blob, so passphrase-encrypted continuation lines reached the session transcript. Partial, passphrase-encrypted, reached no file and no commit and no remote. The redaction method changed immediately. Both defects are in `evidence/2026-08-08-spine-3fy-buzz-key-escrow/` because an evidence bundle that reports only wins is marketing.

## The host that looked most exposed held nothing unique

Third finding from the register, and it went the other direction.

The home server looks like the sharp end. Least monitored box in the estate, least backed up, currently offline. It holds two passphrase files. The expectation going in was a transfer job.

It was not. Both files are the VPS repo passphrase and the dev-box repo passphrase. A value that opens repo X **is** repo X's passphrase, and the scripts on that box `borg check`, `list`, and `extract` exactly those two repos. Both are now escrowed elsewhere, so that whole slice collapsed from a migration into a one-command confirmation. Recorded with its caveats: the box is offline right now, and six days in seven the pull runs `--repository-only`, which needs no key at all.

That is also the exception I promised earlier. The dev-box passphrase was not literally single-copy. There was a second one, sitting on the home server, because a script there needed it to check the replica. Nothing recorded that. It is not in a register, not in a runbook, not in the coverage table. So the estate's actual survival odds on a dev-box loss depended on an undocumented file, on an offline box, that nobody would have thought to look for while trying to open 84 GB of archives in an emergency.

Both directions of that are the same finding. Replication moved the data and not the access. Documentation tracked neither. The register is what made both visible, and the most useful single thing it produced about the scariest host in the estate was proof that there was no gap there at all. An inventory that can only return findings is not an inventory. That is the neighboring failure to [an artifact with a producer and no consumer](https://startaitools.com/posts/nothing-read-it-so-nothing-failed/): here the artifact had a consumer and no record, so key custody was decided by whoever last wrote a script.

Two more things it surfaced, both outside the redundancy story, both worth naming because the same register produced them.

A third age recipient, `age197nar...`, can decrypt every production secret and is documented nowhere (swept `000-docs/`, the runbooks, and the `.sops.yaml` comments, no match). It is one of the three recipients the earlier before-and-after check confirmed as unchanged, which is exactly why "nothing changed" is a weaker guarantee than it reads. Recorded as an open question for the owner and deliberately **not removed**. Removing an unknown recipient locks out whatever depends on it, and you learn which service that was at the worst possible moment.

And the identity fact (D179). The Buzz Desktop app runs on the home server, so the nostr identity `0ace65ad` lives there. The repo could not answer this and actively contradicted itself: `000-docs/033` defines "workstation" as the dev box, `000-docs/142` says the desktop app is on the home server, and three separate docs say "client-side" without naming a machine. Look at the shape of that. Every prior statement in the repo about where a human key lives was a **negative**: "client-side", "never touches our shells". Those tell you where the key is not. Blast radius needs a positive. That identity owns both the CCA private channel and welcome-everyone, so its exposure is a fact about the least-monitored box in the estate, and the docs could not say so because they had only ever ruled places out.

`RUNBOOK-key-incidents.md` priced two keys, `RELAY_OWNER_PUBKEY` and `BUZZ_RELAY_PRIVATE_KEY`, both recoverable, and omitted the one that is not. Added as a fourth incident, honest that it is mostly a warning: an nsec cannot be reset, only a channel's owner can act on it, and the relay owner has no override. Loss permanently forfeits ownership with no administrative path back. It also records the mitigation considered and **not** taken: co-owning channels with Buzz Admin would cost sole-delete rights over the CCA private channel, which is a deliberate confidentiality boundary, so the cheaper fix buys resilience by spending the thing the channel exists for.

## The docs are the handover artifact

Executing `spine-3fy` made several statements across the Buzz documentation set false. Not stale, false. `RUNBOOK-backup-restore.md` carried a MUST-do warning that is now done, plus a correction block asserting it "was also never actioned". Both onboarding guides told the new lead the key had never been exported.

So the set got re-read as a handover artifact instead of spot-checked, and the corrections landed as **dated notes rather than rewrites**, original text retained inline. That is the repo's discipline: when two records disagree, running reality wins, then you fix the loser with a dated correction so the provenance survives. A clean rewrite would have erased the evidence that the estate ever believed the wrong thing, which is the part a new owner most needs to see.

The re-read raised a new gap rather than leaving it silent. `buzz.borg-escrow.sops.yaml` is a **fourth** file in `ops/buzz/secrets/` and the new lead's grant 4 covers three. As written, he would own Buzz operationally and be unable to decrypt Buzz's backup escrow. The lesson that went into his onboarding: executing a remediation is also a re-audit of the remediation.

## What is not fixed

Buzz production still has **no off-site copy**, so the disaster recovery posture stays partial. `spine-9yg`, P0, open. This work unblocks it, because an off-site copy of an undecryptable archive is not a backup, but it does not build the leg. The `coverage[]` row still correctly reads `no_offsite_copy`. Buzz production has exactly one copy of its data. That copy is now decryptable after host loss, which is a different and much smaller claim than being recoverable after host loss. Better than 2026-08-07. Still not a backup.

`spine-u1a.2.3` stays open on its second half: the restore-only age key does not exist. And the age private keys are the bootstrap exception. They cannot be age-escrowed, their out-of-band status is UNCONFIRMED, and losing the estate key makes every escrow described here unreadable. `0ace65ad` is still unescrowed, because that one is an owner-only UI action.

No key was rotated. None is proposed.

## The session that would not build the workaround

Gates green: `pnpm check` exit 0 (markdownlint over 525 files inside a chain of about thirty steps), disclosure gate clean, `gitleaks protect --staged` clean, `ops/buzz/tests/key-runbook-commands-test.sh` 7 of 7 with the new incident added. One real catch on the way through: `validate:buzz-skill-refs` failed because `.claude/skills/buzz-ops/` vendors a copy of the deployment reference that had drifted. Resynced, all three vendored references match canonical.

Handling, since escrowing a key badly is worse than not escrowing it. Plaintext key material existed only in `/dev/shm`, was `shred`ed after encryption, and moved host to host in a single `tar | ssh` stream into a `mktemp -d` with `trap ... EXIT` cleanup. Nothing hit disk on either box.

That work ran with **Claude Opus 5**, four sessions and about twenty hours of span, and one thing from earlier in the day belongs here because it is the same subject. The session opened on an unrelated task, deploying the already-built B3.2b receiver, and hit a wall: no route existed to get `origin/main` onto the VPS. Four routes checked, four closed. The stale VPS checkout was 24 commits behind and carrying a marker file named `STALE-CHECKOUT-NOT-DEPLOY-SOURCE.txt`. A read-only deploy key returned 422, deploy keys disabled org-wide. The VPS PAT in SOPS returned 401, expired. No CI deploy workflow exists.

Every one of those is an invitation to invent a credential. Instead the key material already created got cleaned up rather than left stranded, the blocker was filed as a P0 bead (`spine-7br`), and the conclusion was that this is an owner call and not more engineering. Refusing to route around a deliberately disabled credential with an ad-hoc one is the correct answer on any day. On a day whose entire subject is who can decrypt what, it is the only answer, and it is not the one that feels productive at 2 a.m.

## Also shipped

Three other PRs landed the same day. Different systems, and one of them is the same mistake in a different register.

**PR #405, the collector supersedes its own stale proposals.** Each proposal branch is named after its content digest, so a changed run opens a new branch, and `promotion.py` had no close path at all. The sweep found four open at once, all rewriting the same ~100 generated files, so every extra one was a merge conflict waiting for whoever reviewed second. Close only if the branch carries the collector's prefix **and** the title is the generated proposal title, because a cron job closing a human's PR is far worse than a stale proposal staying open. The guard was proven by planting the defect: remove the title check and exactly two scoping tests fail, one of them the human-PR case. It also retracted an earlier claim of mine with measured data. `rclone size` reports 9.922 GiB current against 11.507 GiB with versions on an 11 GB source, about 1.16x, so "monotonic growth, raising the cap only defers it" was wrong. It is a cap set below the data. Raise it, roughly $0.07 a month, add an alert under it, leave Object Lock alone.

**PR #396, the HQ checkpoint result.** HQ proposed two additions and a direction change. All three had been ratified two days earlier as `decision-log/047`, same six columns, same verbatim framing. Leading with that correction beat burying it, because HQ spending a cycle closing a gap that is already closed is the expensive outcome. The report answers its own seven operational-readiness questions against the B3.2b receiver rather than assuming, and scores **5 of 7**, so by its own rule that receiver is not operational and would not be even if it deployed today. It also records two things the session got wrong, including "byte-identical" asserted before it was proven.

**PR #12 in partner-portals, a false sentence the live page was serving.** It claimed Plane has no SMTP configured. Plane keeps mail settings in `instance_configurations`, not the container environment, so the check that produced the claim looked in the wrong place. Proved live by sending through Plane's own `get_email_configuration()`. The invite genuinely never arrived, but for a different reason: the public v1 API writes the invitation row without enqueuing `workspace_invitation`. And the new lead was never blocked at all, because `__check_signup` treats an existing invite row as an explicit exemption. Same day, the welcome email went through a five-lens review (69 findings, six blockers) and shrank from about 2,400 words to 562, because it had become a mutable snapshot of the guides, which is the "v2 attached to an email" the portal exists to prevent. The skills bundle now ships as portal plus published hash instead of an attachment: a skill carries `allowed-tools` and instructions an agent acts on, and an emailed zip teaches a new hire to trust the next emailed zip.

## Related Posts

- [Nothing Read It, So Nothing Failed](https://startaitools.com/posts/nothing-read-it-so-nothing-failed/) is the backup fabric this sits next to, five defects that all shared the shape of an artifact with a producer and no consumer.
- [The Drills Passed. Reality Did Not.](https://startaitools.com/posts/the-drills-passed-reality-did-not/) is the same gap seen from the other side, a documented posture versus what the deployed copy actually does.
- [Onboarding One Person Audited the Whole Estate](https://startaitools.com/posts/onboarding-one-person-audited-the-whole-estate/) is the day before this one, and the same handover that forced the custody decision.
