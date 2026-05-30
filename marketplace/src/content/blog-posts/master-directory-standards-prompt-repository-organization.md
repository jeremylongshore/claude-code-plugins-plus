---
title: "Applying Universal Directory Standards to a Prompt Engineering Repository"
description: "How we systematically applied master directory standards to organize 150+ prompt templates, created TaskWarrior integration protocols, and built streamlined GitHub release workflows - including the messy iteration process."
date: "2025-10-08"
tags: ["directory-structure", "organization", "standards", "automation", "taskwarrior", "github-workflows", "qa-testing"]
featured: false
---
## The Problem: Inconsistent File Naming Across Master Systems

I had a prompt engineering repository with 150+ templates organized in a logical category structure, but the `000-master-systems/` directory had inconsistent file naming. Some files used `CATEGORY-###-description-MMDDYY.md`, others didn't. I needed to apply universal directory standards without breaking the existing structure.

The repository: [prompts-intent-solutions](https://github.com/jeremylongshore/prompts-intent-solutions)

## The Challenge: Two Different Naming Conventions

Here's where it got interesting. I initially thought the pattern was:

```
CATEGORY-###-description-MMDDYY.md
```

Looking at existing files in `000-master-systems/github/`:

```
GITHUB-001-master-repo-audit-092825.md
GITHUB-002-master-repo-chore-092825.md
GITHUB-003-master-repo-release-092825.md
```

But the MASTER DIRECTORY STANDARDS document specified a different format:

```
NNN-abv-description.ext
```

Where:

- `NNN` = zero-padded sequence number (001, 002, 003...)
- `abv` = approved abbreviation (tsk, gde, rel, aud, etc.)
- `description` = kebab-case description
- No date suffix for reference documents

**The confusion:** Number first or category first?

## The Iterative Solution Process

### Attempt 1: Following the Existing Pattern

I created new TaskWarrior files matching the github directory pattern:

```
TASKWARRIOR-001-mandatory-integration-protocol-100825.md
TASKWARRIOR-002-complete-usage-guide-100825.md
```

This seemed right because it matched what I saw.

### Attempt 2: Examining the Standards Document

Then I re-read the MASTER DIRECTORY STANDARDS more carefully:

```markdown
## DOCS FILE NAMING STANDARD

### Format
NNN-abv-short-description.ext

- NNN = Zero-padded sequence number (chronology enforced)
- abv = Approved abbreviation from table below
- short-description = 1–4 words, kebab-case
- ext = File extension
```

**The realization:** The existing `github/` directory was using an old pattern. The standard called for number-first, not category-first.

### Attempt 3: The Correct Approach

Renamed to proper format:

```
001-tsk-mandatory-integration-protocol.md
002-gde-complete-usage-guide.md
```

Using approved abbreviations:

- `tsk` = Task Breakdown/List
- `gde` = User Guide/Handbook

**Key insight:** Reference documents don't need date suffixes. Dates are for versioned files like `deployment-config-2024-10-05-v2.json`.

## What We Built: Five Master System Documents

### 1. TaskWarrior Integration Protocol (`001-tsk-mandatory-integration-protocol.md`)

**Purpose:** Enforce TaskWarrior lifecycle tracking for all code-related tasks.

**The Four-Phase Mandate:**

1. **Task Decomposition** - Break work into discrete tasks before coding
2. **Task Activation** - Start time tracking with `task <ID> start`
3. **Code Execution** - Implement with progress annotations
4. **Task Completion** - Mark done and review time spent

**Required Attributes:**

```bash
task add "Build authentication system" \
  project:WebDev \
  priority:H \
  due:today \
  +coding +security
```

Every task must include:

- `project:` - Categorization
- `priority:` - Urgency (H/M/L)
- `due:` - Realistic deadline
- `tags:` - Minimum 2 relevant tags

**The Validation Checklist:**

- [ ] All discrete work units captured as tasks
- [ ] Dependencies properly linked
- [ ] Priority and due dates set
- [ ] Task started before code execution
- [ ] Time tracking active
- [ ] Task marked done after completion

### 2. TaskWarrior Usage Guide (`002-gde-complete-usage-guide.md`)

**Purpose:** Practical examples for every usage scenario.

**Pattern Catalog:**

- **Simple single-task**: Create → start → code → done
- **Complex multi-step**: Parent task with dependent subtasks
- **Debugging**: High priority, annotation of findings, resolution notes
- **Recurring maintenance**: `recur:weekly` for ongoing tasks

**Troubleshooting Section:**
Common issues and solutions:

- Claude jumps to code without creating tasks → Re-emphasize mandate
- Tasks lack proper attributes → Specify required fields
- No time tracking → Verify `task active` output
- Tasks not completed → Explicit completion command

**Customization Examples:**

- Team collaboration mode
- Custom urgency weights
- Project-specific tag vocabularies
- Minimal mode for rapid prototyping

### 3. Streamlined GitHub Release Workflow (`001-rel-master-repo-release.md`)

**Purpose:** Complete release pipeline without handoff bloat.

**The Problem We Solved:**
The original release system had:

- Chore handoff files
- Manual script orchestration
- Complex initialization phases
- Handoff between audit → chore → release

**The Solution - 8-Phase Linear Pipeline:**

1. **Verification** - Close issues, run tests, check clean state
2. **Version Management** - Determine bump type, increment, commit
3. **Changelog Generation** - Build entry (newest first), commit
4. **Documentation Sync** - Update README, docs, commit
5. **Tag & Release** - Annotated tag, push, GitHub release
6. **Deployment** - NPM/Docker/Actions based on repo type
7. **Announcement** - Issue, pin, discussion post
8. **Archive & Schedule** - Save artifacts, schedule next audit

**Guarantees:**

- Sequential correctness - proper semantic versioning
- Consistency - all references match current release
- Audit trail - archived artifacts with linked milestones
- Automation ready - standalone or end-to-end execution

**Practical Implementation:**

```bash
# Version bump
npm version patch -m "chore: bump version to %s"

# Changelog update
cat >> CHANGELOG.md << 'EOF'
## [X.Y.Z] - YYYY-MM-DD
### Added
- New features
### Fixed
- Bug fixes
EOF

# Create tag and release
git tag -a vX.Y.Z -m "Release vX.Y.Z"
git push origin vX.Y.Z
gh release create vX.Y.Z --generate-notes --latest
```

### 4. Multi-Repo Workflow Installation (`002-aut-install-release-workflow-all-repos.md`)

**Purpose:** Install standardized release workflow across entire GitHub organization.

**The Mega Prompt Approach:**

**Discovery Phase:**

```bash
# Scan organizations
gh repo list "$ORG" --limit 1000 --json name,owner,isArchived,isFork

# Filter repos
grep -E "$INCLUDE_REGEX" | grep -Ev "$EXCLUDE_REGEX"
```

**Workflow Features:**

- Auto-detect version bump from commits (BREAKING CHANGE, feat:, or patch)
- Generate changelog from commit history since last tag
- Update version files (package.json, version.txt, README.md)
- Create annotated Git tags
- Generate GitHub releases
- Dry run mode for testing

**Safety Features:**

- Concurrency control
- Test validation before release
- Clean state verification
- No destructive operations

**Output:**
CSV summary with status for each repo:

```
repo,status,branch,commit_or_pr
jeremylongshore/prompts-intent-solutions,pr-opened,main,https://github.com/.../pull/42
jeremylongshore/bobs-brain,pr-opened,main,https://github.com/.../pull/15
```

### 5. Universal Web-App QA Framework (`001-qap-universal-webapp-qa-mega-prompt.md`)

**Purpose:** Complete end-to-end QA suite for any web application.

**The Non-Negotiables:**

- ✅ Preserve every existing test (only add or refactor)
- ✅ Idempotent runs (no destructive ops)
- ✅ Gate optional suites behind capability checks
- ✅ Report after each phase

**6-Phase Workflow:**

**Phase 0 - Detect & Plan:**

- Auto-detect framework (React/Next/Vue/Svelte/Static)
- Auto-detect host (Netlify/Vercel/Cloudflare/AWS)
- Select adapters for submission verification and email
- Print plan summary and wait for approval

**Phase 1 - Structure & Scripts:**

```
tests/
├── playwright/
├── cypress/
├── helpers/
├── adapters/
├── scripts/
└── artifacts/<YYYY-MM-DD_HHMM>/
```

Capability-guarded npm scripts:

```json
{
  "test:core": "Playwright E2E",
  "test:accessibility": "axe/pa11y",
  "test:performance": "Lighthouse",
  "test:visual": "BackstopJS",
  "test:security": "headers, XSS/SQLi",
  "test:complete": "everything available"
}
```

**Phase 3 - Test Coverage Matrix (11 categories):**

A. **Manual-equivalent E2E:**

- Form happy path with submission verification
- Dashboard/API verification
- Email notification receipt and content check
- Error handling, network fail, offline messaging
- Rate-limit/spam, honeypot/reCAPTCHA checks

B. **Validation & Edge Cases:**

- Empty, partial, invalid formats
- Boundary lengths, unicode, RTL, emojis
- XSS payloads (confirm no alert/injection)
- Rapid multi-submit and idempotency

C. **Cross-browser & Devices:**

- Chromium, Firefox, WebKit
- Mobile (iPhone/Android), tablet, desktop
- Private mode and ad-block

D. **Accessibility (WCAG 2.1 AA):**

- Keyboard-only flow, tab order, focus visible
- Labels, roles, ARIA announcements
- Color contrast, 200% zoom without horizontal scroll
- Live regions for status updates

E. **Performance:**

- Lighthouse thresholds: Performance ≥70, Accessibility ≥90, Best-Practices ≥90, SEO ≥90
- Web-Vitals sampling

F. **Visual Regression:**

- Key routes and form states
- Mismatch threshold ≤ 0.1%

G. **Security Sanity:**

- HTTPS redirect, HSTS, X-Frame-Options, X-Content-Type-Options
- CSP, Referrer-Policy
- XSS/SQLi probes must not leak stack traces

H. **Networking & Observability:**

- Console error-free
- Network POST status 2xx/3xx
- Server/app logs captured

I. **Load/Soak (optional):**

- 1-5 rps warmup, 10 rps sustain, 20 rps spike
- Track p95 latency and error rate

J. **Internationalization:**

- Locale switch, date/number formats, RTL

K. **Cookies/Storage/Auth:**

- CSRF token presence and rotation
- SameSite, Secure flags

**Phase 5 - Evidence Pack:**

Complete audit trail in `tests/artifacts/<timestamp>/`:

```
├── reports/              # HTML, JSON, JUnit
├── screenshots/          # Visual evidence
├── videos/               # Test recordings
├── traces/               # Playwright traces
├── lighthouse/           # Performance reports
├── accessibility/        # a11y results
├── security/             # Security scans
├── visual/               # Regression diffs
├── evidence/             # IDs, headers, payloads
└── SUMMARY.md            # Executive summary
```

**Exit Criteria:**

- All core E2E pass
- WCAG 2.1 AA violations = 0 (or documented waivers)
- Lighthouse thresholds met (or ticketed)
- Security headers present (or ticketed)
- Visual diffs approved
- Evidence pack complete

**Adapter Pattern:**

```javascript
// tests/adapters/submission-verifier.netlify.js
class NetlifySubmissionVerifier {
  async verifySubmission(submissionId, expectedData) {
    const response = await axios.get(
      `https://api.netlify.com/api/v1/sites/${siteId}/submissions/${submissionId}`,
      { headers: { Authorization: `Bearer ${authToken}` } }
    );

    return {
      found: true,
      matches: Object.keys(expectedData).every(
        key => response.data.data[key] === expectedData[key]
      ),
      submissionId: response.data.id,
      timestamp: response.data.created_at
    };
  }
}
```

## Applying the Directory Standards

### The Adaptation Challenge

The repository isn't a traditional code project - it's a **prompt library**. The standard structure assumes:

```
02-Src/      # Source code
03-Tests/    # Test suites
```

But our core product is:

```
prompts/     # 150+ prompt templates
```

**Decision:** Adapt the standards while preserving the product structure.

### Final Structure

```
prompts-intent-solutions/
├── .github/                    # Workflows, templates
├── 000-master-systems/         # Master automation (DO NOT MODIFY)
│   ├── taskwarrior/            # TaskWarrior protocols
│   ├── directory/              # Directory standards
│   ├── github/                 # GitHub workflows
│   ├── content/                # Content systems
│   ├── debug/                  # Debug workflows
│   ├── tracking/               # Time tracking
│   ├── testing/                # QA frameworks
│   └── legacy/                 # Archive
├── 01-Docs/                    # Project docs (FLAT)
├── prompts/                    # Core prompt library
│   ├── development/            # Dev prompts
│   ├── business/               # Business prompts
│   └── specialized/            # Advanced prompts
├── tools/                      # Validation & automation
├── 99-Archive/                 # Deprecated content
├── .directory-standards.md     # Standards reference
├── README.md                   # Updated with standards
├── CLAUDE.md                   # Updated with standards
├── CHANGELOG.md                # Newest-first format
└── LICENSE
```

### Updated Documentation

**README.md addition:**

```markdown
## Directory Standards

