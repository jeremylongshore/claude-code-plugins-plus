# Technical Stack Reference

## Table of Contents
1. Core Technologies
2. Animation Libraries
3. Smooth Scrolling Solutions
4. 3D & WebGL
5. Build Tools & Frameworks
6. Performance Optimization
7. Deployment & Hosting

---

## 1. Core Technologies

### CSS Approach

```
METHODOLOGY
├── CSS Custom Properties (required)
├── Modern CSS (container queries, :has(), etc.)
├── Utility-first OR Component-based (not mixed)
└── PostCSS for processing (autoprefixer, nesting)

RECOMMENDED STACK
├── Plain CSS with custom properties
├── Tailwind CSS (for rapid prototyping)
├── CSS Modules (for React/Vue scoping)
└── Vanilla Extract (for type-safe CSS-in-JS)
```

### JavaScript Standards

```javascript
// Modern JS features to use freely
const features = {
  modules: true,                    // ES Modules
  asyncAwait: true,                 // Async/await
  optionalChaining: true,           // obj?.prop
  nullishCoalescing: true,          // value ?? default
  destructuring: true,              // const { a, b } = obj
  spreadOperator: true,             // [...arr, newItem]
  templateLiterals: true,           // `${var}`
  arrowFunctions: true,             // () => {}
};

// Avoid
const avoid = {
  var: true,                        // Use const/let
  callbacks: 'Use promises/async',
  jquery: 'Use native APIs',
};
```

---

## 2. Animation Libraries

### GSAP (GreenSock)

```
THE INDUSTRY STANDARD
├── Power: Most capable animation library
├── Performance: Optimized for 60fps
├── Ecosystem: ScrollTrigger, SplitText, MorphSVG
└── License: Free for most uses, paid for some plugins

INSTALLATION
npm install gsap

CORE PLUGINS (free)
├── ScrollTrigger - scroll-based animations
├── Observer - scroll/touch/pointer tracking
├── Draggable - drag interactions
└── MotionPath - animate along SVG paths

CLUB PLUGINS (paid)
├── SplitText - text splitting for animation
├── MorphSVG - shape morphing
├── DrawSVG - line drawing effects
├── ScrollSmoother - smooth scroll + ScrollTrigger
└── Flip - layout animations
```

```javascript
// GSAP initialization pattern
import { gsap } from "gsap";
import { ScrollTrigger } from "gsap/ScrollTrigger";

gsap.registerPlugin(ScrollTrigger);

// Set defaults
gsap.defaults({
  ease: "expo.out",
  duration: 1
});

// Basic animation
gsap.to(".element", {
  x: 100,
  opacity: 1,
  duration: 0.8
});

// Timeline
const tl = gsap.timeline();
tl.to(".first", { x: 100 })
  .to(".second", { x: 100 }, "-=0.5") // overlap
  .to(".third", { x: 100 }, "+=0.2"); // gap
```

### Motion (Framer Motion)

```
REACT-SPECIFIC
├── Declarative API
├── Layout animations
├── Gesture support
├── Exit animations
└── Server-side rendering support

INSTALLATION
npm install motion
```

```jsx
// Motion usage
import { motion, AnimatePresence } from "motion/react";

// Basic animation
<motion.div
  initial={{ opacity: 0, y: 20 }}
  animate={{ opacity: 1, y: 0 }}
  exit={{ opacity: 0 }}
  transition={{ duration: 0.6, ease: [0.16, 1, 0.3, 1] }}
>
  Content
</motion.div>

// Scroll-triggered
<motion.div
  initial={{ opacity: 0 }}
  whileInView={{ opacity: 1 }}
  viewport={{ once: true, margin: "-100px" }}
>
  Reveals on scroll
</motion.div>

// Layout animation
<motion.div layout>
  {/* Animates when layout changes */}
</motion.div>
```

### Anime.js

```
LIGHTWEIGHT ALTERNATIVE
├── Size: ~17KB minified
├── SVG morphing included
├── Timeline support
└── Good for simpler projects

INSTALLATION
npm install animejs
```

