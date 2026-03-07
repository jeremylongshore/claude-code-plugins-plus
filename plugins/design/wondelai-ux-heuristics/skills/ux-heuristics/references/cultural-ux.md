# Cultural UX Considerations

Designing for global audiences: RTL languages, color meanings, form conventions, and localization.

## Right-to-Left (RTL) Languages

### Languages That Use RTL

- Arabic
- Hebrew
- Persian (Farsi)
- Urdu

### What to Mirror

| Element | LTR | RTL |
|---------|-----|-----|
| Text alignment | Left | Right |
| Navigation | Left side | Right side |
| Progress indicators | Left to right | Right to left |
| Icons with direction | → | ← |
| Checkmarks | ✓ on right | ✓ on left |
| Back buttons | ← | → |
| Carousels/sliders | Swipe left for next | Swipe right for next |

### What NOT to Mirror

| Element | Reason |
|---------|--------|
| Numbers | Always LTR (123, not ٣٢١) |
| Phone numbers | Universal format |
| Clocks | Universal format |
| Video player controls | Universal convention |
| Brand logos | Design integrity |
| Math equations | Universal notation |

### CSS for RTL

```css
/* Modern approach using logical properties */
.element {
  /* Instead of margin-left: 16px */
  margin-inline-start: 16px;

  /* Instead of padding-right: 8px */
  padding-inline-end: 8px;

  /* Instead of text-align: left */
  text-align: start;

  /* Instead of float: left */
  float: inline-start;
}

/* Or use dir attribute */
[dir="rtl"] .element {
  /* RTL-specific overrides */
}
```

### RTL Icons

Icons with inherent direction need mirroring:

| Icon | Mirror? | Reason |
|------|---------|--------|
| Back arrow | Yes | Directional navigation |
| Forward arrow | Yes | Directional navigation |
| Reply icon | Yes | Shows direction of response |
| Search icon | No | Magnifying glass is universal |
| Home icon | No | House has no direction |
| Settings gear | No | Symmetric |
| Play button | No | Universal media convention |

---

## Color Meanings Across Cultures

### Red

| Culture | Meaning |
|---------|---------|
| Western | Danger, stop, error, love |
| China | Good luck, prosperity, happiness |
| India | Purity, fertility |
| South Africa | Mourning |
| Japan | Life, anger |

**Design implication:** Don't use red for error states in apps targeting Chinese markets without context.

### White

| Culture | Meaning |
|---------|---------|
| Western | Purity, cleanliness, peace |
| China/Japan | Death, mourning |
| India | Unhappiness, mourning |

**Design implication:** White space may have different connotations; "clean" design may feel empty or cold.

### Green

| Culture | Meaning |
|---------|---------|
| Western | Go, success, nature, money |
| Islamic | Sacred, paradise |
| China | Infidelity (green hat = cuckold) |
| Ireland | National identity |

**Design implication:** Green success states work globally, but be careful with green accessories or hats in Chinese contexts.

### Yellow

| Culture | Meaning |
|---------|---------|
| Western | Caution, happiness |
| Japan | Courage, royalty |
| Egypt | Mourning |
| Latin America | Death, mourning |

### Blue

| Culture | Meaning |
|---------|---------|
| Most cultures | Trust, calm, professionalism |
| Iran | Mourning, spirituality |

**Design implication:** Blue is relatively safe globally; commonly used for links and primary actions.

### General Guidelines

1. **Test with local users** - Color perception varies
2. **Don't rely on color alone** - Add icons and text
3. **Provide customization** - Let users choose colors where possible
4. **Research target markets** - Specific meanings in your target regions

---

## Form Conventions

### Name Fields

| Culture | Name Structure |
|---------|----------------|
| Western | First + Last (given + family) |
| China/Japan/Korea | Family + Given |
| Iceland | Given + Patronymic |
| Spanish | Given + Father's surname + Mother's surname |
| Arabic | Given + Father's + Grandfather's + Family |

**Best practices:**
- Use single "Full Name" field when possible
- If splitting, use "Given Name" and "Family Name" (not First/Last)
- Don't assume first/last order
- Allow long names (>50 characters)

### Address Fields

| Region | Considerations |
|--------|----------------|
| US | State, ZIP code (5 or 9 digits) |
| UK | County optional, postcode format varies |
| Japan | Prefecture, address reads large→small |
| Brazil | CEP codes |
| Countries without postal codes | 50+ countries don't use them |

**Best practices:**
- Don't require postal code universally
- Use country-appropriate field labels
- Allow flexible formats
- Consider address autocomplete services

