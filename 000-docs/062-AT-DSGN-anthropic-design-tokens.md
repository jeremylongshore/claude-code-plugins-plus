# Anthropic-Inspired Design Tokens

**Status:** Idea / Future Consideration
**Created:** 2025-10-18
**Purpose:** Custom brand identity for claudecodeplugins.io marketplace (Option 2: Create complementary identity)

---

## Research Summary

Anthropic's brand uses a warm, earthy palette that differentiates them from typical tech companies. Instead of cold blues/purples, they chose terracotta and warm neutrals to humanize AI.

### Brand Philosophy
- **Warmth + Minimalism** - Making minimalism feel inviting, not sterile
- **Human-centered AI** - Technology second, humans first
- **Sophisticated but accessible** - Clean sans serif + humanist serif pairing
- **"Do simple thing that works"** - Restraint IS the design

---

## Color Palette (Reverse-Engineered from Public Sources)

### Primary Colors
| Role | Hex | Notes |
|------|-----|-------|
| Logo/Accent | `#da7756` | Terra cotta / warm red (Claude logo color) |
| Dark Text | `#1f1f1e` | Near-black (softer than pure black) |
| Light Background | `#fbf6f2` | "Digital paper" - aged cream stock |

### Warm Neutral Progression
| Level | Hex | Usage |
|-------|-----|-------|
| Neutral 50 | `#fbf6f2` | Background base |
| Neutral 200 | `#ead1bf` | Cards, surfaces |
| Neutral 300 | `#ddb599` | Hover states |
| Neutral 400 | `#d8ac8c` | Borders, dividers |

### UI Elements
| Element | Hex | Notes |
|---------|-----|-------|
| Surface | `#fbf6f2` | Same as neutral 50 |
| Card | `#ead1bf` | Same as neutral 200 |
| Border | `#e6d9cc` | Slightly darker than neutral 200 |

### Feedback Colors (Extensions)
| State | Hex | Notes |
|-------|-----|-------|
| Info | `#6a9bcc` | Blue for informational states |
| Success | `#788c5d` | Earthy green |
| Warning | `#d97757` | Similar to accent |
| Danger | `#b24c3a` | Darker red |

---

## Typography System

### Font Families
- **Headings:** `'Neutral Grotesque', 'Inter', Arial, Helvetica, sans-serif`
- **Body:** `'Tiempos Text', 'Georgia', 'Times New Roman', serif`

**Note:** Anthropic likely uses custom fonts. These are approximations for web implementation.

### Font Sizes (rem-based scale)
```
xs:   0.75rem   (12px)
sm:   0.875rem  (14px)
md:   1rem      (16px)
lg:   1.25rem   (20px)
xl:   1.5rem    (24px)
2xl:  1.875rem  (30px)
3xl:  2.25rem   (36px)
4xl:  3rem      (48px)
```

### Font Weights
```
regular:   400
medium:    500
semibold:  600
bold:      700
```

### Line Heights
```
tight:   1.15  (headings)
snug:    1.25  (subheadings)
normal:  1.5   (body text)
```

---

## Design Token Formats

### 1. W3C Design Tokens (JSON)

