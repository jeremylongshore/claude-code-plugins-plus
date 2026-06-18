# Krug's Usability Principles

Full methodology from "Don't Make Me Think" for creating intuitive, usable interfaces.

## The Reality of How Users Use the Web

### Fact 1: We Don't Read, We Scan

**Why users scan:**
- They're on a mission (have a goal)
- They know they don't need to read everything
- They're good at scanning from years of practice

**Design implications:**
- Create visual hierarchy (important things bigger, bolder)
- Use headings and subheadings liberally
- Keep paragraphs short
- Use bulleted lists
- Highlight key terms

### Fact 2: We Don't Make Optimal Choices, We Satisfice

**Satisficing** = "satisfying" + "sufficing"

Users click the first reasonable option, not the best option.

**Why satisficing:**
- Optimizing is hard and takes time
- The penalty for guessing wrong is low (back button)
- Weighing options doesn't improve results much
- Guessing is more fun

**Design implications:**
- Make the right choice obvious
- Don't rely on users reading all options
- Make consequences clear before clicking

### Fact 3: We Don't Figure Out How Things Work, We Muddle Through

Users don't read instructions. They try things until something works.

**Why muddling through:**
- It's not important to them to know how it works
- If they find something that works, they stick with it
- It rarely matters if they don't use something optimally

**Design implications:**
- Make things obvious so "figuring out" isn't needed
- Expect users to use things "wrong"
- Design for recovery from mistakes

---

## Things You Should Never Do

### Don't Make Users Think

Signs that your page makes users think:

| Symptom | Example |
|---------|---------|
| Puzzling labels | "Solutions" (solutions to what?) |
| Links that could go anywhere | "Click here" |
| Unexplained options | Checkboxes without context |
| Unfamiliar terminology | Industry jargon |
| Gratuitous cleverness | Puns, wordplay in navigation |

### Don't Waste Users' Goodwill

Users have a finite reservoir of goodwill:

**Things that diminish goodwill:**
- Hiding info they need (phone numbers, prices)
- Punishing them for not doing things your way
- Asking for unnecessary information
- Making them feel stupid
- Making them repeat themselves
- Sites that look like an afterthought
- Amateur errors (broken links, typos)

**Things that increase goodwill:**
- Know what questions they have and answer them
- Minimize steps
- Put effort into UI quality
- Know what they're likely to struggle with
- Make it easy to recover from errors
- Apologize when things go wrong

### Don't Make Words Seem Important If They're Not

**Happy talk example:**
> "Welcome to our website! We're excited to help you find exactly what you're looking for. Our team of dedicated professionals is committed to providing you with the best possible experience."

**Reality:** Users skip this. It says nothing.

**Rule:** If users will skip it, remove it.

---

## Navigation Must-Haves

### The Permanent Navigation

Every page needs:

1. **Site ID** (logo/name) - Top left corner
2. **Page name** - Prominent, matches link that brought them
3. **Sections** - Major site areas
4. **Local navigation** - What's in this section
5. **Utilities** - Sign in, Search, Help, Cart
6. **"You are here" indicator** - Highlighted nav item

### The Trunk Test

Can users answer these on any random page?

| Question | Element That Answers It |
|----------|------------------------|
| What site is this? | Logo/Site ID |
| What page am I on? | Page title |
| What major sections exist? | Main navigation |
| What are my options here? | Local navigation |
| Where am I in the structure? | Breadcrumbs, highlighted nav |
| How can I search? | Search box |

### Breadcrumbs

**Good breadcrumbs:**
```
Home > Products > Shoes > Running > Men's Trail Runners
```

**Rules:**
- Put them at the top
- Use ">" between levels
- Make the current page name visible but not a link
- Use small text (secondary importance)

---

## Homepage Guidelines

The homepage has to do too many things:

1. Site identity and mission
2. Site hierarchy (navigation)
3. Search
4. Teases (content, features)
5. Timely content
6. Deals
7. Shortcuts (popular items)
8. Registration/Sign in

### Homepage Priorities

**Must do:**
- Tell me what this site is
- Tell me what I can do here
- Tell me why I should be here (and not somewhere else)
- Start me on my way

**Should do:**
- Show me what I'm looking for
- Show me where to start
- Establish credibility and trust

### The Big Bang Theory of Web Design

**You have 3-4 seconds to answer:**
1. What is this?
2. What can I do here?
3. Why should I be here?

### Tagline Guidelines

| Good Tagline | Bad Tagline |
|--------------|-------------|
| Conveys unique value | Generic platitude |
| Specific and informative | Vague and fluffy |
| 6-8 words | Too long or too short |
| Instantly understandable | Requires thought |

Examples:
- Good: "Find anything from thousands of stores"
- Bad: "Welcome to the future of shopping"

---

## Mobile Usability

### Mobile Considerations

**Constraints:**
- Smaller viewport
- Fat fingers (need bigger targets)
- Single-column layout
- No hover states
- Variable attention and context

### Mobile Specifics

| Issue | Solution |
|-------|----------|
| Tiny tap targets | Minimum 44×44 px |
| Crowded nav | Hamburger or bottom nav |
| Long forms | Break into steps |
| Hover-dependent UI | Alternative for touch |
| Text too small | 16px minimum body text |

### Mobile Trade-offs

**What to prioritize:**
- Primary tasks front and center
- Essential content visible
- Fast load times
- Easy to tap, hard to mis-tap

**What to hide/remove:**
- Secondary navigation
- Non-essential images
- Decorative elements
- Long-form content

---

## Usability Testing on $0

### How Many Users?

**3-4 users catches most issues.**

Testing with more users has diminishing returns. Better to test with 3, fix issues, then test again with 3.

### What to Test

1. Can they complete core tasks?
2. Where do they get stuck?
3. What do they say out loud?
4. What did they expect vs. what happened?

### Test Protocol

**Before:**
- "I'm testing the site, not you"
- "Think out loud as you go"
- "There are no wrong answers"

**During:**
- Don't help. Don't explain. Just watch.
- Note hesitations and confusions
- Write down what they say

**After:**
- Ask what was confusing
- Ask what they expected
- Ask how they'd describe the site

### Common Findings

| What Users Do | What It Means |
|---------------|---------------|
| Click wrong thing | Label is confusing |
| Hesitate | Decision isn't obvious |
| Look around lost | "You are here" is unclear |
| Read everything | Design isn't self-evident |
| Use search immediately | Navigation is failing |
| Express confusion | Copy is unclear |

---

## Accessibility Basics

### Why It Matters

- 15-20% of population has some disability
- Accessible sites are better for everyone
- It's often required by law
- It's the right thing to do

### Quick Wins

| Fix | Benefit |
|-----|---------|
| Add alt text to images | Screen readers can describe |
| Use sufficient contrast | Low-vision users can read |
| Allow keyboard navigation | Motor-impaired users can navigate |
| Use semantic HTML | Assistive tech understands structure |
| Add focus indicators | Keyboard users know where they are |
| Make touch targets large | Everyone benefits |
