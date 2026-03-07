# Liquid Glass

Apple's new material design system for iOS 26+. Comprehensive coverage of Liquid Glass visual properties, implementation patterns, and design principles.

**When to use**: Implementing Liquid Glass effects, reviewing UI for adoption, debugging visual artifacts, requesting expert review of implementations

## Key Features

- **Expert Review Checklist** – 7-section validation checklist for reviewing Liquid Glass implementations
  - Material appropriateness (navigation layer vs content layer)
  - Variant selection (Regular vs Clear decision criteria)
  - Legibility and contrast
  - Layering and hierarchy
  - Scroll edge effects
  - Accessibility (Reduced Transparency, Increased Contrast, Reduced Motion)
  - Performance considerations
- Layered system architecture (highlights, shadows, glow, tinting)
- Troubleshooting visual artifacts, dark mode issues, performance
- Migration from UIBlurEffect/NSVisualEffectView
- Complete API reference with working code examples

**Requirements**: iOS 26+, iPadOS 26+, macOS Tahoe+, visionOS 3+, Xcode 26+

## Example Prompts

These are real questions developers ask that this skill answers:

- **"I just saw Liquid Glass in WWDC videos. How is it different from blur effects?"**
  → Explains Liquid Glass as a lensing-based material (not blur), shows design philosophy and adoption criteria

- **"I'm implementing Liquid Glass but the lensing effect looks like regular blur."**
  → Covers visual properties (lensing vs motion vs environment), Regular vs Clear variants, debugging artifacts

- **"Liquid Glass looks great on iPhone but odd on iPad."**
  → Demonstrates adaptive patterns and platform-specific guidance (iOS 26+, macOS Tahoe+, visionOS 3+)

- **"I need Liquid Glass but text legibility is terrible."**
  → Covers tinting strategies, adaptive colors, and opacity patterns for maintaining readability

- **"We want expert review of our Liquid Glass implementation."**
  → Provides comprehensive review checklist and professional push-back frameworks for design reviews

## WWDC References

- [Meet Liquid Glass – Session 219](https://developer.apple.com/videos/play/wwdc2025/219/)
- [Build a SwiftUI app with the new design – Session 323](https://developer.apple.com/videos/play/wwdc2025/323/)
