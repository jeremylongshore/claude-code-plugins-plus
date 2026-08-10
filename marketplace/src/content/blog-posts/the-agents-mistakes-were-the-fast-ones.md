---
title: "The Agent's Mistakes Were the Fast Ones"
description: "Six agent failures on a self-hosted team relay. Five traced back to a rule I wrote down and never made anything actually enforce."
date: "2026-08-09"
tags: ["ai-agents", "devops", "architecture", "automation", "self-hosting"]
featured: false
canonical: "https://startaitools.com/posts/the-agents-mistakes-were-the-fast-ones/"
---
Intent Solutions runs a chat relay it owns. The software is Buzz, and the property we are building
toward is that humans and AI agents are co-members of the same room, each holding their own key,
every message landing on an audit trail that belongs to us instead of to a vendor. Owning the
record is the entire reason the project exists.

We adopted it knowing exactly what it is. Upstream says out loud that this is preview software. The
bundled object store is labeled evaluation-only. Rate limiting is defined in configuration and not
enforced in code. Several workflow features are stubs. That honesty is what makes adoption a scoped
hardening job rather than an act of faith. When a project tells you where its edges are, you can put
your own gates at those edges instead of discovering them in production.

The team it is for is a founding group of a few dozen people who currently live in a consumer group
chat. The migration is not done. A handful of identities are on the relay so far, and the all-in
onboarding is still open work. I am saying that here rather than saving it for a tidy ending,
because everything below is substrate work for a room most of the team has not walked into yet.

The part that actually matters, and the reason for all of it: agents as members rather than
integrations. Not a bot posting into a channel through someone else's API token. A member with a
key.

Over about two weeks, agents doing that substrate work broke things. Six times, specifically. I
logged all six. Then I went back through them looking for a pattern in the agents, and found a
different pattern instead.

**The agent's mistakes were the fast ones. Mine were slow, invisible, and upstream of nearly every
one of them.**

Five of the six trace back to a decision I made to write a rule down and call it done. The agent
violated a contract that lived in prose. It reported green from a probe that authenticated as the
wrong identity, because nobody had ever made it prove otherwise. It built machinery the contract
said was unnecessary, because the contract was not in front of it. The sixth is an arithmetic slip
in an audit, and I am not going to stretch it into an indictment of me to make the pattern come out
clean. Five is the number, and five is enough.

Those are real failures and they stay on the record below. But an agent that breaks a rule nothing
enforces is not the interesting story. The interesting story is that I wrote the rule, felt
finished, and did not notice for weeks that nothing was checking it.

## Where the agent messed up

An agent solved a real bug, and solved it well. Invited members were not being joined to the
canonical general channel. The fix was CI-proven, reviewer-hardened, and reproduction-tested. Then
it landed on our fork's main branch instead of going upstream through the contribution lane, and it
dragged fourteen upstream-owned paths along with it: two files of relay source, six of desktop
source, all four of upstream's own CI workflows, and both dependency lockfiles. The code was good.
The lane was wrong.
It came out as a single revert, no history rewrite, which is the one mercy of catching it before
anything built on top of it.

The same working session built our own relay images, then went and fought a container registry
credential wall to push them. The fork contract says we deploy upstream's published images and
carry zero patches of our own. None of that apparatus was needed at all. Nobody had to debug it,
because it should never have existed. Work done well against a requirement that does not exist is
still work that gets thrown away.

The audit written about the branch breach documented, correctly, that two lists disagreed: the
enforcement script's allowlist was missing two hash-pin files that the fork contract's must-survive
table names. In the same document, it reported the must-survive check passing at ten of ten,
against a table that names twelve paths. An audit about a counting problem that miscounted the
count.

A functional membership probe reported green while authenticating as the relay owner. The owner is
the most privileged identity on the system and is always allowed. The probe proved that the door
opens for the person who owns the door. It was rewritten to authenticate as a throwaway member
identity, publish a message, read that message back, and clean up after itself, with a separate
assertion that an un-invited key gets refused.

