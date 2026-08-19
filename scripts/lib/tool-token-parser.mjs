/**
 * tool-token-parser.mjs — THE tool-token parser (blueprint 727, Epic 3 bead
 * 3.3: "one parser, one vocabulary").
 *
 * Every gate that reads a tool allowlist/denylist token — the capability
 * coverage check (E3.3), the adapter derive-check (E3.4), the thinness gate
 * (E3.5), the canonical vendor-literal gate (E3.10), and Epic 4's
 * runtime-safety gate (E4.2) — parses through THIS module. A second parser is
 * the anti-pattern this bead exists to end.
 *
 * A token parses to { kind, name, scope }:
 *   kind 'builtin'    name 'Bash'|'Read'|…     scope: the Bash(...) inner text
 *                                              split on commas, or null
 *   kind 'mcp'        name 'server' , tool     mcp__server__tool / mcp__server
 *   kind 'namespaced' name 'ns' , tool         ns:tool — custom platform tool
 *                                              names some packs declare
 *   kind 'unknown'    name: raw                anything else — NEVER silently
 *                                              accepted; callers must fail or
 *                                              disposition it
 */

const BUILTIN_SHAPE = /^([A-Z][A-Za-z]*)(?:\((.*)\))?$/;
const MCP_SHAPE = /^mcp__([A-Za-z0-9_-]+?)(?:__([A-Za-z0-9_-]+))?$/;
const NAMESPACED_SHAPE = /^([a-z][a-z0-9_-]*):([a-z][a-z0-9_]*)$/;

/** Split a CSV or YAML-list-derived allowlist string into raw tokens. */
export function splitTokenList(value) {
  if (Array.isArray(value)) return value.flatMap(splitTokenList);
  if (typeof value !== 'string') return [];
  // Commas inside Bash(...) scopes must not split the token.
  const tokens = [];
  let depth = 0;
  let current = '';
  for (const ch of value) {
    if (ch === '(') depth += 1;
    if (ch === ')') depth = Math.max(0, depth - 1);
    if (ch === ',' && depth === 0) {
      if (current.trim()) tokens.push(current.trim());
      current = '';
    } else {
      current += ch;
    }
  }
  if (current.trim()) tokens.push(current.trim());
  return tokens;
}

export function parseToken(raw) {
  const token = String(raw).trim();
  const mcp = token.match(MCP_SHAPE);
  if (mcp) {
    return { kind: 'mcp', name: mcp[1], tool: mcp[2] ?? null, raw: token };
  }
  const namespaced = token.match(NAMESPACED_SHAPE);
  if (namespaced) {
    return { kind: 'namespaced', name: namespaced[1], tool: namespaced[2], raw: token };
  }
  const builtin = token.match(BUILTIN_SHAPE);
  if (builtin) {
    const scope =
      builtin[2] === undefined
        ? null
        : builtin[2]
            .split(',')
            .map((s) => s.trim())
            .filter(Boolean);
    return { kind: 'builtin', name: builtin[1], scope, raw: token };
  }
  return { kind: 'unknown', name: token, raw: token };
}

export function parseTokenList(value) {
  return splitTokenList(value).map(parseToken);
}
