# iOS Colors & Theming Reference

SKILL.md section 3 covers the core semantic palette (`label`, `secondaryLabel`, `systemBackground`, `systemBlue`/`systemRed`/`systemGreen`) and the three Dark Mode adaptation rules. This file adds what it does not carry: the extra layering tokens and the full WCAG contrast table.

## Extra Semantic Tokens (beyond the core set)

For multi-level hierarchy and grouped layouts, reach past the core six:

```swift
Color(.tertiaryLabel)              // 3rd-level text (placeholders, disabled)
Color(.quaternaryLabel)            // 4th-level (separators, faint glyphs)
Color(.secondarySystemBackground)  // elevated cards / grouped table sections
Color(.tertiarySystemBackground)   // a layer above secondary
Color(.systemGroupedBackground)    // base behind grouped lists (Settings style)
Color(.separator)                  // hairline dividers (already mode-aware)
```

Use the grouped-background family for `.insetGrouped` lists; use the plain `systemBackground` family for full-bleed content.

## Color Contrast (full WCAG table)

SKILL.md states the 4.5:1 floor for body text. The complete set of minimums:

| Content | Minimum ratio |
|---------|---------------|
| Normal text (< 18pt, or < 14pt bold) | 4.5:1 |
| Large text (>= 18pt, or >= 14pt bold) | 3:1 |
| UI components and graphical objects (icons, control borders, focus rings) | 3:1 |

Verify with Xcode's Accessibility Inspector color contrast check, in both light and dark modes and with Increase Contrast enabled.
