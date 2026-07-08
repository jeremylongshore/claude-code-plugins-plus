# mnemos verify — efficacy harness

Two tests, two numbers, both repeatable.

## Retrieval (cheap, fast)

```
mnemos verify retrieval
```

Reads `verify/retrieval.yaml`. For each probe, runs the listed queries
through the live store and checks whether the named memory appears in
the top-K hits. Reports precision@K. Failures point at ranking, tags, or
content — the memory exists but the trigger context can't reach it.

Add a fixture entry every time you save a high-importance memory:

```yaml
- id: 01ABCDEF...
  title: short human label
  queries:
    - "the situation phrasing that should surface this memory"
    - "another way the agent might describe the same trigger"
  expect_in_top: 5
```

## Behavior (expensive, slow, real tokens)

```
mnemos verify behavior
```

Reads `verify/behavior.yaml`. For each scenario, runs the trigger prompt
N times under each arm (mnemos on, mnemos off) and counts how often the
agent's transcript matches the assertion. Lift = pass_rate(on) -
pass_rate(off). A correction memory that produces zero lift is reaching
the agent but not changing its conduct.

The arms are command templates. The default uses
`claude -p ... --mcp-config <on|off>.json --strict-mcp-config` so the
two arms see different MCP configurations; customize to match your CLI.
`{{trigger}}` is substituted per run.

## Both

```
mnemos verify all
```

Run together pre-release. Retrieval can run on every commit; behavior is
slow enough that nightly or per-release is the right cadence.
