---
title: "Production Setup"
description: "Deploy Claude Code plugins in production environments. CI/CD integration, validation gates, team configuration, and monitoring setup."
category: "Operations"
wordCount: 2500
readTime: 13
featured: true
order: 13
tags: ["production", "deployment", "ci-cd", "team", "configuration"]
prerequisites: ["12-beginner-onboarding"]
relatedPlaybooks: ["12-beginner-onboarding", "14-troubleshooting"]
---

<p>Moving from local development to production requires validation gates, CI/CD integration, team configuration, and monitoring. This playbook covers every step needed to deploy Claude Code plugins in a production environment with confidence.</p>

<h2>Step 1: Validate All Plugins</h2>

<h3>Two-Tier Validation System</h3>

<p>The plugin ecosystem uses a two-tier validation system. Standard tier checks basic structure; Enterprise tier enforces a 100-point grading rubric with strict field requirements.</p>

<pre><code class="language-bash"># Standard validation (basic structure checks)
python3 scripts/validate-skills-schema.py --verbose

# Enterprise validation (100-point grading, all fields required)
python3 scripts/validate-skills-schema.py --enterprise --verbose

# Validate only SKILL.md files
python3 scripts/validate-skills-schema.py --skills-only

# Validate only command files
python3 scripts/validate-skills-schema.py --commands-only</code></pre>

<h3>What Enterprise Validation Checks</h3>

<table>
<thead>
<tr>
<th>Check</th>
<th>Points</th>
<th>What It Validates</th>
</tr>
</thead>
<tbody>
<tr>
<td><strong>Frontmatter fields</strong></td>
<td>30</td>
<td>name, description, version, author, license, allowed-tools</td>
</tr>
<tr>
<td><strong>Description quality</strong></td>
<td>20</td>
<td>Trigger phrases, length, actionable language</td>
</tr>
<tr>
<td><strong>Tool scoping</strong></td>
<td>20</td>
<td>No unscoped Bash, specific tool allowlists</td>
</tr>
<tr>
<td><strong>Content structure</strong></td>
<td>15</td>
<td>Headers, code examples, reference links</td>
</tr>
<tr>
<td><strong>Metadata</strong></td>
<td>15</td>
<td>Tags, compatibility, version format</td>
</tr>
</tbody>
</table>

<p><strong>Target score</strong>: 90+ for production deployments. Skills scoring below 80 should be revised before deployment.</p>

<h3>Full Plugin Validation</h3>

<pre><code class="language-bash"># Comprehensive validation: JSON, frontmatter, refs, permissions
./scripts/validate-all-plugins.sh

# Validate a specific plugin
./scripts/validate-all-plugins.sh plugins/devops/docker-hardener/

# Quick test (build + lint + validate, ~30 seconds)
./scripts/quick-test.sh</code></pre>

<hr>

<h2>Step 2: Add Validation to CI</h2>

<h3>GitHub Actions Integration</h3>

<p>Add plugin validation as a required check in your CI pipeline. This prevents invalid plugins from reaching production:</p>

<pre><code class="language-yaml"># .github/workflows/validate-plugins.yml
name: Validate Plugins

on:
  pull_request:
    paths:
      - 'plugins/**'
      - '.claude-plugin/**'

jobs:
  validate:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - name: Setup Node.js
        uses: actions/setup-node@v4
        with:
          node-version: '20'

      - name: Setup pnpm
        uses: pnpm/action-setup@v2
        with:
          version: 9

      - name: Install dependencies
        run: pnpm install

      - name: Validate plugin structure
        run: ./scripts/validate-all-plugins.sh

      - name: Enterprise skill validation
        run: python3 scripts/validate-skills-schema.py --enterprise --verbose

      - name: Check catalog sync
        run: |
          pnpm run sync-marketplace
          git diff --exit-code .claude-plugin/marketplace.json || \
            (echo "ERROR: marketplace.json out of sync. Run 'pnpm run sync-marketplace'" && exit 1)

      - name: Secret scanning
        run: |
          # Ensure no API keys or secrets in plugin files
          if grep -r "sk-ant-\|ANTHROPIC_API_KEY\|Bearer " plugins/; then
            echo "ERROR: Potential secrets found in plugin files"
            exit 1
          fi</code></pre>

<h3>Required Status Checks</h3>

