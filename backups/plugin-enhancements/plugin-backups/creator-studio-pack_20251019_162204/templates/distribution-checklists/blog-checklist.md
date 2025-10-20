# Blog Post Distribution Checklist

**Complete checklist for embedding videos and optimizing blog content**

---

## Pre-Publishing Preparation

### Content Creation

- [ ] **Video embedded** at top of post (native OR YouTube embed)
- [ ] **Transcript** included (full or edited for readability)
- [ ] **Introduction** written (150-300 words, SEO-optimized)
- [ ] **Section headers** (H2, H3) with keywords
- [ ] **Code snippets** properly formatted with syntax highlighting
- [ ] **Screenshots** added at key points
- [ ] **Diagrams/visuals** created if needed
- [ ] **Conclusion** written with key takeaways
- [ ] **Call to action** clear (subscribe, comment, share)
- [ ] **Word count**: 1500+ words (better SEO)

### SEO Optimization

**Title**:
- [ ] **Primary keyword** at beginning
- [ ] **Length**: 50-60 characters
- [ ] **Compelling**: Balances SEO and clickability
- [ ] **Format**: "How to [X] | [Benefit] | [Year/Guide]"

**Meta Description**:
- [ ] **Written** (155-160 characters)
- [ ] **Includes keyword** naturally
- [ ] **Compelling hook**: Why should they click?
- [ ] **Call to action**: "Learn how to..."

**URL Slug**:
- [ ] **Keyword-rich**: /how-to-build-rest-api-nodejs
- [ ] **Short**: 3-5 words ideal
- [ ] **No stop words**: Remove "a", "the", "and"
- [ ] **Hyphens** not underscores
- [ ] **Lowercase** only

**Keywords**:
- [ ] **Primary keyword** identified (main focus)
- [ ] **Secondary keywords** (3-5 related terms)
- [ ] **Long-tail keywords** (specific phrases)
- [ ] **Keyword density**: 1-2% (natural, not stuffed)
- [ ] **Keywords in**: Title, H2s, first 100 words, conclusion

**Internal Links**:
- [ ] **3-5 internal links** to related posts
- [ ] **Anchor text** descriptive (not "click here")
- [ ] **Opens in same tab** (keeps users on site)
- [ ] **Relevant**: Actually related content

**External Links**:
- [ ] **Authority sources** linked (documentation, research)
- [ ] **Opens in new tab** (keeps users on your site)
- [ ] **No broken links** (check with tool)
- [ ] **Follow vs nofollow** appropriately set

---

## Video Embedding

### Embed Options

**Native Upload** (Best for SEO):
- [ ] **Video file uploaded** directly to blog platform
- [ ] **Thumbnail** customized
- [ ] **Auto-play** disabled (user-friendly)
- [ ] **Controls** visible
- [ ] **Responsive**: Works on mobile

**YouTube Embed** (Most Common):
- [ ] **Embed code** copied from YouTube
- [ ] **Responsive embed** (scales to container)
- [ ] **Privacy-enhanced mode** enabled (no cookies until play)
- [ ] **Start time** set if needed (?t=30s)
- [ ] **Chapters** work in embed
- [ ] **Lazy load** enabled (faster page load)

**Video Placement**:
- [ ] **Above the fold**: At top of post
- [ ] **Aligned**: Centered or full-width
- [ ] **Spacing**: Proper margins above/below
- [ ] **Caption**: Brief description below video

---

## Content Structure

### Introduction (150-300 words)

```markdown
# [Title with Primary Keyword]

[Video embed - full width]

[Hook paragraph - 2-3 sentences]

In this tutorial, I'll show you [main goal]. We'll cover:
- [Key point 1]
- [Key point 2]
- [Key point 3]

[Context paragraph - why this matters]

[Watch time estimate]: "This tutorial takes [X] minutes to watch."

Let's dive in.
```

- [ ] **Hook** grabs attention
- [ ] **Value prop** clear
- [ ] **Primary keyword** in first 100 words
- [ ] **Watch time** mentioned (improves engagement)
- [ ] **Table of contents** if long post (auto-generated OR manual)

