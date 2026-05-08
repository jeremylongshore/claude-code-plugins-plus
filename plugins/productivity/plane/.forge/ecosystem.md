# Forge Ecosystem Absorb — Plane

**Captured**: 2026-05-07
**Source**: WebSearch + direct knowledge of the IS / Anthropic ecosystem

## Competing tools

### 1. Plane web UI (`projects.intentsolutions.io`)

**What it does**: official ticket entry, cycle planning, project dashboards, member management.
**What it does well**: visual overview of one project at a time; great for ticket entry; shows the standard agile dashboards (burndown, velocity by cycle).
**What it doesn't do**:
- Cross-project synthesis — each project is its own dashboard; aggregated questions ("Alice's load across all projects") require multi-tab gymnastics
- Behavioral signal — ticket counts, not patterns of behavior under pressure
- Stated-vs-actual priority drift — the planning view and the closed-ticket view never get JOINed in the UI

### 2. `mcp__plane` MCP server

**What it does**: direct CRUD against Plane API exposed as MCP tools (~50 tools covering issues / cycles / modules / members / labels / states).
**What it does well**: programmatic access from any MCP-aware tool (Claude Code, etc.); 1:1 surface coverage of the Plane API.
**What it doesn't do**:
- Compound queries — every tool returns one resource type (issues OR cycles OR members), never JOINed
- Synthesis — `mcp__plane__list_project_issues` returns 100 issues; the consumer is responsible for any aggregation, scoring, or pattern detection
- Scoring — no built-in concepts of "stale" or "bottleneck" or "drift"

This is the **closest tool** to what this forge produces, but it's a layer below: this skill consumes `mcp__plane` plus its own JOIN logic to produce behavioral observations.

### 3. Linear (competitor)

**What it does**: similar issue tracker with comparable cycle/triage/roadmap features. Generally faster + more polished UX than Plane.
**What it doesn't do** (relevant to this forge): same gap — Linear's API surface is also CRUD-shaped; behavioral synthesis is not in their product.
**Note**: Linear has a vibrant ecosystem of community CLI/dashboard tools, but they are mostly display layers on Linear's existing data, not observation engines.

### 4. Notion + Plane embeds (third-party pattern)

**What it does**: visual aggregation of Plane data inside Notion via embeds + iframe walls.
**What it does well**: keeps the data viewer in the team's main collaboration tool.
**What it doesn't do**: display-only; no scoring; no behavioral pattern detection; the Plane embed renders Plane's UI inside Notion, doesn't transform it.

### 5. Plane CLI (community)

**What it does**: terminal-friendly access to ticket CRUD via the Plane API.
**What it doesn't do**: same as MCP — surfaces the API, doesn't synthesize.

## Gap analysis

The five tools above cluster into three categories:

1. **Display layers** (web UI, Notion embeds): show the data. None synthesize.
2. **Surface exposers** (MCP, CLI): expose the API. None synthesize.
3. **Competitor trackers** (Linear): same API shape, same display-or-expose dichotomy.

**Nobody is selling the observation engine.** The closest thing in the wild is internal scripts engineers write for their own teams (JOIN cycle data, score by churn, surface bottlenecks) — but those are bespoke per-team, not packaged as a reusable skill.

## How this forge differs

This skill occupies the **observation layer** that's missing from the ecosystem:

- It assumes you ALREADY have access to Plane (via `mcp__plane`); doesn't compete with display or surface tools
- It JOINs across endpoints to surface patterns — cycle-velocity vs. estimate, ownership churn, reviewer gate strength, priority drift, cross-project load
- It scores rather than just lists — every output is annotated with a behavioral score the consumer can act on
- It frames the output in terms of team behavior, not ticket state — the question "is this team's plan rooted in reality?" is the through-line

If a "Plane skill" already existed in the marketplace, that question would settle the differentiation: does it answer behavioral questions or data-retrieval questions? **None of the five tools above answer behavioral questions.** This one does.

## Decision: ship

The NOI is genuinely uncovered ground. Forge proceeds.
