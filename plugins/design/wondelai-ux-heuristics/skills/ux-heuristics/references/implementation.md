# UX Heuristics -- Nielsen's 10 Principles Implementation Guide

## Overview

Apply Jakob Nielsen's 10 Usability Heuristics to conduct systematic UX audits of web applications, dashboards, and mobile interfaces.

## The 10 Heuristics with Application Examples

### 1. Visibility of System Status

Users should always know what is happening.

```markdown
Checklist:
- [ ] Loading states shown for all async operations (skeleton loaders or spinners)
- [ ] Progress indicators for multi-step processes
- [ ] Success/error messages appear immediately after actions
- [ ] Active navigation item is visually distinguished
- [ ] File upload progress shown (not just spinner)
```

### 2. Match Between System and Real World

Use language and concepts the user knows.

```markdown
Checklist:
- [ ] No jargon or technical terms in user-facing UI
- [ ] Icons match real-world analogies (trash = delete, envelope = email)
- [ ] Dates shown in user's locale format
- [ ] Error messages in plain language ("Email is invalid" not "ERR_VALIDATION_422")
```

### 3. User Control and Freedom

Users make mistakes. Make it easy to undo.

```markdown
Checklist:
- [ ] Undo available immediately after every destructive action
- [ ] "Cancel" button present in all dialogs and forms
- [ ] Browser back button works as expected
- [ ] Accidental modal dismissal is easy (click outside, Escape key)
- [ ] Deleted items go to trash (30-day recovery)
```

### 4. Consistency and Standards

Platform conventions should be followed.

```markdown
Checklist:
- [ ] Same label for the same action across the app
- [ ] Navigation structure consistent across pages
- [ ] Colors mean the same thing everywhere (red = danger/error)
- [ ] External link indicators consistent
```

### 5-10. Quick Audit Sheet

```markdown
| Heuristic | Score (1-5) | Top Issue |
|-----------|------------|-----------|
| 5. Error Prevention | | |
| 6. Recognition over Recall | | |
| 7. Flexibility (shortcuts) | | |
| 8. Aesthetic & Minimalist | | |
| 9. Error Recovery | | |
| 10. Help & Documentation | | |
```

## Heuristic Audit Process

```markdown
## Audit Worksheet

Product: ___
Evaluator: ___
Date: ___

For each screen / flow, rate each heuristic 0-4:
0 = Catastrophic failure
1 = Major usability problem
2 = Minor usability problem
3 = Cosmetic issue
4 = No problem

Issues found:
| Heuristic | Description | Severity | Recommended Fix |
|-----------|-------------|----------|----------------|
| H1 | ___ | ___ | ___ |

Prioritization:
- Severity 0-1: Fix immediately (pre-launch blocker)
- Severity 2: Fix in next sprint
- Severity 3: Add to backlog
```

## Severity Rating Scale

| Score | Label | Definition |
|-------|-------|-----------|
| 0 | Catastrophic | Prevents task completion |
| 1 | Critical | Major difficulty completing task |
| 2 | Moderate | Causes confusion, user may recover |
| 3 | Minor | Cosmetic or edge-case problem |

## References

- Nielsen, J. (1994). Enhancing the explanatory power of usability heuristics. *CHI '94.*
- [NN/g 10 Heuristics](https://www.nngroup.com/articles/ten-usability-heuristics/)
