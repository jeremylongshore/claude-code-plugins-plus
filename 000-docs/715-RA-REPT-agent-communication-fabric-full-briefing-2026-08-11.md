<!-- doc-class: record -->

---
title: "Agent Communication Fabric"
subtitle: "Where we are, what the research says, what two adversarial panels found, and the six decisions waiting on you"
author: "Prepared for Jeremy Longshore · Intent Solutions"
date: "11 August 2026"
---

# Read this first

You asked a simple question a few days ago: could we build the best agent-to-agent communication plugin in the world and ship it through TonsOfSkills. This document is the honest answer, and the honest answer is more interesting than a yes or a no.

Three things happened between the question and now.

**First, the research came back and it was good but wrong in specific ways.** I surveyed the field, cloned three competitors, read their source at line level, and produced a competitive analysis with a recommended architecture. It concluded that three capabilities were held by nobody in the world and that we should build a new system clean-room to claim them.

**Second, you pointed out that I had not looked in our own garage.** You asked about `herdr`, about your Slack channel project, and about AGP. All three were absent from the research. When I went and looked, it turned out that two of the three "unclaimed" capabilities were already implemented, by us, under a license we control, shipping at version 0.12.0. The research had surveyed the entire external world and skipped the estate.

**Third, I ran two adversarial panels against my own work, and between them they found nine defects.** Seven seats of business judgment found four. Six named engineering thinkers found five more. Four of those nine were in claims I had personally marked as verified with file-and-line citations. One of them was a live security hole in code that was sitting in an open pull request with a commit message claiming it had been fixed.

So the state of play is: the strategy question is genuinely open, the engineering picture is much clearer than it was, one real bug is fixed and shipped, and there are six decisions that are yours and that I have deliberately not made for you.

This document walks all of it. It is long because you asked for long, and because the most valuable material in it is the disagreement, not the conclusions. Where two smart perspectives collided I have kept both rather than averaging them into mush.

---

# Part I: The assignment, and how it changed under us

## What we set out to answer

The brief was to determine whether a harness-agnostic agent-to-agent communication capability was worth building and distributing through the marketplace. Harness-agnostic matters: the marketplace serves people using Claude Code, but also Codex, Cursor, Cline, Gemini CLI, Goose, OpenCode, and Crush. A capability that only works in one of those is a feature; a capability that works across all of them is a category.

The research needed to answer four things. What already exists and what does it actually do at code level, not README level. What does nobody combine. What can we legally reuse. And what would we build.

## Two corrections I made to my own first pass

Before either panel got involved, I had to correct myself twice, and both corrections are worth recording because they show the failure mode that recurred later.

I initially reported that the "MCP Agent Mail" concept had only tiny lookalike projects with zero to two stars. That was false. `dicklesworthstone/mcp_agent_mail` has 2,078 stars, 219 forks, and roughly 35,000 lines of source. I had searched badly and drawn a confident conclusion from a bad search.

I also reported that a project called `elijahmuraoka/agent-comms` returned a 404 and did not exist. It exists. The skill lives inside a repository called `elijahmuraoka/skills`. Again: a confident negative conclusion drawn from an incomplete look.

Both errors have the same shape, and you will see that shape three more times in this document. **A confident claim built on a search or a citation that was not checked against the thing it claimed to describe.** That pattern is the single most important operational finding in this entire body of work, and I will come back to it in Part VI because it is also the answer to the question you asked me about adversarial sub-agents.

## What changed the assignment

Your intervention. You asked what `herdr` was, and about the Slack channel repo, and about AGP. Those three questions invalidated a section of the research and reframed the central recommendation. I will cover each in Part III, but the headline is that the question stopped being "what should we build" and became "should we build, or should we extract what we already have."

---

# Part II: The field as it actually exists

Everything in this part was verified against source or the GitHub API on 9 August 2026. Where I say a project does something, I read the code that does it. Where I say a project fails to do something, I searched for the thing and found nothing.

## The five families, and why each one is structurally stuck

There are five distinct architectural approaches in this space. Each solves one axis genuinely well and then fails the others not by accident but by construction — the thing that makes it good at its axis is the thing that makes it bad at the rest.

**The live mesh.** Exemplar: `ExaDev/agent-comms`. Every MCP server instance is already a running process, so the bridge processes themselves form a mesh. No daemon, no filesystem, no polling, millisecond latency, real presence. The structural failure: all state lives in in-memory maps. An agent that is not running cannot receive anything, and when the processes exit, every message is gone. It cannot be fixed without becoming a different architecture.

**The durable store.** Exemplar: `mcp_agent_mail`. SQLite as the operational index, git as a human-auditable artifact store, threads, leases, a contact and consent model. The structural failure: it is single-machine by construction. Notification is a local signal file on disk. The project key is an absolute filesystem path, which means the same repository checked out on two machines is two entirely different projects. Cross-machine is not a missing feature, it is excluded by the data model.

**Terminal injection.** Exemplars: `elijahmuraoka/skills` and `ShawnPana/smux`. Type into another agent's terminal via tmux. The enormous advantage is that it requires zero cooperation from the target — it works with any agent that has a prompt, including ones that expose no API at all. The structural failure: no guarantees of any kind. A successful `send-keys` return code means tmux accepted keystrokes, not that an agent received a message. There is no acknowledgement, no correlation identifier, and in neither project any cross-process lock.

**The object-storage relay.** Exemplar: `StanimirTenev/fleetpost`. Push files to object storage, poll for new ones. Offline-tolerant and serverless. The structural failure: hourly latency by design, and there is no send path in the codebase at all — sending is a hand-composed `rclone` command documented in the README.

**The standard protocol.** Exemplar: A2A, 25,262 stars, Apache 2.0, now under the Linux Foundation. Real, versioned, cross-organizational. The structural failure for our purposes: it has no local story. I searched GitHub for A2A used together with local coding agents and got zero results. It is a protocol for service agents talking across organizational boundaries, not for two coding agents on your laptop.

## The projects, individually

### mcp_agent_mail — the incumbent, and the one we cannot touch

35,311 lines of source, 46,114 lines of tests across 120 test files, 820 commits, one contributor.

