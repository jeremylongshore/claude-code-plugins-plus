import { describe, expect, it, vi } from 'vitest';
import {
  BlockedDestinationError,
  DEFAULT_MAX_RESPONSE_BYTES,
  DEFAULT_REQUEST_TIMEOUT_MS,
  MAX_REDIRECTS,
  RequestTimeoutError,
  ResponseTooLargeError,
  assertDestinationAllowed,
  configFromEnv,
  createGuardedFetch,
  createPinnedLookup,
  isPrivateAddress,
  shouldSendCredential,
  type GuardConfig,
} from '../src/net-guard.js';

function cfg(over: Partial<GuardConfig> = {}): GuardConfig {
  return {
    allowedHosts: new Set(),
    allowedDestinationOrigins: new Set(),
    allowPrivateHosts: false,
    allowTaskCancellation: false,
    authHeaderName: 'Authorization',
    authHeaderValue: '',
    requestTimeoutMs: DEFAULT_REQUEST_TIMEOUT_MS,
    maxResponseBytes: DEFAULT_MAX_RESPONSE_BYTES,
    ...over,
  };
}

/** Resolver stub so tests never touch real DNS. */
const resolves = (map: Record<string, string[]>) => async (h: string) => {
  if (!(h in map)) throw new Error(`no stub for ${h}`);
  return map[h];
};

describe('isPrivateAddress', () => {
  it.each([
    '127.0.0.1',
    '10.1.2.3',
    '192.168.1.1',
    '172.16.0.1',
    '172.31.255.255',
    '169.254.169.254', // cloud instance metadata — the classic SSRF target
    '100.64.0.1', // carrier-grade NAT / tailnet range
    '0.0.0.0',
    '::1',
    'fe80::1',
    'fd00::1',
    '::ffff:10.0.0.1', // IPv4-mapped IPv6 must not be a bypass
    '::ffff:a00:1', // mapped private IPv4 in hexadecimal form
  ])('flags %s as private', (addr) => {
    expect(isPrivateAddress(addr)).toBe(true);
  });

  it.each(['8.8.8.8', '1.1.1.1', '93.184.216.34', '172.32.0.1', '2606:4700::1111'])(
    'allows public %s',
    (addr) => {
      expect(isPrivateAddress(addr)).toBe(false);
    },
  );
});

