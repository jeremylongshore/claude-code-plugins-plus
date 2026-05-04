# Drawing Rules

Visual design rules for engineer-design-diagram output. Palette and arrow-masking pattern inspired by [Cocoon AI/architecture-diagram-generator](https://github.com/Cocoon-AI/architecture-diagram-generator) (MIT).

## Table of Contents

- [Color Palette](#color-palette)
- [Role Inference](#role-inference)
- [Typography](#typography)
- [Canvas & Grid](#canvas--grid)
- [Component Boxes](#component-boxes)
- [Arrow Masking](#arrow-masking)
- [Z-Order](#z-order)
- [Boundaries & Groups](#boundaries--groups)
- [Message Buses](#message-buses)
- [Spacing Rules](#spacing-rules)
- [Legend Placement](#legend-placement)
- [Delta Markers (Diff Mode)](#delta-markers-diff-mode)

## Color Palette

Semantic OKLCH palette by component role. Values are used as CSS custom properties on `:root` in `templates/base.html`.

| Role | Fill (rgba) | Stroke (hex) | CSS tokens |
|------|-------------|--------------|------------|
| Frontend | `rgba(8, 51, 68, 0.4)` | `#22d3ee` | `--role-frontend-fill` / `--role-frontend-stroke` |
| Backend | `rgba(6, 78, 59, 0.4)` | `#34d399` | `--role-backend-fill` / `--role-backend-stroke` |
| Database | `rgba(76, 29, 149, 0.4)` | `#a78bfa` | `--role-db-fill` / `--role-db-stroke` |
| Cloud (AWS/GCP/Azure) | `rgba(120, 53, 15, 0.3)` | `#fbbf24` | `--role-cloud-fill` / `--role-cloud-stroke` |
| Security | `rgba(136, 19, 55, 0.4)` | `#fb7185` | `--role-security-fill` / `--role-security-stroke` |
| Message Bus | `rgba(251, 146, 60, 0.3)` | `#fb923c` | `--role-bus-fill` / `--role-bus-stroke` |
| External / Generic | `rgba(30, 41, 59, 0.5)` | `#94a3b8` | `--role-external-fill` / `--role-external-stroke` |

## Role Inference

When the DCI output doesn't explicitly name a role, apply these heuristics in order:

1. **Port-based**: `80/443/3000-3999` + name contains `web|ui|app|frontend|next|react|vue|svelte` → **frontend**
2. **Image-based** (docker-compose): `postgres|mysql|mongo|redis|cassandra|elastic|dynamo|sqlite` → **database**
3. **Known bus images**: `kafka|rabbitmq|nats|pulsar|sqs|pubsub|eventhub` → **message-bus**
4. **Known security services**: `auth|cognito|oauth|keycloak|vault|cert-manager` → **security**
5. **Cloud-specific kinds**: `aws_*`, `google_*`, `azurerm_*` terraform resources → **cloud**
6. **HTTP handler**: name contains `api|service|handler|worker|backend|server` → **backend**
7. **Default**: **external** (slate) — documents in legend as "other / unknown"

## Typography

JetBrains Mono for all text — monospace, technical aesthetic:

```html
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=JetBrains+Mono:wght@400;500;600;700&display=swap" rel="stylesheet">
```

Font sizes:
- Component name: `12px`, weight `600`
- Sublabel: `9px`, weight `400`, color `#94a3b8`
- Annotations: `8px`, weight `400`
- Tiny labels (bus names): `7px`, weight `400`

## Canvas & Grid

Background: `#020617` (slate-950). Subtle grid pattern as a `<defs><pattern>`:

```svg
<defs>
  <pattern id="grid" width="40" height="40" patternUnits="userSpaceOnUse">
    <path d="M 40 0 L 0 0 0 40" fill="none" stroke="#1e293b" stroke-width="0.5"/>
  </pattern>
</defs>
<rect width="100%" height="100%" fill="url(#grid)"/>
```

Arrow-mask background fill color (behind semi-transparent boxes): `#0f172a`.

## Component Boxes

Rounded rectangles with 1.5px stroke, semi-transparent fill, `rx="6"`:

```svg
<rect x="X" y="Y" width="W" height="H" rx="6"
      fill="var(--role-backend-fill)"
      stroke="var(--role-backend-stroke)"
      stroke-width="1.5"/>
<text x="CX" y="Y+20" fill="white" font-size="12" font-weight="600" text-anchor="middle">Name</text>
<text x="CX" y="Y+36" fill="#94a3b8" font-size="9" text-anchor="middle">sublabel</text>
```

Every `<rect>` representing a node must include a `<title>` child for accessibility (see [accessibility.md](accessibility.md)).

Standard dimensions:
- Width: `180px` default, `140-220px` range
- Height: `60px` for services, `80-120px` for larger grouped components

## Arrow Masking

Component boxes have semi-transparent fills (`0.3-0.5` alpha), so arrows drawn behind them show through and look messy. The fix: draw an opaque background rect first, then the semi-transparent styled rect on top.

```svg
<!-- 1. Opaque mask underlayer -->
<rect x="X" y="Y" width="W" height="H" rx="6" fill="#0f172a"/>
<!-- 2. Styled semi-transparent box on top -->
<rect x="X" y="Y" width="W" height="H" rx="6"
      fill="var(--role-db-fill)"
      stroke="var(--role-db-stroke)"
      stroke-width="1.5"/>
```

## Z-Order

SVG elements are painted in document order. Our stacking rule:

1. `<defs>` (patterns, markers, gradients)
2. Grid background rect
3. Group/boundary rects (dashed)
4. Connection arrows/paths
5. Arrow-mask underlayers (opaque)
6. Component box rects (semi-transparent styled)
7. Component text labels
8. Legend

Arrows drawn before components appear **behind** them — correct behavior. Arrows drawn last appear on top and obscure text — wrong.

## Boundaries & Groups

**Security groups:** dashed stroke, rose color, transparent fill.

```svg
<rect x="X" y="Y" width="W" height="H" rx="6"
      fill="none" stroke="#fb7185" stroke-width="1.5" stroke-dasharray="4,4"/>
<text x="X+8" y="Y+14" fill="#fb7185" font-size="9" font-weight="500">Security Group</text>
```

**Region / cluster boundaries:** larger dashes, amber color, rounder corners.

```svg
<rect x="X" y="Y" width="W" height="H" rx="12"
      fill="none" stroke="#fbbf24" stroke-width="1.5" stroke-dasharray="8,4"/>
<text x="X+12" y="Y+18" fill="#fbbf24" font-size="10" font-weight="500">us-east-1</text>
```

## Message Buses

Small inline connectors placed in the gap between services. Orange fill + stroke:

```svg
<rect x="X" y="Y" width="120" height="20" rx="4"
      fill="var(--role-bus-fill)" stroke="var(--role-bus-stroke)" stroke-width="1"/>
<text x="CX" y="Y+14" fill="#fb923c" font-size="7" text-anchor="middle">Kafka / RabbitMQ</text>
```

## Spacing Rules

**40px minimum vertical gap** between components. Buses go *in* the gap, not overlapping.

Standard component heights:
- Service/container: `60px`
- Grouped service (with sublabel list): `80-120px`
- Message bus connector: `20px` (placed inside the 40px gap)

Correct vertical layout:

```
Component A:  y=70,   height=60   → ends at y=130
Gap:          y=130 → y=170       → 40px gap, bus at y=140 (20px tall, centered in 40px gap)
Component B:  y=170,  height=60   → ends at y=230
```

Incorrect: placing a bus at `y=160` when Component B starts at `y=170` — causes overlap.

## Legend Placement

**Legends go OUTSIDE all boundary boxes** (regions, clusters, security groups).

1. Compute `max_boundary_y = max(boundary.y + boundary.height for boundary in boundaries)`
2. Place legend at `y = max_boundary_y + 20px` minimum
3. Expand SVG `viewBox` height if needed

Correct:

```
Kubernetes cluster boundary:  y=30,  height=460  → ends at y=490
Legend:                       y=510  (20px below boundary)
SVG viewBox height:           ≥ 560 (fits legend + padding)
```

Incorrect: legend at `y=470` inside a cluster boundary ending at `y=490`.

## Delta Markers (Diff Mode)

For PR-diff output, apply CSS classes to added/removed/changed elements:

```css
.delta-added {
  stroke-dasharray: none;
  filter: drop-shadow(0 0 6px #22c55e);
}
.delta-removed {
  opacity: 0.4;
  stroke-dasharray: 4,2;
  filter: grayscale(1);
}
.delta-changed {
  filter: drop-shadow(0 0 6px #fbbf24);
}
```

And add a delta legend row next to the main legend:

```svg
<rect class="delta-added" x="X" y="Y" width="16" height="16" rx="3"/>
<text x="X+22" y="Y+12" font-size="9">Added in this PR</text>
```