```json
{
  "$schema": "https://json.schemastore.org/design-tokens.json",
  "meta": {
    "name": "Anthropic Approx Brand Tokens",
    "version": "0.1.0",
    "source": "Reverse-engineered from public materials; not official."
  },
  "color": {
    "primary": {
      "accent": {
        "value": "#da7756"
      }
    },
    "text": {
      "dark": {
        "value": "#1f1f1e"
      },
      "onAccent": {
        "value": "#ffffff"
      }
    },
    "background": {
      "light": {
        "value": "#fbf6f2"
      }
    },
    "neutral": {
      "50": {
        "value": "#fbf6f2"
      },
      "200": {
        "value": "#ead1bf"
      },
      "300": {
        "value": "#ddb599"
      },
      "400": {
        "value": "#d8ac8c"
      }
    },
    "ui": {
      "surface": {
        "value": "{color.neutral.50.value}"
      },
      "card": {
        "value": "{color.neutral.200.value}"
      },
      "border": {
        "value": "#e6d9cc"
      }
    },
    "feedback": {
      "info": {
        "value": "#6a9bcc"
      },
      "success": {
        "value": "#788c5d"
      },
      "warning": {
        "value": "#d97757"
      },
      "danger": {
        "value": "#b24c3a"
      }
    }
  },
  "font": {
    "family": {
      "heading": {
        "value": "'Neutral Grotesque', 'Inter', Arial, Helvetica, sans-serif"
      },
      "body": {
        "value": "'Tiempos Text', 'Georgia', 'Times New Roman', serif"
      }
    },
    "size": {
      "xs": {
        "value": "0.75rem"
      },
      "sm": {
        "value": "0.875rem"
      },
      "md": {
        "value": "1rem"
      },
      "lg": {
        "value": "1.25rem"
      },
      "xl": {
        "value": "1.5rem"
      },
      "2xl": {
        "value": "1.875rem"
      },
      "3xl": {
        "value": "2.25rem"
      },
      "4xl": {
        "value": "3rem"
      }
    },
    "weight": {
      "regular": {
        "value": "400"
      },
      "medium": {
        "value": "500"
      },
      "semibold": {
        "value": "600"
      },
      "bold": {
        "value": "700"
      }
    },
    "lineHeight": {
      "tight": {
        "value": "1.15"
      },
      "snug": {
        "value": "1.25"
      },
      "normal": {
        "value": "1.5"
      }
    }
  },
  "radius": {
    "sm": {
      "value": "6px"
    },
    "md": {
      "value": "12px"
    },
    "lg": {
      "value": "20px"
    }
  },
  "shadow": {
    "sm": {
      "value": "0 1px 2px rgba(0,0,0,0.06)"
    },
    "md": {
      "value": "0 6px 16px rgba(0,0,0,0.10)"
    },
    "lg": {
      "value": "0 12px 32px rgba(0,0,0,0.12)"
    }
  }
}
```

### 2. Tailwind Config

```javascript
{
  "theme": {
    "extend": {
      "colors": {
        "accent": "#da7756",
        "bg": "#fbf6f2",
        "textdark": "#1f1f1e",
        "surface": "#fbf6f2",
        "card": "#ead1bf",
        "border": "#e6d9cc"
      },
      "fontFamily": {
        "heading": [
          "Neutral Grotesque",
          "Inter",
          "Arial",
          "Helvetica",
          "sans-serif"
        ],
        "body": [
          "Tiempos Text",
          "Georgia",
          "Times New Roman",
          "serif"
        ]
      },
      "borderRadius": {
        "lg": "20px",
        "md": "12px",
        "sm": "6px"
      },
      "boxShadow": {
        "brand-sm": "0 1px 2px rgba(0,0,0,0.06)",
        "brand-md": "0 6px 16px rgba(0,0,0,0.10)",
        "brand-lg": "0 12px 32px rgba(0,0,0,0.12)"
      }
    }
  }
}
```

### 3. CSS Custom Properties

```css
:root {
  /* Colors */
  --color-accent: #da7756;
  --color-text-dark: #1f1f1e;
  --color-text-on-accent: #ffffff;
  --color-bg: #fbf6f2;
  --color-surface: #fbf6f2;
  --color-card: #ead1bf;
  --color-border: #e6d9cc;

  /* Typography */
  --font-heading: 'Neutral Grotesque', 'Inter', Arial, Helvetica, sans-serif;
  --font-body: 'Tiempos Text', 'Georgia', 'Times New Roman', serif;
  --lh-tight: 1.15;
  --lh-snug: 1.25;
  --lh-normal: 1.5;

  /* Border Radius */
  --radius-sm: 6px;
  --radius-md: 12px;
  --radius-lg: 20px;

  /* Shadows */
  --shadow-sm: 0 1px 2px rgba(0,0,0,0.06);
  --shadow-md: 0 6px 16px rgba(0,0,0,0.10);
  --shadow-lg: 0 12px 32px rgba(0,0,0,0.12);

  /* Font Sizes */
  --fs-xs: 0.75rem;
  --fs-sm: 0.875rem;
  --fs-md: 1rem;
  --fs-lg: 1.25rem;
  --fs-xl: 1.5rem;
  --fs-2xl: 1.875rem;
  --fs-3xl: 2.25rem;
  --fs-4xl: 3rem;
}

/* Base Styles */
.body-bg {
  background: var(--color-bg);
  color: var(--color-text-dark);
  font-family: var(--font-body);
  line-height: var(--lh-normal);
}

/* Typography Classes */
.h1, h1 {
  font-family: var(--font-heading);
  font-size: var(--fs-4xl);
  line-height: var(--lh-tight);
}

.h2, h2 {
  font-family: var(--font-heading);
  font-size: var(--fs-3xl);
  line-height: var(--lh-tight);
}

.h3, h3 {
  font-family: var(--font-heading);
  font-size: var(--fs-2xl);
  line-height: var(--lh-snug);
}

/* Button Component */
.btn-accent {
  background: var(--color-accent);
  color: var(--color-text-on-accent);
  border-radius: var(--radius-md);
  box-shadow: var(--shadow-sm);
}
```

