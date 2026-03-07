# Nielsen's 10 Usability Heuristics

Jakob Nielsen's 10 general principles for interaction design, with practical examples and common violations.

---

## 1. Visibility of System Status

**Principle:** The system should always keep users informed about what is going on, through appropriate feedback within reasonable time.

### Examples of Good Implementation

| Situation | Good Feedback |
|-----------|---------------|
| File uploading | Progress bar with percentage |
| Form submitted | "Your message has been sent" |
| Action processing | Loading spinner |
| Background task | "Syncing 3 files..." notification |
| Successful action | Green checkmark confirmation |

### Common Violations

| Violation | Problem | Fix |
|-----------|---------|-----|
| No loading indicator | User thinks it's broken | Add spinner/progress |
| Silent failures | User thinks action worked | Show error message |
| Delayed feedback | User clicks again | Immediate visual response |
| No confirmation | "Did that work?" | Confirm successful actions |
| Hidden status | User can't find progress | Surface status prominently |

### Severity Examples

- **Minor (1):** Save button has no "saved" confirmation
- **Major (3):** Payment processing with no indicator
- **Catastrophic (4):** Form submit shows nothing, user submits multiple times

---

## 2. Match Between System and Real World

**Principle:** The system should speak the users' language, with words, phrases, and concepts familiar to the user, rather than system-oriented terms.

### Examples of Good Implementation

| System Term | User-Friendly Term |
|-------------|-------------------|
| Authenticate | Sign in |
| Terminate | Cancel / End |
| Query | Search |
| Repository | Folder |
| Navigate to | Go to |
| Initiate | Start |

### Real-World Metaphors

| Digital Element | Real-World Match |
|-----------------|------------------|
| Trash/Recycle bin | Waste basket |
| Folder | File folder |
| Desktop | Physical desk |
| Shopping cart | Store cart |
| Bookmark | Physical bookmark |

### Common Violations

| Violation | Problem | Fix |
|-----------|---------|-----|
| Technical jargon | Confusion | Use plain language |
| Internal names | Meaningless to users | User-tested labels |
| Inconsistent terms | Same thing, different names | One term per concept |
| Unfamiliar icons | Users guess wrong | Add labels or tooltips |
| Illogical order | Not matching expectations | Follow real-world sequences |

---

## 3. User Control and Freedom

**Principle:** Users often choose system functions by mistake and need a clearly marked "emergency exit" to leave the unwanted state without having to go through an extended dialogue.

### Examples of Good Implementation

| Action | Escape Route |
|--------|--------------|
| Accidentally deleted email | Undo button (Gmail) |
| Wrong menu opened | Click outside to close |
| Filled form incorrectly | Clear form / Reset |
| Navigated wrong | Back button works |
| Started wrong workflow | Cancel / Exit anytime |

### Common Violations

| Violation | Problem | Fix |
|-----------|---------|-----|
| No undo | Users afraid to act | Add undo for all actions |
| Forced wizards | Can't skip or go back | Allow non-linear navigation |
| Modal traps | Can't escape | Clear close/cancel buttons |
| Broken back button | Frustration | Never hijack browser history |
| Immediate deletion | No recovery | Soft delete + undo option |

### Key Principle

**Undo > Confirmation dialogs**

Users click through "Are you sure?" without reading. Undo lets them act confidently.

---

## 4. Consistency and Standards

**Principle:** Users should not have to wonder whether different words, situations, or actions mean the same thing. Follow platform conventions.

### Types of Consistency

| Type | Example |
|------|---------|
| **Internal** | Same button style throughout your app |
| **External** | Same patterns as other apps |
| **Visual** | Same colors mean same things |
| **Functional** | Same action = same result |
| **Linguistic** | Same terms for same concepts |

### Platform Conventions

