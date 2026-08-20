/**
 * harness-lexicon.mjs — THE harness-name lexicon (blueprint 727, Epic 3).
 *
 * Harness names the portability gates recognize in prose claims. Owned here
 * in scripts/lib/ so both consumers — check-portability-claims.mjs (the
 * unbacked-portability ratchet, E3.11) and check-denylist-degradation.mjs
 * (the denylist silent-drop gate, E4.12) — import ONE definition. A second
 * copy of this list is exactly the drift class Epic 3 exists to end.
 */

/** [id, matcher] pairs — matcher tests a SKILL.md `compatibility` value. */
export const KNOWN_HARNESSES = [
  ['claude-code', /claude\s*code/i],
  ['codex', /\bcodex\b/i],
  ['openclaw', /open\s*claw/i],
  ['gemini-cli', /\bgemini\b/i],
  ['cursor', /\bcursor\b/i],
  ['copilot', /\bcopilot\b/i],
  ['windsurf', /\bwindsurf\b/i],
  ['aider', /\baider\b/i],
  ['cline', /\bcline\b/i],
];
