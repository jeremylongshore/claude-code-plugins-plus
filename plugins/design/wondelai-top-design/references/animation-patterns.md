# Animation Patterns Reference

## Table of Contents
1. Easing Functions
2. Page Load Sequences
3. Scroll-Triggered Animations
4. Micro-Interactions
5. Page Transitions
6. Text Animations
7. Performance Optimization

---

## 1. Easing Functions

### CSS Custom Easings (Agency Standards)

```css
:root {
  /* Smooth exits - most common for UI */
  --ease-out-expo: cubic-bezier(0.16, 1, 0.3, 1);
  --ease-out-quart: cubic-bezier(0.25, 1, 0.5, 1);
  --ease-out-quint: cubic-bezier(0.22, 1, 0.36, 1);
  --ease-out-circ: cubic-bezier(0, 0.55, 0.45, 1);
  
  /* Dramatic entrances */
  --ease-in-expo: cubic-bezier(0.7, 0, 0.84, 0);
  --ease-in-quart: cubic-bezier(0.5, 0, 0.75, 0);
  
  /* Symmetric - for toggles, loops */
  --ease-in-out-quint: cubic-bezier(0.83, 0, 0.17, 1);
  --ease-in-out-expo: cubic-bezier(0.87, 0, 0.13, 1);
  
  /* Bouncy/Elastic */
  --ease-out-back: cubic-bezier(0.34, 1.56, 0.64, 1);
  --ease-out-elastic: cubic-bezier(0.68, -0.6, 0.32, 1.6);
  
  /* Duration standards */
  --duration-fast: 150ms;
  --duration-normal: 300ms;
  --duration-slow: 500ms;
  --duration-slower: 800ms;
  --duration-slowest: 1200ms;
}
```

### GSAP Equivalent

```javascript
// Common GSAP easings
gsap.to(element, {
  duration: 1,
  ease: "expo.out"      // Most used for reveals
});

gsap.to(element, {
  duration: 0.8,
  ease: "power4.out"    // Slightly faster settle
});

gsap.to(element, {
  duration: 1.2,
  ease: "power2.inOut"  // Symmetric movement
});

// Custom ease (Locomotive-style)
gsap.registerPlugin(CustomEase);
CustomEase.create("smooth", "0.16, 1, 0.3, 1");
```

---

## 2. Page Load Sequences

### Staggered Reveal Pattern

```css
/* CSS-only staggered reveal */
.reveal-item {
  opacity: 0;
  transform: translateY(60px);
  animation: revealUp 0.8s var(--ease-out-expo) forwards;
}

.reveal-item:nth-child(1) { animation-delay: 0.1s; }
.reveal-item:nth-child(2) { animation-delay: 0.2s; }
.reveal-item:nth-child(3) { animation-delay: 0.3s; }
.reveal-item:nth-child(4) { animation-delay: 0.4s; }

@keyframes revealUp {
  to {
    opacity: 1;
    transform: translateY(0);
  }
}
```

### GSAP Page Load

```javascript
// Orchestrated page load
const tl = gsap.timeline({ defaults: { ease: "expo.out" } });

tl.set(".page-content", { visibility: "visible" })
  .from(".hero-title .word", {
    y: 120,
    opacity: 0,
    duration: 1.2,
    stagger: 0.1
  })
  .from(".hero-subtitle", {
    y: 40,
    opacity: 0,
    duration: 0.8
  }, "-=0.6")
  .from(".hero-cta", {
    y: 30,
    opacity: 0,
    duration: 0.6
  }, "-=0.4")
  .from(".nav-item", {
    y: -20,
    opacity: 0,
    duration: 0.5,
    stagger: 0.05
  }, "-=0.8");
```

### Split Text Animation

```javascript
// Using GSAP SplitText or custom splitting
import { SplitText } from "gsap/SplitText";

const split = new SplitText(".hero-title", { 
  type: "words,chars",
  wordsClass: "word",
  charsClass: "char"
});

gsap.from(split.chars, {
  y: 100,
  opacity: 0,
  duration: 0.8,
  ease: "expo.out",
  stagger: 0.02
});

// CSS approach (manual splitting)
/* HTML: <span class="char">H</span><span class="char">e</span>... */
.char {
  display: inline-block;
  opacity: 0;
  transform: translateY(100%);
  animation: charReveal 0.6s var(--ease-out-expo) forwards;
}

.char:nth-child(1) { animation-delay: calc(0.03s * 1); }
.char:nth-child(2) { animation-delay: calc(0.03s * 2); }
/* ... generate with CSS custom properties or JS */
```

