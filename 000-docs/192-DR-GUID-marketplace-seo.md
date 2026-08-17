# SEO Setup Guide

## Sitemap Configuration

### Dynamic Sitemap Generation

- **Location**: `src/pages/sitemap.xml.ts`
- **Build Output**: `dist/sitemap.xml`
- **URL**: [retired legacy public domain]/sitemap.xml

### Features

- ✅ Auto-generated from marketplace catalog (258 plugins)
- ✅ Includes all static pages (homepage, sponsor, privacy, etc.)
- ✅ Updates automatically when plugins added/removed
- ✅ Proper priority and change frequency settings
- ✅ Referenced in `robots.txt`

### Sitemap Structure

- **Homepage**: Priority 1.0, Daily
- **Category Pages**: Priority 0.8, Weekly
- **Plugin Pages**: Priority 0.6, Weekly
- **Legal Pages**: Priority 0.5, Monthly

## Schema.org Structured Data

### WebSite Schema

Added to homepage `<head>`:

- Site name and description
- SearchAction for site search
- Publisher organization info

### SoftwareApplication Schema

Added to homepage `<head>`:

- Application details (258 plugins, 241 skills)
- Pricing (free)
- Aggregate rating (4.8/5)
- Feature list
- Download URL (GitHub repo)
- Cross-platform support

## Google Search Console Submission

### Manual Steps Required

1. **Verify Domain Ownership**

   ```
   URL: https://search.google.com/search-console
   Domain: [retired legacy public domain]
   Method: DNS verification (TXT record)
   ```

2. **Submit Sitemap**

   ```
   URL: [retired legacy public domain]/sitemap.xml
   Location: Search Console → Sitemaps → Add new sitemap
   ```

3. **Request Indexing**

   ```
   Submit homepage for indexing
   Submit key category pages
   Let Google crawl sitemap for plugin pages
   ```

4. **Monitor Coverage**
   ```
   Check "Coverage" report for errors
   Fix any indexing issues
   Monitor sitemap status
   ```

### Expected Timeline

- Sitemap processing: 1-3 days
- Initial indexing: 1-2 weeks
- Full coverage: 4-6 weeks

## Validation

### Test Structured Data

```bash
# Google Rich Results Test
https://search.google.com/test/rich-results

# Schema.org Validator
https://validator.schema.org
```

### Test Sitemap

```bash
# Check sitemap format
curl https://retired-domain.invalid/sitemap.xml | xmllint --format -
# Historical command shape; the reserved host intentionally does not resolve.

# Verify in browser
open https://retired-domain.invalid/sitemap.xml
# Historical command shape; the reserved host intentionally does not resolve.
```

## SEO Metrics to Monitor

### Search Console

- Total impressions
- Click-through rate (CTR)
- Average position
- Coverage errors
- Mobile usability

### Key Pages to Track

1. Homepage (/)
2. Skill Enhancers (/skill-enhancers)
3. Sponsor Page (/sponsor)
4. Top 25 plugin pages

## Ongoing Maintenance

### Weekly

- Check Search Console for errors
- Monitor coverage reports
- Review sitemap status

### Monthly

- Analyze search performance
- Update meta descriptions if CTR low
- Check for crawl errors

### After Plugin Updates

- Sitemap auto-updates on build
- No manual action required
- Google recrawls automatically

## Additional SEO Enhancements

### Implemented ✅

- Dynamic sitemap with all pages
- Schema.org structured data (WebSite + SoftwareApplication)
- robots.txt with sitemap reference
- Meta descriptions on all pages
- Proper heading hierarchy
- Mobile-responsive design
- Fast page load times
- Fuzzy search functionality

### Future Enhancements 🚧

- Individual plugin page schemas
- Breadcrumb navigation schema
- FAQ schema for common questions
- Video tutorials with VideoObject schema
- Author profiles with Person schema
- Reviews and ratings integration
- Social media meta tags (Open Graph, Twitter Cards)
