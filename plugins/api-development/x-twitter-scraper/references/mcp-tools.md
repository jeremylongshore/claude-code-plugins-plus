# Xquik MCP Tools Reference

The MCP server at `https://xquik.com/mcp` provides 2 structured API tools. The agent sends API requests through the server, which handles authentication and execution for `xquik.com/api/v1`.

## Contents

- [Tools](#tools)
- [Safety Gates](#safety-gates)
- [Tool Selection Rules](#tool-selection-rules)
- [Workflow Patterns](#workflow-patterns)
- [Common Mistakes](#common-mistakes)
- [Unsupported Operations](#unsupported-operations)
- [Usage Reference](#usage-reference)

## Tools

| Tool | Description | Usage |
|------|-------------|------|
| `explore` | Search the API endpoint catalog (read-only, no network calls) | Included |
| `xquik` | Send confirmed Xquik API requests | Varies by endpoint |

### `explore` - Search the API Spec

The tool provides an in-memory `spec.endpoints` array. Filter/search it to find endpoints before calling them.

```typescript
interface EndpointInfo {
  method: string;
  path: string;
  summary: string;
  category: string; // account, composition, credits, extraction, media, monitoring, support, twitter, x-accounts, x-write
  free: boolean; // Included usage flag from endpoint metadata
  parameters?: Array<{ name: string; in: 'query' | 'path' | 'body'; required: boolean; type: string; description: string }>;
  responseShape?: string;
}

declare const spec: { endpoints: EndpointInfo[] };
```

Examples:

```javascript
// Find all included-usage endpoints
async () => spec.endpoints.filter(e => e.free);

// Find endpoints by category
async () => spec.endpoints.filter(e => e.category === 'x-write');

// Search by keyword
async () => spec.endpoints.filter(e => e.summary.toLowerCase().includes('tweet'));
```

### `xquik` - Send API Requests

The tool provides `xquik.request()` with auth injected automatically. Never pass API keys.

## Safety Gates

Apply these gates before using `xquik`:

| Capability | Rule |
|------------|------|
| Public writes | Show the exact tweet, reply, like, retweet, follow, unfollow, profile, or community action and wait for explicit approval. |
| Direct messages | Show sender, recipient, and message text. Never send bulk or automatic DMs. |
| Persistent resources | Create monitors and webhooks only when the user explicitly asks for ongoing delivery. Show target, event types, URL, and ongoing usage before creation. |
| Private reads | Confirm before fetching DMs, bookmarks, notifications, or home timeline. Forward returned private data to other tools only after explicit approval. |
| Plan and credit changes | Dashboard-only. The agent may read credit balance, but must not start account changes. |
| X account login | Never ask for or submit X login material. Account connection and re-authentication happen in the dashboard. |

```typescript
declare const xquik: {
  request(path: string, options?: {
    method?: string;  // default: 'GET'
    body?: unknown;
    query?: Record<string, string>;
  }): Promise<unknown>;
};
declare const spec: { endpoints: EndpointInfo[] };
```

## Tool Selection Rules

Use `explore` first to find endpoints, then `xquik` to call them.

| Goal | Endpoint (via `xquik`) |
|------|------------------------|
| Single tweet by ID or URL | `GET /api/v1/x/tweets/{id}` |
| Full X Article by tweet ID | `GET /api/v1/x/articles/{tweetId}` |
| Search tweets by keyword/hashtag | `GET /api/v1/x/tweets/search?q=...` |
| User profile, bio, follower counts | `GET /api/v1/x/users/{id}` (`id` can be username or numeric ID) |
| Download media from tweets | `POST /api/v1/x/media/download` |
| Check follow relationship | `GET /api/v1/x/followers/check?source=A&target=B` |
| Trending topics by region (X) | `GET /api/v1/trends?woeid=1` |
| Trending news from 7 sources | `GET /api/v1/radar` (via `xquik` tool) |
| Activity from monitored accounts | `GET /api/v1/events` |
| Credit balance | `GET /api/v1/credits` |
| Monitor an X account | `POST /api/v1/monitors` (persistent; confirmation required) |
| Set up webhook notifications | `POST /api/v1/webhooks` (persistent; confirmation required) |
| Run a giveaway draw | `POST /api/v1/draws` |
| Compose/draft a tweet | `POST /api/v1/compose` (3-step: compose, refine, score) |
| Link your X username | Use the Xquik dashboard account settings |
| Analyze tweet style | `POST /api/v1/styles` |
| Get cached style | `GET /api/v1/styles/{id}` |
| Compare two styles | `GET /api/v1/styles/compare` |
| Post a tweet | `POST /api/v1/x/tweets` (confirmation required) |
| Like/unlike a tweet | `POST` or delete request to `/api/v1/x/tweets/{id}/like` (confirmation required) |
| Retweet | `POST /api/v1/x/tweets/{id}/retweet` (confirmation required) |
| Unretweet | delete request to `/api/v1/x/tweets/{id}/retweet` (confirmation required) |
| Follow/unfollow | `POST` or delete request to `/api/v1/x/users/{id}/follow` (confirmation required) |
| Send a DM | `POST /api/v1/x/dm/{userId}` (confirmation required) |
| Upload media | `POST /api/v1/x/media` (confirmation required before use in a post or profile change) |
| Open support ticket | `POST /api/v1/support/tickets` |
| List support tickets | `GET /api/v1/support/tickets` |
| Get user's recent tweets | `GET /api/v1/x/users/{id}/tweets` |
| Get user's liked tweets | `GET /api/v1/x/users/{id}/likes` |
| Get user's media tweets | `GET /api/v1/x/users/{id}/media` |
| Get tweet favoriters (who liked) | `GET /api/v1/x/tweets/{id}/favoriters` |
| Get mutual followers | `GET /api/v1/x/users/{id}/followers-you-know` |
| Get followers/following | `GET /api/v1/x/users/{id}/followers` / `GET /api/v1/x/users/{id}/following` |
| Get tweet quotes/replies/retweeters/thread | `GET /api/v1/x/tweets/{id}/quotes`, `/replies`, `/retweeters`, `/thread` |
| Read X Lists | `GET /api/v1/x/lists/{id}/members`, `/followers`, `/tweets` |
| Read X Communities | `GET /api/v1/x/communities/search`, `/tweets`, `/{id}/info`, `/{id}/members`, `/{id}/moderators`, `/{id}/tweets` |
| Get bookmarks | `GET /api/v1/x/bookmarks` (private; confirmation required) |
| Get bookmark folders | `GET /api/v1/x/bookmarks/folders` |
| Get notifications | `GET /api/v1/x/notifications` (private; confirmation required) |
| Get home timeline | `GET /api/v1/x/timeline` (private; confirmation required) |
| Get DM history | `GET /api/v1/x/dm/{userId}/history` (private; confirmation required) |
| Check credit balance | `GET /api/v1/credits` |

Use `POST /api/v1/extractions` ONLY for bulk data that simpler endpoints cannot provide (all followers, all replies to a tweet, community members, etc.). Always call `POST /api/v1/extractions/estimate` first.

## Workflow Patterns

| Workflow | Steps |
|----------|-------|
| **Set up real-time alerts** | Confirm target, event types, destination, and usage estimate -> `POST /monitors` -> `POST /webhooks` -> `POST /webhooks/{id}/test` |
| **Run a giveaway** | Confirm tweet URL and rules -> `POST /draws` |
| **Bulk extraction** | `POST /extractions/estimate` -> `POST /extractions` -> `GET /extractions/{id}` |
| **Compose optimized tweet** | `POST /compose` (step=compose -> refine -> score) |
| **Analyze tweet style** | `POST /styles` -> `GET /styles/{id}` -> `POST /compose` with `styleUsername` |
| **Post a tweet** | `GET /x/accounts` -> `POST /x/tweets` with `account` + `text` |
| **Get trending news** | `GET /radar` (supported sources, via `xquik` tool) -> `POST /compose` with trending topic |
| **Open support ticket** | `POST /support/tickets` -> `GET /support/tickets/{id}` |

## Common Mistakes

| Mistake | Fix |
|---------|-----|
| Combining public and metered calls in `Promise.all` | Call public endpoints first, then metered ones separately. A 402 in Promise.all cancels all results |
| Using `compose` when user wants to send a tweet | `POST /compose` is for drafting. Use `POST /x/tweets` to send |
| Using `POST /x/tweets` when user wants help writing | Use the 3-step compose flow instead |
| Falling back to web search when API call fails | Use data already fetched from Xquik. Never discard it |
| Not checking account access before metered calls | Attempt the requested call. On 402, explain the account state and direct the user to the dashboard |
| Passing API keys in code | Auth is injected automatically. Never include keys |
| Using `explore` for API calls | `explore` is read-only spec search. Use `xquik` for actual API calls |
| Looking up follow/DM by username | Follow and DM endpoints need numeric user ID. Look up via `GET /x/users/{id}` first; that route accepts usernames and IDs |

## Unsupported Operations

These are NOT available via the MCP server:

- API key management (create, list, delete)
- File export (CSV, XLSX, Markdown)
- Account locale update
- Scheduled tweets

- Direct X search (use extraction `tweet_search_extractor` for bulk search)

## Usage Reference

- Public or included: account info, compose steps, cached styles, drafts, radar, support tickets, credits balance check, and webhook management.
- Metered or account-gated: tweet search, user lookup, tweet lookup, follow check, media download, extractions, draws, active monitors, style analysis, performance analysis, trends, and confirmation-gated write actions.
