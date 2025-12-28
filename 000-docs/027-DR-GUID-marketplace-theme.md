# Intent Solutions Theme Style Guide
## For claudecodeplugins.io Marketplace

**Generated**: 2025-10-16
**Source**: https://intentsolutions.io
**Target**: Astro 5 + Tailwind CSS v4

---

## Color Palette

### Primary Colors
```css
--color-background: #FFFFFF;
--color-background-subtle: #FAFAFA;
--color-text-primary: #1a1a1a;
--color-text-secondary: #666666;
--color-accent: #0066CC;
--color-border: #E5E5E5;
```

### Tailwind CSS v4 Configuration
```css
@theme {
  --color-background: #FFFFFF;
  --color-background-subtle: #FAFAFA;
  --color-text-primary: #1a1a1a;
  --color-text-secondary: #666666;
  --color-accent: #0066CC;
  --color-border: #E5E5E5;
}
```

### Usage Examples
- **Backgrounds**: `bg-white`, `bg-[#FAFAFA]`
- **Text**: `text-[#1a1a1a]`, `text-[#666666]`
- **Accents**: `text-[#0066CC]`, `hover:text-[#0066CC]`
- **Borders**: `border-[#E5E5E5]`

---

## Typography

### Font Stack
```css
font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif;
```

**Tailwind**: `font-sans` (default system font stack)

### Type Scale

| Element | Size | Weight | Line Height | Tailwind Classes |
|---------|------|--------|-------------|------------------|
| **H1** | 2.5-3rem (40-48px) | 700-800 | 1.2 | `text-5xl font-bold leading-tight` |
| **H2** | 2rem (32px) | 700 | 1.3 | `text-4xl font-bold leading-snug` |
| **H3** | 1.5rem (24px) | 600 | 1.4 | `text-2xl font-semibold leading-normal` |
| **H4** | 1.25rem (20px) | 600 | 1.4 | `text-xl font-semibold` |
| **Body** | 1rem (16px) | 400 | 1.6 | `text-base leading-relaxed` |
| **Small** | 0.875rem (14px) | 400 | 1.5 | `text-sm` |

### Typography Classes
```html
<!-- Hero Heading -->
<h1 class="text-5xl font-bold text-[#1a1a1a] leading-tight">

<!-- Section Heading -->
<h2 class="text-4xl font-bold text-[#1a1a1a] leading-snug mb-6">

<!-- Body Text -->
<p class="text-base text-[#666666] leading-relaxed">

<!-- Small Text -->
<span class="text-sm text-[#666666]">
```

---

## Layout Patterns

### Container System
```html
<!-- Main Container -->
<div class="max-w-screen-xl mx-auto px-4 sm:px-6 lg:px-8">

<!-- Narrow Container -->
<div class="max-w-4xl mx-auto px-4">

<!-- Wide Container -->
<div class="max-w-7xl mx-auto px-6">
```

### Spacing System (Consistent rem-based)
- **Extra Small**: `0.5rem` → `space-y-2`, `gap-2`, `p-2`
- **Small**: `1rem` → `space-y-4`, `gap-4`, `p-4`
- **Medium**: `1.5rem` → `space-y-6`, `gap-6`, `p-6`
- **Large**: `2rem` → `space-y-8`, `gap-8`, `p-8`
- **Extra Large**: `3rem` → `space-y-12`, `gap-12`, `p-12`

### Section Padding
```html
<!-- Standard Section -->
<section class="py-16 px-4 sm:px-6 lg:px-8">

<!-- Hero Section -->
<section class="py-24 px-4 sm:px-6 lg:px-8">

<!-- Compact Section -->
<section class="py-12 px-4">
```

---

## Component Styles

### Buttons

#### Primary Button (CTA)
```html
<a href="#" class="inline-block px-6 py-3 text-base font-semibold text-white bg-[#0066CC] rounded-md hover:bg-[#0052a3] transition-colors duration-200">
  Start a Project
</a>
```

#### Secondary Button
```html
<a href="#" class="inline-block px-6 py-3 text-base font-semibold text-[#1a1a1a] border-2 border-[#E5E5E5] rounded-md hover:border-[#0066CC] hover:text-[#0066CC] transition-colors duration-200">
  Learn More
</a>
```

