---
title: "Twenty-One Documents and a Weak Reject: Building a Research Corpus for a Novel Search Architecture"
description: "4000+ lines across 21 documents — invention disclosure, 6-paper research series, competitive landscape, probability assessment, and toolchain evaluation for a search architecture that eliminates precomputed embeddings. A simulated peer review returned Weak Reject. That was the most useful document of all."
date: "2026-04-13"
tags: ["architecture", "ai-engineering", "claude-code", "automation"]
featured: false
---
Every vector search system you have ever used assumes the same thing: that someone already ran every document through an embedding model and stored the results. For most workloads, that assumption is fine. For some, it is fatal.

Forensic seizure of 50TB of unstructured data. A due diligence data room that exists for 72 hours. Medical records under privacy regulations that prohibit persistent derived representations. In these scenarios, the hours required to build an embedding index *are* the problem. You need semantic search over raw text that was never preprocessed, and you need it in minutes, not days.

That is the problem space I spent a full day building a research corpus around. Seven commits. Twenty-one documents. Over 4,000 lines. The entire journey from invention disclosure to patent filing prep, captured in a single repository.

## The Shape of a Research Day

The day did not start with writing. It started with organizing.

The core idea had been kicking around for weeks as scattered notes — a search architecture where you compile the query into a lightweight scorer at query time and stream it over raw text, rather than precomputing document embeddings. No vector index. No preprocessing pipeline. Just a compiled operator and storage bandwidth.

Turning scattered notes into something filing-ready required a specific document structure. Here is what the final corpus looks like:

**Invention packet (7 documents):** The evolution from rough notes through a formal invention disclosure. Version history tracking how the concept sharpened. A prior-art appendix positioning the work against existing systems. An attorney handoff memo with filing strategy. An experiment plan.

**Research paper series (6 documents):** A proper academic treatment. Problem survey. Method paper with formal notation. Application domain analysis for "cold corpora" — data that arrives without an index and needs search immediately. Systems architecture covering both software runtime and a speculative hardware concept. Evaluation plan with seven experiment blocks, failure criteria, and exit conditions. A combined synthesis paper designed as the single entry point for anyone who only wants to read one thing.

**Analysis documents (5 documents):** Competitive landscape mapping 28 existing systems. Probability assessment with a 10-item risk register. Toolchain evaluation for the research tools needed to validate the work. A next-step decision document. A patent strengthening plan.

That is 18 documents with three more (the CLAUDE.md updates and editorial review) bringing the total to 21 committed artifacts.

## Writing a 6-Paper Series in Sequence

The research series followed a deliberate order. Each paper builds on the previous one, but each also stands alone.

Paper 1 (problem survey) established the cost model. How long does it actually take to embed a corpus? What are the real-world scenarios where that cost is prohibitive? This paper exists to convince a skeptic that the problem is worth solving.

Paper 2 (method) formalized the approach. The key question any reviewer will ask: can a lightweight scorer compiled at query time approximate the relevance judgments of a full embedding model? This paper frames that as a testable hypothesis with specific success criteria.

Paper 3 (cold corpora) defined the application domain. "Cold corpora" is the term for data where no preprocessing has occurred — forensic seizures, transient data rooms, privacy-constrained records. This paper argues that cold corpora are not edge cases. They are a growing category of search workload that existing architectures handle poorly.

Paper 4 (systems architecture) designed the runtime. How does the compiled scorer integrate with storage? What does the software pipeline look like? This paper also introduces a speculative hardware concept, carefully labeled as *target* rather than *proven*.

Paper 5 (evaluation plan) specified exactly how to test everything. Seven experiment blocks, each with success criteria, failure buckets, and exit conditions. The evaluation plan exists so that when GPU time becomes available, no design decisions remain. Just execution.

Paper 6 (combined synthesis) consolidated the entire series. This is the "read only one paper" version — the document you hand someone who needs the full picture in 20 minutes.

The discipline of writing each paper to stand alone while maintaining series coherence is hard. Cross-references have to be precise. Terminology must be consistent across 1,400 lines. Citation numbering needs to work both within individual papers and across the series.

### The Editorial Review

An editorial review pass caught a dozen inconsistencies that had crept in across the series. Arithmetic errors in FLOPs calculations — quoting the compute cost for 128-token sequences when the architecture actually targets 512-token windows, which changes the numbers substantially. A variable name collision where `k` meant both "top-k retrieval parameter" and something else in the same equation. A citation to an image retrieval system that was being treated as evidence for text retrieval performance.

These are the kinds of errors that survive multiple drafts because they are locally correct. The FLOPs number was right for 128 tokens. The variable name was defined earlier in the paper. The cited system does do retrieval. You only catch them when you read the entire corpus as a reviewer would — sequentially, checking each claim against its context.

The editorial commit touched every document in the series. That single pass upgraded the corpus from "internally consistent enough" to "externally defensible."

## The Competitive Landscape Problem

Paper 014 mapped 28 existing systems against the proposed architecture. This was the most uncomfortable document to write.

When you map 28 systems, you inevitably find work that overlaps with yours. Late-interaction retrieval models. Efficient first-pass scoring. Query-conditioned representations. The research space is not empty.

The exercise forced a precise articulation of what, specifically, is different about this approach versus each existing system. Not "our approach is better" — that is a claim you cannot make without results. Instead: "our approach differs in these specific dimensions, and those differences matter for these specific workloads."

Twenty-eight systems is also enough to spot patterns. Which architectural decisions keep recurring? Where is the field converging? What gaps remain genuinely open?

