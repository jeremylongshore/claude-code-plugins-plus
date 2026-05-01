# Resolving Heuristic Conflicts

When usability principles contradict each other—frameworks for making trade-off decisions.

## The Nature of Conflicts

Usability heuristics are guidelines, not laws. In real design, they often pull in opposite directions. Good UX design requires recognizing these tensions and making thoughtful trade-offs.

**Common tension patterns:**
- Simplicity vs. Power
- Consistency vs. Optimal for context
- Efficiency vs. Error prevention
- User control vs. Guidance
- Discoverability vs. Clean interface

---

## Major Heuristic Conflicts

### 1. Simplicity vs. Flexibility

**The tension:**
- "Keep it simple" (Krug, Nielsen)
- "Support user control and freedom" (Nielsen #3)
- "Flexibility and efficiency of use" (Nielsen #7)

**Example:** Photo editing app
- Simple: Few options, quick editing
- Flexible: Many controls, professional results

**Resolution framework:**

| Factor | Lean Simple | Lean Flexible |
|--------|-------------|---------------|
| User expertise | Novice | Expert |
| Task frequency | Occasional | Daily |
| Consequences of error | Low | High |
| Time pressure | High | Low |

**Design patterns:**
- Progressive disclosure (simple default, power underneath)
- Personas-based modes (Basic/Advanced)
- Contextual features (show when relevant)

### 2. Consistency vs. Context Optimization

**The tension:**
- "Consistency and standards" (Nielsen #4)
- "Match between system and real world" (Nielsen #2)

**Example:** Destructive actions
- Consistent: Red "Delete" button everywhere
- Context-optimized: Prominent delete for items that should be deleted, hidden for critical data

**Resolution framework:**

| Factor | Lean Consistent | Lean Contextual |
|--------|-----------------|-----------------|
| User base diversity | High | Low |
| Learning curve concern | Yes | No |
| Action frequency | Common | Rare |
| Mental model strength | Established | Forming |

**Design patterns:**
- Consistent patterns, contextual prominence
- Same actions, different emphasis
- Gradual introduction of contextual variations

### 3. Efficiency vs. Error Prevention

**The tension:**
- "Error prevention" (Nielsen #5)
- "Flexibility and efficiency of use" (Nielsen #7)

**Example:** Checkout flow
- Error prevention: Confirmation at every step
- Efficiency: One-click purchase

**Resolution framework:**

| Factor | Lean Error Prevention | Lean Efficiency |
|--------|----------------------|-----------------|
| Reversibility | Irreversible | Easily undone |
| Cost of error | High (money, data) | Low |
| User familiarity | New users | Power users |
| Frequency | Rare | Very frequent |

**Design patterns:**
- Undo instead of confirm (efficient + safe)
- Confidence-based friction (add steps for risky actions)
- User-controlled safety level

### 4. Discoverability vs. Clean Interface

**The tension:**
- "Recognition rather than recall" (Nielsen #6)
- "Aesthetic and minimalist design" (Nielsen #8)

**Example:** Feature-rich application
- Discoverable: Show all options visibly
- Clean: Hide features until needed

**Resolution framework:**

| Factor | Lean Discoverable | Lean Clean |
|--------|-------------------|------------|
| Feature frequency | Core features | Edge cases |
| User expertise | Beginner | Expert |
| Task complexity | Simple | Complex |
| Screen real estate | Generous | Limited |

**Design patterns:**
- Primary actions visible, secondary in menus
- Progressive disclosure
- Contextual menus
- Search/command palettes for power users

### 5. Guidance vs. User Control

**The tension:**
- Help users avoid errors
- Respect user autonomy

**Example:** Form validation
- Guidance: Prevent submission until valid
- Control: Let users submit and see what happens

**Resolution framework:**

| Factor | Lean Guidance | Lean Control |
|--------|---------------|--------------|
| User expertise | Novice | Expert |
| Error recovery | Difficult | Easy |
| System tolerance | Low (strict rules) | High (flexible) |
| User frustration with restrictions | Low | High |

**Design patterns:**
- Inline guidance (not blocking)
- Warnings vs. blockers
- "Are you sure?" rather than "You can't"

---

## Resolution Framework

### Step 1: Identify the Conflict

Name the specific heuristics in tension:
- Which principle says do A?
- Which principle says do B?
- Why can't we fully satisfy both?

### Step 2: Assess the Context

Consider:
- **User type:** Novice vs. expert
- **Task criticality:** Browsing vs. financial transaction
- **Frequency:** One-time vs. daily
- **Reversibility:** Can they undo?
- **Consequence:** What happens if wrong?

### Step 3: Prioritize for This Context

| Context | Usually Prioritize |
|---------|-------------------|
| Critical data, irreversible | Error prevention > Efficiency |
| Frequent actions, low stakes | Efficiency > Error prevention |
| New users, unfamiliar domain | Guidance > Control |
| Expert users, familiar domain | Flexibility > Simplicity |
| Limited screen, focused task | Minimalism > Discoverability |
| Learning interface | Discoverability > Minimalism |

### Step 4: Design for Both When Possible

Often, clever design satisfies both:

| Conflict | Both-And Solution |
|----------|-------------------|
| Simple vs. Powerful | Progressive disclosure |
| Efficient vs. Safe | Undo instead of confirm |
| Clean vs. Discoverable | Contextual reveal |
| Consistent vs. Optimal | Consistent patterns, variable emphasis |
| Guided vs. Controlled | Warnings, not blockers |

### Step 5: Test the Trade-off

Validate with real users:
- Does the chosen priority work for target users?
- Are edge cases handled acceptably?
- Do users understand why limitations exist?

---

## Common Conflict Scenarios

### Scenario: Onboarding Flow

**Conflict:** Efficiency (skip it) vs. Guidance (require it)

**Resolution:**
- Allow skip but show value
- Defer to contextual moments
- Progressive onboarding during natural use

### Scenario: Mobile Navigation

**Conflict:** Discoverability (show all options) vs. Minimalism (hamburger menu)

**Resolution:**
- Bottom navigation for 3-5 key items
- Hamburger for secondary items
- Tab bar > hamburger for primary navigation

### Scenario: Form Validation

**Conflict:** Error prevention (validate immediately) vs. Efficiency (let them type)

**Resolution:**
- Validate on blur (not on keystroke)
- Show errors inline, not modal
- Allow submission, show all errors

### Scenario: Confirmation Dialogs

**Conflict:** Error prevention (confirm everything) vs. Efficiency (just do it)

**Resolution:**
- Confirm only irreversible/high-cost actions
- Provide undo instead of confirm
- Use clear language about consequences

### Scenario: Default Settings

**Conflict:** User control (let them configure) vs. Simplicity (sensible defaults)

**Resolution:**
- Smart defaults that work for 80%
- Easy access to change settings
- Don't require configuration to start

---

## Decision Documentation

When making trade-off decisions, document:

```markdown
## Design Decision: [Feature]

### Conflict
[Heuristic A] suggests we should...
[Heuristic B] suggests we should...

### Context
- User type: [Novice/Expert]
- Task: [Critical/Casual]
- Frequency: [Daily/Occasional]
- Reversibility: [Yes/No]

### Decision
We chose to prioritize [Heuristic] because...

### Mitigation
We addressed the other concern by...

### Validation
We'll know this is right when...
```

---

## Key Principles

### 1. Context Is King

The same conflict should be resolved differently in different contexts. A banking app and a social media app may reach opposite conclusions.

### 2. Know Your Users

The trade-off depends heavily on user expertise and expectations. Test with real users, not assumptions.

### 3. Design for Both When Possible

Often, the conflict is artificial and clever design can satisfy both principles.

### 4. Make Conscious Trade-offs

Don't accidentally violate a heuristic. Violate it consciously with reasoning.

### 5. Document Decisions

Future you (and your team) will want to know why choices were made.

### 6. Revisit Trade-offs

As products and users evolve, optimal trade-offs may shift. Periodically review past decisions.
