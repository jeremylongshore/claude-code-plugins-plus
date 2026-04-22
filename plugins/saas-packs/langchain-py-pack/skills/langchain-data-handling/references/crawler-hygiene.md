# Crawler Hygiene

How to configure `WebBaseLoader` and related loaders so you don't get 403'd by Cloudflare, violate `robots.txt`, or get your IP banned. The P50 fix plus the broader etiquette that makes crawlers sustainable.

## The P50 Failure Mode

`WebBaseLoader` uses `requests` with a default User-Agent like `python-requests/2.31.0`. Every major bot-protection service (Cloudflare, Akamai, Imperva, AWS WAF) flags this as non-human traffic. The response you get is one of:

- **403 Forbidden** — explicit block.
- **503 Service Unavailable** — JavaScript challenge (Cloudflare "I'm Under Attack" mode).
- **200 OK with challenge HTML** — the response body contains `"Checking your browser before accessing..."` or similar interstitial text. Your crawler thinks the page loaded fine and indexes the challenge page.

The third mode is the silent killer. Every query hitting that source returns the same interstitial text. Users see "Checking your browser..." as the answer.

## Fix 1 — Set a Realistic User-Agent

```python
from langchain_community.document_loaders import WebBaseLoader

loader = WebBaseLoader(
    "https://example.com/article",
    header_template={
        "User-Agent": (
            "Mozilla/5.0 (X11; Linux x86_64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/120.0.0.0 Safari/537.36"
        ),
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        "Accept-Language": "en-US,en;q=0.9",
        "Accept-Encoding": "gzip, deflate, br",
    },
)
docs = loader.load()
```

Use a **current** Chrome/Firefox UA. UAs from Chrome 60 (2017) are as suspicious as `python-requests` now.

### Don't: identify as a specific company bot unless you're prepared to back it

`User-Agent: AcmeBot/1.0 (+https://acme.example/bot)` is honest and fine — if you also publish a page at that URL describing the bot, respect every `robots.txt`, and have an abuse contact. Otherwise a site owner who sees your UA and bans it has banned a real company you can't hide from next time.

## Fix 2 — Respect `robots.txt`

```python
from urllib.robotparser import RobotFileParser
from urllib.parse import urlparse

def can_fetch(url: str, user_agent: str = "Mozilla/5.0") -> bool:
    parsed = urlparse(url)
    robots_url = f"{parsed.scheme}://{parsed.netloc}/robots.txt"
    rp = RobotFileParser()
    rp.set_url(robots_url)
    try:
        rp.read()
    except Exception:
        return True  # if robots.txt is unreachable, proceed
    return rp.can_fetch(user_agent, url)

# Use before every load
if not can_fetch(url):
    print(f"robots.txt disallows: {url}")
    continue

docs = WebBaseLoader(url, header_template={"User-Agent": "Mozilla/5.0 ..."}).load()
```

`robots.txt` is a request, not a legal wall. But ignoring it:

1. Gets your IP banned when the site owner notices.
2. In some jurisdictions (EU especially), violates the site's terms of service in a way that can matter in court if you build a commercial product on scraped data.
3. Is rude. Don't be the reason small sites have to go behind Cloudflare.

## Fix 3 — Rate Limit Per Host

A corpus crawl across 100 URLs on the same domain, unrate-limited, is a DDoS. Cap at 1 request per second per host by default:

```python
import time
from collections import defaultdict
from urllib.parse import urlparse

_last_fetch = defaultdict(float)

def rate_limited_load(url: str, min_interval: float = 1.0) -> list:
    host = urlparse(url).netloc
    elapsed = time.monotonic() - _last_fetch[host]
    if elapsed < min_interval:
        time.sleep(min_interval - elapsed)
    _last_fetch[host] = time.monotonic()
    return WebBaseLoader(
        url,
        header_template={"User-Agent": "Mozilla/5.0 ..."},
    ).load()
```

For large crawls, use an async semaphore per host:

