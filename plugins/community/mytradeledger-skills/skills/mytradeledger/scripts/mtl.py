#!/usr/bin/env python3
"""MyTradeLedger API helper — read and manage journaled crypto trades, accounts,
ledger entries, assets, and P&L through the MyTradeLedger REST API (served at
`<base>/api`).

Auth and instance URL are loaded from a `.env` file in the skill directory
(gitignored; copy it from `.env.sample`). A real environment variable of the
same name overrides `.env`. Recognised keys:
    MTL_URL    -> base URL of the instance (no trailing /api).
                  Defaults to https://mytradeledger.com for the hosted service.
    MTL_TOKEN  -> personal access token, sent as `Authorization: Bearer <token>`

Stdlib only — no third-party packages required.

The API wraps successful payloads in a top-level `{"data": ...}` envelope; list
endpoints add `{"meta": {"total", "limit", "offset"}}`. This script prints the
raw JSON response and exits non-zero on any non-2xx status (except `export-csv`,
which streams raw CSV text).

Examples
--------
    # Does auth work / who am I
    ./mtl.py whoami

    # Accounts
    ./mtl.py accounts
    ./mtl.py account-balance acc-uuid-1
    ./mtl.py account-pnl acc-uuid-1

    # Ledger (journaled trades)
    ./mtl.py ledger --symbol BTC/USD --entry-type BUY --limit 20
    ./mtl.py entry-create --symbol BTC/USD --entry-type BUY --quantity 1.0 --price 60000 --fee 9.99
    ./mtl.py export-csv --symbol BTC/USD --start-date 2025-01-01 -o btc-2025.csv
"""

import argparse
import json
import os
import sys
import urllib.error
import urllib.parse
import urllib.request

# Skill root = the dir above scripts/. The host-local .env lives there (0600,
# gitignored). .env.sample is the committed template.
SKILL_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

ENTRY_TYPES = ("BUY", "SELL", "FEE", "DEPOSIT", "WITHDRAWAL", "ADJUSTMENT")


def _load_dotenv():
    """Populate os.environ from <skill>/.env if present. Real environment
    variables always win — a value already in the environment is never
    overwritten. Supports `KEY=val`, optional `export ` prefix, `#` comments,
    and single/double quotes."""
    path = os.path.join(SKILL_ROOT, ".env")
    try:
        with open(path) as f:
            lines = f.readlines()
    except FileNotFoundError:
        return
    for raw in lines:
        line = raw.strip()
        if not line or line.startswith("#"):
            continue
        if line.startswith("export "):
            line = line[len("export "):]
        if "=" not in line:
            continue
        key, val = line.split("=", 1)
        key = key.strip()
        val = val.strip()
        if len(val) >= 2 and val[0] == val[-1] and val[0] in "\"'":
            val = val[1:-1]
        if key and key not in os.environ:
            os.environ[key] = val


def _api_base():
    url = os.environ.get("MTL_URL", "https://mytradeledger.com")
    return url.rstrip("/") + "/api"


def _token():
    tok = os.environ.get("MTL_TOKEN")
    if not tok:
        sys.exit(
            "ERROR: MTL_TOKEN must be set (a MyTradeLedger personal access "
            "token). Populate the skill's .env — see README.md."
        )
    return tok


def _request(method, path, payload=None, query=None, raw=False):
    url = _api_base() + path
    if query:
        clean = {k: v for k, v in query.items() if v is not None}
        if clean:
            url += "?" + urllib.parse.urlencode(clean, doseq=True)
    data = json.dumps(payload).encode() if payload is not None else None
    req = urllib.request.Request(url, data=data, method=method)
    req.add_header("Authorization", f"Bearer {_token()}")
    req.add_header("Accept", "text/csv" if raw else "application/json")
    if data is not None:
        req.add_header("Content-Type", "application/json")
    try:
        with urllib.request.urlopen(req) as resp:
            body = resp.read().decode()
            if raw:
                return resp.status, body
            return resp.status, (json.loads(body) if body else {})
    except urllib.error.HTTPError as e:
        body = e.read().decode()
        try:
            body = json.loads(body)
        except ValueError:
            pass
        return e.code, body
    except urllib.error.URLError as e:
        return 0, {"error": "network", "reason": str(e.reason)}


