# TweetClaw

X/Twitter automation plugin for OpenClaw and compatible agents. Post tweets, reply, like, retweet, follow, DM, search, extract bulk data, monitor accounts, and run giveaway draws.

Powered by the [Xquik REST API](https://docs.xquik.com) with 121 endpoints across 12 categories.

## Installation

```bash
/plugin install tweetclaw@claude-code-plugins-plus
```

### Alternative installs

```bash
# Via OpenClaw
openclaw plugins install @xquik/tweetclaw

# Via npx
npx skills add Xquik-dev/tweetclaw
```

## Configuration

Get an API key from [xquik.com](https://xquik.com):

```bash
openclaw config set plugins.entries.tweetclaw.config.apiKey "$XQUIK_API_KEY"
```

Or set the environment variable:

```bash
export XQUIK_API_KEY="xq_YOUR_KEY_HERE"
```

## Features

- **121 REST API endpoints** across 12 categories
- **23 bulk extraction tools** (followers, replies, quotes, mentions, communities, lists, spaces)
- **2 MCP tools** via hosted server at `xquik.com/mcp` ([setup guide](https://docs.xquik.com/mcp/overview))
- **2 slash commands** (`/xstatus` for account info, `/xtrends` for trending topics)
- **Account monitoring** with webhook and Telegram delivery
- **Giveaway draws** with configurable filters
- **AI tweet composition** with algorithm scoring

## Usage Examples

### Search tweets

```
Search for recent tweets about "AI agents"
```

### Post a tweet

```
Post a tweet saying "Hello from TweetClaw!"
```

### Extract followers

```
Extract the first 1000 followers of @elonmusk
```

### Monitor an account

```
Set up monitoring for @openai and notify me via webhook when they post
```

### Run a giveaway

```
Run a giveaway draw from the replies to this tweet: https://x.com/example/status/123
Pick 3 winners who retweeted and follow @example
```

## Pricing

Credit-based pricing via Xquik. 1 credit = $0.00015.

| Operation | Credits | Cost |
|-----------|---------|------|
| Read (tweet, search, timeline) | 1 | $0.00015 |
| Read (user profile) | 2 | $0.0003 |
| Write (tweet, like, follow, DM) | 10 | $0.0015 |
| Extraction | 1-5/result | $0.00015-0.00075/result |
| Monitors, webhooks, compose | 0 | Free |

## Documentation

- [Full API docs](https://docs.xquik.com)
- [Skill reference](./skills/tweetclaw/SKILL.md)
- [Source repository](https://github.com/Xquik-dev/tweetclaw)

## License

MIT
