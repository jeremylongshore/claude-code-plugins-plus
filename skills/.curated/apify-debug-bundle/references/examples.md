# Apify Debug Bundle — Worked Examples

End-to-end walkthroughs showing the debug-bundle workflow applied to real
failure scenarios. Each example maps to a step in
[implementation.md](implementation.md).

## Example 1: A run that finished with status `FAILED`

You have a run ID (`abc123DEF`) that ended in failure and you want the full
picture before opening a ticket.

```bash
export APIFY_TOKEN="apify_api_..."
./apify-debug-bundle.sh abc123DEF
# → Collecting debug info for run abc123DEF...
# → Bundle created: apify-debug-20260717-142530.tar.gz
# → Attach this file to your Apify support ticket.
```

Unpack and inspect the tail of the log to find the stack trace:

```bash
tar -xzf apify-debug-20260717-142530.tar.gz
tail -40 apify-debug-20260717-142530/run-log.txt
```

## Example 2: "It worked yesterday" — compare against a good run

The Actor succeeded last run but fails now with the same input. Diff the two
to surface what changed (build number, memory, timeout, request stats):

```typescript
await compareRuns('goodRun789', 'badRun456');
// === Run Comparison ===
// Field                     | Success         | Failed
// ------------------------------------------------------------
// status                    | SUCCEEDED       | FAILED <--
// buildNumber               | 0.1.7           | 0.1.8 <--
// options.memoryMbytes      | 2048            | 2048
// stats.requestsFailed      | 0               | 143 <--
```

The `<--` markers point straight at the regression: a new build (0.1.8) that
now fails 143 requests.

## Example 3: Empty dataset investigation

The run reports `SUCCEEDED` but produced zero items. Pull the run summary and
dataset stats with the SDK:

```typescript
const { run } = await investigateRun('emptyRun321');
// Dataset items: 0
```

Zero items on a successful run points at the Actor's own logic — check the
`failedRequestHandler` in the Actor code (see the Error Handling table in
SKILL.md).

## Example 4: Live-tailing a hung run

A run has been `RUNNING` far longer than expected and the final log is not yet
available. Stream it live instead:

```bash
RUN_ID="hangingRun999" ./tail-log.sh
# ...streams log lines every 2s until you Ctrl-C...
```

Watch for the last line before the stall — repeated retry/timeout lines usually
indicate a proxy or target-site block rather than an Actor bug.