What it genuinely gets right is worth stealing as ideas. Its SQLite tuning is the best in the field: write-ahead logging, synchronous set to normal, a sixty-second busy timeout, a 256MB memory map, a connection pool, and a passive WAL checkpoint on check-in. It uses `BEGIN IMMEDIATE` for read-check-write transactions, which is the correct primitive and which almost nobody bothers with. It has a genuine dual-store consistency compensation: if the git write fails, it hard-deletes the message rows and re-raises rather than leaving the two stores disagreeing. And it has a contact and consent model with directed links, time-to-live, and a policy enum.

Where it is beatable, and these are all verified at line level:

**Its headline feature does not do what its name says.** Exclusive file reservations are granted even when a conflicting holder is detected. The code appends the conflict to a list and then proceeds to grant the reservation anyway — there is no `continue`, no `else`, no refusal. Two agents can hold "exclusive" leases on the same file glob simultaneously. The only actual enforcement is a git pre-commit hook that is disabled unless an environment variable is set, that trusts a bare environment variable as identity, that honors a bypass flag, and that is defeated by `--no-verify`.

**There is zero prompt-injection defense on the read path.** The message body is stored verbatim and returned verbatim into the recipient agent's context. The sanitization library appears only in the web viewer, never on the path that actually feeds an agent. No provenance framing, no trust tier, no test corpus.

**Identity is bookkeeping, not security.** Tokens are stored in plaintext. Their own command-line tool will read any agent's token with no authentication. A window identifier from an environment variable is accepted as proof of identity.

**It is ungovernable.** Zero of fifty-three pull requests have been merged, by stated policy. Bus factor of one. There is an open priority-zero issue where a kill-based startup seizure lost committed rows and wedged a unit in a permanent crash loop — the reporter's summary is the best line in the whole corpus: *a kill that can lose committed rows converts a liveness problem into a corruption problem.*

There is also a security audit filed against it by an outside contributor across issues 197 through 232 which is, frankly, the most valuable free document in this space. Expired approvals still authorizing. Silent drops of failed deliveries. Invalid policy silently defaulting to permissive. Tokens accepted without a key identifier. Every one of those is the same bug: **fail-open under error.** We should adopt that list as a regression suite.

And we cannot use a line of its code. See Part II's licensing section.

### ExaDev/agent-comms — the most used project, and the one that already ran our experiment

Thirteen stars, which is why the original brief missed it, but npm version 1.24.2, 58 releases, 515 weekly downloads, and 20,291 lines of TypeScript. By actual usage it is the largest thing in this space, and star count is a terrible proxy here.

Its README documents, in plain language, the exact experiment we would otherwise have repeated:

> The project began as a filesystem-based bus. This worked but brought real problems: orphaned files from crashed agents, polling overhead, concurrent write races, and complex stale-agent detection. The key insight was that each MCP server instance is already a running process. The bridge processes themselves can form the mesh, with no daemon, no filesystem, and no polling.

They tried the filesystem mailbox and abandoned it publicly, with reasons. That single paragraph is worth more than most of the code in this survey, and it is the direct reason the mailbox skill in our own pull request was closed.

It is also a name collision. They own `agent-comms` on npm.

### getbeb/beb — zero stars, best architecture in the field

Thirty-six hours old when I read it. 3,726 lines of production code, 2,304 of tests, 75 tests, **one direct dependency**, a full CI gate with formatting, vet, race detection, linting and four-target cross-compilation, and fifteen tagged releases with checksummed binaries. Star count is worthless as a signal here.

Its central idea is the best single idea in the entire research set: **identity comes from the channel, never from the message.**

An SSH `authorized_keys` line binds one public key to one node name using a forced command. The server refuses to start without a node name, and that name comes from the key line, so a client cannot assert it. The client asks who it is and a mismatch is fatal, non-retryable, and re-checked on every reconnect.

The consequence is that **sshd is the daemon.** The serve command reads standard input to end-of-file and exits. Zero resident processes. Zero new listening ports. Zero new credential store. NAT traversal, jump hosts, and known-hosts handling all inherited free from the user's existing SSH config. This is the lowest-operational-cost design in the field by a wide margin.

Four more ideas worth taking:

*Kernel-enforced single reader.* An exclusive non-blocking file lock on the cursor, with the process ID written inside so a refusal can name the holder. The kernel releases it on process death, so there is no stale-lock garbage collection. Takeover is a cooperative marker file tested by presence, not modification time, because some filesystems round timestamps to the second. The reasoning in the source comment is the sharpest in the corpus: two readers draining one inbox produce **no error signal at all** — mail is gone, the cursor moved, nothing failed. That must be made impossible, not diagnosable.

*Notify is not deliver.* The notify path reports that mail exists and never advances the cursor. A lost nudge costs a nudge, not a message.

*One greppable line per message.* Sequence, timestamp, sender, body, capped at 512 bytes, with the newline as the frame. Torn writes become trivially detectable and reading stops at the first unparseable line, so a cursor can never advance past corruption.

*It refuses to send to a non-member.* Creating an inbox on demand, in the author's words, would acknowledge a message into a mailbox nobody reads, which is mail loss reported as success.

Durability is real: write, then fsync, then acknowledge. Injection defense is real: it rejects C0 control characters, delete, **and the C1 range**, specifically calling out the bare control-sequence-introducer character. Names are restricted to a safe character class, which makes path traversal unrepresentable rather than merely checked.

Its limits are real too. Reads parse whole segments, and listing reads every topic's full log to count. Sends serialize workspace-wide on one global lock. Authorization is binary roster membership. No content trust.

### hrubymar10/aimebu — the stronger product, the weaker architecture

27,488 lines of production code, 24,428 of tests, 644 tests plus three fuzz targets, and **no CI directory at all.** None of those tests run anywhere.

It has the best collaboration model in the field. Presence is derived from three independent signals: an open long-poll or websocket is definitive liveness regardless of timestamps; a 45-second session heartbeat keeps a five-minute model turn from looking dead; and last-seen age is only the fallback. Presence transitions are published into the room as system messages rather than hidden in a sidebar. Humans are first-class rows in the same table as agents, exempt from AI read-expiry, and an attention flag force-subscribes every registered human.

Two disqualifying flaws:

**No authentication whatsoever.** The sender field is entirely client-asserted. The only control is an IP address allowlist. Any local process can impersonate any agent, read every direct message, and issue a delete-all.

**It is actively hostile to offline agents.** After thirty minutes idle an agent is deleted, which removes it from every room and drops its roles. Deleting the agent deletes its read cursor, because the cursor lives only on the agent record. On return, the cursor is initialized to the head minus five. **An agent offline for thirty-one minutes that missed two hundred messages comes back and sees five.**

