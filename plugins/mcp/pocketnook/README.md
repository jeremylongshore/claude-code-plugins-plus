# pocketnook MCP server

Deploy a repository to a private URL without leaving the agent that wrote it.

```
> deploy this somewhere private

  owner/studio-board is deployed: https://pocketnook.dev/s/nook-…/
  It is private — only you can open it until you share it. (static, 42 files)
```

The deploy step belongs inside the tool where the software is being written,
which is both the distribution and the product.

## Install

**1. Get a token.** Sign in at [pocketnook.dev](https://pocketnook.dev), open
**Agent access** on the home page, and create one. It is shown once.

**2. Add the server.**

```sh
claude mcp add pocketnook \
  --env POCKETNOOK_TOKEN=pnka_… \
  -- npx -y @pocketnook/mcp
```

Or, from a checkout of this repository, point at the entry directly:

```sh
claude mcp add pocketnook \
  --env POCKETNOOK_TOKEN=pnka_… \
  -- node /absolute/path/to/apps/mcp/bin/pocketnook-mcp.mjs
```

The server has no dependencies and runs on Node 22.18 or newer — the floor
`package.json` declares, so an older Node warns rather than silently half-works.
Any MCP client works; the commands above are Claude Code's.

**3. Optionally add the skill**, which teaches the agent the things the tool
descriptions cannot say on their own — that a deploy builds what is pushed
rather than what is on disk, and that sharing does not notify anyone:

```sh
cp -r skills/pocketnook ~/.claude/skills/
```

### Or install both at once, as a Claude Code plugin

This repository is also a Claude Code plugin: the skill above and the MCP
server, wired together, with the token read from your environment.

```sh
claude plugin marketplace add shotintoeternity/pocketnook-mcp
claude plugin install pocketnook@pocketnook-mcp
```

Then check it: `claude plugin details pocketnook@pocketnook-mcp` should report
one skill and one MCP server.

That check is worth running, because the obvious one does not cover it.
`claude plugin validate` reads `plugin.json` and the skills, and **does not
read `.mcp.json` at all** — it reports `✔ Validation passed` on a plugin whose
`.mcp.json` is not even parseable JSON. `details` is what counts the
components, and it reports `MCP servers (0)` for exactly that plugin.

The marketplace manifest and the plugin manifest are both here, in one
repository, because a plugin-only repository is not installable: `plugin
marketplace add` fails with *Marketplace file not found*, and `plugin install`
answers *not found in any configured marketplace*. `.claude-plugin/marketplace.json`
lists this repository's root as its one plugin.

## Configuration

| Variable | Meaning |
|---|---|
| `POCKETNOOK_TOKEN` | An agent token. Required. |
| `POCKETNOOK_URL` | Base URL, if not `https://pocketnook.dev`. |

## Tools

| Tool | What it does |
|---|---|
| `deploy` | Deploy a GitHub repository — the tip of its default branch — and return its private URL. |
| `deploy_directory` | Deploy a directory from this machine as it is on disk. No repository needed. |
| `list_nooks` | Everything this account has deployed, with URLs and status. |
| `nook_logs` | Build output — the first thing to read when a deploy went wrong. |
| `stop_nook` | Take a nook offline, keeping its URL, grants, and secrets. |

### The two deploys, and why they are two tools

`deploy` builds what GitHub has. `deploy_directory` uploads what is on the disk,
including uncommitted work, and needs no repository at all. It exists because
the person an agent is writing for may never make a push.

They are not merged into one tool with a heuristic, because the heuristic has
two silent failure modes: guess towards the repository and an afternoon of work
is quietly not deployed; guess towards the directory and half-finished local
edits go live. Neither announces itself, which is what makes the guess
unaffordable: a wrong answer that stays quiet is worse than a question.

### What is deliberately absent

There is no `delete` tool. Deleting a nook destroys its grants and secrets and
cannot be undone, so it stays a decision made on a page that can say so; `stop`
is the recoverable version of the same intent. There is nothing for managing
tokens either — the gateway refuses a token on `/api/tokens` entirely, so an
agent cannot extend its own credential or revoke the one being used to stop it.

**`share_nook` and `set_nook_secret` were removed on 2026-08-01.** They shipped
here on 2026-07-27 and then a design decision made both routes session-only —
*a token deploys, a session administers.* They did not
become ill-advised, they became impossible: `sessionOnly` in the gateway answers
any bearer token with 401. A tool that can never succeed is worse than no tool,
because an agent reads the refusal as transient and retries it. Setting a
secret, sharing a nook and deleting one all happen in the browser now, and the
server's MCP `instructions` say so, so a model sends its person there rather
than inventing a workaround such as committing the secret into the project.

## What the token can and cannot do

An agent token acts as the account that minted it, on that account's own nooks.
Three limits are enforced by pocketnook's gateway, and tested there — they are
properties of the server, not of this client, so a modified copy of this code
cannot widen them:

- **It cannot mint or revoke a token.** Only a browser session can, so a leaked
  token cannot renew itself, and revoking always has somewhere to happen from.
- **It carries no email or GitHub username claim.** Access to someone else's
  nook is granted to a username or a verified email domain, and a token holds
  neither — so it can act as an owner but can never become a viewer.
- **It cannot open a nook.** `/s/:id/` reads the session cookie and nothing
  else. A token is one more way to deploy and no new way to read.

Tokens are stored as a SHA-256 hash, expire after 90 days, and can be revoked
from the same panel that created them.

## Known limits

- **Builds are synchronous.** A deploy holds the request until the build
  finishes, and this client waits up to 15 minutes. Clients apply their own tool
  timeout on top of that; if a build outlasts it, the build still completes —
  check `list_nooks` or pocketnook.dev/home rather than deploying again.
- **A disconnecting client cancels a build.** Same root cause: there is no
  queue, so the build lives in the request.
- **Root-relative assets.** A nook is served under `/s/:id/`, so an app that
  requests `/logo.png` escapes its own prefix. Apps that use relative paths (for
  example Vite's `base: './'`) are unaffected.
- **`deploy_directory` needs `tar` on the PATH**, and refuses a directory that
  contains your home directory — packing `~` would upload SSH keys and cloud
  credentials along with the project. Uploads are capped at 32 MB by the
  gateway; `node_modules`, `.git` and build caches are left out.
- **A build log is somebody else's output.** Control characters are stripped
  before it reaches the agent, and it arrives inside `--- begin build output ---`
  markers that say whose text it is. That is a mitigation, not a fix: an
  instruction written into a build log is ordinary text and no escaping removes
  it. The markers give the model the context to discount it.

## Development

```sh
npm test          # node --test, no dependencies
```

To drive the protocol by hand:

```sh
printf '%s\n' '{"jsonrpc":"2.0","id":1,"method":"tools/list"}' | node bin/pocketnook-mcp.mjs
```