---

## 3. Scroll-Triggered Animations

### Intersection Observer (Vanilla)

```javascript
// Reusable scroll reveal
const observerOptions = {
  root: null,
  rootMargin: '0px 0px -100px 0px',
  threshold: 0.1
};

const revealOnScroll = (entries, observer) => {
  entries.forEach(entry => {
    if (entry.isIntersecting) {
      entry.target.classList.add('is-visible');
      observer.unobserve(entry.target);
    }
  });
};

const observer = new IntersectionObserver(revealOnScroll, observerOptions);

document.querySelectorAll('[data-reveal]').forEach(el => {
  observer.observe(el);
});
```

```css
/* Accompanying CSS */
[data-reveal] {
  opacity: 0;
  transform: translateY(60px);
  transition: opacity 0.8s var(--ease-out-expo),
              transform 0.8s var(--ease-out-expo);
}

[data-reveal].is-visible {
  opacity: 1;
  transform: translateY(0);
}

/* Stagger children */
[data-reveal="stagger"] > * {
  opacity: 0;
  transform: translateY(40px);
  transition: opacity 0.6s var(--ease-out-expo),
              transform 0.6s var(--ease-out-expo);
}

[data-reveal="stagger"].is-visible > *:nth-child(1) { transition-delay: 0.1s; }
[data-reveal="stagger"].is-visible > *:nth-child(2) { transition-delay: 0.2s; }
[data-reveal="stagger"].is-visible > *:nth-child(3) { transition-delay: 0.3s; }
[data-reveal="stagger"].is-visible > * {
  opacity: 1;
  transform: translateY(0);
}
```

### GSAP ScrollTrigger

```javascript
import { gsap } from "gsap";
import { ScrollTrigger } from "gsap/ScrollTrigger";

gsap.registerPlugin(ScrollTrigger);

// Fade up on scroll
gsap.utils.toArray('.reveal').forEach(el => {
  gsap.from(el, {
    y: 60,
    opacity: 0,
    duration: 1,
    ease: "expo.out",
    scrollTrigger: {
      trigger: el,
      start: "top 85%",
      toggleActions: "play none none none"
    }
  });
});

// Parallax effect
gsap.to('.parallax-bg', {
  yPercent: -30,
  ease: "none",
  scrollTrigger: {
    trigger: '.parallax-section',
    start: "top bottom",
    end: "bottom top",
    scrub: true
  }
});

// Horizontal scroll section
gsap.to('.horizontal-panels', {
  xPercent: -100 * (panels.length - 1),
  ease: "none",
  scrollTrigger: {
    trigger: '.horizontal-container',
    pin: true,
    scrub: 1,
    end: () => "+=" + document.querySelector('.horizontal-panels').offsetWidth
  }
});

// Pin and reveal
gsap.timeline({
  scrollTrigger: {
    trigger: '.pinned-section',
    start: "top top",
    end: "+=200%",
    pin: true,
    scrub: 1
  }
})
.from('.pinned-title', { opacity: 0, y: 100 })
.from('.pinned-content', { opacity: 0, y: 50 }, 0.3);
```

### Lenis Smooth Scroll + GSAP

```javascript
import Lenis from '@studio-freight/lenis';
import { gsap } from 'gsap';
import { ScrollTrigger } from 'gsap/ScrollTrigger';

// Initialize Lenis
const lenis = new Lenis({
  duration: 1.2,
  easing: (t) => Math.min(1, 1.001 - Math.pow(2, -10 * t)),
  direction: 'vertical',
  smooth: true,
});

// Connect Lenis to GSAP ScrollTrigger
lenis.on('scroll', ScrollTrigger.update);

gsap.ticker.add((time) => {
  lenis.raf(time * 1000);
});

gsap.ticker.lagSmoothing(0);
```

---

## 4. Micro-Interactions

### Button Hover States

