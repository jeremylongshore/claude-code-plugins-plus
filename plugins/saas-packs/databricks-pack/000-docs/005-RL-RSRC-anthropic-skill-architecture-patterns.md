# Architectural Patterns in Anthropic-Published Claude Code Skills (2026)

**Compiled:** 2026-05-27
**Purpose:** Reference catalog for the Databricks skill-pack rebuild. Captures the patterns Anthropic itself uses in first-party skills and plugins shipped through `anthropics/skills` and `anthropics/claude-plugins-official`, with deepest attention to the **`security-guidance` plugin** (v2.0.0) released as the public face of "Claude Code Security."
**Primary corpus:**

- `github.com/anthropics/skills` — official skill library (skill-creator, mcp-builder, pdf, docx, pptx, xlsx, webapp-testing, frontend-design, brand-guidelines, internal-comms, …)
- `github.com/anthropics/claude-plugins-official` — official directory of Anthropic-managed plugins (`security-guidance`, `pr-review-toolkit`, `feature-dev`, `code-review`, `hookify`, `mcp-server-dev`, `skill-creator`, `claude-md-management`, 20+ LSP plugins, …)
- `github.com/anthropics/claude-code-security-review` — earlier GitHub-Action incarnation of the security reviewer (predecessor to `security-guidance`)
- `platform.claude.com/docs/en/agents-and-tools/agent-skills/best-practices` — canonical authoring guide
- `code.claude.com/docs/en/skills` — Claude Code skill runtime reference
- Anthropic engineering blog: "Equipping agents for the real world with Agent Skills"

**How to read this catalog:** every pattern has a real Anthropic-shipped example with file path. Where I infer behavior from docs without a code-level confirmation, the entry is explicitly marked **"INFERRED."** For Databricks (or any other) rebuild, pick the patterns that fit the problem shape — they compose.

---

## Source reference: the security-guidance plugin

Three architectural surfaces, one plugin. The same plugin demonstrates ~6 of the 10 patterns below, so it's worth understanding once up-front:

| Layer | Trigger | Mechanism | Cost |
|---|---|---|---|
| **1. Pattern warnings** | `PostToolUse` on `Edit\|Write\|MultiEdit\|NotebookEdit` | Pure-Python regex match in `patterns.py` (~25 rules) — **zero model calls** | Free |
| **2. LLM diff review** | `Stop` hook (turn complete) | Sends git diff to a fast model via Agent SDK | One Opus 4.7 call per turn |
| **3. Agentic commit review** | `PostToolUse` on `Bash(git commit:*)` / `Bash(git push:*)` | Spawns a subagent loop (Read/Grep/Glob) for cross-file vuln tracing, then a separate self-refute pass | Multiple model calls |

Layer 1 fires synchronously in the hook; layers 2 and 3 use `asyncRewake` so the reviewer runs in the background and re-wakes Claude when findings land. This is the canonical Anthropic recipe for "proactive intervention without blocking the user" and underlies several patterns below.

---

## AP01 — Three-level progressive disclosure (metadata → SKILL.md → bundled files)

**Type:** progressive-disclosure
**What it does:** Skills are loaded in three context-cost tiers. Tier 1 — the YAML `name` + `description` (~100 tokens) — is permanently in the system prompt for every skill the agent knows about. Tier 2 — the SKILL.md body (≤500 lines) — is read only when the description matches the user's intent. Tier 3 — `references/*.md`, `scripts/*`, `assets/*` — is read on demand, file by file, when the SKILL.md body points to it. Files never read consume zero context.

**Anthropic example:** Every official skill. `anthropics/skills/skills/mcp-builder/SKILL.md` is the prototypical case: the body is a 4-phase workflow that references `reference/mcp_best_practices.md`, `reference/node_mcp_server.md`, `reference/python_mcp_server.md`, `reference/evaluation.md` with inline pointers like `"For TypeScript (recommended): [⚡ TypeScript Guide](./reference/node_mcp_server.md)"`. Claude reads only the language guide it needs. From `best-practices.md`:

> "1. Metadata pre-loaded: At startup, the name and description from all Skills' YAML frontmatter are loaded into the system prompt. 2. Files read on-demand: Claude uses bash Read tools to access SKILL.md and other files from the filesystem when needed. 3. Scripts executed efficiently: Utility scripts can be executed via bash without loading their full contents into context. Only the script's output consumes tokens."

**When to use it:** Always. This is the foundational pattern — any skill larger than ~200 lines should be split.

**When NOT to use it:** Simple, single-purpose skills that fit comfortably in one screen. Forcing references on a 50-line skill adds navigation overhead with no token savings.

**Implementation sketch:**

```
my-skill/
├── SKILL.md                     # ≤500 lines: workflow + decision points + pointers
└── references/
    ├── api-reference.md         # only read if Claude needs API specifics
    ├── examples.md              # only read if Claude needs examples
    └── platform-aws.md          # only read if user targets AWS
```

```markdown
# SKILL.md
## Quick start
[the 80% case inline]

## Advanced features
**Form filling:** see [references/forms.md](references/forms.md)
**API reference:** see [references/api.md](references/api.md)
**Platform variants:** AWS [aws.md], GCP [gcp.md], Azure [azure.md]
```

**Hard rules from Anthropic's best-practices doc:**

- Keep references **one level deep** from SKILL.md. Claude may `head -100` nested references and miss content.
- For reference files >100 lines, include a **table of contents at the top** so partial reads still surface the full scope.
- Organize references by domain (`reference/finance.md`, `reference/sales.md`) not by file number (`docs/file1.md`).

**Citations:**