```javascript
import anime from 'animejs';

anime({
  targets: '.element',
  translateX: 250,
  rotate: '1turn',
  duration: 800,
  easing: 'easeOutExpo'
});

// Stagger
anime({
  targets: '.grid-item',
  translateY: [50, 0],
  opacity: [0, 1],
  delay: anime.stagger(100)
});
```

---

## 3. Smooth Scrolling Solutions

### Lenis (Recommended)

```
MODERN & LIGHTWEIGHT
├── Size: ~4KB gzipped
├── Native scroll (accessibility preserved)
├── GSAP integration
├── Performant
└── Actively maintained by Studio Freight

INSTALLATION
npm install lenis
```

```javascript
import Lenis from 'lenis';

const lenis = new Lenis({
  duration: 1.2,
  easing: (t) => Math.min(1, 1.001 - Math.pow(2, -10 * t)),
  orientation: 'vertical',
  gestureOrientation: 'vertical',
  smoothWheel: true,
  wheelMultiplier: 1,
  touchMultiplier: 2,
  infinite: false,
});

function raf(time) {
  lenis.raf(time);
  requestAnimationFrame(raf);
}

requestAnimationFrame(raf);

// GSAP integration
import { gsap } from 'gsap';
import { ScrollTrigger } from 'gsap/ScrollTrigger';

lenis.on('scroll', ScrollTrigger.update);

gsap.ticker.add((time) => {
  lenis.raf(time * 1000);
});

gsap.ticker.lagSmoothing(0);
```

### Locomotive Scroll

```
FEATURE-RICH
├── Smooth scrolling
├── Parallax effects built-in
├── Data attributes for quick setup
├── Horizontal scroll support
└── Heavier than Lenis

INSTALLATION
npm install locomotive-scroll
```

```javascript
import LocomotiveScroll from 'locomotive-scroll';

const scroll = new LocomotiveScroll({
  el: document.querySelector('[data-scroll-container]'),
  smooth: true,
  multiplier: 1,
  lerp: 0.1
});

// Data attribute usage
// <div data-scroll data-scroll-speed="2">Parallax element</div>
```

---

## 4. 3D & WebGL

### Three.js

```
FULL 3D CAPABILITY
├── Complete 3D engine
├── Large ecosystem
├── Extensive documentation
└── Performance-intensive

INSTALLATION
npm install three
```

```javascript
import * as THREE from 'three';

// Basic scene setup
const scene = new THREE.Scene();
const camera = new THREE.PerspectiveCamera(75, window.innerWidth / window.innerHeight, 0.1, 1000);
const renderer = new THREE.WebGLRenderer({ antialias: true, alpha: true });

renderer.setSize(window.innerWidth, window.innerHeight);
renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2));
document.body.appendChild(renderer.domElement);

// Animation loop
function animate() {
  requestAnimationFrame(animate);
  renderer.render(scene, camera);
}
animate();
```

### React Three Fiber

```
THREE.JS FOR REACT
├── Declarative Three.js
├── React ecosystem integration
├── Easier state management
└── Drei helpers library

INSTALLATION
npm install @react-three/fiber @react-three/drei
```

```jsx
import { Canvas } from '@react-three/fiber';
import { OrbitControls, Environment } from '@react-three/drei';

function Scene() {
  return (
    <Canvas>
      <ambientLight intensity={0.5} />
      <mesh>
        <boxGeometry />
        <meshStandardMaterial color="orange" />
      </mesh>
      <OrbitControls />
      <Environment preset="city" />
    </Canvas>
  );
}
```

### OGL

```
LIGHTWEIGHT WEBGL
├── Size: ~30KB
├── Lower-level than Three.js
├── Better for simple effects
└── Less overhead

INSTALLATION
npm install ogl
```

---

## 5. Build Tools & Frameworks

### Vite (Recommended for Simple Sites)

```
FAST BUILD TOOL
├── Instant dev server
├── Native ES modules
├── Optimized production builds
└── Framework agnostic

SETUP
npm create vite@latest
```

### Next.js (React Apps)

