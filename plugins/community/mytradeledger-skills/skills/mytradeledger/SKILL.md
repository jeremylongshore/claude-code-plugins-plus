---
name: mytradeledger
description: >-
  Access and manage your MyTradeLedger journaled crypto trades through its REST
  API — list/create/update/delete ledger entries (trades), list accounts and
  read their open-position balances and realized P&L, bulk-import entries,
  export the ledger as CSV, manage the asset registry, attach metadata to
  entries, and manage personal access tokens. Authenticates with a PAT via the
  MTL_TOKEN and MTL_URL environment variables. Use when the user wants to view,
  journal, import, or export trades, or check P&L/balances on MyTradeLedger.
  Triggers: "show my MyTradeLedger trades", "log a BTC buy", "what's my realized
  P&L", "export my ledger to CSV", "my open positions", "import these trades".
---

# mytradeledger

Read and manage journaled crypto trades on MyTradeLedger with one stdlib-only
Python script — no `pip install` required.

## Setup check (do this first if unsure)

Config comes from a host-local `.env` file in the skill directory, which the
script auto-loads on every run (real environment variables, if set, take
precedence):

- `MTL_URL` — base URL of the instance, **no trailing `/api`**. Defaults to the
  hosted `https://mytradeledger.com`; set it to your self-host (e.g.
  `https://mytradeledger.home.arpa`) if needed.
- `MTL_TOKEN` — a MyTradeLedger personal access token.

`.env` is gitignored and must never be committed; `.env.sample` is the committed
template. If `.env` is missing, create it: `cp .env.sample .env && chmod 600 .env`,
then fill in real values. The token is sent as an `Authorization: Bearer …`
header and never printed. If a call returns 401/403, `.env` is missing/unfilled
or the token is wrong — tell the user to populate `.env` (see this skill's
`README.md`); **do not** ask them to paste the token into the chat. Run `whoami`
to confirm auth.

Run everything through the helper (commands assume the skill directory as cwd):

```bash
python3 scripts/mtl.py <command> ...
```

Output is the JSON API response (pretty-printed); the exit code is non-zero on
any non-2xx response. Successful payloads are wrapped in a `{"data": …}`
envelope, and list endpoints add `{"meta": {"total","limit","offset"}}`.
`export-csv` is the one exception — it streams raw CSV text.

## Confirm auth

```bash
python3 scripts/mtl.py whoami        # the authenticated user; verifies the token
```

## Ledger entries (journaled trades)

A ledger entry is one journaled transaction. `entryType` is one of `BUY`,
`SELL`, `FEE`, `DEPOSIT`, `WITHDRAWAL`, `ADJUSTMENT`. Realized P&L is computed
on `SELL` entries; `quantity`/`price`/`fee`/`valueBase`/`pnl` come back as
**strings** to preserve precision.

```bash
# List — all filters optional; symbol is case-sensitive, e.g. BTC/USD
python3 scripts/mtl.py ledger                                   # (alias: trades)
python3 scripts/mtl.py ledger --symbol BTC/USD --entry-type BUY --limit 20
python3 scripts/mtl.py ledger --start-date 2025-01-01 --end-date 2025-12-31 --offset 100

python3 scripts/mtl.py entry-get entry-uuid-1

# Create one entry (symbol, entry-type, quantity, price required;
# fee/timestamp/notes/account-id optional — Default account if account-id omitted)
python3 scripts/mtl.py entry-create \
  --symbol BTC/USD --entry-type BUY --quantity 1.0 --price 60000 \
  --fee 9.99 --timestamp 2026-01-15T10:30:00Z --notes "Initial purchase"

# Update (only provided fields change; pass 'null' to clear fee/notes)
python3 scripts/mtl.py entry-update entry-uuid-1 --price 61000 --notes null
```

### Bulk import

`entry-batch` posts many entries at once. Pass a JSON file that is either a bare
array of entry objects or `{"entries": [...]}`; use `-` to read from stdin.

