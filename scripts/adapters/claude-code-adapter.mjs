/**
 * claude-code-adapter.mjs — the claude-code harness adapter's resolution
 * seams (blueprint 727, Epic 3 beads 3.8 and 3.9).
 *
 * THE canonical layer is harness-free: it carries `model_class` tiers and the
 * portable `${SKILL_DIR}` variable. This module is where the claude-code
 * harness resolves both — and it FAILS CLOSED (§ 5.4 rule 4): an
 * unresolvable tier or an unknown runtime variable throws; silent
 * substitution is exactly how "model-agnostic" becomes a claim exceeding its
 * evidence.
 *
 * E3.8 — model class resolution. The claude-code frontmatter `model:` field
 * accepts harness aliases (opus / sonnet / haiku / fable / inherit); the
 * adapter maps canonical tiers onto them:
 *
 *   reasoning-high → opus      (deep-reasoning alias)
 *   balanced       → sonnet    (the corpus default: 268 of 321 agent models)
 *   fast           → haiku
 *
 * E3.9 — runtime bindings. Canonical bodies write `${SKILL_DIR}`; this
 * adapter emits the Claude-branded `${CLAUDE_SKILL_DIR}` (and
 * `${PLUGIN_ROOT}` → `${CLAUDE_PLUGIN_ROOT}`). An unknown `${…_DIR}`-shaped
 * variable in canonical text throws rather than passing through unmapped.
 */

export const ADAPTER_ID = 'claude-code';

const MODEL_CLASS_MAP = {
  'reasoning-high': 'opus',
  balanced: 'sonnet',
  fast: 'haiku',
};

/** E3.8 — resolve a canonical model tier to this harness's model alias. */
export function resolveModelClass(modelClass) {
  const resolved = MODEL_CLASS_MAP[modelClass];
  if (!resolved) {
    throw new Error(
      `claude-code adapter: no model registered for model_class "${modelClass}" — ` +
        'an adapter with no matching model errors (fail closed, blueprint § 5.4 rule 4)',
    );
  }
  return resolved;
}

const RUNTIME_BINDINGS = {
  SKILL_DIR: 'CLAUDE_SKILL_DIR',
  PLUGIN_ROOT: 'CLAUDE_PLUGIN_ROOT',
};

/**
 * E3.9 — rewrite portable runtime variables into this harness's spelling.
 * Unknown portable variables of the recognized shape throw; harness-branded
 * variables must never appear in canonical input (that is E3.10's gate, but
 * this seam refuses them too rather than double-branding).
 */
export function bindRuntimeVariables(text) {
  const out = text.replace(/\$\{([A-Z_]+)\}/g, (whole, name) => {
    if (RUNTIME_BINDINGS[name]) return '${' + RUNTIME_BINDINGS[name] + '}';
    if (name.startsWith('CLAUDE_')) {
      throw new Error(
        `claude-code adapter: canonical text already contains harness-branded \${${name}} — ` +
          'canonical bodies use the portable ${SKILL_DIR} family only',
      );
    }
    if (name.endsWith('_DIR') || name.endsWith('_ROOT')) {
      throw new Error(
        `claude-code adapter: unknown portable variable \${${name}} — ` +
          'add a runtime binding or fix the canonical text (fail closed)',
      );
    }
    return whole; // ordinary env-var interpolation is not a runtime binding
  });
  return out;
}
