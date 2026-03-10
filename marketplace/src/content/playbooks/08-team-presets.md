---
title: "Team Presets & Workflows"
description: "Team standardization and collaboration. Plugin bundles, workflow templates, automated onboarding, and multi-layer configuration hierarchy (org/team/project/individual)."
category: "Operations"
wordCount: 5000
readTime: 25
featured: false
order: 8
tags: ["team", "presets", "workflows", "onboarding", "collaboration"]
prerequisites: []
relatedPlaybooks: ["02-cost-caps", "07-compliance-audit"]
---

<p><strong>Production Playbook for Team Leads and Engineering Managers</strong></p>

<p>Standardizing Claude Code configurations across engineering teams accelerates onboarding, ensures consistency, and enables collaborative development. This playbook provides team plugin bundles, workflow templates, configuration management strategies, and automation for distributed teams.</p>

<h2>Team Configuration Strategy</h2>

<h3>Configuration Layers</h3>

<pre><code class="language-mermaid">graph TB
    A[Organization Config] --> B[Team Config]
    B --> C[Project Config]
    C --> D[Individual Config]

<p>A --> E[Global Plugins]</p>
<p>B --> F[Team-Specific Plugins]</p>
<p>C --> G[Project Plugins]</p>
<p>D --> H[Personal Preferences]</code></pre></p>

<p><strong>Configuration Precedence</strong>:</p>
<ul>
<li><strong>Organization</strong> - Security policies, approved plugins, compliance settings</li>
<li><strong>Team</strong> - Team-specific workflows, shared plugins, coding standards</li>
<li><strong>Project</strong> - Project dependencies, custom agents, specific tools</li>
<li><strong>Individual</strong> - Personal preferences, API keys, editor settings</li>
</ul>

<h3>Team Configuration File</h3>

<pre><code class="language-jsonc">// .claude/team-config.json
{
  "teamId": "engineering-team-backend",
  "organization": "acme-corp",
  "version": "1.0.0",

<p>"plugins": {</p>
<p>"required": [</p>
<p>"code-reviewer@claude-code-plugins-plus",</p>
<p>"test-automator@claude-code-plugins-plus",</p>
<p>"security-auditor@claude-code-plugins-plus"</p>
<p>],</p>
<p>"recommended": [</p>
<p>"performance-engineer@claude-code-plugins-plus",</p>
<p>"database-optimizer@claude-code-plugins-plus"</p>
<p>],</p>
<p>"forbidden": [</p>
<p>"untrusted-plugin"  // Security risk</p>
<p>]</p>
<p>},</p>

<p>"workflows": {</p>
<p>"default": "code-review-workflow",</p>
<p>"available": [</p>
<p>"code-review-workflow",</p>
<p>"hotfix-workflow",</p>
<p>"feature-development-workflow"</p>
<p>]</p>
<p>},</p>

<p>"standards": {</p>
<p>"coding": {</p>
<p>"linter": "eslint",</p>
<p>"formatter": "prettier",</p>
<p>"typeChecker": "typescript"</p>
<p>},</p>
<p>"security": {</p>
<p>"scanOnCommit": true,</p>
<p>"preventSecrets": true</p>
<p>},</p>
<p>"review": {</p>
<p>"minReviewers": 2,</p>
<p>"requireTests": true</p>
<p>}</p>
<p>},</p>

<p>"onboarding": {</p>
<p>"steps": [</p>
<p>"install-required-plugins",</p>
<p>"configure-git-hooks",</p>
<p>"setup-local-environment",</p>
<p>"run-first-workflow"</p>
<p>],</p>
<p>"documentation": "https://wiki.acme.com/claude-code-setup"</p>
<p>}</p>
<p>}</code></pre></p>

<hr>

<h2>Plugin Bundles</h2>

<h3>Team-Specific Plugin Packs</h3>

<p><strong>Backend Engineering Team</strong>:</p>
<pre><code class="language-json">{
  "name": "backend-engineering-pack",
  "version": "1.0.0",
  "plugins": [
    "code-reviewer@claude-code-plugins-plus",
    "test-automator@claude-code-plugins-plus",
    "database-optimizer@claude-code-plugins-plus",
    "security-auditor@claude-code-plugins-plus",
    "api-documenter@claude-code-plugins-plus",
    "performance-engineer@claude-code-plugins-plus"
  ],
  "skills": [
    "typescript-pro",
    "nodejs-expert",
    "postgresql-optimizer",
    "rest-api-designer"
  ]
}</code></pre>

