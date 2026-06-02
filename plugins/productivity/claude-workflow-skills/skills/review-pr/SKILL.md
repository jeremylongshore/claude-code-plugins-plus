---
name: review-pr
description: Reviews an open pull request against coding standards, security, and test coverage, then posts a structured review comment and either approves or requests changes. Use when the user says review this PR, check the PR, look at PR #N, or review pull request.
allowed-tools: Read Glob Grep Bash
disable-model-invocation: true
argument-hint: "[PR-number]"
---

# Review PR

PR: !`gh pr view --json number,title --jq '"#\(.number): \(.title)"' 2>/dev/null || echo "none"`

Fetches a pull request diff, evaluates it against the project's coding standards, security posture,
and test coverage, then posts a structured review and either approves or requests changes.

## Step 0: Pre-flight check

```bash
gh auth status 2>&1 || { echo "ERROR: gh is not authenticated. Run: gh auth login"; exit 1; }
```

Determine the PR to review. If the user named a number, use it. Otherwise default to the current
branch's open PR:

```bash
gh pr view --json number,title 2>/dev/null || echo "No PR for current branch"
```

If no PR is found, stop and ask the user which PR number to review.

## Step 1: Fetch PR context

```bash
gh pr view <number> --json number,title,body,headRefName,baseRefName,author,labels,commits,files
```

```bash
gh pr diff <number>
```

Also read the project files to understand standards and conventions:

- `README.md` — stated purpose and feature set
- `CLAUDE.md` — current decisions and context, if present
- `~/.claude/CLAUDE.md` — personal development standards already loaded in context

## Step 2: Evaluate the diff

Review the diff against the following criteria. Note findings — positive and negative — for each:

### Correctness

- Does the change do what the PR description says?
- Are there logic errors, off-by-one errors, or incorrect conditionals?
- Are edge cases handled?

### Coding standards (from `~/.claude/CLAUDE.md`)

- Scripts use correct shebang and follow the Bash Style Guide
- Terminal output uses pfb (Bash) or Rich (Python) with correct visual hierarchy
- Functions have Google-style documentation headers
- No hardcoded configuration — environment variables with `.env.template`
- Error messages are actionable (say what went wrong and what to do)

### Security

- No secrets, credentials, or tokens in code or comments
- External input validated at system boundaries
- No command injection risks (unquoted variables in shell, unsanitised input in queries)
- File paths handled safely (no unquoted expansions, no `eval` on external data)

### Test coverage

- Are new code paths exercised by tests?
- Do existing tests still pass (check for any test files modified or added)?
- Are failure paths tested, not just happy paths?

### Documentation and markdown

- New or changed markdown passes markdownlint conventions (blank lines around blocks, language on
  code fences, line length ≤ 120)
- Public interfaces, scripts, and functions are documented

### Scope

- Does the PR stay within its stated scope?
- Are there unrelated changes bundled in?

## Step 3: Draft the review body

Write a structured review using this format:

```markdown
## Summary

<1–2 sentences on overall quality and whether the PR achieves its stated goal.>

## Findings

### Must fix

- <issue> — <file:line if applicable> — <what to do>

### Suggestions

- <non-blocking improvement or style note>

### Looks good

- <specific thing done well — always include at least one>

## Verdict

<Approve / Request changes> — <one sentence reason>
```

If there are no must-fix items, the verdict is **Approve**.
If there is at least one must-fix item, the verdict is **Request changes**.

## Step 4: Post the review

For an approval:

```bash
gh pr review <number> --approve --body "$(cat <<'REVIEW'
<review body>

🤖 Generated with [claude-workflow-skills:review-pr](https://github.com/ali5ter/claude-workflow-skills) on behalf of [Alister](https://github.com/ali5ter)
REVIEW
)"
```

For a request-changes review:

```bash
gh pr review <number> --request-changes --body "$(cat <<'REVIEW'
<review body>

🤖 Generated with [claude-workflow-skills:review-pr](https://github.com/ali5ter/claude-workflow-skills) on behalf of [Alister](https://github.com/ali5ter)
REVIEW
)"
```

After posting, output the review verdict and a link to the PR for the user.
