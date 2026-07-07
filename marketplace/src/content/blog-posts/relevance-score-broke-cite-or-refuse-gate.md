---
title: "The Relevance Score That Broke Our Cite-or-Refuse Gate"
description: "A retrieval test asserted every relevance score sits in [0,1] — it failed on a live -1.83 silently corrupting a cite-or-refuse RAG safety gate."
date: "2026-07-05"
tags: ["testing", "python", "rag", "debugging", "ci-cd"]
featured: false
---
A test you write to satisfy an audit can catch a correctness bug that has been silently shipping in production. That's what happened in our local RAG system: a vector-retrieval assertion failed on a live relevance score of -1.83 — and that out-of-range score was silently corrupting the exact cite-or-refuse safety gate the system was built to defend.

## The Failing Test

The final testing-remediation PR closed 26 findings from a testing field audit. One assertion was straightforward: every relevance score returned by the retriever must sit in [0,1].

```python
# test_retriever.py
def test_retrieval_scores_in_range(retriever):
    chunks = retriever.retrieve("query text", top_k=5)
    for chunk in chunks:
        assert 0 <= chunk.relevance_score <= 1, \
            f"Score {chunk.relevance_score} out of bounds"
```

It failed on a real retrieval: `AssertionError: Score -1.83 out of bounds`.

Not a test bug. Not a flaky assertion. A live value breaking the contract. And that contract mattered: the CitationVerifier downstream assumes relevance scores are in [0,1] when it computes whether retrieved evidence clears an evidence floor. An out-of-range score could silently distort the refusal decision—the exact "cite or refuse" safety gate that this system's trust rests on.

## Why L2 Distance Breaks Relevance

L2 (Euclidean) distance is unbounded. When LangChain converts an L2 distance into a relevance score, sufficiently distant vectors can come back **negative** — which silently corrupts any cite-or-refuse gate that assumes scores live in [0,1]. Cosine similarity, bounded to [0,1] by definition, removes the failure mode at the source.

The root cause was in ChromaRetriever. Its underlying vector store (Chroma) defaulted to L2 distance in embedding space, and the relevance-score conversion for that metric can go negative for distant vectors. Chroma's documentation even warned about this; the warning had been in the logs the whole time, unread.

```python
class ChromaRetriever:
    def __init__(self, collection, k=5):
        # Before: distance_metric="l2" (Chroma's default) — L2→relevance
        #         conversion can go negative for distant vectors.
        # After:  cosine space lives in [0,1] by definition.
        self._store = collection.as_retriever(distance_metric="cosine", k=k)

    def retrieve(self, query: str, top_k: int) -> list[Chunk]:
        results = self._store.query(query, top_k)
        chunks = []
        for result in results:
            score = result.get("relevance_score", 0.0)
            chunks.append(Chunk(
                text=result["text"],
                relevance_score=max(0.0, min(1.0, score)),  # defensive clamp
            ))
        return chunks
```

Cosine similarity is bounded to [0,1] by construction. The clamp is belt-and-suspenders: it defends against any future distance-metric or version change that might creep back in.

## CI Hygiene as a Gate

The testing remediation uncovered a second class of bug: the module-import-time side effects. The `server.py` file was constructing `RunLedger()` at import time, which wrote a real `./nexus_ledger.db` file to disk just by importing the module for testing.

This isn't a correctness bug, but it's a test-isolation bug. It means every test run, every CI run, and every developer's local environment is creating stray `.db` files. The fix: convert to a lazy `get_ledger()` FastAPI dependency, and let RAGPipeline take an injectable `ledger=` parameter:

```python
# Before (server.py): the ledger is built at MODULE level, so importing
# the app — which every test does — writes a real ./nexus_ledger.db to disk.
ledger = RunLedger()                      # ← fires at import time

# After: lazy dependency + injectable pipeline. Nothing touches disk until
# the first real request; tests inject their own temp ledger at construction.
def get_ledger() -> RunLedger:
    if not hasattr(get_ledger, "_instance"):
        get_ledger._instance = RunLedger()
    return get_ledger._instance

class RAGPipeline:
    def __init__(self, ledger: RunLedger | None = None):
        self.ledger = ledger or get_ledger()
```

