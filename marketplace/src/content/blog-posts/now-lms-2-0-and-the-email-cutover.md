---
title: "Now-LMS 2.0 and the Email Cutover"
description: "A 2.0.0 that is mostly a careful rename plus security headers is exactly what a healthy release looks like."
date: "2026-07-25"
tags: ["release-engineering", "python", "devops", "web-development"]
featured: false
---
A healthy major version is not always a rewrite. now-lms shipped 2.0.0 yesterday as proof: the release was ninety percent discipline, ten percent new surface area. The breaking changes were documented with exact incompatibility points. A migration guide shipped alongside the code. That is the standard.

## The custom-pages refactor

The spine of the release was a single architectural rename. The system had a `static_pages` table. It became `custom_pages`. That sounds cosmetic until you trace the blast radius: the table, the blueprint that mapped it, the admin CRUD flow that touched it, the Jinja templates that rendered it, the test suite that exercised all of the above.

The refactor split the `static_pages` concern into three independent blueprints. The new `custom_pages` blueprint owns the core CRUD. Separate blueprints handle `contact` and `footer_links`, each with its own admin panel entry. Each change is versioned via Alembic.

The migration was clean:

```python
def upgrade():
    op.rename_table('static_pages', 'custom_pages')
```

Single line. No data loss. The beauty of a rename is that it forces you to verify every dependency. If you miss a reference, the code breaks loudly. No silent data drift.

## Security and theme fallback

The release added a full HTTP security header suite site-wide: `X-Content-Type-Options`, `X-Frame-Options`, `Referrer-Policy`, and the usual family. The theme system was hardened too. If a custom theme is missing its `theme.yml` manifest, the system falls back to the built-in `now_lms` theme instead of crashing. Fallback logic was added to every macro in `current_theme()`.

One more thing: the i18n layer was retired. The upstream project caught up with translation support. A fork-local workaround is dead weight once upstream ships. Delete it.

## Rate limiting atomicity (1.3.x)

Earlier in the day, a chain of releases (1.3.0 through 1.3.3) fixed a concurrency bug in the rate-limit counter. The old code read the current value, added one, and wrote it back. Under load, two requests would both read, both add one, and both write the same value. Lost increments. Race condition.

The fix uses native Redis INCR. Atomicity guaranteed by Redis itself. Fallback to the cachelib backend uses its native `inc()` method, same guarantee. The bug is closed.

## Email cutover: MXroute prep

On the infrastructure side, the MXroute migration of intentsolutions.io is underway. The DNS prep landed yesterday. Today, the cutover scripts went live: mailbox creation, a Porkbun DNS update step, and the cutover script itself. Mirrored into Plane so the ops team can track progress. Email cutovers are unforgiving. Every step is deliberate.

## Related posts

- [Temporary Is Not a Plan](/posts/temporary-is-not-a-plan/)
- [Do Not Blindly Restart](/posts/do-not-blindly-restart/)
- [Wrong Mode: Green Is Not a Gate](/posts/wrong-mode-green-is-not-a-gate/)