| Element | Convention |
|---------|------------|
| Logo | Top left, links to home |
| Search | Top right, magnifying glass |
| Cart | Top right, shopping cart icon |
| Menu (mobile) | Hamburger icon |
| Primary action | Right side or bottom of form |
| Cancel | Left of primary action (or text link) |

### Common Violations

| Violation | Problem | Fix |
|-----------|---------|-----|
| Different button styles | Confusion about importance | Consistent button hierarchy |
| Same word, different meanings | Misunderstanding | One term per concept |
| Unexpected link behavior | New tab when expecting same tab | Follow conventions |
| Non-standard icons | Guessing game | Use recognized icons |
| Inconsistent layouts | Relearning each page | Template-based layouts |

---

## 5. Error Prevention

**Principle:** Even better than good error messages is a careful design which prevents a problem from occurring in the first place.

### Prevention Strategies

| Strategy | Example |
|----------|---------|
| **Constraints** | Date picker instead of text field |
| **Suggestions** | Autocomplete |
| **Defaults** | Pre-fill common values |
| **Confirmation** | "Delete permanently?" for destructive actions |
| **Warnings** | "Unsaved changes" before leaving |

### Types of Errors to Prevent

| Error Type | Prevention |
|------------|------------|
| **Slips** (accidental) | Confirmation, undo, large targets |
| **Mistakes** (wrong intention) | Clear instructions, better defaults |
| **Data errors** | Validation, formatting help |
| **Navigation errors** | Clear labels, undo |

### Common Violations

| Violation | Problem | Fix |
|-----------|---------|-----|
| Free text for constrained data | Invalid entries | Dropdowns, pickers |
| No save warning | Lost work | "Unsaved changes" prompt |
| Easy destructive actions | Accidental deletion | Require confirmation |
| Accepting bad input | Garbage data | Inline validation |
| Ambiguous choices | Wrong selection | Clear differentiation |

---

## 6. Recognition Rather Than Recall

**Principle:** Minimize the user's memory load by making objects, actions, and options visible. Don't require users to remember information.

### Recognition Techniques

| Instead of | Do This |
|------------|---------|
| User remembers command | Show menu of options |
| User types from memory | Dropdown/autocomplete |
| User remembers where they were | Breadcrumbs, recent history |
| User remembers codes | Show decoded values |
| User recalls previous info | Show previous entries |

### Examples

| Bad (Recall) | Good (Recognition) |
|--------------|-------------------|
| "Enter country code" | Dropdown with country names |
| Command-line interface | Graphical menus |
| "See page 47 for options" | Options shown in context |
| "Re-enter your email" | Pre-filled from previous step |
| Complex keyboard shortcuts | Visible toolbar buttons |

### Common Violations

| Violation | Problem | Fix |
|-----------|---------|-----|
| Empty form fields | User must remember format | Placeholder examples |
| Hidden actions | User forgets they exist | Keep visible or in menus |
| No recent items | User re-searches | Show search history |
| Unlabeled icons | User guesses meaning | Add text labels |
| Disconnected workflows | User loses context | Show progress, breadcrumbs |

---

## 7. Flexibility and Efficiency of Use

**Principle:** Accelerators—unseen by the novice user—may often speed up the interaction for the expert user. Allow users to tailor frequent actions.

### Accelerators for Experts

| Feature | Example |
|---------|---------|
| **Keyboard shortcuts** | Ctrl+S to save |
| **Touch gestures** | Swipe to archive |
| **Recent/Favorites** | Quick access to common items |
| **Saved searches** | One-click complex queries |
| **Customization** | Personalized dashboard |
| **Bulk actions** | Select all + action |

### Progressive Disclosure

| User Level | What They See |
|------------|---------------|
| Novice | Essential features only |
| Intermediate | Common advanced options |
| Expert | Full power (shortcuts, customization) |

### Common Violations

| Violation | Problem | Fix |
|-----------|---------|-----|
| No shortcuts | Experts slowed down | Add keyboard shortcuts |
| No bulk operations | Tedious repetition | Add multi-select |
| Required tutorials | Experts frustrated | Allow skipping |
| Hidden power features | Experts don't find them | Discoverable advanced mode |
| No customization | Forced workflows | Allow personalization |