def _emit(status, body):
    print(json.dumps(body, indent=2, ensure_ascii=False))
    sys.exit(0 if 200 <= status < 300 else 1)


def _num(value):
    """Parse a numeric CLI value, keeping ints int and floats float."""
    if value is None:
        return None
    try:
        f = float(value)
        return int(f) if f.is_integer() and "." not in str(value) and "e" not in str(value).lower() else f
    except ValueError:
        sys.exit(f"ERROR: '{value}' is not a number.")


def _confirm(args, what):
    """Guard destructive actions behind --yes."""
    if not getattr(args, "yes", False):
        sys.exit(
            f"ERROR: {what} is destructive and cannot be undone. Re-run with "
            "--yes to confirm."
        )


# --------------------------------------------------------------------------- #
# Identity
# --------------------------------------------------------------------------- #
def cmd_whoami(args):
    _emit(*_request("GET", "/auth/me"))


# --------------------------------------------------------------------------- #
# Accounts
# --------------------------------------------------------------------------- #
def cmd_accounts(args):
    query = {"includeArchived": "true"} if args.include_archived else None
    _emit(*_request("GET", "/accounts", query=query))


def cmd_account_get(args):
    _emit(*_request("GET", f"/accounts/{args.id}"))


def cmd_account_create(args):
    payload = {"name": args.name}
    if args.base_currency is not None:
        payload["baseCurrency"] = args.base_currency
    _emit(*_request("POST", "/accounts", payload))


def cmd_account_update(args):
    payload = {}
    if args.name is not None:
        payload["name"] = args.name
    if args.base_currency is not None:
        payload["baseCurrency"] = args.base_currency
    if not payload:
        sys.exit("ERROR: nothing to update — pass --name and/or --base-currency.")
    _emit(*_request("PATCH", f"/accounts/{args.id}", payload))


def cmd_account_set_default(args):
    _emit(*_request("POST", f"/accounts/{args.id}/set-default"))


def cmd_account_archive(args):
    _emit(*_request("POST", f"/accounts/{args.id}/archive"))


def cmd_account_unarchive(args):
    _emit(*_request("POST", f"/accounts/{args.id}/unarchive"))


def cmd_account_balance(args):
    _emit(*_request("GET", f"/accounts/{args.id}/balance"))


def cmd_account_pnl(args):
    _emit(*_request("GET", f"/accounts/{args.id}/pnl"))


def cmd_account_delete(args):
    _confirm(args, "Deleting an account (and ALL its ledger entries)")
    _emit(*_request("DELETE", f"/accounts/{args.id}"))


# --------------------------------------------------------------------------- #
# Ledger entries (journaled trades)
# --------------------------------------------------------------------------- #
def _ledger_filters(args):
    return {
        "symbol": args.symbol,
        "entryType": args.entry_type,
        "startDate": args.start_date,
        "endDate": args.end_date,
    }


def cmd_ledger(args):
    query = _ledger_filters(args)
    query["limit"] = args.limit
    query["offset"] = args.offset
    _emit(*_request("GET", "/ledger", query=query))


def cmd_entry_get(args):
    _emit(*_request("GET", f"/ledger/{args.id}"))


def _entry_payload(args, require=False):
    payload = {}
    if args.symbol is not None:
        payload["symbol"] = args.symbol
    if args.entry_type is not None:
        payload["entryType"] = args.entry_type
    if args.quantity is not None:
        payload["quantity"] = _num(args.quantity)
    if args.price is not None:
        payload["price"] = _num(args.price)
    if args.fee is not None:
        payload["fee"] = None if args.fee == "null" else _num(args.fee)
    if args.timestamp is not None:
        payload["timestamp"] = args.timestamp
    if args.notes is not None:
        payload["notes"] = None if args.notes == "null" else args.notes
    if getattr(args, "account_id", None) is not None:
        payload["accountId"] = args.account_id
    if require:
        for field in ("symbol", "entryType", "quantity", "price"):
            if field not in payload:
                sys.exit(f"ERROR: --{field.replace('Type', '-type')} is required to create an entry.")
    return payload


