# firecrawl-crawl-site

## Skill Scaffold

```
firecrawl-crawl-site/
  SKILL.md
```

## File Descriptions

### 1. SKILL.md
**Purpose:** Crawl entire websites or sections with depth control, URL filtering, sitemap respect, and comprehensive coverage options.
**Workflow:** Multi-page crawling workflow - extracts content from entire sites or specific sections with intelligent navigation.
**Relates to:** Extends firecrawl-scrape-single; complements firecrawl-batch-processing for high-volume operations

## Summary

This skill implements full website crawling with FireCrawl's crawl endpoint. It covers crawl configuration including max depth, URL include/exclude patterns, sitemap utilization, rate limiting, and page limits. The skill handles the asynchronous nature of crawl jobs, polling for completion, and aggregating results. This enables comprehensive content extraction from documentation sites, blogs, knowledge bases, and entire domains.