```css
/* Magnetic button effect */
.magnetic-btn {
  position: relative;
  transition: transform 0.3s var(--ease-out-expo);
}

/* JS handles the magnetic effect, CSS handles the visual */
.magnetic-btn::before {
  content: '';
  position: absolute;
  inset: 0;
  background: var(--color-accent);
  transform: scaleX(0);
  transform-origin: right;
  transition: transform 0.5s var(--ease-out-expo);
}

.magnetic-btn:hover::before {
  transform: scaleX(1);
  transform-origin: left;
}

/* Text slide effect */
.text-slide-btn {
  overflow: hidden;
  position: relative;
}

.text-slide-btn span {
  display: block;
  transition: transform 0.5s var(--ease-out-expo);
}

.text-slide-btn span::after {
  content: attr(data-text);
  position: absolute;
  top: 100%;
  left: 0;
}

.text-slide-btn:hover span {
  transform: translateY(-100%);
}
```

```javascript
// Magnetic button JS
document.querySelectorAll('.magnetic-btn').forEach(btn => {
  btn.addEventListener('mousemove', (e) => {
    const rect = btn.getBoundingClientRect();
    const x = e.clientX - rect.left - rect.width / 2;
    const y = e.clientY - rect.top - rect.height / 2;
    
    gsap.to(btn, {
      x: x * 0.3,
      y: y * 0.3,
      duration: 0.3,
      ease: "power2.out"
    });
  });
  
  btn.addEventListener('mouseleave', () => {
    gsap.to(btn, {
      x: 0,
      y: 0,
      duration: 0.5,
      ease: "elastic.out(1, 0.5)"
    });
  });
});
```

### Link Underline Animations

```css
/* Slide in underline */
.link-underline {
  position: relative;
}

.link-underline::after {
  content: '';
  position: absolute;
  bottom: 0;
  left: 0;
  width: 100%;
  height: 1px;
  background: currentColor;
  transform: scaleX(0);
  transform-origin: right;
  transition: transform 0.4s var(--ease-out-expo);
}

.link-underline:hover::after {
  transform: scaleX(1);
  transform-origin: left;
}

/* Draw underline */
.link-draw {
  background-image: linear-gradient(currentColor, currentColor);
  background-position: 0 100%;
  background-repeat: no-repeat;
  background-size: 0% 1px;
  transition: background-size 0.4s var(--ease-out-expo);
}

.link-draw:hover {
  background-size: 100% 1px;
}
```

### Card Hover Effects

```css
/* 3D tilt card */
.tilt-card {
  transform-style: preserve-3d;
  transition: transform 0.5s var(--ease-out-expo);
}

.tilt-card:hover {
  transform: perspective(1000px) rotateX(5deg) rotateY(-5deg);
}

.tilt-card::before {
  content: '';
  position: absolute;
  inset: 0;
  background: linear-gradient(
    135deg,
    rgba(255,255,255,0.1) 0%,
    transparent 50%
  );
  opacity: 0;
  transition: opacity 0.3s;
}

.tilt-card:hover::before {
  opacity: 1;
}
```

---

## 5. Page Transitions

### Basic Fade Transition

```javascript
// Using Barba.js
import barba from '@barba/core';

barba.init({
  transitions: [{
    name: 'fade',
    leave(data) {
      return gsap.to(data.current.container, {
        opacity: 0,
        duration: 0.5,
        ease: "power2.inOut"
      });
    },
    enter(data) {
      return gsap.from(data.next.container, {
        opacity: 0,
        duration: 0.5,
        ease: "power2.inOut"
      });
    }
  }]
});
```

### Overlay Wipe Transition

```javascript
// Wipe transition with overlay
barba.init({
  transitions: [{
    name: 'wipe',
    leave(data) {
      const tl = gsap.timeline();
      
      tl.to('.transition-overlay', {
        scaleY: 1,
        transformOrigin: 'bottom',
        duration: 0.6,
        ease: "expo.inOut"
      })
      .to(data.current.container, {
        opacity: 0,
        duration: 0.3
      }, 0.3);
      
      return tl;
    },
    enter(data) {
      const tl = gsap.timeline();
      
      tl.set(data.next.container, { opacity: 1 })
        .to('.transition-overlay', {
          scaleY: 0,
          transformOrigin: 'top',
          duration: 0.6,
          ease: "expo.inOut"
        })
        .from('[data-reveal]', {
          y: 60,
          opacity: 0,
          stagger: 0.1,
          duration: 0.8,
          ease: "expo.out"
        }, 0.2);
      
      return tl;
    }
  }]
});
```

