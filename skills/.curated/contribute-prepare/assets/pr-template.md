# Pull-request description template

Prepare this draft only after the upstream's required design or issue workflow
is satisfied.

~~~~markdown
## What

{{one-paragraph summary}}

Closes #{{issue_number}}.

## Why

{{evidence-backed problem statement}}

## How

- {{key change 1}}
- {{key change 2}}
- {{explicit non-goal}}

## Tests

~~~text
{{exact test command and result summary}}
~~~

## Screenshots or recordings

{{UI changes only; otherwise "Not applicable"}}

## Checklist

- [ ] Tests pass locally
- [ ] Linters and type checks pass
- [ ] Repository contribution policy followed
- [ ] CLA/DCO handled when required
- [ ] AI disclosure included when required

## Risk

{{changed-file count, rough LOC, caveats, and follow-up work}}
~~~~

Match the upstream's existing pull-request template and tone. This asset creates
a local draft; `contribute-publish` owns any GitHub mutation.
