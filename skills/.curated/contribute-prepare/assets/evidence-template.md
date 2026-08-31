# Evidence summary template

Use this local draft block in a review packet. Do not include secrets or raw
environment output.

~~~~markdown
## Evidence

**Repository state**: `{{commit_sha}}` on `{{branch}}`, based on
`{{upstream}}@{{upstream_sha}}`

**Tests**:

~~~text
{{exact test command and result summary}}
~~~

**Lint and type checking**:

~~~text
{{exact lint/typecheck command and result summary}}
~~~

**Manual verification**:

- {{step 1}}
- {{step 2}}

Local log: `$CONTRIBUTE_STATE_DIR/test-logs/{{run_filename}}`
~~~~
