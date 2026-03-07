# Constraints: Limiting Actions to Prevent Errors

Constraints are design elements that limit the possible actions a user can take. Used well, they make errors impossible or improbable. The underlying principle is simple: instead of telling users what not to do, make the wrong action physically, logically, or semantically impossible. Every constraint added is one fewer error the user can make.

## Four Constraint Types

### Physical Constraints

Physical constraints use shape, size, or material properties to restrict actions.

| Constraint | How It Works | Example |
|-----------|-------------|---------|
| Shape exclusion | Parts only fit one way | USB-A plug has a correct orientation; USB-C fits both ways |
| Size limitation | Object is too large/small for wrong use | A large plug cannot fit a small socket |
| Material resistance | Force required prevents accidental activation | Childproof medicine bottle requires push-and-twist |
| Barrier | Physical blockage prevents access | Guardrails prevent cars from leaving the road |

**Digital equivalent**: Input masks, character limits, file type restrictions, and minimum/maximum values.

### Cultural Constraints

Cultural constraints rely on shared social conventions and learned norms to guide behavior.

| Constraint | How It Works | Example |
|-----------|-------------|---------|
| Social norms | Expected behavior in context | Whispering in a library, facing forward in an elevator |
| Color conventions | Shared color meanings | Red for stop/danger, green for go/safe |
| Positional conventions | Expected placement of elements | OK/Cancel button order (platform-dependent) |
| Interaction conventions | Learned digital behaviors | Double-click to open, single-click to select |

**Design implication**: Cultural constraints are powerful but invisible. Violating them causes confusion even when the system technically works.

### Semantic Constraints

Semantic constraints use the meaning of a situation to limit the set of possible actions.

| Constraint | How It Works | Example |
|-----------|-------------|---------|
| Contextual meaning | Meaning restricts logical placement | A rearview mirror only makes sense facing the rear |
| Role meaning | Knowledge of purpose limits actions | A windshield is obviously not a door |
| Temporal meaning | Timing restricts when actions make sense | Cannot review an order before adding items |

**Digital equivalent**: Contextual menus that show only relevant actions, conditional fields that appear based on prior selections.

### Logical Constraints

Logical constraints use reasoning to limit what is possible through exclusion.

| Constraint | How It Works | Example |
|-----------|-------------|---------|
| Process of elimination | Only one option remains | Last puzzle piece can only go in the remaining hole |
| Mutual exclusion | Choosing A makes B impossible | Radio buttons: selecting one deselects others |
| Dependency chains | Step B requires step A | Cannot format text before selecting it |
| Completeness check | All parts must be present | Form cannot submit until all required fields are filled |

---

## Digital Constraint Implementations

### Input Validation as Constraint

| Validation Type | What It Constrains | Implementation |
|----------------|-------------------|----------------|
| **Type restriction** | Only numbers, only letters, specific format | `input type="email"`, `type="tel"`, regex patterns |
| **Range restriction** | Minimum and maximum values | `min="0" max="100"`, date ranges, slider bounds |
| **Length restriction** | Character count | `maxlength="280"`, with visible counter |
| **Format restriction** | Specific pattern required | Input mask for phone: (___) ___-____ |
| **Enum restriction** | Only predefined options allowed | Dropdown, radio buttons, autocomplete with fixed list |
| **Real-time validation** | Invalid input rejected as typed | Inline error showing before form submission |

### Best Practices for Input Validation

- Prefer prevention over detection: use a date picker instead of validating a typed date.
- Validate in real time, not only on submit. Show inline feedback as the user types.
- When rejecting input, explain what is expected: "Phone number must be 10 digits" not "Invalid input."
- Accept flexible formats and normalize internally: "1234567890", "(123) 456-7890", and "123-456-7890" should all be accepted for a phone number.

### Progressive Disclosure as Constraint

Progressive disclosure constrains what users see and interact with, reducing cognitive load and preventing premature actions.