describe('assertDestinationAllowed', () => {
  const encodedLoopbackHosts = [
    '127.0.0.1',
    '127.1',
    '2130706433',
    '0x7f000001',
    '0177.0.0.1',
    '[::1]',
    ['[::ffff:', [127, 0, 0, 1].join('.'), ']'].join(''),
  ];

  it.each(encodedLoopbackHosts.map((host) => `https://${host}/a2a`))(
    'refuses encoded literal loopback address %s',
    async (url) => {
    await expect(
      assertDestinationAllowed(new URL(url), cfg(), resolves({})),
    ).rejects.toBeInstanceOf(BlockedDestinationError);
    },
  );

  it('refuses localhost by name without a DNS round trip', async () => {
    await expect(
      assertDestinationAllowed(new URL('https://localhost:8443/a2a'), cfg(), resolves({})),
    ).rejects.toThrow(/loopback or local hostname/);
  });

  it('refuses credentials embedded in the URL', async () => {
    const credentialedUrl = new URL('https://agents.example.com/a2a');
    credentialedUrl.username = 'user';
    credentialedUrl.password = 'secret';
    await expect(
      assertDestinationAllowed(
        credentialedUrl,
        cfg(),
        resolves({ 'agents.example.com': ['93.184.216.34'] }),
      ),
    ).rejects.toThrow(/credentials embedded in URLs/);
  });

  it('refuses a public NAME that resolves inward — the rebinding-style bypass', async () => {
    await expect(
      assertDestinationAllowed(
        new URL('https://evil.example.com/a2a'),
        cfg(),
        resolves({ 'evil.example.com': ['169.254.169.254'] }),
      ),
    ).rejects.toThrow(/resolves to a private, loopback, link-local, or reserved address/);
  });

  it('refuses when ANY resolved address is private, not just the first', async () => {
    await expect(
      assertDestinationAllowed(
        new URL('https://mixed.example.com/a2a'),
        cfg(),
        resolves({ 'mixed.example.com': ['93.184.216.34', '10.0.0.5'] }),
      ),
    ).rejects.toBeInstanceOf(BlockedDestinationError);
  });

  it('refuses when DNS fails rather than falling open', async () => {
    await expect(
      assertDestinationAllowed(new URL('https://nx.example.com/a2a'), cfg(), resolves({})),
    ).rejects.toThrow(/DNS resolution failed/);
  });

  it('allows a public destination', async () => {
    await expect(
      assertDestinationAllowed(
        new URL('https://agents.example.com/a2a'),
        cfg(),
        resolves({ 'agents.example.com': ['93.184.216.34'] }),
      ),
    ).resolves.toBeUndefined();
  });

  it('permits private destinations only under the explicit opt-in', async () => {
    await expect(
      assertDestinationAllowed(
        new URL('http://127.0.0.1:41777/a2a'),
        cfg({ allowPrivateHosts: true }),
        resolves({}),
      ),
    ).resolves.toBeUndefined();
  });

  it('permits localhost names only under the explicit local-development opt-in', async () => {
    await expect(
      assertDestinationAllowed(
        new URL('http://localhost:41777/a2a'),
        cfg({ allowPrivateHosts: true }),
        resolves({ localhost: ['127.0.0.1'] }),
      ),
    ).resolves.toBeUndefined();
  });

  it('enforces the requested origin independently from credential scope', async () => {
    await expect(
      assertDestinationAllowed(
        new URL('https://attacker.example.com/a2a'),
        cfg({ allowedHosts: new Set(['attacker.example.com']) }),
        resolves({ 'attacker.example.com': ['93.184.216.35'] }),
        'https://partner.example.com',
      ),
    ).rejects.toThrow(/A2A_ALLOWED_DESTINATIONS/);
  });

  it('permits an exact cross-origin destination explicitly authorized by the operator', async () => {
    await expect(
      assertDestinationAllowed(
        new URL('https://delegate.example.com/a2a'),
        cfg({ allowedDestinationOrigins: new Set(['https://delegate.example.com']) }),
        resolves({ 'delegate.example.com': ['93.184.216.35'] }),
        'https://partner.example.com',
      ),
    ).resolves.toBeUndefined();
  });

  it('does not widen an allowed destination origin to a different port', async () => {
    await expect(
      assertDestinationAllowed(
        new URL('https://delegate.example.com:8443/a2a'),
        cfg({ allowedDestinationOrigins: new Set(['https://delegate.example.com']) }),
        resolves({ 'delegate.example.com': ['93.184.216.35'] }),
        'https://partner.example.com',
      ),
    ).rejects.toThrow(/cross-origin destination/);
  });
});

describe('shouldSendCredential — fail closed', () => {
  it('sends nothing when no credential is held', () => {
    expect(
      shouldSendCredential(
        new URL('https://a.example.com'),
        cfg({ allowedHosts: new Set(['a.example.com']) }),
      ),
    ).toBe(false);
  });

  it('sends nothing when a credential is held but NO allowlist is configured', () => {
    expect(
      shouldSendCredential(new URL('https://a.example.com'), cfg({ authHeaderValue: 'Bearer t' })),
    ).toBe(false);
  });

  it('does not send to a host outside the allowlist', () => {
    expect(
      shouldSendCredential(
        new URL('https://attacker.example.com'),
        cfg({ authHeaderValue: 'Bearer t', allowedHosts: new Set(['partner.example.com']) }),
      ),
    ).toBe(false);
  });

  it('does not send a credential over plaintext HTTP, even to a nominated host', () => {
    expect(
      shouldSendCredential(
        new URL('http://partner.example.com/a2a'),
        cfg({ authHeaderValue: 'Bearer t', allowedHosts: new Set(['partner.example.com']) }),
      ),
    ).toBe(false);
  });

  it('sends to a nominated host', () => {
    expect(
      shouldSendCredential(
        new URL('https://partner.example.com/a2a'),
        cfg({ authHeaderValue: 'Bearer t', allowedHosts: new Set(['partner.example.com']) }),
      ),
    ).toBe(true);
  });

  it('matches host case-insensitively', () => {
    expect(
      shouldSendCredential(
        new URL('https://Partner.Example.com/a2a'),
        cfg({ authHeaderValue: 'Bearer t', allowedHosts: new Set(['partner.example.com']) }),
      ),
    ).toBe(true);
  });
});

