/**
 * Fail-closed outbound guard for every A2A HTTP request.
 *
 * The same validated DNS answer is handed to Undici's socket connector. This is
 * intentionally stronger than a preflight lookup followed by an unrelated runtime
 * lookup: there is no DNS-rebinding gap between policy evaluation and connect.
 */

import { lookup } from 'node:dns/promises';
import type { LookupFunction } from 'node:net';
import { isIP } from 'node:net';
import ipaddr from 'ipaddr.js';
import { Agent, type Dispatcher } from 'undici';

export interface GuardConfig {
  /** Hosts a configured credential may be sent to. Empty means no credential is sent. */
  allowedHosts: Set<string>;
  /** Cross-origin destinations explicitly authorized by the operator. */
  allowedDestinationOrigins: Set<string>;
  /** Permit private destinations for deliberate local development only. */
  allowPrivateHosts: boolean;
  /** Destructive task cancellation remains disabled unless explicitly enabled. */
  allowTaskCancellation: boolean;
  authHeaderName: string;
  authHeaderValue: string;
  requestTimeoutMs: number;
  maxResponseBytes: number;
}

export type Resolver = (host: string) => Promise<string[]>;

interface GuardedRequestInit extends RequestInit {
  dispatcher?: Dispatcher;
}

const SENSITIVE_HEADERS = ['authorization', 'proxy-authorization', 'cookie'];
const BODY_HEADERS = [
  'content-encoding',
  'content-language',
  'content-length',
  'content-location',
  'content-type',
];

export const DEFAULT_REQUEST_TIMEOUT_MS = 30_000;
export const DEFAULT_MAX_RESPONSE_BYTES = 2 * 1024 * 1024;
const MAX_CONFIGURED_TIMEOUT_MS = 5 * 60_000;
const MAX_CONFIGURED_RESPONSE_BYTES = 64 * 1024 * 1024;

function positiveIntegerSetting(
  name: string,
  raw: string | undefined,
  fallback: number,
  maximum: number,
): number {
  if (raw === undefined || raw === '') return fallback;
  if (!/^\d+$/.test(raw)) throw new Error(`${name} must be a positive integer`);
  const parsed = Number(raw);
  if (!Number.isSafeInteger(parsed) || parsed < 1 || parsed > maximum) {
    throw new Error(`${name} must be between 1 and ${maximum}`);
  }
  return parsed;
}

function configuredDestinationOrigins(raw: string | undefined): Set<string> {
  const origins = new Set<string>();
  for (const value of (raw ?? '')
    .split(',')
    .map((item) => item.trim())
    .filter(Boolean)) {
    let url: URL;
    try {
      url = new URL(value);
    } catch {
      throw new Error(`A2A_ALLOWED_DESTINATIONS contains an invalid origin: ${value}`);
    }
    if (
      (url.protocol !== 'http:' && url.protocol !== 'https:') ||
      url.username ||
      url.password ||
      url.pathname !== '/' ||
      url.search ||
      url.hash
    ) {
      throw new Error(
        `A2A_ALLOWED_DESTINATIONS entries must be bare HTTP(S) origins without credentials, paths, query strings, or fragments: ${value}`,
      );
    }
    origins.add(url.origin);
  }
  return origins;
}

export function configFromEnv(env: NodeJS.ProcessEnv = process.env): GuardConfig {
  const bearer = env.A2A_BEARER_TOKEN ?? '';
  const apiKey = env.A2A_API_KEY ?? '';
  return {
    allowedHosts: new Set(
      (env.A2A_ALLOWED_HOSTS ?? '')
        .split(',')
        .map((host) => host.trim().toLowerCase())
        .filter(Boolean),
    ),
    allowedDestinationOrigins: configuredDestinationOrigins(env.A2A_ALLOWED_DESTINATIONS),
    allowPrivateHosts: env.A2A_ALLOW_PRIVATE_HOSTS === '1',
    allowTaskCancellation: env.A2A_ALLOW_TASK_CANCELLATION === '1',
    authHeaderName: env.A2A_AUTH_HEADER_NAME ?? 'Authorization',
    authHeaderValue: bearer ? `Bearer ${bearer}` : apiKey,
    requestTimeoutMs: positiveIntegerSetting(
      'A2A_REQUEST_TIMEOUT_MS',
      env.A2A_REQUEST_TIMEOUT_MS,
      DEFAULT_REQUEST_TIMEOUT_MS,
      MAX_CONFIGURED_TIMEOUT_MS,
    ),
    maxResponseBytes: positiveIntegerSetting(
      'A2A_MAX_RESPONSE_BYTES',
      env.A2A_MAX_RESPONSE_BYTES,
      DEFAULT_MAX_RESPONSE_BYTES,
      MAX_CONFIGURED_RESPONSE_BYTES,
    ),
  };
}