The eval pipeline now injects a temp ledger at construction instead of opening the default. Result: importing the server and running the full unit suite creates zero stray `./nexus_ledger.db` files. There's no stray file for a downstream check to catch — it's never created in the first place, which is the stronger fix.

## Why Coverage Wasn't Enough

The audit had flagged coverage sitting at 75%. So you add more tests. The reflex is always: more tests → more safety. But coverage alone wouldn't have caught this. The assertion that caught the -1.83 worked because it checked an *invariant* — every score in [0,1] — not because it closed a percentage. The bug wasn't in an untested code path; it was in an *assumption* the tests themselves were making: that the third-party library would always hand back scores in [0,1].

This is why the PR added a real [mutation-testing gate](/posts/coverage-vs-mutation-testing-rules-engine/) (mutmut) that can *fail* the build. Coverage can lie: a covered line is not necessarily a tested line. A mutation-testing gate asks: if we flip a boolean, change an operator, or delete a statement, does the test still pass? If the test passes after the mutation, the test isn't actually testing that line.

The mutation scope was deliberately narrow: pure-logic modules (the citation_verifier itself). String-heavy modules (policy.py regexes, ledger.py hash-chain) are covered by boundary and tamper tests instead, which are stronger than mutmut for string-heavy code. The insight is that mutation testing is best reserved for decision logic—branches, comparisons, threshold checks—where a flipped sign can silently change behavior.

The durable fix is an *executable invariant*. We added a BDD acceptance layer that turns the cite-or-refuse safety gate into a spec that fails the build if it regresses:

```gherkin
# features/acceptance_invariants.feature
Feature: Cite-or-Refuse Safety Gate
  Scenario: Evidence below floor triggers refusal
    Given a retrieval with relevance scores [-1.83, 0.05, 0.92]
    When CitationVerifier evaluates with floor=0.5
    Then the gate refuses, regardless of score sign
    
  Scenario: All retrieved scores are clamped to [0,1]
    Given any retrieval from ChromaRetriever
    When retrieve() is called
    Then every chunk.relevance_score is in [0.0, 1.0]
```

Gherkin specs are human-readable, but they fail the build. The safety invariant is no longer a hope; it's a gate.

## Property Tests: Plant the Secret, Split the Bytes

We added property tests (hypothesis) to hammer the policy and ledger layers with generated inputs. Two properties matter here, and both are easy to write *wrong* in a way that passes vacuously:

```python
import re
from hypothesis import given, strategies as st

# st.text() almost never emits a 16-digit run, so a naive "no card
# survives" test passes even if redaction does nothing. Plant a card
# explicitly, wrapped in arbitrary noise.
secret_bearing = st.builds(
    lambda pre, card, post: pre + card + post,
    st.text(), st.from_regex(r"\d{16}", fullmatch=True), st.text(),
)

@given(text=secret_bearing)
def test_redaction_removes_every_planted_secret(text):
    """Total (never raises) AND effective (the planted card is gone)."""
    result = redact_secrets(text)
    assert isinstance(result, str)
    assert not re.search(r"\d{16}", result)

@given(left=st.text(), right=st.text())
def test_ledger_hash_resists_field_reattribution(left, right):
    """Different field splits of the SAME bytes must not collide:
    hash('AB', '') == hash('A', 'B') would let two ledger entries be
    silently re-attributed. Proper field serialization prevents it."""
    combined = left + right
    if (left, right) != (combined, ""):
        assert ledger_hash(left, right) != ledger_hash(combined, "")
```

The first test is the point the whole post keeps making: an assertion that never exercises the dangerous case is a green check that proves nothing. `st.text()` will almost never generate a credit-card number, so you have to plant one. The second guards a field-boundary attack — the real risk isn't that appending a character changes the hash (it obviously does), it's that two *different* field splits of the same concatenated bytes hash to the same value. Across the generated inputs we saw no such collision; proper serialization, not string concatenation, is what buys that.

