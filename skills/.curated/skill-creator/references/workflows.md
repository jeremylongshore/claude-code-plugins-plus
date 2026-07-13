# Skill Workflow Patterns

Reference for common workflow patterns in Claude Agent Skills.
Source: Anthropic best practices, official skill-creator patterns.

---

## Sequential Workflow

Steps execute in fixed order. Simplest pattern.

```markdown
## Instructions

### Step 1: Gather Input
Read the target file and extract relevant data.

### Step 2: Process
Transform the data according to the rules.

### Step 3: Output
Write the result to the specified location.
```

**Best for**: File conversion, data transformation, build scripts.
**Degrees of freedom**: Low (fixed steps, predictable output).

---

## Conditional Workflow

Branch execution based on input or context.

```markdown
## Instructions

### Step 1: Analyze Input
Determine the type of input:
- If markdown file: proceed to Step 2a
- If HTML file: proceed to Step 2b
- If unknown: ask user with AskUserQuestion

### Step 2a: Process Markdown
Convert markdown using pandoc conventions...

### Step 2b: Process HTML
Parse HTML and extract content...

### Step 3: Output
Write the converted result.
```

**Best for**: Skills handling multiple input types, multi-purpose tools.
**Degrees of freedom**: Medium (defined branches, flexible within each).

---

## Wizard-Style Workflow

Interactive multi-step gathering using AskUserQuestion.

```markdown
## Instructions

### Step 1: Gather Requirements
Ask the user:
1. What is the project name?
2. Which framework? (React / Vue / Svelte)
3. Include testing? (Yes / No)

Use AskUserQuestion for each decision point.

### Step 2: Generate Based on Choices
Based on responses, generate the appropriate scaffold.

### Step 3: Verify
Show the user what was created and confirm.
```

**Best for**: Complex setup, project scaffolding, configuration generation.
**Degrees of freedom**: Medium (user drives decisions).

---

## Plan-Validate-Execute

Verifiable intermediates with feedback loops. Anthropic's recommended pattern for high-stakes tasks.

```markdown
## Instructions

### Step 1: Plan
Analyze the current state and create an execution plan.
Show the plan to the user before proceeding.

### Step 2: Validate Plan
Check each planned step for:
- Prerequisites met
- No conflicts with existing state
- Reversibility if something goes wrong

### Step 3: Execute
Execute each step, verifying success before proceeding:
1. Execute step → verify → continue
2. If verification fails → rollback → report

### Step 4: Report
Summarize what was done, what succeeded, and any issues.
```

**Best for**: Deployment, migration, refactoring, any destructive operation.
**Degrees of freedom**: Low (strict verification at each stage).

---

## Feedback Loop Workflow

Iterative refinement until quality threshold met.

```markdown
## Instructions

### Step 1: Generate Initial Output
Create the first draft/version.

### Step 2: Evaluate Quality
Check against criteria:
- [ ] Criterion A met?
- [ ] Criterion B met?
- [ ] Criterion C met?

### Step 3: Iterate if Needed
If any criteria not met:
1. Identify the gap
2. Refine the output
3. Return to Step 2

Maximum 3 iterations. If still not passing, report issues.

### Step 4: Finalize
Output the final version with quality report.
```

**Best for**: Content generation, code quality, optimization tasks.
**Degrees of freedom**: Medium (defined criteria, flexible refinement).

---

## Search-Analyze-Report

Codebase exploration with structured analysis.

```markdown
## Instructions

### Step 1: Search
Use Glob and Grep to find relevant files:
- Pattern: `**/*.py`
- Search: `def.*deprecated`

### Step 2: Analyze
For each finding:
- Context (what file, what function)
- Severity (critical / warning / info)
- Recommended action

### Step 3: Report
Generate structured report:

| File | Line | Issue | Severity | Fix |
|------|------|-------|----------|-----|
| ... | ... | ... | ... | ... |
```

**Best for**: Code review, security audit, dependency analysis, codebase understanding.
**Degrees of freedom**: High (Claude decides what's relevant).

---

## Checklist Workflow

Copy-pasteable progress tracking for complex multi-step processes. Claude checks items off as it completes them.

```markdown
## Instructions

### Progress Checklist
- [ ] Step 1: Gather requirements
- [ ] Step 2: Validate inputs
- [ ] Step 3: Execute primary operation
- [ ] Step 4: Run verification checks
- [ ] Step 5: Generate report

### Step 1: Gather Requirements
{{GATHER_INSTRUCTIONS}}
Update checklist: mark Step 1 complete.

### Step 2: Validate Inputs
{{VALIDATION_INSTRUCTIONS}}
Update checklist: mark Step 2 complete.

### Step 3: Execute
{{EXECUTION_INSTRUCTIONS}}
Update checklist: mark Step 3 complete.

### Step 4: Verify
{{VERIFICATION_INSTRUCTIONS}}
Update checklist: mark Step 4 complete.

### Step 5: Report
Show completed checklist with summary of each step's outcome.
```

**Best for**: Multi-step processes where progress visibility matters (releases, migrations, audits).
**Degrees of freedom**: Low to Medium (defined steps, flexible execution within each).

---

## Choosing the Right Pattern

| If your skill... | Use this pattern |
|-----------------|-----------------|
| Does one thing in fixed order | Sequential |
| Handles different input types | Conditional |
| Needs user decisions | Wizard-Style |
| Does something risky/irreversible | Plan-Validate-Execute |
| Needs iterative quality | Feedback Loop |
| Explores and reports on code | Search-Analyze-Report |
| Needs visible progress tracking | Checklist |
| Combines multiple concerns | Compose patterns together |

Patterns can be composed. A deployment skill might use:
Wizard (gather config) → Plan-Validate-Execute (deploy) → Feedback Loop (health check).
