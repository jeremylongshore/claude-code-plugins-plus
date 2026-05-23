---
title: "Debugging Slack Integration: From 6 Duplicate Responses to Instant Acknowledgment"
description: "Real-world debugging of Slack webhook integration causing duplicate responses. Learn how Slack's 3-second timeout triggers retries and how to fix it with immediate HTTP 200 acknowledgment and background processing."
date: "2025-10-09"
tags: ["slack-api", "webhook-debugging", "background-processing", "api-integration", "production-debugging"]
featured: false
---
## The Problem: Bob Responded 6 Times to Every Message

I integrated my AI agent (Bob's Brain) with Slack, and it worked—sort of. Every time I sent a message, Bob responded **six times with the exact same answer**. The Cloudflare Tunnel logs showed constant timeout errors:

```
2025-10-09T08:12:20Z ERR Request failed error="Incoming request ended abruptly: context canceled"
```

This wasn't a "minor bug"—this was a production-breaking issue that made the integration unusable.

## The Journey: What Actually Happened

### Starting Point: Unstable Tunnels

Before we even got to Slack, we had tunnel stability issues:

**localhost.run** kept changing URLs:

- `cf011aadb6f85d.lhr.life`
- `0ca4fddc58e906.lhr.life`
- `7aa0d045663613.lhr.life`

Every URL change required updating Slack Event Subscriptions. Not sustainable.

**Solution:** Switched to **Cloudflare Tunnel** (`cloudflared`)

- Free, no account required for testing
- Stable URL: `https://editor-steering-width-innovation.trycloudflare.com`
- Persists as long as the process runs

```bash
# Install cloudflared
curl -sLO https://github.com/cloudflare/cloudflared/releases/latest/download/cloudflared-linux-amd64.deb
sudo dpkg -i cloudflared-linux-amd64.deb

# Start tunnel in background
nohup cloudflared tunnel --url http://localhost:8080 > /tmp/cloudflared.log 2>&1 &
```

### Side Quest: LlamaIndex API Migration

While setting up Slack, Bob's Knowledge Orchestrator was throwing deprecation warnings:

```python
# OLD (deprecated)
from llama_index.core import ServiceContext, set_global_service_context
service_context = ServiceContext.from_defaults(llm=llm, chunk_size=512)
set_global_service_context(service_context)

# NEW (Settings API)
from llama_index.core import Settings
Settings.llm = llm
Settings.chunk_size = 512
```

**Why this mattered:** Bob integrates three knowledge sources (653MB Knowledge DB, Analytics DB, Research index). The deprecation was blocking clean initialization.

**Result after fix:**

```
✅ Knowledge orchestrator initialized successfully
```

### The Main Problem: Slack's 3-Second Timeout

Slack verified the webhook URL successfully. Bob started responding to messages. But every message triggered **6 duplicate responses**.

**Initial code flow:**

1. Slack sends webhook event
2. Bob processes entire LLM query (10-60 seconds)
3. Bob sends Slack message
4. Bob returns HTTP 200

**Slack's behavior:**

- Waits 3 seconds for HTTP 200
- No response? **Retry the event**
- Keeps retrying until it gets acknowledgment
- Result: 4-6 duplicate event deliveries

### The Debugging Process

**First attempt:** "Maybe it's the tunnel?"

- Checked tunnel logs: Connection stable
- Tested endpoint locally: `curl http://localhost:8080/slack/events` → Works fine

**Second attempt:** "Maybe it's LLM response time?"

- Ollama (local): 5-15 seconds
- Groq (cloud): 2-8 seconds
- Even fastest responses exceeded Slack's 3-second window

**Root cause identified:**

```python
@app.post("/slack/events")
def slack_events():
    # ... validation ...

    # ❌ PROBLEM: This takes 10-60 seconds
    answer = llm(prompt)
    slack_client.chat_postMessage(channel=channel, text=answer)

    # By the time we return HTTP 200, Slack has retried 4-6 times
    return jsonify({"ok": True})
```

## The Solution: Immediate Acknowledgment + Background Processing

**Key insight:** Slack doesn't need to wait for the LLM response. It just needs to know we received the event.

### Implementation

**1. Create background processing function:**

```python
_slack_event_cache = {}  # Deduplication cache

def _process_slack_message(text, channel, user, event_id):
    """Background processing - can take as long as needed"""
    try:
        # 1. Check cache
        cached = get_cached_llm_response(text)
        if cached:
            slack_client.chat_postMessage(channel=channel, text=cached['answer'])
            return

        # 2. Get conversation history
        history = get_conversation_history(user, limit=10)

        # 3. Route to optimal LLM
        routing = ROUTER.route(text)

        # 4. Query knowledge bases if complex
        knowledge_context = ""
        if routing['complexity'] > 0.3:
            knowledge_context = KNOWLEDGE.query(text, mode='auto')

        # 5. Generate answer
        llm = llm_client()
        prompt = build_conversation_prompt(history, text, knowledge_context)
        answer = llm(prompt)

        # 6. Send to Slack (no rush, we're in background)
        slack_client.chat_postMessage(
            channel=channel,
            text=f"{answer}\n\n_[via {routing['provider']}]_"
        )

        # 7. Cache and learn
        cache_llm_response(text, answer, ttl=3600)
        add_to_conversation(user, "user", text)
        add_to_conversation(user, "assistant", answer)
        COL.run_once([{"type": "slack_message", ...}])

    finally:
        # Cleanup dedup cache after 60 seconds
        threading.Timer(60, lambda: _slack_event_cache.pop(event_id, None)).start()
```

**2. Modify webhook handler to return immediately:**

```python
@app.post("/slack/events")
def slack_events():
    payload = request.get_json(silent=True) or {}

    # Handle URL verification
    if payload.get("type") == "url_verification":
        return jsonify({"challenge": payload.get("challenge")})

    event = payload.get("event", {})
    event_id = payload.get("event_id", "")

    # ✅ CRITICAL: Deduplicate retries
    if event_id and event_id in _slack_event_cache:
        log.info(f"Ignoring duplicate event: {event_id}")
        return jsonify({"ok": True})

    if event_id:
        _slack_event_cache[event_id] = True

    # Validate event
    if event.get("bot_id") or event.get("type") not in ["message", "app_mention"]:
        return jsonify({"ok": True})

    text = event.get("text", "")
    channel = event.get("channel")
    user = event.get("user")

    if not text or not channel:
        return jsonify({"ok": True})

    # ✅ SOLUTION: Spawn background thread
    thread = threading.Thread(
        target=_process_slack_message,
        args=(text, channel, user, event_id),
        daemon=True
    )
    thread.start()

    # ✅ Return HTTP 200 immediately (< 100ms)
    log.info(f"Queued Slack message for background processing")
    return jsonify({"ok": True})
```

### Why This Works

**Before:**

- Slack → Webhook → Process (10-60s) → HTTP 200
- Slack timeout → Retry → Process again → HTTP 200
- Result: 6 responses

**After:**

- Slack → Webhook → HTTP 200 (< 100ms)
- Background: Process → Send Slack message
- Deduplication: Retries ignored via `event_id` cache
- Result: 1 response

## Results

**Performance:**

- HTTP 200 acknowledgment: < 100ms (was 10-60 seconds)
- No more Cloudflare timeout errors
- One message in → One response out

**Testing:**

```bash
# Before fix
User: "Hey Bob"
Bob: [response 1]
Bob: [response 2]
Bob: [response 3]
Bob: [response 4]
Bob: [response 5]
Bob: [response 6]

# After fix
User: "Hey Bob"
Bob: [response]  ✓
```

## Bonus: DiagPro Training

While debugging, I also trained Bob on a 19,000-word DiagPro customer avatar document using the `/learn` endpoint:

```bash
curl -X POST http://localhost:8080/learn \
  -H "Content-Type: application/json" \
  -H "X-API-Key: $BB_API_KEY" \
  -d '{
    "correction": "DiagPro is a $4.99 AI-powered automotive diagnostic platform targeting drivers aged 25-60 who fear being overcharged by mechanics..."
  }'
```

Bob's Circle of Life learning system processes this knowledge and makes it available for queries through the Knowledge Orchestrator.

## Key Lessons

1. **Webhook timeout limits are real** - Slack's 3-second timeout isn't negotiable
2. **Background processing is essential** - Don't make the HTTP client wait for slow operations
3. **Deduplication is critical** - Retries WILL happen; handle them gracefully
4. **Event IDs exist for a reason** - Use them to detect duplicate deliveries
5. **Tunnel stability matters** - Cloudflare Tunnel >>> localhost.run for production use

## Related Posts

- [Building AI-Friendly Codebase Documentation: Real-Time CLAUDE.md Creation Journey](/posts/building-ai-friendly-codebase-documentation-real-time-claude-md-creation-journey/)
- [Building Multi-Brand RSS Validation System: 97% of 226 Feeds Tested](/posts/building-multi-brand-rss-validation-system-97-feeds-tested/)

## Tech Stack

- **Python 3.12** with Flask
- **Slack SDK** for Python
- **Cloudflare Tunnel** for public HTTPS
- **LlamaIndex** for knowledge integration
- **Ollama** (local), Groq, Google Gemini (cloud LLMs)
- **Redis** for caching and conversation memory

**Author:** Jeremy Longshore
**Email:** jeremy@intentsolutions.io
**GitHub:** [@jeremylongshore](https://github.com/jeremylongshore)

*Building production-grade AI agents with real-world integration lessons learned the hard way.*