Nine sessions running in parallel on one machine, sharing nothing but a filesystem. One of them
retired a shared library that another was still calling. The failure surfaced as an ordinary
missing file, which is the worst possible disguise a coordination problem can wear, because you
will spend your first ten minutes looking for a typo.

An agent wrote into the canonical naming record that upstream had independently fixed one half of a
problem we were tracking. The upstream fix was open, not merged. Because that document is the
canonical record, every document that defers to it inherited the overstatement. One overclaim in
the right file propagates for free, and nothing downstream has any way to notice, because deferring
to the canonical record is the correct behavior. The document was doing its job. It was just wrong.

None of those six took long to fix once seen. The revert was one command. The probe rewrite was an
afternoon. The miscount was a text edit. Speed of repair is not the measure that matters here.

## Where I messed up

I wrote the fork contract in prose and enforced it with a local pre-push hook, then trusted it. An
agent working through tooling that pushes without that hook, or working from a fresh clone, never
runs it. The repository's required checks were upstream's own, and upstream's checks know nothing
about our contract. The rule existed. The enforcement did not. In one line: the contract lived in
prose and a local hook, not in a required check. Every minute the agent spent on the wrong branch
was a minute I had already paid for weeks earlier.

The difference between a rule and a gate is who has to remember. A rule delegates the remembering
to whoever shows up next, and a fresh clone remembers nothing. A gate remembers on their behalf and
does not get tired. I knew that. I have said it about deploy pipelines for years. I did not apply
it to the one contract I cared most about, because I was the one who wrote it, and writing it felt
like the work.

The nine parallel sessions were my decision too. An agent does not choose to be one of nine. I
fanned that wide because it is faster, and the coordination mechanism I gave them for the one
surface they share is a journal file each session is asked to append to, plus a convention that
says commit early or work in an isolated tree. Both of those are rules. Neither is a gate. A
session that never read the convention is indistinguishable from one that read it and was in a
hurry, and the retired library proves which one I actually shipped: that refactor was complete and
correct and was never committed, so the next session found a tree missing a file and a guard that
refused to run on a dirty one. I have the exact diagnosis written down one paragraph up, and I did
not apply it to the surface I was running nine things on.

I put two repository names into the canonical record for repositories that were never created. One
of them got the same string as a real production host. When that collision started causing
confusion, I wrote a rule saying that a bare use of the name is a defect to fix on sight. Read that
again. A name that needs a footnote every time it appears is itself the defect. Killing the phantom
removed the collision at the source, so the rule got deleted rather than policed, and deleting it
cost nothing and broke nothing. That is the tell. I had built a permanent maintenance burden, and
enforced it on every mention for weeks, to manage a problem whose entire existence was a line I
wrote.

I wrote the documentation for myself, so nothing ever executed it. There is one reader and the
reader is the author, which means the runbook and my head agree, and the agreement is never tested.
Wrong documentation can sit there indefinitely at zero cost, because the only person consuming it
already knows the answer. Handing it to a new lead priced it immediately. The access list grew from
six grants to nine while it was still being written. Two grants that looked exactly like access
were not access at all: one invitation could never be delivered, because the mail path was never
configured, and one was a data row with no invitation behind it. A ghost that looks like a grant.

Key custody was never decided, only deferred. Five separate open items were each waiting on the
same missing choice, and the inventory that would have surfaced that was itself open and had never
been run. The forcing function was a handover, not an audit. I was about to hand someone a
production system whose master decryption key existed in exactly one place on one disk, with no
export, and only then did the deferral start to look like a decision I had actually made. Two
things the audit had not caught: the backup repository's key was stored inside the repository it
protects, and its passphrase was a single-copy file on that same host. Escrowing the key alone
would have closed a high-priority item while leaving the actual failure completely intact. That is
the worst outcome available, because it retires the ticket that would have made someone look again.

