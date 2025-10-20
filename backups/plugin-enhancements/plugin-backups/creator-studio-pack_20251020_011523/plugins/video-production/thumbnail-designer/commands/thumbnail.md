---
name: thumbnail
description: Generate YouTube-style thumbnails with text overlays, faces, and attention-grabbing designs
---

# Thumbnail Designer Command

Generate high-CTR YouTube thumbnails with AI-assisted design and proven formulas.

## Usage

```bash
/thumbnail "[video title]"                    # Generate from title
/thumbnail "[title]" --style mr-beast         # Use specific style
/thumbnail "[title]" --face screenshot.png    # Use face from image
/thumbnail analyze [existing-thumbnail.jpg]   # Analyze existing thumbnail
/thumbnail batch [video-list.txt]             # Generate multiple
```

## Purpose

Create thumbnails that:
- **Stop the scroll** - Eye-catching in feed
- **Communicate value** - Clear what video is about
- **Optimize CTR** - A/B test multiple versions
- **Match brand** - Consistent style across channel

## Thumbnail Formulas

### Formula 1: Mr Beast Style
```
Elements:
- Large expressive face (40% of thumbnail)
- 3-5 words in huge text
- High contrast colors (red, yellow, blue)
- Shocked/excited expression
- Minimal background, maximum focus

Best For: Entertainment, challenges, reactions
Example: "I SPENT $100,000 ON THIS?!"
CTR Benchmark: 12-18%
```

### Formula 2: Ali Abdaal Style
```
Elements:
- Clean minimalist design
- Professional headshot
- Bold sans-serif text (2-4 words)
- Subtle background (blurred or gradient)
- Icons or simple graphics

Best For: Education, productivity, tutorials
Example: "How I Read 100 Books"
CTR Benchmark: 8-12%
```

### Formula 3: Tech Review Style
```
Elements:
- Product photo (professional)
- "VS" or comparison layout
- Verdict indicator (✓/✗ or rating)
- Clean text with stats/numbers
- Tech aesthetic (dark mode, neon)

Best For: Reviews, comparisons, tech content
Example: "MacBook M3 vs M2: Worth It?"
CTR Benchmark: 10-14%
```

### Formula 4: Tutorial Style
```
Elements:
- Before/After split
- Large text describing outcome
- Arrows showing transformation
- Professional but accessible
- Step number or duration badge

Best For: How-to, tutorials, courses
Example: "10x Faster API in 15 Minutes"
CTR Benchmark: 7-11%
```

### Formula 5: Vlog Style
```
Elements:
- Candid action shot
- Location or context visible
- Personal/relatable moment
- Casual text overlay
- Warm, authentic colors

Best For: Behind-the-scenes, vlogs, personal
Example: "Building My Startup (Day 47)"
CTR Benchmark: 6-10%
```

## Implementation

When user runs `/thumbnail "How I Made My API 10x Faster"`:

**Step 1: Analyze Title**
```
📊 TITLE ANALYSIS

Title: "How I Made My API 10x Faster"
Category: Technical tutorial
Keywords: API, performance, speed
Hook: "10x Faster" (specific result)

Recommended Style: Tutorial (Formula 4)
Alternative: Tech Review (Formula 3)
```

**Step 2: Generate Design Concepts**
```
🎨 GENERATING 3 CONCEPTS

Concept A: "Tutorial Style" (Recommended)
├─ Layout: Before/After split screen
├─ Left: "SLOW API" with 2000ms badge
├─ Right: "FAST API" with 180ms badge
├─ Center: Large "10x" with arrow
├─ Bottom: "In 1 Hour" time badge
├─ Colors: Red → Green gradient
└─ Predicted CTR: 9.5%

Concept B: "Tech Style"
├─ Layout: Code editor screenshot
├─ Text: "10x FASTER API" (huge, top)
├─ Subtext: "Redis Tutorial"
├─ Performance graph overlay
├─ Colors: Dark mode + neon green
└─ Predicted CTR: 8.2%

Concept C: "Mr Beast Style"
├─ Layout: Shocked face (if provided)
├─ Text: "10x FASTER!"
├─ Subtext: "One Simple Change"
├─ High contrast background
├─ Colors: Yellow + Red + Black
└─ Predicted CTR: 11.3%

Select concept (A/B/C) or 'all' to generate all 3:
```