### Phone Numbers

| Consideration | Approach |
|---------------|----------|
| Country codes | Allow input or select separately |
| Length | Varies widely (7-15 digits) |
| Format | Don't enforce specific format |
| Mobile vs landline | Labels may not translate |

**Best practices:**
- Accept multiple formats
- Store in E.164 format internally (+1234567890)
- Display in local format
- Don't validate too strictly

### Dates

| Region | Format |
|--------|--------|
| US | MM/DD/YYYY |
| Most of world | DD/MM/YYYY |
| Japan, China, Korea | YYYY/MM/DD |
| ISO standard | YYYY-MM-DD |

**Best practices:**
- Use date pickers instead of text input
- Show month names (not numbers) to avoid confusion
- Store in ISO format (YYYY-MM-DD)
- Display in user's locale

### Currency

| Consideration | Examples |
|---------------|----------|
| Symbol position | $100 vs 100€ vs 100 kr |
| Decimal separator | $1,234.56 vs €1.234,56 |
| Thousands separator | 1,000 vs 1.000 vs 1 000 |
| Currency names | Dollar, Yuan, Rupee |

**Best practices:**
- Format according to user locale
- Always show currency symbol/code
- Be clear about which currency
- Handle conversion if multi-currency

---

## Text Considerations

### Text Expansion

Translated text is often longer than English:

| Language | Expansion Factor |
|----------|------------------|
| German | 1.3x |
| French | 1.2x |
| Russian | 1.2x |
| Spanish | 1.2x |
| Chinese | 0.8x |
| Japanese | 0.9x |

**Design implications:**
- Don't design to exact English text length
- Allow buttons and labels to expand
- Test layouts with longest expected translations
- Use flexible grid/flexbox layouts

### Text in Images

Avoid text in images because:
- Can't be translated easily
- Not accessible to screen readers
- Doesn't scale with user preferences
- Complicates localization workflow

**Alternative:** Use CSS text over images.

### Numbers and Units

| Element | Consideration |
|---------|---------------|
| Measurement | Metric (most world) vs Imperial (US) |
| Paper size | A4 (most world) vs Letter (US, Canada) |
| Temperature | Celsius vs Fahrenheit |
| Time | 24-hour vs 12-hour (AM/PM) |

---

## Icons and Imagery

### Potentially Problematic Icons

| Icon | Issue | Alternative |
|------|-------|-------------|
| Mailbox | US-specific design | Envelope |
| Check mark | Means "wrong" in some cultures | Consider context |
| Thumbs up | Offensive in some cultures | Hearts, stars |
| Hand gestures | Vary widely in meaning | Avoid gestures |
| Animals | Religious/cultural sensitivities | Research target market |
| Religious symbols | May exclude or offend | Use neutral symbols |

### Photography

| Consideration | Approach |
|---------------|----------|
| Diversity | Represent target audience |
| Gestures | Avoid culture-specific gestures |
| Clothing | Consider cultural norms |
| Settings | Use locally relevant contexts |
| Food | Be aware of dietary restrictions |

---

## Localization Best Practices

### Technical

```javascript
// Use internationalization libraries
const formatter = new Intl.DateTimeFormat('de-DE');
const date = formatter.format(new Date());

const currencyFormatter = new Intl.NumberFormat('ja-JP', {
  style: 'currency',
  currency: 'JPY'
});
const price = currencyFormatter.format(1000);
```

### Content

- Use simple, clear language (easier to translate)
- Avoid idioms and colloquialisms
- Don't hardcode strings (use translation keys)
- Provide context for translators
- Test with pseudo-localization during development

### Design

- Design for flexibility (expanding text)
- Use icons with text (not alone)
- Test layouts in RTL and longest languages
- Consider reading order in complex layouts

---

## Quick Reference Checklist

Before launching internationally:

**Layout:**
- [ ] Supports RTL if targeting Arabic, Hebrew, Persian
- [ ] Text can expand 30% without breaking
- [ ] No text in images
- [ ] Icons are culturally neutral

**Forms:**
- [ ] Name fields are flexible
- [ ] Addresses work without postal codes
- [ ] Phone numbers accept various formats
- [ ] Dates use pickers or clear formats

**Content:**
- [ ] Colors don't carry unintended meaning
- [ ] Images represent target audience
- [ ] No culture-specific idioms
- [ ] Units match target region

**Technical:**
- [ ] Dates, numbers, currency use locale formatting
- [ ] All strings externalized for translation
- [ ] Character encoding supports target languages
- [ ] Font supports required character sets