This project follows the **MASTER DIRECTORY STANDARDS**.

- **Structure**: See `.directory-standards.md` for details
- **Documentation**: All docs in `01-Docs/` using `NNN-abv-description.ext`
- **Prompts**: Core library organized in `prompts/` by category
- **File Naming**: kebab-case files, PascalCase directories
- **Chronology**: Documentation in strict chronological order
```

**CLAUDE.md addition:**

```markdown
## Directory Standards

Follow `.directory-standards.md` for structure and file naming.

### Key Standards
- Store all docs in `01-Docs/` using `NNN-abv-description.ext`
- Maintain strict chronological order
- Prompts directory is core product - organize by category
- File naming: kebab-case, PascalCase for main directories
- CHANGELOG.md: Newest entries on TOP
- 000-master-systems/: DO NOT modify without permission
```

**CHANGELOG.md format:**

```markdown
# Changelog

Format: Newest entries on TOP (reverse chronological order).

## [Unreleased]
### Changed
- Applied MASTER DIRECTORY STANDARDS
- Updated README.md and CLAUDE.md with standards references
- Reorganized CHANGELOG.md to newest-first

## [1.0.1] - 2025-10-02
...
```

## The Abbreviation Table Discovery

The MASTER DIRECTORY STANDARDS includes 120+ approved abbreviations organized by category:

**Product & Planning:**

- prd, pln, rmp, brd, frd, sow, kpi, okr

**Architecture & Technical:**

- adr, tad, dsg, api, sdk, int, dia

**Testing & Quality:**

- tst, tsc, qap, bug, perf, sec, pen

**Operations & Deployment:**

- ops, dep, inf, cfg, env, rel, chg, inc, pst

**Project Management:**

- tsk, bkl, spr, ret, stb, rsk, iss

**Documentation & Reference:**

- ref, gde, man, faq, gls, sop, tmp, chk

**After Action:**

- aar, lsn, pmi

**Workflows & Automation:**

- wfl, n8n, aut, hok

This standardization means every document type has a consistent, recognizable abbreviation across all projects.

## Lessons Learned

### 1. Examine Before You Name

Don't assume the existing pattern is correct. Check the authoritative standards document first.

### 2. Numbers vs Categories

The sequence number comes **first** (`001-tsk-`), not the category (`TASKWARRIOR-001-`). This enforces chronological order and makes sorting work correctly.

### 3. Date Suffixes Are Optional

Reference documents don't need dates. Reserve `-MMDDYY` suffix for versioned files that change over time.

### 4. Flat Structures for Documentation

Both `01-Docs/` and `claudes-docs/` should be flat - no subdirectories. Use the numbering and abbreviation system for organization.

### 5. CHANGELOG Newest-First

Modern practice: newest entries on top (reverse chronological). Users want to see what's new immediately.

### 6. Adaptation Over Rigidity

The standards are universal, but implementation must adapt to the repository type. A prompt library isn't a code project, so preserve the product structure while applying the naming standards.

### 7. Protection of Master Systems

The `000-master-systems/` directory is protected. It contains the source-of-truth automation workflows that shouldn't be modified without explicit approval.

## Related Resources

- AI Dev Transformation Part 2: Enterprise Library - Building comprehensive prompt libraries
- AI-Assisted Technical Writing Automation Workflows - Documentation automation systems
- [GitHub Repository Organization Master Standards](https://github.com/jeremylongshore/prompts-intent-solutions/blob/main/.directory-standards.md)

## Key Takeaways

1. **File naming matters** - Consistent naming enables automation, sorting, and discovery
2. **Standards require interpretation** - Adapt universal standards to repository type
3. **Chronology is enforced** - Sequential numbering creates a timeline of development
4. **Abbreviations reduce cognitive load** - 120+ standard abbreviations mean instant recognition
5. **CHANGELOG format evolved** - Newest-first is modern best practice
6. **Master systems need protection** - Source-of-truth workflows shouldn't be casually modified
7. **Iteration is normal** - We went through 3 attempts to get the naming right

The result: A professionally organized prompt engineering repository with universal directory standards, comprehensive automation workflows, and complete documentation.

**Repository:** [prompts-intent-solutions](https://github.com/jeremylongshore/prompts-intent-solutions)
