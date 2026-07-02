# Backlog Zero — SaaS-pack supersession close manifest (2026-07-02)

**Campaign:** Backlog Zero Wave 0 (umbrella: intent-solutions-io/intent-os#21).
**Cluster issue:** jeremylongshore/claude-code-plugins-plus-skills#938 · Plane CCPI-58.
**Epic bead:** "Supersede the v1 SaaS-pack hand-written skill tree: nine packs shipped under the v2 standardized template".

## Verdict

Of the nine v1 SaaS-pack bead trees' 268 open beads (9 pack epics + 259 children), **260
close** — most as superseded, a handful as done-with-evidence or duplicate — and **8 survive
as carve-outs** (next section). The packs shipped, but under the v2 standardized template
(install-auth / hello-world / core-workflow-* / common-errors …), not the per-topic
hand-written plan the beads describe. Three independent adversarial verification agents
(one per three packs) re-ran the repo's enterprise validator read-only and attacked the
supersession claim before any close; their carve-outs are honored in full.
Evidence class, verified on disk 2026-07-02 and re-checked by one adversarial verification
agent per pack before any close:

| Pack | Skills on disk | plugin.json version | marketplace.extended.json |
|---|---|---|---|
| snowflake | 30 | 1.0.0 | yes |
| hubspot | 10 (pain-catalog-grounded rebuild) | 2.0.0 | yes |
| vercel | 30 | 1.0.0 | yes |
| supabase | 30 | 1.0.0 | yes |
| openrouter | 30 | 1.0.0 | yes |
| figma | 30 | 1.0.0 | yes |
| notion | 32 | 1.0.0 | yes |
| shopify | 38 | 2.0.0 | yes |
| sentry | 30 | 1.0.0 | yes |

One-pagers: none exist for any shipped pack — dropped by the v2 template as a class.
"Final validation + ship (target 90+)": packs are catalog-live and gated by the required
`marketplace-validation` CI check; the 90+ target belonged to the retired v1 rubric.

## Close protocol

Scripted, one bead per `bd close`, `bd export` JSONL flush + state verification after every
close (bd ≤1.0.4 rapid-write race), one retry then FAIL-log. Followed by a stratified random
sample audit (≥10%, min 20, spread across packs) with halt-and-reverify-the-pack on any failure.
Bead IDs below are bd command handles for audit replay, per the estate bead-naming convention.

## Carve-outs (NOT closed by this manifest)

Eight beads survived the adversarial per-pack verification and stay OPEN, reparented under
the supersession epic with narrowed scopes (per-bead detail lives in bd comments):

| Bead | Title | Why it survives | Disposition |
|---|---|---|---|
| `claude-zo2d.34` | Snowflake: Final validation + ship (target 90+) | Validator avg 75.6/100, 0/30 skills ≥90; CI enterprise sweep is report-only. Carries the class-level policy question: does the 90+ bar bind template-generated packs? | needs-human, decision-by 2026-07-16 |
| `claude-v68g.34` | Supabase: Final validation + ship (target 90+) | Avg 87.7/100, 10 standing marketplace-tier findings | still-valid (clear findings or waiver) |
| `claude-hvx0.34` | OpenRouter: Final validation + ship (target 90+) | Avg 84.5/100, **179 standing marketplace-tier errors** — worst of the nine | still-valid |
| `claude-c33v.34` | Figma: Final validation + ship (target 90+) | Avg 81.3/100, 26 errors, stale TRACKER.csv row, no documented rewrite pass | still-valid (quality pass) |
| `claude-c33v.33` | Figma: Generate one-pagers | HARD carve-out: figma-pack ships ZERO references dirs (0/30) — no reference material of any kind (siblings: supabase 27/30, openrouter 30/30) | still-valid (add references content) |
| `claude-8r76.34` | HubSpot: Final validation + ship | 90+ met (90.2) but both catalogs + README still advertise "30 skills v1.0.0" vs the shipped 10-skill v2.0.0 | still-valid (catalog/README sync) |
| `claude-oqfc.34` | Notion: Final validation + ship (target 90+) | Avg 79.8/100 with 5 marketplace-tier ERRORS (missing sections, >500-line bodies, unscoped Bash + missing Safety Justification) | still-valid |
| `claude-6do9.34` | Sentry: Final validation + ship (target 90+) | Avg 90.6 meets target but 2 marketplace-tier ERRORS remain (missing Overview in cost-tuning + load-scale) | still-valid (two-file fix, then close) |

Two NEW decision beads were created under the supersession epic (both needs-human,
decision-by 2026-07-16):

1. **"Decide whether the HubSpot pack grows beyond its 10 shipped v2 skills"** — the
   v2.0.0 rebuild (commit a04d1a23e) was a deliberate scope decision; the 20 unshipped
   v1 topics are verifiably absent (0–8 occurrences each). Recommended default: keep at 10.
2. **"Decide whether per-skill one-pagers are part of the SaaS-pack standard"** — the v2
   template ships none and 102/107 packs have none, but 5 hand-worked flagship packs do
   (langchain-py 33, claude 32, oraclecloud 26, navan 26, onenote 18), so the drop was
   never an explicit decision. The eight per-pack one-pager beads close as superseded
   citing this bead as the open owner question. Recommended default: not part of the
   v2 standard.

Also noted for Wave 1 (observed drift, not beads yet): TRACKER.csv stale rows (snowflake
npm "reserved"/"not_added" though cataloged; notion "marketplace not_added"), and
package.json-vs-plugin.json version skews (snowflake 1.0.2/1.0.0, vercel 1.0.3/1.0.0 —
npm surface only).

## Closed beads

| Bead | Pack | Class | Title |
|---|---|---|---|
| `claude-c33v.10` | figma | build-skill | Figma Pack: Build skill 8/30 — rest-api |
| `claude-c33v.11` | figma | build-skill | Figma Pack: Build skill 9/30 — comments-api |
| `claude-c33v.12` | figma | build-skill | Figma Pack: Build skill 10/30 — version-history |
| `claude-c33v.13` | figma | build-skill | Figma Pack: Build skill 11/30 — branch-merge |
| `claude-c33v.14` | figma | build-skill | Figma Pack: Build skill 12/30 — dev-mode |
| `claude-c33v.15` | figma | build-skill | Figma Pack: Build skill 13/30 — code-generation |
| `claude-c33v.16` | figma | build-skill | Figma Pack: Build skill 14/30 — inspect-panel |
| `claude-c33v.17` | figma | build-skill | Figma Pack: Build skill 15/30 — prototype-api |
| `claude-c33v.18` | figma | build-skill | Figma Pack: Build skill 16/30 — webhooks |
| `claude-c33v.19` | figma | build-skill | Figma Pack: Build skill 17/30 — team-library |
| `claude-c33v.20` | figma | build-skill | Figma Pack: Build skill 18/30 — node-properties |
| `claude-c33v.21` | figma | build-skill | Figma Pack: Build skill 19/30 — image-export |
| `claude-c33v.22` | figma | build-skill | Figma Pack: Build skill 20/30 — style-api |
| `claude-c33v.23` | figma | build-skill | Figma Pack: Build skill 21/30 — text-api |
| `claude-c33v.24` | figma | build-skill | Figma Pack: Build skill 22/30 — layout-grids |
| `claude-c33v.25` | figma | build-skill | Figma Pack: Build skill 23/30 — constraints |
| `claude-c33v.26` | figma | build-skill | Figma Pack: Build skill 24/30 — effects-fills |
| `claude-c33v.27` | figma | build-skill | Figma Pack: Build skill 25/30 — selection-api |
| `claude-c33v.28` | figma | build-skill | Figma Pack: Build skill 26/30 — pages-frames |
| `claude-c33v.29` | figma | build-skill | Figma Pack: Build skill 27/30 — interactive-components |
| `claude-c33v.3` | figma | build-skill | Figma Pack: Build skill 1/30 — file-api |
| `claude-c33v.30` | figma | build-skill | Figma Pack: Build skill 28/30 — variant-properties |
| `claude-c33v.31` | figma | build-skill | Figma Pack: Build skill 29/30 — boolean-operations |
| `claude-c33v.32` | figma | build-skill | Figma Pack: Build skill 30/30 — asset-export |
| `claude-c33v.4` | figma | build-skill | Figma Pack: Build skill 2/30 — component-library |
| `claude-c33v.5` | figma | build-skill | Figma Pack: Build skill 3/30 — auto-layout |
| `claude-c33v.6` | figma | build-skill | Figma Pack: Build skill 4/30 — design-tokens |
| `claude-c33v.7` | figma | build-skill | Figma Pack: Build skill 5/30 — variables-api |
| `claude-c33v.8` | figma | build-skill | Figma Pack: Build skill 6/30 — plugin-development |
| `claude-c33v.9` | figma | build-skill | Figma Pack: Build skill 7/30 — widget-api |
| `claude-c33v` | figma | epic | EPIC: Figma Pack — 30 hand-written skills |
| `claude-8r76.10` | hubspot | build-skill | HubSpot Pack: Build skill 8/30 — association-api |
| `claude-8r76.11` | hubspot | build-skill | HubSpot Pack: Build skill 9/30 — crm-search |
| `claude-8r76.12` | hubspot | build-skill | HubSpot Pack: Build skill 10/30 — oauth-setup |
| `claude-8r76.13` | hubspot | build-skill | HubSpot Pack: Build skill 11/30 — webhook-subscription |
| `claude-8r76.14` | hubspot | build-skill | HubSpot Pack: Build skill 12/30 — timeline-events |
| `claude-8r76.15` | hubspot | build-skill | HubSpot Pack: Build skill 13/30 — marketing-email |
| `claude-8r76.16` | hubspot | build-skill | HubSpot Pack: Build skill 14/30 — landing-pages |
| `claude-8r76.17` | hubspot | build-skill | HubSpot Pack: Build skill 15/30 — meeting-scheduler |
| `claude-8r76.18` | hubspot | build-skill | HubSpot Pack: Build skill 16/30 — quote-generation |
| `claude-8r76.19` | hubspot | build-skill | HubSpot Pack: Build skill 17/30 — ticket-management |
| `claude-8r76.20` | hubspot | build-skill | HubSpot Pack: Build skill 18/30 — company-records |
| `claude-8r76.21` | hubspot | build-skill | HubSpot Pack: Build skill 19/30 — engagement-tracking |
| `claude-8r76.22` | hubspot | build-skill | HubSpot Pack: Build skill 20/30 — property-groups |
| `claude-8r76.23` | hubspot | build-skill | HubSpot Pack: Build skill 21/30 — import-export |
| `claude-8r76.24` | hubspot | build-skill | HubSpot Pack: Build skill 22/30 — batch-operations |
| `claude-8r76.25` | hubspot | build-skill | HubSpot Pack: Build skill 23/30 — owner-assignment |
| `claude-8r76.26` | hubspot | build-skill | HubSpot Pack: Build skill 24/30 — pipeline-stages |
| `claude-8r76.27` | hubspot | build-skill | HubSpot Pack: Build skill 25/30 — lead-scoring |
| `claude-8r76.28` | hubspot | build-skill | HubSpot Pack: Build skill 26/30 — attribution-reporting |
| `claude-8r76.29` | hubspot | build-skill | HubSpot Pack: Build skill 27/30 — conversation-inbox |
| `claude-8r76.3` | hubspot | build-skill | HubSpot Pack: Build skill 1/30 — contact-create |
| `claude-8r76.30` | hubspot | build-skill | HubSpot Pack: Build skill 28/30 — chatbot-builder |
| `claude-8r76.31` | hubspot | build-skill | HubSpot Pack: Build skill 29/30 — blog-api |
| `claude-8r76.32` | hubspot | build-skill | HubSpot Pack: Build skill 30/30 — analytics-api |
| `claude-8r76.4` | hubspot | build-skill | HubSpot Pack: Build skill 2/30 — deal-pipeline |
| `claude-8r76.5` | hubspot | build-skill | HubSpot Pack: Build skill 3/30 — email-send |
| `claude-8r76.6` | hubspot | build-skill | HubSpot Pack: Build skill 4/30 — workflow-automation |
| `claude-8r76.7` | hubspot | build-skill | HubSpot Pack: Build skill 5/30 — form-submission |
| `claude-8r76.8` | hubspot | build-skill | HubSpot Pack: Build skill 6/30 — list-segmentation |
| `claude-8r76.9` | hubspot | build-skill | HubSpot Pack: Build skill 7/30 — custom-objects |
| `claude-8r76` | hubspot | epic | EPIC: HubSpot Pack — 30 hand-written skills |
| `claude-8r76.33` | hubspot | one-pagers | HubSpot Pack: Generate one-pagers for all 30 skills |
| `claude-oqfc.10` | notion | build-skill | Notion Pack: Build skill 8/30 — authentication |
| `claude-oqfc.11` | notion | build-skill | Notion Pack: Build skill 9/30 — pagination |
| `claude-oqfc.12` | notion | build-skill | Notion Pack: Build skill 10/30 — rich-text |
| `claude-oqfc.13` | notion | build-skill | Notion Pack: Build skill 11/30 — database-create |
| `claude-oqfc.14` | notion | build-skill | Notion Pack: Build skill 12/30 — page-archive |
| `claude-oqfc.15` | notion | build-skill | Notion Pack: Build skill 13/30 — block-children |
| `claude-oqfc.16` | notion | build-skill | Notion Pack: Build skill 14/30 — comments-api |
| `claude-oqfc.17` | notion | build-skill | Notion Pack: Build skill 15/30 — user-list |
| `claude-oqfc.18` | notion | build-skill | Notion Pack: Build skill 16/30 — filter-sorts |
| `claude-oqfc.19` | notion | build-skill | Notion Pack: Build skill 17/30 — oauth-flow |
| `claude-oqfc.20` | notion | build-skill | Notion Pack: Build skill 18/30 — webhook-setup |
| `claude-oqfc.21` | notion | build-skill | Notion Pack: Build skill 19/30 — file-upload |
| `claude-oqfc.22` | notion | build-skill | Notion Pack: Build skill 20/30 — template-pages |
| `claude-oqfc.23` | notion | build-skill | Notion Pack: Build skill 21/30 — linked-databases |
| `claude-oqfc.24` | notion | build-skill | Notion Pack: Build skill 22/30 — status-property |
| `claude-oqfc.25` | notion | build-skill | Notion Pack: Build skill 23/30 — unique-id |
| `claude-oqfc.26` | notion | build-skill | Notion Pack: Build skill 24/30 — button-property |
| `claude-oqfc.27` | notion | build-skill | Notion Pack: Build skill 25/30 — ai-integration |
| `claude-oqfc.28` | notion | build-skill | Notion Pack: Build skill 26/30 — synced-blocks |
| `claude-oqfc.29` | notion | build-skill | Notion Pack: Build skill 27/30 — database-views |
| `claude-oqfc.3` | notion | build-skill | Notion Pack: Build skill 1/30 — page-create |
| `claude-oqfc.30` | notion | build-skill | Notion Pack: Build skill 28/30 — permissions-share |
| `claude-oqfc.31` | notion | build-skill | Notion Pack: Build skill 29/30 — page-analytics |
| `claude-oqfc.32` | notion | build-skill | Notion Pack: Build skill 30/30 — workspace-setup |
| `claude-oqfc.4` | notion | build-skill | Notion Pack: Build skill 2/30 — database-query |
| `claude-oqfc.5` | notion | build-skill | Notion Pack: Build skill 3/30 — block-append |
| `claude-oqfc.6` | notion | build-skill | Notion Pack: Build skill 4/30 — search-api |
| `claude-oqfc.7` | notion | build-skill | Notion Pack: Build skill 5/30 — page-properties |
| `claude-oqfc.8` | notion | build-skill | Notion Pack: Build skill 6/30 — relation-rollup |
| `claude-oqfc.9` | notion | build-skill | Notion Pack: Build skill 7/30 — formula-fields |
| `claude-oqfc` | notion | epic | EPIC: Notion Pack — 30 hand-written skills |
| `claude-oqfc.33` | notion | one-pagers | Notion Pack: Generate one-pagers for all 30 skills |
| `claude-hvx0.10` | openrouter | build-skill | OpenRouter Pack: Build skill 8/30 — rate-limit-handling |
| `claude-hvx0.11` | openrouter | build-skill | OpenRouter Pack: Build skill 9/30 — token-counting |
| `claude-hvx0.12` | openrouter | build-skill | OpenRouter Pack: Build skill 10/30 — provider-preferences |
| `claude-hvx0.13` | openrouter | build-skill | OpenRouter Pack: Build skill 11/30 — json-mode |
| `claude-hvx0.14` | openrouter | build-skill | OpenRouter Pack: Build skill 12/30 — vision-models |
| `claude-hvx0.15` | openrouter | build-skill | OpenRouter Pack: Build skill 13/30 — context-caching |
| `claude-hvx0.16` | openrouter | build-skill | OpenRouter Pack: Build skill 14/30 — batch-requests |
| `claude-hvx0.17` | openrouter | build-skill | OpenRouter Pack: Build skill 15/30 — model-search |
| `claude-hvx0.18` | openrouter | build-skill | OpenRouter Pack: Build skill 16/30 — credit-management |
| `claude-hvx0.19` | openrouter | build-skill | OpenRouter Pack: Build skill 17/30 — usage-analytics |
| `claude-hvx0.20` | openrouter | build-skill | OpenRouter Pack: Build skill 18/30 — prompt-caching |
| `claude-hvx0.21` | openrouter | build-skill | OpenRouter Pack: Build skill 19/30 — tool-use |
| `claude-hvx0.22` | openrouter | build-skill | OpenRouter Pack: Build skill 20/30 — reasoning-models |
| `claude-hvx0.23` | openrouter | build-skill | OpenRouter Pack: Build skill 21/30 — multimodal-input |
| `claude-hvx0.24` | openrouter | build-skill | OpenRouter Pack: Build skill 22/30 — structured-output |
| `claude-hvx0.25` | openrouter | build-skill | OpenRouter Pack: Build skill 23/30 — model-benchmarks |
| `claude-hvx0.26` | openrouter | build-skill | OpenRouter Pack: Build skill 24/30 — api-key-management |
| `claude-hvx0.27` | openrouter | build-skill | OpenRouter Pack: Build skill 25/30 — error-handling |
| `claude-hvx0.28` | openrouter | build-skill | OpenRouter Pack: Build skill 26/30 — latency-optimization |
| `claude-hvx0.29` | openrouter | build-skill | OpenRouter Pack: Build skill 27/30 — content-moderation |
| `claude-hvx0.3` | openrouter | build-skill | OpenRouter Pack: Build skill 1/30 — chat-completion |
| `claude-hvx0.30` | openrouter | build-skill | OpenRouter Pack: Build skill 28/30 — fine-tune-routing |
| `claude-hvx0.31` | openrouter | build-skill | OpenRouter Pack: Build skill 29/30 — embedding-models |
| `claude-hvx0.32` | openrouter | build-skill | OpenRouter Pack: Build skill 30/30 — completion-params |
| `claude-hvx0.4` | openrouter | build-skill | OpenRouter Pack: Build skill 2/30 — model-routing |
| `claude-hvx0.5` | openrouter | build-skill | OpenRouter Pack: Build skill 3/30 — cost-tracking |
| `claude-hvx0.6` | openrouter | build-skill | OpenRouter Pack: Build skill 4/30 — streaming-response |
| `claude-hvx0.7` | openrouter | build-skill | OpenRouter Pack: Build skill 5/30 — function-calling |
| `claude-hvx0.8` | openrouter | build-skill | OpenRouter Pack: Build skill 6/30 — model-comparison |
| `claude-hvx0.9` | openrouter | build-skill | OpenRouter Pack: Build skill 7/30 — fallback-chains |
| `claude-hvx0` | openrouter | epic | EPIC: OpenRouter Pack — 30 hand-written skills |
| `claude-hvx0.33` | openrouter | one-pagers | OpenRouter Pack: Generate one-pagers for all 30 skills |
| `claude-mj8k.1` | sentry | duplicate | Sentry Pack: Research SDK, API, docs, pricing, errors |
| `claude-6do9` | sentry | epic | EPIC: Sentry Pack — 30 hand-written skills |
| `claude-6do9.33` | sentry | one-pagers | Sentry Pack: Generate one-pagers for all 30 skills |
| `claude-6230.10` | shopify | build-skill | Shopify Pack: Build skill 8/30 — webhook-handlers |
| `claude-6230.11` | shopify | build-skill | Shopify Pack: Build skill 9/30 — app-bridge |
| `claude-6230.12` | shopify | build-skill | Shopify Pack: Build skill 10/30 — metafields |
| `claude-6230.13` | shopify | build-skill | Shopify Pack: Build skill 11/30 — discount-functions |
| `claude-6230.14` | shopify | build-skill | Shopify Pack: Build skill 12/30 — payment-extensions |
| `claude-6230.15` | shopify | build-skill | Shopify Pack: Build skill 13/30 — fulfillment-service |
| `claude-6230.16` | shopify | build-skill | Shopify Pack: Build skill 14/30 — customer-accounts |
| `claude-6230.17` | shopify | build-skill | Shopify Pack: Build skill 15/30 — cart-api |
| `claude-6230.18` | shopify | build-skill | Shopify Pack: Build skill 16/30 — shopify-cli |
| `claude-6230.19` | shopify | build-skill | Shopify Pack: Build skill 17/30 — polaris-components |
| `claude-6230.20` | shopify | build-skill | Shopify Pack: Build skill 18/30 — graphql-queries |
| `claude-6230.21` | shopify | build-skill | Shopify Pack: Build skill 19/30 — bulk-operations |
| `claude-6230.22` | shopify | build-skill | Shopify Pack: Build skill 20/30 — multipass-auth |
| `claude-6230.23` | shopify | build-skill | Shopify Pack: Build skill 21/30 — script-tags |
| `claude-6230.24` | shopify | build-skill | Shopify Pack: Build skill 22/30 — liquid-templates |
| `claude-6230.25` | shopify | build-skill | Shopify Pack: Build skill 23/30 — app-subscriptions |
| `claude-6230.26` | shopify | build-skill | Shopify Pack: Build skill 24/30 — delivery-profiles |
| `claude-6230.27` | shopify | build-skill | Shopify Pack: Build skill 25/30 — collection-rules |
| `claude-6230.28` | shopify | build-skill | Shopify Pack: Build skill 26/30 — analytics-api |
| `claude-6230.29` | shopify | build-skill | Shopify Pack: Build skill 27/30 — pos-extensions |
| `claude-6230.3` | shopify | build-skill | Shopify Pack: Build skill 1/30 — storefront-api |
| `claude-6230.30` | shopify | build-skill | Shopify Pack: Build skill 28/30 — hydrogen-storefront |
| `claude-6230.31` | shopify | build-skill | Shopify Pack: Build skill 29/30 — markets-api |
| `claude-6230.32` | shopify | build-skill | Shopify Pack: Build skill 30/30 — gift-cards |
| `claude-6230.4` | shopify | build-skill | Shopify Pack: Build skill 2/30 — admin-api |
| `claude-6230.5` | shopify | build-skill | Shopify Pack: Build skill 3/30 — checkout-extensions |
| `claude-6230.6` | shopify | build-skill | Shopify Pack: Build skill 4/30 — theme-development |
| `claude-6230.7` | shopify | build-skill | Shopify Pack: Build skill 5/30 — product-management |
| `claude-6230.8` | shopify | build-skill | Shopify Pack: Build skill 6/30 — order-processing |
| `claude-6230.9` | shopify | build-skill | Shopify Pack: Build skill 7/30 — inventory-sync |
| `claude-6230.34` | shopify | done-validated | Shopify Pack: Final validation + ship (target 90+) |
| `claude-6230` | shopify | epic | EPIC: Shopify Pack — 30 hand-written skills |
| `claude-6230.33` | shopify | one-pagers | Shopify Pack: Generate one-pagers for all 30 skills |
| `claude-zo2d.10` | snowflake | build-skill | Snowflake Pack: Build skill 8/30 — data-sharing |
| `claude-zo2d.11` | snowflake | build-skill | Snowflake Pack: Build skill 9/30 — clone-objects |
| `claude-zo2d.12` | snowflake | build-skill | Snowflake Pack: Build skill 10/30 — time-travel |
| `claude-zo2d.13` | snowflake | build-skill | Snowflake Pack: Build skill 11/30 — access-control |
| `claude-zo2d.14` | snowflake | build-skill | Snowflake Pack: Build skill 12/30 — network-policies |
| `claude-zo2d.15` | snowflake | build-skill | Snowflake Pack: Build skill 13/30 — resource-monitors |
| `claude-zo2d.16` | snowflake | build-skill | Snowflake Pack: Build skill 14/30 — external-tables |
| `claude-zo2d.17` | snowflake | build-skill | Snowflake Pack: Build skill 15/30 — materialized-views |
| `claude-zo2d.18` | snowflake | build-skill | Snowflake Pack: Build skill 16/30 — dynamic-tables |
| `claude-zo2d.19` | snowflake | build-skill | Snowflake Pack: Build skill 17/30 — snowpipe-streaming |
| `claude-zo2d.20` | snowflake | build-skill | Snowflake Pack: Build skill 18/30 — cortex-llm |
| `claude-zo2d.21` | snowflake | build-skill | Snowflake Pack: Build skill 19/30 — search-optimization |
| `claude-zo2d.22` | snowflake | build-skill | Snowflake Pack: Build skill 20/30 — data-masking |
| `claude-zo2d.23` | snowflake | build-skill | Snowflake Pack: Build skill 21/30 — row-access-policy |
| `claude-zo2d.24` | snowflake | build-skill | Snowflake Pack: Build skill 22/30 — tag-management |
| `claude-zo2d.25` | snowflake | build-skill | Snowflake Pack: Build skill 23/30 — alert-notification |
| `claude-zo2d.26` | snowflake | build-skill | Snowflake Pack: Build skill 24/30 — marketplace-listing |
| `claude-zo2d.27` | snowflake | build-skill | Snowflake Pack: Build skill 25/30 — reader-accounts |
| `claude-zo2d.28` | snowflake | build-skill | Snowflake Pack: Build skill 26/30 — fail-safe |
| `claude-zo2d.29` | snowflake | build-skill | Snowflake Pack: Build skill 27/30 — replication |
| `claude-zo2d.3` | snowflake | build-skill | Snowflake Pack: Build skill 1/30 — warehouse-management |
| `claude-zo2d.30` | snowflake | build-skill | Snowflake Pack: Build skill 28/30 — database-roles |
| `claude-zo2d.31` | snowflake | build-skill | Snowflake Pack: Build skill 29/30 — hybrid-tables |
| `claude-zo2d.32` | snowflake | build-skill | Snowflake Pack: Build skill 30/30 — iceberg-tables |
| `claude-zo2d.4` | snowflake | build-skill | Snowflake Pack: Build skill 2/30 — query-execution |
| `claude-zo2d.5` | snowflake | build-skill | Snowflake Pack: Build skill 3/30 — stage-loading |
| `claude-zo2d.6` | snowflake | build-skill | Snowflake Pack: Build skill 4/30 — stream-processing |
| `claude-zo2d.7` | snowflake | build-skill | Snowflake Pack: Build skill 5/30 — task-scheduling |
| `claude-zo2d.8` | snowflake | build-skill | Snowflake Pack: Build skill 6/30 — stored-procedures |
| `claude-zo2d.9` | snowflake | build-skill | Snowflake Pack: Build skill 7/30 — udf-creation |
| `claude-zo2d` | snowflake | epic | EPIC: Snowflake Pack — 30 hand-written skills |
| `claude-zo2d.33` | snowflake | one-pagers | Snowflake Pack: Generate one-pagers for all 30 skills |
| `claude-v68g.10` | supabase | build-skill | Supabase Pack: Build skill 8/30 — postgrest-api |
| `claude-v68g.11` | supabase | build-skill | Supabase Pack: Build skill 9/30 — auth-providers |
| `claude-v68g.12` | supabase | build-skill | Supabase Pack: Build skill 10/30 — database-types |
| `claude-v68g.13` | supabase | build-skill | Supabase Pack: Build skill 11/30 — foreign-tables |
| `claude-v68g.14` | supabase | build-skill | Supabase Pack: Build skill 12/30 — triggers-functions |
| `claude-v68g.15` | supabase | build-skill | Supabase Pack: Build skill 13/30 — vector-search |
| `claude-v68g.16` | supabase | build-skill | Supabase Pack: Build skill 14/30 — cron-jobs |
| `claude-v68g.17` | supabase | build-skill | Supabase Pack: Build skill 15/30 — webhooks |
| `claude-v68g.18` | supabase | build-skill | Supabase Pack: Build skill 16/30 — branching |
| `claude-v68g.19` | supabase | build-skill | Supabase Pack: Build skill 17/30 — cli-commands |
| `claude-v68g.20` | supabase | build-skill | Supabase Pack: Build skill 18/30 — local-development |
| `claude-v68g.21` | supabase | build-skill | Supabase Pack: Build skill 19/30 — auth-hooks |
| `claude-v68g.22` | supabase | build-skill | Supabase Pack: Build skill 20/30 — multi-tenancy |
| `claude-v68g.23` | supabase | build-skill | Supabase Pack: Build skill 21/30 — connection-pooling |
| `claude-v68g.24` | supabase | build-skill | Supabase Pack: Build skill 22/30 — backup-restore |
| `claude-v68g.25` | supabase | build-skill | Supabase Pack: Build skill 23/30 — vault-secrets |
| `claude-v68g.26` | supabase | build-skill | Supabase Pack: Build skill 24/30 — queue-system |
| `claude-v68g.27` | supabase | build-skill | Supabase Pack: Build skill 25/30 — log-drain |
| `claude-v68g.28` | supabase | build-skill | Supabase Pack: Build skill 26/30 — custom-claims |
| `claude-v68g.29` | supabase | build-skill | Supabase Pack: Build skill 27/30 — auth-mfa |
| `claude-v68g.3` | supabase | build-skill | Supabase Pack: Build skill 1/30 — auth-signup |
| `claude-v68g.30` | supabase | build-skill | Supabase Pack: Build skill 28/30 — storage-policies |
| `claude-v68g.31` | supabase | build-skill | Supabase Pack: Build skill 29/30 — database-testing |
| `claude-v68g.32` | supabase | build-skill | Supabase Pack: Build skill 30/30 — project-management |
| `claude-v68g.4` | supabase | build-skill | Supabase Pack: Build skill 2/30 — database-query |
| `claude-v68g.5` | supabase | build-skill | Supabase Pack: Build skill 3/30 — realtime-subscribe |
| `claude-v68g.6` | supabase | build-skill | Supabase Pack: Build skill 4/30 — storage-upload |
| `claude-v68g.7` | supabase | build-skill | Supabase Pack: Build skill 5/30 — edge-functions |
| `claude-v68g.8` | supabase | build-skill | Supabase Pack: Build skill 6/30 — row-level-security |
| `claude-v68g.9` | supabase | build-skill | Supabase Pack: Build skill 7/30 — migrations |
| `claude-v68g` | supabase | epic | EPIC: Supabase Pack — 30 hand-written skills |
| `claude-v68g.33` | supabase | one-pagers | Supabase Pack: Generate one-pagers for all 30 skills |
| `claude-uezf.10` | vercel | build-skill | Vercel Pack: Build skill 8/30 — analytics-setup |
| `claude-uezf.11` | vercel | build-skill | Vercel Pack: Build skill 9/30 — cron-jobs |
| `claude-uezf.12` | vercel | build-skill | Vercel Pack: Build skill 10/30 — middleware |
| `claude-uezf.13` | vercel | build-skill | Vercel Pack: Build skill 11/30 — image-optimization |
| `claude-uezf.14` | vercel | build-skill | Vercel Pack: Build skill 12/30 — isr-revalidation |
| `claude-uezf.15` | vercel | build-skill | Vercel Pack: Build skill 13/30 — edge-config |
| `claude-uezf.16` | vercel | build-skill | Vercel Pack: Build skill 14/30 — feature-flags |
| `claude-uezf.17` | vercel | build-skill | Vercel Pack: Build skill 15/30 — web-analytics |
| `claude-uezf.18` | vercel | build-skill | Vercel Pack: Build skill 16/30 — speed-insights |
| `claude-uezf.19` | vercel | build-skill | Vercel Pack: Build skill 17/30 — firewall-rules |
| `claude-uezf.20` | vercel | build-skill | Vercel Pack: Build skill 18/30 — deploy-hooks |
| `claude-uezf.21` | vercel | build-skill | Vercel Pack: Build skill 19/30 — monorepo-config |
| `claude-uezf.22` | vercel | build-skill | Vercel Pack: Build skill 20/30 — team-management |
| `claude-uezf.23` | vercel | build-skill | Vercel Pack: Build skill 21/30 — log-drains |
| `claude-uezf.24` | vercel | build-skill | Vercel Pack: Build skill 22/30 — integration-api |
| `claude-uezf.25` | vercel | build-skill | Vercel Pack: Build skill 23/30 — ai-sdk-usage |
| `claude-uezf.26` | vercel | build-skill | Vercel Pack: Build skill 24/30 — blob-storage |
| `claude-uezf.27` | vercel | build-skill | Vercel Pack: Build skill 25/30 — kv-storage |
| `claude-uezf.28` | vercel | build-skill | Vercel Pack: Build skill 26/30 — postgres-setup |
| `claude-uezf.29` | vercel | build-skill | Vercel Pack: Build skill 27/30 — framework-presets |
| `claude-uezf.3` | vercel | build-skill | Vercel Pack: Build skill 1/30 — deploy-project |
| `claude-uezf.30` | vercel | build-skill | Vercel Pack: Build skill 28/30 — project-linking |
| `claude-uezf.31` | vercel | build-skill | Vercel Pack: Build skill 29/30 — rollback-deploy |
| `claude-uezf.32` | vercel | build-skill | Vercel Pack: Build skill 30/30 — custom-headers |
| `claude-uezf.4` | vercel | build-skill | Vercel Pack: Build skill 2/30 — environment-variables |
| `claude-uezf.6` | vercel | build-skill | Vercel Pack: Build skill 4/30 — serverless-api |
| `claude-uezf.7` | vercel | build-skill | Vercel Pack: Build skill 5/30 — domain-management |
| `claude-uezf.8` | vercel | build-skill | Vercel Pack: Build skill 6/30 — build-configuration |
| `claude-uezf.5` | vercel | done-as-named | Vercel Pack: Build skill 3/30 — edge-functions |
| `claude-uezf.9` | vercel | done-as-named | Vercel Pack: Build skill 7/30 — preview-deployments |
| `claude-uezf.34` | vercel | done-validated-90 | Vercel Pack: Final validation + ship (target 90+) |
| `claude-uezf` | vercel | epic | EPIC: Vercel Pack — 30 hand-written skills |
| `claude-uezf.33` | vercel | one-pagers | Vercel Pack: Generate one-pagers for all 30 skills |

_Generated from the wave-start snapshot of .beads/issues.jsonl; 260 beads._

## Post-close verification (addendum, 2026-07-02)

- **Full-set check:** 260/260 closed, 0 unclosed, verified per-bead against the re-exported
  `issues.jsonl` (one `bd export` flush after every write batch).
- **Ordering:** the initial one-at-a-time loop hit dependency-refused closes (one-pagers and
  final-validation beads are dep-blocked by their build-skill siblings; epics by their
  children). Re-run as ordered batches — children → one-pagers → epics — after which every
  close landed clean. No `--force` was needed: all blockers were in-tree and closed first.
- **Stratified sample audit:** 27 sampled (3 per pack, random): 26 PASS on
  status+disk+reason-evidence; 1 evidence-string artifact (the duplicate-class close reason
  did not name its pack — amended to cite the duplicate target bead explicitly; the sentry
  pack was then fully reverified: its earlier build closes carry per-PR evidence, e.g.
  "Built sentry-load-scale → PR #416").
- **Database effect:** claude-code-plugins open count 487 → 230. Survivors: the supersession
  epic, its 2 needs-human decision beads, and the 8 carve-outs.
