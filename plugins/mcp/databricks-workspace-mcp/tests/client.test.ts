import { describe, expect, it } from "vitest";
import { DatabricksError } from "../src/errors.js";
import { RateLimiter } from "../src/ratelimit.js";
import { jsonResponse, recordingFetch, testClient } from "./helpers.js";

describe("DatabricksClient — happy path", () => {
  it("GETs and parses JSON, sending a Bearer token", async () => {
    const { fetchImpl, calls } = recordingFetch(() => jsonResponse({ ok: true, n: 3 }));
    const client = testClient(fetchImpl);
    const res = await client.get<{ ok: boolean; n: number }>("/api/2.0/clusters/list", "clusters");
    expect(res).toEqual({ ok: true, n: 3 });
    expect(calls[0].headers.authorization).toBe("Bearer dapiTESTtoken");
    expect(calls[0].url).toBe("https://dbc-test.cloud.databricks.com/api/2.0/clusters/list");
  });

  it("serializes query params and POST bodies", async () => {
    const { fetchImpl, calls } = recordingFetch(() => jsonResponse({}));
    const client = testClient(fetchImpl);
    await client.get("/api/2.0/clusters/get", "clusters", { cluster_id: "abc", limit: 5, skip: undefined });
    expect(calls[0].url).toContain("cluster_id=abc");
    expect(calls[0].url).toContain("limit=5");
    expect(calls[0].url).not.toContain("skip");

    await client.post("/api/2.0/clusters/events", "clusters", { cluster_id: "abc" });
    expect(calls[1].method).toBe("POST");
    expect(JSON.parse(calls[1].body!)).toEqual({ cluster_id: "abc" });
  });

  it("returns {} for an empty 200 body", async () => {
    const { fetchImpl } = recordingFetch(() => new Response("", { status: 200 }));
    const client = testClient(fetchImpl);
    expect(await client.get("/api/2.0/clusters/list", "clusters")).toEqual({});
  });
});

describe("DatabricksClient — retry", () => {
  it("retries on 429 then succeeds, honoring retry-after", async () => {
    const { fetchImpl, calls } = recordingFetch((_url, _call, i) =>
      i === 0
        ? jsonResponse({ message: "rate limited" }, { status: 429, headers: { "retry-after": "0" } })
        : jsonResponse({ ok: true }),
    );
    const client = testClient(fetchImpl);
    expect(await client.get("/x", "f")).toEqual({ ok: true });
    expect(calls.length).toBe(2);
  });

  it("retries on 500 and eventually throws a retriable structured error", async () => {
    const { fetchImpl, calls } = recordingFetch(() => jsonResponse({ message: "boom" }, { status: 503 }));
    const client = testClient(fetchImpl, { maxRetries: 2 });
    try {
      await client.get("/x", "f");
      expect.unreachable();
    } catch (e) {
      expect(e).toBeInstanceOf(DatabricksError);
      expect((e as DatabricksError).retriable).toBe(true);
      expect((e as DatabricksError).status).toBe(503);
    }
    expect(calls.length).toBe(3); // 1 + 2 retries
  });

  it("does NOT retry a 403 and surfaces the Databricks error_code", async () => {
    const { fetchImpl, calls } = recordingFetch(() =>
      jsonResponse({ error_code: "PERMISSION_DENIED", message: "no access" }, { status: 403 }),
    );
    const client = testClient(fetchImpl);
    try {
      await client.get("/x", "f");
      expect.unreachable();
    } catch (e) {
      const err = e as DatabricksError;
      expect(err.kind).toBe("auth");
      expect(err.errorCode).toBe("PERMISSION_DENIED");
      expect(err.retriable).toBe(false);
    }
    expect(calls.length).toBe(1);
  });

  it("captures x-request-id on errors", async () => {
    const { fetchImpl } = recordingFetch(() =>
      jsonResponse({ error_code: "INVALID_PARAMETER_VALUE", message: "bad" }, { status: 400, headers: { "x-request-id": "req-123" } }),
    );
    const client = testClient(fetchImpl);
    await expect(client.get("/x", "f")).rejects.toMatchObject({ requestId: "req-123" });
  });
});

describe("RateLimiter", () => {
  it("hands out burst tokens then throttles until refill", async () => {
    let t = 0;
    const slept: number[] = [];
    const rl = new RateLimiter({
      capacity: 2,
      refillPerSec: 1,
      now: () => t,
      sleep: async (ms) => {
        slept.push(ms);
        t += ms; // advance virtual clock so refill makes progress
      },
    });
    await rl.acquire(); // token 1 (no wait)
    await rl.acquire(); // token 2 (no wait)
    await rl.acquire(); // empty -> must wait ~1000ms for one token
    expect(slept.length).toBeGreaterThan(0);
    expect(slept[0]).toBeGreaterThanOrEqual(1000);
  });
});
