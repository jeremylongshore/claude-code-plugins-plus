---
name: windsurf-theme-customization
description: |
  Configure Windsurf themes and visual settings for accessibility. Activate when users mention
  "change theme", "customize colors", "accessibility settings", "visual preferences",
  or "dark mode". Handles theme configuration and accessibility compliance.
allowed-tools: Read,Write,Edit
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
---

# Windsurf Theme Customization

Configure visual settings for accessibility and developer comfort.

## Directory Structure

```
~/.windsurf/
    settings.json                # Global visual settings
        # Color theme selection
        # Font configuration
        # UI scale settings
        # Accessibility options

    themes/
        custom-dark.json         # Custom dark theme
            # Editor colors
            # Syntax highlighting
            # UI element colors
            # Cascade panel styling

        custom-light.json        # Custom light theme
            # High contrast options
            # Reduced eye strain colors
            # Print-friendly settings

project-root/
    .vscode/
        settings.json            # Project theme overrides
            # Workspace-specific colors
            # Language-specific highlighting
            # Semantic token colors

    .windsurfrules               # AI response formatting
        # Code block styling preferences
        # Diff highlighting colors
        # Cascade output formatting
```

## Theme Configuration

### Color Accessibility
- Minimum 4.5:1 contrast ratio for text
- Distinct colors for syntax elements
- Color-blind friendly palettes
- Focus indicators for keyboard navigation

### Font Settings
- Editor font: Monospace with ligature support
- Terminal font: Clear distinction from editor
- UI font: System default or accessible choice
- Font size: Scalable based on preference

## Configuration Steps

1. **Select Base Theme**
   - Choose dark or light base
   - Consider time-of-day switching
   - Test with actual code samples

2. **Customize Colors**
   - Adjust syntax highlighting
   - Configure UI element colors
   - Set Cascade panel styling

3. **Verify Accessibility**
   - Check contrast ratios
   - Test keyboard navigation
   - Validate with accessibility tools

## Success Criteria

- WCAG 2.1 AA compliance
- Correct rendering across all panels
- Reduced eye strain and fatigue