- https://platform.claude.com/docs/en/agents-and-tools/agent-skills/best-practices (§ "Progressive disclosure patterns")
- https://github.com/anthropics/skills/blob/main/skills/mcp-builder/SKILL.md
- https://www.anthropic.com/engineering/equipping-agents-for-the-real-world-with-agent-skills

---

## AP02 — Hook-driven proactive intervention (PostToolUse / Stop / UserPromptSubmit)

**Type:** hook-driven
**What it does:** Instead of waiting for the user to invoke a skill, the plugin registers hooks that run on Claude Code lifecycle events (`SessionStart`, `UserPromptSubmit`, `PreToolUse`, `PostToolUse`, `Stop`). The hook script — usually a thin bash launcher that hands off to Python — sees tool calls, file edits, and turn boundaries, and decides whether to inject context, warn, or escalate. This is the only way to make a skill **mandatory** (it fires whether Claude remembers to invoke it or not).

**Anthropic example:** `security-guidance/hooks/hooks.json` registers four event types:

```json
{
  "hooks": {
    "SessionStart": [{"hooks": [{"type": "command", "command": "bash ${CLAUDE_PLUGIN_ROOT}/hooks/sg-python.sh ${CLAUDE_PLUGIN_ROOT}/hooks/ensure_agent_sdk.py", "timeout": 180}]}],
    "UserPromptSubmit": [{"hooks": [{"type": "command", "command": "bash ${CLAUDE_PLUGIN_ROOT}/hooks/sg-python.sh ${CLAUDE_PLUGIN_ROOT}/hooks/security_reminder_hook.py"}]}],
    "PostToolUse": [
      {"matcher": "Edit|Write|MultiEdit|NotebookEdit", "hooks": [{"type": "command", "command": "..."}]},
      {"matcher": "Bash", "hooks": [
        {"if": "Bash(git commit:*)", "asyncRewake": true, "rewakeMessage": "Background security review of commit ...", "command": "..."},
        {"if": "Bash(git push:*)", "asyncRewake": true, "rewakeMessage": "Background security review of pushed commits ...", "command": "..."}
      ]}
    ],
    "Stop": [{"hooks": [{"type": "command", "asyncRewake": true, "rewakeMessage": "Background security review feedback ...", "command": "..."}]}]
  }
}
```

Note the **matcher** field on `PostToolUse` (regex `Edit|Write|MultiEdit|NotebookEdit`) and the **conditional `if`** on Bash hooks (`Bash(git commit:*)`, `Bash(git push:*)`). The same hook script is registered four times with different gating — the script reads the event payload via stdin and dispatches.

`hookify/hooks/` (another Anthropic plugin) shows the same shape distilled to one file per event: `pretooluse.py`, `posttooluse.py`, `stop.py`, `userpromptsubmit.py`.

**When to use it:** When the safety / correctness property must hold **whether or not Claude opts in** — security scans, lint enforcement, secret-leak detection, mandatory pre-commit checks, session-start CLAUDE.md injection.

**When NOT to use it:** Hooks add latency to every matched event. Don't use them for capabilities the user invokes deliberately — those belong in commands or skills. Don't use a `PreToolUse` hook that calls an LLM (blocks the tool call for seconds); use `PostToolUse` + asyncRewake instead.

**Implementation sketch:** `hooks.json` at the plugin root:

```json
{
  "hooks": {
    "PostToolUse": [{
      "matcher": "Edit|Write|MultiEdit",
      "hooks": [{
        "type": "command",
        "command": "bash \"${CLAUDE_PLUGIN_ROOT}/hooks/run.sh\" \"${CLAUDE_PLUGIN_ROOT}/hooks/scan.py\""
      }]
    }]
  }
}
```

Hook script reads JSON event from stdin, exits 0 for "no comment", exits 2 with stderr message for "block this tool call" (PreToolUse only), or prints to stdout for "inject this back as context."

**Citations:**

- https://github.com/anthropics/claude-plugins-official/blob/main/plugins/security-guidance/hooks/hooks.json
- https://github.com/anthropics/claude-plugins-official/tree/main/plugins/hookify
- https://code.claude.com/docs/en/hooks

---

## AP03 — Async rewake (background review without blocking the user)

**Type:** hook-driven / async-orchestration
**What it does:** A long-running hook (e.g., one that calls an LLM for a code review) declares `asyncRewake: true` in `hooks.json`. The hook returns immediately so Claude can finish its turn and the user gets a response. When the background work completes with findings, the hook **rewakes the conversation** by injecting a system message (`rewakeMessage`) plus a one-line summary (`rewakeSummary`) into Claude's next turn. Claude then has to address or acknowledge the findings before continuing the user's original task.

**Anthropic example:** `security-guidance`'s `Stop` and `PostToolUse(Bash)` hooks:

```json
{
  "type": "command",
  "command": "bash ... security_reminder_hook.py",
  "if": "Bash(git commit:*)",
  "asyncRewake": true,
  "rewakeMessage": "Background security review of commit — address or acknowledge the findings below, then continue with the user's original request or continue waiting for their reply:",
  "rewakeSummary": "Commit security review found issues"
}
```

The plugin's `review_api.py` runs a **two-stage agentic review** (investigate → self-refute, AP07 below) that takes 10-60s of model time. Without `asyncRewake`, the user would stare at a frozen terminal after every `git commit`. With it, the commit returns, Claude tells the user "commit done," and a few seconds later a fresh context block appears: "🛡 Background security review found issues — here are 2 medium-severity findings to address before pushing."

**When to use it:** Any hook that takes longer than ~3s, especially anything that calls an LLM. Critical for skills that want to add a "second pair of eyes" without slowing the loop.

