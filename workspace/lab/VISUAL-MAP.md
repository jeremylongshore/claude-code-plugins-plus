# Visual Map: Learning Lab Structure

```
workspace/lab/
│
├── README.md ←─────────────────────── START HERE
│   └─→ Quick navigation guide
│
├── Learning Guides (Read in Order)
│   ├── GUIDE-00-START-HERE.md ──────→ Mental model (5 min)
│   ├── GUIDE-01-PATTERN-EXPLAINED.md → Deep dive (15 min)
│   ├── GUIDE-02-BUILDING-YOUR-OWN.md → Adaptation guide (30 min)
│   └── GUIDE-03-DEBUGGING-TIPS.md ──→ Troubleshooting (15 min)
│
├── schema-optimization/ ←───────────── REFERENCE IMPLEMENTATION
│   │
│   ├── SKILL.md ←─────────────────── Orchestrator (conductor)
│   │   └─→ Creates session dir
│   │   └─→ Spawns phases in order
│   │   └─→ Validates outputs
│   │   └─→ Aggregates final JSON
│   │
│   ├── agents/ ←──────────────────── Phase Subagents (workers)
│   │   ├── phase_1.md ──→ Initial Analysis
│   │   ├── phase_2.md ──→ Field Utilization
│   │   ├── phase_3.md ──→ Impact Assessment
│   │   ├── phase_4.md ──→ Verification ★ CRITICAL
│   │   └── phase_5.md ──→ Final Recommendations
│   │
│   ├── references/ ←──────────────── Step-by-Step Instructions
│   │   ├── 01-phase-1.md ──→ "Do exactly this for Phase 1"
│   │   ├── 04-verify-with-script.md ★ "Run script, compare results"
│   │   └── ... (other phases)
│   │
│   ├── scripts/ ←─────────────────── Deterministic Tools
│   │   └── analyze_field_utilization.sh ★ Empirical validation
│   │       └─→ Input: schema files
│   │       └─→ Output: field_utilization_report.json
│   │       └─→ NO LLM - pure computation
│   │
│   └── reports/ ←─────────────────── Evidence Repository
│       ├── runs/ ──→ Session directories (created at runtime)
│       │   └── 2025-01-15_143022/
│       │       ├── 01-initial-schema-analysis.md
│       │       ├── 02-field-utilization-analysis.md
│       │       ├── 03-impact-assessment.md
│       │       ├── 04-field-utilization-verification.md ★
│       │       └── 05-final-recommendations.md
│       └── _samples/ ──→ Example outputs (TODO)
│
└── exercises/ ←────────────────────── Hands-On Practice
    ├── exercise-1-run-workflow.md ─→ Execute reference implementation
    ├── exercise-2-modify-script.md → (TODO) Extend verification
    ├── exercise-3-add-phase-6.md ──→ (TODO) Add new phase
    └── exercise-4-build-from-scratch.md → (TODO) Your own workflow
```

---

## The Pattern Flow