def cmd_entry_create(args):
    _emit(*_request("POST", "/ledger", _entry_payload(args, require=True)))


def cmd_entry_update(args):
    payload = _entry_payload(args)
    if not payload:
        sys.exit("ERROR: nothing to update — pass at least one field.")
    _emit(*_request("PATCH", f"/ledger/{args.id}", payload))


def cmd_entry_delete(args):
    _confirm(args, "Deleting a ledger entry")
    _emit(*_request("DELETE", f"/ledger/{args.id}"))


def cmd_entry_batch(args):
    text = sys.stdin.read() if args.file == "-" else open(args.file).read()
    try:
        parsed = json.loads(text)
    except ValueError as e:
        sys.exit(f"ERROR: --file is not valid JSON: {e}")
    # Accept either a bare list of entries or a {"entries": [...]} envelope.
    entries = parsed.get("entries") if isinstance(parsed, dict) else parsed
    if not isinstance(entries, list):
        sys.exit('ERROR: expected a JSON array of entries, or {"entries": [...]}.')
    _emit(*_request("POST", "/ledger/batch", {"entries": entries}))


def cmd_recalculate_pnl(args):
    _emit(*_request("POST", "/ledger/recalculate-pnl"))


def cmd_ledger_delete_all(args):
    _confirm(args, "Deleting ALL ledger entries across every account")
    _emit(*_request("DELETE", "/ledger/all"))


def cmd_export_csv(args):
    query = _ledger_filters(args)
    status, body = _request("GET", "/ledger/export/csv", query=query, raw=True)
    if not (200 <= status < 300):
        # Error bodies come back as JSON even on the CSV endpoint.
        try:
            body = json.dumps(json.loads(body), indent=2)
        except (ValueError, TypeError):
            pass
        sys.stderr.write(str(body) + "\n")
        sys.exit(1)
    if args.output:
        with open(args.output, "w") as f:
            f.write(body)
        print(f"Wrote {len(body)} bytes to {args.output}")
    else:
        sys.stdout.write(body)


# --------------------------------------------------------------------------- #
# Ledger entry metadata
# --------------------------------------------------------------------------- #
def cmd_metadata(args):
    _emit(*_request("GET", f"/ledger/{args.id}/metadata"))


def cmd_metadata_add(args):
    _emit(*_request("POST", f"/ledger/{args.id}/metadata",
                    {"key": args.key, "value": args.value}))


def cmd_metadata_delete(args):
    _emit(*_request("DELETE", f"/ledger/{args.id}/metadata/{args.metadata_id}"))


# --------------------------------------------------------------------------- #
# Asset registry
# --------------------------------------------------------------------------- #
def cmd_assets(args):
    _emit(*_request("GET", "/assets"))


def cmd_asset_get(args):
    _emit(*_request("GET", f"/assets/{args.id}"))


def cmd_asset_create(args):
    _emit(*_request("POST", "/assets",
                    {"symbol": args.symbol, "name": args.name,
                     "precision": _num(args.precision)}))


def cmd_asset_update(args):
    payload = {}
    if args.name is not None:
        payload["name"] = args.name
    if args.precision is not None:
        payload["precision"] = _num(args.precision)
    if not payload:
        sys.exit("ERROR: nothing to update — pass --name and/or --precision.")
    _emit(*_request("PATCH", f"/assets/{args.id}", payload))


def cmd_asset_delete(args):
    _confirm(args, "Deleting a registered asset")
    _emit(*_request("DELETE", f"/assets/{args.id}"))


# --------------------------------------------------------------------------- #
# Personal access tokens
# --------------------------------------------------------------------------- #
def cmd_tokens(args):
    _emit(*_request("GET", "/auth/tokens"))