**When NOT to use it:** Don't async-rewake for findings the user must acknowledge **before** the next action proceeds — that's a confirmation gate (AP05), not a review. Don't use async-rewake if the cost of running it is so high you'd want the user's go-ahead first.

**Implementation sketch:**

```json
{
  "type": "command",
  "command": "bash slow-reviewer.sh",
  "asyncRewake": true,
  "rewakeMessage": "Background analysis complete. Findings below — fold them into your next response or acknowledge to user:",
  "rewakeSummary": "Analysis found 3 issues"
}
```

The script prints findings to stdout; the harness captures them and queues them as the next user-visible system message. The user feels no latency, but Claude can't ignore the findings — they re-enter the context at the next turn boundary.

**Citations:**

- https://github.com/anthropics/claude-plugins-official/blob/main/plugins/security-guidance/hooks/hooks.json (the `asyncRewake` / `rewakeMessage` / `rewakeSummary` fields)
- https://github.com/anthropics/claude-plugins-official/blob/main/plugins/security-guidance/README.md (§ "Three layers")

---

## AP04 — Script-vs-LLM decision separation (deterministic-first, LLM-as-fallback)

**Type:** script-orchestration
**What it does:** Operations that have a clear right answer — regex matches, file existence checks, JSON parsing, byte counting, hashing — are executed as **pre-written scripts** invoked from the hook or skill. LLM reasoning is reserved for tasks that genuinely require judgment (cross-file vulnerability tracing, "is this finding a false positive given this codebase's conventions"). The official best-practices doc calls this out explicitly:

> "Prefer scripts for deterministic operations: Write `validate_form.py` rather than asking Claude to generate validation code." — *best-practices.md*
>
> "Code is deterministic." — *Equipping agents for the real world*

**Anthropic example:** The `security-guidance` plugin's three layers are a perfect ladder of escalation:

1. **Layer 1 (deterministic, zero model calls):** `hooks/patterns.py` contains ~25 hand-written rules — each one a regex + path filter + reminder string. The launch announcement specifically calls out: *"the first running a fast, deterministic pattern match with no model call ... because this layer requires no AI inference, it adds zero usage cost."*
2. **Layer 2 (single LLM call):** `Stop` hook runs `git diff`, sends it to Opus 4.7 with a one-shot prompt, returns findings.
3. **Layer 3 (agentic, multiple LLM calls):** On `git commit`, an Agent-SDK reviewer with Read/Grep/Glob traces data flow across files.

The skill author chose where on the deterministic ↔ reasoning ladder each check belongs. `eval(`, `yaml.load()`, `dangerouslySetInnerHTML` — those are regex catches. "Does this new endpoint enforce ownership against the entity it mutates?" — that's the agentic layer.

The `mcp-builder` skill demonstrates the same principle differently: the skill body is decision-flow prose for the LLM, but the heavy reference content (TypeScript SDK conventions, Python SDK conventions, MCP best practices) is **static reference files Claude reads when needed** rather than generated each time.

**When to use it:** Whenever an operation is repeatable and verifiable. Common candidates: file format detection, syntax validation, regex pre-filtering, hash verification, structured-data extraction, schema checking.

**When NOT to use it:** Don't deterministic-script a check that depends on codebase context the script can't see ("is this `eval()` safe because the caller validated upstream?"). Use the script to *raise the candidate*, then let the LLM reason about it.

**Implementation sketch:**

```python
# patterns.py (deterministic)
SECURITY_PATTERNS = [
    {"ruleName": "eval_injection",
     "path_filter": lambda p: not p.endswith(_DOC_EXTS),
     "regex": r"(?<![a-zA-Z0-9_\.])eval\(",
     "reminder": "⚠️ eval() executes arbitrary code. Use JSON.parse() ..."},
    # ...24 more
]
```

```python
# review_api.py (LLM, gated to high-leverage work only)
AGENTIC_INVESTIGATE_SYSTEM = """You are a senior application-security engineer ...
The #1 cause of missed vulnerabilities is not reading the file that contains them.
Before any analysis: Read EVERY changed file in full ..."""
```

**Citations:**

- https://github.com/anthropics/claude-plugins-official/blob/main/plugins/security-guidance/hooks/patterns.py
- https://www.helpnetsecurity.com/2026/05/27/anthropic-claude-code-security-guidance-plugin/ (deterministic-first claim)
- https://platform.claude.com/docs/en/agents-and-tools/agent-skills/best-practices (§ "Prefer scripts for deterministic operations")

---

## AP05 — Subagent fanout for parallel investigation

**Type:** subagent-fanout
**What it does:** Instead of one long Claude turn that explores N angles sequentially, the skill spawns N subagents (via the `Task` tool or an Agent-SDK loop) **in the same turn**, each focused on one aspect, each with its own context window. Results come back together and the parent agent synthesizes. The pattern works because subagents share no context — each starts fresh — so 5 parallel investigations cost 5× tokens but ~1× wall-clock time.

**Anthropic example:** `feature-dev/commands/feature-dev.md` makes this the entire architecture:

> Phase 2 — Codebase Exploration:
> "Launch 2-3 code-explorer agents in parallel. Each agent should ... Target a different aspect of the codebase (eg. similar features, high level understanding, architectural understanding, user experience, etc) ... Once the agents return, please read all files identified by agents to build deep understanding"
>
> Phase 4 — Architecture Design:
> "Launch 2-3 code-architect agents in parallel with different focuses: minimal changes (smallest change, maximum reuse), clean architecture (maintainability, elegant abstractions), or pragmatic balance (speed + quality)"
>
> Phase 6 — Quality Review:
> "Launch 3 code-reviewer agents in parallel with different focuses: simplicity/DRY/elegance, bugs/functional correctness, project conventions/abstractions"

