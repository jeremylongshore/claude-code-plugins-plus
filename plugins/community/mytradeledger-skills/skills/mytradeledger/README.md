# mytradeledger skill

Access and manage your [MyTradeLedger](https://mytradeledger.com) journaled
crypto trades from Claude Code through the MyTradeLedger REST API. One
stdlib-only Python script (`scripts/mtl.py`) — no `pip install` required.

## What it can do

- **Ledger entries (trades):** list (with symbol / type / date filters and
  paging), get, create, update, delete, bulk-import, and recompute realized P&L.
- **Accounts:** list (incl. archived), get, create, update, archive/unarchive,
  set-default, and read per-account open-position balances and realized P&L.
- **Export:** download the ledger as CSV.
- **Metadata:** attach/list/delete key-value records on a ledger entry.
- **Asset registry:** list/get/create/update/delete registered assets.
- **Tokens:** list, create, and revoke personal access tokens.

See `SKILL.md` for the full command reference.

## Configuration

Configuration is read from a host-local `.env` file in this directory, which the
script auto-loads on every run. A real environment variable of the same name
overrides the `.env` value.

| Key | Required | Meaning |
| --- | --- | --- |
| `MTL_TOKEN` | yes | Personal access token, sent as `Authorization: Bearer <token>`. |
| `MTL_URL` | no | Base URL of the instance, **no trailing `/api`**. Defaults to `https://mytradeledger.com`. Set to your self-host (e.g. `https://mytradeledger.home.arpa`) if applicable. |

### First-time setup

```bash
cd ~/.claude/skills/mytradeledger   # (or wherever this skill lives)
cp .env.sample .env
chmod 600 .env
# then edit .env and paste your real token
```

Generate a token in the MyTradeLedger web app under **Settings → API Tokens**
(route `/app/settings/tokens`). Copy it once and paste it into `.env` as
`MTL_TOKEN`. Verify with:

```bash
python3 scripts/mtl.py whoami
```

`.env` is gitignored (covered by the repo's `.gitignore`) and must never be
committed. `.env.sample` is the committed template and contains no secrets.

## API shape

- Base URL: `<MTL_URL>/api` (e.g. `https://mytradeledger.com/api`).
- Auth: `Authorization: Bearer <MTL_TOKEN>` on every request.
- Success responses are wrapped as `{"data": ...}`; list endpoints add
  `{"meta": {"total","limit","offset"}}`.
- Numeric ledger fields (`quantity`, `price`, `fee`, `valueBase`, `pnl`) are
  returned as **strings** to preserve precision.

Reference docs: <https://mytradeledger.com/docs/overview>

## Safety

Destructive commands (`account-delete`, `entry-delete`, `ledger-delete-all`)
refuse to run without an explicit `--yes` flag. The script prints the token in
no code path; auth failures point you back here rather than echoing secrets.
