---
title: "IntentCAD Viewer — Closing the DWG FastView Gap"
description: "Web workers, animated zoom, progress feedback, and color-coded selections. The changes that took IntentCAD's browser viewer from prototype to production-grade — benchmarked against DWG FastView."
date: "2026-03-28"
tags: ["react", "web-development", "architecture", "testing", "python"]
featured: false
---
DWG FastView is the benchmark. It's the viewer AEC professionals already use. It loads fast, zooms smooth, and never locks the UI on a 50MB drawing. If your browser-based CAD viewer doesn't match that bar, nobody will trust it with real work.

IntentCAD's viewer wasn't there yet. It worked. But "works" and "feels right" are different categories. The drawing would freeze for a few seconds on load. Zoom was instant — which sounds good until you realize instant zoom with no interpolation is disorienting. And when you selected three entities, they all turned the same shade of blue. Good luck telling them apart.

Two PRs this week fixed all of it.

## The Main Thread Problem

The dxf-viewer library does everything on the main thread by default. Font loading, fetching, DXF parsing, geometry preparation — all of it blocks the UI. On a small test drawing, you don't notice. On a real architectural floor plan, you get 2-4 seconds of frozen interface.

The fix is three lines in a web worker file:

```javascript
// web/frontend/src/workers/dxf-viewer-worker.js
import { DxfViewer } from 'dxf-viewer';
DxfViewer.SetupWorker();
```

Three lines. The library already supports worker-based parsing — it just needs a worker file and a factory function. The viewer component passes both:

```javascript
const workerFactory = () =>
  new Worker(new URL('../workers/dxf-viewer-worker.js', import.meta.url), { type: 'module' });
```

Now DXF parsing runs off the main thread. The UI stays responsive during load. No freezing.

## Progress Feedback

A responsive UI during load is necessary but not sufficient. The user still needs to know something is happening. DWG FastView shows a progress bar. We need one too.

The dxf-viewer library exposes a `progressCbk` callback with phase labels and byte counts:

```javascript
const progressCbk = (phase, processedSize, totalSize) => {
  const labels = { font: 'Loading fonts', fetch: 'Downloading', parse: 'Parsing', prepare: 'Preparing' };
  setLoadPhase(labels[phase] || phase);
  if (phase === 'fetch' && totalSize > 0) {
    setLoadProgress(Math.round((processedSize / totalSize) * 100));
  } else if (phase === 'prepare') {
    setLoadProgress(90);
  }
};
```

Four phases, human-readable labels, a 4px progress bar with smooth CSS transitions. The user sees "Downloading... 34%" instead of a blank canvas.

## Animated Zoom

The old zoom behavior: click the + button, camera jumps to 1.3x. Instant. No interpolation.

The problem is spatial orientation. When the view changes instantly, your brain has to re-locate where you are in the drawing. FastView animates its zoom. Every professional CAD viewer animates its zoom. There's a reason.

The replacement uses requestAnimationFrame with an ease-out cubic curve:

```javascript
const animateZoom = useCallback((targetZoom) => {
  const startZoom = cam.zoom;
  const startTime = performance.now();
  const duration = 200;
  const step = (now) => {
    const t = Math.min((now - startTime) / duration, 1);
    const ease = 1 - (1 - t) ** 3; // ease-out cubic
    cam.zoom = startZoom + (targetZoom - startZoom) * ease;
    cam.updateProjectionMatrix();
    viewer.Render();
    if (t < 1) requestAnimationFrame(step);
  };
  requestAnimationFrame(step);
}, []);
```

200ms. Fast enough to not feel sluggish, slow enough for the eye to track the transition. The cubic ease-out decelerates at the end — the zoom settles rather than stopping dead.

## Color-Cycling Selections

When you select multiple entities in the viewer, you need to distinguish them visually. The old behavior gave every selection the same blue highlight. Select five entities and you get five blue outlines with no way to match them to their entries in the operations panel.

The fix is a six-color palette applied by index: blue, emerald, amber, purple, pink, cyan. Each selected entity gets its own color in both the viewer overlay and the entity tag in the sidebar. Selection #1 is blue, #2 is emerald, #3 is amber, and so on.

Six colors is intentional. You rarely select more than six entities at once, and the palette cycles if you do. The colors are chosen for contrast on both dark backgrounds (the viewer canvas) and light backgrounds (the operations panel).

## Click-to-Focus Operations

The operations panel lists planned changes. "Move HVAC-UNIT-01 to (240, 180)." Useful, but which entity is HVAC-UNIT-01? On a dense drawing, good luck finding it.

Now each operation row is clickable. The backend adds `bounds` to each operation via a new `_op_bounds()` helper that looks up the target entity's bounding box. The frontend calls `focusOnBounds()` to pan and zoom the viewer to the target entity with a highlight ring.

Click an operation. The viewer flies to it. Simple interaction, large usability gain.

## The Small Stuff

Two things that don't warrant their own section but matter:

**Accessibility fix.** Operation checkboxes had been changed from `<label>` to `<div>` elements. Screen readers couldn't associate the checkbox with its text. Restored proper `<label>` elements.

**CI hygiene.** Ruff flagged a SIM103 simplification lint. Fixed. Pygments has an unpatched CVE-2026-4539 — we don't use Pygments in production, so added an ignore rule rather than blocking CI on a dev-only dependency with no upstream fix.

## Dependabot Housekeeping

The google-adk bump from 1.18.0 to 1.28.0 arrived via Dependabot as PR #131. It branched before the lint and CVE fixes landed, so CI was red. Merged main into the dependabot branch, CI went green, squash-merged. Routine dependency maintenance.

## The Gap Is Closing

FastView is still the reference. It has years of optimization behind it. But the gap is now about edge cases and scale, not fundamentals. IntentCAD's viewer loads off the main thread, shows progress, animates transitions, and gives you color-coded multi-selection. That's the baseline for a professional CAD viewer in the browser.

Two PRs. About 15 files changed. 614 insertions. The viewer went from "demo-quality" to "production-ready."

---

### Related Posts

- [IntentCAD: Entity Selection + Diff Detection UX](/posts/intentcad-entity-selection-diff-detection-ux) — the PR that built the selection system this work extends
- [IntentCAD: Pascal Editor, Cached Index & Tool Narrowing](/posts/intentcad-pascal-editor-cached-index-tool-narrowing) — performance work on the backend that pairs with these frontend improvements
- [Write Once, Publish Everywhere — Content Distribution Infra](/posts/write-once-publish-everywhere-content-distribution-infra) — the pipeline that publishes these posts
