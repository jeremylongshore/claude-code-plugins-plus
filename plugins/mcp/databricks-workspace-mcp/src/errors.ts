/**
 * Structured error types for the Databricks control-plane MCP server.
 *
 * Databricks REST APIs return errors as JSON `{ error_code, message }`. We normalize
 * every failure — transport, auth, rate-limit, and API — into one shape so the MCP tool
 * layer can return a predictable `isError` payload that the calling agent can reason about
 * (rather than a raw stack trace).
 */

export type DatabricksErrorKind =
  | "auth" // credentials missing / rejected / wrong mode
  | "config" // server misconfiguration (no host, etc.)
  | "rate_limit" // 429 after retries exhausted
  | "api" // a 4xx/5xx from the Databricks REST API
  | "network" // fetch threw (DNS, TLS, timeout)
  | "unknown";

export interface StructuredError {
  kind: DatabricksErrorKind;
  /** Databricks `error_code` when present (e.g. PERMISSION_DENIED, RESOURCE_DOES_NOT_EXIST). */
  errorCode?: string;
  message: string;
  /** HTTP status when the failure came from a response. */
  status?: number;
  /** The control-plane endpoint that was called, for triage. */
  endpoint?: string;
  /** Databricks request id (`x-request-id`) when present — give this to Databricks support. */
  requestId?: string;
  /** True when a retry could plausibly succeed (429 / 5xx / network). */
  retriable?: boolean;
}

export class DatabricksError extends Error {
  readonly kind: DatabricksErrorKind;
  readonly errorCode?: string;
  readonly status?: number;
  readonly endpoint?: string;
  readonly requestId?: string;
  readonly retriable: boolean;

  constructor(e: StructuredError) {
    super(e.message);
    this.name = "DatabricksError";
    this.kind = e.kind;
    this.errorCode = e.errorCode;
    this.status = e.status;
    this.endpoint = e.endpoint;
    this.requestId = e.requestId;
    this.retriable = e.retriable ?? false;
  }

  toStructured(): StructuredError {
    return {
      kind: this.kind,
      errorCode: this.errorCode,
      message: this.message,
      status: this.status,
      endpoint: this.endpoint,
      requestId: this.requestId,
      retriable: this.retriable,
    };
  }
}

/** Map an HTTP status + parsed Databricks error body into a StructuredError. */
export function errorFromResponse(
  status: number,
  endpoint: string,
  body: unknown,
  requestId?: string,
): DatabricksError {
  let errorCode: string | undefined;
  let message = `Databricks API returned ${status} for ${endpoint}`;
  if (body && typeof body === "object") {
    const b = body as Record<string, unknown>;
    if (typeof b.error_code === "string") errorCode = b.error_code;
    if (typeof b.message === "string" && b.message.length > 0) message = b.message;
    // Some surfaces return a bare `{ error: "..." }`.
    else if (typeof b.error === "string" && b.error.length > 0) message = b.error;
  } else if (typeof body === "string" && body.length > 0) {
    message = body;
  }
  const retriable = status === 429 || status >= 500;
  const kind: DatabricksErrorKind =
    status === 401 || status === 403 ? "auth" : status === 429 ? "rate_limit" : "api";
  return new DatabricksError({
    kind,
    errorCode,
    message,
    status,
    endpoint,
    requestId,
    retriable,
  });
}

/** Render any thrown value as a StructuredError for the MCP isError payload. */
export function toStructuredError(err: unknown, endpoint?: string): StructuredError {
  if (err instanceof DatabricksError) return err.toStructured();
  if (err instanceof Error) {
    // A thrown fetch is almost always a transport problem.
    return {
      kind: "network",
      message: err.message,
      endpoint,
      retriable: true,
    };
  }
  return { kind: "unknown", message: String(err), endpoint };
}
