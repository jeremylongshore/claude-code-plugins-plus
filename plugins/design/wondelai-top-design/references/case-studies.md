# Case Studies: Agency Technique Analysis

## Table of Contents
1. Locomotive (Montreal)
2. Studio Freight (New York)
3. AREA 17 (Paris/NYC)
4. Hello Monday (Copenhagen/NYC)
5. Dogstudio (Belgium/Chicago)
6. Tonik (Poland)
7. Instrument (Portland)
8. Active Theory (LA)
9. Common Patterns Across Elite Agencies

---

## 1. Locomotive (Montreal)

**Signature: Smooth, refined, editorial precision**

### Technical Fingerprint
```
STACK
├── Custom scroll (Locomotive Scroll - they created it)
├── GSAP for animations
├── Custom vanilla JS
├── No heavy frameworks
└── Hand-crafted CSS

SIGNATURE TECHNIQUES
├── Extreme smooth scrolling with lerp
├── Parallax on almost everything (but subtle)
├── Split text animations on every headline
├── Magnetic cursor effects
├── Scale-up reveals on scroll
```

### Design Patterns
```css
/* Locomotive-style color palette */
:root {
  --loco-cream: #f5f2eb;
  --loco-black: #1a1a1a;
  --loco-accent: #ff5c00;
}

/* Their characteristic wide spacing */
.loco-section {
  padding: 20vh 0;
}

/* Massive display type */
.loco-hero-title {
  font-size: clamp(4rem, 15vw, 18rem);
  font-weight: 500;
  letter-spacing: -0.04em;
  line-height: 0.85;
}
```

### Animation Style
```javascript
// Locomotive-style page reveal
gsap.timeline()
  .from(".hero-title .word", {
    y: "110%",
    duration: 1.4,
    ease: "expo.out",
    stagger: 0.08
  })
  .from(".hero-meta", {
    opacity: 0,
    y: 30,
    duration: 0.8,
    ease: "expo.out"
  }, "-=0.8");
```

---

## 2. Studio Freight (New York)

**Signature: Bold, typographic, tech-forward**

### Technical Fingerprint
```
STACK
├── Lenis (they created it)
├── React/Next.js
├── GSAP with custom easings
├── Three.js for 3D elements
├── Heavy WebGL use

SIGNATURE TECHNIQUES
├── Massive typography as hero
├── Shader-based transitions
├── Horizontal scroll sections
├── Custom cursor interactions
├── Grid-breaking layouts
```

### Design Patterns
```css
/* Studio Freight aesthetic */
:root {
  --sf-black: #0e0e0e;
  --sf-white: #f8f8f8;
  --sf-rust: #c4553d;
}

/* Their bold type treatment */
.sf-headline {
  font-family: 'Monument Extended', sans-serif;
  font-size: clamp(3rem, 12vw, 14rem);
  font-weight: 800;
  text-transform: uppercase;
  letter-spacing: -0.03em;
}

/* Characteristic list styling */
.sf-list {
  font-family: 'Neue Montreal', sans-serif;
  font-size: 1rem;
  letter-spacing: 0.02em;
}

.sf-list li {
  padding: 1rem 0;
  border-bottom: 1px solid rgba(255,255,255,0.1);
}

.sf-list li::before {
  content: '→';
  margin-right: 0.5rem;
}
```

### Their Project Card Style
```css
.sf-project-card {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 1rem;
  padding: 2rem;
  background: var(--sf-black);
  transition: transform 0.6s cubic-bezier(0.16, 1, 0.3, 1);
}

.sf-project-card:hover {
  transform: scale(0.98);
}

.sf-project-card img {
  transition: transform 0.8s cubic-bezier(0.16, 1, 0.3, 1);
}

.sf-project-card:hover img {
  transform: scale(1.05);
}
```

---

## 3. AREA 17 (Paris/NYC)

**Signature: Sophisticated, institutional, systematic**

### Technical Fingerprint
```
STACK
├── Twill (their CMS)
├── Vue.js preference
├── GSAP for animations
├── Custom design systems
└── Enterprise-grade infrastructure

SIGNATURE TECHNIQUES
├── Restrained animations
├── Perfect typography
├── Systematic color application
├── Accessibility-first
├── Content-driven layouts
```

### Design Patterns
```css
/* AREA 17 systematic approach */
:root {
  /* They use client's brand colors systematically */
  --brand-primary: currentColor;
  --text-primary: #1a1a1a;
  --text-secondary: #666666;
  --surface: #ffffff;
  --border: #e5e5e5;
}

/* Their grid is always precise */
.a17-grid {
  display: grid;
  grid-template-columns: repeat(12, 1fr);
  gap: 2rem;
  max-width: 1440px;
  margin: 0 auto;
  padding: 0 4rem;
}

/* Typography hierarchy */
.a17-h1 {
  font-size: clamp(2.5rem, 5vw, 4rem);
  font-weight: 400;
  line-height: 1.1;
  letter-spacing: -0.02em;
}

.a17-body {
  font-size: 1.125rem;
  line-height: 1.6;
  max-width: 65ch;
}
```

