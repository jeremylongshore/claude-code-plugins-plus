// @ts-check
import { defineConfig } from 'astro/config';
import tailwindcss from '@tailwindcss/vite';

// https://astro.build/config
export default defineConfig({
  site: 'https://tonsofskills.com',
  base: '/',
  redirects: {
    // Fix 404s from deleted Learning Lab pages (Jan 2026)
    '/learning/built-system-summary': '/learning/',
    '/learning/getting-started': '/learning/overview/',
    // Spotlight page retired 2026-04-22 — Hall of Fame lives on /community.
    '/spotlight': '/community#hall-of-fame',

    // ── Dead SaaS-pack skill slugs (added 2026-08-03) ──────────────────────
    // Umami showed the 404 page as the 3rd most-served page on the site: 176
    // pageviews over 7 days across 104 distinct URLs. Cross-referencing every
    // tracked path against dist/ showed 76% of them under /skills/, and every
    // one of those slugs is absent from skills-index.json — not a routing bug.
    //
    // Cause: the SaaS packs were rewritten. databricks-pack, for one, went from
    // ~18 generic template skills (hello-world, webhooks-events, common-errors,
    // install-auth …) to 5 bespoke ones. The old slugs stayed in Google's index
    // and in third-party links, so the traffic kept arriving and kept bouncing.
    //
    // Each dead slug redirects to its VENDOR PACK page rather than to /skills/,
    // because the pack page lists what actually replaced it — a generic index
    // makes the visitor start their search over, which is the drop-off we are
    // trying to close.
    //
    // Scanner noise (base64 probes, deep .md paths, malformed URLs) is
    // deliberately NOT listed: ~20 pageviews across 19 one-off URLs, none of
    // them human. A redirect table padded with bot probes is harder to maintain
    // and buys nothing.
    //
    // Regenerate the evidence with the Umami path metric + a dist/ cross-check;
    // do not hand-extend this list from guesses.
    '/downloads/plugins': '/cowork/',
    '/irsb-ecosystem': '/',
    '/learn/attio': '/learn/',
    '/learn/figma': '/learn/',
    '/legacy': '/',
    '/plugins/geepers': '/plugins/',
    '/plugins/langchain-pack': '/plugins/',
    '/plugins/portaljs/examples/openspending': '/plugins/portaljs/',
    '/posts/two-false-positive-fixes-same-root-cause': '/blog/',
    '/posts/verify-system-map-against-live-infra': '/blog/',
    '/skills/01-devops-basics': '/skills/',
    '/skills/amplify': '/skills/',
    '/skills/coreweave-migration-deep-dive': '/plugins/coreweave-pack/',
    '/skills/coreweave-rate-limits': '/plugins/coreweave-pack/',
    '/skills/coreweave-reference-architecture': '/plugins/coreweave-pack/',
    '/skills/coreweave-webhooks-events': '/plugins/coreweave-pack/',
    '/skills/databricks-bundle-medic/hooks/bundle-grant-retry.py': '/plugins/databricks-pack/',
    '/skills/databricks-ci-integration': '/plugins/databricks-pack/',
    '/skills/databricks-common-errors': '/plugins/databricks-pack/',
    '/skills/databricks-core-workflow-a': '/plugins/databricks-pack/',
    '/skills/databricks-cost-tuning': '/plugins/databricks-pack/',
    '/skills/databricks-data-handling': '/plugins/databricks-pack/',
    '/skills/databricks-deploy-integration': '/plugins/databricks-pack/',
    '/skills/databricks-enterprise-rbac': '/plugins/databricks-pack/',
    '/skills/databricks-hello-world': '/plugins/databricks-pack/',
    '/skills/databricks-install-auth': '/plugins/databricks-pack/',
    '/skills/databricks-local-dev-loop': '/plugins/databricks-pack/',
    '/skills/databricks-multi-env-setup': '/plugins/databricks-pack/',
    '/skills/databricks-observability': '/plugins/databricks-pack/',
    '/skills/databricks-performance-tuning': '/plugins/databricks-pack/',
    '/skills/databricks-prod-checklist': '/plugins/databricks-pack/',
    '/skills/databricks-reference-architecture': '/plugins/databricks-pack/',
    '/skills/databricks-security-basics': '/plugins/databricks-pack/',
    '/skills/databricks-upgrade-migration': '/plugins/databricks-pack/',
    '/skills/databricks-webhooks-events': '/plugins/databricks-pack/',
    '/skills/guidewire-common-errors': '/plugins/guidewire-pack/',
    '/skills/guidewire-cost-tuning': '/plugins/guidewire-pack/',
    '/skills/guidewire-debug-bundle': '/plugins/guidewire-pack/',
    '/skills/guidewire-deploy-integration': '/plugins/guidewire-pack/',
    '/skills/guidewire-performance-tuning': '/plugins/guidewire-pack/',
    '/skills/guidewire-rate-limits': '/plugins/guidewire-pack/',
    '/skills/guidewire-upgrade-migration': '/plugins/guidewire-pack/',
    '/skills/guidewire-webhooks-events': '/plugins/guidewire-pack/',
    '/skills/hubspot-architecture-variants': '/plugins/hubspot-pack/',
    '/skills/hubspot-ci-integration': '/plugins/hubspot-pack/',
    '/skills/hubspot-core-workflow-a': '/plugins/hubspot-pack/',
    '/skills/hubspot-enterprise-rbac': '/plugins/hubspot-pack/',
    '/skills/hubspot-incident-runbook': '/plugins/hubspot-pack/',
    '/skills/hubspot-migration-deep-dive': '/plugins/hubspot-pack/',
    '/skills/hubspot-multi-env-setup': '/plugins/hubspot-pack/',
    '/skills/hubspot-reliability-patterns': '/plugins/hubspot-pack/',
    '/skills/hubspot-upgrade-migration': '/plugins/hubspot-pack/',
    '/skills/langchain-core-workflow-a': '/skills/',
    '/skills/langchain-core-workflow-b': '/skills/',
    '/skills/langchain-data-handling-2': '/skills/',
    '/skills/langchain-debug-bundle-2': '/skills/',
    '/skills/langchain-enterprise-rbac-2': '/skills/',
    '/skills/langchain-hello-world': '/skills/',
    '/skills/langchain-incident-runbook-2': '/skills/',
    '/skills/langchain-performance-tuning-2': '/skills/',
    '/skills/langchain-prod-checklist': '/skills/',
    '/skills/langchain-reference-architecture-2': '/skills/',
    '/skills/langchain-security-basics-2': '/skills/',
    '/skills/langchain-upgrade-migration-2': '/skills/',
    '/skills/langchain-webhooks-events-2': '/skills/',
    '/skills/podium-core-workflow-a': '/plugins/podium-pack/',
    '/skills/podium-core-workflow-b': '/plugins/podium-pack/',
    '/skills/security': '/skills/',
    '/skills/windsurf-api-development': '/plugins/windsurf-pack/',
    '/skills/windsurf-audit-logging': '/plugins/windsurf-pack/',
    '/skills/windsurf-cascade-agents': '/plugins/windsurf-pack/',
    '/skills/windsurf-cascade-onboarding': '/plugins/windsurf-pack/',
    '/skills/windsurf-code-privacy': '/plugins/windsurf-pack/',
    '/skills/windsurf-debugging-ai': '/plugins/windsurf-pack/',
    '/skills/windsurf-flows-automation': '/plugins/windsurf-pack/',
    '/skills/windsurf-mcp-integration': '/plugins/windsurf-pack/',
    '/skills/windsurf-performance-profiling': '/plugins/windsurf-pack/',
    '/skills/windsurf-team-settings': '/plugins/windsurf-pack/',
    '/skills/windsurf-terminal-ai': '/plugins/windsurf-pack/',
    '/skills/windsurf-usage-analytics': '/plugins/windsurf-pack/',
    '/skills/windsurf-workspace-setup': '/plugins/windsurf-pack/',
  },
  build: {
    assets: '_astro',
    inlineStylesheets: 'auto'
  },
  output: 'static',
  compressHTML: false,  // Disabled: iOS Safari fails with lines > 5000 chars
  vite: {
    plugins: [tailwindcss()],
    build: {
      cssCodeSplit: true,
      rollupOptions: {
        output: {
          assetFileNames: '_astro/[name].[hash][extname]'
        }
      }
    }
  }
});