| Pattern | What It Constrains | Example |
|---------|-------------------|---------|
| **Collapsed sections** | Hides advanced options until requested | "Advanced settings" expandable panel |
| **Wizard / stepper** | Shows only current step | Multi-step checkout flow |
| **Conditional fields** | Shows fields only when relevant | "Other" text field appears only when "Other" is selected |
| **Role-based visibility** | Shows features based on permissions | Admin panel visible only to admin users |
| **Contextual menus** | Shows only actions relevant to the selected item | Right-click menu changes based on element type |

### Disabled States and Forced Sequences

Disabled states constrain users by making actions visually present but temporarily unavailable.

| Pattern | When to Use | How to Implement |
|---------|------------|-----------------|
| **Disabled button** | Required precondition not met | Gray out button, add tooltip explaining why |
| **Locked wizard step** | Prior steps incomplete | Show step indicator but prevent skipping ahead |
| **Conditional enable** | Depends on another field's value | Enable "Confirm" only after checkbox is checked |
| **Time-gated action** | Action requires waiting period | "You can send again in 30 seconds" with countdown |
| **Auth-gated action** | Requires login or elevated permissions | Show the action but redirect to login on click |

**Critical rule for disabled states**: Always explain why the action is disabled. A disabled button with no explanation is a constraint that creates frustration rather than guiding users.

| Implementation | User Experience |
|---------------|----------------|
| Disabled button, no explanation | "Why can't I click this? Is it broken?" |
| Disabled button with tooltip | "I see -- I need to fill in the required fields first." |
| Disabled button with inline helper text | "Fill in all required fields to enable submission." |

### Undo/Redo as Error Recovery Constraint

Undo/redo does not prevent errors, but it constrains the impact of errors by making them reversible.

| Pattern | Implementation | Example |
|---------|---------------|---------|
| **Immediate undo** | Toast notification with "Undo" link | Gmail "Message sent. Undo" |
| **Action history** | List of recent actions with rollback | Google Docs version history |
| **Soft delete** | Items move to trash, not permanently deleted | Recycle bin, 30-day retention |
| **Autosave with versions** | Every change is saved and reversible | Google Docs, Figma auto-save |
| **Confirmation dialog** | "Are you sure?" before destructive action | Delete account confirmation |

### When to Use Confirmation Dialogs

Confirmation dialogs are appropriate only for:
- **Irreversible** actions (delete account, send broadcast email)
- **High-consequence** actions (charge credit card, publish to production)
- **Unusual** actions (something the user does rarely and might have triggered accidentally)

They are NOT appropriate for:
- Routine actions (saving a document, closing a tab)
- Actions that are easily reversible (moving an item, changing a setting)
- Frequent operations (every dialog slows the user down and trains them to click "OK" without reading)

---

## Constraint Design Patterns by Use Case

### E-Commerce Checkout

| Constraint | Type | Purpose |
|-----------|------|---------|
| Cannot proceed to payment without shipping address | Logical (forced sequence) | Prevents incomplete orders |
| Credit card field accepts only digits with auto-formatting | Physical (input mask) | Prevents format errors |
| "Place Order" disabled until terms checkbox is checked | Logical (dependency) | Ensures legal compliance |
| Quantity selector with min=1, max=99 | Physical (range) | Prevents zero or absurd quantities |
| Address autocomplete from verified database | Semantic (constrained options) | Prevents undeliverable addresses |

### User Registration

| Constraint | Type | Purpose |
|-----------|------|---------|
| Password strength meter with minimum requirements | Physical (validation) | Prevents weak passwords |
| Email format validation | Physical (format) | Prevents invalid email addresses |
| Username uniqueness check (real-time) | Logical (exclusion) | Prevents duplicate accounts |
| Age gate with date picker | Semantic (contextual) | Prevents underage registration |
| CAPTCHA before submission | Cultural (convention) + Logical | Prevents automated abuse |

### Content Management