```
┌─────────────────────────────────────────────────────────────────┐
│  USER INVOKES ORCHESTRATOR                                      │
│  Input: {skill_dir, input_folder, extraction_type}             │
└─────────────────────────────────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────────┐
│  ORCHESTRATOR CREATES SESSION DIRECTORY                         │
│  reports/runs/2025-01-15_143022/                                │
└─────────────────────────────────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────────┐
│  PHASE 1: Initial Analysis                                      │
│  ┌────────────────────────────────────────────────────────────┐ │
│  │ 1. Read: references/01-phase-1.md                          │ │
│  │ 2. Scan schema files in input_folder                       │ │
│  │ 3. Write: session_dir/01-initial-schema-analysis.md        │ │
│  │ 4. Return: {status, report_path, schema_summary}           │ │
│  └────────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────────┘
                            │
                            ▼ Orchestrator validates JSON + file
┌─────────────────────────────────────────────────────────────────┐
│  PHASE 2: Field Utilization Analysis                            │
│  ┌────────────────────────────────────────────────────────────┐ │
│  │ 1. Read: references/02-phase-2.md                          │ │
│  │ 2. Read: Phase 1 report (context)                          │ │
│  │ 3. Analyze field usage patterns                            │ │
│  │ 4. Write: session_dir/02-field-utilization-analysis.md     │ │
│  │ 5. Return: {status, report_path, utilization_summary}      │ │
│  └────────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────────┘
                            │
                            ▼ Orchestrator validates JSON + file
┌─────────────────────────────────────────────────────────────────┐
│  PHASE 3: Impact Assessment                                     │
│  ┌────────────────────────────────────────────────────────────┐ │
│  │ 1. Read: references/03-phase-3.md                          │ │
│  │ 2. Read: Phase 1-2 reports (context)                       │ │
│  │ 3. Assess risks and savings                                │ │
│  │ 4. Write: session_dir/03-impact-assessment.md              │ │
│  │ 5. Return: {status, report_path, impact_summary}           │ │
│  └────────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────────┘
                            │
                            ▼ Orchestrator validates JSON + file
┌─────────────────────────────────────────────────────────────────┐
│  PHASE 4: VERIFICATION ★ THE CRITICAL PHASE                     │
│  ┌────────────────────────────────────────────────────────────┐ │
│  │ 1. Read: references/04-verify-with-script.md               │ │
│  │ 2. Read: Phase 2-3 reports (manual conclusions)            │ │
│  │ 3. Execute: scripts/analyze_field_utilization.sh           │ │
│  │    ├─→ Input: schema files                                 │ │
│  │    ├─→ Output: field_utilization_report.json               │ │
│  │    └─→ Deterministic (NO LLM)                              │ │
│  │ 4. Compare: Manual conclusions vs Script results           │ │
│  │    ├─→ Confirmed: Manual = Script                          │ │
│  │    ├─→ Revised: Manual ≠ Script                            │ │
│  │    └─→ Unexpected: Script found issues manual missed       │ │
│  │ 5. Write: session_dir/04-field-utilization-verification.md │ │
│  │ 6. Return: {status, report_path, verification_summary}     │ │
│  └────────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────────┘
                            │
                            ▼ Orchestrator validates JSON + file
┌─────────────────────────────────────────────────────────────────┐
│  PHASE 5: Final Recommendations                                 │
│  ┌────────────────────────────────────────────────────────────┐ │
│  │ 1. Read: references/05-phase-5.md                          │ │
│  │ 2. Read: All 4 prior phase reports                         │ │
│  │ 3. Synthesize validated findings                           │ │
│  │ 4. Prioritize actions (confirmed > revised)                │ │
│  │ 5. Write: session_dir/05-final-recommendations.md          │ │
│  │ 6. Return: {status, report_path, recommendations_summary}  │ │
│  └────────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────────┘
                            │
                            ▼ Orchestrator validates JSON + file
┌─────────────────────────────────────────────────────────────────┐
│  ORCHESTRATOR RETURNS FINAL JSON                                │
│  {                                                              │
│    "status": "complete",                                        │
│    "session_dir": "reports/runs/2025-01-15_143022/",            │
│    "phase_reports": {...},                                      │
│    "final_summary": {                                           │
│      "total_tables": 42,                                        │
│      "total_fields": 367,                                       │
│      "unused_fields": 23,                                       │
│      "verification_status": "confirmed",                        │
│      "estimated_savings_gb": 55.2                               │
│    }                                                            │
│  }                                                              │
└─────────────────────────────────────────────────────────────────┘
```

---

## Key Components Explained

### ★ Orchestrator (SKILL.md)
- Creates session directory with timestamp
- Spawns phases sequentially
- Passes context between phases
- Validates JSON + files after each phase
- Stops on first failure (fail-fast)
- Aggregates final results

### ★ Phase Agents (agents/*.md)
- Define what phase does
- Specify input/output contracts
- Document JSON schemas
- Handle errors gracefully

### ★ Reference Docs (references/*.md)
- Step-by-step instructions
- Examples and templates
- Quality checklists
- Error handling guides

### ★ Verification Script (scripts/*.sh)
- Deterministic (no randomness)
- Fast (seconds, not minutes)
- Structured JSON output
- No LLM usage (pure computation)
- Empirical validation

### ★ Session Directories (reports/runs/)
- One directory per workflow run
- Timestamp-based naming
- Preserves all phase outputs
- Audit trail for debugging
- Comparison across runs

---

## The "Money Shot" - Phase 4 Verification

**Traditional LLM workflow:**
```
Phase 2: "I found 23 unused fields"
Phase 3: "We can save 45GB by removing them"
Phase 5: "Here are my recommendations"

User: "How do I know this is correct?"
Agent: "Trust me?"
```

**Test harness workflow:**
```
Phase 2: "I found 23 unused fields" [writes report]
Phase 3: "We can save 45GB" [writes report]
Phase 4: "Running verification script..."
         Script: "Confirmed 21/23 fields unused"
         Script: "Revised 2 fields (actually 68% null, not 85%)"
         Script: "Found 3 additional unused fields"
         [writes verification report comparing manual vs script]
Phase 5: "Recommendations based on empirically validated data" [writes report]

User: "I can inspect all reports. Phase 4 ran real script. Trust verified ✅"
```

---

## Visual Legend

```
├── File or directory
│   └─→ Relationship or flow
★ CRITICAL - Pay special attention
┌─────┐
│ Box │ Process or component
└─────┘
```

---

## Quick Start Paths

**Path 1: Understand the Pattern (30 min)**
```
README.md → GUIDE-00 → GUIDE-01 → Done
```

**Path 2: Hands-On Practice (1 hour)**
```
README.md → GUIDE-00 → Exercise 1 → GUIDE-03 → Done
```

**Path 3: Build Your Own (Half day)**
```
All guides → All exercises → Adapt for your use case → Deploy
```

---

*This visual map provides a high-level overview of the entire learning lab structure.*
