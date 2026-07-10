# Motion protocol

The shared motion-engineering step the [`motion`](../../agents/motion.md) agent invokes when designing or reviewing how
elements move. Motion is an **engineering discipline, not decoration** — it must communicate state, hold a frame
budget, respect physics, degrade for reduced-motion, and stay inside the design system's motion language.

This file is the **single source of truth** for the motion rules. The `motion` charter references it by one line and
never restates it. It binds — it does not duplicate — the `ui` persona ([`personas-A.md`](personas-A.md)) and the
`performance` persona ([`personas-B.md`](personas-B.md)). Deep creative-motion patterns live in the local taste skills
indexed in [`design-system.md`](design-system.md), not here.

## Motion respects the system first

Read `.hyperflow/design/system.md` → **Motion language** before animating anything. Every easing curve, duration, and
spring traces to that section. **Extend** the Motion language when a new pattern is needed — never invent a one-off
off-system motion. The design system owns the vocabulary; this protocol owns the engineering.

## 60 fps performance floor

The budget is **60 fps** (≈16 ms/frame). Stay on the compositor:

- **Animate only `transform` and `opacity`** — the two properties that skip layout and paint. Use `translate()` /
  `rotate()` / `scale()` for movement and sizing.
- **Never animate layout properties** — `width`, `height`, `top`, `left`, `margin`, `padding` trigger layout
  thrashing (geometry recalculated every frame). Remap expensive geometry changes to transforms via **FLIP** (First /
  Last / Invert / Play).
- **`will-change` is a scalpel, not a default** — apply only after profiling identifies a bottleneck, to few elements;
  overuse starves resources and slows the page.
- **`content-visibility: auto`** on off-screen/chunked subtrees skips their layout+paint (Baseline since 2025-09).
- **No `requestAnimationFrame` polling loops** — they block the main thread and miss compositor updates. Prefer native
  scroll-driven CSS, `IntersectionObserver`, or the library's own ticker.
- **Measure, don't guess** — Chrome DevTools "Frame Rendering Stats", and Percent Dropped Frames (95th percentile over
  1-second windows) rather than a raw FPS counter. "It feels smooth" is not a benchmark (the `performance` persona's
  measure-first rule).

## Library decision matrix

Pick the lightest tool that fits — state the choice, never default to the heaviest.

| Tool | Use when |
|---|---|
| CSS transitions / animations | simple state changes (hover, load, toggle); the reduced-motion-friendliest baseline |
| Web Animations API (WAAPI) | programmatic control over dynamic tweens without a library; low-level foundation |
| Native CSS scroll-driven (`animation-timeline`, `scroll()`, `view()`) | scroll-linked reveals/parallax/progress — Baseline 2025, compositor-friendly, no main-thread listener |
| **GSAP** (now 100% free, all plugins incl. ScrollTrigger / SplitText / MorphSVG) | complex orchestrated sequences, SVG morphing, scroll choreography, drag |
| **Motion for React** (ex-Framer Motion, MIT; hybrid WAAPI engine) | declarative React production animation; gesture + layout animations |
| **Reanimated** | native mobile (React Native) — animations on the UI thread, gesture-driven |

## Physics defaults

- **Springs beat fixed cubic-bezier** when motion reacts to interruption or gesture — a spring computes velocity
  on-the-fly and stays natural when a user drags past the endpoint; a bezier is a fixed curve.
- **Default spring** ≈ `stiffness 100 · damping 10 · mass 1`. Gentler: `stiffness 50 · damping 20`. Or the modern
  two-parameter approach: **bounce** (0–1) + **perceptual duration** (ms).
- **Keep interaction durations < 500 ms** — 300–400 ms reads as snappy; longer feels unresponsive and invites
  mid-motion interruption. Springs self-adapt their duration.

## Accessibility (non-negotiable)

The `ui` persona's `prefers-reduced-motion` rule binds here unchanged and is a hard floor (defer to
[`accessibility-reviewer`](../../agents/accessibility-reviewer.md) on any conflict):

- **Dual-media pattern** — gate decorative motion behind `@media (prefers-reduced-motion: no-preference)`; provide a
  static/instant fallback under `@media (prefers-reduced-motion: reduce)`.
- **Disable decorative motion** (parallax, auto-reveal, attention-grabbing transitions); **keep functional feedback**
  (action-received confirms, focus transitions) — those carry information.
- **WCAG 2.3.3 (Animation from Interactions)** — interaction-triggered motion (scaling/panning large objects) must be
  disable-able unless essential; large movement triggers vestibular discomfort.
- **Runtime** — a `matchMedia('(prefers-reduced-motion: reduce)')` listener stops/adjusts JS animations when the
  preference changes mid-session.

## Scroll-driven & orchestration

- Prefer **native CSS scroll-driven animations** over main-thread scroll listeners — they run on the compositor.
- For orchestrated scroll work, **GSAP `ScrollTrigger`** with timelines; `ScrollTrigger.batch()` to stagger
  initialization across many elements.
- **Stagger with discipline** — macro (a wave across a group) plus optional micro (small variance within it). Stagger
  communicates hierarchy and reading order; it is not confetti.

## Anti-slop motion floor

- **Motion must communicate** state, hierarchy, or continuity — never exist because "it looked cool" (the `ui`
  persona's motion rule).
- No **gratuitous parallax** (repaints + vestibular cost), no **everything-animates** (cognitive overload, cheap
  feel), no **layout-property animation** (jank), no **over-long durations**, no **`will-change` spam**.

## Output discipline

Motion specs and the Motion-language section are **files** under `.hyperflow/` (rule 8, file-first). Research output is
a short cited brief ([`web-research.md`](web-research.md) token discipline) ending in `Sources consulted:` when
research ran. Every library/best-practice claim cites a current source — uncited is a doctrine violation.

## Sources consulted (seed — refresh on each gated run)

- Stick to Compositor-Only Properties and Manage Layer Count — https://web.dev/articles/stick-to-compositor-only-properties-and-manage-layer-count
- High-Performance CSS Animations — https://web.dev/articles/animations-guide
- `will-change` — https://developer.mozilla.org/en-US/docs/Web/CSS/will-change
- `content-visibility` is now Baseline — https://web.dev/blog/css-content-visibility-baseline (2025-09)
- Towards an Animation Smoothness Metric (Percent Dropped Frames) — https://web.dev/articles/smoothness
- Animation performance and frame rate — https://developer.mozilla.org/en-US/docs/Web/Performance/Guides/Animation_performance_and_frame_rate
- CSS Scroll-Driven Animations — https://developer.mozilla.org/en-US/docs/Web/CSS/Guides/Scroll-driven_animations
- GSAP is now 100% free — https://webflow.com/blog/gsap-becomes-free (2024)
- Motion (JavaScript & React animation library) — https://motion.dev/
- Web Animations API — https://developer.mozilla.org/en-US/docs/Web/API/Web_Animations_API
- A Friendly Introduction to Spring Physics — https://www.joshwcomeau.com/animation/a-friendly-introduction-to-spring-physics/
- prefers-reduced-motion — https://web.dev/prefers-reduced-motion/
- Understanding SC 2.3.3: Animation from Interactions — https://www.w3.org/WAI/WCAG22/Understanding/animation-from-interactions.html