```python
import asyncio
from collections import defaultdict

_host_sem = defaultdict(lambda: asyncio.Semaphore(1))

async def async_load(url: str):
    host = urlparse(url).netloc
    async with _host_sem[host]:
        # ... async load with aiohttp ...
        await asyncio.sleep(1.0)  # 1 req/sec per host
```

## Fix 4 — Prefer Structured Sources

In order of courtesy and reliability:

1. **Sitemap** (`/sitemap.xml`) — the site-owner-approved list of pages. Use `SitemapLoader`.
2. **RSS / Atom feed** — updates only, no full-crawl. Use `RSSFeedLoader`.
3. **API** — if the site has one. JSON > HTML parsing.
4. **Sampled HTML crawl** — only after exhausting the above.
5. **Full crawl** — rarely justified; expensive for both sides.

```python
from langchain_community.document_loaders import SitemapLoader

loader = SitemapLoader(
    "https://example.com/sitemap.xml",
    filter_urls=[r".*blog.*"],  # regex to filter paths
    requests_per_second=2,
    header_template={"User-Agent": "Mozilla/5.0 ..."},
)
docs = loader.load()
```

## Fix 5 — Detect Interstitial Responses

Even with a good UA, some sites serve challenge pages. Assert response sanity:

```python
INTERSTITIAL_MARKERS = [
    "checking your browser",
    "enable javascript and cookies",
    "attention required",         # Cloudflare
    "access denied",
    "please verify you are a human",
    "distil_identify_cookie",      # Imperva
]

def is_interstitial(doc) -> bool:
    text = doc.page_content[:2000].lower()
    return any(m in text for m in INTERSTITIAL_MARKERS)

docs = [d for d in loader.load() if not is_interstitial(d)]

# Also length check — interstitials are usually short
docs = [d for d in docs if len(d.page_content) > 500]
```

## Fix 6 — Handle JS-Rendered Content

Sites built as SPAs (React, Vue, Svelte) render empty HTML to `requests`. You need a real browser:

```python
from langchain_community.document_loaders import PlaywrightURLLoader

loader = PlaywrightURLLoader(
    urls=["https://spa.example.com/page"],
    remove_selectors=["nav", "footer", ".ad"],
    continue_on_failure=True,
)
docs = loader.load()
```

Trade-off: ~200 MB of browser runtime and ~2-5s per page. Use only for pages where the static HTML is empty.

## Fix 7 — Retry with Backoff on 429 / 503

```python
import time
import requests
from requests.exceptions import HTTPError

def fetch_with_backoff(url: str, max_retries: int = 3) -> str:
    for attempt in range(max_retries):
        try:
            resp = requests.get(
                url,
                headers={"User-Agent": "Mozilla/5.0 ..."},
                timeout=30,
            )
            if resp.status_code == 429:
                retry_after = int(resp.headers.get("Retry-After", 60))
                time.sleep(min(retry_after, 300))
                continue
            if resp.status_code == 503:
                time.sleep(2 ** attempt)
                continue
            resp.raise_for_status()
            return resp.text
        except HTTPError:
            if attempt == max_retries - 1:
                raise
            time.sleep(2 ** attempt)
    raise RuntimeError(f"failed after {max_retries} retries: {url}")
```

## Checklist for a Production Crawler

- [ ] Realistic, current User-Agent (Chrome 120+ or Firefox 120+)
- [ ] `robots.txt` checked before every request
- [ ] Per-host rate limit (default 1 req/sec)
- [ ] Sitemap / RSS preferred over HTML crawl
- [ ] Interstitial detection (text markers + length check)
- [ ] Retry with exponential backoff on 429 / 503
- [ ] Honor `Retry-After` headers
- [ ] Log every URL + status code for audit
- [ ] Abuse contact email in UA if using a custom UA

## Pain Catalog Anchors

- **P50** — `WebBaseLoader` default UA returns 403 / interstitial on Cloudflare. Fix: realistic UA + `robots.txt` respect + rate limiting + interstitial detection.
