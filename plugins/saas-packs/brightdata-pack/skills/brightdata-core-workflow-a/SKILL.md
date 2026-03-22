---
name: brightdata-core-workflow-a
description: |
  Scrape structured data with Bright Data Scraping Browser using Playwright/Puppeteer.
  Use when scraping JavaScript-rendered pages, SPAs, or sites requiring browser interaction.
  Trigger with phrases like "brightdata scraping browser", "brightdata playwright",
  "brightdata puppeteer", "scrape SPA with brightdata", "browser scraping".
allowed-tools: Read, Write, Edit, Bash(npm:*), Bash(npx:*), Grep
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
tags: [saas, scraping, data, brightdata, playwright, puppeteer]
compatible-with: claude-code
---

# Bright Data Scraping Browser

## Overview

Use Bright Data's Scraping Browser to scrape JavaScript-rendered pages. The Scraping Browser works like a regular Playwright/Puppeteer browser but routes through Bright Data's proxy infrastructure with built-in CAPTCHA solving, fingerprint management, and automatic retries.

## Prerequisites

- Completed `brightdata-install-auth` setup
- Scraping Browser zone active in Bright Data control panel
- Playwright or Puppeteer installed

## Instructions

### Step 1: Install Playwright

```bash
npm install playwright
npx playwright install chromium
```

### Step 2: Connect to Scraping Browser with Playwright

```typescript
// scraping-browser.ts
import { chromium } from 'playwright';
import 'dotenv/config';

const { BRIGHTDATA_CUSTOMER_ID, BRIGHTDATA_ZONE, BRIGHTDATA_ZONE_PASSWORD } = process.env;

const AUTH = `brd-customer-${BRIGHTDATA_CUSTOMER_ID}-zone-${BRIGHTDATA_ZONE}:${BRIGHTDATA_ZONE_PASSWORD}`;
const BROWSER_WS = `wss://${AUTH}@brd.superproxy.io:9222`;

async function scrapWithBrowser(url: string) {
  console.log('Connecting to Scraping Browser...');
  const browser = await chromium.connectOverCDP(BROWSER_WS);

  try {
    const page = await browser.newPage();
    await page.goto(url, { waitUntil: 'domcontentloaded', timeout: 60000 });

    // Wait for dynamic content to load
    await page.waitForSelector('body', { timeout: 30000 });

    // Extract structured data
    const data = await page.evaluate(() => ({
      title: document.title,
      metaDescription: document.querySelector('meta[name="description"]')?.getAttribute('content') || '',
      h1: document.querySelector('h1')?.textContent?.trim() || '',
      links: Array.from(document.querySelectorAll('a[href]')).slice(0, 20).map(a => ({
        text: a.textContent?.trim(),
        href: a.getAttribute('href'),
      })),
    }));

    console.log('Scraped data:', JSON.stringify(data, null, 2));
    return data;
  } finally {
    await browser.close();
  }
}

scrapWithBrowser('https://example.com').catch(console.error);
```

### Step 3: Scrape Dynamic Product Listings

```typescript
// scrape-products.ts — real-world example
import { chromium, Page } from 'playwright';
import 'dotenv/config';

interface Product {
  name: string;
  price: string;
  rating: string;
  url: string;
}

const AUTH = `brd-customer-${process.env.BRIGHTDATA_CUSTOMER_ID}-zone-${process.env.BRIGHTDATA_ZONE}:${process.env.BRIGHTDATA_ZONE_PASSWORD}`;

async function scrapeProducts(searchUrl: string): Promise<Product[]> {
  const browser = await chromium.connectOverCDP(`wss://${AUTH}@brd.superproxy.io:9222`);
  const page = await browser.newPage();

  try {
    await page.goto(searchUrl, { waitUntil: 'networkidle', timeout: 90000 });

    // Scroll to trigger lazy-loaded content
    await autoScroll(page);

    const products = await page.evaluate(() => {
      return Array.from(document.querySelectorAll('[data-testid="product-card"]')).map(card => ({
        name: card.querySelector('.product-title')?.textContent?.trim() || '',
        price: card.querySelector('.price')?.textContent?.trim() || '',
        rating: card.querySelector('.rating')?.textContent?.trim() || '',
        url: card.querySelector('a')?.getAttribute('href') || '',
      }));
    });

    return products;
  } finally {
    await browser.close();
  }
}

async function autoScroll(page: Page): Promise<void> {
  await page.evaluate(async () => {
    await new Promise<void>((resolve) => {
      let totalHeight = 0;
      const distance = 300;
      const timer = setInterval(() => {
        window.scrollBy(0, distance);
        totalHeight += distance;
        if (totalHeight >= document.body.scrollHeight) {
          clearInterval(timer);
          resolve();
        }
      }, 200);
    });
  });
}
```

### Step 4: Puppeteer Alternative

```typescript
// scraping-browser-puppeteer.ts
import puppeteer from 'puppeteer-core';

const AUTH = `brd-customer-${process.env.BRIGHTDATA_CUSTOMER_ID}-zone-${process.env.BRIGHTDATA_ZONE}:${process.env.BRIGHTDATA_ZONE_PASSWORD}`;

async function scrapeWithPuppeteer(url: string) {
  const browser = await puppeteer.connect({
    browserWSEndpoint: `wss://${AUTH}@brd.superproxy.io:9222`,
  });
  const page = await browser.newPage();
  await page.goto(url, { waitUntil: 'domcontentloaded', timeout: 60000 });
  const title = await page.title();
  console.log('Page title:', title);
  await browser.close();
}
```

## Output

- Browser connection through Bright Data's proxy network
- Scraped structured data from JS-rendered pages
- Automatic CAPTCHA solving and fingerprint management

## Error Handling

| Error | Cause | Solution |
|-------|-------|----------|
| `WebSocket connection failed` | Wrong zone or credentials | Verify Scraping Browser zone is active |
| `Timeout 60000ms exceeded` | Slow page load | Increase timeout; use `domcontentloaded` instead of `networkidle` |
| `Target closed` | Browser disconnected | Implement retry logic; browser sessions are ephemeral |
| `Navigation failed` | Site blocked request | Scraping Browser handles this; increase timeout |

## Resources

- [Scraping Browser Docs](https://docs.brightdata.com/scraping-automation/scraping-browser/overview)
- [Scraping Browser Code Examples](https://docs.brightdata.com/scraping-automation/scraping-browser/code-examples)
- [Playwright CDP Docs](https://playwright.dev/docs/api/class-browsertype#browser-type-connect-over-cdp)

## Next Steps

For SERP API scraping, see `brightdata-core-workflow-b`.