<p>In your GitHub repository settings, mark these checks as required for merging to main:</p>

<ul>
<li><code>validate</code> - Plugin structure and schema validation</li>
<li><code>check-package-manager</code> - Enforces pnpm/npm policy</li>
<li><code>marketplace-validation</code> - Astro build, route validation, link integrity</li>
</ul>

<hr>

<h2>Step 3: Set Up Team Plugin Presets</h2>

<h3>Shared Plugin Configuration</h3>

<p>Create a <code>.claude/plugins.json</code> at your repository root to standardize which plugins your team uses:</p>

<pre><code class="language-json">{
  "plugins": [
    "jeremylongshore/claude-code-plugins/plugins/devops/docker-hardener",
    "jeremylongshore/claude-code-plugins/plugins/security/owasp-top-10",
    "jeremylongshore/claude-code-plugins/plugins/code-quality/code-reviewer"
  ],
  "saas-packs": [
    "jeremylongshore/claude-code-plugins/plugins/saas-packs/supabase-pack"
  ]
}</code></pre>

<h3>Per-Team Configurations</h3>

<p>Different teams may need different plugin sets. Organize by team function:</p>

<pre><code class="language-bash"># Backend team
.claude/plugins-backend.json    # Database, API, security plugins

# Frontend team
.claude/plugins-frontend.json   # UI, accessibility, performance plugins

# DevOps team
.claude/plugins-devops.json     # CI/CD, infrastructure, monitoring plugins</code></pre>

<h3>Onboarding New Team Members</h3>

<p>With shared configuration, new team members get the right plugins automatically:</p>

<pre><code class="language-bash"># New team member setup (single command)
claude

# Claude Code reads .claude/plugins.json and loads the team's plugins
# No manual plugin installation needed</code></pre>

<hr>

<h2>Step 4: Configure Model Preferences Per Skill</h2>

<h3>Model Selection Strategy</h3>

<p>Choose the right model for each skill based on task complexity and cost requirements:</p>

<table>
<thead>
<tr>
<th>Model</th>
<th>Best For</th>
<th>Speed</th>
<th>Cost</th>
</tr>
</thead>
<tbody>
<tr>
<td><strong>haiku</strong></td>
<td>Simple lookups, formatting, validation</td>
<td>Fastest</td>
<td>Lowest</td>
</tr>
<tr>
<td><strong>sonnet</strong></td>
<td>Code review, generation, analysis</td>
<td>Fast</td>
<td>Medium</td>
</tr>
<tr>
<td><strong>opus</strong></td>
<td>Architecture decisions, complex debugging</td>
<td>Slower</td>
<td>Highest</td>
</tr>
</tbody>
</table>

<h3>Setting Model Overrides</h3>

<p>In your skill's SKILL.md frontmatter, specify the model:</p>

<pre><code class="language-yaml">---
name: quick-lint
description: |
  Use when the user wants a fast lint check on their code.
model: haiku
allowed-tools: Read, Glob, Grep
---</code></pre>

<p><strong>Production recommendation</strong>: Use <code>sonnet</code> as the default for most skills. Reserve <code>opus</code> for skills that require deep reasoning (architecture review, complex debugging). Use <code>haiku</code> for high-volume, simple tasks to control costs.</p>

<hr>

<h2>Step 5: Enable Monitoring</h2>

<h3>Analytics Daemon</h3>

<p>The analytics daemon provides real-time monitoring of plugin usage, API calls, and performance:</p>

<pre><code class="language-bash"># Start the analytics daemon
cd packages/analytics-daemon
pnpm install && pnpm start

# WebSocket endpoint for real-time events
# ws://localhost:3456

# HTTP API for status and metrics
# http://localhost:3333/api/status</code></pre>

<h3>Key Metrics to Monitor</h3>

<ul>
<li><strong>Skill activation frequency</strong>: Which skills are used most? Are any unused?</li>
<li><strong>Error rates</strong>: Track 429 (rate limit) and 500 (server error) responses</li>
<li><strong>Token usage</strong>: Monitor consumption per skill to identify cost outliers</li>
<li><strong>Response times</strong>: Track latency to identify slow skills</li>
</ul>

<h3>Dashboard Setup</h3>

<pre><code class="language-bash"># Start the analytics dashboard
cd packages/analytics-dashboard
pnpm install && pnpm dev

