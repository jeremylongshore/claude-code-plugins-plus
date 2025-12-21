# Test Harness Pattern Learning Lab

**Purpose:** Safe sandbox for learning and building phased workflow skills with strict validation.

**Status:** Reference implementation of schema-optimization workflow (5-phase test harness)

---

## Quick Start

```bash
# You are here:
cd workspace/lab/

# Explore the reference implementation:
ls -la schema-optimization/

# Read the learning guides:
cat GUIDE-00-START-HERE.md          # Start here (5 min read)
cat GUIDE-01-PATTERN-EXPLAINED.md   # Deep dive on pattern (15 min)
cat GUIDE-02-BUILDING-YOUR-OWN.md   # Build your own workflow (30 min)
cat GUIDE-03-DEBUGGING-TIPS.md      # Troubleshooting common issues
```

---

## What's Inside

### Reference Implementation
**`schema-optimization/`** - Complete 5-phase workflow skill system
- Orchestrator that creates session directories, spawns phases, validates outputs
- 5 phase agents with strict JSON contracts
- Reference instruction docs (the "do exactly this" procedures)
- Real verification script (Phase 4 runs actual shell script)
- Sample outputs showing realistic workflow results

### Learning Guides
1. **GUIDE-00-START-HERE.md** - Introduction and mental model (5 min)
2. **GUIDE-01-PATTERN-EXPLAINED.md** - Why this pattern works, component breakdown (15 min)
3. **GUIDE-02-BUILDING-YOUR-OWN.md** - Step-by-step: adapt this for your use case (30 min)
4. **GUIDE-03-DEBUGGING-TIPS.md** - Common pitfalls and solutions (15 min)
5. **ORCHESTRATION-PATTERN.md** ⭐ - Complete reference guide (60 min) - The definitive deep-dive into subagent orchestration with contracts, verification, and advanced patterns

### Interactive Examples
**`exercises/`** - Hands-on practice
- Exercise 1: Run the reference workflow
- Exercise 2: Modify Phase 4 verification script
- Exercise 3: Add a new Phase 6
- Exercise 4: Build a 3-phase workflow from scratch

---

## Why This Pattern Matters

Traditional LLM workflows are fragile:
- Agent writes text, you can't verify it's correct
- No evidence of work performed
- Hard to debug when it fails
- Outputs are unstructured

**Test harness pattern solves this:**
- Agent MUST produce file artifact (evidence)
- Agent MUST return strict JSON (machine-checkable)
- Orchestrator validates before continuing
- Each phase builds on validated prior work
- Failure points are clear and debuggable

**Real-world applications:**
- Data pipeline validation (this example)
- Code review workflows (analyze → lint → test → security scan → report)
- Research synthesis (search → extract → analyze → verify → synthesize)
- Compliance audits (collect → analyze → verify → remediate → report)

---

## Learning Path

**Beginner (1 hour):**
1. Read GUIDE-00-START-HERE.md
2. Explore schema-optimization/ structure
3. Read one phase agent contract (agents/phase_1.md)
4. Skim ORCHESTRATION-PATTERN.md for big picture
4. Look at corresponding reference doc (references/01-phase-1.md)
5. Run Exercise 1: Execute the workflow

**Intermediate (3 hours):**
1. Read GUIDE-01-PATTERN-EXPLAINED.md
2. Study orchestrator validation logic (SKILL.md)
3. Run Exercise 2: Modify verification script
4. Read GUIDE-02-BUILDING-YOUR-OWN.md
5. Run Exercise 3: Add Phase 6

**Advanced (1 day):**
1. Read GUIDE-03-DEBUGGING-TIPS.md
2. Run Exercise 4: Build 3-phase workflow from scratch
3. Adapt pattern for your own use case
4. Deploy to production (move out of lab/)

---

## File Structure

```
workspace/lab/
├── README.md (you are here)
├── GUIDE-00-START-HERE.md
├── GUIDE-01-PATTERN-EXPLAINED.md
├── GUIDE-02-BUILDING-YOUR-OWN.md
├── GUIDE-03-DEBUGGING-TIPS.md
├── schema-optimization/          # Reference implementation
│   ├── SKILL.md                  # Orchestrator
│   ├── agents/                   # Phase subagents
│   │   ├── phase_1.md
│   │   ├── phase_2.md
│   │   ├── phase_3.md
│   │   ├── phase_4.md
│   │   └── phase_5.md
│   ├── references/               # Step-by-step procedures
│   │   ├── 01-phase-1.md
│   │   ├── 02-phase-2.md
│   │   ├── 03-phase-3.md
│   │   ├── 04-verify-with-script.md
│   │   └── 05-phase-5.md
│   ├── scripts/                  # Deterministic tools
│   │   └── analyze_field_utilization.sh
│   └── reports/                  # Output artifacts
│       ├── runs/                 # Session directories (created at runtime)
│       └── _samples/             # Example outputs
│           └── 2025-01-15_143022/
│               ├── 01-initial-schema-analysis.md
│               ├── 02-field-utilization-analysis.md
│               ├── 03-impact-assessment.md
│               ├── 04-field-utilization-verification.md
│               └── 05-final-recommendations.md
└── exercises/
    ├── exercise-1-run-workflow.md
    ├── exercise-2-modify-script.md
    ├── exercise-3-add-phase-6.md
    └── exercise-4-build-from-scratch.md
```

---

## Design Principles

1. **Evidence-Based**: Every phase writes a file (can't fake it)
2. **Machine-Checkable**: JSON outputs can be validated programmatically
3. **Fail-Fast**: Orchestrator stops on first validation failure
4. **Composable**: Phases are independent, reusable components
5. **Debuggable**: Clear failure points, structured outputs
6. **Repeatable**: Same inputs = same outputs (deterministic scripts)

---

## gitignore Status

This entire `workspace/` directory is gitignored:
- Safe to experiment freely
- No risk of committing test artifacts
- Can run real workflows with real data
- Delete and rebuild anytime

When you build something production-ready:
1. Move it out of workspace/
2. Clean up any test data
3. Add proper documentation
4. Commit to version control

---

## Questions?

**Q: Can I modify the reference implementation?**
A: Yes! That's the point. This is a learning sandbox.

**Q: What if I break something?**
A: Just delete and rebuild. Or refer to the guides.

**Q: Can I use this pattern for non-data workflows?**
A: Absolutely. See GUIDE-02-BUILDING-YOUR-OWN.md for examples.

**Q: Is this production-ready?**
A: The pattern is. The reference implementation is educational.
For production: add error handling, logging, monitoring, tests.

---

**Next Step:** Open `GUIDE-00-START-HERE.md` and start learning.

---

*Intent Solutions IO - Learning Lab*
*Created: 2025-01-15*
