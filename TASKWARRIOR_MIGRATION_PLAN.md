# Agent Skills Migration - Taskwarrior Plan
**Created:** 2025-10-23
**Tasks:** 32 total (across 7 phases)
**Estimated Time:** ~9 hours
**Target Completion:** 3 days

---

## 📊 Project Overview

### Status
- **Total Tasks:** 32
- **Completed:** 0
- **Remaining:** 32
- **Progress:** 0%

### Project Hierarchy
```
SkillsMigration (parent)
├── Phase1: AI-Powered Analysis (3 tasks, ~2.5h)
├── Phase2: Migration Script Development (3 tasks, ~2h)
├── Phase3: Proof of Concept (3 tasks, ~40min)
├── Phase4: Bulk Migration (4 tasks, ~40min)
├── Phase5: Script Updates (4 tasks, ~1.75h)
├── Phase6: Documentation (5 tasks, ~2.75h)
└── Phase7: Release (8 tasks, ~1h)
```

### Key Features
- ✅ Proper task dependencies (prevents out-of-order execution)
- ✅ Time estimates for each task
- ✅ Priority levels (H/M/L)
- ✅ Due dates (today, tomorrow, 2-3 days)
- ✅ Tags for filtering (+vertex-ai, +gemini, +automation, etc.)
- ✅ Project hierarchy for organization

---

## 📋 Phase Breakdown

### Phase 1: AI-Powered Analysis (~2.5 hours)

**Objective:** Use Vertex AI Gemini to analyze all 164 plugins and suggest optimal skill names

**Tasks:**

1. **Task 99** - Create Gemini skill name analyzer script
   - Priority: HIGH
   - Due: Today
   - Estimate: 2 hours
   - Tags: +development +vertex-ai +gemini
   - Dependencies: Task 98 (parent)
   - **Description:** Build Python script that uses Vertex AI Gemini free tier to analyze each plugin's SKILL.md and suggest semantically meaningful directory names

2. **Task 100** - Generate skill name mappings for all 164 plugins
   - Priority: HIGH
   - Due: Today
   - Estimate: 20 minutes
   - Tags: +automation +vertex-ai +analysis
   - Dependencies: Task 99
   - **Description:** Run analyzer script to process all 164 plugins and create JSON mapping file with old → new directory names

3. **Task 101** - Review and validate suggested names
   - Priority: HIGH
   - Due: Today
   - Estimate: 30 minutes
   - Tags: +review +qa
   - Dependencies: Task 100
   - **Description:** Manually review Gemini's suggestions for uniqueness, clarity, and appropriateness. Approve or adjust names as needed

**Deliverables:**
- `scripts/analyze-skill-names.py` - Gemini analyzer script
- `skill-name-mappings.json` - Validated name mappings

---

### Phase 2: Migration Script Development (~2 hours)

**Objective:** Generate automated migration scripts with safety features

**Tasks:**

4. **Task 102** - Create migration script generator
   - Priority: HIGH
   - Due: Today
   - Estimate: 1 hour
   - Tags: +development +automation
   - Dependencies: Task 101
   - **Description:** Build Python script that uses Gemini to generate bash migration script from the approved name mappings

5. **Task 103** - Generate migrate-skills-structure.sh
   - Priority: HIGH
   - Due: Today
   - Estimate: 30 minutes
   - Tags: +automation +scripting
   - Dependencies: Task 102
   - **Description:** Use generator to create migration script with dry-run mode, validation checks, and rollback capabilities

6. **Task 104** - Create validation script
   - Priority: HIGH
   - Due: Today
   - Estimate: 45 minutes
   - Tags: +development +qa
   - Dependencies: Task 102
   - **Description:** Build Python script to verify all migrations completed successfully (SKILL.md exists, correct depth, YAML intact)

**Deliverables:**
- `scripts/generate-migration.py` - Migration generator
- `scripts/migrate-skills-structure.sh` - Executable migration script
- `scripts/validate-skill-structure.py` - Validation script

---

### Phase 3: Proof of Concept (~40 minutes)

**Objective:** Test migration on 2 Jeremy personal plugins before bulk operation

**Tasks:**

7. **Task 105** - Full backup of plugins/ directory
   - Priority: HIGH
   - Due: Today
   - Estimate: 5 minutes
   - Tags: +backup +safety
   - Dependencies: Task 103
   - **Description:** Create timestamped backup of entire plugins/ directory before any modifications

