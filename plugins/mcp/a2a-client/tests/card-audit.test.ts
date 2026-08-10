import { describe, expect, it } from 'vitest';
import type { AgentCard } from '@a2a-js/sdk';
import { auditCard, claimsOf, REQUIRED_CARD_FIELDS } from '../servers/card-audit.js';

/** A minimal card that satisfies every required field, for tests to mutate. */
function validCard(overrides: Partial<AgentCard> = {}): AgentCard {
  return {
    name: 'Incident Summarizer',
    description: 'Summarizes incident timelines.',
    version: '1.2.0',
    supportedInterfaces: [
      {
        url: 'https://agents.example.com/a2a/v1',
        protocolBinding: 'JSONRPC',
        protocolVersion: '1.0',
        tenant: '',
      },
    ],
    capabilities: { streaming: false, pushNotifications: false, extensions: [] },
    defaultInputModes: ['text/plain'],
    defaultOutputModes: ['text/markdown'],
    skills: [
      {
        id: 'summarize',
        name: 'Summarize',
        description: 'Condense a timeline.',
        tags: ['incident'],
        examples: [],
        inputModes: [],
        outputModes: [],
        securityRequirements: [],
      },
    ],
    signatures: [],
    securitySchemes: {},
    securityRequirements: [],
    ...overrides,
  } as unknown as AgentCard;
}

describe('structure verdict', () => {
  it('accepts a card carrying every required field', () => {
    const audit = auditCard(validCard());
    expect(audit.structure).toBe('valid');
    expect(audit.missingFields).toEqual([]);
  });

  it.each(REQUIRED_CARD_FIELDS)('reports %s as missing when absent', (field) => {
    const card = validCard();
    delete (card as unknown as Record<string, unknown>)[field];
    const audit = auditCard(card);
    expect(audit.structure).toBe('malformed');
    expect(audit.missingFields).toContain(field);
  });

  it('treats an empty required array as missing, not as present-but-thin', () => {
    const audit = auditCard(validCard({ skills: [] } as Partial<AgentCard>));
    expect(audit.missingFields).toContain('skills');
  });
});

describe('interface findings', () => {
  it('flags a private-range interface URL for an operator decision', () => {
    const audit = auditCard(
      validCard({
        supportedInterfaces: [
          {
            url: 'https://10.0.0.7:8443/a2a/v1',
            protocolBinding: 'JSONRPC',
            protocolVersion: '1.0',
            tenant: '',
          },
        ],
      } as Partial<AgentCard>),
    );
    const finding = audit.findings.find((f) => f.claim === 'supportedInterfaces[0].url');
    expect(finding?.disposition).toBe('operator-decision-required');
    expect(finding?.finding).toMatch(/private-range|loopback/);
  });

  it.each(['https://localhost/a2a', 'https://127.0.0.1/a2a', 'https://192.168.1.4/a2a', 'https://172.20.0.9/a2a'])(
    'flags %s',
    (url) => {
      const audit = auditCard(
        validCard({
          supportedInterfaces: [
            { url, protocolBinding: 'JSONRPC', protocolVersion: '1.0', tenant: '' },
          ],
        } as Partial<AgentCard>),
      );
      expect(audit.operatorDecisionsRequired).toBeGreaterThan(0);
    },
  );

  it('flags a plaintext interface URL as a downgrade', () => {
    const audit = auditCard(
      validCard({
        supportedInterfaces: [
          {
            url: 'http://agents.example.com/a2a/v1',
            protocolBinding: 'JSONRPC',
            protocolVersion: '1.0',
            tenant: '',
          },
        ],
      } as Partial<AgentCard>),
    );
    expect(audit.findings.some((f) => f.finding === 'Non-HTTPS interface URL.')).toBe(true);
  });

  it('does not flag a public HTTPS interface', () => {
    const audit = auditCard(validCard());
    expect(audit.operatorDecisionsRequired).toBe(0);
  });

  it('flags an unparseable URL rather than silently skipping it', () => {
    const audit = auditCard(
      validCard({
        supportedInterfaces: [
          { url: 'grpc.example.com:443', protocolBinding: 'GRPC', protocolVersion: '1.0', tenant: '' },
        ],
      } as Partial<AgentCard>),
    );
    expect(audit.operatorDecisionsRequired).toBe(1);
  });
});