**Step 3: Generate Thumbnail**
```
✨ GENERATING THUMBNAIL

Concept A (Tutorial Style)
[▓▓▓▓▓▓▓▓▓▓] 100%

Created:
- thumbnails/api-10x-faster-A.png (1280x720)
- thumbnails/api-10x-faster-A-preview.jpg (480x270)

Design Details:
├─ Font: Inter Bold (96pt main, 48pt subtext)
├─ Colors: #EF4444 → #10B981 gradient
├─ Elements: 2 screenshots, 1 arrow, 2 badges
├─ Text Hierarchy: Clear, readable at small size
└─ File Size: 186 KB (optimized for upload)

Mobile Preview:
[Shows 100x100px preview - text still readable? ✓]

Suggested Improvements:
- Consider adding small face in corner for personal touch
- Could increase contrast on "10x" text
- Alternative: Try green/blue instead of red/green for colorblind accessibility
```

**Step 4: A/B Test Recommendations**
```
📈 A/B TEST STRATEGY

Test These Variants:
1. With vs without face
2. "10x Faster" vs "10x Speed Boost"
3. Dark mode vs light mode background
4. Graph overlay vs clean design

Run 1,000 impressions each
Winner typically clear after 24 hours
Expected CTR improvement: 20-40%
```

## Advanced Features

### Face Detection and Enhancement

```bash
/thumbnail "My Video Title" --face webcam.jpg
```

Automatically:
- Detect face in image
- Remove background
- Enhance contrast and color
- Position optimally
- Add subtle shadow/glow
- Ensure face is 30-40% of frame

```
🎭 FACE PROCESSING

Detected: 1 face at (340, 120) - (580, 420)
Expression: Smiling (confidence: 94%)
Lighting: Good (no correction needed)

Enhancements Applied:
- Background removed (AI matting)
- Contrast increased 15%
- Slight color correction (warmer)
- Positioned: Right side, 38% of frame
- Added subtle outline glow

Face Quality Score: 8.7/10 ✓
```

### Text Optimization

Automatically optimize text for readability:

**Text Analysis**
```
Title: "How I Made My API 10x Faster"
Length: 32 characters

Thumbnail Text Options:
1. "10x FASTER API" (Simple, direct)
2. "API SPEED 10x" (Alternative emphasis)
3. "FASTER APIs" + "10x" badge (Split)

Readability Scores:
- Small (100px): 9/10, 8/10, 10/10 ✓
- Mobile: 8/10, 7/10, 10/10 ✓

Recommended: Option 3 (best mobile readability)
```

**Font Selection**
```
Based on "technical tutorial" category:

Primary Font: Inter Bold (modern, readable)
- Weight: 800
- Size: 96pt (main), 48pt (sub)
- Color: White with black stroke (3px)
- Shadow: Drop shadow for depth

Alternative Fonts:
- Montserrat (similar energy)
- Roboto Condensed (more compact)
- Bebas Neue (more dramatic)
```

### Color Psychology

Choose colors based on content:

```
Video: "How I Made My API 10x Faster"
Category: Tutorial, Technical

Recommended Palette:
Primary: #10B981 (Green - Success, improvement)
Secondary: #3B82F6 (Blue - Trust, technical)
Accent: #F59E0B (Yellow - Highlight, attention)
Background: #1F2937 (Dark gray - Modern, tech)

Why These Colors:
- Green: Positive outcome, improvement
- Blue: Technical credibility
- Dark: Professional, coding aesthetic
- High contrast: Readable at all sizes

Alternative for "Error/Bug Fix" content:
Primary: #EF4444 (Red - Problem)
Secondary: #10B981 (Green - Solution)
```

### Batch Generation

Generate thumbnails for multiple videos:

```bash
/thumbnail batch video-list.txt
```

`video-list.txt`:
```
How I Made My API 10x Faster | tutorial
Building a Redis Cache | tutorial
Database Optimization Tips | listicle
My Biggest Coding Mistake | story
Redis vs Memcached | comparison
```

Output:
```
📦 BATCH GENERATION

Processing 5 videos...

[▓▓▓▓▓▓▓▓▓▓] 1/5 - How I Made My API 10x Faster
Generated: 3 variants (tutorial style)

[▓▓▓▓▓▓▓▓▓▓] 2/5 - Building a Redis Cache
Generated: 3 variants (tutorial style)

[▓▓▓▓▓▓▓▓▓▓] 3/5 - Database Optimization Tips
Generated: 3 variants (listicle style)

[▓▓▓▓▓▓▓▓▓▓] 4/5 - My Biggest Coding Mistake
Generated: 3 variants (story style)

[▓▓▓▓▓▓▓▓▓▓] 5/5 - Redis vs Memcached
Generated: 3 variants (comparison style)

✅ BATCH COMPLETE

Total: 15 thumbnails generated
Location: thumbnails/batch-2025-01-15/
Average generation time: 12 seconds per video

Ready for upload with distribution-automator
```