8. **Task 106** - Migrate 2 Jeremy personal plugins (POC)
   - Priority: HIGH
   - Due: Today
   - Estimate: 15 minutes
   - Tags: +migration +poc
   - Dependencies: Task 105, Task 104
   - **Description:** Run migration script on `000-jeremy-content-consistency-validator` and `001-jeremy-taskwarrior-integration` only

9. **Task 107** - Validate POC migration and test loading
   - Priority: HIGH
   - Due: Today
   - Estimate: 20 minutes
   - Tags: +testing +validation
   - Dependencies: Task 106
   - **Description:** Run validation script, then test plugin loading in Claude Code CLI to ensure structure works

**Deliverables:**
- Backup: `plugins-backup-2025-10-23/`
- 2 migrated plugins in new structure
- Validation report for POC

---

### Phase 4: Bulk Migration (~40 minutes)

**Objective:** Migrate all 162 remaining plugins after POC success

**Tasks:**

10. **Task 108** - Execute dry-run migration
    - Priority: HIGH
    - Due: Tomorrow
    - Estimate: 5 minutes
    - Tags: +migration +dry-run
    - Dependencies: Task 107
    - **Description:** Run migration script in dry-run mode to preview all 162 changes

11. **Task 109** - Review dry-run results
    - Priority: HIGH
    - Due: Tomorrow
    - Estimate: 15 minutes
    - Tags: +review +approval
    - Dependencies: Task 108
    - **Description:** Review proposed changes for any issues, conflicts, or unexpected renames

12. **Task 110** - Execute actual bulk migration
    - Priority: HIGH
    - Due: Tomorrow
    - Estimate: 10 minutes
    - Tags: +migration +bulk
    - Dependencies: Task 109
    - **Description:** Run migration script in actual mode to rename all 162 remaining plugin skill directories

13. **Task 111** - Validate all migrations
    - Priority: HIGH
    - Due: Tomorrow
    - Estimate: 10 minutes
    - Tags: +validation +qa
    - Dependencies: Task 110
    - **Description:** Run validation script on all 164 plugins to ensure 100% migration success

**Deliverables:**
- 164 plugins fully migrated
- Validation report showing 100% success
- Dry-run log for reference

---

### Phase 5: Script Updates (~1.75 hours)

**Objective:** Update skill generation scripts for future plugins

**Tasks:**

14. **Task 112** - Update vertex-skills-generator-safe.py
    - Priority: MEDIUM
    - Due: Tomorrow
    - Estimate: 45 minutes
    - Tags: +development +generator
    - Dependencies: Task 107
    - **Description:** Modify to generate compliant `skills/{skill-name}/` structure instead of `skills/skill-adapter/`

15. **Task 113** - Update generate-skills-gemini.py
    - Priority: MEDIUM
    - Due: Tomorrow
    - Estimate: 30 minutes
    - Tags: +development +generator
    - Dependencies: Task 107
    - **Description:** Modify to use new directory structure and support optional scripts/, references/, assets/ subdirectories

16. **Task 114** - Update next-skill.sh
    - Priority: MEDIUM
    - Due: Tomorrow
    - Estimate: 15 minutes
    - Tags: +development +generator
    - Dependencies: Task 107
    - **Description:** Update paths and directory creation logic for compliant structure

17. **Task 115** - Test new skill generation
    - Priority: MEDIUM
    - Due: Tomorrow
    - Estimate: 20 minutes
    - Tags: +testing +validation
    - Dependencies: Task 112, Task 113, Task 114
    - **Description:** Generate test skill with updated scripts to verify correct structure

**Deliverables:**
- Updated generation scripts
- Test skill in compliant structure
- Documentation of new workflow

---

### Phase 6: Documentation (~2.75 hours)

**Objective:** Update all documentation to reflect new structure

**Tasks:**

18. **Task 116** - Update CLAUDE.md
    - Priority: MEDIUM
    - Due: 2 days
    - Estimate: 30 minutes
    - Tags: +documentation
    - Dependencies: Task 111
    - **Description:** Update Agent Skills structure section with new format, examples, and progressive disclosure features

19. **Task 117** - Update README.md
    - Priority: MEDIUM
    - Due: 2 days
    - Estimate: 20 minutes
    - Tags: +documentation
    - Dependencies: Task 111
    - **Description:** Update skill structure examples and quick reference

20. **Task 118** - Update scripts/SKILLS_AUTOMATION.md
    - Priority: MEDIUM
    - Due: 2 days
    - Estimate: 20 minutes
    - Tags: +documentation
    - Dependencies: Task 115
    - **Description:** Document new skill generation workflow with updated script usage