def cmd_token_create(args):
    # The freshly minted token is returned ONCE in the response — store it.
    _emit(*_request("POST", "/auth/tokens", {"name": args.name}))


def cmd_token_revoke(args):
    _emit(*_request("DELETE", f"/auth/tokens/{args.id}"))


# --------------------------------------------------------------------------- #
# CLI
# --------------------------------------------------------------------------- #
def _add_ledger_filters(p):
    p.add_argument("--symbol", help="Filter by symbol, e.g. BTC/USD (case-sensitive).")
    p.add_argument("--entry-type", choices=ENTRY_TYPES, help="Filter by entry type.")
    p.add_argument("--start-date", help="ISO 8601: only entries on/after this date.")
    p.add_argument("--end-date", help="ISO 8601: only entries on/before this date.")


def _add_entry_fields(p):
    p.add_argument("--symbol", help="Trading pair / symbol, e.g. BTC/USD.")
    p.add_argument("--entry-type", choices=ENTRY_TYPES, help="Entry type.")
    p.add_argument("--quantity", help="Positive number.")
    p.add_argument("--price", help="Positive number (price per unit).")
    p.add_argument("--fee", help="Fee amount, or 'null' to clear (update).")
    p.add_argument("--timestamp", help="ISO 8601 timestamp; defaults to now.")
    p.add_argument("--notes", help="Free-text note, or 'null' to clear (update).")