### Body Sections

```markdown
## [H2 with Secondary Keyword]

[Explanation paragraph]

### [H3 for Sub-Topic]

[Code block with syntax highlighting]

[Screenshot of result]

[Explanation of code]
```

For each section:
- [ ] **H2 headers** with keywords
- [ ] **Paragraphs**: 3-4 sentences max (readability)
- [ ] **Code blocks**: Properly formatted with language specified
- [ ] **Screenshots**: Captioned and compressed
- [ ] **Lists**: Bulleted or numbered where appropriate
- [ ] **Bold/italic**: Emphasize key points
- [ ] **Quotes**: Highlight important concepts

### Code Blocks

- [ ] **Language specified**: ```javascript, ```python, etc.
- [ ] **Syntax highlighting** working
- [ ] **Copy button** available (if platform supports)
- [ ] **Line numbers** (optional, for longer blocks)
- [ ] **Commented**: Explain complex parts
- [ ] **Tested**: Code actually works
- [ ] **GitHub link**: Full code in repository

### Images/Screenshots

- [ ] **Alt text** added (accessibility + SEO)
- [ ] **Descriptive filenames**: api-request-example.png (not img001.png)
- [ ] **Compressed**: Under 200KB each (use TinyPNG)
- [ ] **Responsive**: Scales on mobile
- [ ] **Captions**: Brief description below image
- [ ] **Relevant**: Every image adds value

### Conclusion (100-200 words)

```markdown
## Conclusion

In this tutorial, we [summary of what was built/learned].

Key takeaways:
- [Takeaway 1]
- [Takeaway 2]
- [Takeaway 3]

[Next steps]: Try implementing [suggestion].

[Resources]
- GitHub: [link to code]
- Video: [link to YouTube]
- Documentation: [link to official docs]

[Final CTA]: What will you build with this? Let me know in the comments!
```

- [ ] **Summary** of main points
- [ ] **Key takeaways** listed
- [ ] **Next steps** suggested
- [ ] **Resources** linked
- [ ] **CTA** clear (comment, share, subscribe)

---

## Technical SEO

### On-Page SEO

- [ ] **Schema markup** added (Article OR VideoObject schema)
- [ ] **Open Graph tags** (for social sharing)
- [ ] **Twitter Card tags** (for Twitter preview)
- [ ] **Canonical URL** set (avoid duplicate content)
- [ ] **Mobile-friendly**: Responsive design
- [ ] **Page speed**: Loads in <3 seconds
- [ ] **HTTPS**: Secure connection
- [ ] **Breadcrumbs**: Navigation path visible

### Schema Markup (JSON-LD)

**Article Schema**:
```json
{
  "@context": "https://schema.org",
  "@type": "Article",
  "headline": "[Post Title]",
  "image": "[Featured image URL]",
  "author": {
    "@type": "Person",
    "name": "[Your Name]"
  },
  "publisher": {
    "@type": "Organization",
    "name": "[Site Name]",
    "logo": "[Logo URL]"
  },
  "datePublished": "[YYYY-MM-DD]",
  "description": "[Meta description]"
}
```

- [ ] **Added to post** (head or footer)

**VideoObject Schema** (if video is primary):
```json
{
  "@context": "https://schema.org",
  "@type": "VideoObject",
  "name": "[Video Title]",
  "description": "[Video Description]",
  "thumbnailUrl": "[Thumbnail URL]",
  "uploadDate": "[YYYY-MM-DD]",
  "duration": "[PT10M30S]",
  "contentUrl": "[Video URL]",
  "embedUrl": "[Embed URL]"
}
```

- [ ] **Added to post**

### Open Graph Tags

```html
<meta property="og:title" content="[Post Title]" />
<meta property="og:description" content="[Meta Description]" />
<meta property="og:image" content="[Featured Image URL]" />
<meta property="og:url" content="[Post URL]" />
<meta property="og:type" content="article" />
<meta property="og:site_name" content="[Site Name]" />
```

