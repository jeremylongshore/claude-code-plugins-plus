# Design of Everyday Things -- Implementation Guide

## Overview

Apply Don Norman's design principles (Affordances, Signifiers, Mappings, Feedback, Constraints, Conceptual Models) to audit and improve product UX.

## Core Concepts Applied to Digital Products

### 1. Affordances & Signifiers

**Affordance:** What action is possible.
**Signifier:** How you communicate that affordance.

```markdown
## Signifier Audit

For each interactive element, ask:
- Does it look clickable/tappable?
- Is the cursor change correct (pointer vs. default)?
- Does it have enough visual weight to be noticed?

Common failures:
- Links that look like plain text
- Buttons that look like labels
- Clickable images with no hover state
```

### 2. Mappings

The relationship between controls and their effects should be spatial and intuitive.

```markdown
## Mapping Audit

Good mapping examples:
- Up arrow = increase (volume, font size)
- Left/right swipe = previous/next item
- Drag handle = resize element

Bad mapping (fix these):
- "Submit" button that deletes data
- Undo button that is far from the action
- Scrollbar on wrong side of content
```

### 3. Feedback

Every action needs immediate, clear, perceivable feedback.

```markdown
## Feedback Checklist

- [ ] Button shows loading state during async action
- [ ] Form shows inline validation (not just on submit)
- [ ] Success message appears within 200ms of action
- [ ] Error messages name the problem AND the fix
- [ ] Undo is available immediately after destructive actions
```

### 4. Constraints

Prevent errors by making wrong actions impossible or difficult.

```markdown
## Constraint Types

Physical: "Delete" button is disabled until checkbox is checked
Logical: Cannot save form with empty required fields
Cultural: Red = warning/danger, Green = success
Semantic: "Are you sure?" confirmation for irreversible actions
```

### 5. Conceptual Models

Users build mental models. Design to match the correct model.

```markdown
## Conceptual Model Audit

Question: What mental model does the user bring?
(e.g., "email inbox" model, "folder/file" model, "feed" model)

Does your UI reinforce or violate that model?

Mismatch example: A "Save" button that auto-saves AND requires manual save confirmation.
```

## UX Audit Template (Norman Framework)

```markdown
## UX Audit: [Feature Name]

Affordances: Are possible actions obvious? ___
Signifiers: Do interactive elements signal their affordance? ___
Mapping: Is the control-effect relationship spatial/intuitive? ___
Feedback: Is there clear, immediate response to every action? ___
Constraints: Are errors prevented through design? ___
Conceptual model: Does the UI match user expectations? ___

Top 3 issues:
1. ___
2. ___
3. ___
```

## References

- Norman, D. (1988). *The Design of Everyday Things.* Basic Books.