---

## Analysis & Recommendations

### What Works Exceptionally Well
- ✅ **Terracotta accent (#da7756)** - Brave choice that humanizes AI
- ✅ **Warm neutrals** - Creates inviting minimalism
- ✅ **Typography pairing** - Geometric sans + humanist serif = technical + approachable
- ✅ **Design token structure** - Professional-grade semantic naming
- ✅ **Brand differentiation** - Won't confuse with OpenAI/DeepMind/Google

### Gaps to Address for Production Use
- ⚠️ **Limited color vocabulary** - Need secondary/tertiary accents for complex UIs
- ⚠️ **No dark mode tokens** - Warm palette won't invert well
- ⚠️ **Neutral scale gaps** - Missing intermediate values (100, 150, 500, 600)
- ⚠️ **Feedback colors clash** - Success green/info blue don't harmonize with terracotta
- ⚠️ **Accessibility** - Need to verify WCAG AA contrast ratios

### Potential Enhancements
1. **Fill neutral scale:** Add 100, 150, 500, 600, 700, 800, 900
2. **Add secondary accents:** 2-3 complementary colors for UI complexity
3. **Dark mode palette:** Build warm dark theme from scratch (not inverted)
4. **Harmonized feedback colors:** Replace generic blue/green with earthy alternatives
5. **Accessibility audit:** Test all color combinations for WCAG compliance

---

## Implementation Strategy for claudecodeplugins.io

### Phase 1: Foundation
1. Create `marketplace/src/styles/tokens.css` with CSS custom properties
2. Update `marketplace/src/styles/global.css` to import tokens
3. Apply base typography and color system

### Phase 2: Component Library
1. Build button variants (accent, neutral, ghost)
2. Create card components with proper shadows
3. Implement navigation with warm neutrals
4. Design plugin grid with terracotta accents

### Phase 3: Refinement
1. Add dark mode toggle with custom warm dark palette
2. Build intermediate neutral values for hover/disabled states
3. Create harmonized feedback colors
4. Accessibility audit and fixes

---

## Sources & Attribution

**Public Research:**
- Claude logo color: #da7756 (Claude101)
- Design firm: Geist (Anthropic identity work)
- Neutral palette: ColorsWall community interpretations
- Typography approach: Geist design commentary

**Disclaimer:** These tokens are reverse-engineered approximations based on publicly available Anthropic brand materials. This is NOT an official Anthropic design system. For community marketplace use only.

---

## Legal Considerations

### Trademark & Brand Guidelines
- **Do NOT** imply official Anthropic endorsement
- **Do** create complementary identity that signals "Claude ecosystem"
- **Do** differentiate with own visual identity elements
- **Consider** reaching out to Anthropic for brand guideline clarification

### Recommended Approach
- Use terracotta family as **accent only** (not primary brand color)
- Add own **secondary colors** for distinction
- Maintain **warm aesthetic** without copying exactly
- Focus on **complementary, not identical** branding

---

## Next Steps (When Ready to Implement)

1. **Decision:** Get community/team buy-in on this direction
2. **Extend:** Fill in missing neutral values and secondary colors
3. **Build:** Create dark mode variants
4. **Test:** Accessibility audit (WCAG AA minimum)
5. **Deploy:** Implement in Astro marketplace incrementally
6. **Monitor:** Track user feedback and iterate

---

**Status:** Documented for future consideration
**Last Updated:** 2025-10-18
**Prepared by:** Claude Code (Research & Analysis)
