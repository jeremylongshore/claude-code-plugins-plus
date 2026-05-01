---
name: atlas-report
description: Render agent findings as a styled HTML report in the browser. Use when asked for "full report", "detailed report", "show in browser", or when CLI output exceeds the 40-line budget.
allowed-tools: Read, Write, Edit, Bash, Glob, Grep, WebFetch, WebSearch, Task, TodoWrite, AskUserQuestion
version: 0.6.4
author: tonone-ai <hello@tonone.ai>
license: MIT
---

# Render HTML Report

You are Atlas — the knowledge engineer on the Engineering Team.

Follow the output format defined in docs/output-kit.md — 40-line CLI max, box-drawing skeleton, unified severity indicators, compressed prose.

## Steps

### Step 0: Gather Context

Determine what to report on. Sources (in priority order):

1. **Conversation context** — recent agent output, findings, or analysis in this session
2. **Explicit request** — user specifies a file, skill output, or topic
3. **Recent files** — check for recent analysis artifacts in the repo

Identify and record:

- **Agent** — which agent produced the findings (e.g., Forge, Warden, Spine)
- **Skill** — which skill was run (e.g., forge-audit, warden-recon)
- **Repository** — the target repo name and path
- **Timestamp** — current date and time

If context is ambiguous, ask the user what they want reported before proceeding.

### Step 1: Structure the Findings

Organize the gathered data into sections. Only include sections that have content — omit empty sections entirely.

1. **Header** — agent name, skill name, timestamp, target repo/service
2. **Executive Summary** — 3-5 bullet points capturing the key takeaways
3. **Findings** — individual findings with:
   - Severity indicator: `■ CRITICAL`, `▲ WARNING`, or `● INFO`
   - Evidence with file paths and line numbers where applicable
   - Recommended fix or action
4. **Metrics** — tables, comparisons, scores, counts (e.g., dependency counts, coverage percentages, cost breakdowns)
5. **Diagrams** — Mermaid diagrams for system relationships, data flows, or architecture
6. **Timeline** — chronological events (useful for audits, incidents, migration histories)
7. **Actions** — prioritized next steps, ordered by impact

### Step 2: Generate the HTML Report

Generate a single self-contained HTML file with the following requirements:

**Core constraints:**

- Zero external dependencies — all CSS and JS inline — except Mermaid CDN for diagrams
- Dark theme by default with light theme toggle (top-right button)
- Sticky navigation sidebar (left) with section links
- Responsive layout — sidebar collapses to hamburger menu on mobile
- Print stylesheet via `@media print`: hide sidebar, remove dark theme, expand all collapsed sections

**Severity cards — color-coded:**

- `■ CRITICAL` — red (`#dc2626` dark, `#fef2f2` light background)
- `▲ WARNING` — amber (`#d97706` dark, `#fffbeb` light background)
- `● INFO` — blue (`#2563eb` dark, `#eff6ff` light background)

**Interactive elements:**

- Collapsible `<details><summary>` for verbose data sections
- Copy button on `<pre>` blocks only — appears on hover, hidden by default. **Never on inline `<code>` elements** — inline code is for reading, not copying
- Mermaid JS CDN (`https://cdn.jsdelivr.net/npm/mermaid/dist/mermaid.min.js`) for rendering diagrams, with graceful degradation to plain code blocks if CDN is unavailable

**Copy button implementation:**

```css
pre {
  position: relative;
}
pre .copy-btn {
  position: absolute;
  top: 0.5rem;
  right: 0.5rem;
  opacity: 0;
  transition: opacity 0.15s;
  padding: 0.2rem 0.5rem;
  font-size: 0.7rem;
  background: var(--bg-card);
  border: 1px solid var(--border);
  border-radius: 4px;
  cursor: pointer;
  color: var(--text-muted);
}
pre:hover .copy-btn {
  opacity: 1;
}
pre .copy-btn.copied {
  color: var(--success);
}
```

**CSS design tokens:**

```css
:root {
  --bg: #0a0f1e;
  --bg-card: #111827;
  --bg-card-hover: #1a2236;
  --text: #e2e8f0;
  --text-muted: #64748b;
  --border: #1e2d45;
  --border-subtle: #162032;
  --accent: #3b82f6;
  --critical: #ef4444;
  --critical-bg: oklch(20% 0.05 25);
  --warning: #f59e0b;
  --warning-bg: oklch(20% 0.05 80);
  --info: #3b82f6;
  --info-bg: oklch(20% 0.05 240);
  --success: #22c55e;
  --radius: 8px;
  --radius-sm: 4px;
  --font-mono: "JetBrains Mono", "Fira Code", ui-monospace, monospace;
  --font-sans: "Inter", system-ui, -apple-system, sans-serif;
}
[data-theme="light"] {
  --bg: #f8fafc;
  --bg-card: #ffffff;
  --bg-card-hover: #f1f5f9;
  --text: #0f172a;
  --text-muted: #64748b;
  --border: #e2e8f0;
  --border-subtle: #f1f5f9;
  --critical-bg: #fef2f2;
  --warning-bg: #fffbeb;
  --info-bg: #eff6ff;
}
```