function normalizedHost(host: string): string {
  return host
    .toLowerCase()
    .replace(/^\[|\]$/g, '')
    .split('%', 1)[0];
}

/** True for every non-public IP range, including mapped IPv4-in-IPv6 values. */
export function isPrivateAddress(address: string): boolean {
  try {
    let parsed = ipaddr.parse(normalizedHost(address));
    if (parsed instanceof ipaddr.IPv6 && parsed.isIPv4MappedAddress()) {
      parsed = parsed.toIPv4Address();
    }
    return parsed.range() !== 'unicast';
  } catch {
    return true;
  }
}

export class BlockedDestinationError extends Error {
  readonly code = 'DESTINATION_BLOCKED';

  constructor(host: string, reason: string) {
    super(
      `a2a-client refused an outbound request to "${host}": ${reason}. ` +
        'Set A2A_ALLOW_PRIVATE_HOSTS=1 only for deliberate local development.',
    );
    this.name = 'BlockedDestinationError';
  }
}

export class RequestTimeoutError extends Error {
  readonly code = 'REQUEST_TIMEOUT';

  constructor(timeoutMs: number) {
    super(`a2a-client aborted the outbound request after ${timeoutMs}ms`);
    this.name = 'RequestTimeoutError';
  }
}

export class ResponseTooLargeError extends Error {
  readonly code = 'RESPONSE_TOO_LARGE';

  constructor(limit: number) {
    super(`a2a-client refused a response larger than ${limit} bytes`);
    this.name = 'ResponseTooLargeError';
  }
}

function validateUrlShape(url: URL, cfg: GuardConfig): string {
  if (url.protocol !== 'http:' && url.protocol !== 'https:') {
    throw new BlockedDestinationError(url.protocol, 'only HTTP and HTTPS are permitted');
  }
  if (url.username || url.password) {
    throw new BlockedDestinationError(url.hostname, 'credentials embedded in URLs are forbidden');
  }
  const host = normalizedHost(url.hostname);
  if (
    !cfg.allowPrivateHosts &&
    (host === 'localhost' || host.endsWith('.localhost') || host.endsWith('.local'))
  ) {
    throw new BlockedDestinationError(host, 'loopback or local hostname');
  }
  return host;
}

async function defaultResolve(host: string): Promise<string[]> {
  const records = await lookup(host, { all: true, verbatim: true });
  return records.map((record) => record.address);
}

async function validatedAddresses(
  host: string,
  cfg: GuardConfig,
  resolver: Resolver,
): Promise<string[]> {
  let addresses: string[];
  try {
    addresses = isIP(host) ? [host] : await resolver(host);
  } catch (error) {
    throw new BlockedDestinationError(host, `DNS resolution failed (${errorMessage(error)})`);
  }
  if (addresses.length === 0) {
    throw new BlockedDestinationError(host, 'DNS resolution returned no addresses');
  }
  if (!cfg.allowPrivateHosts) {
    const blocked = addresses.find(isPrivateAddress);
    if (blocked) {
      throw new BlockedDestinationError(
        host,
        `resolves to a private, loopback, link-local, or reserved address (${blocked})`,
      );
    }
  }
  return addresses;
}

/** Preflight validation used for fast refusal and independently testable policy coverage. */
export async function assertDestinationAllowed(
  url: URL,
  cfg: GuardConfig,
  resolver: Resolver = defaultResolve,
  requestedOrigin?: string,
): Promise<void> {
  const host = validateUrlShape(url, cfg);
  if (
    requestedOrigin !== undefined &&
    url.origin !== requestedOrigin &&
    !cfg.allowedDestinationOrigins.has(url.origin)
  ) {
    throw new BlockedDestinationError(
      host,
      `cross-origin destination ${url.origin} is not the requested origin ${requestedOrigin} or an entry in A2A_ALLOWED_DESTINATIONS`,
    );
  }
  await validatedAddresses(host, cfg, resolver);
}

/**
 * DNS lookup passed to Undici's actual connector. The callback receives only an
 * address from the checked answer set, so a second runtime lookup cannot rebind it.
 */
