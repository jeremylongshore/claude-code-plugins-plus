# GUIDE 00: Start Here - The Test Harness Pattern

**Read time:** 5 minutes
**Goal:** Understand the mental model before diving into code

---

## The Problem We're Solving

You ask an LLM to do multi-step work:
1. "Analyze this codebase"
2. "Find performance bottlenecks"
3. "Suggest optimizations"
4. "Verify your suggestions"
5. "Write a report"

**What usually happens:**
- Agent writes a wall of text
- You can't verify if it actually did the work
- No structured output (just narrative)
- If something's wrong, you can't tell where it failed
- Hard to reuse or automate

**What you wish happened:**
- Agent produces evidence of each step
- You can verify work was done
- Outputs are machine-readable
- Failures are clear and debuggable
- System is repeatable and composable

---

## The Solution: Test Harness Pattern

Think of this like a CI/CD pipeline for LLM work:

```
┌─────────────────────────────────────────────────────┐
│  ORCHESTRATOR (Main Skill)                          │
│  - Creates session directory (isolated run folder)  │
│  - Spawns phases in order                           │
│  - Validates outputs before continuing              │
│  - Aggregates final results                         │
└─────────────────────────────────────────────────────┘
                        │
                        ▼
    ┌───────────────────────────────────────┐
    │  PHASE 1: Initial Analysis            │
    │  - Reads instructions                 │
    │  - Does work                          │
    │  - Writes report file                 │
    │  - Returns JSON                       │
    └───────────────────────────────────────┘
                        │
                        ▼ (orchestrator validates)
    ┌───────────────────────────────────────┐
    │  PHASE 2: Deep Analysis               │
    │  - Reads Phase 1 report               │
    │  - Does more work                     │
    │  - Writes report file                 │
    │  - Returns JSON                       │
    └───────────────────────────────────────┘
                        │
                        ▼ (orchestrator validates)
    ┌───────────────────────────────────────┐
    │  PHASE 3: Risk Assessment             │
    │  - Reads Phase 1-2 reports            │
    │  - Calculates risks                   │
    │  - Writes report file                 │
    │  - Returns JSON                       │
    └───────────────────────────────────────┘
                        │
                        ▼ (orchestrator validates)
    ┌───────────────────────────────────────┐
    │  PHASE 4: VERIFICATION (KEY PHASE)    │
    │  - Reads Phase 2-3 conclusions        │
    │  - RUNS REAL SCRIPT                   │
    │  - Compares script vs conclusions     │
    │  - Writes verification report         │
    │  - Returns JSON                       │
    └───────────────────────────────────────┘
                        │
                        ▼ (orchestrator validates)
    ┌───────────────────────────────────────┐
    │  PHASE 5: Final Recommendations       │
    │  - Synthesizes all prior work         │
    │  - Prioritizes actions                │
    │  - Writes final report                │
    │  - Returns JSON                       │
    └───────────────────────────────────────┘
                        │
                        ▼
    ┌───────────────────────────────────────┐
    │  ORCHESTRATOR OUTPUT                  │
    │  {                                    │
    │    "status": "complete",              │
    │    "session_dir": "...",              │
    │    "phase_reports": {...},            │
    │    "final_summary": {...}             │
    │  }                                    │
    └───────────────────────────────────────┘
```

---

## Key Concepts

### 1. Session Directory
Every workflow run gets its own isolated folder:
```
reports/runs/2025-01-15_143022/
├── 01-initial-analysis.md
├── 02-deep-analysis.md
├── 03-risk-assessment.md
├── 04-verification.md
└── 05-recommendations.md
```

**Why:** Evidence. You can inspect what was actually done.

### 2. Strict JSON Contracts
Every phase MUST return this format:
```json
{
  "status": "complete",
  "report_path": "/absolute/path/to/report.md",
  "phase_summary": {
    "key1": "value1",
    "key2": "value2"
  }
}
```

**Why:** Machine-readable. The orchestrator can validate programmatically.

### 3. Validation Gates
After each phase, orchestrator checks:
- ✅ JSON is valid (not malformed)
- ✅ `status` is "complete"
- ✅ `report_path` file exists on disk
- ✅ Required summary keys are present

**Why:** Fail-fast. If Phase 2 fails, don't waste time on Phase 3-5.