<p><strong>Frontend Engineering Team</strong>:</p>
<pre><code class="language-json">{
  "name": "frontend-engineering-pack",
  "version": "1.0.0",
  "plugins": [
    "code-reviewer@claude-code-plugins-plus",
    "ui-visual-validator@claude-code-plugins-plus",
    "frontend-security-coder@claude-code-plugins-plus",
    "seo-content-auditor@claude-code-plugins-plus"
  ],
  "skills": [
    "react-expert",
    "css-architect",
    "accessibility-specialist",
    "responsive-design"
  ]
}</code></pre>

<p><strong>DevOps Team</strong>:</p>
<pre><code class="language-json">{
  "name": "devops-pack",
  "version": "1.0.0",
  "plugins": [
    "cloud-architect@claude-code-plugins-plus",
    "kubernetes-architect@claude-code-plugins-plus",
    "terraform-specialist@claude-code-plugins-plus",
    "observability-engineer@claude-code-plugins-plus",
    "deployment-engineer@claude-code-plugins-plus"
  ],
  "skills": [
    "kubernetes-ops",
    "terraform-infra",
    "prometheus-monitoring",
    "docker-containerization"
  ]
}</code></pre>

<h3>Bundle Installation Script</h3>

<pre><code class="language-bash">#!/bin/bash
# install-team-bundle.sh - Install team plugin bundle

<p>BUNDLE=$1</p>

<p>if [ -z "$BUNDLE" ]; then</p>
<p>echo "Usage: ./install-team-bundle.sh <backend|frontend|devops>"</p>
<p>exit 1</p>
<p>fi</p>

<p>BUNDLE_FILE="team-bundles/${BUNDLE}-engineering-pack.json"</p>

<p>if [ ! -f "$BUNDLE_FILE" ]; then</p>
<p>echo "Bundle not found: $BUNDLE_FILE"</p>
<p>exit 1</p>
<p>fi</p>

<p># Parse plugins from bundle</p>
<p>PLUGINS=$(jq -r '.plugins[]' $BUNDLE_FILE)</p>

<p># Install each plugin</p>
<p>for plugin in $PLUGINS; do</p>
<p>echo "Installing: $plugin"</p>
<p>/plugin install $plugin</p>
<p>done</p>

<p># Verify installation</p>
<p>/plugin list</p>

<p>echo "✓ Team bundle installed: $BUNDLE"</code></pre></p>

<hr>

<h2>Workflow Templates</h2>

<h3>Code Review Workflow</h3>

<pre><code class="language-markdown"><!-- .claude/workflows/code-review-workflow.md -->
# Code Review Workflow

<p><h2>Steps</h2></p>

<ul>
<li><strong>Pre-Review Analysis</strong></li>
</ul>
<p>- Run linter: <code>npm run lint</code></p>
<p>- Run tests: <code>npm test</code></p>
<p>- Check types: <code>npm run typecheck</code></p>

<ul>
<li><strong>Automated Code Review</strong></li>
</ul>
<p>- Activate: <code>code-reviewer</code> plugin</p>
<p>- Scan for security issues: <code>security-auditor</code></p>
<p>- Check performance: <code>performance-engineer</code></p>

<ul>
<li><strong>Generate Review Report</strong></li>
</ul>
<p>- Create summary of findings</p>
<p>- Categorize issues by severity (critical, major, minor)</p>
<p>- Suggest fixes with code examples</p>

<ul>
<li><strong>Submit for Human Review</strong></li>
</ul>
<p>- Create GitHub PR with AI review in description</p>
<p>- Assign to team members</p>
<p>- Link Jira ticket if applicable</p>

<p><h2>Triggers</h2></p>

<ul>
<li><strong>Manual</strong>: <code>/review-pr <pr-number></code></li>
<li><strong>Automated</strong>: Git hook on <code>git push origin <branch></code></li>
<li><strong>CI/CD</strong>: GitHub Actions on PR creation</li>
</ul>

<p><h2>Success Criteria</h2></p>

<ul>
<li>✅ No critical security issues</li>
<li>✅ Test coverage >= 80%</li>
<li>✅ All tests passing</li>
<li>✅ Linter passing</li>
<li>✅ Performance within acceptable range</code></pre></li>
</ul>