```
REACT FRAMEWORK
├── Server-side rendering
├── Static site generation
├── API routes
├── Image optimization
└── File-based routing

SETUP
npx create-next-app@latest
```

### Astro (Content Sites)

```
CONTENT-FOCUSED
├── Zero JS by default
├── Partial hydration
├── Any framework components
├── Excellent performance
└── Great for portfolios/marketing

SETUP
npm create astro@latest
```

### Nuxt (Vue Apps)

```
VUE FRAMEWORK
├── SSR/SSG
├── Auto-imports
├── File-based routing
└── Excellent DX

SETUP
npx nuxi@latest init
```

---

## 6. Performance Optimization

### Image Optimization

```
FORMATS
├── WebP: Primary format, 25-35% smaller than JPEG
├── AVIF: Best compression, growing support
├── SVG: Icons, logos, illustrations
└── JPEG/PNG: Fallbacks only

TOOLS
├── Sharp (Node.js): npm install sharp
├── Squoosh: squoosh.app (browser-based)
├── ImageOptim: Desktop app (Mac)
└── SVGO: SVG optimization

RESPONSIVE IMAGES
<picture>
  <source srcset="image.avif" type="image/avif">
  <source srcset="image.webp" type="image/webp">
  <img src="image.jpg" alt="Description" loading="lazy">
</picture>

SRCSET FOR RESOLUTION
<img 
  srcset="image-400.webp 400w, image-800.webp 800w, image-1200.webp 1200w"
  sizes="(max-width: 600px) 400px, (max-width: 1200px) 800px, 1200px"
  src="image-800.webp"
  alt="Description"
  loading="lazy"
>
```

### Font Optimization

```html
<!-- Preload critical fonts -->
<link rel="preload" href="/fonts/display.woff2" as="font" type="font/woff2" crossorigin>

<!-- Font-display strategy -->
<style>
@font-face {
  font-family: 'Display';
  src: url('/fonts/display.woff2') format('woff2');
  font-display: swap; /* or optional for non-critical */
  unicode-range: U+0000-00FF; /* Subset to Latin */
}
</style>
```

### Code Splitting

```javascript
// Dynamic imports
const HeavyComponent = lazy(() => import('./HeavyComponent'));

// Route-based splitting (Next.js automatic)
// Each page is a separate chunk

// Manual chunk with Vite
// vite.config.js
export default {
  build: {
    rollupOptions: {
      output: {
        manualChunks: {
          vendor: ['gsap', 'three'],
        },
      },
    },
  },
};
```

### Critical CSS

```javascript
// Extract critical CSS with Critters (Vite plugin)
// npm install critters
import critters from 'critters';

// Or inline critical styles manually
<style>
  /* Above-the-fold styles inlined */
</style>
<link rel="preload" href="/styles.css" as="style" onload="this.rel='stylesheet'">
```

---

## 7. Deployment & Hosting

### Recommended Platforms

```
STATIC SITES
├── Vercel: Best for Next.js, excellent DX
├── Netlify: Great for Jamstack, easy deploys
├── Cloudflare Pages: Fast edge network
└── GitHub Pages: Free, simple static hosting

FULL-STACK
├── Vercel: Serverless functions, edge middleware
├── Railway: Containers, databases
├── Render: Full infrastructure
└── AWS Amplify: AWS ecosystem

CDN FOR ASSETS
├── Cloudflare: Free tier, global
├── AWS CloudFront: Enterprise scale
├── Bunny CDN: Cost-effective, fast
└── Imgix/Cloudinary: Image-specific CDN
```

### Performance Checklist

```
PRE-LAUNCH
□ Images optimized (WebP/AVIF, lazy loaded)
□ Fonts subset and preloaded
□ CSS/JS minified and compressed
□ Gzip/Brotli compression enabled
□ HTTP/2 or HTTP/3 enabled
□ Cache headers configured
□ Critical CSS inlined
□ Unused CSS/JS removed

MONITORING
□ Lighthouse CI in deployment
□ Core Web Vitals tracking
□ Real User Monitoring (RUM)
□ Error tracking (Sentry, etc.)
```