21. **Task 119** - Create MIGRATION_GUIDE.md
    - Priority: MEDIUM
    - Due: 2 days
    - Estimate: 45 minutes
    - Tags: +documentation +user-guide
    - Dependencies: Task 111
    - **Description:** Write comprehensive guide for users on how the migration affects them and what actions they need to take

22. **Task 120** - Create progressive disclosure tutorial
    - Priority: LOW
    - Due: 2 days
    - Estimate: 1 hour
    - Tags: +documentation +tutorial
    - Dependencies: Task 111
    - **Description:** Write tutorial showing how to use scripts/, references/, assets/ subdirectories with examples

**Deliverables:**
- Updated core documentation files
- User migration guide
- Progressive disclosure tutorial and templates

---

### Phase 7: Release (~1 hour)

**Objective:** Version bump, changelog, and GitHub release

**Tasks:**

23. **Task 121** - Update VERSION to 1.3.0
    - Priority: HIGH
    - Due: 3 days
    - Estimate: 2 minutes
    - Tags: +release
    - Dependencies: Task 116, 117, 118, 119
    - **Description:** Bump version file to 1.3.0 (structural breaking change)

24. **Task 122** - Update package.json to 1.3.0
    - Priority: HIGH
    - Due: 3 days
    - Estimate: 2 minutes
    - Tags: +release
    - Dependencies: Task 121
    - **Description:** Update package.json version field

25. **Task 123** - Update CHANGELOG.md
    - Priority: HIGH
    - Due: 3 days
    - Estimate: 30 minutes
    - Tags: +release +changelog
    - Dependencies: Task 122
    - **Description:** Write comprehensive v1.3.0 changelog documenting breaking changes, migration path, and new features

26. **Task 124** - Sync marketplace catalogs
    - Priority: HIGH
    - Due: 3 days
    - Estimate: 2 minutes
    - Tags: +marketplace +sync
    - Dependencies: Task 123
    - **Description:** Run `pnpm run sync-marketplace` to regenerate CLI-compatible catalog

27. **Task 125** - Commit and push to GitHub
    - Priority: HIGH
    - Due: 3 days
    - Estimate: 5 minutes
    - Tags: +git +release
    - Dependencies: Task 124
    - **Description:** Commit all changes with comprehensive message and push to main

28. **Task 126** - Create v1.3.0 git tag
    - Priority: HIGH
    - Due: 3 days
    - Estimate: 2 minutes
    - Tags: +git +release
    - Dependencies: Task 125
    - **Description:** Create annotated git tag for v1.3.0

29. **Task 127** - Push git tag
    - Priority: HIGH
    - Due: 3 days
    - Estimate: 1 minute
    - Tags: +git +release
    - Dependencies: Task 126
    - **Description:** Push tag to trigger GitHub Actions release workflow

30. **Task 128** - Create GitHub release
    - Priority: HIGH
    - Due: 3 days
    - Estimate: 15 minutes
    - Tags: +github +release
    - Dependencies: Task 127
    - **Description:** Create GitHub release with migration notes, breaking changes warning, and upgrade instructions

31. **Task 129** - Generate final migration report
    - Priority: MEDIUM
    - Due: 3 days
    - Estimate: 30 minutes
    - Tags: +documentation +report
    - Dependencies: Task 128
    - **Description:** Create comprehensive report documenting migration success, metrics, and lessons learned

**Deliverables:**
- v1.3.0 release on GitHub
- Updated marketplace catalogs
- Final migration report

---

## 🎯 Next Actions

### Immediate Next Task (Ready to Start Now)

**Task 99: Create Gemini skill name analyzer script**
- Start: `task start 99`
- Estimated time: 2 hours
- No blockers (parent task 98 is organizational only)

### Command Reference

**View all tasks:**
```bash
task project:SkillsMigration
```

**View by phase:**
```bash
task project:SkillsMigration.Phase1
task project:SkillsMigration.Phase2
task project:SkillsMigration.Phase3
task project:SkillsMigration.Phase4
task project:SkillsMigration.Phase5
task project:SkillsMigration.Phase6
task project:SkillsMigration.Phase7
```

**View next actionable tasks:**
```bash
task next project:SkillsMigration
```

**Start working on a task:**
```bash
task start 99
```

**Mark task complete:**
```bash
task 99 done
```

**View tasks by tag:**
```bash
task +vertex-ai
task +gemini
task +automation
task +migration
task +documentation
```

---

## 📈 Progress Tracking

### Daily Goals

