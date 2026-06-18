# Mappings: Connecting Controls to Outcomes

A mapping is the relationship between a control and its effect. When the mapping is natural, the connection between the two is obvious and immediate. When the mapping is arbitrary, users must memorize or guess which control does what. Natural mappings exploit spatial analogies, cultural conventions, and logical relationships to make products intuitive without instruction.

## Natural Mapping Principles

Natural mapping means the layout of the controls corresponds to the layout of the things being controlled. The best mappings require zero explanation.

### The Spectrum of Mapping Quality

| Quality | Characteristics | Learning Effort | Example |
|---------|----------------|-----------------|---------|
| **Natural / Direct** | Control IS the thing | None | Touchscreen: tap directly on the element to manipulate it |
| **Spatial analog** | Control layout mirrors output layout | Minimal | Car seat adjustment shaped like a miniature seat |
| **Cultural convention** | Learned but universally known | Low (one-time) | Red = stop, green = go |
| **Labeled arbitrary** | No inherent connection, but labeled | Moderate | Labeled switches on a panel |
| **Unlabeled arbitrary** | No inherent connection, no label | High (memorization) | Unmarked row of identical switches |

---

## Spatial Mapping: Controls Match Layout of Output

Spatial mapping is the most powerful type. When controls are arranged in the same physical pattern as the things they control, users do not need to think.

### Principles

1. **Layout correspondence**: If the controlled objects are arranged in a 2x2 grid, arrange the controls in a 2x2 grid.
2. **Direction correspondence**: Moving a control up should make something go up. Moving it right should make something go right.
3. **Proximity**: Each control should be physically close to the thing it affects.

### Real-World Examples

| Product | Spatial Mapping | Why It Works |
|---------|----------------|-------------|
| Car seat adjuster (Mercedes style) | A miniature seat shape that you tilt, slide, or raise | The control IS a spatial model of the seat |
| Elevator buttons arranged vertically | Higher button = higher floor | Spatial direction matches physical direction |
| Car side mirrors with a joystick | Push joystick left = mirror angles left | Direction of control matches direction of result |
| Crosswalk button facing the street it controls | Button faces the direction of the crosswalk | Proximity and orientation match |

### Digital Spatial Mapping

| Pattern | Spatial Relationship | Example |
|---------|---------------------|---------|
| Inline editing | Click on the content itself to edit it | Click a table cell to edit the value directly |
| WYSIWYG editors | What you see on screen matches the output | Document editors where formatting is visible |
| Drag-to-reorder | Move items to their new position directly | Drag a list item from position 3 to position 1 |
| Map controls | Pan the map by dragging the map itself | Google Maps, Figma canvas |
| Layout builders | Drag components to their spatial position | Website builders, dashboard editors |

---

## Proximity Mapping: Controls Near What They Affect

When a control is placed next to the thing it affects, the relationship is self-evident.

### Principles

1. **Adjacent placement**: The edit button should be next to the content it edits.
2. **Grouping**: Related controls should be grouped visually.
3. **Context menus**: Show actions in the context of the object they affect.

### Digital Proximity Patterns

| Pattern | Implementation | Benefit |
|---------|---------------|---------|
| Inline action buttons | Edit, delete, and copy icons appear on hover within each row | No ambiguity about which item the action affects |
| Contextual toolbars | Text formatting toolbar appears directly above selected text | Toolbar is clearly associated with the selection |
| Section-level controls | An "Add item" button at the bottom of the section it adds to | Users see where the new item will appear |
| Form-field validation | Error message appears directly below the field with the error | No confusion about which field is problematic |
| Tooltip/popover on element | Information appears next to the element that triggered it | Spatial proximity creates clear association |

### Proximity Failures

| Failure | Problem | Fix |
|---------|---------|-----|
| Global action bar far from content | Users cannot tell which content the actions apply to | Move actions inline or use clear selection indicators |
| Settings in a separate page | Users cannot see the effect of their changes | Show a live preview next to the settings |
| Error summary at the top of a form | Users must scroll to find the problematic field | Show errors inline at each field AND in a summary |

---