<h3>Hotfix Workflow</h3>

<pre><code class="language-markdown"><!-- .claude/workflows/hotfix-workflow.md -->
# Hotfix Workflow

<p><h2>Steps</h2></p>

<ul>
<li><strong>Create Hotfix Branch</strong></code></pre>bash</li>
</ul>
<p>git checkout -b hotfix/issue-description main</p>
<p>\`\`<code></p>

<ul>
<li><strong>Implement Fix</strong></li>
</ul>
<p>- Make minimal changes</p>
<p>- Focus on immediate issue</p>
<p>- Defer refactoring to follow-up</p>

<ul>
<li><strong>Expedited Testing</strong></li>
</ul>
<p>- Run affected tests only</p>
<p>- Manual verification in staging</p>

<ul>
<li><strong>Deploy</strong></li>
</ul>
<p>- Deploy to staging</p>
<p>- Verify fix</p>
<p>- Deploy to production</p>

<ul>
<li><strong>Post-Deployment</strong></li>
</ul>
<p>- Monitor metrics (error rate, latency)</p>
<p>- Create postmortem (if SEV-1/SEV-2)</p>
<p>- Schedule follow-up refactoring</p>

<h2>Approval</h2>

<ul>
<li><strong>SEV-1</strong>: Single approver required (on-call engineer)</li>
<li><strong>SEV-2</strong>: Two approvers required</li>
<li><strong>SEV-3</strong>: Standard review process</li>
</ul>

<h2>Rollback Plan</h2>

<ul>
<li>Keep previous version ready</li>
<li>Monitor for 30 minutes post-deploy</li>
<li>Auto-rollback if error rate > 5%</li>
</ul>
</code>\`<code>

<h3>Feature Development Workflow</h3>

<pre><code class="language-typescript">// .claude/workflows/feature-development.ts

<p>interface FeatureWorkflow {</p>
<p>name: string;</p>
<p>steps: Step[];</p>
<p>approvals: string[];</p>
<p>testing: TestRequirement[];</p>
<p>}</p>

<p>const featureDevelopmentWorkflow: FeatureWorkflow = {</p>
<p>name: 'feature-development',</p>
<p>steps: [</p>
<p>{</p>
<p>name: 'Requirements Gathering',</p>
<p>duration: '1-2 days',</p>
<p>deliverables: ['PRD', 'Technical spec', 'UX mockups'],</p>
<p>agents: ['product-manager', 'architect-reviewer']</p>
<p>},</p>
<p>{</p>
<p>name: 'Design Review',</p>
<p>duration: '0.5 days',</p>
<p>deliverables: ['Architecture diagram', 'API contracts'],</p>
<p>agents: ['backend-architect', 'database-optimizer']</p>
<p>},</p>
<p>{</p>
<p>name: 'Implementation',</p>
<p>duration: '3-5 days',</p>
<p>deliverables: ['Code', 'Unit tests', 'Integration tests'],</p>
<p>agents: ['code-reviewer', 'test-automator']</p>
<p>},</p>
<p>{</p>
<p>name: 'Code Review',</p>
<p>duration: '0.5 days',</p>
<p>deliverables: ['Approved PR', 'Security scan', 'Performance review'],</p>
<p>agents: ['code-reviewer', 'security-auditor', 'performance-engineer']</p>
<p>},</p>
<p>{</p>
<p>name: 'QA Testing',</p>
<p>duration: '1 day',</p>
<p>deliverables: ['Test plan', 'Bug reports', 'Sign-off'],</p>
<p>agents: ['test-automator']</p>
<p>},</p>
<p>{</p>
<p>name: 'Deployment',</p>
<p>duration: '0.5 days',</p>
<p>deliverables: ['Production deployment', 'Monitoring setup'],</p>
<p>agents: ['deployment-engineer', 'observability-engineer']</p>
<p>}</p>
<p>],</p>
<p>approvals: [</p>
<p>'tech-lead',</p>
<p>'product-manager',</p>
<p>'security-reviewer'</p>
<p>],</p>
<p>testing: [</p>
<p>{ type: 'unit', coverage: 0.8 },</p>
<p>{ type: 'integration', coverage: 0.6 },</p>
<p>{ type: 'e2e', coverage: 0.4 }</p>
<p>]</p>
<p>};</code></pre></p>

<hr>

<h2>Onboarding Automation</h2>

<h3>New Team Member Setup Script</h3>

<pre><code class="language-bash">#!/bin/bash
# onboard-team-member.sh - Automated onboarding

<p>MEMBER_NAME=$1</p>
<p>TEAM=$2</p>

<p>if [ -z "$MEMBER_NAME" ] || [ -z "$TEAM" ]; then</p>
<p>echo "Usage: ./onboard-team-member.sh <name> <team>"</p>
<p>exit 1</p>
<p>fi</p>

<p>echo "🚀 Onboarding: $MEMBER_NAME to $TEAM team"</p>

<p># 1. Install Claude Code</p>
<p>echo "Installing Claude Code..."</p>
<p>npm install -g claude-code</p>

<p># 2. Configure team settings</p>
<p>echo "Configuring team settings..."</p>
<p>mkdir -p ~/.claude</p>
<p>cp team-configs/$TEAM/config.json ~/.claude/config.json</p>

<p># 3. Install team plugin bundle</p>
<p>echo "Installing team plugins..."</p>
<p>./install-team-bundle.sh $TEAM</p>

<p># 4. Set up Git hooks</p>
<p>echo "Setting up Git hooks..."</p>
<p>cp team-configs/$TEAM/hooks/* .git/hooks/</p>
<p>chmod +x .git/hooks/*</p>

<p># 5. Install Beads (task tracker)</p>
<p>echo "Installing Beads..."</p>
<p>npm install -g @beads/cli</p>

<p># 6. Clone team repositories</p>
<p>echo "Cloning team repositories..."</p>
<p>while read repo; do</p>
<p>git clone git@github.com:acme-corp/$repo.git</p>
<p>done < team-configs/$TEAM/repositories.txt</p>

<p># 7. Generate welcome document</p>
<p>cat > ONBOARDING_$MEMBER_NAME.md <<EOF</p>
<p># Welcome to the $TEAM Team!</p>

<p><h2>Your Setup</h2></p>
<ul>
<li>Claude Code: Installed ✅</li>
<li>Team Plugins: Installed ✅</li>
<li>Git Hooks: Configured ✅</li>
<li>Repositories: Cloned ✅</li>
</ul>

<p><h2>Next Steps</h2></p>
<ul>
<li>Read team docs: https://wiki.acme.com/$TEAM</li>
<li>Join Slack: #team-$TEAM</li>
<li>Attend standup: Daily at 9:30 AM</li>
<li>Review team workflows: .claude/workflows/</li>
</ul>

<p><h2>Quick Commands</h2></p>
<ul>
<li>Review code: /review-pr <number></li>
<li>Run tests: npm test</li>
<li>Deploy to staging: npm run deploy:staging</li>
</ul>

<p><h2>Team Contacts</h2></p>
<ul>
<li>Tech Lead: @tech-lead</li>
<li>Product Manager: @product-manager</li>
<li>DevOps: @devops</li>
</ul>

<p>Happy coding! 🎉</p>
<p>EOF</p>

<p>echo "✅ Onboarding complete!"</p>
<p>echo "Review: ONBOARDING_$MEMBER_NAME.md"</code></pre></p>

<h3>Interactive Onboarding CLI</h3>

<pre><code class="language-typescript">// onboard-cli.ts
import inquirer from 'inquirer';

<p>interface OnboardingAnswers {</p>
<p>name: string;</p>
<p>team: string;</p>
<p>role: string;</p>
<p>projects: string[];</p>
<p>}</p>

<p>async function runOnboarding(): Promise<void> {</p>
<p>console.log('🎯 Claude Code Team Onboarding\n');</p>

<p>const answers = await inquirer.prompt<OnboardingAnswers>([</p>
<p>{</p>
<p>type: 'input',</p>
<p>name: 'name',</p>
<p>message: 'Your name:',</p>
<p>validate: (input) => input.length > 0</p>
<p>},</p>
<p>{</p>
<p>type: 'list',</p>
<p>name: 'team',</p>
<p>message: 'Select your team:',</p>
<p>choices: ['backend', 'frontend', 'devops', 'mobile', 'qa']</p>
<p>},</p>
<p>{</p>
<p>type: 'list',</p>
<p>name: 'role',</p>
<p>message: 'Your role:',</p>
<p>choices: ['engineer', 'senior-engineer', 'staff-engineer', 'manager']</p>
<p>},</p>
<p>{</p>
<p>type: 'checkbox',</p>
<p>name: 'projects',</p>
<p>message: 'Projects you\'ll work on:',</p>
<p>choices: ['api-server', 'web-app', 'mobile-app', 'analytics', 'infrastructure']</p>
<p>}</p>
<p>]);</p>

<p>console.log('\n⚙️  Setting up your environment...\n');</p>

<p>// Install team bundle</p>
<p>console.log('📦 Installing plugins...');</p>
<p>await installTeamBundle(answers.team);</p>

<p>// Configure projects</p>
<p>console.log('📂 Configuring projects...');</p>
<p>for (const project of answers.projects) {</p>
<p>await configureProject(project);</p>
<p>}</p>

<p>// Set up workflows</p>
<p>console.log('🔧 Setting up workflows...');</p>
<p>await setupWorkflows(answers.team);</p>

<p>console.log('\n✅ Onboarding complete!\n');</p>
<p>console.log('Next steps:');</p>
<p>console.log('1. Read team docs: https://wiki.acme.com/' + answers.team);</p>
<p>console.log('2. Join Slack: #team-' + answers.team);</p>
<p>console.log('3. Run your first workflow: /code-review');</p>
<p>}</p>

<p>runOnboarding().catch(console.error);</code></pre></p>

<hr>

<h2>Configuration Management</h2>

<h3>Centralized Configuration Repository</h3>

</code>\`<code>
<p>team-configs/</p>
<p>├── backend/</p>
<p>│   ├── config.json</p>
<p>│   ├── plugins.json</p>
<p>│   ├── workflows/</p>
<p>│   ├── hooks/</p>
<p>│   └── repositories.txt</p>
<p>├── frontend/</p>
<p>│   ├── config.json</p>
<p>│   ├── plugins.json</p>
<p>│   └── ...</p>
<p>└── devops/</p>
<p>├── config.json</p>
<p>└── ...</p>
</code>\`<code>

<h3>Configuration Sync</h3>

<pre><code class="language-typescript">// sync-team-config.ts
import { execSync } from 'child_process';
import { readFileSync, writeFileSync } from 'fs';

<p>class TeamConfigSync {</p>
<p>private readonly configRepo = 'git@github.com:acme-corp/team-configs.git';</p>

<p>async syncFromCentral(team: string): Promise<void> {</p>
<p>// Clone/pull config repo</p>
<p>execSync(`git clone ${this.configRepo} /tmp/team-configs || (cd /tmp/team-configs && git pull)`);</p>

<p>// Copy team config</p>
<p>const teamConfig = readFileSync(`/tmp/team-configs/${team}/config.json`, 'utf-8');</p>
<p>writeFileSync(`${process.env.HOME}/.claude/config.json`, teamConfig);</p>

<p>// Copy workflows</p>
<p>execSync(`cp -r /tmp/team-configs/${team}/workflows/* ${process.env.HOME}/.claude/workflows/`);</p>

<p>// Copy hooks</p>
<p>execSync(`cp /tmp/team-configs/${team}/hooks/* .git/hooks/`);</p>

<p>console.log(`✓ Synced configuration for ${team} team`);</p>
<p>}</p>

<p>async pushLocalChanges(team: string, message: string): Promise<void> {</p>
<p>// Copy local config back to central repo</p>
<p>execSync(`cp ${process.env.HOME}/.claude/config.json /tmp/team-configs/${team}/config.json`);</p>

<p>// Commit and push</p>
<p>execSync(</code></p>
<p>cd /tmp/team-configs &&</p>
<p>git add ${team}/ &&</p>
<p>git commit -m "${message}" &&</p>
<p>git push origin main</p>
<p><code>);</p>

<p>console.log(`✓ Pushed changes to central repository`);</p>
<p>}</p>
<p>}</p>

<p>// Usage</p>
<p>const sync = new TeamConfigSync();</p>
<p>await sync.syncFromCentral('backend');</code></pre></p>

<hr>

<h2>Collaborative Development</h2>

<h3>Pair Programming with AI</h3>

<pre><code class="language-typescript">// pair-programming.ts

<p>interface PairSession {</p>
<p>driver: string;  // Human writing code</p>
<p>navigator: string;  // AI agent providing guidance</p>
<p>task: string;</p>
<p>startTime: number;</p>
<p>}</p>

<p>class AIPairProgramming {</p>
<p>async startSession(task: string): Promise<PairSession> {</p>
<p>const session: PairSession = {</p>
<p>driver: 'user-123',</p>
<p>navigator: 'code-reviewer-agent',</p>
<p>task,</p>
<p>startTime: Date.now()</p>
<p>};</p>

<p>console.log(`🎯 Pair Programming Session Started`);</p>
<p>console.log(`Task: ${task}`);</p>
<p>console.log(`Navigator: ${session.navigator}`);</p>
<p>console.log('------------------------------------------\n');</p>

<p>return session;</p>
<p>}</p>

<p>async provideGuidance(code: string, context: string): Promise<string> {</p>
<p>// AI agent analyzes code and provides real-time feedback</p>
<p>const response = await callClaude({</p>
<p>agent: 'code-reviewer',</p>
<p>prompt: `As a pair programming navigator, review this code:\n\n${code}\n\nContext: ${context}\n\nProvide:\n1. Immediate feedback\n2. Suggestions for improvement\n3. Potential bugs\n4. Best practices`</p>
<p>});</p>

<p>return response;</p>
<p>}</p>

<p>async endSession(session: PairSession): Promise<void> {</p>
<p>const duration = Date.now() - session.startTime;</p>
<p>console.log(`\n✅ Pair Programming Session Complete`);</p>
<p>console.log(`Duration: ${Math.floor(duration / 60000)} minutes`);</p>
<p>}</p>
<p>}</code></pre></p>

<h3>Code Review Automation</h3>

<pre><code class="language-typescript">// automated-code-review.ts

<p>interface ReviewResult {</p>
<p>approved: boolean;</p>
<p>issues: Issue[];</p>
<p>suggestions: string[];</p>
<p>score: number;  // 0-100</p>
<p>}</p>

<p>interface Issue {</p>
<p>severity: 'critical' | 'major' | 'minor';</p>
<p>file: string;</p>
<p>line: number;</p>
<p>description: string;</p>
<p>suggestion?: string;</p>
<p>}</p>

<p>class AutomatedCodeReview {</p>
<p>async reviewPullRequest(prNumber: number): Promise<ReviewResult> {</p>
<p>// Get PR diff</p>
<p>const diff = await getPRDiff(prNumber);</p>

<p>// Run parallel reviews</p>
<p>const [</p>
<p>securityReview,</p>
<p>performanceReview,</p>
<p>styleReview,</p>
<p>testCoverage</p>
<p>] = await Promise.all([</p>
<p>this.securityAudit(diff),</p>
<p>this.performanceAnalysis(diff),</p>
<p>this.styleCheck(diff),</p>
<p>this.checkTestCoverage(diff)</p>
<p>]);</p>

<p>// Aggregate results</p>
<p>const issues = [</p>
<p>...securityReview.issues,</p>
<p>...performanceReview.issues,</p>
<p>...styleReview.issues</p>
<p>];</p>

<p>const score = this.calculateScore(issues, testCoverage);</p>

<p>// Auto-approve if score >= 85 and no critical issues</p>
<p>const criticalIssues = issues.filter(i => i.severity === 'critical');</p>
<p>const approved = score >= 85 && criticalIssues.length === 0;</p>

<p>return {</p>
<p>approved,</p>
<p>issues,</p>
<p>suggestions: this.generateSuggestions(issues),</p>
<p>score</p>
<p>};</p>
<p>}</p>

<p>private calculateScore(issues: Issue[], testCoverage: number): number {</p>
<p>let score = 100;</p>

<p>// Deduct points for issues</p>
<p>score -= issues.filter(i => i.severity === 'critical').length * 20;</p>
<p>score -= issues.filter(i => i.severity === 'major').length * 10;</p>
<p>score -= issues.filter(i => i.severity === 'minor').length * 5;</p>

<p>// Factor in test coverage</p>
<p>score = Math.min(score, testCoverage);</p>

<p>return Math.max(0, score);</p>
<p>}</p>

<p>private async securityAudit(diff: string): Promise<{ issues: Issue[] }> {</p>
<p>// Use security-auditor plugin</p>
<p>return { issues: [] };</p>
<p>}</p>

<p>private async performanceAnalysis(diff: string): Promise<{ issues: Issue[] }> {</p>
<p>// Use performance-engineer plugin</p>
<p>return { issues: [] };</p>
<p>}</p>

<p>private async styleCheck(diff: string): Promise<{ issues: Issue[] }> {</p>
<p>// Run linter</p>
<p>return { issues: [] };</p>
<p>}</p>

<p>private async checkTestCoverage(diff: string): Promise<number> {</p>
<p>// Calculate test coverage</p>
<p>return 85;</p>
<p>}</p>

<p>private generateSuggestions(issues: Issue[]): string[] {</p>
<p>return issues</p>
<p>.filter(i => i.suggestion)</p>
<p>.map(i => i.suggestion!);</p>
<p>}</p>
<p>}</code></pre></p>

<hr>

<h2>Best Practices</h2>

<h3>DO ✅</h3>

<ul>
<li><strong>Standardize configurations</strong></li>
</ul>
   <pre><code class="language-json">{
     "team": "backend",
     "plugins": [...],
     "workflows": [...]
   }</code></pre>

<ul>
<li><strong>Automate onboarding</strong></li>
</ul>
   <pre><code class="language-bash">./onboard-team-member.sh alice backend</code></pre>

<ul>
<li><strong>Version control team configs</strong></li>
</ul>
   <pre><code class="language-bash">git commit -m "Update team workflow templates"</code></pre>

<ul>
<li><strong>Document workflows</strong></li>
</ul>
   <pre><code class="language-markdown"># Code Review Workflow
   1. Run linter
   2. Run tests
   ...</code></pre>

<h3>DON'T ❌</h3>

<ul>
<li><strong>Don't hardcode credentials</strong></li>
</ul>
   <pre><code class="language-json">// ❌ Hardcoded API key
   { "apiKey": "sk-..." }

<p>// ✅ Environment variable</p>
<p>{ "apiKey": "${ANTHROPIC_API_KEY}" }</code></pre></p>

<ul>
<li><strong>Don't skip testing workflows</strong></li>
</ul>
   <pre><code class="language-bash"># ❌ Deploy untested workflow
   # ✅ Test first
   ./test-workflow.sh code-review</code></pre>

<hr>

<h2>Tools & Resources</h2>

<h3>Configuration Management</h3>

<ul>
<li><strong>Git</strong>: Version control for configs</li>
<li><strong>Ansible</strong>: Configuration automation</li>
<li><strong>Terraform</strong>: Infrastructure as code</li>
</ul>

<h3>Collaboration Tools</h3>

<ul>
<li><strong>GitHub</strong>: Code review, PRs</li>
<li><strong>Slack</strong>: Team communication</li>
<li><strong>Jira</strong>: Task tracking</li>
</ul>

<hr>

<h2>Summary</h2>

<p><strong>Key Takeaways</strong>:</p>

<ul>
<li><strong>Standardize configurations</strong> - Team-wide consistency</li>
<li><strong>Create plugin bundles</strong> - Backend, frontend, DevOps packs</li>
<li><strong>Define workflows</strong> - Code review, hotfix, feature development</li>
<li><strong>Automate onboarding</strong> - Scripts for new team members</li>
<li><strong>Version control configs</strong> - Git repo for team settings</li>
<li><strong>Enable collaboration</strong> - Pair programming, automated reviews</li>
<li><strong>Document everything</strong> - Workflows, standards, processes</li>
</ul>

<p><strong>Team Setup Checklist</strong>:</p>
<ul>
<li>[ ] Create team configuration file</li>
<li>[ ] Define plugin bundle for team</li>
<li>[ ] Document workflows (code review, hotfix, feature)</li>
<li>[ ] Write onboarding script</li>
<li>[ ] Set up configuration repository</li>
<li>[ ] Configure Git hooks</li>
<li>[ ] Establish coding standards</li>
<li>[ ] Create workflow templates</li>
<li>[ ] Train team on workflows</li>
<li>[ ] Schedule quarterly config reviews</li>
</ul>

<hr>

<p><strong>Last Updated</strong>: 2025-12-24</p>
<p><strong>Author</strong>: Jeremy Longshore</p>
<p><strong>Related Playbooks</strong>: <a href="./02-cost-caps.md">Cost Caps & Budget Management</a>, <a href="./07-compliance-audit.md">Compliance & Audit Guide</a></p>