### Animation Philosophy
```javascript
// AREA 17 - restrained, purposeful
// They rarely use flashy effects

// Simple fade up on scroll
gsap.utils.toArray('[data-reveal]').forEach(el => {
  gsap.from(el, {
    y: 40,
    opacity: 0,
    duration: 0.8,
    ease: "power2.out",
    scrollTrigger: {
      trigger: el,
      start: "top 85%"
    }
  });
});

// No stagger, no split text, just clean reveals
```

---

## 4. Hello Monday (Copenhagen/NYC)

**Signature: Playful, inventive, technically ambitious**

### Technical Fingerprint
```
STACK
├── React/Next.js
├── Three.js / WebGL heavy
├── GSAP + custom physics
├── Pixel-perfect craft
└── Experimental approaches

SIGNATURE TECHNIQUES
├── Custom physics simulations
├── Interactive 3D scenes
├── Particle systems
├── Sound design integration
├── Gamification elements
```

### Design Philosophy
```css
/* Hello Monday embraces bold experiments */
.hm-experimental {
  /* They're not afraid of: */
  mix-blend-mode: difference;
  cursor: none; /* Custom cursor always */
  
  /* Complex gradients */
  background: 
    radial-gradient(ellipse at 20% 80%, rgba(255,100,100,0.3) 0%, transparent 50%),
    radial-gradient(ellipse at 80% 20%, rgba(100,100,255,0.3) 0%, transparent 50%),
    linear-gradient(180deg, #0a0a0a, #1a1a2e);
}

/* Their type tends toward expressive */
.hm-display {
  font-family: 'Custom Variable Font', sans-serif;
  font-variation-settings: 'wght' 800, 'wdth' 125;
  font-size: clamp(4rem, 20vw, 20rem);
}
```

### Interactive Pattern
```javascript
// Hello Monday-style interactive element
class InteractiveScene {
  constructor() {
    this.mouse = { x: 0, y: 0 };
    this.targetMouse = { x: 0, y: 0 };
    this.lerp = 0.1;
    
    window.addEventListener('mousemove', this.onMouseMove.bind(this));
    this.animate();
  }
  
  onMouseMove(e) {
    this.targetMouse.x = (e.clientX / window.innerWidth) * 2 - 1;
    this.targetMouse.y = -(e.clientY / window.innerHeight) * 2 + 1;
  }
  
  animate() {
    // Smooth interpolation
    this.mouse.x += (this.targetMouse.x - this.mouse.x) * this.lerp;
    this.mouse.y += (this.targetMouse.y - this.mouse.y) * this.lerp;
    
    // Apply to 3D scene, particles, etc.
    requestAnimationFrame(this.animate.bind(this));
  }
}
```

---

## 5. Dogstudio (Belgium/Chicago)

**Signature: Emotional, immersive, story-driven**

### Technical Fingerprint
```
STACK
├── Custom solutions
├── WebGL for immersive experiences
├── GSAP animation
├── Video integration
└── Performance-optimized

SIGNATURE TECHNIQUES
├── Cinematic page transitions
├── Full-screen video backgrounds
├── Scroll-based storytelling
├── Sound + visual harmony
├── Cultural institution specialization
```

### Design Patterns
```css
/* Dogstudio immersive approach */
.ds-immersive-section {
  position: relative;
  height: 100vh;
  overflow: hidden;
}

.ds-video-bg {
  position: absolute;
  inset: 0;
  object-fit: cover;
  width: 100%;
  height: 100%;
}

.ds-content-overlay {
  position: relative;
  z-index: 1;
  display: flex;
  flex-direction: column;
  justify-content: flex-end;
  height: 100%;
  padding: 4rem;
  background: linear-gradient(
    to top,
    rgba(0,0,0,0.8) 0%,
    transparent 50%
  );
}

/* Their navigation is often minimal */
.ds-nav {
  position: fixed;
  top: 2rem;
  left: 2rem;
  right: 2rem;
  display: flex;
  justify-content: space-between;
  mix-blend-mode: difference;
  color: white;
  z-index: 100;
}
```

---

## 6. Tonik (Poland)

**Signature: Startup-focused, fast, modern**

