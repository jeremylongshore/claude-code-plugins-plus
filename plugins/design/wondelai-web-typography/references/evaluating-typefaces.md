# Evaluating Typefaces

A systematic approach to assessing whether a typeface will work for your project.

## Quality Indicators

### Visual Consistency

A well-designed typeface has consistent visual rhythm:

| Check | What to Look For |
|-------|------------------|
| **Stroke weight** | Consistent thickness throughout the alphabet |
| **Color** | Even darkness when viewing a text block |
| **Proportion** | Characters relate harmoniously to each other |
| **Curves** | Smooth, intentional curves without awkward joints |

**Quick test:** Set a paragraph and squint. Good typefaces appear as an even gray; poor ones show dark spots or inconsistent density.

### Technical Quality

| Criterion | Signs of Quality | Signs of Problems |
|-----------|------------------|-------------------|
| **Kerning** | Even spacing across character pairs | Awkward gaps (AV, To, Ty, ff) |
| **Hinting** | Crisp rendering at small sizes | Blurry or uneven at 14-16px |
| **Spacing** | Consistent rhythm without adjustment | Needs manual letter-spacing fixes |
| **Rendering** | Clean on multiple browsers/OS | Looks different across platforms |

### Character Set Completeness

**Minimum requirements:**
- Full ASCII (A-Z, a-z, 0-9, basic punctuation)
- Common accented characters (é, ñ, ü, etc.)
- Proper typographic quotes ("" '' vs "" '')
- Em dash (—), en dash (–), minus (−)
- Euro (€), pound (£), other needed currency

**Better:**
- Full Latin Extended character set
- Smart quotes and proper apostrophes
- Multiple figure styles (oldstyle, lining, tabular)
- True small caps
- Ligatures (fi, fl, ff, ffi)