| Constraint | Type | Purpose |
|-----------|------|---------|
| Draft / Published / Archived states with transitions | Logical (forced sequence) | Content must be reviewed before publishing |
| Character limits on titles and descriptions | Physical (length) | Prevents layout-breaking content |
| Image upload restricted to specific formats and sizes | Physical (type + size) | Prevents unsupported media |
| Scheduled publish date must be in the future | Semantic (temporal) | Prevents backdated publishing |
| Role-based editing permissions | Cultural (authority) + Logical | Prevents unauthorized changes |

---

## When Constraints Help vs. Frustrate

### Constraints That Help

| Scenario | Why It Helps |
|----------|-------------|
| Date picker instead of free text | Users cannot enter an invalid date format |
| Disabled "Next" until required fields are complete | Users cannot skip required information |
| Autocomplete for city/state from zip code | Reduces typing and prevents mismatched data |
| File upload limit with clear message | Prevents timeout errors on oversized files |
| Character counter approaching limit | Users adjust their content proactively |

### Constraints That Frustrate

| Scenario | Why It Frustrates |
|----------|------------------|
| Password rules that are excessively complex | Users cannot create a memorable password |
| Dropdown with 200+ country options | Slower than typing; users scroll endlessly |
| Forced sequence when steps are independent | Users cannot fill in information in their preferred order |
| Preventing paste into a "confirm email" field | Users must retype, increasing error rate |
| Requiring phone number when it is not needed | Users feel the product is collecting unnecessary data |

### The Constraint Spectrum

```
Too few constraints          Just right               Too many constraints
      |                         |                           |
  Error-prone             Error-free, smooth          Frustrating, slow
  Confusing               Guided                      Patronizing
  Flexible                Efficient                   Rigid
```

The goal is the middle zone: enough constraints to prevent errors, not so many that users feel restricted.

---

## Anti-Patterns: Over-Constraining Users

| Anti-Pattern | Problem | Better Approach |
|-------------|---------|----------------|
| **Preventing copy-paste in forms** | Increases errors by forcing manual re-entry | Allow paste; validate the result |
| **Session timeouts without warning** | Users lose work without notice | Warn before timeout, offer extension |
| **Forced password change every 90 days** | Users choose weaker passwords to cope | Monitor for breaches instead |
| **Maximum line length in text fields** | Users cannot write naturally | Use soft limits with warnings, not hard limits |
| **Blocking form submission for non-critical warnings** | Users cannot proceed despite having correct intent | Distinguish errors (block) from warnings (allow with note) |
| **Requiring all fields when most are optional** | Users abandon the form | Mark truly required fields; make the rest optional |

---

## Constraint Audit Checklist

### Error Prevention

- [ ] All form inputs have appropriate type constraints (number fields accept only numbers, etc.).
- [ ] Date and time inputs use pickers rather than free-text fields.
- [ ] Required fields are clearly marked and enforced before submission.
- [ ] Actions that depend on preconditions are disabled (with explanation) until preconditions are met.
- [ ] Destructive actions require confirmation or offer undo.

### Input Quality

- [ ] Input masks or autocomplete are used for structured data (phone, postal code, credit card).
- [ ] Range constraints are enforced with clear min/max indicators.
- [ ] Real-time validation provides feedback as the user types.
- [ ] Error messages explain what is expected, not just what is wrong.

### Sequence and Flow

- [ ] Multi-step processes enforce logical order when necessary.
- [ ] Independent steps can be completed in any order.
- [ ] The current step and remaining steps are visible.
- [ ] Users can go back to previous steps without losing data.

### Recovery

- [ ] Undo is available for all non-destructive actions.
- [ ] Soft delete (trash/archive) is used instead of permanent deletion.
- [ ] Autosave prevents data loss.
- [ ] Session recovery restores unsaved work after timeout or crash.

### Appropriateness

- [ ] No constraint exists purely for the system's convenience at the user's expense.
- [ ] Constraints match the severity of the potential error.
- [ ] Users are not forced to provide information that is not necessary for the task.
- [ ] Paste is allowed in all text fields.
- [ ] Flexible input formats are accepted and normalized (phone numbers, dates).