- [ ] **Added to post head**
- [ ] **Image**: 1200x630px (Facebook/LinkedIn optimal)

### Twitter Card Tags

```html
<meta name="twitter:card" content="summary_large_image" />
<meta name="twitter:title" content="[Post Title]" />
<meta name="twitter:description" content="[Meta Description]" />
<meta name="twitter:image" content="[Featured Image URL]" />
<meta name="twitter:site" content="[@YourHandle]" />
<meta name="twitter:creator" content="[@YourHandle]" />
```

- [ ] **Added to post head**
- [ ] **Test**: Use Twitter Card Validator

---

## Visual Elements

### Featured Image

- [ ] **Created**: Eye-catching, relevant design
- [ ] **Size**: 1200x630px (social media optimal)
- [ ] **Text**: Readable, not too small
- [ ] **Brand colors**: Consistent with your brand
- [ ] **File size**: Under 500KB (compressed)
- [ ] **Alt text**: Descriptive (80 characters max)

### In-Post Images

- [ ] **Compressed**: All under 200KB
- [ ] **Lazy loading**: Enabled for faster page load
- [ ] **Responsive**: Work on all screen sizes
- [ ] **Captions**: Added where helpful
- [ ] **Copyright**: You own OR properly attributed

---

## Pre-Publishing Checklist

### Content Review

- [ ] **Proofread**: No typos or grammar errors (use Grammarly)
- [ ] **Links work**: All internal and external links tested
- [ ] **Code tested**: All code snippets actually work
- [ ] **Video plays**: Embed works on desktop and mobile
- [ ] **Images load**: All screenshots and visuals display
- [ ] **Formatting**: Consistent heading hierarchy
- [ ] **Readability**: Short paragraphs, clear language

### SEO Check

- [ ] **Primary keyword** in: Title, H1, first 100 words, H2s, conclusion
- [ ] **Meta description** compelling and under 160 characters
- [ ] **URL slug** keyword-rich and short
- [ ] **Internal links**: 3-5 to related posts
- [ ] **External links**: Authority sources cited
- [ ] **Alt text**: All images have descriptive alt text
- [ ] **Schema markup**: Added and validated

### Technical Check

- [ ] **Mobile preview**: Looks good on phone
- [ ] **Page speed**: <3 second load time (test with PageSpeed Insights)
- [ ] **Responsive**: Works on all devices
- [ ] **Browser testing**: Works in Chrome, Safari, Firefox
- [ ] **Accessibility**: Screen reader friendly (test with WAVE)

---

## Publishing

### Publish Settings

- [ ] **Category** selected (relevant to content)
- [ ] **Tags** added (5-10 relevant tags)
- [ ] **Featured image** set
- [ ] **Excerpt** written (if platform requires)
- [ ] **Author** set correctly
- [ ] **Publish date** scheduled or immediate
- [ ] **Comments** enabled (if you want engagement)

### Social Sharing Settings

- [ ] **Social image** customized (if different from featured)
- [ ] **Social title** optimized (if different from H1)
- [ ] **Social description** compelling (if different from meta)

---

## Post-Publishing Actions

### Immediate (Within 1 Hour)

- [ ] **Share on Twitter** with thread + clips
- [ ] **Share on LinkedIn** as article OR post
- [ ] **Post in Discord/Slack** communities (with context)
- [ ] **Pin to blog homepage** (if major post)
- [ ] **Email list**: Send announcement (if applicable)
- [ ] **Add to sitemap**: Ensure it's indexed by Google

### First 24 Hours

- [ ] **Submit to Google Search Console** (request indexing)
- [ ] **Submit to Reddit** (relevant subreddits with context)
- [ ] **Share on Hacker News** (if technically deep)
- [ ] **Post to Dev.to/Medium** (canonical URL to original)
- [ ] **Reply to comments** (engagement signal for SEO)

### First Week

- [ ] **Monitor rankings**: Check Google Search Console
- [ ] **Respond to comments**: All comments replied to
- [ ] **Share again**: Post different angle on social media
- [ ] **Update if needed**: Fix errors, add clarifications
- [ ] **Internal link**: Add links from related older posts