`pr-review-toolkit/commands/review-pr.md` makes the parallel mode an explicit user-selectable option (`/pr-review-toolkit:review-pr all parallel`) and ships six specialized agents: `code-reviewer`, `code-simplifier`, `comment-analyzer`, `pr-test-analyzer`, `silent-failure-hunter`, `type-design-analyzer`.

The `skill-creator` skill in `anthropics/skills` shows the same pattern for evals: *"For each test case, spawn two subagents in the same turn — one with the skill, one without. ... Launch everything at once so it all finishes around the same time."*

**When to use it:**

- The task has clearly separable axes (security / performance / style / tests).
- Each axis benefits from a focused system prompt.
- You can afford the token cost (each subagent is a fresh context, so 5× cost is real).

**When NOT to use it:** When the angles aren't independent — if subagent B needs subagent A's findings, the fanout collapses to sequential. Don't fan out when one well-prompted main agent could do it in 1.5× the time at 0.2× the cost.

**Implementation sketch:** In a slash command's SKILL.md or command body:

```markdown
## Phase 2: Parallel exploration

Launch these subagents IN ONE TURN (don't serialize):

- Agent A (code-explorer): "Find similar features to <X> and trace their implementation"
- Agent B (code-explorer): "Map the architecture for <X area>, list 5-10 key files"
- Agent C (code-explorer): "Identify UI/test/extension patterns relevant to <X>"

When all three return, READ the files they each surface, then synthesize.
```

The subagent itself is an `agents/<name>.md` file with its own narrow tool allowlist and system prompt:

```yaml
---
name: code-architect
description: Designs feature architectures by analyzing existing codebase patterns ...
tools: Glob, Grep, LS, Read, NotebookRead, WebFetch, TodoWrite
model: sonnet
color: green
---
You are a senior software architect ...
```

**Citations:**

- https://github.com/anthropics/claude-plugins-official/blob/main/plugins/feature-dev/commands/feature-dev.md
- https://github.com/anthropics/claude-plugins-official/blob/main/plugins/pr-review-toolkit/commands/review-pr.md
- https://github.com/anthropics/skills/blob/main/skills/skill-creator/SKILL.md (§ "Spawn all runs in the same turn")

---

## AP06 — Confirmation gate before destructive actions (PreToolUse + exit-2 block)

**Type:** confirmation-gate
**What it does:** A `PreToolUse` hook intercepts a tool call **before it executes**, applies a deterministic check (or even an LLM call if cost permits), and either lets it through (exit 0) or blocks it (exit 2 with a stderr message that the harness surfaces to Claude). The blocked tool call doesn't happen; Claude must decide what to do with the feedback. Distinct from AP03 (async rewake) — this is a hard gate, not a background nudge.

