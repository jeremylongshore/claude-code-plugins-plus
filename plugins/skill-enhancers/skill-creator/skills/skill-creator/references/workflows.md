# Workflow Patterns

Reference guide for choosing the right workflow pattern when creating skills.

---

## Sequential

Fixed steps executed in order. Best for deterministic tasks with predictable flow.

**When to use:** Data processing pipelines, file transformations, deployment scripts.

```
Step 1 -> Step 2 -> Step 3 -> Done
```

**Example:** Generate release notes — parse commits, group by type, format output, write file.

---

## Conditional

Branch based on input or detected state. Best when different scenarios need different handling.

**When to use:** Error diagnosis, multi-format support, environment-specific logic.

```
Detect input type
  ├── Type A -> Path A steps
  ├── Type B -> Path B steps
  └── Unknown -> Error handling
```

**Example:** File converter — detect format (JSON/YAML/TOML), apply appropriate parser, output in target format.

---

## Wizard

Interactive multi-step gathering with user input between phases. Best for configuration or personalized output.

**When to use:** Project scaffolding, skill creation, configuration generation.

```
Ask question 1 -> Process answer -> Ask question 2 -> ... -> Generate output
```

**Example:** Skill Creator Step 1 — ask name, purpose, tools, complexity, then generate.

---

## Plan-Validate-Execute

Generate a plan, validate feasibility, then execute. Best when operations are hard to reverse.

**When to use:** Database migrations, infrastructure changes, bulk refactoring.

```
Analyze current state -> Generate plan -> Validate plan -> Execute -> Verify
```

**Example:** Database migration — analyze schema diff, generate migration SQL, dry-run validate, execute, verify integrity.

---

## Feedback Loop

Iterate until quality threshold is met. Best for optimization and creative tasks.

**When to use:** Description tuning, code quality improvement, test coverage gaps.

```
Generate -> Evaluate -> Score -> (below threshold?) -> Modify -> Re-evaluate
```

**Example:** Description optimization — generate description, test trigger accuracy, if <90% modify and retry.

---

## Search-Analyze-Report

Explore a codebase or dataset, analyze findings, produce structured report. Best for audit and discovery tasks.

**When to use:** Security audits, dependency analysis, code review, documentation gaps.

```
Search (Glob/Grep) -> Collect findings -> Analyze patterns -> Generate report
```

**Example:** Security scanner — search for SQL injection patterns, analyze severity, generate prioritized report.

---

## Choosing a Pattern

| Task Type | Recommended Pattern |
|-----------|-------------------|
| Build/generate something | Sequential |
| Fix/diagnose something | Conditional |
| Configure/set up | Wizard |
| Migrate/transform | Plan-Validate-Execute |
| Optimize/improve | Feedback Loop |
| Audit/review | Search-Analyze-Report |

Most skills combine patterns. A skill creator uses Wizard (gather info) + Sequential (write files) + Feedback Loop (validate and iterate).