The verdict that matters: aimebu is the stronger product, beb is the stronger architecture. You can add rooms to a secure bus. You cannot retrofit identity into a bus where every message is self-attested.

### The terminal family, and its real ceiling

`elijahmuraoka/skills` is the most engineered thing in the survey: 6,440 lines of source, 4,668 of tests, five adapters, twenty-nine typed error codes. Its four-tier resolver — live REPL, then dormant session resume, then cold spawn, then a typed not-found error — is built on a genuinely correct principle it calls the single-writer invariant: the running agent stays the only writer to its own conversation state. That principle generalizes to any transport.

Its injection technique is careful: load a uniquely-named buffer via standard input, paste it, then send the return key, so concurrent calls do not clobber a shared buffer.

But there is no correlation identifier anywhere in the codebase. "Response" is a screen-capture diff after the display has been byte-stable for a few seconds. Its loop protection is a natural-language paragraph asking the receiving model to please propagate a depth counter, and its own documentation concedes this catches honest loops, not adversaries. One of its error codes is defined and never thrown. And its destination lock is a module-scoped in-process map, which provides zero protection across processes — the normal case.

`ShawnPana/smux` is one 403-line shell script. Its addressing is tmux-native — a pane option rather than a registry file, so it cannot go stale relative to reality. Its return-address header converts blocking screen-scraping into asynchronous message passing with a reply-to field, in about three lines of shell, and that is genuinely elegant. But its read guard is a bare touch on a predictable world-writable temporary path keyed on target only, so one sender's read satisfies another sender's write.

And there is a field report in an unmerged pull request on that project that we should treat as the canonical warning for this whole family:

> Type, message, and keys could reach any pane on the server; scope was pure convention. With dozens of sessions running, one stale identifier was enough to deliver a message into an unrelated project's pane.

## Harness compatibility

Nine harnesses, and MCP reaches eight of them.

| Harness | Stars | MCP | Note |
|---|---|---|---|
| Claude Code | — | Yes | Plus plugins, skills, hooks |
| sst/opencode | 195,418 | Yes | Largest by stars; absent from the original brief |
| google-gemini/gemini-cli | 106,430 | Yes | Config key differs |
| openai/codex | 104,947 | Yes | Plus a notify handler |
| cline/cline | 65,921 | Yes | |
| block/goose | 52,609 | Yes | MCP-native; every extension is an MCP server |
| charmbracelet/crush | 27,220 | Yes | Absent from the original brief |
| Cursor | — | Yes | |
| Aider-AI/aider | 48,081 | Partial | Last push May 2026; the MCP holdout |

The conclusion held at the time and is now qualified: MCP is universal **among harnesses**. It is not universal one layer down. See `herdr` in Part III.

## Licensing, which turned out to be strategically decisive

This is not paperwork. It determines what we can build.

`mcp_agent_mail` is MIT plus a rider. The rider names Anthropic, PBC as an explicit Restricted Party. It forbids hosting, making available, or otherwise permitting access to the software or any derivative work to a Restricted Party. It extends the definition of "use" to incorporating the software into any evaluation harness. And it requires the rider to propagate unmodified into derivatives.

The maintainer clarified in an issue that end users running it alongside Claude Code are fine. That blesses **use**. It does not bless **redistribution**, and an issue comment is not a license amendment. Publishing a derivative into a Claude Code marketplace is precisely the fact pattern the rider was drafted to catch.

Our General Counsel seat went further and I think is right: a license that names a specific company as a restricted party and forbids fields of endeavor fails the Open Source Definition. It is a proprietary license wearing MIT's clothes, and we should stop calling it MIT in our own records, because mischaracterizing a license in your own documents is the kind of thing that looks like knowledge in hindsight.

`elijahmuraoka/skills` has no license field, no license file, and is marked private. That means all rights reserved. We may read it. We may not copy from it.

`ExaDev/agent-comms` says MIT on npm but has no license file in the repository. Ambiguous, and not usable without the author fixing it.

`beb`, `smux`, `fleetpost`, `aimebu`, and `agent-message-queue` are all MIT and freely reusable with attribution. A2A and `herdr` are Apache 2.0. `synapse-messenger` is AGPL and should stay far away from a marketplace artifact.

**The ruling: clean-room with respect to the two strongest implementations.** Read them, learn the ideas, copy nothing. Ideas and failure classes are facts and are free; expression is not.

---

# Part III: The estate blind spot

This is the part you caused, and it is the most consequential section in the document.

## claude-code-slack-channel

Apache 2.0. Version 0.12.0. OpenSSF Scorecard badge. CI green. Root-level TypeScript is 16,301 lines of production code against 19,631 lines of tests — a test-to-source ratio better than most things in this survey.

Verified at code level, not from the README:

**A hash-chained, Ed25519-signed audit journal.** Each event's hash is the SHA-256 of the previous hash concatenated with the canonicalized event, using RFC 8785 JSON canonicalization, anchored at a genesis value. The framing fields are writer-assigned, so callers structurally cannot forge them. It is offline-verifiable. The signing key is loaded by spawning the operator's own SOPS binary and piping in-process — it is never written to disk, not even to shared memory. That key handling is better than most commercial signing paths.

**A monotonic fencing token on session turns.** The source comment says it plainly: exactly one owner holds a live lease, and the monotonic token fences writes so a resurrected owner's stale token no longer matches. That is the canonical answer to the lease-expiry problem and it is **strictly stronger than anything in the external survey.** Recall that the leading incumbent grants conflicting exclusive leases outright.

**Deterministic multi-agent loop control**, including ring loops. There is a per-bot check for the simple back-and-forth case and a channel-wide circuit breaker explicitly documented as catching N-cycle rings that stay under the per-bot cap. Compare the most-engineered external project, whose loop control is a paragraph of English asking the model to behave.

**A tiered, declarative policy engine on every tool call**, with identity-aware permission gates, nonce-based human-in-the-loop approval, and cross-channel operator approval.

**Test posture that exceeds every project in the survey except the incumbent**: 19,631 lines in a single test file, plus behavior-driven feature files covering the audit chain verifier, a file exfiltration guard, the inbound gate, the outbound reply filter, and policy evaluation, plus property tests and a canonicalization interoperability corpus.

**Slack as the human surface**, over Socket Mode, which is outbound-only and needs no public URL, so it works behind NAT.

## agent-governance-plane

