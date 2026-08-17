/**
 * Machine-readable ownership registry for generated projections and retained
 * point-in-time evidence. Consumers must use this registry instead of growing
 * private path lists.
 */

export const GENERATED_ARTIFACT_REGISTRY = [
  {
    id: 'epic-1-scorecard',
    kind: 'generated_projection',
    tracking: 'tracked',
    pattern: /^000-docs\/742-RA-DATA-epic-1-scorecard\.json$/,
    canonical: 'scripts/measure-epic-1.mjs',
    regenerate: 'pnpm run measure:e1',
    postprocess: 'pnpm run normalize:dead-domain-projections',
    why: 'governed Epic 1 measurement output',
  },
  {
    id: 'marketplace-build-data',
    kind: 'generated_projection',
    tracking: 'tracked',
    pattern: /^marketplace\/src\/data\/.*\.json$/,
    canonical: 'marketplace build inputs and scripts',
    regenerate: 'cd marketplace && npm run build',
    postprocess: 'pnpm run normalize:dead-domain-projections',
    why: 'tracked website build data pending the Epic 1 generated-artifact disposition',
  },
  {
    id: 'marketplace-plugin-content',
    kind: 'generated_projection',
    tracking: 'tracked',
    pattern: /^marketplace\/src\/content\/plugins\/.*\.json$/,
    canonical: '.claude-plugin/marketplace.extended.json and plugin source files',
    regenerate: 'cd marketplace && node generate-content.js',
    postprocess: 'pnpm run normalize:dead-domain-projections',
    why: 'Astro plugin content generated from repository plugin metadata',
  },
  {
    id: 'plugin-package-manifests',
    kind: 'generated_projection',
    tracking: 'tracked',
    pattern: /^plugins\/[^/]+\/[^/]+\/package\.json$/,
    canonical: 'plugin.json and repository package policy',
    regenerate: 'node scripts/generate-plugin-package-jsons.mjs',
    postprocess: 'pnpm run normalize:dead-domain-projections',
    why: 'package tracking manifests generated from plugin metadata',
  },
  {
    id: 'curated-skill-mirror',
    kind: 'generated_projection',
    tracking: 'tracked',
    pattern: /^skills\/\.curated\//,
    canonical: 'plugin skill sources selected by freshie/grades.csv',
    regenerate: 'python3 freshie/scripts/promote-to-curated.py',
    why: 'curated skills.sh projection',
  },
  {
    id: 'marketplace-public-data',
    kind: 'generated_projection',
    tracking: 'untracked',
    pattern: /^marketplace\/public\/data\/.*\.json$/,
    pathspec: ':(top)marketplace/public/data/*.json',
    glob: 'marketplace/public/data/*.json',
    canonical: 'marketplace/src/data/*.json',
    regenerate: 'cd marketplace && npm run build   (or: node scripts/copy-public-data.mjs)',
    why: 'runtime static-asset copy of the canonical build data; ~28.5MB when tracked',
  },
  {
    id: 'cowork-downloads',
    kind: 'generated_projection',
    tracking: 'untracked',
    pattern: /^marketplace\/public\/downloads\//,
    pathspec: ':(top)marketplace/public/downloads/**',
    glob: 'marketplace/public/downloads/**',
    canonical: '.claude-plugin/marketplace.extended.json',
    regenerate: 'cd marketplace && npm run build   (cowork:zips)',
    why: 'cowork zips are rebuilt from the catalog on every build',
  },
  {
    id: 'freshie-run-snapshots',
    kind: 'historical_snapshot',
    tracking: 'tracked',
    pattern: /^freshie\/exports\/run-[1-9]\d*\//,
    canonical: 'freshie/exports/run-N/csv-exports/INDEX.md and its recorded commit',
    regenerate: null,
    why: 'point-in-time discovery evidence; preserve observed values byte-for-byte',
  },
];

export function artifactRegistration(candidate) {
  const path = String(candidate).replaceAll('\\', '/').replace(/^\.\//, '');
  const matches = GENERATED_ARTIFACT_REGISTRY.filter((entry) => entry.pattern.test(path));
  if (matches.length > 1) {
    throw new Error(
      `generated-artifact registry overlap for ${path}: ${matches.map((entry) => entry.id).join(', ')}`,
    );
  }
  return matches[0] ?? null;
}

export function artifactRegistrationsByTracking(tracking) {
  return GENERATED_ARTIFACT_REGISTRY.filter((entry) => entry.tracking === tracking);
}
