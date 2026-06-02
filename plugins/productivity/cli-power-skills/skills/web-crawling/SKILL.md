---
name: web-crawling
description: "Use when scraping web pages, automating browser interactions, crawling sites for content, or extracting data from rendered JavaScript pages"
allowed-tools: [Bash(node*), Bash(python3*), Bash(scrapy*), Bash(katana*), Read, Write]
version: 1.0.0
author: ykotik
license: MIT
---

# Web Crawling

## When to Use
- Scraping content from web pages (especially JavaScript-rendered)
- Automating browser interactions (login, form submission, navigation)
- Crawling a site to discover and extract structured data
- Taking screenshots or generating PDFs of web pages
- Discovering URLs and endpoints on a target site
- Extracting data from sites with anti-bot protection

## Tools

| Tool | Purpose | When to choose |
|------|---------|---------------|
| **Playwright** | Cross-browser automation (Chromium, Firefox, WebKit) | JS-rendered pages, screenshots, complex interactions |
| **Puppeteer** | Chrome/Firefox automation via DevTools Protocol | Chrome-specific automation, familiar API |
| **Scrapy** | Production-grade Python crawling framework | Large-scale structured crawling with pipelines |
| **Crawlee** | Node.js crawling with anti-blocking built in | Sites with bot detection, proxy rotation needed |
| **Katana** | Fast Go-based URL discovery crawler | Endpoint discovery, reconnaissance, speed |

## Patterns

### Playwright: Scrape a page (inline Node.js script)
```bash
node -e "
const { chromium } = require('playwright');
(async () => {
  const browser = await chromium.launch();
  const page = await browser.newPage();
  await page.goto('https://example.com');
  const title = await page.title();
  const text = await page.locator('body').innerText();
  console.log(JSON.stringify({ title, text }));
  await browser.close();
})();
"
```

### Playwright: Take a screenshot
```bash
node -e "
const { chromium } = require('playwright');
(async () => {
  const browser = await chromium.launch();
  const page = await browser.newPage();
  await page.goto('https://example.com');
  await page.screenshot({ path: 'screenshot.png', fullPage: true });
  await browser.close();
})();
"
```

### Playwright: Extract structured data from a table
```bash
node -e "
const { chromium } = require('playwright');
(async () => {
  const browser = await chromium.launch();
  const page = await browser.newPage();
  await page.goto('https://example.com/data');
  const rows = await page.locator('table tr').evaluateAll(trs =>
    trs.map(tr => Array.from(tr.querySelectorAll('td,th')).map(c => c.textContent.trim()))
  );
  console.log(JSON.stringify(rows));
  await browser.close();
})();
"
```

### Playwright: Wait for JS content to load
```bash
node -e "
const { chromium } = require('playwright');
(async () => {
  const browser = await chromium.launch();
  const page = await browser.newPage();
  await page.goto('https://example.com/spa');
  await page.waitForSelector('.content-loaded');
  const data = await page.locator('.content-loaded').innerText();
  console.log(data);
  await browser.close();
})();
"
```

### Puppeteer: Generate PDF from a page
```bash
node -e "
const puppeteer = require('puppeteer');
(async () => {
  const browser = await puppeteer.launch();
  const page = await browser.newPage();
  await page.goto('https://example.com', { waitUntil: 'networkidle0' });
  await page.pdf({ path: 'output.pdf', format: 'A4' });
  await browser.close();
})();
"
```

### Katana: Discover all URLs on a site
```bash
katana -u https://example.com -silent -d 3
```

### Katana: Discover URLs and output as JSON
```bash
katana -u https://example.com -silent -d 2 -jsonl
```

### Katana: Crawl with headless browser for JS-rendered links
```bash
katana -u https://example.com -headless -d 2 -silent
```

### Scrapy: Quick single-page scrape (no project needed)
```bash
scrapy fetch --nolog https://example.com | python3 -c "
import sys
from scrapy import Selector
html = sys.stdin.read()
sel = Selector(text=html)
for item in sel.css('h2::text').getall():
    print(item)
"
```

### Crawlee: Basic crawler with anti-blocking
```bash
node -e "
const { PlaywrightCrawler } = require('crawlee');
const crawler = new PlaywrightCrawler({
  async requestHandler({ page, request }) {
    const title = await page.title();
    console.log(JSON.stringify({ url: request.url, title }));
  },
  maxRequestsPerCrawl: 10,
});
crawler.run(['https://example.com']);
"
```

## Pipelines

### Discover URLs → filter interesting ones → scrape
```bash
katana -u https://example.com -silent -d 2 | grep '/blog/' | head -5 | while read url; do
  node -e "
    const { chromium } = require('playwright');
    (async () => {
      const browser = await chromium.launch();
      const page = await browser.newPage();
      await page.goto('$url');
      const title = await page.title();
      const text = await page.locator('article').innerText().catch(() => '');
      console.log(JSON.stringify({ url: '$url', title, text: text.slice(0, 500) }));
      await browser.close();
    })();
  "
done
```
Each stage: Katana discovers URLs, grep filters to blog posts, Playwright scrapes each page.

### Crawl → extract to JSON → query with DuckDB
```bash
katana -u https://example.com -silent -d 2 -jsonl > crawl.jsonl
duckdb -c "SELECT endpoint, status_code, COUNT(*) FROM read_json_auto('crawl.jsonl') GROUP BY endpoint, status_code ORDER BY COUNT(*) DESC"
```
Each stage: Katana crawls to JSONL, DuckDB runs SQL on the crawl results.

## Prefer Over
- Prefer **Playwright** over curl for JavaScript-rendered pages — curl only gets raw HTML, Playwright executes JS
- Prefer **Katana** over manual URL enumeration — fast, recursive, handles JS links
- Prefer **Scrapy** over ad-hoc scripts for structured multi-page crawling — built-in rate limiting, pipelines, persistence

## Do NOT Use When
- Page content is available via a REST API — use the API directly (api-testing skill)
- Extracting article text from a news URL — use newspaper4k (web-research skill), it's purpose-built
- Simple static HTML that curl can fetch — use `curl` + `jq`/`pup`
- The site explicitly prohibits scraping — respect robots.txt and ToS