Apache 2.0. It runs an agent inside a sandbox, gates every tool call through a policy engine and, where a rule requires, a human approval, and writes each decision to the same signed hash-chained journal.

The decisive property is that it is **multi-harness by contract**: Claude Code and Codex both run through one adapter, one policy gate, and one signed journal with no harness-specific code path, and this is asserted by a conformance test. It is contract-first with six frozen contracts. It fails closed. And it holds no model credentials — it gates the agent rather than impersonating it.

The research document had an open question asking where lease enforcement gets teeth, since pre-commit hooks are bypassable by design. **AGP is a working answer to that question that the research did not know existed.**

## ACP — a third protocol nobody in the research mentioned

The research considered exactly two protocols, MCP and A2A. The Slack channel repo already ships an adapter for the Agent Client Protocol — JSON-RPC 2.0, adopted by Zed, with open issues tracking the same primitive in Google's agent development kit and in Zed itself.

The adapter is quarantined by design. Its header comment says it is the only place in the codebase where ACP terminology appears, and it maps ACP verbs onto the existing internal vocabulary without changing it. That is exactly the "conform, do not author" posture the research recommended — already implemented, for a protocol the research does not name.

## herdr — the runtime the research never saw

26,413 stars. 1,861 forks. Apache 2.0. Rust. Created in March 2026, pushed the day I looked. Its own description: *the runtime your coding agents live on.* Its topics are multiplexer, terminal-multiplexer, tmux, tui, workspace-manager, claude-code, codex, coding-agents.

It has an ecosystem: a code-review sidebar at 372 stars, a file viewer at 365, a remote driver at 208, and a session mirror at 113 that drives remote sessions over SSH.

Two consequences, and both matter.

**It is not a row in the harness table. It is a layer beneath it.** It is a tmux successor that Claude Code and Codex run *inside*. Our entire analysis of the terminal-injection family was conducted against tmux and a 403-line shell script, while the 26,000-star Rust runtime that is displacing tmux for coding agents went unexamined. If the doorbell adapter targets tmux, it is targeting the receding substrate.

**It is a counterexample to the MCP thesis.** It shows zero MCP, ACP, or A2A references in its README and zero MCP hits in a repository code search. "MCP is the universal surface" holds across harnesses and fails at the runtime layer where the largest adjacent project lives.

## What the blind spot changes

The research concluded that three capability columns were unclaimed by everyone: leases that actually deny, injection-framed reads, and unspoofable identity combined with durable offline delivery. It then recommended building a new core clean-room, on the reasoning that the two most complete implementations are legally radioactive.

That reasoning is intact. Its conclusion no longer follows, because a third complete implementation exists that is Apache 2.0 and ours.

So the live question stopped being *what do we build* and became:

> **Is the fabric a new core, or a transport-and-routing layer over the existing policy, journal, and fencing-lease kernel, with AGP as the enforcement gate, and ACP alongside MCP and A2A?**

Arguments for extraction: the hardest capabilities exist; Apache 2.0 and ours means zero licensing friction; and the repository's own README describes its kernel as the substrate that AGP reimplements, so extraction is an anticipated direction rather than a violation of its design.

Arguments against: it is Slack-coupled, which drags a cloud vendor and a rate limiter into a system whose pitch is local-first. It is a Research Preview requiring a specific Claude Code version and a browser login, with API-key-only authentication explicitly not working — a hard adoption ceiling. And its fencing lease is in-memory today, with the durable token deferred.

---

# Part IV: The business council

## Why a council

I convened the seven-seat adversarial executive council: Chief Technology Officer, General Counsel, Chief Marketing Officer, Chief Financial Officer, Chief Standards Officer, Chief Information Security Officer, and VP of Developer Relations. Each argues from its own value system and is explicitly instructed not to seek consensus.

The reason is that the failure modes here are asymmetric. A wrong identity model gets written into an append-only signed journal and cannot be corrected. A wrong name propagates into a marketplace with 2,000 stars and 300 forks and cannot be recalled. A wrong licensing ruling cannot be proven clean after the fact.

## What it found first: my research was wrong in four places

Three seats independently re-read the cited source rather than accepting my summary. I re-verified every finding before entering it into the record.

**One. The injection-defense claim was false.** I wrote that the Slack channel repo strips C0 and C1 control characters from untrusted input, and cited a line. The function at that line strips C0 and delete only. There is no C1 handling anywhere in the repository — a search for the range returns zero hits — so the bare control-sequence-introducer character, the one thing `beb` specifically defends against, passes through everywhere. Worse, the function is applied at exactly two call sites, both on Slack **display names**, capped at 64 characters. **No message body is sanitized anywhere in the codebase.**

I had trusted a code comment that says "C0/C1" instead of reading the regular expression directly beside it. This is the exact failure I criticized the incumbent for: shipping sanitization in the web viewer while claiming injection defense on the agent path.

**Two. Ring-loop control was reported as a gap and is actually implemented.** I under-claimed. The channel-wide circuit breaker exists and its comment explicitly names the N-cycle case.

**Three. The line count counted tests as production code**, inflating the figure by roughly double.

**Four, and this one was not in my document at all: a live security hole in our own open pull request.** Covered in Part VII.

The pattern the CTO seat named, and which I have adopted as a binding rule:

> A capability claim is valid only when it names a test that fails if the capability is deleted.

## The votes

**On the gating question — new core or extraction?** Six of seven for a narrow extraction plus a clean build of everything else. Zero votes for a full clean-room rebuild. Zero for layering over the existing system wholesale. One dissent: the CFO seat argued build nothing yet.

The three seats that named specific modules converged independently, which I found more persuasive than the tally. The CTO named journal, crypto, and policy. The CFO named journal, crypto, and the rate limiter. The CISO named journal, crypto, and the key loader. **The intersection is journal and crypto, unanimous among everyone who named anything.**

The CFO and CTO also independently measured the coupling, and both found the kernel far more separable than my document implied: the crypto module has zero Slack references, the journal has four incidental ones, and the Slack mass is concentrated in three files totaling roughly 8,000 lines with 341 references that nobody proposes touching.

**On licensing:** seven of seven, the clean-room ruling holds. Two seats say it is understated.

**On the mesh:** seven of seven, no mesh in version one. This was the point my document flagged as the sharpest place to challenge me, and the council unanimously upheld the conclusion while rejecting my reasoning. The CTO's correction: citing ExaDev against durable queues confuses a bad implementation with a bad category. ExaDev abandoned a *naive* file bus. `beb` solves the same substrate correctly.