describe('createGuardedFetch', () => {
  const ok = () => new Response('{}', { status: 200 });
  type FetchArgs = [Request, RequestInit & { dispatcher?: unknown }];

  it('blocks the request before it reaches fetch', async () => {
    const inner = vi.fn(ok);
    const g = createGuardedFetch(cfg(), inner as unknown as typeof fetch, resolves({}));
    await expect(g('https://10.0.0.9/a2a')).rejects.toBeInstanceOf(BlockedDestinationError);
    expect(inner).not.toHaveBeenCalled();
  });

  it('does NOT attach a credential to a non-nominated host', async () => {
    const inner = vi.fn(ok);
    const g = createGuardedFetch(
      cfg({ authHeaderValue: 'Bearer secret', allowedHosts: new Set(['partner.example.com']) }),
      inner as unknown as typeof fetch,
      resolves({ 'attacker.example.com': ['93.184.216.34'] }),
    );
    await g('https://attacker.example.com/a2a');
    expect(inner).toHaveBeenCalledOnce();
    const [, init] = inner.mock.calls[0] as unknown as FetchArgs;
    expect(new Headers(init!.headers).get('Authorization')).toBeNull();
  });

  it('strips caller-supplied credentials from a non-nominated host', async () => {
    const inner = vi.fn(ok);
    const g = createGuardedFetch(
      cfg(),
      inner as unknown as typeof fetch,
      resolves({ 'attacker.example.com': ['93.184.216.34'] }),
    );
    await g('https://attacker.example.com/a2a', {
      headers: { Authorization: 'Bearer caller-secret', Cookie: 'session=secret' },
    });
    const [, init] = inner.mock.calls[0] as unknown as FetchArgs;
    expect(new Headers(init.headers).get('Authorization')).toBeNull();
    expect(new Headers(init.headers).get('Cookie')).toBeNull();
  });

  it('attaches the credential to a nominated host', async () => {
    const inner = vi.fn(ok);
    const g = createGuardedFetch(
      cfg({ authHeaderValue: 'Bearer secret', allowedHosts: new Set(['partner.example.com']) }),
      inner as unknown as typeof fetch,
      resolves({ 'partner.example.com': ['93.184.216.34'] }),
    );
    await g('https://partner.example.com/a2a');
    const [, init] = inner.mock.calls[0] as unknown as FetchArgs;
    expect(new Headers(init!.headers).get('Authorization')).toBe('Bearer secret');
  });

  it('honours a custom auth header name', async () => {
    const inner = vi.fn(ok);
    const g = createGuardedFetch(
      cfg({
        authHeaderName: 'X-Api-Key',
        authHeaderValue: 'k123',
        allowedHosts: new Set(['partner.example.com']),
      }),
      inner as unknown as typeof fetch,
      resolves({ 'partner.example.com': ['93.184.216.34'] }),
    );
    await g('https://partner.example.com/a2a');
    const [, init] = inner.mock.calls[0] as unknown as FetchArgs;
    expect(new Headers(init!.headers).get('X-Api-Key')).toBe('k123');
  });

  // --- Redirect handling. Each of these fails if `redirect: 'manual'` and the
  // per-hop re-check are removed, which is exactly what they exist to pin.
  const redirectTo = (loc: string, status = 302) =>
    new Response(null, { status, headers: { location: loc } });

  it("never lets the runtime follow redirects — always requests redirect: 'manual'", async () => {
    const inner = vi.fn(ok);
    const g = createGuardedFetch(
      cfg(),
      inner as unknown as typeof fetch,
      resolves({ 'partner.example.com': ['93.184.216.34'] }),
    );
    await g('https://partner.example.com/a2a');
    const [, init] = inner.mock.calls[0] as unknown as FetchArgs;
    expect(init?.redirect).toBe('manual');
    expect(init.dispatcher).toBeDefined();
  });

  it('refuses a redirect into cloud instance metadata (the 169.254.169.254 bypass)', async () => {
    const inner = vi
      .fn()
      .mockResolvedValueOnce(redirectTo('http://169.254.169.254/latest/meta-data/'))
      .mockResolvedValue(ok());
    const g = createGuardedFetch(
      cfg({ allowedDestinationOrigins: new Set(['http://169.254.169.254']) }),
      inner as unknown as typeof fetch,
      resolves({ 'partner.example.com': ['93.184.216.34'] }),
    );
    await expect(g('https://partner.example.com/a2a')).rejects.toBeInstanceOf(
      BlockedDestinationError,
    );
    // The hop was refused by the guard, never handed to fetch.
    expect(inner).toHaveBeenCalledOnce();
  });

  it('refuses a redirect to a host that resolves privately', async () => {
    const inner = vi
      .fn()
      .mockResolvedValueOnce(redirectTo('https://rebind.example.com/x'))
      .mockResolvedValue(ok());
    const g = createGuardedFetch(
      cfg({ allowedDestinationOrigins: new Set(['https://rebind.example.com']) }),
      inner as unknown as typeof fetch,
      resolves({
        'partner.example.com': ['93.184.216.34'],
        'rebind.example.com': ['10.0.0.9'],
      }),
    );
    await expect(g('https://partner.example.com/a2a')).rejects.toBeInstanceOf(
      BlockedDestinationError,
    );
  });

  it('drops the credential when a nominated host redirects to a non-nominated one', async () => {
    const inner = vi
      .fn()
      .mockResolvedValueOnce(redirectTo('https://attacker.example.com/steal'))
      .mockResolvedValue(ok());
    const g = createGuardedFetch(
      cfg({
        authHeaderValue: 'Bearer secret',
        allowedHosts: new Set(['partner.example.com']),
        allowedDestinationOrigins: new Set(['https://attacker.example.com']),
      }),
      inner as unknown as typeof fetch,
      resolves({
        'partner.example.com': ['93.184.216.34'],
        'attacker.example.com': ['93.184.216.35'],
      }),
    );
    await g('https://partner.example.com/a2a');
    expect(inner).toHaveBeenCalledTimes(2);
    const [, first] = inner.mock.calls[0] as unknown as FetchArgs;
    const [, second] = inner.mock.calls[1] as unknown as FetchArgs;
    expect(new Headers(first!.headers).get('Authorization')).toBe('Bearer secret');
    expect(new Headers(second!.headers).get('Authorization')).toBeNull();
  });

  it('drops the credential on an HTTPS-to-HTTP downgrade for a nominated host', async () => {
    const inner = vi
      .fn()
      .mockResolvedValueOnce(redirectTo('http://partner.example.com/plaintext'))
      .mockResolvedValue(ok());
    const g = createGuardedFetch(
      cfg({
        authHeaderValue: 'Bearer secret',
        allowedHosts: new Set(['partner.example.com']),
        allowedDestinationOrigins: new Set(['http://partner.example.com']),
      }),
      inner as unknown as typeof fetch,
      resolves({ 'partner.example.com': ['93.184.216.34'] }),
    );
    await g('https://partner.example.com/a2a');
    expect(inner).toHaveBeenCalledTimes(2);
    const [, first] = inner.mock.calls[0] as unknown as FetchArgs;
    const [, second] = inner.mock.calls[1] as unknown as FetchArgs;
    expect(new Headers(first!.headers).get('Authorization')).toBe('Bearer secret');
    expect(new Headers(second!.headers).get('Authorization')).toBeNull();
  });

  it('refuses a non-HTTP redirect scheme', async () => {
    const inner = vi.fn().mockResolvedValueOnce(redirectTo('file:///etc/passwd'));
    const g = createGuardedFetch(
      cfg(),
      inner as unknown as typeof fetch,
      resolves({ 'partner.example.com': ['93.184.216.34'] }),
    );
    await expect(g('https://partner.example.com/a2a')).rejects.toBeInstanceOf(
      BlockedDestinationError,
    );
  });

  it('blocks a public cross-origin redirect by default before the second fetch', async () => {
    const inner = vi
      .fn()
      .mockResolvedValueOnce(redirectTo('https://delegate.example.com/a2a'))
      .mockResolvedValue(ok());
    const g = createGuardedFetch(
      cfg(),
      inner as unknown as typeof fetch,
      resolves({
        'partner.example.com': ['93.184.216.34'],
        'delegate.example.com': ['93.184.216.35'],
      }),
    );
    await expect(g('https://partner.example.com/a2a')).rejects.toThrow(/cross-origin destination/);
    expect(inner).toHaveBeenCalledOnce();
  });

  it('does not treat the credential allowlist as cross-origin routing authority', async () => {
    const inner = vi
      .fn()
      .mockResolvedValueOnce(redirectTo('https://delegate.example.com/a2a'))
      .mockResolvedValue(ok());
    const g = createGuardedFetch(
      cfg({
        authHeaderValue: 'Bearer secret',
        allowedHosts: new Set(['partner.example.com', 'delegate.example.com']),
      }),
      inner as unknown as typeof fetch,
      resolves({
        'partner.example.com': ['93.184.216.34'],
        'delegate.example.com': ['93.184.216.35'],
      }),
    );
    await expect(g('https://partner.example.com/a2a')).rejects.toBeInstanceOf(
      BlockedDestinationError,
    );
    expect(inner).toHaveBeenCalledOnce();
  });

  it('caps redirect chains instead of looping forever', async () => {
    const inner = vi.fn(() => redirectTo('https://partner.example.com/next'));
    const g = createGuardedFetch(
      cfg(),
      inner as unknown as typeof fetch,
      resolves({ 'partner.example.com': ['93.184.216.34'] }),
    );
    await expect(g('https://partner.example.com/a2a')).rejects.toThrow(/exceeded \d+ redirects/);
    expect(inner.mock.calls.length).toBeLessThanOrEqual(MAX_REDIRECTS + 1);
  });

  it('follows a permitted redirect and returns the final response', async () => {
    const inner = vi
      .fn()
      .mockResolvedValueOnce(redirectTo('https://partner.example.com/moved'))
      .mockResolvedValue(new Response('{"ok":true}', { status: 200 }));
    const g = createGuardedFetch(
      cfg(),
      inner as unknown as typeof fetch,
      resolves({ 'partner.example.com': ['93.184.216.34'] }),
    );
    const res = await g('https://partner.example.com/a2a');
    expect(res.status).toBe(200);
    expect(inner).toHaveBeenCalledTimes(2);
  });

  it.each([301, 302, 303])(
    'degrades a Request-object POST on %i to a bodyless GET',
    async (status) => {
      const inner = vi
        .fn()
        .mockResolvedValueOnce(redirectTo('https://partner.example.com/result', status))
        .mockResolvedValue(ok());
      const g = createGuardedFetch(
        cfg(),
        inner as unknown as typeof fetch,
        resolves({ 'partner.example.com': ['93.184.216.34'] }),
      );
      const original = new Request('https://partner.example.com/a2a', {
        method: 'POST',
        body: '{"a":1}',
        headers: { 'content-type': 'application/json' },
      });
      await g(original);
      const [second] = inner.mock.calls[1] as unknown as FetchArgs;
      expect(second.method).toBe('GET');
      expect(second.body).toBeNull();
      expect(second.headers.get('content-type')).toBeNull();
    },
  );

  it.each([307, 308])('preserves a Request-object method and body across %i', async (status) => {
    const inner = vi
      .fn()
      .mockResolvedValueOnce(redirectTo('https://partner.example.com/retry', status))
      .mockResolvedValue(ok());
    const g = createGuardedFetch(
      cfg(),
      inner as unknown as typeof fetch,
      resolves({ 'partner.example.com': ['93.184.216.34'] }),
    );
    await g(
      new Request('https://partner.example.com/a2a', {
        method: 'POST',
        body: '{"a":1}',
      }),
    );
    const [second] = inner.mock.calls[1] as unknown as FetchArgs;
    expect(second.method).toBe('POST');
    expect(await second.clone().text()).toBe('{"a":1}');
  });

  it('times out even when the fetch implementation ignores its AbortSignal', async () => {
    const inner = vi.fn(() => new Promise<Response>(() => undefined));
    const g = createGuardedFetch(
      cfg({ requestTimeoutMs: 5 }),
      inner as unknown as typeof fetch,
      resolves({ 'partner.example.com': ['93.184.216.34'] }),
    );
    await expect(g('https://partner.example.com/a2a')).rejects.toBeInstanceOf(RequestTimeoutError);
  });

  it('times out a DNS resolver that never settles', async () => {
    const inner = vi.fn(ok);
    const g = createGuardedFetch(
      cfg({ requestTimeoutMs: 5 }),
      inner as unknown as typeof fetch,
      () => new Promise<string[]>(() => undefined),
    );
    await expect(g('https://partner.example.com/a2a')).rejects.toBeInstanceOf(RequestTimeoutError);
    expect(inner).not.toHaveBeenCalled();
  });

  it('rejects an oversized declared response before exposing its body', async () => {
    const inner = vi.fn(() =>
      Promise.resolve(new Response('{}', { headers: { 'content-length': '100' } })),
    );
    const g = createGuardedFetch(
      cfg({ maxResponseBytes: 10 }),
      inner as unknown as typeof fetch,
      resolves({ 'partner.example.com': ['93.184.216.34'] }),
    );
    await expect(g('https://partner.example.com/a2a')).rejects.toBeInstanceOf(
      ResponseTooLargeError,
    );
  });

  it('rejects an oversized streamed response even without Content-Length', async () => {
    const inner = vi.fn(() => Promise.resolve(new Response('123456')));
    const g = createGuardedFetch(
      cfg({ maxResponseBytes: 5 }),
      inner as unknown as typeof fetch,
      resolves({ 'partner.example.com': ['93.184.216.34'] }),
    );
    const response = await g('https://partner.example.com/a2a');
    await expect(response.text()).rejects.toBeInstanceOf(ResponseTooLargeError);
  });

  it('times out a response body that stalls after headers', async () => {
    const inner = vi.fn(() =>
      Promise.resolve(
        new Response(
          new ReadableStream({
            pull: () => new Promise<void>(() => undefined),
          }),
        ),
      ),
    );
    const g = createGuardedFetch(
      cfg({ requestTimeoutMs: 5 }),
      inner as unknown as typeof fetch,
      resolves({ 'partner.example.com': ['93.184.216.34'] }),
    );
    const response = await g('https://partner.example.com/a2a');
    await expect(response.text()).rejects.toBeInstanceOf(RequestTimeoutError);
  });
});

