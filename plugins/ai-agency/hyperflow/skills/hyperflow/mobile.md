# Mobile standards

The standards the [`mobile`](../../agents/mobile.md) agent binds by reference — framework selection, app
architecture, the accessibility floor, the device-size test matrix, and on-device performance budgets. Extend the
relevant section rather than inventing one-off rules; every best-practice claim must cite a current source from the
agent's web-research step (frameworks and tooling move fast — an uncited claim is a guess).

## Platform / framework matrix — pick, don't default

| Target | Use when | Current (2026) notes |
|---|---|---|
| **React Native** | Strong JS/TS team; web↔mobile code/skill sharing; standard CRUD + moderate motion | **New Architecture** (Fabric renderer, TurboModules, JSI) is production-ready and **mandatory ≥ 0.82**; legacy bridge is gone |
| **Flutter** | Visual consistency / custom design across platforms; animation-heavy UI | **Impeller** renderer (replaced Skia, 120fps-capable), Dart WASM; Material + Cupertino widget parity |
| **Native iOS** | Max performance, deep platform integration (AR, real-time graphics), platform-first feel | Swift / **SwiftUI**; follow Apple **HIG** |
| **Native Android** | Same, Android side | Kotlin / **Jetpack Compose**; lifecycle-aware `ViewModel`/state; follow **Material** |
| **Responsive mobile web** | Reach without install; content-first | PWA where offline/install matters; same a11y + touch-target floor applies |

State the choice against the app's actual needs (team skills, performance ceiling, design-consistency vs
platform-native feel, budget/time). Native only when a cross-platform framework genuinely can't meet the bar.

## App architecture

- **Navigation graph** defined up front (stack/tab/drawer, deep links, back-button semantics on Android).
- **Offline-first** where the feature implies connectivity gaps: on-device store as the source of truth, optimistic
  UI that responds without waiting on the server, and a sync/conflict strategy. The UI never blocks on the network.
- **Lifecycle-aware state** (e.g. Android `ViewModel`/state holders, RN app-state listeners) — no work leaks across
  background/foreground transitions.
- **Startup + bundle budgets** set from sprint one; audit every dependency and drop unused ones (performance debt
  compounds faster than technical debt).

## Accessibility floor (non-negotiable — WCAG 2.2 AA / EAA 2026)

- Every interactive element has a meaningful **VoiceOver** (iOS) / **TalkBack** (Android) label and role.
- **Touch targets** ≥ **44 × 44 pt (iOS)** / **48 × 48 dp (Android)**; WCAG 2.5.8 floor is 24 × 24 px.
- **Dynamic Type** (iOS) / scalable **`sp`** units (Android) — never hardcode font sizes; layouts reflow at the
  largest system text size.
- **Contrast** ≥ 4.5:1 normal text, 3:1 large text.
- **Gesture alternatives:** every complex gesture (pinch, multi-finger, drag) has a single-finger / button path.

## Device-size test matrix

"Tested at all sizes" means concretely:
- **Widths:** small phone → large phone → tablet (and foldable where relevant); verify no horizontal overflow.
- **Safe area / notch / dynamic island:** insets respected top and bottom; nothing clipped under the status bar or
  home indicator.
- **Orientation:** portrait and landscape where the app allows rotation.
- **Surfaces:** simulator/emulator for breadth + at least one **real device** for gesture/perf truth.

## Test tooling — choose with a named device matrix

| Tool | Scope | Use when |
|---|---|---|
| **Maestro** | iOS, Android, RN, Flutter, web — declarative YAML flows | Cross-platform E2E, lowest setup, low flakiness — the default for mixed stacks |
| **Detox** | React Native (gray-box, syncs with app state) | RN-only apps wanting the lowest flakiness |
| **XCUITest** | iOS native (Xcode) | iOS-only, deep native integration |
| **Espresso** | Android native | Android-only |

Name the tool, the device/OS matrix, and the simulator-vs-real-device split — don't leave testing implicit.

## Performance budgets

- **16 ms** main-thread budget per frame — anything heavier janks; verify with frame stats, not by eye.
- **Images:** optimize/resize before ship (unoptimized images remain a top mobile perf killer).
- **Lists:** virtualize long lists; never render off-screen rows.
- **Bundle + startup:** audit dependency weight; track cold-start time as a budget, not an afterthought.
- **Battery / data:** background work, polling, and large downloads are costs the design must justify.