**Check character support:** [caniuse.com's font feature tests](https://wakamaifondue.com/) for OpenType features.

## Structural Analysis

### X-Height Assessment

Higher x-height improves screen readability at small sizes.

```
Typeface A:   The quick brown fox    (large x-height)
Typeface B:   The quick brown fox    (small x-height)

At same point size, A appears larger and more readable.
```

**When to prefer larger x-height:**
- Body text on screens
- Small sizes (14-16px)
- UI text
- Mobile interfaces

**When smaller x-height works:**
- Large display text
- Headlines
- Print (higher resolution)
- When elegance matters more than readability

### Counter and Aperture Openness

Open counters and apertures improve legibility, especially on screens:

```
Open:    a e c s g    (clear, distinct)
Closed:  a e c s g    (can fill in at small sizes)
```

Check these characters specifically:
- **a** - How open is the counter?
- **e** - How large is the aperture?
- **c** - Wide or closed opening?
- **s** - Open curves or tight?

### Stroke Contrast

| Contrast | Screen Performance | Personality |
|----------|-------------------|-------------|
| Low/None | Excellent - consistent at all sizes | Modern, neutral, sturdy |
| Medium | Good - works for most body text | Classic, refined |
| High | Poor at small sizes - thin strokes disappear | Elegant, delicate, display-only |

**Rule:** High-contrast typefaces (Bodoni, Didot) are headlines-only on screens.

### Distinguishable Characters

Critical for legibility. Test these easily-confused sets:

| Set | What to Check |
|-----|---------------|
| **Il1\|** | Can you distinguish capital I, lowercase l, numeral 1, pipe? |
| **O0** | Is capital O distinct from zero? |
| **rn vs m** | Do "rn" together look like "m"? |
| **cl vs d** | At small sizes, could these be confused? |
| **5S** | Distinct enough in both cases? |
| **6b, 9q** | Clear differentiation? |

Some typefaces add distinguishing features:
- Serifs on capital I
- Slashed or dotted zero
- Curved tail on lowercase l
- Open counter on 4

## Testing Protocol

### 1. Test at Actual Sizes

Don't evaluate at 36px if you'll use it at 16px. Common sizes to test:

| Use Case | Test Sizes |
|----------|------------|
| Body text | 14px, 16px, 18px |
| Secondary text | 12px, 13px |
| Headlines | 24px, 32px, 48px |
| UI text | 13px, 14px, 15px |

### 2. Test with Real Content

Lorem ipsum hides problems. Use:
- Actual content from your project
- Text with numbers (to check figure styles)
- Text with punctuation (em dashes, quotes)
- Text with special characters your audience needs

### 3. Test in Context

- On actual target devices (phone, tablet, desktop)
- In actual browsers (Chrome, Safari, Firefox)
- On different operating systems (Windows renders differently than Mac)
- With your actual background colors

### 4. Test at Scale

If possible, set several paragraphs. Single sentences don't reveal:
- Text color (overall density)
- How the typeface "feels" to read
- Any rhythm issues
- Line-to-line consistency

## Practical Evaluation Checklist

### Body Text Candidates

- [ ] Readable at 16px without strain
- [ ] Even color in text blocks (squint test)
- [ ] Distinguishable Il1 and O0
- [ ] Open counters (check lowercase a, e, c)
- [ ] Complete character set for your languages
- [ ] Regular + Bold + Italics available
- [ ] Good hinting (crisp on Windows)
- [ ] Reasonable file size (< 50KB per weight)
- [ ] Clear at 200% browser zoom
- [ ] Renders consistently across browsers

### Headline Candidates

- [ ] Strong personality at large sizes
- [ ] Maintains character down to ~24px
- [ ] Works with your body typeface
- [ ] At least 2-3 weights available
- [ ] File size acceptable for what's loaded
- [ ] Distinct from body text (provides contrast)

### UI Text Candidates

- [ ] Crystal clear at 13-14px
- [ ] Compact but readable
- [ ] Multiple weights for hierarchy
- [ ] Numbers align well (tabular figures available)
- [ ] Good uppercase (for buttons, labels)
- [ ] Works with icons at same size

## Free vs. Paid Considerations

### Free Fonts (Google Fonts, Font Squirrel, etc.)

**Advantages:**
- No cost
- Easy implementation
- Often good quality (Google Fonts are curated)

**Considerations:**
- May be overused (Roboto, Open Sans everywhere)
- Sometimes incomplete character sets
- Variable quality in hinting/kerning
- May lack advanced OpenType features

**Quality free options:**
- Inter (UI, body)
- Source Sans/Serif Pro (body, editorial)
- IBM Plex family (tech, corporate)
- Literata (reading)
- Atkinson Hyperlegible (accessibility)

### Paid Fonts

**Advantages:**
- Often superior craftsmanship
- More distinctive options
- Better support and updates
- Complete feature sets
- Professional licensing terms

**Considerations:**
- Cost (though often reasonable per-project)
- Licensing complexity for web use
- Need to self-host or use a service

**When to pay:**
- Brand differentiation matters
- Long-form reading is primary use
- You need specific OpenType features
- Project budget allows

## Web Font Performance

File size directly impacts load time. Budget guidelines:

| Quality | Total Font Budget |
|---------|-------------------|
| Fast | < 100KB |
| Acceptable | 100-200KB |
| Heavy | > 200KB (needs justification) |

### Optimization Strategies

1. **Subset:** Include only characters you need
2. **Choose wisely:** 2 weights instead of 5
3. **WOFF2 format:** Smallest file size
4. **Variable fonts:** One file, many weights

### Format Priority

```css
@font-face {
  font-family: 'Custom';
  src: url('font.woff2') format('woff2'),  /* Modern browsers */
       url('font.woff') format('woff');     /* Older browsers */
}
```

WOFF2 has best compression and near-universal support. Skip TTF/OTF for web.

## Red Flags

Avoid typefaces with these issues:

| Red Flag | Why It Matters |
|----------|----------------|
| No hinting | Will render poorly on Windows |
| Very thin weights | Disappear at small sizes |
| Incomplete kerning | Requires manual spacing fixes |
| Missing basic characters | Will show boxes or fallback |
| Poor screen rendering | May look fine in samples, not in use |
| Unusual licensing | Can cause legal issues |
| "Inspired by" knock-offs | Lower quality, potential legal issues |
| Only one weight | Limits hierarchy options |

## Quick Comparison Method

When choosing between finalists:

1. Set identical paragraph with each
2. View at 100%, 150%, and 50% zoom
3. Check on phone and desktop
4. Read a full paragraph with each (actually read it)
5. Look away, then look back—which is more inviting?
6. Check file sizes and loading impact
7. Verify all needed characters exist

Trust your reading experience. If something feels "off" while reading, it probably is, even if you can't articulate why.
