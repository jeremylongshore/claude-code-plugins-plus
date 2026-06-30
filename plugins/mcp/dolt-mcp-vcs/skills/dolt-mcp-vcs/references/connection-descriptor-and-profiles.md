# Connection descriptor + schema profiles — the value formats

Two value formats turn this plugin from a beads-first tool into a Dolt-first core
(blueprint §2, §4). Both are *data the core reads*, not hardcoded structure, and
both are treated as **untrusted input** — live introspection always wins over a
stored value, and every name/secret is validated before use.

This file is a spec, not a behavioral snapshot. The installed binary + live schema
are still the authority (see `dolt-internals.md`).

---

## 1. The connection descriptor (`connection.descriptor.json`)

One committed descriptor per workspace is the home for the connection's
flavor/endpoint/database/creds/maturity. It replaces frozen `.mcp.json` literals
with data.

```jsonc
{
  "flavor":    "dolt",            // dolt | doltgres | doltlite | dumbo
  "endpoint":  "127.0.0.1:3308",  // host:port (Hosted-Dolt URL, DoltLab host, …)
  "database":  "beads",           // the named database on the server
  "creds-ref": "env:DOLT_PASSWORD", // a POINTER to a secret — never the secret
  "maturity":  "ga"              // ga | beta | alpha | experimental
}
```

What is genuinely *new* here (the rest was already parameterized in `.mcp.json` via
`${VAR:-default}` — see D4 / the panel's strawman correction):

- **`flavor`** selects the wire dialect (`dolt` ⇒ `--dolt`, `doltgres` ⇒
  `--doltgres`). `doltlite`/`dumbo` validate but are descriptor-stubs with no live
  connect flag yet (decision 6) until `dolt-watch` reports beta.
- **`maturity`** is read by the mutation gate. `alpha`/`experimental` hold the
  connection to **read-only** regardless of `--allow-mutation`
  (`sql_classifier.gate_decision`).

**The transform.** `scripts/descriptor-to-mcp-args.py` validates the descriptor and
emits the `dolt-mcp-server` args + env (`--format json|args`). It also *is* the
descriptor **validator rule** (fail-closed, exit 2) — it rejects a missing required
field, an unknown `flavor`/`maturity`, or a `creds-ref` with no known scheme.

---

## 2. `creds-ref` — the secret pointer, resolved fail-closed

A `creds-ref` is always a pointer, never a literal. Accepted **schemes**:

| Scheme | Form | Resolves via |
|---|---|---|
| `env` | `env:NAME` | the `NAME` environment variable |
| `sops` | `sops:PATH#KEY` | `KEY` from a SOPS file at `PATH`, decrypted to stdout only (never to disk) |
| `pass` | `pass:PATH` | `pass show PATH` |

**Resolution order + fail-closed rule** (`scripts/resolve-creds-ref.py`):

1. **Unknown scheme → reject** (exit 2). This is the validator rule: a `creds-ref`
   that is not a known `scheme:` prefix is never silently treated as a literal
   password.
2. Resolve via the scheme's resolver.
3. **Empty/unresolved secret:**
   - **loopback endpoint** (`127.0.0.1` / `localhost` / `::1`) → empty is allowed
     (bd's local dolt server is unauthenticated by default);
   - **non-loopback endpoint** → **fail closed** (exit 4). We never connect a remote
     endpoint with an empty (unauthenticated) password.

The resolved secret is printed to stdout for capture into an env var
(`export DOLT_PASSWORD="$(resolve-creds-ref.py …)"`); **never echo or log it.**

---

## 3. Schema profiles (`profiles/*.profile.json`)

A profile is the named encoding + value vocabulary the generic agents/scripts read
as INPUT, so a schema is a profile rather than a hardcode. Format:

```jsonc
{
  "name": "beads",
  "tables":  { "issues": "issues", "dependencies": "dependencies" },
  "columns": { "id": "id", "status": "status", "type": "type", "issue_type": "issue_type" },
  "encodings": {
    "parent-child": { "child": "issue_id", "parent": "depends_on_id" },
    "blocks":       { "blocked": "issue_id", "blocker": "depends_on_id" }
  },
  "closed-value": "closed",
  "epic-value":   "epic"
}
```

- `tables` / `columns` map the logical role → the real identifier in this schema.
- each `encodings` entry maps the role columns and may carry an optional `value`
  (the string stored in the `type` column; defaults to the encoding key — beads
  stores literally `'parent-child'`/`'blocks'`).
- `closed-value` / `epic-value` are the status/issue_type literals.

**The seam.** `scripts/profile_sql.py` builds the epic-closure + bottleneck SQL from
a profile. `profiles/beads.profile.json` is adapter #1; `profiles/example-generic.profile.json`
is a throwaway second schema that renames *everything* — `tests/test_profile_sql.py`
proves the same builder emits correct SQL for both with zero code change. (The
bash audit scripts get wired to the profile in Build 1b; the seam is proven at the
unit level now.)

**Untrusted input.** A profile is validated before use: every table/column name
must be a bare identifier (`^[A-Za-z_][A-Za-z_0-9]*$`) or the builder refuses it,
and `type`/status/`issue_type` *values* are quoted+escaped as string literals — so
a hostile profile cannot inject SQL. At agent runtime, live schema introspection
(`SHOW TABLES`, `information_schema`) still overrides the profile on any conflict.