**Day 1 (Today):**
- ✅ Phase 1: Complete (all 3 tasks)
- ✅ Phase 2: Complete (all 3 tasks)
- ✅ Phase 3: Complete (all 3 tasks)
- **Target:** 9 tasks completed, ~5 hours work

**Day 2 (Tomorrow):**
- ✅ Phase 4: Complete (all 4 tasks)
- ✅ Phase 5: Complete (all 4 tasks)
- ✅ Phase 6: Start (at least 3 of 5 tasks)
- **Target:** 11 tasks completed, ~4 hours work

**Day 3:**
- ✅ Phase 6: Complete (remaining 2 tasks)
- ✅ Phase 7: Complete (all 8 tasks)
- **Target:** 10 tasks completed, ~2.5 hours work

### Milestone Tracking

- [ ] Milestone 1: AI Analysis Complete (Task 101 done)
- [ ] Milestone 2: Scripts Generated (Task 104 done)
- [ ] Milestone 3: POC Success (Task 107 done)
- [ ] Milestone 4: Full Migration Complete (Task 111 done)
- [ ] Milestone 5: Generators Updated (Task 115 done)
- [ ] Milestone 6: Docs Updated (Task 120 done)
- [ ] Milestone 7: Release Published (Task 128 done)

---

## 🔧 Vertex AI Gemini Free Tier Usage

### Quota Management

**Daily Limit:** 1500 requests/day (Gemini 1.5 Flash)

**Our Usage:**
- Phase 1: ~164 requests (one per plugin for name analysis)
- Phase 2: ~5 requests (script generation)
- Phase 3: ~2 requests (validation)
- **Total: ~171 requests** (well within limit)

### Batching Strategy

To maximize efficiency:
1. **Batch name analysis:** Process 10 plugins per request (16-17 total requests instead of 164)
2. **Cache responses:** Store mappings in JSON to avoid re-running
3. **Error handling:** Retry failed requests with exponential backoff

### Cost Analysis

**Vertex AI Gemini 1.5 Flash:**
- ✅ Completely FREE (no charges)
- ✅ 1500 requests/day limit
- ✅ Perfect for our use case

**Alternative (if needed):**
- Gemini 1.5 Pro: Higher quality, lower quota
- Claude Sonnet: Paid API, no free tier

---

## 🎓 Learning Outcomes

By completing this migration, we will have:

1. **AI-Powered Refactoring Experience**
   - Using Gemini for intelligent code analysis
   - Automated bulk operations with AI guidance
   - Validation and quality assurance with AI

2. **Agent Skills Mastery**
   - Deep understanding of Anthropic's spec
   - Progressive disclosure patterns
   - Advanced skill structuring

3. **DevOps Best Practices**
   - Safe bulk migration strategies
   - Rollback and recovery procedures
   - Validation and testing at scale

4. **Documentation Excellence**
   - Comprehensive user guides
   - Migration documentation
   - Tutorial creation

---

## ⚠️ Risk Mitigation

### High-Risk Items

1. **Bulk migration failure**
   - Mitigation: Full backup, dry-run first, atomic operations
   - Rollback: Restore from backup if needed

2. **Name collisions**
   - Mitigation: Gemini checks uniqueness, manual review
   - Fallback: Append category if collision occurs

3. **Breaking user installations**
   - Mitigation: Clear changelog, migration guide
   - Support: GitHub issues for user questions

### Contingency Plans

**If Phase 3 POC fails:**
- Stop immediately
- Analyze failure
- Adjust approach
- Re-test POC

**If bulk migration has issues:**
- Rollback to backup
- Fix migration script
- Re-run with corrections

**If Gemini quota exceeded:**
- Use manual naming for remainder
- Batch requests more efficiently
- Spread work across multiple days

---

## 📊 Success Metrics

**Must Achieve:**
- ✅ 164/164 plugins migrated successfully
- ✅ 0 broken SKILL.md paths
- ✅ 100% validation pass rate
- ✅ Generation scripts updated and tested

**Should Achieve:**
- ✅ <1 hour total migration execution time
- ✅ Meaningful skill directory names
- ✅ Comprehensive documentation
- ✅ Smooth user migration experience

**Nice to Have:**
- 🎁 Progressive disclosure examples
- 🎁 Community tutorial video
- 🎁 Blog post about the process

---

**Generated:** 2025-10-23
**Taskwarrior IDs:** 98-129 (32 tasks)
**Status:** Ready to execute
**First Task:** Start with Task 99 (Gemini analyzer script)
