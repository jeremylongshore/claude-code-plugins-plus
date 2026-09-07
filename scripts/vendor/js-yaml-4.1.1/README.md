# js-yaml 4.1.1 vendored distribution

This directory contains the upstream ESM distribution used by the deterministic,
install-free `generated-content-drift` CI job.

- Upstream: <https://github.com/nodeca/js-yaml>
- Package: `js-yaml@4.1.1`
- Source file: `dist/js-yaml.mjs` from the published npm package
- SHA-256: `efbc45850bf15f0c8ee3434983f512be656002d7507dc292c7ade4449b5d57fa`
- License: MIT; preserved in `LICENSE`

Do not edit `js-yaml.mjs` by hand. Upgrades must replace it with the exact
published distribution, preserve the corresponding license, update this receipt,
and update the pinned hash assertion in `scripts/generated-content-ci.test.mjs`.