describe('DNS rebinding resistance at the connector lookup', () => {
  function lookupOnce(lookupFn: ReturnType<typeof createPinnedLookup>, host: string) {
    return new Promise<string>((resolve, reject) => {
      lookupFn(host, { all: false }, (error, address) => {
        if (error) reject(error);
        else resolve(address as string);
      });
    });
  }

  it('rejects a hostname that changes from public during preflight to private at connect', async () => {
    let call = 0;
    const resolver = async () => (++call === 1 ? ['93.184.216.34'] : ['169.254.169.254']);
    await assertDestinationAllowed(new URL('https://rebind.example/a2a'), cfg(), resolver);
    const connectorLookup = createPinnedLookup(cfg(), resolver);
    await expect(lookupOnce(connectorLookup, 'rebind.example')).rejects.toBeInstanceOf(
      BlockedDestinationError,
    );
  });

  it('blocks the changed DNS answer in the dispatcher used by the real fetch implementation', async () => {
    let call = 0;
    const resolver = async () => (++call === 1 ? ['93.184.216.34'] : ['169.254.169.254']);
    const guarded = createGuardedFetch(cfg(), fetch, resolver);
    await expect(guarded('http://rebind.invalid:41777/a2a')).rejects.toBeInstanceOf(
      BlockedDestinationError,
    );
    expect(call).toBe(2);
  });

  it('returns the already-validated address to the socket connector', async () => {
    const connectorLookup = createPinnedLookup(
      cfg(),
      resolves({ 'agent.example': ['93.184.216.34'] }),
    );
    await expect(lookupOnce(connectorLookup, 'agent.example')).resolves.toBe('93.184.216.34');
  });
});