**Anthropic example:** **INFERRED FROM DOCS.** The `security-guidance` plugin chose **not** to use `PreToolUse` for blocking — instead it uses `PostToolUse` + `asyncRewake`, accepting that Claude will commit the bad code first and then be forced to fix it. The design tradeoff is in the `security-guidance` README: blocking pre-commit hooks add visible latency to every Bash call, so for "best-effort assistive tool, not a guarantee" they prefer the rewake pattern. **PreToolUse-as-blocking-gate is documented in `code.claude.com/docs/en/hooks` and shipped in many community plugins** (e.g., this repo's own `intent-eval-core` permission hooks), but I did not find a public Anthropic-first-party skill that uses it as a blocking gate. The pattern is real and supported; the design preference at Anthropic appears to be "warn after, never block."

**When to use it:**

- The cost of letting the action happen is genuinely irreversible (force push to main, delete production data, send an email).
- The check is fast (< 500ms) so the user doesn't feel the gate.
- The wrong-block cost is acceptable (the user/Claude can bypass and re-issue if they're sure).

**When NOT to use it:** Anything that needs LLM reasoning to decide (use AP03 instead — let the action happen and review after, so the latency hides behind the next turn). Anything where false-blocks would frustrate the user more than the rare bad action would cost.

**Implementation sketch:**

```json
{
  "hooks": {
    "PreToolUse": [{
      "matcher": "Bash",
      "hooks": [{"type": "command", "command": "${CLAUDE_PLUGIN_ROOT}/hooks/destructive-gate.sh"}]
    }]
  }
}
```

```bash
#!/usr/bin/env bash
# destructive-gate.sh: read tool call from stdin, exit 2 to block
input=$(cat)
cmd=$(echo "$input" | jq -r '.tool_input.command')
case "$cmd" in
  *"git push --force"*|*"rm -rf /"*|*"DROP TABLE"*)
    echo "BLOCKED: $cmd looks destructive. Confirm with user before re-issuing." >&2
    exit 2 ;;
esac
exit 0
```

**Citations:**

- https://code.claude.com/docs/en/hooks (exit-code-2 semantic on PreToolUse)
- https://github.com/anthropics/claude-plugins-official/blob/main/plugins/security-guidance/README.md (§ "Limitations" — "best-effort assistive tool, not a guarantee" frames the design choice against blocking)

---

## AP07 — Two-stage agentic reasoning (investigate → self-refute)

**Type:** subagent-fanout / confirmation-gate (for LLM findings)
**What it does:** A reasoning task is split into **two sequential model calls with opposite goals**. Stage 1 (investigate) is high-recall: read every relevant file, surface every candidate finding, default to flagging. Stage 2 (self-refute) is adversarial: try to disprove each finding by reading more code. Only findings that survive stage 2 reach the user. This reproduces the dual-prompt pattern Anthropic uses to ship credibility — *"Claude re-examines each result, attempting to prove or disprove its own findings and filter out false positives."* (Anthropic news post).

**Anthropic example:** `security-guidance/hooks/review_api.py` is the textbook implementation. The investigate system prompt is ~3000 words and includes:

> "METHOD: Phase 1 — Map entry points and sinks touched by this change. ... Phase 2 — High-miss patterns ... Phase 3 — Assess. Report when you can name (a) the source, (b) the sink, (c) the path with no effective mitigation. Medium-confidence is fine — a separate adjudication pass will filter; **your job is RECALL, not precision.**" — emphasis mine; this is the explicit hand-off to stage 2.

Then stage 2:

```python
AGENTIC_REFUTE_SYSTEM = (
    "You adversarially verify security findings. You have "
    "Read/Grep over the repo. Default = SURVIVES unless you "
    "find concrete refuting evidence."
)
```

Output schema for stage 2:

```python
SURVIVED_SCHEMA = {
    "type": "object",
    "properties": {
        "survived": {"type": "array", "items": {"type": "integer"}},
        "refuted": {"type": "array", "items": {"type": "object",
            "properties": {"idx": {"type": "integer"}, "reason": {"type": "string"}}}}}}
```

Stage 1 emits N candidates by index; stage 2 returns the surviving indices and short reasons for the refuted ones. The plugin also has an optional `SG_DUAL_OR=on` mode that runs two stage-1 calls in parallel and unions findings — explicit recall/precision/cost dial.

**When to use it:** Any task where the agent generates a finding/recommendation/diff that the user will trust. Code review, security scan, compliance check, architectural critique. Especially valuable when the cost of a false positive (user loses trust) is higher than the cost of one more model call.

**When NOT to use it:** Tasks where the output is the artifact itself (writing a file, generating a chart) — there's nothing to refute. Tasks where the user adjudicates inline anyway (interactive Q&A).

**Implementation sketch:**

```python
# Stage 1: high recall
inv_prompt = """You investigate <X>. Your job is RECALL, not precision.
Medium-confidence findings are fine — a separate pass will filter them.
Return findings:[] of {filePath, category, vulnerableCode, explanation, severity, confidence}."""

findings = call_model(inv_prompt, tools=[Read, Grep, Glob], schema=FINDINGS_SCHEMA)

# Stage 2: adversarial refute
ref_prompt = f"""You adversarially verify these {len(findings)} findings.
Default = SURVIVES unless you find concrete refuting evidence in the code.
Findings (by index): {findings}"""

survived_indices = call_model(ref_prompt, tools=[Read, Grep], schema=SURVIVED_SCHEMA)["survived"]
return [findings[i] for i in survived_indices]
```

**Citations:**

- https://github.com/anthropics/claude-plugins-official/blob/main/plugins/security-guidance/hooks/review_api.py (stage 1 + stage 2 prompts in full)
- https://www.anthropic.com/news/claude-code-security ("Claude re-examines each result, attempting to prove or disprove its own findings")
- https://snyk.io/articles/anthropic-launches-claude-code-security/

---

## AP08 — Domain-sliced reference loading (load only the relevant variant)

**Type:** context-injection / progressive-disclosure
**What it does:** When a skill supports multiple variants of the same workflow — multiple cloud providers, multiple languages, multiple datasets — split the variant-specific content into one reference file per variant and have SKILL.md route to exactly one. This avoids loading 4 cloud-deploy guides when the user only cares about AWS. Anthropic's best-practices doc shows this as **"Pattern 2: Domain-specific organization"** with the BigQuery example.

**Anthropic example:**

- `mcp-builder/SKILL.md` routes to `reference/node_mcp_server.md` *or* `reference/python_mcp_server.md` depending on the user's choice — *"For TypeScript (recommended): [⚡ TypeScript Guide](./reference/node_mcp_server.md). For Python: [🐍 Python Guide](./reference/python_mcp_server.md)."*
- The official best-practices guide canonical example:

  ```text
  bigquery-skill/
  ├── SKILL.md (overview and navigation)
  └── reference/
      ├── finance.md   # revenue, billing metrics
      ├── sales.md     # opportunities, pipeline
      ├── product.md   # API usage, features
      └── marketing.md # campaigns, attribution
  ```

  And: *"When a user asks about sales metrics, Claude only needs to read sales-related schemas, not finance or marketing data. This keeps token usage low and context focused."*

The same pattern shows up in `skill-creator`'s docs guidance: *"**Domain organization**: When a skill supports multiple domains/frameworks, organize by variant ... Claude reads only the relevant reference file."*

**When to use it:** Skills with N variants of the same underlying workflow (cloud providers, ORMs, languages, dataset categories, output formats). Skills where reference content per variant exceeds ~50 lines.

**When NOT to use it:** Skills where the variants share most of their content — the duplication burden across reference files will drift. Use a unified reference with a small "platform-specific notes" section instead.

**Implementation sketch:**

```
databricks-skill/
├── SKILL.md                    # workflow + selection logic
└── reference/
    ├── delta-tables.md         # only loaded when user is on Delta
    ├── unity-catalog.md        # only loaded when user is on UC
    ├── mlflow.md               # only loaded for ML workflows
    └── jobs-api.md             # only loaded for orchestration
```

```markdown
# SKILL.md

## Decide what you're doing

The user's intent maps to one of these surfaces. Read ONLY the matching reference:

| Intent | Reference |
|---|---|
| Read/write tables, schema mgmt | reference/delta-tables.md |
| Lineage, grants, governance | reference/unity-catalog.md |
| Model training, tracking | reference/mlflow.md |
| Scheduled jobs, workflows | reference/jobs-api.md |

Do not preload others — they consume context with no benefit.
```

**Citations:**

- https://platform.claude.com/docs/en/agents-and-tools/agent-skills/best-practices (§ "Pattern 2: Domain-specific organization" and § "Skill structure")
- https://github.com/anthropics/skills/blob/main/skills/mcp-builder/SKILL.md (language-routing example)
- https://github.com/anthropics/skills/blob/main/skills/skill-creator/SKILL.md (§ "Domain organization")

---

## AP09 — MCP server as typed live-data bridge (bundle inside the plugin)

**Type:** mcp-bridge
**What it does:** When a skill needs **current** data from a system (not static documentation), bundle an MCP server with the plugin. The skill body teaches Claude *when* to call which MCP tool (`ServerName:tool_name`); the MCP server handles auth, pagination, error retries, response shaping. The MCP server is in the same plugin directory as the skill, declared in `.mcp.json` at the plugin root. This contrasts with reference-doc skills that capture API knowledge statically — MCP is for "the answer depends on what's in production right now."

**Anthropic example:** `claude-plugins-official/plugins/example-plugin/` is the canonical scaffold. `.mcp.json`:

```json
{
  "example-server": {
    "type": "http",
    "url": "https://mcp.example.com/api"
  }
}
```

And the bundled `skills/example-skill/SKILL.md` references it. The `mcp-server-dev` plugin ships three skills (`build-mcp-app`, `build-mcp-server`, `build-mcpb`) specifically to scaffold this pattern. The `mcp-builder` skill in `anthropics/skills` is the authoritative "how to design the MCP server you'll bundle" guide — covering transport choice (stdio for local, streamable-HTTP for remote), tool-naming conventions (`github_create_issue`, `github_list_repos`), and a four-phase workflow ending in 10 evaluations.

Anthropic's best-practices doc has a hard rule for skills that reference MCP tools:

> "**Always use fully qualified tool names** to avoid 'tool not found' errors. Format: `ServerName:tool_name`. Example: 'Use the BigQuery:bigquery_schema tool to retrieve table schemas.' Without the server prefix, Claude may fail to locate the tool, especially when multiple MCP servers are available."

**When to use it:**

- The skill needs **live** state (current issue list, current table schema, current run status).
- The API has > ~5 endpoints — bundling a typed wrapper saves the LLM from re-deriving call shapes.
- Auth is non-trivial (OAuth, signed requests) — the MCP server hides credential handling.

**When NOT to use it:**

- Static knowledge (API reference docs, schema specs) — that's reference files (AP01, AP08), not MCP.
- One-shot scripts that don't need typed tools — a bash script does it cheaper.
- When the user is unlikely to have credentials configured — the MCP server will fail at every invocation. Use environment gating (`requires_env`) and fallback patterns.

**Implementation sketch:** Plugin layout:

```
my-plugin/
├── .claude-plugin/plugin.json
├── .mcp.json                          # registers the server
├── skills/
│   └── work-with-foo/
│       └── SKILL.md                   # teaches Claude when/how to call Foo:* tools
└── mcp-servers/
    └── foo-server/
        ├── package.json
        └── src/index.ts               # MCP server impl (FastMCP / TS SDK)
```

`.mcp.json`:

```json
{
  "foo": {
    "type": "stdio",
    "command": "node",
    "args": ["${CLAUDE_PLUGIN_ROOT}/mcp-servers/foo-server/dist/index.js"]
  }
}
```

`SKILL.md` references tools with the full prefix:

```markdown
## Querying Foo

Use Foo:list_records to enumerate. Filter with Foo:search_records.
Never invent endpoint URLs — every Foo call MUST go through one of the
Foo:* tools listed in the MCP server's tool list.
```

**Citations:**

- https://github.com/anthropics/claude-plugins-official/blob/main/plugins/example-plugin/.mcp.json
- https://github.com/anthropics/skills/blob/main/skills/mcp-builder/SKILL.md
- https://platform.claude.com/docs/en/agents-and-tools/agent-skills/best-practices (§ "MCP tool references")

---

## AP10 — Cross-skill composition via subagent invocation

**Type:** cross-skill-composition
**What it does:** A command/skill in plugin A invokes a subagent that itself uses a skill from plugin B. The skills don't import each other; they compose at runtime through the agent loop — the parent's command says "spawn an agent with these tools and this prompt" and that agent autonomously discovers and loads the relevant child skill. Anthropic's first-party plugins compose this way constantly: the `feature-dev` workflow spawns `code-explorer`, `code-architect`, `code-reviewer` subagents that share the same conversation harness but have independent system prompts.

**Anthropic example:**

- `feature-dev/commands/feature-dev.md` orchestrates `code-explorer` (Phase 2), `code-architect` (Phase 4), `code-reviewer` (Phase 6) — each is a separate `agents/<name>.md` file with its own tool allowlist and frontmatter (`model: sonnet`, `color: green`).
- `pr-review-toolkit/commands/review-pr.md` orchestrates six specialized agents (`code-reviewer`, `code-simplifier`, `comment-analyzer`, `pr-test-analyzer`, `silent-failure-hunter`, `type-design-analyzer`) selectable by user argument.
- `claude-md-management` plugin uses its own pair of skills (`claude-md-improver`, `revise-claude-md`) invoked through `commands/`.

The composition is **lexical, not API**: the parent command's body uses imperative prose ("Launch 3 code-reviewer agents in parallel") and the harness's `Task` tool resolves the named agent. Same skill discovery / metadata-tier mechanism (AP01) — agents are discovered exactly like skills.

There's a key sub-pattern in the `code-reviewer` agent worth lifting: it adopts the **confidence-score filter** to make composition safe:

```markdown
## Issue Confidence Scoring
Rate each issue from 0-100:
- 0-25: Likely false positive
- 26-50: Minor nitpick
- 51-75: Valid but low-impact
- 76-90: Important issue requiring attention
- 91-100: Critical bug or explicit CLAUDE.md violation
**Only report issues with confidence ≥ 80**
```

So when a parent command fans out to N reviewers, each one self-filters at the same threshold, and the parent's aggregation logic just unions the results — no scoring conflicts.

**When to use it:**

- The parent workflow has phases that benefit from distinct expertise / different system prompts.
- The child agents are reusable across multiple parents (DRY — don't inline the system prompt).
- You want narrow tool allowlists per phase (the architect agent gets Read/Grep/WebFetch, no Edit).

**When NOT to use it:**

- One-off prompts that no other workflow will reuse — inline them.
- When the agents need to share intermediate state — agents are isolated by design. Use the file system (have one agent write to `./reviews/architect.md` and the next read it) or pass results through the parent.

**Implementation sketch:** Parent command:

```markdown
# /my-workflow

## Phase 1
Launch a Task with subagent_type: my-explorer
prompt: "Map the codebase for <thing>. Return 5-10 file paths."

## Phase 2
Read the files the explorer surfaced.
Launch THREE Tasks in one turn with subagent_type: my-reviewer
prompts: ["focus on X", "focus on Y", "focus on Z"]

## Phase 3
Synthesize the three review reports. Surface critical-only to user.
```

Child agent `agents/my-reviewer.md`:

```yaml
---
name: my-reviewer
description: Reviews <X> against <Y> rubric. Returns findings with confidence scores.
tools: Read, Grep, Glob
model: sonnet
---
You are a domain expert in <X>...
Only report findings with confidence ≥ 80.
Output as: {severity, file, line, finding, confidence, fix}.
```

**Citations:**

- https://github.com/anthropics/claude-plugins-official/tree/main/plugins/feature-dev/agents
- https://github.com/anthropics/claude-plugins-official/blob/main/plugins/pr-review-toolkit/commands/review-pr.md
- https://github.com/anthropics/claude-plugins-official/blob/main/plugins/pr-review-toolkit/agents/code-reviewer.md (confidence-score filter)

---

## Cross-cutting design rules

These are not patterns but principles Anthropic-shipped skills consistently follow. Lift them all.

| Rule | Source | Why |
|---|---|---|
| **Always third-person in `description`** | best-practices.md | Description is injected into system prompt; first-person ("I can help...") causes discovery problems |
| **Description includes both WHAT and WHEN** | best-practices.md | Triggering is description-driven; "Use when X mentions Y" wording materially improves recall |
| **Be slightly "pushy" in descriptions** | skill-creator SKILL.md | Quote: *"currently Claude has a tendency to 'undertrigger' skills ... please make the skill descriptions a little bit 'pushy'"* |
| **Gerund form names** (`processing-pdfs`) | best-practices.md | Clear activity description; consistent across skill library |
| **≤500 lines in SKILL.md body** | best-practices.md | Above this, split via AP01 |
| **References one level deep** | best-practices.md | Quote: *"Claude may partially read files when they're referenced from other referenced files"* — nested refs lose content |
| **Forward slashes in all paths** | best-practices.md | Windows-style `\` breaks on Unix |
| **Don't punt to Claude in scripts** | best-practices.md | Scripts should handle errors (return default, log, retry) — not raise and hope Claude figures it out |
| **No "voodoo constants"** | best-practices.md | Document every magic number with the reasoning that justified it |
| **Plan → validate → execute for batch ops** | best-practices.md | Intermediate JSON file gives a verifiable checkpoint before destructive changes (mirrored in security-guidance's two-stage refute) |
| **Build evals BEFORE writing docs** | best-practices.md | Skills should solve real failures, not anticipated ones |
| **Iterate with Claude-A-builds / Claude-B-uses** | best-practices.md | Different Claude instances expose blind spots |
| **Confidence threshold ≥ 80 for review-style agents** | pr-review-toolkit code-reviewer.md | Filters noise; makes parallel-agent composition (AP10) safe |

---

## Gaps in this research

Where I wanted Anthropic-first-party source and found only marketing copy or community examples:

1. **Anthropic blog post on `security-guidance` architecture** — the `anthropic.com/news/claude-code-security` page is marketing-tier and does not describe the three-layer design. The technical detail in this catalog comes from the plugin's `README.md`, `hooks.json`, and `review_api.py` — those are the source-of-truth artifacts.
2. **PreToolUse-as-blocking-gate (AP06)** — I found no first-party Anthropic skill using it. The pattern is documented in `code.claude.com/docs/en/hooks` but the security plugin chose `PostToolUse` + `asyncRewake` instead. **Worth treating as "documented, supported, but Anthropic doesn't lead with it"** — interpret accordingly when designing the Databricks skill.
3. **Anthropic's published evaluation harness for skills** — `best-practices.md` shows the eval JSON schema but says *"There is not currently a built-in way to run these evaluations."* The `anthropics/skills` repo's `skill-creator/eval-viewer/` directory implements one in-process — that's the closest we get to an Anthropic-blessed runner.
4. **MCP server inside `security-guidance`** — `security-guidance` does NOT bundle an MCP server. AP09 examples come from the smaller `example-plugin` and `mcp-server-dev` plugins; no major first-party plugin demonstrates a production MCP-server-bundled-with-skills surface. The `mcp-builder` skill teaches you to build them, but you have to look at community plugins (or this repo's own `plugins/productivity/plane/`) for end-to-end MCP-bundled-plugin reality.
5. **Cross-plugin composition** (AP10 across plugin boundaries, not just within one plugin) — I found composition only within a single plugin's `agents/` directory. Cross-plugin subagent invocation works (Claude can discover any installed agent) but no Anthropic-shipped workflow exercises it. **Inferred-but-supported.**

---

## Recommended pattern subset for the Databricks rebuild

Without prejudging the rebuild scope, here's the minimum-viable architectural surface a Databricks skill pack should pick up:

1. **AP01 + AP08** (progressive disclosure + domain-sliced references) — Databricks has at least four distinct surfaces (Delta tables, Unity Catalog, MLflow, Jobs). One SKILL.md per surface or one SKILL.md routing to per-surface references; either way, don't preload all four.
2. **AP09** (MCP server) — Databricks has a stable REST API and notebook/job runtime state that needs live access; static reference docs alone will miss the "what's currently deployed" use case.
3. **AP04** (script-vs-LLM separation) — deterministic checks (cluster exists, table schema present, job ID valid, notebook path resolves) belong in scripts. LLM reasoning belongs at "design this notebook" / "review this Delta migration" level.
4. **AP02 + AP03** (hooks + asyncRewake) — IF the skill wants to enforce things like "validate the SQL against the table schema before running it" without blocking the user. Optional.
5. **AP07** (two-stage agentic) — IF the skill ships a Databricks-specific cost/security/governance reviewer (e.g., "does this notebook leak PII through cluster logs?"). The investigate→refute pattern is the right shape.
6. **AP10** (subagent composition) — IF the skill spans enough phases (design → implement → review) to warrant separate system prompts per phase.

Patterns to skip unless there's specific demand:

- **AP05** (subagent fanout) — overkill for most Databricks workflows; users typically pick one surface and dig in.
- **AP06** (PreToolUse blocking) — Anthropic itself doesn't lead with this. Use only if the cost of letting an action happen is genuinely irreversible (e.g., dropping a production Delta table).

---

## Bibliography (full URL list)

**Primary — Anthropic GitHub source**

- https://github.com/anthropics/skills
- https://github.com/anthropics/skills/blob/main/skills/skill-creator/SKILL.md
- https://github.com/anthropics/skills/blob/main/skills/mcp-builder/SKILL.md
- https://github.com/anthropics/claude-plugins-official
- https://github.com/anthropics/claude-plugins-official/tree/main/plugins/security-guidance
- https://github.com/anthropics/claude-plugins-official/blob/main/plugins/security-guidance/hooks/hooks.json
- https://github.com/anthropics/claude-plugins-official/blob/main/plugins/security-guidance/hooks/patterns.py
- https://github.com/anthropics/claude-plugins-official/blob/main/plugins/security-guidance/hooks/review_api.py
- https://github.com/anthropics/claude-plugins-official/blob/main/plugins/security-guidance/README.md
- https://github.com/anthropics/claude-plugins-official/blob/main/plugins/security-guidance/.claude-plugin/plugin.json
- https://github.com/anthropics/claude-plugins-official/tree/main/plugins/feature-dev
- https://github.com/anthropics/claude-plugins-official/blob/main/plugins/feature-dev/commands/feature-dev.md
- https://github.com/anthropics/claude-plugins-official/blob/main/plugins/feature-dev/agents/code-architect.md
- https://github.com/anthropics/claude-plugins-official/tree/main/plugins/pr-review-toolkit
- https://github.com/anthropics/claude-plugins-official/blob/main/plugins/pr-review-toolkit/commands/review-pr.md
- https://github.com/anthropics/claude-plugins-official/blob/main/plugins/pr-review-toolkit/agents/code-reviewer.md
- https://github.com/anthropics/claude-plugins-official/tree/main/plugins/example-plugin
- https://github.com/anthropics/claude-plugins-official/tree/main/plugins/hookify
- https://github.com/anthropics/claude-plugins-official/tree/main/plugins/mcp-server-dev
- https://github.com/anthropics/claude-plugins-official/tree/main/plugins/claude-md-management
- https://github.com/anthropics/claude-code-security-review

**Primary — Anthropic docs**

- https://platform.claude.com/docs/en/agents-and-tools/agent-skills/overview
- https://platform.claude.com/docs/en/agents-and-tools/agent-skills/best-practices
- https://code.claude.com/docs/en/skills
- https://code.claude.com/docs/en/hooks
- https://www.anthropic.com/engineering/equipping-agents-for-the-real-world-with-agent-skills
- https://www.anthropic.com/news/claude-code-security
- https://resources.anthropic.com/hubfs/The-Complete-Guide-to-Building-Skill-for-Claude.pdf

**Secondary — coverage of the security-guidance release (corroborates layered design)**

- https://www.helpnetsecurity.com/2026/05/27/anthropic-claude-code-security-guidance-plugin/
- https://snyk.io/articles/anthropic-launches-claude-code-security/
- https://venturebeat.com/security/anthropic-claude-code-security-reasoning-vulnerability-hunting
- https://cybersecuritynews.com/free-security-plugin-for-claude-code/

**Secondary — community deep-dives on skill architecture**

- https://leehanchung.github.io/blogs/2025/10/26/claude-skills-deep-dive/
- https://www.mindstudio.ai/blog/claude-code-skills-architecture-progressive-context-loading
- https://github.com/travisvn/awesome-claude-skills
