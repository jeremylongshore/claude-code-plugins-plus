import { describe, expect, it } from "vitest";
import { allTools } from "../src/tools/index.js";
import { callTool } from "../src/server.js";
import { DatabricksError } from "../src/errors.js";
import { jsonResponse, loadFixture, recordingFetch, testClient } from "./helpers.js";

/** Route a request to the right fixture by URL. */
function fixtureFetch() {
  return recordingFetch((url) => {
    if (url.includes("/clusters/list")) return jsonResponse(loadFixture("clusters_list"));
    if (url.includes("/clusters/get")) return jsonResponse(loadFixture("clusters_list"));
    if (url.includes("/clusters/events")) return jsonResponse(loadFixture("clusters_events"));
    if (url.includes("/instance-pools/list")) return jsonResponse(loadFixture("instance_pools_list"));
    if (url.includes("/pipelines/") && url.includes("/events")) return jsonResponse(loadFixture("pipelines_events"));
    if (url.includes("/pipelines/")) return jsonResponse(loadFixture("pipelines_get"));
    if (url.includes("/external-locations")) return jsonResponse(loadFixture("external_locations_list"));
    if (url.includes("/storage-credentials")) return jsonResponse(loadFixture("storage_credentials_list"));
    return jsonResponse({ error_code: "RESOURCE_DOES_NOT_EXIST", message: url }, { status: 404 });
  });
}

function parse(result: { content: Array<{ text: string }> }) {
  return JSON.parse(result.content[0].text);
}

describe("tool catalog", () => {
  it("exposes exactly the 8 control-plane tools", () => {
    expect(allTools.map((t) => t.name).sort()).toEqual(
      [
        "clusters_events",
        "clusters_get",
        "clusters_list",
        "external_locations_list",
        "instance_pools_list",
        "pipelines_get",
        "pipelines_get_event_log",
        "storage_credentials_list",
      ].sort(),
    );
  });

  it("every tool description names a real endpoint and is read-only", () => {
    for (const t of allTools) {
      expect(t.description).toMatch(/GET |POST /);
      expect(t.description.toLowerCase()).toContain("read-only");
    }
  });
});

describe("callTool — happy paths against fixtures", () => {
  it("clusters_list", async () => {
    const { fetchImpl, calls } = fixtureFetch();
    const client = testClient(fetchImpl);
    const out = parse(await callTool(() => client, "clusters_list", {}));
    expect(out.clusters).toHaveLength(3);
    expect(calls[0].method).toBe("GET");
    expect(calls[0].url).toContain("/api/2.0/clusters/list");
  });

  it("clusters_get requires + forwards cluster_id", async () => {
    const { fetchImpl, calls } = fixtureFetch();
    const client = testClient(fetchImpl);
    await callTool(() => client, "clusters_get", { cluster_id: "0608-120000-leak001" });
    expect(calls[0].url).toContain("cluster_id=0608-120000-leak001");
  });

  it("clusters_events is a POST with the cluster_id in the body", async () => {
    const { fetchImpl, calls } = fixtureFetch();
    const client = testClient(fetchImpl);
    const out = parse(await callTool(() => client, "clusters_events", { cluster_id: "0608-120000-leak001", limit: 50 }));
    expect(out.events).toHaveLength(5);
    expect(calls[0].method).toBe("POST");
    expect(JSON.parse(calls[0].body!)).toMatchObject({ cluster_id: "0608-120000-leak001", limit: 50 });
  });

  it("instance_pools_list", async () => {
    const { fetchImpl } = fixtureFetch();
    const out = parse(await callTool(() => testClient(fetchImpl), "instance_pools_list", {}));
    expect(out.instance_pools[0].min_idle_instances).toBe(6);
  });

  it("pipelines_get and pipelines_get_event_log hit the right paths", async () => {
    const { fetchImpl, calls } = fixtureFetch();
    const client = testClient(fetchImpl);
    const pid = "a1b2c3d4-0000-1111-2222-333344445555";
    const got = parse(await callTool(() => client, "pipelines_get", { pipeline_id: pid }));
    expect(got.spec.edition).toBe("ADVANCED");
    const log = parse(await callTool(() => client, "pipelines_get_event_log", { pipeline_id: pid, max_results: 25 }));
    expect(log.events).toHaveLength(2);
    expect(calls[1].url).toContain(`/pipelines/${pid}/events`);
  });

  it("external_locations_list and storage_credentials_list", async () => {
    const { fetchImpl } = fixtureFetch();
    const client = testClient(fetchImpl);
    const loc = parse(await callTool(() => client, "external_locations_list", {}));
    expect(loc.external_locations.map((l: { name: string }) => l.name)).toContain("legacy-hms-warehouse");
    const cred = parse(await callTool(() => client, "storage_credentials_list", {}));
    expect(cred.storage_credentials[0].aws_iam_role.role_arn).toMatch(/^arn:aws:iam::/);
  });
});

describe("callTool — error handling", () => {
  it("rejects unknown tools with a structured error", async () => {
    const { fetchImpl } = fixtureFetch();
    const r = await callTool(() => testClient(fetchImpl), "nope", {});
    expect(r.isError).toBe(true);
    expect(parse(r).error.message).toMatch(/Unknown tool/);
  });

  it("rejects invalid args before any network call", async () => {
    const { fetchImpl, calls } = fixtureFetch();
    const r = await callTool(() => testClient(fetchImpl), "clusters_get", {});
    expect(r.isError).toBe(true);
    expect(parse(r).error.message).toMatch(/Invalid arguments/);
    expect(calls.length).toBe(0);
  });

  it("rejects unknown extra args (strict schemas)", async () => {
    const { fetchImpl } = fixtureFetch();
    const r = await callTool(() => testClient(fetchImpl), "clusters_list", { surprise: 1 });
    expect(r.isError).toBe(true);
  });

  it("returns a clean structured auth error when the client provider throws (MCP present, not configured)", async () => {
    const r = await callTool(
      () => {
        throw new DatabricksError({ kind: "auth", message: "No credentials" });
      },
      "clusters_list",
      {},
    );
    expect(r.isError).toBe(true);
    expect(parse(r).error.kind).toBe("auth");
  });

  it("surfaces an API error from the handler as isError", async () => {
    const { fetchImpl } = recordingFetch(() =>
      jsonResponse({ error_code: "PERMISSION_DENIED", message: "nope" }, { status: 403 }),
    );
    const r = await callTool(() => testClient(fetchImpl), "clusters_list", {});
    expect(r.isError).toBe(true);
    expect(parse(r).error.errorCode).toBe("PERMISSION_DENIED");
  });
});