describe('configFromEnv', () => {
  it('defaults to fail-closed: no allowlist, no private hosts, no credential', () => {
    const c = configFromEnv({});
    expect(c.allowedHosts.size).toBe(0);
    expect(c.allowedDestinationOrigins.size).toBe(0);
    expect(c.allowPrivateHosts).toBe(false);
    expect(c.allowTaskCancellation).toBe(false);
    expect(c.authHeaderValue).toBe('');
    expect(c.requestTimeoutMs).toBe(DEFAULT_REQUEST_TIMEOUT_MS);
    expect(c.maxResponseBytes).toBe(DEFAULT_MAX_RESPONSE_BYTES);
  });

  it('parses a comma-separated allowlist, trimming and lowercasing', () => {
    const c = configFromEnv({ A2A_ALLOWED_HOSTS: ' Partner.example.com , b.example.com ' });
    expect([...c.allowedHosts]).toEqual(['partner.example.com', 'b.example.com']);
  });

  it('formats a bearer token and prefers it over a raw api key', () => {
    const c = configFromEnv({ A2A_BEARER_TOKEN: 't', A2A_API_KEY: 'k' });
    expect(c.authHeaderValue).toBe('Bearer t');
  });

  it('uses a raw api key when no bearer token is set', () => {
    expect(configFromEnv({ A2A_API_KEY: 'k' }).authHeaderValue).toBe('k');
  });

  it('only opts into private hosts on an exact "1"', () => {
    expect(configFromEnv({ A2A_ALLOW_PRIVATE_HOSTS: 'true' }).allowPrivateHosts).toBe(false);
    expect(configFromEnv({ A2A_ALLOW_PRIVATE_HOSTS: '1' }).allowPrivateHosts).toBe(true);
  });

  it('only opts into task cancellation on an exact "1"', () => {
    expect(configFromEnv({ A2A_ALLOW_TASK_CANCELLATION: 'true' }).allowTaskCancellation).toBe(
      false,
    );
    expect(configFromEnv({ A2A_ALLOW_TASK_CANCELLATION: '1' }).allowTaskCancellation).toBe(true);
  });

  it('parses and canonicalizes the separate destination-origin allowlist', () => {
    const c = configFromEnv({
      A2A_ALLOWED_DESTINATIONS: ' HTTPS://Delegate.Example.com:443 ,http://other.example.com:8080 ',
    });
    expect([...c.allowedDestinationOrigins]).toEqual([
      'https://delegate.example.com',
      'http://other.example.com:8080',
    ]);
  });

  it.each([
    'https://delegate.example.com/path',
    'https://user@delegate.example.com',
    'file:///tmp/socket',
  ])('rejects non-origin destination entry %s', (value) => {
    expect(() => configFromEnv({ A2A_ALLOWED_DESTINATIONS: value })).toThrow(
      /bare HTTP\(S\) origins/,
    );
  });

  it('parses bounded timeout and response-size settings', () => {
    const c = configFromEnv({ A2A_REQUEST_TIMEOUT_MS: '250', A2A_MAX_RESPONSE_BYTES: '4096' });
    expect(c.requestTimeoutMs).toBe(250);
    expect(c.maxResponseBytes).toBe(4096);
    expect(() => configFromEnv({ A2A_REQUEST_TIMEOUT_MS: '0' })).toThrow(/between 1 and/);
    expect(() => configFromEnv({ A2A_MAX_RESPONSE_BYTES: 'unlimited' })).toThrow(
      /positive integer/,
    );
  });
});
