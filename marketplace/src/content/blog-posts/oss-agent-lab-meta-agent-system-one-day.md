---
title: "Building a Meta-Agent System From Scratch in One Day"
description: "From first commit to a 9-specialist multi-agent system with capability scoring, session memory, and a meta-agent orchestrator. All in one day."
date: "2026-03-15"
tags: ["ai-agents", "python", "architecture", "testing", "automation"]
featured: false
---
What if the agent routing your requests was itself an agent? Not a switch statement with an LLM wrapper. An actual agent that evaluates other agents, scores their capabilities, remembers what worked, and routes based on evidence.

That's what [oss-agent-lab](https://github.com/jeremylongshore/oss-agent-lab) shipped in a single day. Six phases. Nine specialists. A meta-agent that orchestrates the entire team. Here's how it came together.

## Phase 1: Specs Before Code

Nine specification documents before a single line of application code. Base package structure, contracts, CLI skeleton, specialist template.

This isn't ceremony. When you're building a multi-agent system, the contracts between agents *are* the architecture. Get them wrong and you refactor every specialist when the routing interface changes. Get them right and each phase stacks cleanly.

Every agent implements the same contract:

```python
class BaseSpecialist(ABC):
    """Contract every specialist must satisfy."""

    @abstractmethod
    def capabilities(self) -> list[Capability]:
        """Declare what this specialist can do."""
        ...

    @abstractmethod
    async def execute(self, intent: ClassifiedIntent, context: SessionContext) -> SpecialistResult:
        """Handle a routed request."""
        ...

    @property
    @abstractmethod
    def name(self) -> str:
        """Unique identifier for registry lookup."""
        ...
```

Three methods. That's the entire plugin surface. Declare capabilities, execute against a classified intent, done. No inheritance trees. No framework magic.

## Phase 2: The Conductor

The `ConductorAgent` is the brain. It takes raw user input, classifies the intent using Claude's SDK, and hands it to the router.

```python
class ConductorAgent:
    """Classifies user intent and orchestrates routing."""

    def __init__(self, registry: SpecialistRegistry, router: RouterAgent, memory: SessionMemory):
        self.registry = registry
        self.router = router
        self.memory = memory

    async def handle(self, user_input: str, session_id: str) -> OrchestratedResult:
        # 1. Recall relevant context from prior turns
        context = self.memory.recall(session_id, keywords=extract_keywords(user_input))

        # 2. Classify intent via Claude SDK
        intent = await self.classify_intent(user_input, context)

        # 3. Route to the best specialist
        result = await self.router.route(intent, context)

        # 4. Persist this turn's context for future recall
        self.memory.store(session_id, intent, result)

        return result
```

Four steps. Recall, classify, route, store. The `SessionMemory` uses keyword-based recall — not vector search, not embeddings. Keywords from user input match against stored turn summaries. Simple, fast, debuggable.

The `SpecialistRegistry` is a flat dictionary with validation. No dependency injection framework. No service locator pattern. Call `register()`, declare capabilities, and the router finds you. Add a new specialist and the system discovers it on the next request.

## Phase 3-4: Nine Specialists

First three: `autoresearch`, `swarm_predict`, `deer_flow`. Then six more in a single push. Nine specialists total, each handling a different domain.

The key insight: specialists don't know about each other. They don't import each other. The `RouterAgent` handles all coordination by comparing capability scores against the classified intent.

```python
class RouterAgent:
    """Routes classified intents to specialists based on capability scores."""

    async def route(self, intent: ClassifiedIntent, context: SessionContext) -> OrchestratedResult:
        candidates = self.registry.capabilities()
        scored = self.scoring_engine.score(candidates, intent, context)

        if not scored:
            return OrchestratedResult.unresolvable(intent)

        best = scored[0]
        specialist = self.registry.get(best.specialist)
        return await specialist.execute(intent, context)
```

The scoring isn't a simple keyword match. It's multi-source.

## Phase 5: Capability Scoring Engine

This is where it gets interesting. Three scoring sources, weighted and combined:

**Temporal scoring.** Recent successes get a boost. A specialist that handled a similar intent 5 minutes ago scores higher than one that handled it yesterday. Natural "hot path" behavior without explicit caching.

**User feedback scoring.** Ratings feed back into capability scores. A specialist that consistently gets thumbs-down on a particular intent type sees its score decay. No manual tuning — the system self-corrects.

**Domain relevance scoring.** Static scores declared in each specialist's capability contract. The baseline that temporal and feedback signals modify.

The three combine with configurable weights: 40% domain relevance, 35% temporal, 25% user feedback. Tunable per deployment.

## Phase 6: The Meta-Agent

Here's the recursive part. The meta-agent is itself a specialist registered in the same registry. But instead of handling a single domain, it orchestrates multi-step workflows across the entire specialist team.

When the intent classifier detects a compound request — "research X, then predict Y based on the research" — the conductor routes to the meta-agent. The meta-agent decomposes the compound intent into sub-intents, routes each through the same conductor pipeline, and assembles the results.

It's agents all the way down. Same routing infrastructure as any other request. The meta-agent just happens to produce requests instead of consuming them. The output generator formats results for the final consumer — CLI, API, whatever sits on top.

## The CI Story

This isn't a prototype. mypy strict mode, ruff, unit tests for every component, and E2E orchestration tests covering the full pipeline from user input to specialist output.

The E2E tests prove the contracts work end-to-end:

```python
async def test_full_orchestration():
    registry = SpecialistRegistry()
    registry.register(MockResearchSpecialist())
    registry.register(MockPredictSpecialist())

    conductor = ConductorAgent(registry=registry, router=RouterAgent(registry), memory=SessionMemory())

    result = await conductor.handle("research recent trends in LLM agents", session_id="test-1")

    assert result.specialist == "autoresearch"
    assert result.status == "success"
```

If the contract between conductor, router, registry, and specialist breaks, this test catches it. No mocks hiding the integration boundary.

## Also: claude-code-plugins Detail Pages

Parallel track. The [claude-code-plugins](https://github.com/jeremylongshore/claude-code-plugins) registry shipped enhanced detail pages with README section extraction, markdown-to-HTML rendering for skill content, redesigned contributor cards, and a Killer Skill hero spotlight with email signup. Four PRs.

## From Empty Repo to Multi-Agent System

Six phases in one day is possible because of two things. First: contracts came first. The specialist template, the capability declaration, the intent classification schema — these don't change across phases. Stable core, everything else plugs in.

Second: agents that don't know about each other are easy to build in parallel. No circular dependencies. No coordination overhead. The meta-agent uses the same public API as any external consumer.

The result is an open-source lab where you can evaluate any agent framework by wrapping it in a specialist contract, registering it, and letting the scoring engine figure out when to use it. Not another agent framework. A system for *comparing* agent frameworks.

---

*Related posts:*

- [Building a Deterministic DXF Comparison Engine in One Day](/blog/deterministic-dxf-comparison-engine-one-day-build/) — another greenfield system with layered architecture shipped in a single session
- [From Tool to Platform: IntentCAD Ships Five EPICs in One Day](/blog/from-tool-to-platform-intentcad-five-epics-one-day/) — the same contract-driven routing pattern applied to CAD operations
- [Zero to CI: Full-Stack Dashboard in One Session](/blog/zero-to-ci-full-stack-dashboard-one-session/) — opinionated stack choices and specs-first methodology in a different domain