export function createPinnedLookup(
  cfg: GuardConfig,
  resolver: Resolver = defaultResolve,
): LookupFunction {
  return (hostname, options, callback) => {
    const host = normalizedHost(hostname);
    void validatedAddresses(host, cfg, resolver)
      .then((addresses) => {
        const records = addresses.map((address) => ({ address, family: isIP(address) }));
        if (options.all) {
          callback(null, records);
        } else {
          callback(null, records[0].address, records[0].family);
        }
      })
      .catch((error: unknown) => callback(asErrnoException(error), '', 0));
  };
}

export function createGuardedDispatcher(
  cfg: GuardConfig,
  resolver: Resolver = defaultResolve,
): Dispatcher {
  return new Agent({ connect: { lookup: createPinnedLookup(cfg, resolver) } });
}

function asErrnoException(error: unknown): NodeJS.ErrnoException {
  if (error instanceof Error) return error as NodeJS.ErrnoException;
  return new Error(String(error));
}

function errorMessage(error: unknown): string {
  return error instanceof Error ? error.message : String(error);
}

function blockedDestinationCause(error: unknown): BlockedDestinationError | undefined {
  let current = error;
  for (let depth = 0; depth < 8; depth += 1) {
    if (current instanceof BlockedDestinationError) return current;
    if (current === null || typeof current !== 'object' || !('cause' in current)) return undefined;
    current = (current as { cause?: unknown }).cause;
  }
  return undefined;
}

export function shouldSendCredential(url: URL, cfg: GuardConfig): boolean {
  return (
    url.protocol === 'https:' &&
    cfg.authHeaderValue.length > 0 &&
    cfg.allowedHosts.size > 0 &&
    cfg.allowedHosts.has(normalizedHost(url.hostname))
  );
}

export const MAX_REDIRECTS = 5;

function isRedirectStatus(status: number): boolean {
  return status === 301 || status === 302 || status === 303 || status === 307 || status === 308;
}

function headersForHop(request: Request, url: URL, cfg: GuardConfig): Headers {
  const headers = new Headers(request.headers);
  for (const name of SENSITIVE_HEADERS) headers.delete(name);
  headers.delete(cfg.authHeaderName);
  if (shouldSendCredential(url, cfg)) headers.set(cfg.authHeaderName, cfg.authHeaderValue);
  return headers;
}

function redirectRequest(next: URL, replay: Request, status: number): Request {
  const method = replay.method.toUpperCase();
  const switchToGet =
    (status === 303 && method !== 'HEAD') ||
    ((status === 301 || status === 302) && method === 'POST');

  if (switchToGet) {
    const headers = new Headers(replay.headers);
    for (const name of BODY_HEADERS) headers.delete(name);
    return new Request(next, { method: 'GET', headers, signal: replay.signal });
  }

  const nextInit: RequestInit & { duplex?: 'half' } = {
    method: replay.method,
    headers: replay.headers,
    signal: replay.signal,
  };
  if (replay.body !== null) {
    nextInit.body = replay.body;
    nextInit.duplex = 'half';
  }
  return new Request(next, nextInit);
}

interface RequestDeadline {
  signal: AbortSignal;
  cleanup(): void;
  timeoutError: RequestTimeoutError;
}

function requestDeadline(source: AbortSignal, timeoutMs: number): RequestDeadline {
  const controller = new AbortController();
  const timeoutError = new RequestTimeoutError(timeoutMs);
  let timer: ReturnType<typeof setTimeout> | undefined;

  const cleanup = () => {
    if (timer !== undefined) clearTimeout(timer);
    timer = undefined;
    source.removeEventListener('abort', onSourceAbort);
  };
  const onSourceAbort = () => {
    controller.abort(source.reason);
    cleanup();
  };

  if (source.aborted) {
    controller.abort(source.reason);
  } else {
    source.addEventListener('abort', onSourceAbort, { once: true });
    timer = setTimeout(() => {
      controller.abort(timeoutError);
      cleanup();
    }, timeoutMs);
    timer.unref?.();
  }
  return { signal: controller.signal, cleanup, timeoutError };
}

function responseError(error: unknown, deadline: RequestDeadline): unknown {
  return deadline.signal.reason === deadline.timeoutError ? deadline.timeoutError : error;
}