## Cultural Mapping: Conventions and Expectations

Cultural mappings are not inherently spatial or logical. They are learned conventions that most users in a culture share.

### Common Cultural Conventions

| Convention | Meaning | Scope |
|-----------|---------|-------|
| Red = danger / stop / error | Negative, cautionary | Near-universal |
| Green = safe / go / success | Positive, permissive | Near-universal |
| Left-to-right reading order | Sequence flows left to right | Western, many Asian |
| Right-to-left reading order | Sequence flows right to left | Arabic, Hebrew |
| Top-to-bottom = primary-to-secondary | Importance decreases downward | Most web conventions |
| X icon in top-right = close | Dismiss this window or dialog | Desktop and web |
| Floppy disk icon = save | Store the current state | Legacy but persistent |
| Shopping cart icon = purchase collection | Items selected for purchase | E-commerce |

### When Cultural Conventions Conflict

| Scenario | Conflict | Resolution |
|----------|----------|-----------|
| RTL vs LTR navigation arrows | "Forward" arrow points opposite directions | Flip arrow direction based on locale |
| Color meanings across cultures | Red means danger (West) vs. luck (East Asia) | Use icons and text alongside color |
| Date format | MM/DD/YYYY (US) vs DD/MM/YYYY (most of the world) | Use unambiguous format: "10 Feb 2024" or a date picker |
| Scroll direction | Natural scroll (Mac) vs. traditional scroll | Let users configure, but pick a default and commit |

---

## Sequential Mapping: Order Matches Natural Flow

Sequential mapping means the order of controls or steps matches the natural order of the task.

### Principles

1. **Temporal order**: Steps should be presented in the order they are performed.
2. **Reading order**: In LTR cultures, sequences should flow left-to-right or top-to-bottom.
3. **Dependency order**: Steps that depend on prior input should appear after that input.

### Digital Sequential Mapping Patterns

| Pattern | Implementation | Example |
|---------|---------------|---------|
| Multi-step wizard | Steps progress left-to-right in a stepper | Checkout: Shipping > Payment > Review > Confirm |
| Form field order | Fields ordered by task logic | Name > Email > Password > Confirm Password |
| Timeline / activity feed | Most recent at top, oldest at bottom (or reverse) | Consistent chronological direction |
| Breadcrumbs | Left-most is the root, right-most is the current page | Home > Category > Subcategory > Product |

### Sequential Mapping Failures

| Failure | Problem | Fix |
|---------|---------|-----|
| Address form: City before Street | Violates natural writing order | Reorder to match how people write addresses |
| Payment details before cart review | Users commit before seeing what they are paying for | Show cart summary before payment step |
| "Cancel" button before "Submit" | Reading order suggests cancel is the primary action | Place primary action (Submit) at the end of the reading flow |

---

## Mapping Evaluation Framework

Use this framework to evaluate the mapping quality of any control-to-outcome relationship.

### Mapping Quality Scorecard

| Criterion | Score (1-5) | Notes |
|-----------|:-----------:|-------|
| **Spatial correspondence**: Does the control layout mirror the output layout? | | |
| **Proximity**: Is the control near the thing it affects? | | |
| **Direction**: Does the direction of control movement match the direction of effect? | | |
| **Convention**: Does the mapping follow established cultural conventions? | | |
| **Sequence**: Do steps follow the natural task order? | | |
| **Labeling**: When mapping is not natural, are labels clear and complete? | | |
| **Consistency**: Are similar mappings used consistently throughout the product? | | |
| **Total (average)** | | |

### Interpretation

| Average Score | Quality | Action |
|:------------:|---------|--------|
| 4.5 - 5.0 | Excellent natural mapping | Maintain; minor refinements only |
| 3.5 - 4.4 | Good but learnable | Improve labels and proximity |
| 2.5 - 3.4 | Moderate; requires some learning | Redesign layout to improve spatial and sequential mapping |
| 1.0 - 2.4 | Poor; arbitrary mapping | Fundamental redesign required |

---

## Classic Mapping Failures

### The Stovetop Knob Problem