---

## 8. Aesthetic and Minimalist Design

**Principle:** Dialogues should not contain information which is irrelevant or rarely needed. Every extra unit of information competes with the relevant units.

### Principles

| Principle | Application |
|-----------|-------------|
| **Signal/Noise** | Increase signal, reduce noise |
| **Visual hierarchy** | Important things stand out |
| **Whitespace** | Give elements room to breathe |
| **Content priority** | Show what matters, hide what doesn't |
| **Progressive disclosure** | Complexity on demand |

### What to Remove

| Remove | Why |
|--------|-----|
| Rarely-used features | Clutter |
| Decorative elements | Distraction |
| Redundant text | Noise |
| Unnecessary options | Decision fatigue |
| Instructions users skip | Wasted space |

### Common Violations

| Violation | Problem | Fix |
|-----------|---------|-----|
| Cluttered screens | Overwhelming | Remove/hide secondary |
| Everything is "important" | Nothing stands out | Create hierarchy |
| Long blocks of text | Nobody reads | Break up, summarize |
| Too many colors | Visual noise | Limit palette |
| Dense layouts | Hard to scan | Add whitespace |

---

## 9. Help Users Recognize, Diagnose, and Recover from Errors

**Principle:** Error messages should be expressed in plain language (no codes), precisely indicate the problem, and constructively suggest a solution.

### Good Error Message Components

1. **What happened** (plain language)
2. **Why it happened** (if helpful)
3. **How to fix it** (specific action)

### Examples

| Bad Error | Good Error |
|-----------|------------|
| "Error 500" | "Something went wrong. Please try again." |
| "Invalid input" | "Email must include @" |
| "Failed" | "Payment declined. Check card number or try different card." |
| "Null reference exception" | "We couldn't load your data. Refresh the page." |

### Error Message Guidelines

| Guideline | Example |
|-----------|---------|
| Use plain language | "Connection failed" not "ECONNREFUSED" |
| Be specific | "Password too short" not "Invalid password" |
| Provide action | "Try again" button visible |
| Don't blame user | "Card declined" not "You entered wrong info" |
| Maintain context | Keep filled data, highlight error field |

### Common Violations

| Violation | Problem | Fix |
|-----------|---------|-----|
| Technical jargon | Confusion | Translate to plain English |
| No solution | User stuck | Include next steps |
| Generic messages | Not helpful | Be specific |
| Blaming language | Defensive users | Neutral, helpful tone |
| Clearing form on error | Punishment | Preserve user input |

---

## 10. Help and Documentation

**Principle:** Even though it's better if the system can be used without documentation, it may be necessary to provide help and documentation. Such information should be easy to search, focused on the user's task, and not be too large.

### Characteristics of Good Help

| Characteristic | Implementation |
|----------------|----------------|
| **Searchable** | Full-text search |
| **Task-focused** | "How to..." format |
| **Contextual** | In-page tooltips |
| **Scannable** | Short paragraphs, lists |
| **Actionable** | Step-by-step instructions |

### Types of Help

| Type | When to Use |
|------|-------------|
| **Inline help** | Tooltips, hints | Next to complex fields |
| **Contextual help** | "?" icons | For non-obvious features |
| **Searchable docs** | Knowledge base | For detailed questions |
| **Guided tours** | Onboarding | First-time users |
| **Chat/Support** | Complex issues | When self-service fails |

### Common Violations

| Violation | Problem | Fix |
|-----------|---------|-----|
| No search in docs | Can't find answers | Add search |
| Long documentation | Nobody reads | Concise, task-focused |
| Generic help | Doesn't answer question | Specific to feature/page |
| Hidden help | Users can't find it | Visible help links |
| No contextual help | Users leave page | Inline tooltips |