async function withinDeadline<T>(operation: Promise<T>, deadline: RequestDeadline): Promise<T> {
  if (deadline.signal.aborted) {
    throw responseError(deadline.signal.reason, deadline);
  }
  let onAbort: () => void = () => undefined;
  const aborted = new Promise<never>((_resolve, reject) => {
    onAbort = () => reject(responseError(deadline.signal.reason, deadline));
    deadline.signal.addEventListener('abort', onAbort, { once: true });
  });
  try {
    return await Promise.race([operation, aborted]);
  } finally {
    deadline.signal.removeEventListener('abort', onAbort);
  }
}

function boundedResponse(
  response: Response,
  maxBytes: number,
  deadline: RequestDeadline,
): Response {
  const contentLength = response.headers.get('content-length');
  if (contentLength !== null && /^\d+$/.test(contentLength) && Number(contentLength) > maxBytes) {
    void response.body?.cancel();
    deadline.cleanup();
    throw new ResponseTooLargeError(maxBytes);
  }
  if (response.body === null) {
    deadline.cleanup();
    return response;
  }

  const reader = response.body.getReader();
  let received = 0;
  const body = new ReadableStream<Uint8Array>({
    async pull(controller) {
      try {
        const item = await withinDeadline(reader.read(), deadline);
        if (item.done) {
          deadline.cleanup();
          controller.close();
          return;
        }
        received += item.value.byteLength;
        if (received > maxBytes) {
          const error = new ResponseTooLargeError(maxBytes);
          void reader.cancel(error).catch(() => undefined);
          deadline.cleanup();
          controller.error(error);
          return;
        }
        controller.enqueue(item.value);
      } catch (error) {
        void reader.cancel(error).catch(() => undefined);
        deadline.cleanup();
        controller.error(responseError(error, deadline));
      }
    },
    async cancel(reason) {
      deadline.cleanup();
      await reader.cancel(reason);
    },
  });
  return new Response(body, {
    status: response.status,
    statusText: response.statusText,
    headers: response.headers,
  });
}

/**
 * Create the only fetch implementation supplied to the A2A SDK.
 *
 * Redirects are manual, credentials are stripped and re-evaluated on every hop,
 * and Undici's connector receives the validated DNS address directly. A Request
 * input is normalized up front so POST-to-GET redirects cannot retain its body.
 */
export function createGuardedFetch(
  cfg: GuardConfig,
  fetchImpl: typeof fetch = fetch,
  resolver: Resolver = defaultResolve,
  dispatcher: Dispatcher = createGuardedDispatcher(cfg, resolver),
  requestedBaseUrl?: string | URL,
): typeof fetch {
  let requestedOrigin =
    requestedBaseUrl === undefined ? undefined : new URL(requestedBaseUrl).origin;
  return async function guardedFetch(input: RequestInfo | URL, init?: RequestInit) {
    let request = new Request(input, init);
    requestedOrigin ??= new URL(request.url).origin;
    const deadline = requestDeadline(request.signal, cfg.requestTimeoutMs);
    request = new Request(request, { signal: deadline.signal });

    try {
      for (let hop = 0; ; hop += 1) {
        const url = new URL(request.url);
        await withinDeadline(
          assertDestinationAllowed(url, cfg, resolver, requestedOrigin),
          deadline,
        );

        // Clone before sending: 307/308 must be able to replay the body on the next URL.
        const replay = request.clone();
        let response: Response;
        try {
          response = await withinDeadline(
            fetchImpl(request, {
              headers: headersForHop(request, url, cfg),
              redirect: 'manual',
              dispatcher,
            } as GuardedRequestInit),
            deadline,
          );
        } catch (error) {
          // Node fetch wraps connector lookup failures in TypeError. Preserve the
          // policy error so MCP callers receive DESTINATION_BLOCKED, not a generic failure.
          throw blockedDestinationCause(error) ?? responseError(error, deadline);
        }

        const location = response.headers.get('location');
        if (!isRedirectStatus(response.status) || !location) {
          return boundedResponse(response, cfg.maxResponseBytes, deadline);
        }
        if (hop >= MAX_REDIRECTS) {
          await response.body?.cancel();
          throw new BlockedDestinationError(url.hostname, `exceeded ${MAX_REDIRECTS} redirects`);
        }

        await response.body?.cancel();
        const next = new URL(location, url);
        validateUrlShape(next, cfg);
        request = redirectRequest(next, replay, response.status);
      }
    } catch (error) {
      deadline.cleanup();
      throw error;
    }
  } as typeof fetch;
}