**On identity:** seven of seven, non-negotiable. Three seats named it the single most costly decision to recover from.

**On the pull request:** seven of seven that the mailbox skill must not ship. Five of seven for merging the rest minus that skill. One for closing entirely. One for holding.

**On protocols:** seven of seven that MCP is primary. Five of seven to admit ACP as a quarantined adapter and to demote A2A to an off-by-default client. Six of seven that `herdr` is an integration adapter for later, not a version-one dependency.

## The dissents worth preserving

I am keeping these verbatim because averaging them away would destroy the value of having run the exercise.

**The CFO, on whether this is a market at all:**

> The entire field's adoption ceiling is 515 weekly downloads, which is the most-used project in the category. The incumbent has 2,078 stars, zero of fifty-three pull requests merged, and a bus factor of one — stars measuring interest, not use. Seven projects, aggregate demonstrated usage under a thousand weekly installs. Meanwhile our existing marketplace does 45,000 downloads on plugins we already maintain. This is a builders' market: engineers building for engineers building agents, with the tooling outnumbering the users.

Its gate: three unsolicited requests from distinct users, or one paying client with the requirement in scope.

**The VP of Developer Relations, on the adoption ceiling:**

> Count the accounts a Saturday developer must create before message one: with `beb`, zero. With `smux`, zero. With the Slack-coupled substrate, at least one, plus workspace-admin rights they may not have at their day job. That is not a friction difference, it is a population difference — it excludes every developer whose employer controls the Slack tenant, which is most of them.

**The General Counsel, on the thing that cannot be undone:**

> Contamination is the only decision here that cannot be proven clean after the fact. If we ship and someone alleges we copied, the burden shifts on access plus substantial similarity — and we have already created, dated, and filed the access exhibit ourselves, at line-number granularity. Every other decision has an undo. A contamination allegation has no undo, because you cannot prove a negative about what an engineer had in their head. You can only prove process.

That is also why the GC landed on extraction: the existing repository's git history predates the survey. It is the strongest independent-creation evidence we will ever have, and a clean-room rebuild throws it away.

**The Chief Marketing Officer, on the name:**

> A name is not recoverable. It lands in npm, in the plugin manifest, in the marketplace catalog, in the install slug, in third-party blog posts, in hundreds of forks' READMEs, and in the search index — and it becomes an API. This organization has the definitive proof already: our own install slug is documented as unrenameable because renaming it is a breaking API change.

---

# Part V: The engineering canon

## Why a second panel

The council is seven business value-systems. It adjudicated licensing, positioning, scope, and cost well. But a durable-messaging-with-identity substrate is a distributed-systems artifact, and none of those seats is a distributed-systems seat. That was a real gap in what I first handed you, and you caught it when you asked what the thinker canons said.

I ran six named engineering reviewers independently against the architecture and the council's rulings: Kleppmann on consistency and append-only substrates, Lamport on ordering and coordination, Armstrong on failure modes and supervision, Hickey on data model and simple-versus-easy, Thompson on composability and minimalism, and Beck on test discipline and feedback loops.

**They found five more defects that neither I nor the business council caught.**

## Defect one: the journal and the queue are two stores with no reconciliation invariant

My document makes the durable queue the system of record and separately praises the hash-chained journal. **Neither document says whether message-delivery events are written into the journal at all, or live only in the queue.**

If they are siblings, we inherit the dual-write problem the incumbent papers over with a compensating delete-and-re-raise — a crude compensation that leaves a torn window if the process dies between the delete and the re-raise propagating.

Kleppmann's fix is one sentence: **do not compensate, derive.** The mutable view — queue, cursors, delivery state — should be a deterministic materialization of the append-only log, not a second independently-written store that needs reconciliation after the fact.

He rates this **above identity** as the most costly thing to get wrong, and his reasoning is worth quoting:

> A wrong identity model is at least a known, singular error with a known fix. Two independently-written stores with no declared reconciliation invariant is the kind of gap that produces the exact bug class this whole review exists to catch: everything looks fine for months, until a crash lands in the one-in-ten-thousand window where they disagree, and there is no protocol-level answer for "the log says delivered, the queue says pending, which one is right."

Notably, the existing code already states the correct split in a source comment: the on-disk session file stays the source of truth, and the lease fences writes rather than replacing the file.

## Defect two: the delivery-acknowledgement boundary is undefined

Armstrong's finding, and it is the one that most directly threatens the product's central promise.

The design says fsync before acknowledge, and kernel-released locks. **It never says whether the cursor advances on *read* or on *consumer-acknowledgement-of-processing*.**

> If cursor-advance is synchronous with the read call returning bytes, this is at-most-once delivery wearing at-least-once clothing. A reading process that crashes after the read but before it actually uses the message has a permanently vanished message with the cursor already past it — and that produces no error signal at all, the exact failure class the design elsewhere refuses to accept.

The promise we would market is that a message sent to a sleeping agent still arrives. This gap makes that a lie under precisely the crash the design exists to survive. No row in my test plan covers it. Armstrong rates it most costly.

## Defect three: the fencing token needs a durable check, not just a durable counter

The council bound "durable monotonic fencing token" as a version-one blocker. Lamport's sharpening is that the phrase is doing double duty for two different things.

> If this ships with a durable counter but an in-memory acceptance check, the system will pass every test that exercises "the old holder crashed cleanly" and fail exactly once, at scale, when the storage layer itself restarts mid-contention — observable only in production, indistinguishable from routine flakiness until two writes to the same resource silently interleave.

The minimal correct construction: persist the counter, increment via compare-and-swap inside an immediate transaction, fsync before telling the new holder it won, and have the storage layer reject any token below the maximum accepted for that resource, where that maximum is read from durable state on every check. This is the pattern etcd, ZooKeeper, and Raft all converged on.

Kleppmann independently confirmed the underlying flaw from source: the existing implementation mints from a **process-monotonic** counter, which resets on restart, so a restarted supervisor can mint a token lower than or equal to one already granted. Split-brain by omission rather than by bug.

Lamport also flagged that the thirty-second heartbeat window is being asked to do two jobs — deciding when a challenger may attempt takeover, which is a liveness tuning knob, and guaranteeing safety, which it must never do. A timeout is a synchrony assumption wearing a correctness costume.

## Defect four: cross-machine ordering is undefined, and the lock breaks on network filesystems