## Thumbnail Analysis

Analyze existing thumbnails to learn what works:

```bash
/thumbnail analyze existing-thumbnail.jpg
```

```
🔍 THUMBNAIL ANALYSIS

File: existing-thumbnail.jpg
Dimensions: 1280x720 ✓
File Size: 243 KB ✓

Visual Elements:
├─ Face detected: Yes (42% of frame) ✓
├─ Text detected: "FASTER API" (96pt)
├─ Text readability: 9/10 ✓
├─ Color contrast: 8.2/10 ✓
└─ Background: Dark gradient

Design Score: 8.6/10

Strengths:
✓ Face is expressive and large
✓ Text is clear and bold
✓ High contrast for visibility
✓ Professional color palette

Improvements:
⚠ Text could be 15% larger for mobile
⚠ Consider adding small badge/icon
⚠ Background slightly busy
⚠ Try warmer colors for more personality

Predicted CTR: 9.2%
Compared to average: +34% above typical 6.8%
```

## Platform-Specific Optimization

Different platforms need different approaches:

**YouTube (1280x720)**
```
- Large text (readable at 100px preview)
- High contrast
- Face recommended (if available)
- 3-7 words max
- File size: <2MB
```

**TikTok/Shorts (1080x1920 cover)**
```
- Vertical format
- Face in upper 60%
- Large text in safe zone
- Bright colors
- File size: <500KB
```

**LinkedIn (1200x627)**
```
- Professional appearance
- Clean design
- Text-heavy acceptable
- Business colors
- File size: <5MB
```

**Twitter (1200x675)**
```
- Punchy text
- Eye-catching
- Works without context
- File size: <5MB
```

## Best Practices

### Text Guidelines
- **3-7 words maximum** - Any more is too busy
- **Readable at 100px** - Most people see small previews
- **High contrast** - White text, dark stroke + shadow
- **Split long titles** - Focus on hook, not full title

### Face Guidelines
- **Expression matters** - Shocked, happy, or focused
- **30-40% of frame** - Large enough to see emotion
- **Eye contact** - Looking at camera is best
- **Good lighting** - Front-lit, no harsh shadows

### Color Guidelines
- **High contrast** - Visible in any context
- **3 colors max** - More is chaotic
- **Brand consistency** - Use same palette across videos
- **Test in grayscale** - Should work without color

## Integration Points

Works with other Creator Studio plugins:

- **video-editor-ai**: Extract best frame for thumbnail
- **title-optimizer**: Get optimized title for thumbnail text
- **analytics-insights**: A/B test thumbnail performance
- **distribution-automator**: Auto-upload with video
- **batch-recording-scheduler**: Generate thumbnails for series

## Examples

### Tutorial Thumbnail
```bash
User: /thumbnail "Building a REST API in 15 Minutes"

Claude:
📊 Generated Tutorial Style Thumbnail

Layout: Step-by-step visual
Text: "REST API" (large) + "15 MIN" badge
Colors: Blue/Green tech palette
Elements: Code editor screenshot + terminal
Predicted CTR: 8.9%

Files:
- rest-api-15min-A.png (Tutorial style)
- rest-api-15min-B.png (Tech style)
- rest-api-15min-C.png (Minimal style)
```

### Comparison Thumbnail
```bash
User: /thumbnail "Redis vs PostgreSQL" --style comparison

Claude:
📊 Generated Comparison Style Thumbnail

Layout: Split screen VS design
Left: Redis logo + "FAST" badge
Right: PostgreSQL logo + "RELIABLE" badge
Center: Large "VS" with lightning bolt
Colors: Red vs Blue
Predicted CTR: 11.4%
```

## Troubleshooting

### Text Too Small on Mobile
```
⚠️ Warning: Text may be hard to read on mobile

Current: 72pt font at 1280x720
Recommended: 96pt minimum

Auto-fix: Increase font to 96pt? (y/n)
```

### Low Contrast Warning
```
⚠️ Low contrast detected (4.2:1 ratio)

Current: Light blue text on blue background
Recommended: 7:1 minimum for accessibility

Suggestions:
- Add black stroke (3-4px)
- Add drop shadow
- Darken background
- Use white text instead
```

### Face Detection Failed
```
❌ No face detected in image

Troubleshooting:
- Ensure face is visible and front-on
- Check image isn't too dark
- Try a different photo
- Use manual positioning with --face-coords
```

Your goal: Create scroll-stopping thumbnails that get clicks and accurately represent your video content.
