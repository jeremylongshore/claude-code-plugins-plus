/**
 * Databricks control-plane REST client.
 *
 * Wraps the workspace REST API with the three cross-cutting concerns Epic 1 T10 calls for:
 *   - per-family token-bucket rate limiting (ratelimit.ts)
 *   - exponential-backoff retry on 429 / 5xx, honoring `Retry-After`
 *   - normalization of every failure into a StructuredError (errors.ts)
 *
 * Everything time/network/random is injectable so the whole client is exercised offline with
 * recorded fixtures and a fake clock.
 */

import type { FetchLike, ResolvedAuth } from "./auth.js";
import { DatabricksError, errorFromResponse, type StructuredError } from "./errors.js";
import { FamilyRateLimiters } from "./ratelimit.js";

export interface DatabricksClientOptions {
  auth: ResolvedAuth;
  fetchImpl?: FetchLike;
  rateLimiters?: FamilyRateLimiters;
  /** Total attempts = maxRetries + 1. Default 4 retries. */
  maxRetries?: number;
  /** Base backoff in ms (doubled each attempt). Default 250ms. */
  backoffBaseMs?: number;
  /** Cap on a single backoff wait. Default 20s. */
  backoffMaxMs?: number;
  sleep?: (ms: number) => Promise<void>;
  now?: () => number;
  /** Jitter source in [0,1). Default Math.random. */
  rng?: () => number;
}

export interface RequestSpec {
  method: "GET" | "POST";
  /** Path beginning with `/api/...`. */
  path: string;
  /** Endpoint family for rate limiting (e.g. "clusters", "pipelines"). */
  family: string;
  query?: Record<string, string | number | boolean | undefined>;
  body?: unknown;
}

export class DatabricksClient {
  private readonly auth: ResolvedAuth;
  private readonly fetchImpl: FetchLike;
  private readonly limiters: FamilyRateLimiters;
  private readonly maxRetries: number;
  private readonly backoffBaseMs: number;
  private readonly backoffMaxMs: number;
  private readonly sleep: (ms: number) => Promise<void>;
  private readonly rng: () => number;

  constructor(opts: DatabricksClientOptions) {
    this.auth = opts.auth;
    this.fetchImpl = opts.fetchImpl ?? (globalThis.fetch as FetchLike);
    this.limiters = opts.rateLimiters ?? new FamilyRateLimiters();
    this.maxRetries = opts.maxRetries ?? 4;
    this.backoffBaseMs = opts.backoffBaseMs ?? 250;
    this.backoffMaxMs = opts.backoffMaxMs ?? 20_000;
    this.sleep = opts.sleep ?? ((ms) => new Promise((r) => setTimeout(r, ms)));
    this.rng = opts.rng ?? Math.random;
  }

  get host(): string {
    return this.auth.host;
  }

  private buildUrl(path: string, query?: RequestSpec["query"]): string {
    const url = new URL(this.auth.host + path);
    if (query) {
      for (const [k, v] of Object.entries(query)) {
        if (v !== undefined) url.searchParams.set(k, String(v));
      }
    }
    return url.toString();
  }

  private backoffMs(attempt: number, retryAfterSec?: number): number {
    if (retryAfterSec && retryAfterSec > 0) return Math.min(retryAfterSec * 1000, this.backoffMaxMs);
    const exp = this.backoffBaseMs * 2 ** attempt;
    const jitter = exp * 0.25 * this.rng();
    return Math.min(exp + jitter, this.backoffMaxMs);
  }

  async request<T = unknown>(spec: RequestSpec): Promise<T> {
    await this.limiters.acquire(spec.family);
    const url = this.buildUrl(spec.path, spec.query);

    let lastError: DatabricksError | undefined;
    for (let attempt = 0; attempt <= this.maxRetries; attempt++) {
      let token: string;
      try {
        token = await this.auth.provider.getToken();
      } catch (err) {
        // Auth resolution failures are not retriable.
        throw err instanceof DatabricksError
          ? err
          : new DatabricksError({ kind: "auth", message: String(err), endpoint: spec.path });
      }

      const headers: Record<string, string> = {
        Authorization: `Bearer ${token}`,
        Accept: "application/json",
        "User-Agent": "databricks-workspace-mcp/0.1.0",
      };
      const init: RequestInit = { method: spec.method, headers };
      if (spec.body !== undefined) {
        headers["Content-Type"] = "application/json";
        init.body = JSON.stringify(spec.body);
      }

      let resp: Response;
      try {
        resp = await this.fetchImpl(url, init);
      } catch (err) {
        lastError = new DatabricksError({
          kind: "network",
          message: `Network error calling ${spec.path}: ${err instanceof Error ? err.message : String(err)}`,
          endpoint: spec.path,
          retriable: true,
        });
        if (attempt < this.maxRetries) {
          await this.sleep(this.backoffMs(attempt));
          continue;
        }
        throw lastError;
      }

      const requestId = resp.headers.get("x-request-id") ?? undefined;

      if (resp.ok) {
        // 200 with empty body (some control-plane ops) → {}.
        const text = await resp.text();
        if (!text) return {} as T;
        try {
          return JSON.parse(text) as T;
        } catch {
          throw new DatabricksError({
            kind: "api",
            message: `Non-JSON success body from ${spec.path}`,
            status: resp.status,
            endpoint: spec.path,
            requestId,
          });
        }
      }

      // Error path.
      const bodyText = await resp.text().catch(() => "");
      let parsed: unknown = bodyText;
      try {
        parsed = bodyText ? JSON.parse(bodyText) : undefined;
      } catch {
        /* keep raw text */
      }
      const apiErr = errorFromResponse(resp.status, spec.path, parsed, requestId);
      lastError = apiErr;

      if (apiErr.retriable && attempt < this.maxRetries) {
        const retryAfter = Number(resp.headers.get("retry-after") ?? "");
        await this.sleep(this.backoffMs(attempt, Number.isFinite(retryAfter) ? retryAfter : undefined));
        continue;
      }
      throw apiErr;
    }

    // Exhausted retries.
    throw (
      lastError ??
      new DatabricksError({ kind: "unknown", message: "Request failed", endpoint: spec.path })
    );
  }

  get<T = unknown>(path: string, family: string, query?: RequestSpec["query"]): Promise<T> {
    return this.request<T>({ method: "GET", path, family, query });
  }

  post<T = unknown>(path: string, family: string, body?: unknown): Promise<T> {
    return this.request<T>({ method: "POST", path, family, body });
  }
}

export type { StructuredError };
