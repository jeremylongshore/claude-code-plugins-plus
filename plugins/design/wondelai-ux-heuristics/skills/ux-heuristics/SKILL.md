---
name: ux-heuristics
description: |
  Evaluate and improve interface usability using heuristic analysis. Use when the user mentions "usability audit", "UX review", "users are confused", "heuristic evaluation", "form usability", or "navigation problems". Covers Nielsen's 10 heuristics, severity ratings, and information architecture. For visual design fixes, see refactoring-ui. For conversion-focused audits, see cro-methodology. Trigger with 'ux', 'heuristics'.
allowed-tools: Read, Glob, Grep
license: MIT
author: Wondelai <hello@wondelai.com>
version: 1.0.1
compatible-with: claude-code, codex, openclaw
tags: [design, audit, ux-heuristics]
---
# UX Heuristics Framework

Practical usability principles for evaluating and improving user interfaces. Based on a fundamental truth: users don't read, they scan.

## Core Principle

**"Don't Make Me Think"** - Every page should be self-evident. If something requires thinking, it's a usability problem.

**The foundation:** Users have limited patience and cognitive bandwidth. The best interfaces are invisible -- they let users accomplish goals without ever stopping to wonder "What do I click?" or "Where am I?" Every question mark that pops into a user's head adds to cognitive load and increases the chance they'll leave. Design for scanning, satisficing, and muddling through -- because that's what users actually do.

## Scoring

**Goal: 10/10.** When reviewing or creating user interfaces, rate them 0-10 based on adherence to the principles below. A 10/10 means full alignment with all guidelines; lower scores indicate gaps to address. Always provide the current score and specific improvements needed to reach 10/10.

## Krug's Three Laws of Usability

### 1. Don't Make Me Think

**Core concept:** Every question mark that pops into a user's head adds to their cognitive load and distracts from the task.

**Why it works:** Users are on a mission. They don't want to puzzle over labels, wonder what a link does, or decode clever marketing language. The less thinking required, the more likely they complete the task.

**Key insights:**
- Clever names lose to clear names every time
- Marketing-speak creates friction; plain language removes it
- Unfamiliar categories and labels force users to stop and interpret
- Links that could go anywhere create uncertainty
- Buttons with ambiguous labels cause hesitation

**Product applications:**

| Context | Application | Example |
|---------|-------------|---------|
| **Navigation labels** | Use self-evident names | "Get directions" not "Calculate route to destination" |
| **CTAs** | Use action verbs users understand | "Sign in" not "Access your account portal" |
| **E-commerce** | Match user mental models | "Add to cart" not "Proceed to purchase selection" |
| **Form labels** | Describe what's needed plainly | "Email address" not "Electronic correspondence identifier" |
| **Error states** | Tell users what to do next | "Check your email format" not "Validation error" |

**Copy patterns:**
- Self-evident labels: "Sign in", "Search", "Add to cart"
- Action-oriented buttons: verb + noun ("Create account", "Download report")
- Avoid jargon: "Save" not "Persist", "Remove" not "Disassociate"
- If a label needs explanation, simplify the label

**Ethical boundary:** Clarity should serve users, not obscure information. Never use plain language as a veneer to hide unfavorable terms.

See: [references/krug-principles.md](references/krug-principles.md) for full Krug methodology.

### 2. It Doesn't Matter How Many Clicks

**Core concept:** The myth says "users leave after 3 clicks." The reality is users don't mind clicks if each one is painless, obvious, and confidence-building.

**Why it works:** Cognitive effort per click matters more than click count. Three mindless, confident clicks are far better than one click that requires deliberation. Users abandon when they lose confidence, not when they run out of patience for clicking.