---

## 6. Text Animations

### Word-by-Word Reveal

```javascript
// Split and animate
function animateText(element) {
  const text = element.textContent;
  const words = text.split(' ');
  
  element.innerHTML = words.map(word => 
    `<span class="word-wrapper"><span class="word">${word}</span></span>`
  ).join(' ');
  
  gsap.from(element.querySelectorAll('.word'), {
    y: '100%',
    duration: 0.8,
    ease: "expo.out",
    stagger: 0.05
  });
}
```

### Scramble/Decode Effect

```javascript
// Text scramble effect
class TextScramble {
  constructor(el) {
    this.el = el;
    this.chars = '!<>-_\\/[]{}—=+*^?#________';
    this.update = this.update.bind(this);
  }
  
  setText(newText) {
    const oldText = this.el.innerText;
    const length = Math.max(oldText.length, newText.length);
    const promise = new Promise(resolve => this.resolve = resolve);
    this.queue = [];
    
    for (let i = 0; i < length; i++) {
      const from = oldText[i] || '';
      const to = newText[i] || '';
      const start = Math.floor(Math.random() * 40);
      const end = start + Math.floor(Math.random() * 40);
      this.queue.push({ from, to, start, end });
    }
    
    cancelAnimationFrame(this.frameRequest);
    this.frame = 0;
    this.update();
    return promise;
  }
  
  update() {
    let output = '';
    let complete = 0;
    
    for (let i = 0; i < this.queue.length; i++) {
      let { from, to, start, end, char } = this.queue[i];
      
      if (this.frame >= end) {
        complete++;
        output += to;
      } else if (this.frame >= start) {
        if (!char || Math.random() < 0.28) {
          char = this.chars[Math.floor(Math.random() * this.chars.length)];
          this.queue[i].char = char;
        }
        output += char;
      } else {
        output += from;
      }
    }
    
    this.el.innerText = output;
    
    if (complete === this.queue.length) {
      this.resolve();
    } else {
      this.frameRequest = requestAnimationFrame(this.update);
      this.frame++;
    }
  }
}
```

---

## 7. Performance Optimization

### GPU-Accelerated Properties

```css
/* ONLY animate these for 60fps */
.performant-animation {
  /* Good - GPU accelerated */
  transform: translateX(100px);
  transform: translateY(100px);
  transform: scale(1.2);
  transform: rotate(45deg);
  opacity: 0.5;
  
  /* Bad - triggers layout/paint */
  /* left: 100px; */
  /* top: 100px; */
  /* width: 200px; */
  /* height: 200px; */
  /* margin: 20px; */
  /* padding: 20px; */
}

/* Force GPU layer */
.will-animate {
  will-change: transform, opacity;
  transform: translateZ(0);
}

/* Remove will-change after animation */
.animation-complete {
  will-change: auto;
}
```

### Reduce Motion Support

```css
@media (prefers-reduced-motion: reduce) {
  *,
  *::before,
  *::after {
    animation-duration: 0.01ms !important;
    animation-iteration-count: 1 !important;
    transition-duration: 0.01ms !important;
    scroll-behavior: auto !important;
  }
}
```

```javascript
// JS check for reduced motion
const prefersReducedMotion = window.matchMedia('(prefers-reduced-motion: reduce)');

if (prefersReducedMotion.matches) {
  // Skip or simplify animations
  gsap.globalTimeline.timeScale(10); // Or skip entirely
}
```

### Lazy Animation Loading

```javascript
// Only initialize animations when needed
const animationObserver = new IntersectionObserver((entries) => {
  entries.forEach(entry => {
    if (entry.isIntersecting) {
      initHeavyAnimation(entry.target);
      animationObserver.unobserve(entry.target);
    }
  });
}, { rootMargin: '200px' });

document.querySelectorAll('[data-heavy-animation]').forEach(el => {
  animationObserver.observe(el);
});
```
