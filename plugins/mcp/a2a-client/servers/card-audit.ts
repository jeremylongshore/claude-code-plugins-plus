/**
 * Pure agent-card auditing. No I/O, no network, no side effects — imported by the MCP
 * server and exercised directly by the tests.
 *
 * The governing rule: a card is an externally-authored manifest fetched from outside the
 * trust boundary. Everything here REPORTS what a card claims. Nothing here converts a
 * claim into local authority, and there is deliberately no trust score — a single number
 * would invite automating exactly the decision that has to stay with an operator.
 */

import type { AgentCard } from '@a2a-js/sdk';

export const REQUIRED_CARD_FIELDS = [
  'name',
  'description',
  'version',
  'supportedInterfaces',
  'capabilities',
  'defaultInputModes',
  'defaultOutputModes',
  'skills',
] as const;

/** Loopback, private, link-local, and carrier-grade ranges an outside card should not name. */
const PRIVATE_HOST = /^(localhost$|127\.|10\.|192\.168\.|169\.254\.|::1$|172\.(1[6-9]|2\d|3[01])\.)/;

export type Disposition = 'reported' | 'operator-decision-required';

export interface CardFinding {
  claim: string;
  value: string;
  finding: string;
  disposition: Disposition;
}

export interface CardAudit {
  structure: 'valid' | 'malformed';
  missingFields: string[];
  findings: CardFinding[];
  /** Three-valued in the spec. This module never verifies, so it never reports "verified". */
  signatureStatus: 'absent' | 'unverified';
  operatorDecisionsRequired: number;
}

export function auditCard(card: AgentCard): CardAudit {
  const record = card as unknown as Record<string, unknown>;
  const missingFields = REQUIRED_CARD_FIELDS.filter((f) => {
    const v = record[f];
    return v === undefined || v === null || (Array.isArray(v) && v.length === 0);
  });

  const findings: CardFinding[] = [
    ...interfaceFindings(card),
    ...requiredExtensionFindings(card),
    ...skillOverrideFindings(card),
    ...fetchTargetFindings(card),
  ];

  return {
    structure: missingFields.length === 0 ? 'valid' : 'malformed',
    missingFields,
    findings,
    signatureStatus: (card.signatures ?? []).length > 0 ? 'unverified' : 'absent',
    operatorDecisionsRequired: findings.filter(
      (f) => f.disposition === 'operator-decision-required',
    ).length,
  };
}

function interfaceFindings(card: AgentCard): CardFinding[] {
  const out: CardFinding[] = [];
  for (const [i, iface] of (card.supportedInterfaces ?? []).entries()) {
    const claim = `supportedInterfaces[${i}].url`;
    let host: string;
    try {
      host = new URL(iface.url).hostname;
    } catch {
      out.push({
        claim,
        value: iface.url,
        finding: 'URL does not parse as an absolute URL; may be a gRPC host:port or malformed.',
        disposition: 'operator-decision-required',
      });
      continue;
    }
    if (PRIVATE_HOST.test(host)) {
      out.push({
        claim,
        value: iface.url,
        finding: 'Directs traffic to a loopback or private-range host.',
        disposition: 'operator-decision-required',
      });
    } else if (!iface.url.startsWith('https://')) {
      out.push({
        claim,
        value: iface.url,
        finding: 'Non-HTTPS interface URL.',
        disposition: 'operator-decision-required',
      });
    }
  }
  return out;
}

function requiredExtensionFindings(card: AgentCard): CardFinding[] {
  return (card.capabilities?.extensions ?? [])
    .filter((e) => e.required)
    .map((e) => ({
      claim: 'capabilities.extensions[].required',
      value: e.uri,
      finding: 'Card requires the client to support this extension to interoperate.',
      disposition: 'operator-decision-required' as const,
    }));
}

/**
 * Per-skill securityRequirements OVERRIDE the agent-level list. A card that reads strict
 * at the top can still expose one skill behind a weaker requirement, so the audit runs at
 * the skill level rather than only the agent level.
 */
function skillOverrideFindings(card: AgentCard): CardFinding[] {
  const agentSchemes = new Set(
    (card.securityRequirements ?? []).flatMap((r) => Object.keys(r.schemes ?? {})),
  );
  if (agentSchemes.size === 0) return [];

  const out: CardFinding[] = [];
  for (const skill of card.skills ?? []) {
    const declared = skill.securityRequirements ?? [];
    if (declared.length === 0) continue; // no override — agent-level applies
    const skillSchemes = new Set(declared.flatMap((r) => Object.keys(r.schemes ?? {})));
    const dropped = [...agentSchemes].filter((s) => !skillSchemes.has(s));
    if (dropped.length > 0) {
      out.push({
        claim: `skills[${skill.id}].securityRequirements`,
        value: skillSchemes.size ? [...skillSchemes].join(', ') : '(none)',
        finding: `Per-skill override drops agent-level scheme(s): ${dropped.join(', ')}.`,
        disposition: 'operator-decision-required',
      });
    }
  }
  return out;
}

/** Card-named fetch targets are reported as strings and never resolved on the card's say-so. */
function fetchTargetFindings(card: AgentCard): CardFinding[] {
  const out: CardFinding[] = [];
  for (const field of ['documentationUrl', 'iconUrl'] as const) {
    const value = card[field];
    if (value) {
      out.push({
        claim: field,
        value,
        finding: 'Card-named fetch target. Reported as a string; not resolved by this server.',
        disposition: 'reported',
      });
    }
  }
  return out;
}

/** Claims are labelled and enumerated, never merged into a single verdict. */
export function claimsOf(card: AgentCard) {
  return {
    identity: { name: card.name, version: card.version, provider: card.provider?.organization },
    interfaces: (card.supportedInterfaces ?? []).map((i, idx) => ({
      preference: idx === 0 ? 'preferred' : `fallback-${idx}`,
      url: i.url,
      protocolBinding: i.protocolBinding,
      protocolVersion: i.protocolVersion,
      tenant: i.tenant || undefined,
    })),
    capabilitiesClaimed: {
      streaming: card.capabilities?.streaming ?? false,
      pushNotifications: card.capabilities?.pushNotifications ?? false,
      extendedAgentCard: card.capabilities?.extendedAgentCard ?? false,
      extensions: (card.capabilities?.extensions ?? []).map((e) => ({
        uri: e.uri,
        required: e.required,
      })),
    },
    skillsClaimed: (card.skills ?? []).map((s) => ({ id: s.id, name: s.name, tags: s.tags })),
    securitySchemesClaimed: Object.keys(card.securitySchemes ?? {}),
  };
}