File locks are advisory, single-host, and kernel-scoped. They give a genuine total order on one machine. The roadmap item for cross-machine operation over SSH breaks that guarantee the moment there is more than one serialization point, and the identifier scheme gives approximate wall-clock ordering, not happens-before.

Kleppmann on the tradeoff we did not name:

> "The readers are LLMs, keep it greppable" is a legitimate reason to keep the serialization format flat. It is not a legitimate reason to skip a causality primitive, because those are orthogonal axes. A hybrid-logical-clock component is still one small token on one greppable line.

Separately: file locking over network filesystems has decades of inconsistent-to-absent support, so two readers on two clients can each believe they hold an exclusive lock. That is the "no error signal at all" failure the design exists to prevent, silently reintroduced by deployment topology rather than by code.

## Defect five: the authentication-method field is a closed enum

Hickey, on the identity envelope the council designed:

> A field whose value tells a consumer how to interpret another field is a discriminated union wearing a string costume, and a closed enum on a signed, unversioned envelope means every new auth mechanism is a distributed migration — every verifier on every machine has to learn the new tag simultaneously or silently mis-trust messages tagged with it.

His fix: make it an open namespaced string and push the verification logic into a lookup table external to the envelope, versioned separately. The envelope stays dumb data.

Lamport added a sixth, smaller item: there is no no-duplicate-delivery invariant, and the resolver's live-push and enqueue paths are not mutually exclusive in time.

## Where the canon contradicts the business council

| Topic | Business council | Engineering canon | Resolution |
|---|---|---|---|
| Most costly decision | Identity envelope, three of seven | Split: journal-queue reconciliation, delivery-ack boundary, fencing check durability, identity envelope | Identity keeps the plurality across both panels; three new defects join it in the unrecoverable class |
| Mesh in version one | Seven of seven against | Agree, reasoning rejected | Conclusion stands, rationale replaced |
| Protocol surfaces | ACP admitted five of seven | Thompson and Hickey go further than the CFO: cut ACP, A2A, herdr, telemetry, discovery, delegation from version zero entirely | Canon strengthens the CFO dissent |
| Formal methods | Not considered | Specify only the resolver, lease, and cursor interleaving; explicitly refuse ceremony elsewhere | Adopt the narrow scope |
| Build versus probe | CFO dissent, one of seven | Beck sequences it regardless of who wins | See Part VIII |

Two things stand out. Thompson and Hickey both went **further than our most conservative business seat** on scope. And Lamport, who could have recommended formal specification everywhere, explicitly refused:

> The wire framing is a parser property, checkable by fuzzing, not a coordination problem. Control-character stripping is a pure function over a string — property-based testing is the right tool. And "notify never advances the cursor" is best enforced by making the illegal state unrepresentable in the type system, which is more correct than a proof of a rule the type checker already makes vacuously true. Writing a spec for that would be ceremony; I do not do ceremony.

---

# Part VI: Your question about adversarial sub-agents

You asked, roughly: what if each agent in the system is itself composed of adversarial agents underneath — what could we do under the surface. You said you did not know what you were talking about. You were closer to something real than that suggests, and all six reviewers engaged it directly.

## Why the question is well-founded

It is not hypothetical. **The pattern demonstrably worked in this very engagement.** Seven adversarial business seats found four defects in a document I had marked verified with file-and-line citations. Six adversarial engineering reviewers then found five more in the same document plus the council's own rulings. A single careful pass — mine — missed all nine.

That is empirical evidence that adversarial composition catches a class of error that careful single-threaded work does not.

## The convergent answer: right instinct, wrong placement

All six landed in the same place. It belongs *inside* an agent, below the addressing boundary, or *outside* the fabric as a user of it. **Never in the transport.**

Thompson's version is the cleanest, and it uses this engagement as its own proof:

> The four defects the council found were found by seats independently re-reading source and cross-checking each other, using nothing but plain reading and disagreement. Zero fabric primitives were required. If the fabric grows consensus, voting, or adversarial-turn primitives on the wire, that is the exact same category of creep as leases and delegation lifecycle — someone's application concern leaking into the substrate because it happened once, near the design. Mail moves a byte-capped line from a name to a name. Whether five sub-agents argued before one of them called send is not the fabric's business, any more than sendmail needs to know whether the human writing the letter argued with themselves first.

Kleppmann reached the same conclusion by a different route: a composite agent's internal disagreement is analogous to a consensus cluster's internal leader election. The cluster speaks to clients with one voice through a stable principal; the deliberation that produced that voice is not the client protocol's business. Channel-derived identity already gives us this for free.

Hickey framed it as a data-model question: a message stays a **value** no matter how many disagreeing sub-agents produced it. It goes wrong the instant a consumer's routing or the substrate's delivery behavior branches on whether dissent is present — that smuggles judgment into the transport.

## But there is exactly one real substrate consequence

Kleppmann and Lamport arrived at it independently, from opposite directions, and Lamport's version is the sharp one:

> Channel-derived identity proves *who* signed, never *whether the signer's internal process actually decided* what it signed. A composite that authenticates cleanly can still emit a message its own quorum never approved — a tamper-evident record of an internal fabrication.

That is a genuinely new hole. Our whole identity story is that the sender cannot be forged. It is silent on whether the sender's own internal process actually sanctioned the content. For a composite agent, those come apart.

The fix is small and must happen at the beginning: reserve a decision-provenance field in the envelope from the first commit — unanimous, quorum of N, designated writer with veto, or unspecified — even if it is null in version one. Kleppmann's parallel framing is that if contestedness should be first-class evidence, a dissent record is simply a sibling event in the same hash chain, linked by correlation identifier and pointing at the contested event by its content hash. No Byzantine agreement, no voting protocol, no new primitive.

The reason it cannot wait is the same reason the identity slots cannot wait: **you cannot add a field to a signed append-only structure later without invalidating every prior signature.**

## And Beck reframed the half you were actually reaching for

> It is a testing strategy, not an architecture, and conflating the two is the risk. Right now it worked because it was novel and high-stakes, with a human chair re-verifying every finding. Left as a one-off ceremony, the next research document gets written by one voice again and the next defect ships quiet.

His cheap routine version is not "convene seven seats." It is: **require independent re-verification of every verified citation by someone who did not write it.** Even a single adversarial reviewer whose only job is to re-read the cited line and answer whether the code matches the English sentence, yes or no.

That single check would have caught the control-character error, which is the most embarrassing item in this entire body of work.

