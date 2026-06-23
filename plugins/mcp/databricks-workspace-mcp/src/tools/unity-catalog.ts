/**
 * Unity Catalog governance tools (013-AT-ADEC T8 — KEEP). External locations + storage
 * credentials are the substrate uc-migration-pilot traces for HMS→UC readiness and IAM wiring.
 * Managed MCP serves `system.information_schema` reads but not the UC governance objects + their
 * cloud-IAM bindings.
 */

import { z } from "zod";
import { defineTool } from "./types.js";

const FAMILY = "unity_catalog";

export const externalLocationsList = defineTool({
  name: "external_locations_list",
  description:
    "List Unity Catalog external locations — each binds a cloud storage URL (s3://, abfss://, gs://) to a storage credential, plus owner, read_only flag, and isolation/binding mode. Use to inventory where UC data physically lives and which credential governs each path during an HMS→UC migration. Read-only. GET /api/2.1/unity-catalog/external-locations.",
  schema: z
    .object({
      max_results: z.number().int().min(1).max(1000).optional().describe("Page size"),
      page_token: z.string().optional().describe("Opaque token from a prior response"),
    })
    .strict(),
  family: FAMILY,
  handler: (client, args) =>
    client.get("/api/2.1/unity-catalog/external-locations", FAMILY, {
      max_results: args.max_results,
      page_token: args.page_token,
    }),
});

export const storageCredentialsList = defineTool({
  name: "storage_credentials_list",
  description:
    "List Unity Catalog storage credentials — the cloud-IAM principals (AWS IAM role, Azure managed identity / service principal, GCP service account) UC assumes to access storage, with owner, read_only, and used-for-managed-storage flags. Use to trace the IAM wiring behind external locations and audit credential reuse. Read-only. GET /api/2.1/unity-catalog/storage-credentials.",
  schema: z
    .object({
      max_results: z.number().int().min(1).max(1000).optional().describe("Page size"),
      page_token: z.string().optional().describe("Opaque token from a prior response"),
    })
    .strict(),
  family: FAMILY,
  handler: (client, args) =>
    client.get("/api/2.1/unity-catalog/storage-credentials", FAMILY, {
      max_results: args.max_results,
      page_token: args.page_token,
    }),
});

export const unityCatalogTools = [externalLocationsList, storageCredentialsList];