```bash
python3 scripts/mtl.py entry-batch --file trades.json
cat trades.json | python3 scripts/mtl.py entry-batch --file -
```

Each entry uses the same fields as `entry-create` (`symbol`, `entryType`,
`quantity`, `price`, optional `fee`/`timestamp`/`notes`/`accountId`).

### P&L recompute

```bash
python3 scripts/mtl.py recalculate-pnl   # recompute realized P&L for all SELL entries
```

## Accounts

```bash
python3 scripts/mtl.py accounts                          # active accounts
python3 scripts/mtl.py accounts --include-archived
python3 scripts/mtl.py account-get acc-uuid-1
python3 scripts/mtl.py account-balance acc-uuid-1        # net open quantity per symbol
python3 scripts/mtl.py account-pnl acc-uuid-1            # total realized P&L (in base currency)

python3 scripts/mtl.py account-create --name "Roth IRA" --base-currency USD
python3 scripts/mtl.py account-update acc-uuid-1 --name "Main"
python3 scripts/mtl.py account-set-default acc-uuid-1
python3 scripts/mtl.py account-archive acc-uuid-1
python3 scripts/mtl.py account-unarchive acc-uuid-1
```

`baseCurrency` defaults to `USD` and drives P&L reporting.

## Export to CSV

Accepts the same filters as `ledger`. Writes to stdout, or to a file with `-o`.
URL-encoding of the symbol slash is handled for you — pass `BTC/USD` literally.

```bash
python3 scripts/mtl.py export-csv -o ledger.csv
python3 scripts/mtl.py export-csv --symbol BTC/USD --start-date 2025-01-01 --end-date 2025-12-31 -o btc-2025.csv
```

## Entry metadata

Attach arbitrary key/value records to a ledger entry (e.g. an order id or tax
lot). Multiple records may share a key.

```bash
python3 scripts/mtl.py metadata entry-uuid-1
python3 scripts/mtl.py metadata-add entry-uuid-1 --key orderId --value ORD-8821
python3 scripts/mtl.py metadata-delete entry-uuid-1 meta-uuid-2
```

## Asset registry

```bash
python3 scripts/mtl.py assets
python3 scripts/mtl.py asset-get asset-uuid-1
python3 scripts/mtl.py asset-create --symbol SOL --name Solana --precision 9
python3 scripts/mtl.py asset-update asset-uuid-1 --name "Solana"
```

## Personal access tokens

```bash
python3 scripts/mtl.py tokens                       # list tokens
python3 scripts/mtl.py token-create --name "cli"    # the value is shown ONCE — store it
python3 scripts/mtl.py token-revoke token-uuid-1
```

## Working safely

- **Destructive commands require `--yes`.** `account-delete`, `entry-delete`,
  and `ledger-delete-all` permanently remove data and will refuse to run without
  the flag:

  ```bash
  python3 scripts/mtl.py entry-delete entry-uuid-1 --yes
  python3 scripts/mtl.py ledger-delete-all --yes        # wipes EVERY account's entries
  ```

  Always show the user what will be deleted and get explicit agreement before
  passing `--yes`. Default to read-only commands (`ledger`, `accounts`,
  `account-balance`, `account-pnl`, `export-csv`) when exploring.
- **Paging.** `ledger` returns `meta.total`; default page size is 100. Use
  `--limit`/`--offset` to walk large ledgers rather than assuming one page is
  everything.
- **Precision.** Numeric ledger fields are strings on the way out — don't round
  or coerce them when reporting figures back to the user.

## Failure handling

- 401 / 403 → token missing, wrong, or revoked. Point the user to the README;
  do not request the token in chat. Re-run `whoami` after they fix `.env`.
- 404 → account/entry/asset id not found (or not owned by this token). Re-list
  to get a valid UUID.
- 422 → invalid payload (bad `entryType`, non-positive quantity/price, malformed
  date). The JSON body names the problem.
- 402 → a paid-plan limit was hit (the free tier caps total trades). The body
  explains the upgrade requirement.
- Network errors are reported as `{"error":"network",...}`; the script never
  prints the token.
