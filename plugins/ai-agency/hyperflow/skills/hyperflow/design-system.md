# Design-system protocol

The shared design step the [`designer`](../../agents/designer.md) agent and the [`design`](../design/SKILL.md) skill
invoke before any screen is designed. Good design is **researched, systematic, and grounded in a living design
system** — not improvised per screen and not the templated default an AI reaches for by reflex.

This file is the **single source of truth** for the design method, the design-system artefact, the local taste-skill
index, and the anti-slop floor. The `designer` charter and the `design` skill reference it by one line and never
restate it. It binds — it does not duplicate — the `ui` and `creative` persona standards in
[`personas-A.md`](personas-A.md).

## The design-system artefact

The durable design system lives at **`.hyperflow/design/system.md`** — a living document that survives across
features (distinct from per-feature specs under `.hyperflow/specs/`). It is **created once and extended**, never
regenerated from scratch.

**When it is missing, create it first** — before designing any screen. Format per
[`artefact-format.md`](artefact-format.md): a markdown-table status block, then these sections:

| Section | Holds |
|---|---|
| Domain + audience | the product's field and who it serves — drives every reference choice |
| Color tokens | named values + roles (surface, text, one accent); never a raw hex inline elsewhere |
| Type scale + pairing | display + body (+ utility) faces, sizes, weights, tracking |
| Spacing scale | the only spacing values allowed downstream — no arbitrary pixels |
| Motion language | easing curves, durations, what motion is allowed to communicate — the [`motion`](../../agents/motion.md) agent reads and extends this; deep motion-engineering rules live in [`motion.md`](motion.md) |
| Voice / tone | how copy reads; what words the product does and doesn't use |
| Component inventory | named primitives + their visual treatment, cross-referenced by `frontend`/`ui` workers |
| References | the **real systems studied** to ground the system (with the combination rationale) |
| Anti-patterns | what this brand must avoid — the slop floor below, specialised to this product |

When present, **extend** it: add the new tokens/components, append to references, never rewrite the established
language. The `ui` persona's "read the design token file before introducing any new value" rule resolves against this
file.

## The method (research → combine → diverge)

1. **Research the field.** Study **≥2** real products/systems in the project's own domain via web-research-first
   ([`web-research.md`](web-research.md)) — how peers in this field actually look and behave, plus current
   design-system and interaction patterns and award-tier references for the surface.
2. **Combine.** Synthesise the studied references into a coherent direction — take the load-bearing idea from each,
   not a copy of one. Record the combination rationale in the `References` section.
3. **Diverge with one deliberate signature.** Add a single, named signature move that makes the design ownable. Spend
   boldness in one place; keep the rest quiet (the `creative` persona's thesis discipline).
4. **Never ship the templated default.** If the direction reads like what you'd produce for any brief in this
   category, it has not diverged — revise.

## Local taste-skill index

World-class anti-slop rules already live in the installed taste skills. **Discover and apply them — never duplicate
them here.** Discovery glob: `~/.claude/skills/*/SKILL.md` plus plugin skill directories
(`~/.claude/plugins/marketplaces/*/plugins/*/skills/*/SKILL.md`).

**Tool split (important):** a **dispatched subagent has no `Skill` tool** (its tools are
Read/Grep/Glob/Agent/WebSearch/WebFetch) — the `designer` agent **Reads the `SKILL.md`** and applies its rules. The
**`design` skill** runs in the main session, which *can* call `Skill` — it **invokes the matching taste skill live**,
then dispatches the `designer` under it.

| Skill | Use when |
|---|---|
| `design-taste-frontend` | landing pages, portfolios, redesigns — the default anti-slop frontend skill (audit-first, pre-flight checks) |
| `frontend-design` | brief-grounded distinctive UI — two-pass brainstorm → uniqueness review |
| `high-end-visual-design` | "make it feel expensive" — agency/Awwwards-tier visual language |
| `redesign-existing-projects` | upgrading an existing site/app — audit current design, strip generic patterns |
| `senior-creative-frontend` | animation-rich, SVG/GSAP/Framer, scroll-driven, "make it pop" interfaces |
| `minimalist-ui` | clean editorial monochrome systems — typographic contrast, flat bento, no heavy shadows |
| `industrial-brutalist-ui` | raw mechanical/terminal aesthetics — data-heavy dashboards, declassified-blueprint feel |
| `brandkit` | brand identity, logo systems, identity decks (generates images, not code) |
| `imagegen-frontend-web` / `imagegen-frontend-mobile` | premium design-reference images per section/screen (images only) |
| `image-to-code` | generate the design image, analyse it, then implement the site to match |
| `gpt-taste` / `stitch-design-taste` | editorial GSAP motion / semantic DESIGN.md generation when those workflows fit |

Pick the **fewest** skills that fit the brief — usually one primary taste skill, plus `brandkit`/`imagegen-*` only
when identity or reference imagery is genuinely needed.

## Anti-slop floor (the thin non-negotiables)

A short floor every design passes regardless of skill. Each line points at the taste skill that owns the deep rule —
this floor is deliberately thin and defers to those skills.

- **No default AI gradient.** No reflexive purple/violet or neon mesh-gradient backgrounds. One accent, saturation
  kept in check. (`design-taste-frontend`, `high-end-visual-design`)
- **No serif-by-default.** Serif only when the brand genuinely warrants it and you can say why. (`design-taste-frontend`)
- **No premium-beige reflex.** Warm beige/cream + brass + espresso is the default AI "luxury" palette — rotate
  instead. (`design-taste-frontend`)
- **Eyebrow restraint.** Not an uppercase-tracking eyebrow above every section. (`design-taste-frontend`)
- **No duplicate-intent CTAs.** One label per intent; CTA text fits one line at desktop. (`design-taste-frontend`)
- **Hero fits the viewport.** Headline ≤ 2 lines, CTAs visible without scroll. (`design-taste-frontend`)
- **One locked corner-radius scale** across the whole surface. (`high-end-visual-design`)
- **Motion must communicate.** Every animation conveys state or guides attention — never decoration (the `ui`
  persona's motion rule). (`senior-creative-frontend`)
- **No arbitrary values.** Every color/spacing/type value traces to `.hyperflow/design/system.md`. (the `ui` persona)

## Accessibility floor

The `ui` persona's WCAG-AA minimum, visible focus rings, `prefers-reduced-motion` fallback, and RTL-safe directional
utilities are **non-negotiable** — they bind here unchanged. On any conflict between an aesthetic move and the a11y
floor, the floor wins; defer to [`accessibility-reviewer`](../../agents/accessibility-reviewer.md).

## Output discipline

The design system and design specs are **files** under `.hyperflow/` (rule 8, file-first). Chat shows a short status
box pointing at the file — never the full token dump. Research output is a short cited brief
([`web-research.md`](web-research.md) token discipline), ending in `Sources consulted:` when research ran.
