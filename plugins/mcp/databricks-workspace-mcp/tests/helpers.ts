/**
 * Offline test harness — a fake fetch that serves recorded fixtures, plus client/auth builders
 * with injected clock, sleep, and rng so every test is deterministic and instant (no network).
 */

import { readFileSync } from "node:fs";
import { fileURLToPath } from "node:url";
import { dirname, join } from "node:path";
import type { FetchLike, ResolvedAuth } from "../src/auth.js";
import { resolveAuth } from "../src/auth.js";
import { DatabricksClient } from "../src/client.js";

const HERE = dirname(fileURLToPath(import.meta.url));

export function loadFixture<T = unknown>(name: string): T {
  return JSON.parse(readFileSync(join(HERE, "fixtures", `${name}.json`), "utf8")) as T;
}

export function jsonResponse(body: unknown, init: { status?: number; headers?: Record<string, string> } = {}): Response {
  return new Response(typeof body === "string" ? body : JSON.stringify(body), {
    status: init.status ?? 200,
    headers: { "content-type": "application/json", ...(init.headers ?? {}) },
  });
}

export interface RecordedCall {
  url: string;
  method: string;
  headers: Record<string, string>;
  body?: string;
}

/**
 * A fetch that records every call and dispatches to a handler (url, call) -> Response. The
 * handler may return a Response or an array of Responses to simulate retry sequences (one per
 * successive call to the same URL).
 */
export function recordingFetch(
  handler: (url: string, call: RecordedCall, callIndex: number) => Response | Promise<Response>,
): { fetchImpl: FetchLike; calls: RecordedCall[] } {
  const calls: RecordedCall[] = [];
  const fetchImpl: FetchLike = async (input, reqInit) => {
    const url = typeof input === "string" ? input : input.toString();
    const headers: Record<string, string> = {};
    const h = reqInit?.headers;
    if (h && typeof h === "object" && !Array.isArray(h)) {
      for (const [k, v] of Object.entries(h)) headers[k.toLowerCase()] = String(v);
    }
    const call: RecordedCall = {
      url,
      method: (reqInit?.method ?? "GET").toUpperCase(),
      headers,
      body: typeof reqInit?.body === "string" ? reqInit.body : undefined,
    };
    const idx = calls.length;
    calls.push(call);
    return handler(url, call, idx);
  };
  return { fetchImpl, calls };
}

export const TEST_HOST = "https://dbc-test.cloud.databricks.com";

export function patAuth(token = "dapiTESTtoken"): ResolvedAuth {
  return resolveAuth({ env: { DATABRICKS_HOST: TEST_HOST, DATABRICKS_TOKEN: token } });
}

/** Build a client wired to the given fetch, with fast deterministic timing. */
export function testClient(
  fetchImpl: FetchLike,
  opts: { auth?: ResolvedAuth; maxRetries?: number } = {},
): DatabricksClient {
  return new DatabricksClient({
    auth: opts.auth ?? patAuth(),
    fetchImpl,
    maxRetries: opts.maxRetries ?? 4,
    backoffBaseMs: 1,
    backoffMaxMs: 5,
    sleep: async () => {},
    now: () => 0,
    rng: () => 0,
  });
}
