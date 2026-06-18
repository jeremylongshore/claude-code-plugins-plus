# iOS Colors & Theming

## Semantic Colors

Use semantic colors that automatically adapt to light/dark mode:

```swift
Color(.label)              // Primary text
Color(.secondaryLabel)     // Secondary text
Color(.tertiaryLabel)      // Tertiary text
Color(.systemBackground)   // Primary background
Color(.secondarySystemBackground)  // Elevated/grouped
Color(.systemBlue)         // Default tint/accent
Color(.systemRed)          // Destructive actions
Color(.systemGreen)        // Success/confirmation
```

## Dark Mode Guidelines

1. **Text**: Invert colors (dark → light)
2. **Backgrounds**: Shift darker while maintaining relative hierarchy
3. **Accent colors**: Adjust to pop against dark backgrounds (often lower brightness, higher saturation)

```swift
// Preview both modes during development
struct ContentView_Previews: PreviewProvider {
    static var previews: some View {
        ContentView()
            .preferredColorScheme(.light)
        ContentView()
            .preferredColorScheme(.dark)
    }
}
```

## Color Contrast

Minimum contrast ratios (WCAG):
- **4.5:1** for normal text
- **3:1** for large text (18pt+ or 14pt+ bold)
- **3:1** for UI components