**Summary of the answer to your question.** The metaphor is sound and the placement was wrong. As architecture, it stays out of the transport. As practice, it is cheap and should be routine. And it leaves exactly one mark on the substrate: a reserved slot, decided now, that costs nothing and cannot be added later.

---

# Part VII: What actually shipped

## The security bug

This is the finding I am least comfortable about, because a previous commit on that branch claimed to have closed exactly this class of hole.

The A2A client plugin routes every outbound request through a network guard. The guard has two fail-closed rules: refuse private, loopback, link-local, and carrier-grade-NAT destinations unless explicitly permitted; and attach a credential only to a host the operator has explicitly nominated.

The guard validated the pre-flight URL and then handed the request to the runtime's fetch, which follows redirects by default. **A runtime-followed redirect never re-enters the guard.** So a permitted public host answering with a redirect to the cloud metadata address walked straight around a check that explicitly blocks that address — the code even names it in a comment.

Worse: the credential header was attached before the fetch. So the redirect could carry the operator's bearer token to the redirect target. That is not just server-side request forgery, it is credential exfiltration, and it directly contradicts the module's own stated posture.

**The fix.** Redirects are now followed manually. Every hop re-enters the destination check. The credential is dropped and re-evaluated per hop against that hop's host. Non-HTTP schemes are refused. The chain is capped. Status codes that should degrade to a bodyless GET do so, matching standard fetch semantics.

**The verification, and this is the part that matters.** Eight regression tests pin the behavior, and I mutation-checked them: I flipped the redirect mode back to the broken value and confirmed the suite goes red. That is the binding rule applied to itself — the tests fail if the capability is deleted. Seventy-five of seventy-five pass, type-check clean, lint clean.

One residual is documented rather than papered over: a DNS rebind between the pre-flight resolve and the connect is not covered. Closing it needs a pinned-address dialer that the SDK's fetch seam does not expose. I did not claim it was fixed.

## Pull request 1169: closed

Per your call. I recorded the reasoning on the closed PR rather than letting it vanish: the mailbox skill repeats a design the most-used project in the space publicly abandoned with reasons; the strategy question behind the pack is open and demand-gated; and holding a bundled PR against an undated decision accrues rot on finished code.

The other five skills remain in that branch's history and can be resurrected individually.

## Pull request 1170: open and green

The A2A client server, split out on its own merits with the security fix and its tests. **All three required checks pass. Zero failures.**

Getting there took four fix-up rounds, and one of them was self-inflicted in an instructive way. I added the catalog entry by loading the catalog JSON in Python, appending, sorting, and re-dumping. That reformatted the entire file — 1,610 lines of churn for a one-entry addition — and a repository guard specifically built to catch whole-file reformats rejected it. The catalog's multi-line layout is load-bearing. I redid it as a surgical text splice: fourteen lines. The guard was right and I was careless.

## Documentation

Three documents are on main: the research with an append-only amendment log recording the four falsifications; the council decision record with verbatim seat positions and vote tallies; and the engineering canon review. Verbatim positions from both panels — about 170KB — are preserved outside git.

---

# Part VIII: The decision surface

Six decisions are yours. I have deliberately not made them. For each, here is the honest case on every side.

## Decision one: build, extract, or probe first

**The case for narrow extraction.** Six of seven business seats. The hardest cryptographic work exists and is tested. Apache 2.0 and ours means no licensing friction in a field where the two best implementations are unusable. The git history predates the survey, which is the strongest independent-creation evidence available. Coupling measurements from two independent seats show the kernel is far more separable than feared.

**The case against.** The Slack coupling is in the authentication model, not in configuration. The Research Preview gating — a specific harness version plus a browser login, with API keys explicitly not working — is an adoption ceiling for a marketplace artifact. The fencing lease is in-memory today. And extraction from a codebase whose 19,631-line test file is built around the Slack server means the kernel extracts but its proof of correctness does not — whoever pulls the journal out inherits security-critical crypto with no surviving test suite. Nobody had priced that before the CFO seat did.

**The case for building nothing yet.** The field's aggregate demonstrated demand is roughly 515 weekly downloads across seven projects, against 45,000 on the plugins we already maintain. The incumbent has 2,078 stars and zero merged pull requests — 2,078 people who found it interesting and none who shipped against it. There is no inbound request, no client ask, no marketplace issue. And the extraction is a cheap option that does not expire; exercising it early converts a free option into a permanent maintenance bill for one person.

**My read.** The CFO is not being conservative, it is being correct about sequencing, and Beck showed why the apparent conflict is false. See the resolution below.

## Decision two: the demand gate

If you accept a gate, the CFO's proposal is three unsolicited requests from distinct users, or one paying client with the requirement in scope, instrumented cheaply rather than assumed.

The counter-argument, from the CMO seat, is that some categories have to be created rather than discovered, and that the tagline you operate under is explicitly about creating industries that do not exist. That is a real tension and it is yours to resolve, not mine.

## Decision three: the mailbox skill and the rest of the pack

Already resolved by your call to close. Five skills sit in history. If any come back, the A2A protocol description and the topology and failure-triage skills are the ones with standalone value.

## Decision four: the agent card skill

The Chief Standards Officer raised a motion no other seat supported or opposed, and I think it deserves your attention because it is the only unresolved item from the council:

> Shipping a skill that imitates an identity standard is the highest-credibility-cost artifact in the whole cluster. Identity formats are the touchiest surface any working group owns; a marketplace pack that approximates one, unblessed, is how you get a permanent bad first impression with the exact group we would later need. Zero upside, permanent downside.

## Decision five: the name

`agent-comms` is owned on npm by a live package doing 515 weekly downloads. There is no legal bar — the term is descriptive and almost certainly unregistrable — but publishing under a colliding name fragments search for everyone and reads as careless from a marketplace whose entire pitch is being the clean, governed option.

Both the CMO and DevRel seats independently called the name the most costly thing to recover from, and this organization already has the proof: our own install slug is documented as permanently unrenameable.

Recommendation: cede it without drama. Category becomes something neutral. I will run a clearance sweep across npm, GitHub, and trademark before proposing anything, and nothing gets named without you.

## Decision six: protocol surfaces

The council admitted ACP as a quarantined adapter, demoted A2A to an off-by-default client, and pushed `herdr` to a later integration.