The uncomfortable truth is that a thorough competitive landscape is as likely to kill your project as validate it. If you find a system that already does what you propose, the honest response is to stop. The 28-system mapping did not produce a project-killer, but it did narrow the novelty claim significantly. The competitive landscape document became the foundation for the probability assessment in Paper 015, which estimated overall success probability at 72% — honest enough to acknowledge real risk, specific enough to identify which candidate architecture has the best odds.

## The Simulated Peer Review: Weak Reject

This was the most informative exercise of the entire day.

Running a simulated NeurIPS-format peer review against the combined synthesis paper produced a "Weak Reject" verdict. The breakdown was instructive:

- **Clarity: 8/10.** The writing is good. The problem is well-motivated. The formalization is clean.
- **Novelty: 7/10.** The combination of ideas is genuinely new, but individual components (knowledge distillation, late interaction, streaming scan) are established.
- **Soundness: 5/10.** This is where the paper dies. Zero empirical results. Every claim is hypothesis or target. No benchmarks. No baselines.

A Weak Reject for a paper with no results is actually generous. Most NeurIPS reviewers would desk-reject an architecture paper with no experiments. The fact that the simulated review found enough merit to engage substantively confirmed that the research direction has legs.

But it also delivered the critical insight: **the gap between a good architecture paper and a publishable one is exactly one set of experiments.** The evaluation plan (Paper 012) specifies those experiments precisely. The probability assessment (Paper 015) estimates a 72% chance of success, with one of the three candidate architectures at 75-80%.

The simulated review converted an abstract sense of "we need results" into a concrete gap analysis with specific remediation steps. That is worth more than a hundred pages of architecture.

If you are working on a pre-empirical research project, run a simulated peer review early. The cost is negligible — a single prompt against your draft. The return is a prioritized list of exactly what a hostile reviewer will attack. You can either fix those problems or deliberately accept the risk. Either way, you are no longer surprised at submission time.

## The Filing Prep Pipeline

The invention packet documents (001-007) serve a different purpose than the research papers. The research papers are written for academic reviewers. The invention documents are written for a patent attorney.

Different audiences need different things. An attorney needs claim language, prior art differentiation, filing strategy options, and fallback scopes. A reviewer needs formal notation, experimental methodology, and comparison to baselines.

Writing both in the same day meant constant context-switching between two very different writing modes. The solution was document numbering — invention packet first (001-007), research series second (008-015), analysis documents last (016-018). Strict ordering prevented cross-contamination of audience and tone.

The toolchain evaluation (016) assessed 11 research tools across 5 tracks and selected 4 for the patent strengthening sprint. The next-step decision document (017) defined a 3-day sprint plan where novelty validation gates any empirical work. The patent strengthening plan (018) detailed three phases: prior art expansion, patent landscape search, and a decision gate.

## The Evidence Tag Discipline

Every technical claim in the corpus carries an evidence tag: Proven, Derived, Simulated, Target, or Hypothesis.

Right now, everything is Hypothesis or Target. Nothing is Proven. This is uncomfortable but honest. The evidence tags exist so that six months from now, when experiments are running, each claim can be upgraded individually. No ambiguity about what has been demonstrated versus what is still speculative.

This practice came from the observation that research papers often blur the line between "we hypothesize" and "we demonstrate." Explicit evidence tags make that blurring impossible. They also serve as a progress tracker — when experiments start producing results, the corpus will gradually shift from Hypothesis-heavy to Proven-heavy, and that shift will be visible in the documents themselves.

## Also Shipped

**Braves infrastructure (braves repo):** Added a Caddy reverse proxy in front of the broadcast dashboard stack and locked down Docker ports so containers are no longer directly accessible from the network. Before this change, every container port was reachable from the LAN. The Caddy layer terminates TLS, handles routing, and means exactly one port is exposed. A tunnel script enables secure remote access without opening services to the internet. Also patched npm vulnerabilities in both backend and frontend — the kind of dependency maintenance that prevents a minor advisory from becoming a weekend emergency six months later.

## What the Day Proved

Twenty-one documents and 4,000+ lines is a volume metric. The interesting metric is coverage. By end of day, the project had:

- A formal invention disclosure positioned for patent filing
- A 6-paper research series suitable for academic submission (after experiments)
- A competitive landscape covering 28 systems
- A probability assessment with a 10-item risk register
- A toolchain selected and a sprint plan ready to execute
- A simulated peer review identifying exactly one gap: empirical results

The gap between "interesting idea" and "filing-ready invention" is not insight. It is documentation. The gap between "filing-ready invention" and "publishable research" is not documentation. It is evidence.

The simulated Weak Reject drew that line clearly. Everything on the documentation side of the line is done. Everything on the evidence side awaits GPU time and a 4-6 week experiment sprint.

That clarity — knowing exactly where you stand and exactly what remains — is the actual output of a 21-document research day.

---

*Related posts:*

- [Designing a Local-First Resume Parser Architecture](/posts/designing-local-first-resume-parser-architecture-edge-ai/) — another architecture-first approach where the design phase precedes implementation
- [Building a Meta-Agent System From Scratch in One Day](/posts/oss-agent-lab-meta-agent-system-one-day/) — a different kind of single-day build: code instead of research
- [Building Post-Compaction Recovery for AI Agent Workflows with Beads](/posts/building-post-compaction-recovery-beads/) — the task persistence system that keeps multi-day research projects recoverable across sessions
