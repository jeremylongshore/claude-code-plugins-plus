# iOS Typography Guidelines

## System Font: San Francisco

iOS uses San Francisco (SF Pro) as the default typeface. Use system text styles for automatic Dynamic Type support.

## Standard Text Styles

| Element | Size | Weight | Color |
|---------|------|--------|-------|
| Large Title (unscrolled) | 34pt | Bold | #000000 |
| Title (scrolled) | 17pt | Medium | #000000 |
| Body text, List items | 17pt | Regular | #000000 |
| Secondary text | 15pt | Regular | #3C3C43 @ 60% |
| Caption, Tertiary | 12-13pt | Regular | #3C3C43 @ 60% |
| Tab bar labels | 10pt | Regular | #8A8A8E |

## Typography Rules

1. **Minimum text size**: 11pt (for captions/secondary info)
2. **Line height**: Minimum 1.3× font size for paragraphs
3. **Line length**: 35-50 characters per line for mobile
4. **Alignment**: Left-aligned, non-justified text
5. **Hierarchy**: Use weight and color variation, not size extremes
6. **Contrast**: Minimum 4.5:1 ratio (WCAG AA standard)

```swift
// Use semantic text styles for Dynamic Type support
Text("Title")
    .font(.title)

Text("Body content")
    .font(.body)

Text("Caption")
    .font(.caption)
    .foregroundColor(.secondary)
```

## Dark Mode Typography

- Black text (#000) → White (#FFF)
- Dark gray text → Light gray text
- Background colors shift darker (maintain relative hierarchy)
