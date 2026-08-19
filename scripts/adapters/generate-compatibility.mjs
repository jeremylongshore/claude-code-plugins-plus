#!/usr/bin/env node
/**
 * generate-compatibility.mjs — emit the frontmatter `compatibility` string as
 * a deterministic projection of the canonical contract (blueprint 727, Epic 3
 * bead 3.4).
 *
 * `compatibility` is one of the IS 8 required frontmatter fields and stays
 * REQUIRED (ALWAYS_REQUIRED is untouched) — what changes is its PROVENANCE:
 * for a skill that carries a skill-card, the string is GENERATED from
 * `adapters[]` + `requires.services[]` + `unsupported[]`, never hand-authored.
 * Prose is unenforceable; a claim must be machine-checkable to be honest
 * (§ 5.3). The canonical contract schema already rejects a hand-authored
 * `compatibility` key inside skill-card.yaml; this module is the ONLY
 * sanctioned writer of the projected string.
 *
 * The output is stable, human-readable, and round-trippable by prefix:
 * every generated string begins with the marker "Declared adapters:" so
 * E3.11's ratchet can distinguish generated projections from legacy
 * hand-authored prose during the backfill.
 */

const ADAPTER_DISPLAY = {
  'claude-code': 'Claude Code',
};

export const GENERATED_PREFIX = 'Declared adapters:';

/**
 * Project the compatibility string from a validated skill-card object.
 * Deterministic: same contract → same string, key order irrelevant.
 */
export function generateCompatibility(card) {
  if (!card || !Array.isArray(card.adapters) || card.adapters.length === 0) {
    throw new Error('compatibility projection requires a validated skill-card with adapters[]');
  }
  const adapters = [...card.adapters]
    .sort()
    .map((a) => ADAPTER_DISPLAY[a] ?? a)
    .join(', ');
  const parts = [`${GENERATED_PREFIX} ${adapters}.`];

  const services = card.requires?.services ?? [];
  if (services.length > 0) {
    const svc = [...services]
      .map((s) => `${s.kind} ${s.name}${s.env?.length ? ` (${[...s.env].sort().join(', ')})` : ''}`)
      .sort()
      .join('; ');
    parts.push(`Requires: ${svc}.`);
  }

  const unsupported = card.unsupported ?? [];
  if (unsupported.length > 0) {
    const un = [...unsupported]
      .map((u) => `${u.capability} on ${u.adapter} (${u.degradation ?? 'fail-closed'})`)
      .sort()
      .join('; ');
    parts.push(`Unsupported: ${un}.`);
  }

  return parts.join(' ');
}

/** True when a frontmatter compatibility string is a generated projection. */
export function isGeneratedCompatibility(value) {
  return typeof value === 'string' && value.startsWith(GENERATED_PREFIX);
}