#### Text Link
```html
<a href="#" class="text-[#0066CC] hover:underline transition-all duration-200">
  View Details →
</a>
```

### Navigation

#### Header Navigation
```html
<header class="bg-white border-b border-[#E5E5E5]">
  <div class="max-w-screen-xl mx-auto px-4 sm:px-6 lg:px-8">
    <nav class="flex items-center justify-between h-16">
      <!-- Logo -->
      <div class="text-xl font-bold text-[#1a1a1a]">
        Logo
      </div>

      <!-- Navigation Links -->
      <ul class="hidden md:flex items-center gap-8">
        <li><a href="#" class="text-base text-[#666666] hover:text-[#0066CC] transition-colors">Home</a></li>
        <li><a href="#" class="text-base text-[#666666] hover:text-[#0066CC] transition-colors">About</a></li>
        <li><a href="#" class="text-base text-[#666666] hover:text-[#0066CC] transition-colors">Services</a></li>
        <li><a href="#" class="text-base text-[#666666] hover:text-[#0066CC] transition-colors">Contact</a></li>
      </ul>

      <!-- Mobile Menu Button -->
      <button class="md:hidden text-[#1a1a1a]">
        Menu
      </button>
    </nav>
  </div>
</header>
```

### Cards

#### Service Card
```html
<div class="bg-white border border-[#E5E5E5] rounded-lg p-6 hover:shadow-lg transition-shadow duration-300">
  <h3 class="text-2xl font-semibold text-[#1a1a1a] mb-3">
    Service Title
  </h3>
  <p class="text-base text-[#666666] leading-relaxed mb-4">
    Service description goes here with clear value proposition.
  </p>
  <a href="#" class="text-[#0066CC] hover:underline font-semibold">
    Learn More →
  </a>
</div>
```

#### Project Showcase Card
```html
<article class="bg-white border border-[#E5E5E5] rounded-lg overflow-hidden hover:shadow-xl transition-shadow duration-300">
  <div class="p-6">
    <h3 class="text-xl font-semibold text-[#1a1a1a] mb-2">
      Project Name
    </h3>
    <p class="text-sm text-[#666666] mb-4">
      Tech Stack: React, Node.js, PostgreSQL
    </p>
    <a href="#" class="text-[#0066CC] hover:underline font-semibold text-sm">
      View Case Study →
    </a>
  </div>
</article>
```

#### Plugin Card (for Marketplace)
```html
<div class="bg-white border border-[#E5E5E5] rounded-lg p-6 hover:border-[#0066CC] hover:shadow-lg transition-all duration-300">
  <div class="flex items-start justify-between mb-3">
    <h3 class="text-xl font-semibold text-[#1a1a1a]">
      Plugin Name
    </h3>
    <span class="text-xs font-semibold px-2 py-1 bg-[#FAFAFA] text-[#666666] rounded">
      v1.0.0
    </span>
  </div>
  <p class="text-sm text-[#666666] leading-relaxed mb-4">
    Plugin description explaining what it does and value.
  </p>
  <div class="flex items-center gap-2 mb-4">
    <span class="text-xs px-2 py-1 bg-[#FAFAFA] text-[#666666] rounded">security</span>
    <span class="text-xs px-2 py-1 bg-[#FAFAFA] text-[#666666] rounded">devops</span>
  </div>
  <button class="w-full px-4 py-2 text-sm font-semibold text-white bg-[#0066CC] rounded-md hover:bg-[#0052a3] transition-colors">
    Install Plugin
  </button>
</div>
```

---

## Hero Section Pattern

```html
<section class="relative bg-white py-24 px-4 sm:px-6 lg:px-8">
  <div class="max-w-4xl mx-auto text-center">
    <h1 class="text-5xl font-bold text-[#1a1a1a] leading-tight mb-6">
      Clear Value Proposition Headline
    </h1>
    <p class="text-xl text-[#666666] leading-relaxed mb-8 max-w-2xl mx-auto">
      Supporting description that explains what you do and who you serve.
    </p>
    <div class="flex flex-col sm:flex-row items-center justify-center gap-4">
      <a href="#" class="inline-block px-8 py-4 text-lg font-semibold text-white bg-[#0066CC] rounded-md hover:bg-[#0052a3] transition-colors">
        Primary CTA
      </a>
      <a href="#" class="inline-block px-8 py-4 text-lg font-semibold text-[#1a1a1a] border-2 border-[#E5E5E5] rounded-md hover:border-[#0066CC] hover:text-[#0066CC] transition-colors">
        Secondary CTA
      </a>
    </div>
  </div>
</section>
```