# Dashboard available at http://localhost:5173</code></pre>

<p>The dashboard displays real-time charts for API usage, skill activations, error rates, and cost projections.</p>

<hr>

<h2>Step 6: Set Up Performance Budgets</h2>

<h3>Enforcing Performance Limits</h3>

<p>Performance budgets prevent bloat and ensure fast build times. The marketplace enforces these limits in CI:</p>

<pre><code class="language-bash"># Run performance budget checks
node scripts/check-performance.mjs</code></pre>

<h3>Current Budget Limits</h3>

<table>
<thead>
<tr>
<th>Budget</th>
<th>Limit</th>
<th>What Triggers a Failure</th>
</tr>
</thead>
<tbody>
<tr>
<td><strong>Total bundle (gzipped)</strong></td>
<td>19.5 MB</td>
<td>Too many large plugins or unoptimized assets</td>
</tr>
<tr>
<td><strong>Largest file (gzipped)</strong></td>
<td>550 KB</td>
<td>A single page with too much inline content</td>
</tr>
<tr>
<td><strong>Build time</strong></td>
<td>10 seconds</td>
<td>Slow build steps or unoptimized data processing</td>
</tr>
<tr>
<td><strong>Route count</strong></td>
<td>1,600-2,000</td>
<td>Missing or orphaned plugin pages</td>
</tr>
</tbody>
</table>

<h3>Custom Budgets for Your Project</h3>

<p>Add performance checks to your own CI pipeline:</p>

<pre><code class="language-bash"># In your CI workflow
- name: Check performance budgets
  run: node scripts/check-performance.mjs
  env:
    MAX_BUNDLE_SIZE_MB: 19.5
    MAX_FILE_SIZE_KB: 550
    MAX_BUILD_TIME_S: 10</code></pre>

<hr>

<h2>Step 7: Production Checklist</h2>

<h3>Pre-Deployment Verification</h3>

<p>Run through this checklist before every production deployment:</p>

<h3>Validation</h3>

<ul>
<li>[ ] All plugins pass <code>./scripts/validate-all-plugins.sh</code></li>
<li>[ ] Enterprise validation scores 90+ for all skills</li>
<li>[ ] <code>marketplace.json</code> is in sync (<code>pnpm run sync-marketplace</code>)</li>
<li>[ ] No secrets in plugin files (API keys, tokens, credentials)</li>
</ul>

<h3>Security</h3>

<ul>
<li>[ ] No unscoped <code>Bash</code> in allowed-tools (use <code>Bash(npm:*)</code> instead of <code>Bash</code>)</li>
<li>[ ] All required frontmatter fields present (name, description, version, author, license)</li>
<li>[ ] Plugin permissions are minimal (principle of least privilege)</li>
<li>[ ] <code>plugin.json</code> only contains allowed fields</li>
</ul>

<h3>Quality</h3>

<ul>
<li>[ ] All skills have descriptive <code>description</code> fields with trigger phrases</li>
<li>[ ] Code examples are tested and working</li>
<li>[ ] Reference links resolve correctly</li>
<li>[ ] Version numbers follow semver</li>
</ul>

<h3>Infrastructure</h3>

<ul>
<li>[ ] CI pipeline includes validation job</li>
<li>[ ] Performance budgets are enforced</li>
<li>[ ] Monitoring is active (analytics daemon running)</li>
<li>[ ] Team plugin presets are configured</li>
<li>[ ] Backup/rollback procedure documented</li>
</ul>

<h3>Automated Verification</h3>

<pre><code class="language-bash"># Run the complete verification suite
./scripts/quick-test.sh && \
python3 scripts/validate-skills-schema.py --enterprise --verbose && \
pnpm run sync-marketplace && \
git diff --exit-code .claude-plugin/marketplace.json && \
echo "All checks passed. Ready for production."</code></pre>

<p>If any check fails, fix the issue before deploying. See the <a href="/playbooks/14-troubleshooting/">Troubleshooting Guide</a> for common fixes.</p>

<hr>

<p><strong>Last Updated</strong>: 2026-03-21</p>
<p><strong>Author</strong>: Jeremy Longshore</p>
<p><strong>Related Playbooks</strong>: <a href="/playbooks/12-beginner-onboarding/">Beginner Onboarding</a>, <a href="/playbooks/14-troubleshooting/">Troubleshooting Guide</a></p>