### 4. The Verification Phase (Phase 4)
This is the "money shot" that makes it feel real:
- Reads conclusions from Phases 2-3
- Runs an ACTUAL SCRIPT (not LLM analysis)
- Compares script output vs manual conclusions
- Reports: confirmed, revised, unexpected findings

**Why:** Empirical validation. Script doesn't lie.

### 5. Reference Instruction Docs
Each phase has a corresponding instruction file:
```
references/
├── 01-phase-1.md       # "Do exactly this for Phase 1"
├── 02-phase-2.md       # "Do exactly this for Phase 2"
├── 03-phase-3.md
├── 04-verify-with-script.md  # "Run this script, compare results"
└── 05-phase-5.md
```

**Why:** Deterministic behavior. Same instructions = same outputs.

---

## The Mental Model

Think of it as a **scientific experiment protocol**:

1. **Hypothesis Phase (1-3):** Analyze, form conclusions
2. **Verification Phase (4):** Run experiment to test hypothesis
3. **Conclusion Phase (5):** Synthesize validated findings

Or as a **code review pipeline**:

1. **Analysis:** What's the code doing?
2. **Linting:** Run automated checks
3. **Testing:** Run test suite
4. **Verification:** Compare manual vs automated findings
5. **Recommendation:** What should we change?

Or as a **forensic investigation**:

1. **Scene Analysis:** What happened?
2. **Evidence Collection:** Gather data
3. **Risk Assessment:** What's the impact?
4. **Lab Testing:** Run forensic tests
5. **Report:** Official findings

---

## Why This Works

**Traditional LLM workflow:**
```
User: "Analyze this and give recommendations"
Agent: [writes 5000 words of text]
User: "Uh... is this correct?"
Agent: "Yes! Trust me!"
User: "How do I verify?"
Agent: "...you could manually check everything I said?"
```

**Test harness workflow:**
```
User: "Run schema optimization workflow"
Orchestrator: "Creating session directory..."
Orchestrator: "Phase 1 complete. Report: ./01-analysis.md"
Orchestrator: "Phase 2 complete. Report: ./02-utilization.md"
Orchestrator: "Phase 3 complete. Report: ./03-impact.md"
Orchestrator: "Phase 4 running verification script..."
Orchestrator: "Script confirmed 21/23 conclusions. Revised 2."
Orchestrator: "Phase 5 complete. Final JSON: {...}"
User: "I can inspect all 5 reports. Phase 4 ran real script. Trust verified."
```

---

## What You'll Learn

By the end of this lab, you'll be able to:

1. **Understand** the test harness pattern and why it's powerful
2. **Navigate** the reference implementation (schema-optimization)
3. **Modify** phases and reference docs for your needs
4. **Build** your own multi-phase workflow from scratch
5. **Debug** when phases fail or return invalid outputs
6. **Deploy** production-ready workflows using this pattern

---

## Quick Terminology

| Term | Meaning |
|------|---------|
| **Orchestrator** | Main skill that creates session dir, spawns phases, validates outputs |
| **Phase Agent** | Subagent that executes one step of workflow |
| **Session Directory** | Isolated run folder with timestamp (e.g., `runs/2025-01-15_143022/`) |
| **Reference Doc** | Step-by-step instructions for a phase (e.g., `references/01-phase-1.md`) |
| **JSON Contract** | Required output format: `{ status, report_path, summary }` |
| **Validation Gate** | Orchestrator checks after each phase: JSON valid? File exists? Keys present? |
| **Verification Phase** | Phase that runs real script to empirically validate prior conclusions |

---

## Next Steps

**Option 1: Dive into code**
Open `schema-optimization/SKILL.md` and start reading the orchestrator logic.

**Option 2: Learn the pattern deeply**
Read `GUIDE-01-PATTERN-EXPLAINED.md` for architectural breakdown.

**Option 3: Hands-on practice**
Jump to `exercises/exercise-1-run-workflow.md` and execute the reference implementation.

**Recommended for most people:**
Read GUIDE-01 next, then do Exercise 1.

---

**Key Insight:** This pattern turns "LLM wrote some text" into "LLM executed a validated procedure with evidence and structured outputs."

That's the difference between a chatbot and a production system.

---

*Next: GUIDE-01-PATTERN-EXPLAINED.md*