---

## Grid Layouts

### Three Column Grid
```html
<div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-8">
  <!-- Cards here -->
</div>
```

### Two Column Grid
```html
<div class="grid grid-cols-1 lg:grid-cols-2 gap-12 items-center">
  <!-- Content and image -->
</div>
```

### Four Column Grid (for categories)
```html
<div class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-6">
  <!-- Category cards -->
</div>
```

---

## Footer Pattern

```html
<footer class="bg-[#FAFAFA] border-t border-[#E5E5E5] py-12">
  <div class="max-w-screen-xl mx-auto px-4 sm:px-6 lg:px-8">
    <div class="grid grid-cols-1 md:grid-cols-4 gap-8 mb-8">
      <!-- Company Info -->
      <div>
        <h4 class="text-lg font-semibold text-[#1a1a1a] mb-4">Company</h4>
        <p class="text-sm text-[#666666] leading-relaxed">
          Brief company description or tagline.
        </p>
      </div>

      <!-- Links Column 1 -->
      <div>
        <h4 class="text-sm font-semibold text-[#1a1a1a] mb-4 uppercase tracking-wider">Product</h4>
        <ul class="space-y-2">
          <li><a href="#" class="text-sm text-[#666666] hover:text-[#0066CC]">Features</a></li>
          <li><a href="#" class="text-sm text-[#666666] hover:text-[#0066CC]">Pricing</a></li>
        </ul>
      </div>

      <!-- Links Column 2 -->
      <div>
        <h4 class="text-sm font-semibold text-[#1a1a1a] mb-4 uppercase tracking-wider">Resources</h4>
        <ul class="space-y-2">
          <li><a href="#" class="text-sm text-[#666666] hover:text-[#0066CC]">Documentation</a></li>
          <li><a href="#" class="text-sm text-[#666666] hover:text-[#0066CC]">Guides</a></li>
        </ul>
      </div>

      <!-- Links Column 3 -->
      <div>
        <h4 class="text-sm font-semibold text-[#1a1a1a] mb-4 uppercase tracking-wider">Company</h4>
        <ul class="space-y-2">
          <li><a href="#" class="text-sm text-[#666666] hover:text-[#0066CC]">About</a></li>
          <li><a href="#" class="text-sm text-[#666666] hover:text-[#0066CC]">Contact</a></li>
        </ul>
      </div>
    </div>

    <!-- Copyright -->
    <div class="border-t border-[#E5E5E5] pt-8">
      <p class="text-sm text-[#666666] text-center">
        © 2025 Company Name. All rights reserved.
      </p>
    </div>
  </div>
</footer>
```

---

## Special Effects

### Shadows
```css
/* Subtle hover shadow */
hover:shadow-lg

/* Card shadow on hover */
hover:shadow-xl

/* Tailwind Custom */
shadow-sm: 0 1px 2px 0 rgba(0, 0, 0, 0.05)
shadow: 0 1px 3px 0 rgba(0, 0, 0, 0.1)
shadow-lg: 0 10px 15px -3px rgba(0, 0, 0, 0.1)
shadow-xl: 0 20px 25px -5px rgba(0, 0, 0, 0.1)
```

### Transitions
```css
/* Standard transition */
transition-colors duration-200

/* Smooth all */
transition-all duration-300

/* Shadow transition */
transition-shadow duration-300
```

### Border Radius
```css
/* Standard */
rounded-md (0.375rem / 6px)

/* Large */
rounded-lg (0.5rem / 8px)

/* Pills */
rounded-full
```

---

## Responsive Breakpoints

```css
/* Mobile First */
Default: < 640px

sm: 640px   /* Small tablets */
md: 768px   /* Tablets */
lg: 1024px  /* Laptops */
xl: 1280px  /* Desktops */
2xl: 1536px /* Large desktops */
```