---

## Distribution Strategy

### Email Newsletter

**Subject Line**:
- [ ] **Clear benefit**: "How to [X]" or "[Number] Tips for [Y]"
- [ ] **Length**: 50-60 characters
- [ ] **Curiosity**: Hint at value without giving it all away
- [ ] **Personalization**: Use first name if available

**Email Body**:
- [ ] **Hook**: First 2 sentences grab attention
- [ ] **Video thumbnail**: Linked to post (visual > text)
- [ ] **Summary**: 3-4 sentences about post
- [ ] **Key takeaways**: Bulleted list (3-5 points)
- [ ] **CTA**: "Read the full tutorial" button
- [ ] **P.S.**: Additional value OR teaser for next post

### Social Media

**Twitter Thread**:
- [ ] **Tweet 1**: Hook + post link + video thumbnail
- [ ] **Tweet 2-5**: Key takeaways from post
- [ ] **Tweet 6**: CTA + link again
- [ ] **Video clip** attached (30-60 seconds)

**LinkedIn Article**:
- [ ] **First 2 paragraphs** from blog post
- [ ] **Video embedded** (first 2 minutes)
- [ ] **Link to full post** with CTA
- [ ] **Hashtags**: 3-5 professional tags

**Reddit**:
- [ ] **Context paragraph** explaining why you're sharing
- [ ] **Key points** listed (what they'll learn)
- [ ] **Link to post** (not just video)
- [ ] **Engage with comments** immediately

---

## Long-Term Optimization

### Month 1: Monitor & Update

- [ ] **Google Search Console**: Monitor impressions, clicks, position
- [ ] **Google Analytics**: Track pageviews, time on page, bounce rate
- [ ] **Comments**: Respond to all comments
- [ ] **Updates**: Fix any errors or add clarifications
- [ ] **Internal links**: Add from newer posts back to this one

### Month 3: Refresh

- [ ] **Content audit**: Is information still accurate?
- [ ] **Update code**: Any deprecated methods?
- [ ] **Add new sections**: Expand based on comments/questions
- [ ] **Republish date**: Update to show freshness
- [ ] **Re-promote**: Share again on social media

### Month 6: Expand

- [ ] **Create follow-up post**: Advanced version OR related topic
- [ ] **Update with learnings**: Add "6 months later" section
- [ ] **Turn into series**: Create part 2, part 3
- [ ] **Repurpose**: Extract into multiple shorter posts

---

## Analytics to Track

### Traffic Metrics

- **Pageviews**: Total visits to post
- **Unique visitors**: Individual people
- **Time on page**: >3 minutes is good
- **Bounce rate**: <50% is good
- **Traffic sources**: Organic, social, direct, referral

### Engagement Metrics

- **Comments**: Number and quality of discussion
- **Social shares**: How many times shared
- **Video views**: Embedded video watch count
- **Scroll depth**: How far people read
- **CTA clicks**: Subscribe, GitHub, related posts

### SEO Metrics

- **Impressions**: How often shown in search
- **Clicks**: How often clicked from search
- **CTR**: Click-through rate from search (>3% is good)
- **Position**: Average ranking for keywords
- **Backlinks**: Other sites linking to your post

---

## Tools & Resources

**SEO Tools**:
- Google Search Console (keyword tracking)
- Yoast SEO or Rank Math (WordPress plugins)
- Ahrefs or SEMrush (keyword research)
- Google PageSpeed Insights (performance)

**Content Tools**:
- Grammarly (grammar checking)
- Hemingway Editor (readability)
- Carbon (code screenshots)
- Canva (featured images)

**Analytics**:
- Google Analytics (traffic analysis)
- Hotjar (heatmaps, user behavior)
- Social analytics (native platform tools)

---

**Great blog post = Video + Written content + SEO + Distribution. Use this checklist every time.** 🚀

---

**Version**: 1.0.0
**Checklist Type**: Blog Post Distribution