**Setup**: Four burners arranged in a 2x2 grid. Four knobs arranged in a 1x4 row.

**Problem**: Users cannot tell which knob controls which burner without reading labels, because the linear arrangement of knobs does not match the grid arrangement of burners.

**Fix**: Arrange knobs in a 2x2 grid matching the burner layout, or place each knob directly adjacent to its burner.

### The Light Switch Panel

**Setup**: A row of 6 identical switches controlling lights in different parts of a room.

**Problem**: No spatial correspondence between switch position and light position. Users flip switches randomly.

**Fix**: Arrange switches on a floor plan diagram, or label each switch with the zone it controls, or use smart lighting with per-fixture controls.

### The Elevator Button Panel

**Setup**: Two columns of buttons for floors 1-20.

**Problem**: Is floor 3 in the left column or the right column? Does the left column go up or does the right column? Convention varies between buildings.

**Fix**: A single vertical column where higher buttons correspond to higher floors. Simple, unambiguous spatial mapping.

### The Hotel Shower

**Setup**: A single unmarked knob that controls both temperature and flow.

**Problem**: Users cannot predict whether turning the knob will make the water hotter, colder, or change the pressure. The mapping of rotation direction to outcome is not signified.

**Fix**: Separate temperature and flow controls. Mark hot and cold directions with color (red/blue) and use a consistent rotation convention.

---

## Digital Mapping Patterns

### Settings Panels

| Pattern | Mapping Quality | Why |
|---------|:--------------:|-----|
| Settings grouped by feature, with live preview | High | Proximity to affected feature, immediate feedback |
| Alphabetical settings list | Low | No correspondence between position and function |
| Settings organized by user task | Medium-High | Sequential mapping aligned with task flow |
| Tabbed settings with icons | Medium | Grouping helps, but icon-only tabs can be ambiguous |

### Form Layouts

| Pattern | Mapping Quality | Why |
|---------|:--------------:|-----|
| Single column, top-to-bottom | High | Matches reading order and task sequence |
| Two-column with related fields side by side | Medium-High | Spatial grouping of related fields (First Name / Last Name) |
| Multi-column with unrelated fields | Low | Reading path is ambiguous (left-to-right then down? Or top-to-bottom then right?) |
| Accordion sections | Medium | Groups are clear, but hidden sections break spatial awareness |

### Navigation

| Pattern | Mapping Quality | Why |
|---------|:--------------:|-----|
| Tab bar with current tab highlighted | High | Position indicates section, highlight indicates current state |
| Sidebar matching page structure | High | Spatial hierarchy mirrors content hierarchy |
| Hamburger menu hiding all navigation | Low | No persistent spatial reference; user must open menu to see options |
| Breadcrumbs with clickable segments | High | Sequential mapping showing path from root to current page |

---

## Mapping Improvement Exercises

### Exercise 1: Map the Controls

Choose a screen in your product. Draw two sketches:
1. The layout of the controls (buttons, inputs, toggles).
2. The layout of the things they affect (content areas, settings, outputs).

Draw lines connecting each control to its effect. Ask:
- Do the lines cross? (If yes, the spatial mapping is poor.)
- Are the lines short? (Short lines = good proximity.)
- Does the spatial arrangement match? (Mirror layout = good spatial mapping.)

### Exercise 2: The Label Removal Test

Remove all labels from your interface mockup. Can a user still tell which control affects which element based on spatial position and proximity alone? Where the answer is no, the mapping depends on labels and could be improved with spatial redesign.

### Exercise 3: Sequential Task Walkthrough

List every step of a user task in chronological order. Now list the controls the user must interact with in the order they encounter them on screen. Do these two lists match? Where they diverge, the sequential mapping is broken.

### Exercise 4: Convention Audit

For each control-to-outcome mapping in your product, classify it as:
- **Spatial** (layout matches output)
- **Cultural** (follows a known convention)
- **Labeled** (arbitrary but clearly labeled)
- **Unlabeled arbitrary** (needs memorization)

Any "unlabeled arbitrary" mapping is a design failure. Convert it to spatial, cultural, or at minimum labeled.