**Key insights:**
- Each click should be painless (fast, easy)
- Each click should be obvious (no thinking required)
- Each click should build confidence (users know they're on the right path)
- Three mindless clicks beat one confusing click every time
- Users abandon when confused, not when they've clicked too many times

**Product applications:**

| Context | Application | Example |
|---------|-------------|---------|
| **Information architecture** | Prioritize clarity over depth | Shallow nav with clear labels over deep nav with vague ones |
| **Checkout flows** | Make each step obvious | Clear step indicators with descriptive labels |
| **Settings** | Organize into clear categories | "Account > Security > Change password" (3 confident clicks) |
| **Search results** | Let users drill down confidently | Category filters that narrow results progressively |
| **Onboarding** | Guide with small, clear steps | Wizard with one clear action per step |

**Copy patterns:**
- Progress indicators: "Step 2 of 4: Shipping details"
- Breadcrumbs: "Home > Products > Shoes > Running"
- Confirmations at each step: "Great, your email is verified. Now let's set up your profile."
- Clear link text: "View all running shoes" not "Click here"

**Ethical boundary:** Don't use extra steps to bury cancellation flows or make opting out harder. Every click should move users toward their goal, not away from it.

See: [references/krug-principles.md](references/krug-principles.md) for Krug's click philosophy and scanning behavior.

### 3. Get Rid of Half the Words

**Core concept:** Get rid of half the words on each page, then get rid of half of what's left. Brevity reduces noise, makes useful content more prominent, and shows respect for the user's time.

**Why it works:** Users scan -- they don't read. Every unnecessary word competes with the words that matter. Removing fluff makes important content more discoverable and pages shorter.

**Key insights:**
- Happy-talk ("Welcome to our website!") wastes space
- Instructions nobody reads should be removed
- "Please" and "Kindly" and polite fluff add noise
- Redundant explanations dilute the message
- Shorter pages mean less scrolling and faster scanning

**Product applications:**

| Context | Application | Example |
|---------|-------------|---------|
| **Landing pages** | Cut welcome copy, lead with value | Remove "Welcome to..." paragraphs |
| **Error messages** | State problem and fix, nothing more | "Password too short (min 8 chars)" not a paragraph |
| **Tooltips** | One sentence max | "Last 4 digits of your card" not a full explanation |
| **Empty states** | Action-oriented, minimal | "No results. Try a different search." |
| **Onboarding** | One instruction per screen | "Choose your interests" not a wall of explanatory text |

**Copy patterns:**
- Before: "Please kindly note that a password is required in order to proceed to the next step."
- After: "Enter your password to continue."
- Before: "We've received your message and will get back to you as soon as possible."
- After: "Message sent. We'll reply within 24 hours."

**Ethical boundary:** Brevity must not mean omitting critical information. Concise disclosures for pricing, terms, and data usage are a user right.

See: [references/krug-principles.md](references/krug-principles.md) for Krug's word-cutting methodology.

### 4. The Trunk Test

**Core concept:** A test for navigation clarity: if users were dropped on any random page (like being locked in a car trunk and released at a random spot), could they instantly answer six key questions?

**Why it works:** Good navigation gives users constant orientation. If users can't identify where they are and what their options are, they feel lost and leave.

**Key insights:**
- Users must know what site they're on (brand/logo visible)
- Users must know what page they're on (clear heading)
- Major sections must be visible (navigation)
- Options at this level must be clear (links/buttons)
- Position in hierarchy must be apparent (breadcrumbs)
- Search must be findable

**Product applications:**

| Context | Application | Example |
|---------|-------------|---------|
| **Global nav** | Persistent site ID and sections | Logo top-left, main nav always visible |
| **Page headers** | Clear, descriptive page titles | "Running Shoes - Men's" not just "Products" |
| **Breadcrumbs** | Show hierarchy on all inner pages | "Home > Products > Shoes > Running" |
| **Mobile nav** | Maintain orientation in hamburger menus | Highlight current section, show breadcrumbs |
| **Search** | Visible search on every page | Search box in header, not buried in footer |

**Copy patterns:**
- Page titles that match the link the user clicked
- "You are here" indicators (highlighted nav items, bold breadcrumb)
- Section headings that orient: "Your Account > Billing" not just "Settings"
- Footer navigation for secondary discovery

**Ethical boundary:** Navigation should honestly represent site structure. Don't use misleading labels to funnel users into marketing pages.

See: [references/krug-principles.md](references/krug-principles.md) for the full Trunk Test methodology.

## Nielsen's 10 Usability Heuristics

### 1. Visibility of System Status
Keep users informed about what's happening through timely feedback. Every action needs acknowledgment — progress bars for uploads, confirmations for submissions, skeleton screens for loading. Silent failures destroy trust. Copy pattern: "Saving..." → "Saved" (immediate state transitions).

### 2. Match Between System and Real World
Speak users' language, not system language. Use "Sign in" not "Authenticate", "Search" not "Query." Follow real-world metaphors (trash bin, shopping cart) and natural ordering (street → city → state → zip). One term per concept, everywhere.

### 3. User Control and Freedom
Provide clear "emergency exits." Undo beats "Are you sure?" dialogs every time — users click through confirmations without reading. Every flow needs cancel/exit, back buttons must never break, and soft delete with undo beats permanent deletion.

### 4. Consistency and Standards
Same words, styles, and behaviors should mean the same thing throughout. Internal consistency (your app) and external consistency (platform conventions: logo top-left, search top-right). Pick one term per concept — "Projects" everywhere, never mixing with "Workspaces."

### 5. Error Prevention
Prevent problems before they occur. Constrained inputs (date pickers over text fields), autocomplete, sensible defaults, and "unsaved changes" warnings. Two error types need different prevention: slips (accidental wrong action) and mistakes (wrong intention).

### 6. Recognition Rather Than Recall
Minimize memory load — show options, don't require memorization. Breadcrumbs, recent searches, pre-filled fields, dropdowns with decoded values (country names, not codes). Human working memory holds ~7 items; recognition is far easier than recall.

### 7. Flexibility and Efficiency of Use
Serve both novices and experts. Keyboard shortcuts, touch gestures, bulk actions, saved searches, and command palettes (Cmd+K) speed up power users. Progressive disclosure keeps it simple for beginners while experts access full power.

### 8. Aesthetic and Minimalist Design
Every element must earn its place. Signal-to-noise ratio determines usability — when everything screams for attention, nothing stands out. Show what matters now, hide what doesn't. One primary CTA per page, not five competing ones.

### 9. Help Users Recognize, Diagnose, and Recover from Errors
Error messages need three parts: what happened, why, and how to fix it. Plain language always ("Connection failed" not "ECONNREFUSED"), specific ("Password must be 8+ characters" not "Invalid"), never blame the user, and preserve their input.

### 10. Help and Documentation
Help should be searchable, task-focused ("How to..." not technical reference), and contextual (tooltips, inline hints). Types: inline help, contextual "?" icons, searchable knowledge base, guided tours, live support.

See: [references/nielsen-heuristics.md](references/nielsen-heuristics.md) for detailed examples, product applications, copy patterns, and ethical boundaries for all 10 heuristics.

## Severity Rating Scale

When auditing interfaces, rate each issue:

| Severity | Rating | Description | Priority |
|----------|--------|-------------|----------|
| **0** | Not a problem | Disagreement, not usability issue | Ignore |
| **1** | Cosmetic | Minor annoyance, low impact | Fix if time |
| **2** | Minor | Causes delay or frustration | Schedule fix |
| **3** | Major | Significant task failure | Fix soon |
| **4** | Catastrophic | Prevents task completion | Fix immediately |

### Rating Factors

Consider all three:

1. **Frequency:** How often does it occur?
2. **Impact:** How severe when it occurs?
3. **Persistence:** One-time or ongoing problem?

## Common Mistakes

| Mistake | Why It Fails | Fix |
|---------|-------------|------|
| **Mystery meat navigation** | Icons without labels force guessing | Add text labels alongside icons |
| **Too many choices** | Decision paralysis slows users | Reduce to 7 plus/minus 2 items |
| **No "you are here" indicator** | Users feel lost in the hierarchy | Highlight current section in nav and breadcrumbs |
| **No inline validation** | Submit, error, scroll cycle frustrates | Validate on blur with specific messages |
| **Unclear required fields** | Users confused about what's mandatory | Mark optional fields, not required (most fields should be required) |
| **Wall of text** | Nobody reads dense paragraphs | Break up with headings, bullets, whitespace |
| **Jargon in labels** | Users don't speak your internal language | User-test all labels, use plain language |
| **No loading indicators** | Users think the system is broken | Show spinner, progress bar, or skeleton screen |
| **Tiny tap targets** | Mobile users misclick constantly | Minimum 44x44 px touch targets |
| **Hover-only information** | Mobile and keyboard users miss it entirely | Don't hide critical info behind hover states |
| **No undo** | Users afraid to take any action | Provide undo for all non-destructive actions |
| **Poor error messages** | "Invalid input" tells users nothing | Explain what's wrong and how to fix it |
| **Low contrast text** | Unreadable for many users | WCAG AA minimum (4.5:1 contrast ratio) |
| **Inconsistent nav location** | Users can't find navigation | Fixed position, same location on every page |
| **Broken back button** | Fundamental browser contract violated | Never hijack or break browser history |

## Quick Diagnostic

Audit any interface:

| Question | If No | Action |
|----------|-------|--------|
| Can I tell what site/page this is immediately? | Users are lost and disoriented | Add clear logo, page title, and breadcrumbs |
| Is the main action obvious? | Users don't know what to do | Create visual hierarchy, single primary CTA |
| Is the navigation clear? | Users can't find their way | Apply the Trunk Test, add "you are here" indicators |
| Can I find the search? | Users with specific goals are blocked | Add visible search box in header |
| Does the system show me what's happening? | Users lose trust and re-click | Add loading states, confirmations, progress indicators |
| Are error messages helpful? | Users get stuck on errors | Rewrite in plain language with specific fix |
| Can users undo or go back? | Users are afraid to act | Add undo, cancel, and back options everywhere |
| Does it work without hover? | Mobile and keyboard users are excluded | Replace hover-only interactions with visible alternatives |
| Are all interactive elements labeled? | Users guess at icon meanings | Add text labels or descriptive tooltips |
| Does anything make me stop and think "huh?" | Cognitive load is too high | Simplify -- if it needs explanation, redesign it |

## Heuristic Conflicts

Heuristics sometimes contradict each other. When they do:
- **Simplicity vs. Flexibility**: Use progressive disclosure
- **Consistency vs. Context**: Consistent patterns, contextual prominence
- **Efficiency vs. Error Prevention**: Prefer undo over confirmation dialogs
- **Discoverability vs. Minimalism**: Primary actions visible, secondary hidden

See: [references/heuristic-conflicts.md](references/heuristic-conflicts.md) for resolution frameworks.

## Dark Patterns Recognition

Dark patterns violate heuristics deliberately to manipulate users:
- Forced continuity (hard to cancel)
- Roach motel (easy in, hard out)
- Confirmshaming (guilt-based options)
- Hidden costs (surprise fees at checkout)

See: [references/dark-patterns.md](references/dark-patterns.md) for complete taxonomy and ethical alternatives.

## When to Use Each Method

| Method | When | Time | Findings |
|--------|------|------|----------|
| Heuristic evaluation | Before user testing | 1-2 hours | Major violations |
| User testing | After heuristic fixes | 2-4 hours | Real behavior |
| A/B testing | When optimizing | Days-weeks | Statistical validation |
| Analytics review | Ongoing | 30 min | Patterns and problems |

## Reference Files

- [krug-principles.md](references/krug-principles.md): Full Krug methodology, scanning behavior, navigation clarity
- [nielsen-heuristics.md](references/nielsen-heuristics.md): Detailed heuristic explanations with examples
- [audit-template.md](references/audit-template.md): Structured heuristic evaluation template
- [dark-patterns.md](references/dark-patterns.md): Categories, examples, ethical alternatives, regulations
- [wcag-checklist.md](references/wcag-checklist.md): Complete WCAG 2.1 AA checklist, testing tools
- [cultural-ux.md](references/cultural-ux.md): RTL, color meanings, form conventions, localization
- [heuristic-conflicts.md](references/heuristic-conflicts.md): When heuristics contradict, resolution frameworks

## Further Reading

This skill is based on usability principles developed by Steve Krug and Jakob Nielsen:

- [*"Don't Make Me Think, Revisited"*](https://www.amazon.com/Dont-Make-Think-Revisited-Usability/dp/0321965515?tag=wondelai00-20) by Steve Krug
- [*"Rocket Surgery Made Easy"*](https://www.amazon.com/Rocket-Surgery-Made-Easy-Yourself/dp/0321657292?tag=wondelai00-20) by Steve Krug (DIY usability testing)
- [*"10 Usability Heuristics for User Interface Design"*](https://www.nngroup.com/articles/ten-usability-heuristics/) by Jakob Nielsen (Nielsen Norman Group)

## About the Author

**Steve Krug** is a usability consultant who has been helping companies make their products more intuitive since the 1990s. His book *"Don't Make Me Think"* (first published in 2000, revised 2014) is the most widely read book on web usability and is considered essential reading for anyone involved in designing interfaces. Known for his accessible, humorous writing style and his advocacy for low-cost usability testing, Krug demonstrated that usability doesn't require a lab or a large budget -- just watching a few real users try to accomplish tasks.

**Jakob Nielsen, PhD** is co-founder of the Nielsen Norman Group (NN/g) and is widely regarded as the "king of usability." His 10 Usability Heuristics for User Interface Design, published in 1994, remain the most-used framework for heuristic evaluation worldwide. Nielsen has been called "the guru of Web page usability" by *The New York Times* and has authored numerous influential books on usability engineering. His research-driven approach to interface design helped establish usability as a recognized discipline in software development.

## Overview

Evaluate and improve interface usability using heuristic analysis.

## Prerequisites

- Access to the ORM environment or API
- Required CLI tools installed and authenticated
- Familiarity with ORM concepts and terminology

## Instructions

1. Assess the current state of the ORM configuration
2. Identify the specific requirements and constraints
3. Apply the recommended patterns from this skill
4. Validate the changes against expected behavior
5. Document the configuration for team reference

## Output

- Configuration files or code changes applied to the project
- Validation report confirming correct implementation
- Summary of changes made and their rationale

See [ORM implementation details](${CLAUDE_SKILL_DIR}/references/implementation.md) for output format specifications.

## Error Handling

| Error | Cause | Resolution |
|-------|-------|------------|
| Authentication failure | Invalid or expired credentials | Refresh tokens or re-authenticate with ORM |
| Configuration conflict | Incompatible settings detected | Review and resolve conflicting parameters |
| Resource not found | Referenced resource missing | Verify resource exists and permissions are correct |

## Examples

**Basic usage**: Apply ux heuristics to a standard project setup with default configuration options.

**Advanced scenario**: Customize ux heuristics for production environments with multiple constraints and team-specific requirements.

## Resources

- Official ORM documentation
- Community best practices and patterns
- Related skills in this plugin pack
