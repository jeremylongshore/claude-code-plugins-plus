# DESIGN_AUDIT_2026-05-06.md — Pre-rebrand punch list

**Auditor:** Diagnostician (ui-ux-designer methodology, audit prompt from `rohitg00/awesome-claude-design/prompts/audit-live-site.md`).
**Date:** 2026-05-06.
**Sites audited:** tonsofskills.com homepage, `/explore`, `/skills`, `/docs`.
**Driver:** Kobiton marketing push pointing at tonsofskills.com — CEO-level visual quality required.

This is the input that the rebrand intervention codes against. After Refactorer + Surgeon + Mobile Specialist land their work, the Validator will re-run against this list and check that every P0/P1 item is addressed.

---

## P0 — must-fix before Kobiton push (ship-blocking)

| # | Issue | Where | Fix owner |
|---|---|---|---|
| P0.1 | `explore/index.html` is **12 MB shipped** vs declared 860 KB budget. 8+ s to interactive on a 4G phone — indistinguishable from "site is broken." | `src/pages/explore.astro:4` static-imports the 2.5 MB `unified-search-index.json`. Inlines into HTML. | Performance Surgeon |
| P0.2 | `skills/index.html` is **6.6 MB shipped** vs declared 300 KB budget. | `src/pages/skills/index.astro:3` static-imports the 22.8 MB `skills-catalog.json`. Inlines into HTML. | Performance Surgeon |
| P0.3 | Partner bar shows two unique entries (nixtla.io + agent37.com) duplicated 3× to fake a marquee. Reads as sparse / "we have no partners." | `src/pages/index.astro` ~lines 1199–1218. Hardcoded HTML, infinite-scroll CSS animation. | Refactorer (PR 1) |
| P0.4 | Kobiton (the deadline-driving partner, https://kobiton.com) is not on the partner bar. | n/a — additive change. | Refactorer (PR 1) |
| P0.5 | Visual identity is "warm terracotta + Instrument Sans + Source Sans 3 + DM Mono" — reads as developer-side-project not analytics-product. Doesn't survive the CEO-level gut check. | `src/styles/tokens.css`, `src/styles/global.css`, `src/layouts/BaseLayout.astro`, plus 37 component files with hardcoded font-name strings. | Constitution Author + Refactorer (PR 2) |
| P0.6 | No tablet breakpoint. Layout jumps 768 → 1280 from 1-column directly to 3-column. Tablets in landscape get the cramped mobile layout. | `src/styles/tokens.css` (no `--breakpoint-tablet`); `.results-grid` rule in explore.astro / skills/index.astro. | Mobile Specialist |
| P0.7 | Sticky filter bar on `/explore` consumes 25 % of mobile viewport before any results render. | `src/pages/explore.astro` filter-rail CSS `position: sticky; top: 80 px`. | Mobile Specialist |
| P0.8 | Touch targets below 44 × 44 px on mobile (`.copy-btn` install command, `.filter-chip`, `.sort-select`). Apple HIG floor missed. | Various components, audit + measure required. | Mobile Specialist |

## P1 — must-fix in this intervention but not literally ship-blocking

| # | Issue | Where | Fix owner |
|---|---|---|---|
| P1.1 | Button-vs-link conflation. The same warm-terracotta is used for "Get Started" CTA, inline links in body copy, and section-heading hover states. Reader can't tell what's a primary action. | `src/styles/global.css` `a` rule (line 80–84) gives all anchors `color: var(--primary)`. | Refactorer (PR 3) |
| P1.2 | No `--signal` discipline. Primary accent is everywhere. Should be ONE primary CTA per page. | All pages. Constitution Author authors the rule; Refactorer enforces. | Refactorer (PR 3) |
| P1.3 | Cards monotonous on `/explore` and `/skills` — featured / standard / compact tiers exist as tokens but aren't visually distinct. | `tokens.css` defines tiers; `.result-card` styles in explore.astro don't apply tier-specific differences. | Refactorer (PR 4) |
| P1.4 | Drop-shadow lift on card hover (`box-shadow` in `--card-hover-shadow`). Reads as default-Tailwind aesthetic. | `tokens.css` line 90. | Constitution Author (rewrite to `transform: translateY(-1 px)` only) |
| P1.5 | Typography hierarchy doesn't use tabular numerals. Stats and counts ("1,537 skills · 47 collections") shift width as data updates. | `body` `font-feature-settings` is unset. | Constitution Author (set globally) |
| P1.6 | Section h2 headings have no rule beneath them. Sections fight for attention without structural separators. | Various pages. | Refactorer (PR 3) |
| P1.7 | Footer columns at 480 px collapse to 1-column directly. Should be 2-column at 480–768 px range. | `BaseLayout.astro` `.footer-columns` `@media (max-width: 480px)`. | Mobile Specialist |
| P1.8 | Mobile search input lacks `inputmode="search"` + `enterkeyhint="search"` attributes — iOS shows generic keyboard, not the search-key label. | `src/pages/index.astro` hero search input + `/explore` search input. | Mobile Specialist |
| P1.9 | Light theme exists but is undertested. `[data-theme="light"]` overrides only cover background-color + scrollbar. Many components hardcode dark-only values. | All over. | Refactorer (sweep alongside PR 2) |

## P2 — nice-to-have, defer past this intervention

| # | Issue | Where | Defer reason |
|---|---|---|---|
| P2.1 | Hero stat marquee "live npm downloads · 200 packages · 2,847 last 30d" is an infinite-scroll loop. Same sparse-illusion problem as partner bar. | `src/pages/index.astro` `.hero-stats-marquee`. | Marquee is intentional here (data is meant to scroll); revisit only if tinkering w/ partner bar reveals shared component opportunity. |
| P2.2 | `/cowork` and `/community` pages have separate visual identities. | Various pages. | Out of scope per plan. Solve catalog-density problem first. |
| P2.3 | `/docs` section has its own template. Not yet visually unified with the rebrand. | `src/components/DocsTemplate.astro`. | Touch in follow-up PR; docs traffic is not on the Kobiton-push path. |
| P2.4 | Some component files (Hero.astro, KillerSkills.astro, etc.) hardcode font-family strings rather than using `var(--font-display)`. | 37 files identified by `grep -rE 'instrument sans\|source sans 3\|dm mono' src/`. | Sweep at the same time as the typography swap; if one is missed, the cascade should still resolve correctly. |
| P2.5 | `pre code` styling at line 109–114 of `global.css` hardcodes `var(--primary-light)` for code-block text. Will need to verify post-rebrand that yellow-on-near-black reads. | `global.css`. | Quick visual check; not a P1 because the contrast budget already accounts for it. |

---

## Anti-Slop fingerprint check (rohitg00 methodology)

Of the 16 items in the Anti-Slop Reject Table (DESIGN.md § 8), the current site fails:

| Item | Currently shipping? |
|---|---|
| Border-radius `md` on every surface uniformly | **Yes** — 6 / 8 / 12 px tier discipline is in tokens but not consistently applied. |
| Drop-shadow stacks for card lift | **Yes** — `--card-hover-shadow` uses `box-shadow`. |
| Multiple accent colors | **Partial** — primary terracotta + brand-blue + brand-green all in active use. Mixed signal. |
| `text-gray-400` style theming | **No** — semantic tokens are used. Win. |
| Generic stock illustrations | **No** — never had any. Win. |
| Pastel "AI" gradient on hero | **No** — hero is solid. Win. |
| Glassmorphism | **No** — `backdrop-filter: blur(12px)` on `nav` only, which is acceptable for nav specifically. |

Net: **3 confirmed Anti-Slop fingerprints** the rebrand resolves (radius discipline, shadow stacks, multi-accent). Remaining 13 are either already clean or out of scope.

---

## Pages-by-page summary

### Homepage (`/`)
P0: partner bar (P0.3, P0.4), full-rebrand color/typography (P0.5).
P1: button/link distinction (P1.1, P1.2), section-heading rules (P1.6).
**State after intervention**: hero reads Linear/Bloomberg-tier above the fold. Partner bar shows Kobiton + nixtla + agent37 in a static row.

### `/explore`
P0: 12 MB page weight (P0.1), tablet breakpoint (P0.6), filter rail eats viewport (P0.7), touch targets (P0.8).
P1: card hierarchy (P1.3), card hover (P1.4).
**State after intervention**: page weight under 1 MB; filter rail collapses to chip-row + bottom-sheet on mobile; cards reflow with content-priority order.

### `/skills`
P0: 6.6 MB page weight (P0.2), tablet breakpoint (P0.6), touch targets (P0.8).
P1: card hierarchy (P1.3).
**State after intervention**: page weight under 500 KB first-load; full catalog fetched lazy on filter/paginate.

### `/docs`
Out of scope for this intervention (P2.3). Follow-up PR.

---

## Acceptance criteria for re-audit

After all PRs land, the Diagnostician (or Validator) re-runs and confirms:

- Every P0 line item has a "fix landed in PR #" annotation
- Every P1 line item has either a "fix landed" or "deferred to next sprint with reason"
- Anti-Slop fingerprint count is 0 (or every remaining one is in P2 with explicit defer reason)
- Lighthouse mobile-performance score on `/explore` is ≥ 80 (currently estimated < 20)
- 6 viewport×state screenshots exist under `_before/` and `_after/` directories

---

## File locations for follow-up work

- **Constitution**: `marketplace/DESIGN.md` (authored 2026-05-06, family locked to Data-Dense Pro)
- **Token swap**: `marketplace/src/styles/tokens.css` (Constitution Author owns end-to-end before Refactorer starts)
- **Typography swap**: `marketplace/src/layouts/BaseLayout.astro` (Google Fonts URL + inline font-family rules) + `marketplace/src/styles/global.css` (font variables)
- **Partner bar refactor**: new `marketplace/src/data/partners.json` + new `marketplace/src/components/PartnerBar.astro` + edit at `marketplace/src/pages/index.astro:~1199`
- **Performance surgery**: `marketplace/src/pages/explore.astro`, `marketplace/src/pages/skills/index.astro`, `marketplace/scripts/build.mjs`, `marketplace/scripts/check-performance.mjs`