Both Thompson and Hickey went further than the CFO and would cut all of them from version zero — keeping the lint-enforced boundary as a file that exists and is empty. The Chief Standards Officer's reframing is the one I find most useful, because it replaces star-counting with a better metric:

> Rank by traffic actually flowing, not by star count. A2A has 25,262 stars and zero local packets. herdr has 26,413 stars and no protocol at all. MCP is unglamorous and carries everything.

## The sequencing that dissolves decision one

This is the most useful single idea to come out of either panel, and it is Beck's.

The CFO's "build nothing yet" and the near-unanimous "the identity envelope is the one unretrofittable thing" look opposed. They are not:

> **Ship the probe first — and make the probe exercise the envelope shape.**

Cheap to be wrong about mesh versus queue. Catastrophic to be wrong about the envelope. A roughly two-hundred-line probe that sends and receives while carrying the reserved identity fields tests the only decision that cannot be reversed, costs almost nothing, satisfies the demand gate, and is compatible with every position on the table — including "extract now," which also benefits from validating demand before the boundary tooling gets built.

Thompson's scope floor pairs with it: **three verbs — send, receive, acknowledge.** If you cannot explain a fourth verb in one sentence without the word "future," cut it.

---

# Part IX: Risks, honestly stated

**The one that worries me most is not technical.** It is that this document, and the two before it, are extremely well-researched artifacts about a product for which there is no demonstrated demand. Nine defects found is a good outcome for a process; it is also nine defects found in something nobody has asked us to build. The CFO seat's closing line deserves to sit in front of you: every seat was arguing about how to build a thing nobody has asked for.

**Second: the estate has two live compliance gaps that this work surfaced incidentally**, and they exist whether or not you build anything. There is no export-control self-classification notice for a repository that already ships signing cryptography publicly — a one-time filing that costs an email. And the npm package name does not match the repository name, which will confuse anyone building on it.

**Third: the misleading comment is still in the code.** The line claiming C0/C1 sits over a C0-only regular expression. It caused one documented error already. Beck's guidance is right — do not just fix the comment, write the test that should have existed, watch it fail, then decide honestly whether to implement the C1 handling or narrow the promise.

**Fourth: if we do build, four defects are in the unrecoverable class**, not the annoying class: the journal-queue relationship, the delivery-acknowledgement boundary, the fencing check durability, and the envelope shape. All four must be decided before the first durable write, because all four are written into append-only storage.

**Fifth, and this is a risk about me:** four of the nine defects were in claims I marked verified. The corrective is in place — the claim rule, and Beck's independent re-verification pass — but you should calibrate accordingly. My citations were accurate; my inferences from them were not. That is a specific and correctable failure mode, and it is not the same as sloppiness, but it is not nothing either.

---

# Part X: What I would do

You asked where I am coming from, so here it is plainly, in order.

**One, this week, regardless of the strategy call.** Fix the misleading comment properly, with the test that should have existed. File the export-control notice. Fix the package-name mismatch. These are hours, not days, and they are true regardless of what you decide about the fabric.

**Two, the probe.** Roughly two hundred lines. Three verbs. It carries the four reserved identity fields plus the decision-provenance slot, and it does nothing else. No mesh, no leases, no protocol adapters, no telemetry. Its only job is to answer two questions at once: does the envelope shape survive contact with reality, and does anyone want this. Filmed, fresh machine, no accounts, under ten minutes.

**Three, the gate.** If the probe draws nothing in sixty days, that is the answer and it cost a weekend. If it draws real requests, the extraction is waiting and it has not decayed.

**Four, only then, extraction.** Journal and crypto — the intersection every seat that named modules agreed on. Clean-build the transport, queue, resolver, and durable lease. Enforce the import boundary in CI rather than by discipline. Re-audit line by line rather than trusting my shopping list.

**What I would not do:** build the mesh, ship a protocol adapter for anything with no local traffic, integrate a five-month-old runtime, or name anything before a clearance sweep.

---

# Appendix A: Evidence and verification

Every project named was confirmed via the GitHub API on 9 August 2026. Three external projects were cloned and read at source level. Licenses were read verbatim, not inferred from badges. MCP support was confirmed per harness. A2A's local adoption was tested by search and found to be zero.

Estate claims were verified against the working tree. Where a claim in my research contradicted the source, the source won and the document was amended in an append-only log rather than silently rewritten — on General Counsel's advice, since the research functions as an access exhibit for the clean-room ruling.

Every claim attributed to a panel seat in the filed records was independently re-verified by me against the cited source before entry, including all four that contradicted my own work. Two source claims were confirmed by more than one reviewer independently.

# Appendix B: Where everything lives

The research, the council decision record, and the engineering canon review are filed in the repository's document directory on main, numbered 712, 713, and 714. Verbatim positions from both panels are preserved outside git in the council session directory, alongside the structured session log and metadata. The work is tracked on a bead in the plugins repository with the full finding list recorded as notes.

The security fix and the A2A client server are in pull request 1170, green. Pull request 1169 is closed with its reasoning recorded on the thread.

# Appendix C: The nine defects, in one table

| # | Found by | What | Class |
|---|---|---|---|
| 1 | Business council | Injection-defense claim false: C0 and delete only, display names only, no message body path | My error, amended |
| 2 | Business council | Ring-loop control reported as a gap; it is implemented | My error, amended |
| 3 | Business council | Line count counted tests as production | My error, amended |
| 4 | Business council | Live redirect-bypass and credential egress in an open PR | Shipped fix |
| 5 | Canon | Journal and queue are two stores with no reconciliation invariant | Unrecoverable class |
| 6 | Canon | Delivery-acknowledgement boundary undefined | Unrecoverable class |
| 7 | Canon | Fencing token needs a durable check, not just a counter | Unrecoverable class |
| 8 | Canon | Cross-machine ordering undefined; lock unsafe on network filesystems | Design gap |
| 9 | Canon | Authentication-method field is a closed enum | Unrecoverable class |

# Appendix D: The rules adopted

**On claims.** A capability claim is valid only when it names a test that fails if the capability is deleted.

**On verification.** Every verified citation gets re-read by someone who did not write it, answering one question: does the code match the English sentence.

**On licensing.** Clean-room with respect to the two strongest implementations. Reader and implementer are different people. Neither repository is ever cloned inside the build tree. Failure classes, configuration settings, and published audit findings are facts and may be adopted freely.

**On public claims.** No statement about what a named competitor lacks. Ever. Publish our own pass-and-fail test matrix instead and let readers do the arithmetic.
