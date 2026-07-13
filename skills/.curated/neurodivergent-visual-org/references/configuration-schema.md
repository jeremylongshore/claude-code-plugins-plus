# Configuration File Schema

Users can create a configuration file to set default modes and customize behavior.

**File Location:** `.claude/neurodivergent-visual-org-preference.yml`

## Complete Configuration Example:

```yaml
# Neurodivergent Visual Org v3.1.1 Configuration

# Base mode (required, choose one)
default_mode: neurodivergent  # Options: neurodivergent, neurotypical

# Accessibility modes (optional, can enable one or both)
colorblind_safe: false         # Enable pattern-based differentiation
monochrome: false              # Enable pure B&W print optimization

# Auto-enable rules for accessibility modes
# Note: These will PROMPT for confirmation before applying
auto_prompt_monochrome:
  when_printing: true           # Suggest monochrome when printing
  when_exporting_pdf: true      # Suggest monochrome for PDF export
  when_exporting_png: false     # Keep current mode for PNG exports

auto_prompt_colorblind_safe:
  when_sharing: true            # Suggest colorblind-safe for shared docs
  when_public: true             # Suggest for public-facing documents

# Base mode customizations
neurodivergent_customizations:
  chunk_size: 4                 # Items per chunk (3-5 recommended)
  time_multiplier: 1.5          # Buffer multiplier for time estimates
  micro_step_duration: 5        # Minutes per micro-step (3-10 recommended)
  show_energy_scaffolding: true # Show spoons/breaks explicitly
  use_compassionate_language: true

neurotypical_customizations:
  chunk_size: 6                 # Items per chunk (5-7 recommended)
  time_multiplier: 1.0          # Standard time estimates
  task_duration: 20             # Minutes per task (15-30 recommended)
  show_energy_scaffolding: false
  use_direct_language: true

# Colorblind-safe mode customizations
colorblind_safe_patterns:
  keep: "short-dash"            # Options: short-dash, long-dash, dots, dot-dash, solid
  donate: "long-dash"
  maybe: "dots"
  break: "dot-dash"
  critical: "solid"

  # Border thickness (1-3 recommended)
  critical_thickness: 3
  standard_thickness: 2
  detail_thickness: 1

# Monochrome mode customizations
monochrome_fills:
  priority_1_critical: "solid-black"  # Solid black fill, white text
  priority_2_high: "white-bold"       # White fill, bold border
  priority_3_medium: "white-dashed"   # White fill, dashed border
  priority_4_standard: "white"        # White fill, standard border

# General preferences
preferences:
  always_include_legends: true  # Include pattern/color legends in diagrams
  verbose_labels: true          # Use longer, more explicit labels
  extra_whitespace: false       # Add more space between nodes (good for printing)
  show_wcag_compliance: false   # Show WCAG compliance notes

# Mermaid.live link preferences
mermaid_links:
  # IMPORTANT: <br/> tags in diagrams MUST be URL-encoded as %3Cbr%2F%3E
  # for playground links to work correctly
  auto_generate: true           # Automatically provide mermaid.live links
  use_base64: false             # Use URL params instead of base64 (more readable)
```

## Minimal Configuration (Just Change Defaults):

```yaml
# Simple config - just set your preferred defaults
default_mode: neurodivergent
colorblind_safe: true   # Always use patterns for accessibility
```

## Print-Optimized Configuration:

```yaml
# Optimized for printing and sharing
default_mode: neurodivergent
monochrome: true
preferences:
  extra_whitespace: true
  verbose_labels: true
```

## Configuration Precedence:

1. **Explicit user request** in current message (highest priority)
2. **Configuration file** settings
3. **Auto-detection** from language
4. **Default** (neurodivergent mode, no accessibility modes)

## Loading Configuration:

The skill automatically checks for `.claude/neurodivergent-visual-org-preference.yml` at the start of each conversation. If found, settings are applied. Users can override any setting with explicit requests like "use colorblind-safe mode for this diagram".