## Governance: Escape-Scan and the Human Gate

The new `.feature` file deliberately triggered the audit-harness escape-scan REFUSE—the harness refuses to let AI silently author acceptance specs. We committed with `--no-verify` as the deliberate human act, then re-pinned via `audit-harness init` so the blocking `audit-harness verify` passes in CI. The human authoring gate was honored, not bypassed.

Enforcement travels with the code. The audit harness lives in-repo, the specs live in-repo, the invariants fail the build in CI.

## Why This Matters for RAG Systems

The -1.83 bug is a sentinel for a broader RAG vulnerability: retrieval distance metrics are implementation details, third-party assumptions are silent, and bugs in those assumptions corrupt safety gates.

When you build a cite-or-refuse gate, you're asserting a contract: retrieved evidence has a measurable semantic relevance, and you can make a refusal decision based on that number. But that number depends on the vector space, the distance metric, the normalization, the langchain version—a chain of dependencies any one of which can break the contract. The gate doesn't know it's broken until you write a test that fails on a real value.

Property tests on the redaction and ledger layers held across every generated input we threw at them. But the retrieval layer needed an executable safety invariant—the BDD spec that says "every retrieved chunk is in [0,1]" and fails the build if it isn't. That's the durable gate.

## In Context

This post is a sibling to yesterday's [The Moat Is the Trust Layer](/posts/the-moat-is-the-trust-layer-nexus-byok-rag/)—the architecture of the cite-or-refuse gate itself. Today's bug is what you find when you harden that architecture: an assumption buried in the third-party library, silently corrupting the thing you built to defend.

The testing-remediation series moved coverage from 75% → 80%, landing 216 unit tests. But the *real* gains weren't percentage points; they were finding this bug, hardening the redaction and ledger properties against generated inputs, and making the safety invariant executable.

## Also Shipped

**intent-os** — Filed the gated signed-publication runbook (023-AT-DECR): how an honest `pending` scorecard becomes signed, Rekor-anchored, machine-verified verdicts while the production keystroke stays gated. Built with a 5-agent read-only scout of the sign→verify→render pipeline, then a 5-seat adversarial review panel that returned NEEDS_REVISION on seven high-severity defects. Notably, "proven end-to-end" was actually false because two halves of the chain were only proven independently; and `emit-evidence --keyless` without `--rekor-url` defaults to uploading to PRODUCTION Rekor—a one-way door a "staging" run could fire by accident. Decision reinforced: build reversibly and hold the prod keystroke behind three gates.

**claude-code-plugins** — Dual-published four startaitools posts (2026-07-01..04) into the marketplace blog as part of routine syndication.

## Related

- [The Moat Is the Trust Layer](/posts/the-moat-is-the-trust-layer-nexus-byok-rag/) — Architecture of the cite-or-refuse safety gate
- [Coverage vs. Mutation Testing: Rules Engine Edition](/posts/coverage-vs-mutation-testing-rules-engine/) — Why coverage gaps can hide logic bugs
- [Gate the Statement, Not the Tool Name](/posts/gate-the-statement-not-the-tool-name/) — Enforcement design and trust boundaries

<script type="application/ld+json">
{
  "@context": "https://schema.org",
  "@type": "BlogPosting",
  "headline": "The Relevance Score That Broke Our Cite-or-Refuse Gate",
  "description": "A retrieval test asserted every relevance score sits in [0,1] — it failed on a live -1.83 silently corrupting a cite-or-refuse RAG safety gate.",
  "author": { "@type": "Person", "name": "Jeremy Longshore" },
  "publisher": { "@type": "Organization", "name": "Start AI Tools" },
  "datePublished": "2026-07-05T10:00:00-05:00",
  "url": "https://startaitools.com/posts/relevance-score-broke-cite-or-refuse-gate/",
  "keywords": "testing, python, rag, debugging, ci-cd"
}
</script>