I shipped a coverage manifest whose vocabulary could not express "someone looked and there is
none." It could say nobody has looked. It could say protected. It had no word for a confirmed
absence. So the production system with no off-site copy at all was simply left out of the list, and
a sixteen-row manifest read as complete. An absence you can name is an absence you can page on. An
absence you cannot name is indistinguishable from a thing nobody has checked yet, which is to say
it is invisible in exactly the way that matters.

I never watched a control fail on purpose, so I did not know whether I had one. A document asserted
that a compromise of one machine could not reach the backup history. Both facts it cited were true.
No authorized keys were installed. No SSH daemon was listening on the standard port. Neither of
those was the actual access path, which ran through a different mechanism nobody had enumerated.
It was reasoning from the wrong evidence, which is harder to catch than a lie, because every
individual sentence in it survives review. An isolation claim justified by the absence of one
mechanism is worthless unless every other mechanism has been enumerated. The acceptance test now is
a delete that has to fail. I wrote that claim and then never once tried to falsify it, and for as
long as it stood unfalsified it was not a claim at all. It was a preference with a paragraph built
around it.

Those seven did not get fixed in an afternoon. Two of them needed a personnel handover and a first
login to a machine nobody had logged into, before anyone looked at all. Every one of them had been
sitting in a file I wrote, in language I still agree with, the whole time.

## What we accomplished

Bounded, and all of it verified rather than asserted, which is the only reason it is worth listing
after everything above.

A relay we own, closed from first boot, on a dedicated host with its own ingress. A fast-moving
pre-release stack does not share a kernel, a disk, or a memory ceiling with the workloads that pay
the bills.

Proof that it says no, not just proof that it is running. An un-invited key gets refused over HTTPS
from off the network, plus six classes of unauthenticated request that all have to be rejected and
all six are.

Backups that restore. A named recovery point restored onto a different machine, with the exact
production message physically present, membership intact, and the door still shut afterward.
Recovery time of about three minutes, measured rather than estimated. A proven restore is not a
second copy, which is the distinction the last section is about.

Key custody written down as a register: live copy, escrowed copy, and the command that proves each
one works. Proven by destroying a key inside a copy of the repository and recovering it from the
escrow alone.

Contract violations now fail at the gate instead of in review. The fork gates are a required check,
and a deliberate canary that touches an upstream path goes red.

The estate's own alerting moved onto the relay, so the system posts into the room the team will
live in rather than into a mailbox nobody opens on a Saturday.

## What we are trying to accomplish

The goal is a surface where the agents doing the work are members rather than integrations. They
hold their own keys. They post under their own identity. Their output is reviewable in the same
room, by the same people it affects, at the time it happens. And the company owns the record
instead of renting it. That is a different thing from a chat app with a bot in it, and the
difference is exactly the substrate work above.

The distance still to travel, stated plainly:

- The team is not moved yet. A handful of identities on the relay is not a migration.
- Production still holds one copy of its data. The key is escrowed and restore-proven. The off-site
  copy of the data itself does not exist.
- The most privileged human identity in the system lives on the least backed-up, least monitored
  machine in the estate.
- The automatic updater is installed and deliberately not armed, because arming it means unattended
  weekly deploys of pre-release software onto a live event store.
- One encryption recipient that can decrypt every production secret is documented nowhere. It is
  recorded as an open question rather than removed, because a wrong removal locks out whatever
  depends on it.

The mistakes I could see got fixed the same week. The ones that cost the most were rules I had
already written down, and having written them down is precisely what made them invisible. A rule on
paper feels finished, and a finished thing does not get looked at again. Nothing in this estate was
watching any of them, and I was the only person in a position to notice that, which is the part
that took two weeks.

## Related Posts

- [Onboarding One Person Audited the Whole Estate](https://startaitools.com/posts/onboarding-one-person-audited-the-whole-estate/)
- [Three Copies of the Key, None of the Passphrase](https://startaitools.com/posts/three-copies-of-the-key-none-of-the-passphrase/)
- [The Check That Only Confirmed a Name](https://startaitools.com/posts/the-check-that-only-confirmed-a-name/)
