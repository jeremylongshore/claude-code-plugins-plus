# Onboarding — plug a teammate into Bob's Big Brain

Two real steps for a non-technical teammate to go from zero to connected:

1. **Install Tailscale** and sign in with their `@intentsolutions.io` account
   (this is the one genuinely-manual prerequisite — the GUI *Allow* dialogs can't
   be automated).
2. **Double-click [`install-bobs-big-brain.command`](install-bobs-big-brain.command).**
   It checks tailnet reachability, takes their token (typed hidden), writes
   `~/.teamkb/team.json` at mode `600`, and installs the plugin.

That's it. The installer prints one green line and a `/brain` question to try.

## How the connection actually works

The plugin (`src/index.ts`) resolves its mode at startup with this precedence,
**per key**:

```
real environment variable  →  ~/.teamkb/team.json  →  (absent → local mode)
```

`team.json` is the fix for the day-one failure where a teammate set
`TEAMKB_API_URL` in `~/.zshrc`, but a **GUI/Dock-launched Claude never sources
`~/.zshrc`**, so the vars were absent and the plugin silently ran an empty *local*
brain. A file on disk doesn't depend on the launching shell, so it works from a
double-click.

`team.json` shape (the installer writes exactly this, mode `600`):

```json
{
  "apiUrl": "http://100.109.119.103:3847",
  "apiToken": "<the teammate's per-user bearer token>",
  "tenantId": "intent-solutions"
}
```

**Fail-closed, by design:** a `team.json` that is present but group/world-readable,
unreadable, or not valid JSON makes the plugin **refuse to start** with a clear
message — it does *not* silently fall back to the local brain. A teammate who has a
`team.json` wants team mode; a broken one is an error worth surfacing, not laundering.

## For the admin (Jeremy)

- **Auth-free install.** The installer adds **this public repo as its own marketplace**
  (`claude plugin marketplace add jeremylongshore/governed-second-brain-plugin` →
  `claude plugin install governed-second-brain@governed-second-brain`), so a teammate needs **no**
  `intent-solutions-io` org membership, no private-repo access, and no `gh` login — the earlier
  "repository not found" Prereq-0 is gone.
- **Merge-gated.** The marketplace source tracks this repo's `main` branch unpinned, so
  `claude plugin install` pulls the `main` bundle — only distribute the `.command` after the
  behaviour it depends on is merged to `main`.
- Mint the per-user token, then hand the teammate **the token and this `.command`
  over the same trusted channel** (email/DM). You may pre-fill `TOKEN=` and `NAME=`
  at the top of the `.command` so they *only* double-click — but leaving `TOKEN`
  empty (they paste it) keeps the secret out of the file entirely.
- The token **never** lands in `~/.claude.json`, shell history, argv, or a chat
  transcript — only in `~/.teamkb/team.json` at mode `600`.
- Gatekeeper will flag an unsigned `.command` as "unidentified developer" until we
  ship a signed build (Phase 2): right-click → **Open** clears it.
