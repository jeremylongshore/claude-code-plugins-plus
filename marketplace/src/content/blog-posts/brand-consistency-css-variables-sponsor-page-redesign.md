---
title: "Implementing Brand Consistency with CSS Variables: A Sponsor Page Redesign"
description: "How to migrate a sponsor page from inconsistent hardcoded colors to a cohesive brand design system using CSS variables, with real examples from Claude Code Plugins marketplace."
date: "2025-12-02"
tags: ["css", "design-systems", "frontend", "astro", "branding", "web-development"]
featured: false
---
When your sponsor page looks like it belongs to a different website than your homepage, you have a brand consistency problem. Here's how I fixed it—and what I learned about the iterative process of design system migration.

## The Problem: Three Different Color Schemes

The Claude Code Plugins marketplace had evolved organically. The homepage used Anthropic's warm, professional brand colors (orange, green, earthy tones). The sponsor page? Still using generic blue CTAs and inconsistent grays from an earlier design phase.

**Initial state:**

- Homepage: Anthropic orange (#d97757), green (#788c5d), sophisticated grays
- Sponsor page: Generic blue (#0066CC), basic grays, no brand alignment
- Result: Users clicking from homepage to sponsor page felt like they'd left the site

This wasn't just aesthetic—it undermined the professional positioning we were trying to establish for enterprise sponsors like Nixtla.

## The False Start: Find and Replace

My first instinct? Global find-replace. Search for `#0066CC`, replace with `#d97757`. Ship it.

**Why this failed:**

```css
/* This approach creates maintenance hell */
.cta-primary {
  color: #FFFFFF;
  background: #0066CC;  /* Just changed to #d97757 */
}

.pricing-tier {
  color: #0066CC;  /* Also changed to #d97757 */
}

/* What about hover states? */
.cta-primary:hover {
  background: #0052a3;  /* This is a darker shade of the OLD blue */
}
```

The hover state broke. The darker shade `#0052a3` was calculated for blue, not orange. I'd need to manually calculate new hover shades for every color change.

Worse: what about the 15 other places using grays, borders, and backgrounds? This would take dozens of replacements and introduce inconsistencies.

## The Right Approach: CSS Variables First

Instead of chasing colors through 1,200 lines of CSS, establish the design system once:

```css
:root {
  /* Main Colors */
  --brand-dark: #141413;
  --brand-light: #faf9f5;
  --brand-mid-gray: #b0aea5;
  --brand-light-gray: #e8e6dc;

  /* Accent Colors */
  --brand-orange: #d97757;
  --brand-blue: #6a9bcc;
  --brand-green: #788c5d;

  /* Derived Colors */
  --brand-orange-dark: #c45e3e;
  --brand-orange-light: #e8937a;
}
```

Now all colors reference the system:

```css
/* Before: Brittle, hardcoded */
.cta-primary {
  color: #FFFFFF;
  background: #0066CC;
}

.cta-primary:hover {
  background: #0052a3;  /* Manually calculated darker shade */
}

/* After: Flexible, maintainable */
.cta-primary {
  color: var(--brand-light);
  background: var(--brand-orange);
}

.cta-primary:hover {
  background: var(--brand-orange-dark);  /* Defined once, used everywhere */
}
```

## The Migration Process: 13 Strategic Replacements

Rather than 100+ individual color changes, I focused on component-level migrations:

### 1. Hero Section (Immediate Brand Impact)

```css
.sponsor-hero {
  background: var(--brand-light);  /* Was #FFFFFF */
  border-bottom: 1px solid var(--brand-light-gray);  /* Was #E5E5E5 */
}

.sponsor-hero h1 {
  color: var(--brand-dark);  /* Was #1a1a1a */
}

.stat-number {
  color: var(--brand-orange);  /* Was #0066CC - blue accent */
}
```

**Impact:** Users immediately see brand alignment when landing on sponsor page.

### 2. CTA Buttons (Conversion Elements)

```css
.cta-primary {
  color: var(--brand-light);
  background: var(--brand-orange);  /* Primary brand action color */
}

.cta-primary:hover {
  background: var(--brand-orange-dark);
  box-shadow: 0 10px 20px rgba(217, 119, 87, 0.2);  /* Orange-based shadow */
}

.cta-secondary {
  color: var(--brand-dark);
  border: 2px solid var(--brand-light-gray);
}

.cta-secondary:hover {
  border-color: var(--brand-orange);
  color: var(--brand-orange);  /* Subtle brand color on interaction */
}
```

**Impact:** All CTAs now use consistent brand orange instead of generic blue.

### 3. Pricing Cards (Trust Elements)

```css
.pricing-card {
  background: var(--brand-light);
  border: 2px solid var(--brand-light-gray);
}

.pricing-card:hover {
  border-color: var(--brand-orange);  /* Interactive brand feedback */
}

.pricing-card.featured {
  border-color: var(--brand-orange);
  background: linear-gradient(180deg, var(--brand-light) 0%, #faf5ee 100%);
}

.pricing-features li::before {
  content: "✓";
  color: var(--brand-green);  /* Success/approval indicator */
}
```

**Why green for checkmarks?** In the Anthropic brand palette, green (#788c5d) signals trust and approval. Blue felt too corporate, orange too attention-grabbing. Green was perfect for "yes, this feature is included."

### 4. Tables and Data Display

```css
.comparison-table {
  background: var(--brand-light);
  border: 1px solid var(--brand-light-gray);
}

.comparison-table th {
  background: var(--brand-light-gray);
  color: var(--brand-dark);
}

.check-icon {
  color: var(--brand-green);  /* Consistent with pricing cards */
}
```

### 5. Roadmap and Success Cards

```css
.roadmap-tier {
  background: rgba(217, 119, 87, 0.1);  /* 10% opacity orange */
  color: var(--brand-orange);
}

.roadmap-card:hover {
  border-color: var(--brand-orange);
}

.success-quote {
  border-left: 3px solid var(--brand-orange);
  color: var(--brand-mid-gray);
}
```

**Pattern learned:** Use brand-orange at 10% opacity for subtle backgrounds, full color for borders and accents.

### 6. Final CTA Section

```css
.final-cta {
  background: linear-gradient(135deg, var(--brand-orange) 0%, var(--brand-orange-dark) 100%);
  color: var(--brand-light);
}

.final-cta .cta-primary {
  background: var(--brand-light);
  color: var(--brand-orange);  /* Inverted for contrast */
}
```

## The Mobile Overflow Problem (Discovered During Testing)

While testing the color changes on mobile, I noticed horizontal scrolling. The colors looked great, but the page was broken.

**Root cause:**

```css
/* Footer had excessive padding */
footer {
  padding: 4rem 2rem;  /* 4rem = 64px on all sides */
}

.footer-links {
  display: flex;
  gap: 2rem;
  /* No flex-wrap! Long links forced overflow */
}
```

On iPhone screens (390px), the padding alone consumed 128px (64px × 2), leaving only 262px for content. Links with text like "Enterprise GitHub Sponsors" broke the layout.

**Fix:**

```css
footer {
  padding: 4rem 2rem;  /* Reduced from 4rem all sides */
  box-sizing: border-box;  /* Include padding in width calculation */
}

.footer-links {
  display: flex;
  gap: 2rem;
  flex-wrap: wrap;  /* Allow links to wrap on small screens */
  justify-content: center;
}

@media (max-width: 480px) {
  footer {
    padding: 2rem 1rem;  /* Even more conservative on tiny screens */
  }
}
```

## Git Workflow: Three Commits, Three Concerns

```bash
# 1. Messaging transformation (separate from design)
git commit -m "feat: reposition sponsorship as investment partnerships"

# 2. Mobile fix (critical usability issue)
git commit -m "fix: resolve footer horizontal overflow on mobile devices"

# 3. Brand colors (pure design system change)
git commit -m "fix(sponsor): update sponsor page to match Anthropic brand colors"
```

**Why separate commits?**

- **Messaging** could be reverted without affecting design
- **Mobile fix** was a critical bug that needed quick rollback capability
- **Brand colors** was a safe, large-scale visual change

Each commit could be cherry-picked, reverted, or deployed independently.

## Deployment and Verification

```bash
# Local dev check
cd marketplace && npm run dev
# Verified at http://localhost:4321/sponsor/

# Production deployment
git push origin main
# GitHub Actions auto-deploys to https://claudecodeplugins.io/sponsor/

# Verify deployment
curl -I https://claudecodeplugins.io/sponsor/
# HTTP/2 200 - deployed successfully
```

**Cache consideration:** GitHub Pages has a 10-minute CDN cache. After deployment, I waited 15 minutes before verifying the live changes to ensure I wasn't seeing stale cached content.

## Lessons: Design System Migration

### What Worked

1. **CSS variables prevent ripple effects** - Change `--brand-orange` once, update 50+ usages automatically
2. **Component-level thinking** - Migrate hero section, then CTAs, then cards—each self-contained
3. **Test on real devices** - Desktop looked fine, mobile revealed the overflow bug
4. **Separate concerns in commits** - Content changes separate from design changes
5. **Deploy in stages** - Homepage first, sponsor page second, verify consistency

### What I'd Do Differently

1. **Audit mobile first** - I found the overflow issue late because I was focused on colors
2. **Document color semantics** - Why is green for checkmarks? Why orange for CTAs? Write it down
3. **Create design token documentation** - `--brand-orange` is obvious, but what about `--brand-light-gray` vs `--brand-mid-gray`?

### The Real Win

Before this migration, changing the brand colors would have required touching hundreds of lines of CSS across multiple files. With CSS variables, I can now rebrand the entire site by updating 10 variables in one place.

That's the power of design systems: not making things look good once, but making it easy to keep them looking good forever.

## Technical Specs

- **Framework:** Astro 5.15.6
- **Styling:** Custom CSS with design tokens
- **Typography:** Lora (serif) for body, Poppins (sans-serif) for headings
- **Deployment:** GitHub Actions → GitHub Pages
- **Cache:** CloudFlare CDN, 10-minute cache
- **Lines changed:** 123 insertions, 95 deletions (net +28 lines)

**Related posts:**

- Automating Developer Workflows with Custom AI Commands
- AI-Assisted Technical Writing Automation Workflows
