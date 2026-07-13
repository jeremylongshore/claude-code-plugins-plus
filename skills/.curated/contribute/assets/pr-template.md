# PR description template

Use AFTER the maintainer has approved the design issue (or when the upstream repo's flow expects a direct PR).

```markdown
## What

{{one-paragraph summary of the change}}

Closes #{{issue_number}}.

## Why

{{the problem this solves, in the upstream's voice — usually paraphrased from the issue}}

## How

- {{key change 1}}
- {{key change 2}}
- {{key change 3}}

## Tests

`​`​`
{{paste of test runner output — pytest summary, jest, cargo test, etc.}}
`​`​`

Coverage: {{X%}} (if reported)

## Screenshots / recordings

{{UI changes only — links or attached media}}

## Checklist

- [ ] Tests pass locally
- [ ] Lint passes
- [ ] CONTRIBUTING.md guidelines followed
- [ ] CLA signed (if required)
- [ ] AI disclosure (if repo's PR template asks for it)

## Risk

{{files touched count, rough LOC, known caveats, follow-up TODOs}}
```

Adjust headers + tone to match the upstream repo's existing PR template (read `.github/PULL_REQUEST_TEMPLATE.md` if present).

**Always show this to Jeremy for approval before posting** — never `gh pr create` autonomously.