describe('required extensions', () => {
  it('surfaces an extension the card marks required', () => {
    const audit = auditCard(
      validCard({
        capabilities: {
          streaming: false,
          pushNotifications: false,
          extensions: [
            { uri: 'https://ext.example.com/v1', description: 'x', required: true, params: undefined },
          ],
        },
      } as unknown as Partial<AgentCard>),
    );
    expect(
      audit.findings.some((f) => f.claim === 'capabilities.extensions[].required'),
    ).toBe(true);
  });

  it('does not surface an optional extension', () => {
    const audit = auditCard(
      validCard({
        capabilities: {
          streaming: false,
          pushNotifications: false,
          extensions: [
            { uri: 'https://ext.example.com/v1', description: 'x', required: false, params: undefined },
          ],
        },
      } as unknown as Partial<AgentCard>),
    );
    expect(audit.operatorDecisionsRequired).toBe(0);
  });
});

describe('per-skill security overrides', () => {
  const agentLevel = [{ schemes: { oauth: { list: ['read'] } } }];

  it('flags a skill whose override drops an agent-level scheme', () => {
    const card = validCard({ securityRequirements: agentLevel } as unknown as Partial<AgentCard>);
    card.skills[0].securityRequirements = [
      { schemes: { apiKey: { list: [] } } },
    ] as unknown as AgentCard['skills'][number]['securityRequirements'];
    const audit = auditCard(card);
    const finding = audit.findings.find((f) => f.claim.startsWith('skills[summarize]'));
    expect(finding?.disposition).toBe('operator-decision-required');
    expect(finding?.finding).toContain('oauth');
  });

  it('does not flag a skill with no override — the agent-level baseline applies', () => {
    const card = validCard({ securityRequirements: agentLevel } as unknown as Partial<AgentCard>);
    expect(auditCard(card).operatorDecisionsRequired).toBe(0);
  });

  it('does not flag a skill whose override preserves the agent-level schemes', () => {
    const card = validCard({ securityRequirements: agentLevel } as unknown as Partial<AgentCard>);
    card.skills[0].securityRequirements = [
      { schemes: { oauth: { list: ['read', 'write'] } } },
    ] as unknown as AgentCard['skills'][number]['securityRequirements'];
    expect(auditCard(card).operatorDecisionsRequired).toBe(0);
  });
});

describe('signature honesty', () => {
  it('reports absent when the card carries no signatures', () => {
    expect(auditCard(validCard()).signatureStatus).toBe('absent');
  });

  it('reports unverified — never verified — when signatures are present', () => {
    const audit = auditCard(
      validCard({
        signatures: [{ protected: 'eyJ', signature: 'MEU', header: undefined }],
      } as unknown as Partial<AgentCard>),
    );
    expect(audit.signatureStatus).toBe('unverified');
    expect(audit.signatureStatus).not.toBe('verified');
  });
});

describe('card-named fetch targets', () => {
  it('reports documentationUrl without resolving it', () => {
    const audit = auditCard(
      validCard({ documentationUrl: 'https://docs.example.com' } as Partial<AgentCard>),
    );
    const finding = audit.findings.find((f) => f.claim === 'documentationUrl');
    expect(finding?.disposition).toBe('reported');
    expect(finding?.finding).toContain('not resolved');
  });
});

describe('claims reporting', () => {
  it('labels the first interface preferred and the rest fallbacks', () => {
    const claims = claimsOf(
      validCard({
        supportedInterfaces: [
          { url: 'https://a.example.com', protocolBinding: 'JSONRPC', protocolVersion: '1.0', tenant: '' },
          { url: 'https://b.example.com', protocolBinding: 'HTTP+JSON', protocolVersion: '1.0', tenant: '' },
        ],
      } as Partial<AgentCard>),
    );
    expect(claims.interfaces[0].preference).toBe('preferred');
    expect(claims.interfaces[1].preference).toBe('fallback-1');
  });

  it('reports absent capabilities as false rather than assuming support', () => {
    const claims = claimsOf(validCard({ capabilities: {} } as unknown as Partial<AgentCard>));
    expect(claims.capabilitiesClaimed.streaming).toBe(false);
    expect(claims.capabilitiesClaimed.pushNotifications).toBe(false);
    expect(claims.capabilitiesClaimed.extendedAgentCard).toBe(false);
  });

  it('emits no trust score or overall verdict field', () => {
    const claims = claimsOf(validCard()) as Record<string, unknown>;
    const audit = auditCard(validCard()) as unknown as Record<string, unknown>;
    for (const key of ['trustScore', 'trusted', 'safe', 'verdict']) {
      expect(claims).not.toHaveProperty(key);
      expect(audit).not.toHaveProperty(key);
    }
  });
});