def build_parser():
    parser = argparse.ArgumentParser(
        prog="mtl.py", description="MyTradeLedger API helper (stdlib only).")
    sub = parser.add_subparsers(dest="command", required=True)

    sub.add_parser("whoami", help="Authenticated user profile (verifies token).").set_defaults(func=cmd_whoami)

    # Accounts -------------------------------------------------------------- #
    p = sub.add_parser("accounts", help="List accounts.")
    p.add_argument("--include-archived", action="store_true", help="Include archived accounts.")
    p.set_defaults(func=cmd_accounts)

    p = sub.add_parser("account-get", help="Get one account by UUID.")
    p.add_argument("id")
    p.set_defaults(func=cmd_account_get)

    p = sub.add_parser("account-create", help="Create an account.")
    p.add_argument("--name", required=True)
    p.add_argument("--base-currency", help="Defaults to USD.")
    p.set_defaults(func=cmd_account_create)

    p = sub.add_parser("account-update", help="Update an account's name/currency.")
    p.add_argument("id")
    p.add_argument("--name")
    p.add_argument("--base-currency")
    p.set_defaults(func=cmd_account_update)

    p = sub.add_parser("account-set-default", help="Make this the default account.")
    p.add_argument("id")
    p.set_defaults(func=cmd_account_set_default)

    p = sub.add_parser("account-archive", help="Archive an account.")
    p.add_argument("id")
    p.set_defaults(func=cmd_account_archive)

    p = sub.add_parser("account-unarchive", help="Restore an archived account.")
    p.add_argument("id")
    p.set_defaults(func=cmd_account_unarchive)

    p = sub.add_parser("account-balance", help="Open position balances per symbol.")
    p.add_argument("id")
    p.set_defaults(func=cmd_account_balance)

    p = sub.add_parser("account-pnl", help="Total realized P&L for an account.")
    p.add_argument("id")
    p.set_defaults(func=cmd_account_pnl)

    p = sub.add_parser("account-delete", help="DELETE an account and all its entries.")
    p.add_argument("id")
    p.add_argument("--yes", action="store_true", help="Confirm this irreversible delete.")
    p.set_defaults(func=cmd_account_delete)

    # Ledger ---------------------------------------------------------------- #
    p = sub.add_parser("ledger", aliases=["trades"], help="List ledger entries (journaled trades).")
    _add_ledger_filters(p)
    p.add_argument("--limit", type=int, help="Max results (default 100).")
    p.add_argument("--offset", type=int, help="Results to skip (default 0).")
    p.set_defaults(func=cmd_ledger)

    p = sub.add_parser("entry-get", help="Get one ledger entry by UUID.")
    p.add_argument("id")
    p.set_defaults(func=cmd_entry_get)

    p = sub.add_parser("entry-create", help="Create a single ledger entry.")
    _add_entry_fields(p)
    p.add_argument("--account-id", help="Target account; uses Default if omitted.")
    p.set_defaults(func=cmd_entry_create)

    p = sub.add_parser("entry-update", help="Update fields on a ledger entry.")
    p.add_argument("id")
    _add_entry_fields(p)
    p.set_defaults(account_id=None, func=cmd_entry_update)

    p = sub.add_parser("entry-delete", help="Delete a single ledger entry.")
    p.add_argument("id")
    p.add_argument("--yes", action="store_true", help="Confirm this irreversible delete.")
    p.set_defaults(func=cmd_entry_delete)

    p = sub.add_parser("entry-batch", help="Bulk-create entries from a JSON file (or '-' for stdin).")
    p.add_argument("--file", required=True, help="Path to JSON array or {\"entries\":[...]}, or '-'.")
    p.set_defaults(func=cmd_entry_batch)

    sub.add_parser("recalculate-pnl", help="Recompute realized P&L for all SELL entries.").set_defaults(func=cmd_recalculate_pnl)

    p = sub.add_parser("ledger-delete-all", help="DELETE ALL ledger entries (every account).")
    p.add_argument("--yes", action="store_true", help="Confirm this irreversible delete.")
    p.set_defaults(func=cmd_ledger_delete_all)

    p = sub.add_parser("export-csv", help="Download ledger entries as CSV.")
    _add_ledger_filters(p)
    p.add_argument("-o", "--output", help="Write to this file instead of stdout.")
    p.set_defaults(func=cmd_export_csv)

    # Metadata -------------------------------------------------------------- #
    p = sub.add_parser("metadata", help="List metadata on a ledger entry.")
    p.add_argument("id")
    p.set_defaults(func=cmd_metadata)

    p = sub.add_parser("metadata-add", help="Add a key/value metadata record to an entry.")
    p.add_argument("id")
    p.add_argument("--key", required=True)
    p.add_argument("--value", required=True)
    p.set_defaults(func=cmd_metadata_add)

    p = sub.add_parser("metadata-delete", help="Delete a metadata record by its ID.")
    p.add_argument("id", help="Ledger entry UUID.")
    p.add_argument("metadata_id", help="Metadata record UUID.")
    p.set_defaults(func=cmd_metadata_delete)

    # Assets ---------------------------------------------------------------- #
    sub.add_parser("assets", help="List registered assets.").set_defaults(func=cmd_assets)

    p = sub.add_parser("asset-get", help="Get one registered asset by UUID.")
    p.add_argument("id")
    p.set_defaults(func=cmd_asset_get)

    p = sub.add_parser("asset-create", help="Register a new asset.")
    p.add_argument("--symbol", required=True, help="Must be unique.")
    p.add_argument("--name", required=True)
    p.add_argument("--precision", required=True, help="Decimal places.")
    p.set_defaults(func=cmd_asset_create)

    p = sub.add_parser("asset-update", help="Update a registered asset's name/precision.")
    p.add_argument("id")
    p.add_argument("--name")
    p.add_argument("--precision")
    p.set_defaults(func=cmd_asset_update)

    p = sub.add_parser("asset-delete", help="Remove an asset from the registry.")
    p.add_argument("id")
    p.add_argument("--yes", action="store_true", help="Confirm the delete.")
    p.set_defaults(func=cmd_asset_delete)

    # Tokens ---------------------------------------------------------------- #
    sub.add_parser("tokens", help="List your personal access tokens.").set_defaults(func=cmd_tokens)

    p = sub.add_parser("token-create", help="Create a PAT (value returned once).")
    p.add_argument("--name", required=True)
    p.set_defaults(func=cmd_token_create)

    p = sub.add_parser("token-revoke", help="Revoke a personal access token by ID.")
    p.add_argument("id")
    p.set_defaults(func=cmd_token_revoke)

    return parser


def main():
    _load_dotenv()
    args = build_parser().parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