### Responsive Utilities Pattern
```html
<!-- Hide on mobile, show on desktop -->
<div class="hidden lg:block">

<!-- Show on mobile, hide on desktop -->
<div class="block lg:hidden">

<!-- Responsive grid -->
<div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3">

<!-- Responsive padding -->
<div class="px-4 sm:px-6 lg:px-8">

<!-- Responsive text -->
<h1 class="text-3xl md:text-4xl lg:text-5xl">
```

---

## Application to ClaudeCodePlugins Marketplace

### Recommended Component Mapping

| Marketplace Element | Intent Solutions Pattern |
|---------------------|-------------------------|
| Plugin Cards | Service Cards (white bg, border, hover shadow) |
| Category Navigation | Header Navigation (horizontal, minimal) |
| Hero Section | Centered hero with dual CTAs |
| Plugin Grid | 3-column grid on desktop, 1-column mobile |
| Sponsor Page | Project showcase cards |
| Skill Enhancers Category | Service cards with tech stack tags |
| Footer | 4-column footer with links |

### Key Design Principles
1. **Minimalism**: Clean white backgrounds, subtle borders
2. **High Contrast**: Dark text (#1a1a1a) on white backgrounds
3. **Accent Sparingly**: Blue (#0066CC) only for interactive elements
4. **Consistent Spacing**: rem-based scale (0.5, 1, 1.5, 2, 3)
5. **Subtle Interactions**: Hover states with color shifts and shadows
6. **Mobile First**: Responsive grids and flexible layouts

---

## Quick Start Implementation

### 1. Update Tailwind Config (if using custom theme)
```js
// tailwind.config.js
export default {
  theme: {
    extend: {
      colors: {
        'brand-accent': '#0066CC',
        'text-primary': '#1a1a1a',
        'text-secondary': '#666666',
        'border-light': '#E5E5E5',
        'bg-subtle': '#FAFAFA',
      },
    },
  },
}
```

### 2. Global Styles (for Astro)
```css
/* src/styles/global.css */
@tailwind base;
@tailwind components;
@tailwind utilities;

@layer base {
  body {
    @apply text-base text-[#1a1a1a] bg-white font-sans leading-relaxed;
  }

  h1 { @apply text-5xl font-bold leading-tight; }
  h2 { @apply text-4xl font-bold leading-snug; }
  h3 { @apply text-2xl font-semibold; }

  a {
    @apply transition-colors duration-200;
  }
}

@layer components {
  .btn-primary {
    @apply inline-block px-6 py-3 text-base font-semibold text-white bg-[#0066CC] rounded-md hover:bg-[#0052a3] transition-colors;
  }

  .btn-secondary {
    @apply inline-block px-6 py-3 text-base font-semibold text-[#1a1a1a] border-2 border-[#E5E5E5] rounded-md hover:border-[#0066CC] hover:text-[#0066CC] transition-colors;
  }

  .card {
    @apply bg-white border border-[#E5E5E5] rounded-lg p-6 hover:shadow-lg transition-shadow duration-300;
  }
}
```

### 3. Example Astro Component
```astro
---
// src/components/PluginCard.astro
interface Props {
  name: string;
  description: string;
  version: string;
  category: string;
}

const { name, description, version, category } = Astro.props;
---

<div class="card hover:border-[#0066CC]">
  <div class="flex items-start justify-between mb-3">
    <h3 class="text-xl font-semibold text-[#1a1a1a]">{name}</h3>
    <span class="text-xs font-semibold px-2 py-1 bg-[#FAFAFA] text-[#666666] rounded">
      {version}
    </span>
  </div>
  <p class="text-sm text-[#666666] leading-relaxed mb-4">
    {description}
  </p>
  <div class="flex items-center gap-2 mb-4">
    <span class="text-xs px-2 py-1 bg-[#FAFAFA] text-[#666666] rounded">
      {category}
    </span>
  </div>
  <button class="btn-primary w-full">
    Install Plugin
  </button>
</div>
```

---

**End of Style Guide**
**Generated**: 2025-10-16
**Next Steps**: Apply these patterns to claudecodeplugins.io marketplace components
