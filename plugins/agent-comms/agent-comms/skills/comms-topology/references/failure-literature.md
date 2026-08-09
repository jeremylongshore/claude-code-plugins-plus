# Why topology is the lever — the published evidence

Every claim below is attributed. Citation counts are as of 2026-08-09 and will drift; the direction of
the findings is what the decision rules rest on.

## Coordination defects dominate, not model capability

**Nechepurenko & Shuvalov, "Coordination as an Architectural Layer for LLM-Based Multi-Agent Systems"**
(arXiv:2605.03310, 2026). Reports that multi-agent LLM systems fail in production at rates between
**41% and 87%**, "mostly due to coordination defects rather than base-model capability," and argues
coordination should be treated as "a configurable architectural layer, separable from agent logic and
from information access."

That framing — coordination as a configurable layer rather than an emergent property of the agents — is
the premise this entire skill is built on. Caveat worth stating: the paper is new and lightly cited
(2 citations), and its own instantiation is deliberately scoped as "a methodology-validating first
instantiation, not a general cross-model claim." Use it for the framing; do not over-weight the
specific percentages.

## Inter-agent misalignment is a top-three failure category

**Cemri et al., "Why Do Multi-Agent LLM Systems Fail?"** (arXiv:2503.13657, NeurIPS 2025, ~498
citations). The MAST taxonomy: **14 failure modes** derived from 1,600+ annotated traces across
multiple frameworks, grouped into three top-level categories. One of the three is **inter-agent
misalignment** — failures that live in the conversation between agents, not inside any one of them.

This is the empirical backing for the claim that debugging at the message layer misses the defect.
A failure classified as inter-agent misalignment cannot be fixed by a better prompt on either side.
The `mas-failure-triage` skill in this pack diagnoses against this taxonomy directly.

## Fewer edges is both cheaper and safer

**Zhang et al., "Cut the Crap: An Economical Communication Pipeline for LLM-based Multi-Agent Systems"**
(AgentPrune; arXiv:2410.02506, ICLR, ~121 citations). First to formally define **communication
redundancy** in multi-agent pipelines. Reported results across six benchmarks:

- Comparable results to state-of-the-art topologies at **$5.6 versus $43.7** cost.
- **28.1%–72.8% token reduction** when integrated into existing frameworks.
- Successfully defended against **two types of agent-based adversarial attack**, with a 3.5%–10.8%
  performance improvement while doing so.

The security result is the underappreciated half. Pruning is normally sold as a cost measure; here the
same pruning reduced attack surface, because a redundant edge is also a path an adversarial message can
travel. **Edge count is a security metric, not only a budget line.**

## Cycles break convergence

**Liu et al., "Deep Hierarchical Communication Graph in Multi-Agent Reinforcement Learning"** (DHCG;
IJCAI 2023, ~20 citations). States plainly that "the parallel message-passing update in the undirected
graph with cycles **cannot guarantee convergence**." DHCG's response is to learn dependency
relationships as **directed acyclic graphs**, eliminating cycles with an acyclicity constraint applied
as an intrinsic reward and projecting the graph into the admissible set of DAGs. The paper notes the
same move "removes redundant communication edges for cost improvement."

The setting is multi-agent reinforcement learning, not LLM agents, so this transfers as a structural
argument rather than a measured result: a cyclic message-passing graph has no convergence guarantee,
and enforcing acyclicity buys both termination and redundancy reduction at once. Same lever, twice.

## Individually-aligned agents can still fail collectively

**Bisconti et al., "Beyond Single-Agent Safety: A Taxonomy of Risks in LLM-to-LLM Interactions"**
(arXiv:2512.02682, 2025, ~7 citations). Introduces the **Emergent Systemic Risk Horizon (ESRH)** to
formalize how instability arises "from interaction structure rather than from isolated misbehavior."
The core observation: in systems where outputs are recursively reused as inputs across chains of
agents, "local compliance can aggregate into collective failure even when every model is individually
aligned."

This is the argument for why per-agent guardrails are necessary and insufficient. The safety property
lives in the graph. A topology review is a safety review.

## What this literature does not say

- It does not say multi-agent systems are a bad idea. Every one of these papers assumes collective
  systems outperform single agents on the tasks studied.
- It does not give a universal topology. The decision rules in `topology-decision-rules.md` are
  engineering judgment informed by these findings, not a result any of them proved.
- It does not license claiming an assurance property. Pruning reduced attack success in one study on
  one benchmark set. That is evidence, not a guarantee, and copy should say so.
