# Integration Gating

When to run integration tests live vs. via VCR replay, how to inject secrets, budgeting cost-per-run, and the scheduled re-record pattern. Pairs with the recording workflow in `langchain-local-dev-loop` (F23).

## Three integration-test modes

| Mode | When it runs | Secrets needed? | Cost | Purpose |
|------|--------------|-----------------|------|---------|
| **replay** (`VCR_MODE=none`) | Every PR with `run-integration` label | No | $0 | Regression guard on chain wiring, provider API shape |
| **record-once** (`VCR_MODE=once`) | Nightly cron, manual dispatch | Yes (provider keys) | ~$0.05–0.50 per run | Detect provider drift; refresh cassettes |
| **live** (`VCR_MODE=all`) | Never in CI automatically | Yes | Full API cost | Debug-only; use for incident response |

**Default for PRs: replay.** Contributors without provider keys must be able to run integration locally against cassettes. If a contributor needs to change a prompt and therefore the cassette, they record locally (see F23) and commit the new cassette file.

## Gating pattern

```yaml
integration:
  if: >
    github.event_name == 'schedule' ||
    github.event_name == 'workflow_dispatch' ||
    contains(github.event.pull_request.labels.*.name, 'run-integration')
```

Three triggers:

1. **Nightly cron** — runs record-once mode, detects provider drift, auto-commits refreshed cassettes if tests still pass.
2. **Manual dispatch** (`workflow_dispatch`) — for debugging a specific PR or validating a big refactor.
3. **PR label** (`run-integration`) — contributor explicitly opts in. Replay mode, no keys needed.

Default PR runs do **not** run integration at all — unit + lint + eval are the required gates.

## Secret injection (live / record-once only)

Store provider keys as repository secrets (Settings → Secrets and variables → Actions). Inject them at the job level only when needed:

```yaml
- name: Inject provider keys (nightly only)
  if: github.event_name == 'schedule' || github.event.inputs.run_live == 'true'
  run: |
    echo "ANTHROPIC_API_KEY=${{ secrets.ANTHROPIC_API_KEY }}" >> "$GITHUB_ENV"
    echo "OPENAI_API_KEY=${{ secrets.OPENAI_API_KEY }}" >> "$GITHUB_ENV"
```

Do **not** inject keys into the replay job. If replay somehow hits the network, you want a 401, not a charge.

For forked-PR safety: GitHub Actions does **not** expose secrets to workflows triggered by `pull_request` from forks. The label-gated integration job will silently run without keys in that case — and VCR replay mode works without keys, so this is fine. Live mode from a fork PR would require `pull_request_target`, which has security implications; do not enable it casually.

## Cost budget

Back-of-envelope for a 100-test integration suite running nightly in record-once mode:

| Provider | Avg tokens/request | Cost/request | 100 tests |
|----------|-------------------|--------------|-----------|
| Claude Sonnet 4.6 | 1K in + 500 out | ~$0.013 | $1.30 |
| GPT-4o | 1K in + 500 out | ~$0.008 | $0.80 |
| Gemini 2.5 Pro | 1K in + 500 out | ~$0.005 | $0.50 |

So a full nightly re-record is **~$2.60 per night** across three providers. $80/month. Flag this to whoever owns the GHA bill before turning on the cron.

If budget is tight:

- Run re-record weekly, not nightly (cut cost by 7×).
- Sample — re-record 20 cassettes/night on rotation, not all 100.
- Only re-record cassettes older than N days.

## The record-once flip

`VCR_MODE=once` means: for each test, if a cassette exists use it; if not, call live and record. This is the cheap nightly drift check: cassettes that still match their live counterpart do not re-record; cassettes that drifted fail, re-record, and commit. The follow-up PR review surfaces the drift for human review.

Auto-commit only if *all* tests pass after re-record — otherwise you are laundering regressions through the nightly bot:

```yaml
- name: Commit re-recorded cassettes (nightly only)
  if: github.event_name == 'schedule' && success()
  run: |
    if ! git diff --quiet tests/integration/cassettes/; then
      git config user.name "ci-record-bot"
      git config user.email "ci@example.com"
      git add tests/integration/cassettes/
      git commit -m "chore(ci): re-record VCR cassettes (nightly drift)"
      git push
    fi
```

The `success()` check is critical. A failing nightly should page, not self-heal.

## P05 and the determinism mirage

Anthropic `temperature=0` is **not** greedy decoding — it still nucleus-samples. So a cassette recorded at `temp=0` captures one of many valid completions. When the model drifts, replay-time comparison against that one captured completion will flake.

Two mitigations, both cheap:

1. Match VCR on `body` structural fields only (`method`, `scheme`, `host`, `port`, `path`, `query`) — not on response content. The default match config handles this.
2. For tests that assert on *output content*, own a fake-model fixture instead (see F23). VCR is for testing provider-API shape and HTTP plumbing, not for asserting on prompt-output stability. That is the eval harness's job.

## Cross-references

- Recording cassettes locally — `langchain-local-dev-loop` (F23)
- Secret-scan of committed cassettes — [Pre-Commit Hooks](pre-commit-hooks.md)
- Eval-regression (the right tool for output-stability guarding) — [Eval Regression Gate](eval-regression-gate.md)
