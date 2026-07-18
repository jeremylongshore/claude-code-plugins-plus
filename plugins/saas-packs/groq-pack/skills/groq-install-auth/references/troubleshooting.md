# Groq Install & Auth Troubleshooting

Full error matrix for install and authentication failures. Match the error text
you see to the row, then apply the solution.

| Error | Cause | Solution |
|-------|-------|----------|
| `401 Invalid API Key` | Key missing, revoked, or mistyped | Verify key at console.groq.com/keys |
| `MODULE_NOT_FOUND groq-sdk` | SDK not installed | Run `npm install groq-sdk` |
| `ModuleNotFoundError: No module named 'groq'` | Python SDK missing | Run `pip install groq` |
| `ENOTFOUND api.groq.com` | Network/DNS issue | Check internet connectivity and firewall |

## Diagnostic checklist

1. Confirm the variable is actually exported in the current shell:
   `echo "${GROQ_API_KEY:0:4}"` should print `gsk_` (never echo the full key).
2. Confirm the key starts with `gsk_` and has no surrounding quotes or trailing
   whitespace from a copy/paste.
3. If the key is stored in `.env`, confirm your process actually loads it — Node
   needs `dotenv` (or `--env-file=.env` on Node 20+); Python needs
   `python-dotenv` or the variable exported in the shell.
4. If `models.list()` returns 401 but the key looks right, regenerate the key in
   the console — a rotated or revoked key returns 401 with a valid-looking value.
