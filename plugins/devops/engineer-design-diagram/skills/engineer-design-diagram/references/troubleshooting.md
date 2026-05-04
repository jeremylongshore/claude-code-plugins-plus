# Troubleshooting

Known issues and recovery paths.

## Table of Contents

- [iOS Safari Rendering](#ios-safari-rendering)
- [Large Graphs (>50 nodes)](#large-graphs-50-nodes)
- [Fingerprint Schema Drift](#fingerprint-schema-drift)
- [DCI Output Truncated](#dci-output-truncated)
- [LLM Produces Overlapping Layout](#llm-produces-overlapping-layout)
- [${CLAUDE_PLUGIN_DATA} Not Set](#claude_plugin_data-not-set)
- [Unknown Stack Trace Format](#unknown-stack-trace-format)

## iOS Safari Rendering

**Symptom:** diagram renders blank or truncated on iPhone/iPad.

**Cause:** iOS Safari has a known limit on SVG path length (~10k points per element) and a line-length cap on embedded CSS (>5000 chars per line can fail to paint).

**Fix:**
- Keep SVG paths short — split long polylines into multiple `<path>` elements.
- Break inline `<style>` into multiple lines; never emit one megaline of CSS.
- For any graph exceeding these limits, fall back to `templates/mermaid-fallback.html`.

## Large Graphs (>50 nodes)

**Symptom:** SVG layout becomes a tangle of overlapping boxes and crossing arrows.

**Cause:** The base template uses hand-placed coordinates. At >50 nodes, layout quality collapses.

**Fix:** auto-switch to Mermaid fallback. Trigger conditions (any one):
- Node count > 50
- Detected layout collision (two nodes overlap in output)
- Heuristic flag: sum of `(node.width * node.height)` exceeds 60% of canvas area

## Fingerprint Schema Drift

**Symptom:** `watch` or `diff` emits "baseline restart required".

**Cause:** The `schema_version` field in `arch-state.json` differs from the current skill's schema.

**Fix:**
- Archive the old state: `mv arch-state.json arch-state.json.v<old>.bak`
- Run `/design:generate` to write a fresh baseline with the current schema
- Future diffs compare against the new baseline

## DCI Output Truncated

**Symptom:** a manifest file exists but the diagram is missing services from it.

**Cause:** inline DCI has size caps (see [dci-block.md § Size Budgets](dci-block.md#size-budgets)). Large `package.json` files, sprawling `docker-compose.yml`, or giant `terraform show` output may be truncated.

**Fix:** call `scripts/collect_dci.sh` to fetch bounded extras. Treat the harvester output as authoritative over the inline DCI sample.

## LLM Produces Overlapping Layout

**Symptom:** `validate_html.py` reports overlapping `<rect>` elements.

**Cause:** LLM hand-placing coordinates missed the 40px gap rule or placed a message bus outside the gap.

**Fix (automated):**
- Validator emits the overlap coordinates in its error message
- Re-run template fill with an added constraint: "Move node X to y=N+40" based on validator output
- Max 3 iterations; on 4th failure, fall back to Mermaid

## ${CLAUDE_PLUGIN_DATA} Not Set

**Symptom:** `fingerprint.py` can't find a writable location for state.

**Cause:** env var not set (skill running outside plugin context, or v<2.1.78 Claude Code).

**Fix (automatic fallback chain):**
1. `${CLAUDE_PLUGIN_DATA}/arch-state.json`
2. `${XDG_STATE_HOME}/claude/arch/arch-state.json`
3. `~/.claude-state/arch/arch-state.json` (auto-created)

Script probes each in order; first writable wins.

## Unknown Stack Trace Format

**Symptom:** `/design:trace <file>` outputs "trace parser unknown format".

**Cause:** the input doesn't match Sentry JSON, OpenTelemetry span JSON, or a recognizable raw-text pattern.

**Fix:**
- Inspect input file manually to identify format
- If it's a supported format with unusual shape, report the format to the skill maintainer
- As a workaround: reformat input as raw stack trace (`at ServiceName.methodName(file.ext:line)` per line)
- Fallback: emit Mermaid-only sequence with best-effort parsing; accuracy not guaranteed