### Technical Fingerprint
```
STACK
├── Webflow / Framer (no-code speed)
├── React for complex apps
├── Figma-first workflow
├── Rapid iteration
└── SaaS specialization

SIGNATURE TECHNIQUES
├── Bold gradient usage
├── 3D elements via Spline
├── Micro-animations everywhere
├── Dark mode preference
├── Tech startup aesthetic
```

### Design Patterns
```css
/* Tonik startup aesthetic */
:root {
  --tonik-bg: #0a0a0a;
  --tonik-surface: #141414;
  --tonik-border: rgba(255,255,255,0.1);
  --tonik-accent: linear-gradient(135deg, #6366f1, #8b5cf6);
}

.tonik-card {
  background: var(--tonik-surface);
  border: 1px solid var(--tonik-border);
  border-radius: 1rem;
  padding: 2rem;
  transition: all 0.3s ease;
}

.tonik-card:hover {
  border-color: rgba(99, 102, 241, 0.5);
  transform: translateY(-4px);
}

.tonik-gradient-text {
  background: var(--tonik-accent);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
}

/* Their button style */
.tonik-btn {
  background: var(--tonik-accent);
  color: white;
  padding: 1rem 2rem;
  border-radius: 9999px;
  font-weight: 500;
  transition: transform 0.2s, box-shadow 0.2s;
}

.tonik-btn:hover {
  transform: scale(1.02);
  box-shadow: 0 10px 40px rgba(99, 102, 241, 0.3);
}
```

---

## 7. Instrument (Portland)

**Signature: Brand-centric, polished, scalable**

### Technical Fingerprint
```
STACK
├── Enterprise frameworks
├── Design system focus
├── Accessibility-first
├── Performance optimized
└── Long-term maintenance

SIGNATURE TECHNIQUES
├── Brand system extension
├── Motion design language
├── Component-based design
├── Systematic spacing
├── Client brand preservation
```

### Design Philosophy
```css
/* Instrument systematic approach */
:root {
  /* They create extensive token systems */
  --space-1: 0.25rem;
  --space-2: 0.5rem;
  --space-3: 0.75rem;
  --space-4: 1rem;
  --space-5: 1.5rem;
  --space-6: 2rem;
  --space-7: 3rem;
  --space-8: 4rem;
  --space-9: 6rem;
  --space-10: 8rem;
  
  /* Typography scale */
  --font-size-xs: 0.75rem;
  --font-size-sm: 0.875rem;
  --font-size-md: 1rem;
  --font-size-lg: 1.125rem;
  --font-size-xl: 1.25rem;
  --font-size-2xl: 1.5rem;
  --font-size-3xl: 2rem;
  --font-size-4xl: 2.5rem;
  --font-size-5xl: 3rem;
}

/* Everything built from tokens */
.instrument-component {
  padding: var(--space-6);
  margin-bottom: var(--space-8);
  font-size: var(--font-size-md);
}
```

---

## 8. Active Theory (LA)

**Signature: Technical excellence, immersive WebGL**

### Technical Fingerprint
```
STACK
├── Custom WebGL frameworks
├── Three.js mastery
├── Shader programming
├── VR/AR capabilities
└── Maximum technical ambition

SIGNATURE TECHNIQUES
├── Full 3D environments
├── Custom shader effects
├── Real-time rendering
├── Interactive experiences
├── Sound reactive visuals
```

---

## 9. Common Patterns Across Elite Agencies

### Universal Techniques
```
TYPOGRAPHY
├── Custom/premium fonts (never system fonts)
├── Extreme scale contrast (10:1+ ratios)
├── Negative tracking on display type
├── Line-height varies by use case
└── Text animations on key headlines

ANIMATION
├── Custom easing (never linear, rarely ease)
├── Staggered reveals
├── Scroll-triggered sequences
├── Smooth scrolling (Lenis/Locomotive)
└── Page transitions

LAYOUT
├── 12-column base grid
├── Strategic grid breaking
├── Generous white space
├── Full-bleed imagery
└── Asymmetric compositions

COLOR
├── Limited palettes (2-3 colors max)
├── Bold accent usage
├── Dark mode capability
├── Contextual color shifts
└── Never pure black/white

INTERACTION
├── Custom cursors
├── Magnetic buttons
├── Hover state reveals
├── Micro-feedback
└── Sound design (optional)

PERFORMANCE
├── Optimized assets
├── Lazy loading
├── Code splitting
├── GPU acceleration
└── Core Web Vitals passing
```

### What They ALL Avoid
```
NEVER SEEN ON ELITE SITES
✗ Stock photography (unedited)
✗ Generic icons (Font Awesome default)
✗ System fonts
✗ Bootstrap/default components
✗ Lazy lorem ipsum
✗ Auto-generated layouts
✗ Cookie-cutter templates
✗ Generic loading spinners
✗ Aggressive pop-ups
✗ Cluttered footers
```