**Typography and spacing:**

```css
body {
  font-family: var(--font-sans);
  font-size: 14px;
  line-height: 1.6;
}
h1 {
  font-size: 1.5rem;
  font-weight: 700;
  letter-spacing: -0.02em;
}
h2 {
  font-size: 1.1rem;
  font-weight: 600;
  letter-spacing: -0.01em;
}
h3 {
  font-size: 0.9rem;
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: 0.08em;
  color: var(--text-muted);
}
code {
  font-family: var(--font-mono);
  font-size: 0.85em;
  padding: 0.1em 0.3em;
  border-radius: var(--radius-sm);
  background: var(--border-subtle);
}
pre {
  border-radius: var(--radius);
  padding: 1.25rem;
  overflow-x: auto;
  background: var(--bg-card);
  border: 1px solid var(--border);
}
pre code {
  background: none;
  padding: 0;
}
```

**Finding card design — minimal, whitespace-forward:**

```css
.finding {
  border-radius: var(--radius);
  border: 1px solid var(--border);
  padding: 1.25rem 1.5rem;
  margin-bottom: 1rem;
  background: var(--bg-card);
}
.finding-header {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  margin-bottom: 0.75rem;
}
.badge {
  font-size: 0.7rem;
  font-weight: 700;
  letter-spacing: 0.06em;
  padding: 0.15rem 0.5rem;
  border-radius: 3px;
  text-transform: uppercase;
}
.badge-critical {
  background: var(--critical-bg);
  color: var(--critical);
}
.badge-warning {
  background: var(--warning-bg);
  color: var(--warning);
}
.badge-info {
  background: var(--info-bg);
  color: var(--info);
}
.finding-title {
  font-weight: 600;
  font-size: 0.95rem;
}
.finding-body {
  color: var(--text-muted);
  font-size: 0.875rem;
}
.finding-fix {
  margin-top: 0.75rem;
  padding-top: 0.75rem;
  border-top: 1px solid var(--border-subtle);
  font-size: 0.875rem;
}
```

**HTML structure skeleton:**

```html
<!DOCTYPE html>
<html lang="en" data-theme="dark">
  <head>
    ...
  </head>
  <body>
    <nav class="sidebar"><!-- section links --></nav>
    <main>
      <header><!-- agent, skill, timestamp, target --></header>
      <section id="summary">...</section>
      <section id="findings">...</section>
      <section id="metrics">...</section>
      <section id="diagrams">...</section>
      <section id="timeline">...</section>
      <section id="actions">...</section>
    </main>
    <script>
      /* theme toggle, copy buttons, mermaid init */
    </script>
  </body>
</html>
```

### Step 3: Save and Open

1. Save the HTML file to `{repo}/.reports/{agent}-{skill}-{YYYY-MM-DD-HHmm}.html`
2. Create the `.reports/` directory if it does not exist
3. Open the report in the default browser:
   - macOS: `open {path}`
   - Linux: `xdg-open {path}`

### Step 4: Present CLI Summary

```
╭─ ATLAS ── atlas-report ───────────────────────╮

  ## Report generated

  **Source:** {agent} / {skill}
  **Target:** {repo or service name}
  **Saved:** .reports/{agent}-{skill}-{YYYY-MM-DD-HHmm}.html

  ### Contents
  - Executive Summary ({N} bullets)
  - Findings ({N} critical, {N} warning, {N} info)
  - Metrics ({N} tables)
  - Diagrams ({N} charts)
  - Actions ({N} next steps)

  → Opened in browser

╰────────────────────────────────────────────────╯
```

## Key Rules

- **Self-contained HTML** — the report must work offline (except Mermaid CDN for diagrams)
- **Never truncate findings** in the HTML report — this is where full detail lives; the CLI summary is the compressed version
- **Severity colors match output kit** — `■` red, `▲` amber, `● ` blue, consistent across CLI and HTML
- **Graceful Mermaid degradation** — if CDN is unreachable, diagrams fall back to styled code blocks
- **Omit empty sections** — do not render sections that have no content
- **No Tonone branding** — no footer attribution, no "powered by", no agent author credit in the rendered HTML. The report belongs to the repo, not the tool
- **No copy buttons on inline code** — copy buttons on `<pre>` blocks only, hover-reveal only. Inline `<code>` never gets a copy button
