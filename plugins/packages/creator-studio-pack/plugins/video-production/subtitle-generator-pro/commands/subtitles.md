---
name: subtitles
description: Generate animated subtitles in popular creator styles (Mr Beast, Ali Abdaal,...
---
# Subtitle Generator Pro Command

Create professional, animated subtitles in various popular creator styles with automatic transcription and timing.

## Usage

```bash
/subtitles [video-file.mp4]                   # Auto-generate with default style
/subtitles [video] --style mr-beast           # Use Mr Beast style
/subtitles [video] --style ali-abdaal         # Use Ali Abdaal style
/subtitles [video] --style hormozi            # Use Alex Hormozi style
/subtitles [video] --style minimal            # Clean, simple style
/subtitles [video] --language es              # Generate Spanish subtitles
/subtitles edit [subtitle-file.srt]           # Fine-tune existing subtitles
/subtitles preview [video] [srt]              # Preview before burning in
```

## Purpose

Generate subtitles that:
- **Increase retention** - Keep viewers watching longer
- **Improve accessibility** - Reach deaf/hard-of-hearing audience
- **Enable silent viewing** - 85% of social videos watched on mute
- **Boost engagement** - Highlight key words and phrases
- **Match brand style** - Consistent visual identity

## Subtitle Styles

### Mr Beast Style
```
Characteristics:
├─ Every word animated individually
├─ Large, bold text (center frame)
├─ Yellow highlights on important words
├─ High energy, rapid cuts
├─ ALL CAPS for emphasis
├─ Emoji integration 💰🔥⚡
└─ Bouncing/scaling animations

Example:
┌────────────────────────────┐
│                            │
│      I SPENT 💰            │
│      $100,000 ON THIS      │
│                            │
└────────────────────────────┘
[Each word appears with bounce effect]
[Key numbers/words in yellow]
```

### Ali Abdaal Style
```
Characteristics:
├─ Full sentences displayed
├─ Clean, sans-serif font
├─ Bottom center positioning
├─ Key words highlighted in color
├─ Smooth fade in/out
├─ Professional, readable
└─ Subtle emphasis animations

Example:
┌────────────────────────────┐
│                            │
│                            │
│                            │
│  This technique increased  │
│  my productivity by 10x    │
└────────────────────────────┘
["10x" highlighted in green]
[Smooth, professional transitions]
```

### Alex Hormozi Style
```
Characteristics:
├─ Short, punchy phrases
├─ Bold, impact font
├─ Strategic pauses for emphasis
├─ Red highlights on key points
├─ Minimal but powerful
├─ CAPS for key statements
└─ Vertical center alignment

Example:
┌────────────────────────────┐
│                            │
│       THIS IS THE          │
│       SECRET 🔑            │
│                            │
└────────────────────────────┘
[Quick cuts between phrases]
[Red highlights on power words]
```

### Minimal Style
```
Characteristics:
├─ Simple white text
├─ Black background bar
├─ Bottom third positioning
├─ Easy to read
├─ No animations
├─ Traditional subtitle format
└─ Accessibility-focused

Example:
┌────────────────────────────┐
│                            │
│                            │
│                            │
├────────────────────────────┤
│ Today I'm going to show    │
│ you how I made my API 10x  │
│ faster with Redis caching. │
└────────────────────────────┘
[Clean, traditional, accessible]
```

### Podcast Style
```
Characteristics:
├─ Speaker names displayed
├─ Color-coded by speaker
├─ Larger text for living room viewing
├─ Bottom center
├─ Sentence-based timing
└─ Smooth, unhurried pacing

Example:
┌────────────────────────────┐
│                            │
│                            │
│  JEREMY: So the key here   │
│  is to implement caching   │
│  at the API layer.         │
└────────────────────────────┘
[Speaker name in blue]
[Dialogue in white]
```

## Implementation

When user runs `/subtitles redis-tutorial.mp4 --style mr-beast`:

**Step 1: Transcription**
```
🎤 TRANSCRIBING AUDIO

File: redis-tutorial.mp4
Duration: 35:12
Audio quality: Good ✓

Using: OpenAI Whisper Large v3
Language: Auto-detect (English)
Accuracy mode: High

[▓▓▓▓▓▓▓▓▓▓] 100%

Transcription Complete:
├─ Words: 4,247
├─ Accuracy: 98.2%
├─ Speaker diarization: 1 speaker
└─ Processing time: 2m 14s

Transcript preview:
"Hey everyone! Today I'm going to show you how I
made my API ten times faster using Redis caching.
This took me about an hour to implement and the
results were incredible..."
```

**Step 2: Timing Analysis**
```
⏱️ ANALYZING TIMING

Calculating word-level timestamps...
Detecting natural pauses...
Identifying emphasis points...

Timing Statistics:
├─ Average words per second: 2.1
├─ Natural pauses: 247
├─ Speaking pace: Moderate (good for retention)
└─ Emphasis words detected: 89

Subtitle Segments:
├─ Total segments: 342
├─ Average duration: 2.3 seconds
├─ Max segment: 4.1 seconds ✓ (within limits)
└─ Min segment: 0.8 seconds ✓
```

**Step 3: Style Application**
```
🎨 APPLYING MR BEAST STYLE

Style: Mr Beast (high-energy, word-by-word)
Animation: Bounce + scale on entry
Highlighting: Yellow for numbers and power words
Font: Impact (bold, large)
Position: Center screen
Caps: Strategic (emphasis only)

Processing subtitles...
[▓▓▓▓▓▓▓▓▓▓] 100%

Key Words Highlighted (89 instances):
├─ Numbers: 10x, 2000ms, 180ms, 1 hour
├─ Power words: faster, incredible, amazing
├─ Technical: Redis, API, caching
└─ Emphasis: THIS, NOW, SECRET

Animations Applied:
├─ Entry: Bounce + scale (0.3s)
├─ Exit: Quick fade (0.1s)
├─ Emphasis: Yellow highlight + pulse
└─ Timing: Sync with audio peaks
```

**Step 4: Generate Output**
```
✅ SUBTITLES GENERATED

Files Created:
├─ redis-tutorial-subtitles.srt (standard format)
├─ redis-tutorial-subtitles.ass (advanced, with styling)
├─ redis-tutorial-burned.mp4 (video with subtitles burned in)
└─ redis-tutorial-preview.mp4 (10-second preview)

Subtitle Statistics:
├─ Total segments: 342
├─ Highlighted words: 89
├─ File size: 47 KB (SRT), 156 KB (ASS)
└─ Estimated render time: 8 minutes

Preview:
[Shows 10-second clip with animated subtitles]

Quality Checklist:
✓ Text readable at 480p
✓ Timing synced with audio
✓ No text overlapping
✓ Emphasis words highlighted
✓ Animations smooth
✓ Platform-safe colors (no pure white/black)

Ready to burn in with video-editor-ai or export separately
```

## Advanced Features

### Multi-Language Support

Generate subtitles in multiple languages:

```bash
/subtitles tutorial.mp4 --languages en,es,fr,de
```

```
🌍 MULTI-LANGUAGE GENERATION

Source: English (detected)
Target languages: Spanish, French, German

Transcribing...
├─ English: ✓ (98.2% accuracy)

Translating...
├─ Spanish: ✓ (96.8% accuracy)
├─ French: ✓ (97.1% accuracy)
└─ German: ✓ (96.3% accuracy)

Applying timing from English source...
Style: Ali Abdaal (clean, professional)

Generated:
├─ tutorial-en.srt
├─ tutorial-es.srt
├─ tutorial-fr.srt
└─ tutorial-de.srt

Tip: Upload all to YouTube for automatic language switching
```

### Keyword Highlighting

Automatically highlight important words:

```
🎯 KEYWORD DETECTION

Analyzing transcript for emphasis...

Categories:
├─ Numbers: 10x, 2000ms, 180ms, 100% (26 instances)
├─ Technical terms: Redis, API, cache, query (45 instances)
├─ Action words: implement, optimize, improve (18 instances)
└─ Emotion: incredible, amazing, powerful (12 instances)

Highlight Strategy:
├─ Yellow: Numbers and stats
├─ Green: Positive outcomes
├─ Red: Problems/challenges
├─ Blue: Technical terms
└─ White: Standard text

Custom keywords: "Redis", "10x", "faster", "caching"
```

### Speaker Diarization

Identify and label different speakers:

```
👥 SPEAKER DETECTION

Analyzing audio for speaker changes...

Detected Speakers: 2
├─ Speaker 1 (You): 87% of dialogue
├─ Speaker 2 (Guest): 13% of dialogue
└─ Overlap: 2 instances (both speaking)

Assigning colors:
├─ Speaker 1: Blue
├─ Speaker 2: Green

Formatting:
YOU: Hey everyone! Today we're talking about Redis.

GUEST: Yeah, Redis is an amazing tool for caching.

YOU: Exactly! Let me show you how I implemented it.
```

### Auto-Censoring

Automatically detect and censor profanity:

```
🤬 PROFANITY DETECTION

Scanning transcript...
Found: 3 instances

Censoring options:
1. Bleep sound + [BLEEP] text
2. Replace with "****"
3. Mute audio + hide text (2 seconds)
4. No censoring (leave as-is)

Select option (default: 1):

Applied censoring:
├─ 04:23 - [BLEEP] replaced
├─ 12:45 - [BLEEP] replaced
└─ 18:02 - [BLEEP] replaced

Platform safe: YouTube ✓ | TikTok ✓ | LinkedIn ✓
```

### Accessibility Enhancements

Optimize for deaf and hard-of-hearing:

```
♿ ACCESSIBILITY MODE

Enhancements:
├─ Speaker labels always shown
├─ [Sound effect] descriptions added
├─ [Music playing] indicators
├─ Tone/emotion cues [laughs], [sighs]
├─ Non-speech audio described
└─ High contrast (black background, white text)

Example:
[Upbeat music playing]

JEREMY: Hey everyone!

[Keyboard typing sounds]

JEREMY: So here's the code...

[Notification sound]

JEREMY: Oh wow, it works!
[Excited tone]
```

### Subtitle Editing

Fine-tune auto-generated subtitles:

```bash
/subtitles edit redis-tutorial.srt
```

```
📝 SUBTITLE EDITOR

Subtitle 1 (00:00:00 - 00:00:03)
Original: "Hey everyone today I'm going to show you"
Issues: Missing punctuation

✏️ Corrected: "Hey everyone! Today I'm going to show you"

Subtitle 2 (00:00:03 - 00:00:07)
Original: "how I made my API ten times faster"
Issues: "ten" should be "10x" for emphasis

✏️ Corrected: "how I made my API 10x faster"

Common Fixes Applied:
├─ Added punctuation: 34 instances
├─ Fixed capitalization: 12 instances
├─ Corrected numbers: 8 instances (ten → 10)
├─ Split long segments: 5 instances
└─ Merged short segments: 7 instances

Save changes? (y/n)
```

## Platform-Specific Optimization

### YouTube
```
Format: SRT (upload separately)
Position: Bottom center
Font size: Medium (readable at 480p)
Style: Your brand style
Benefits: SEO boost, accessibility, multi-language
```

### TikTok/Instagram Reels
```
Format: Burned-in (ASS)
Position: Center (safe zone)
Font size: Large (mobile screens)
Style: Mr Beast (high energy, every word)
Benefits: Essential (85% watch on mute)
```

### LinkedIn
```
Format: Burned-in (SRT)
Position: Bottom third
Font size: Large (professional)
Style: Ali Abdaal (clean, readable)
Benefits: Professional, 85% watch on mute
```

### Twitter
```
Format: Burned-in (SRT)
Position: Bottom center
Font size: Large
Style: Minimal (high contrast)
Benefits: Feed auto-plays on mute
```

## Subtitle File Formats

### SRT (SubRip)
```
1
00:00:00,000 --> 00:00:03,500
Hey everyone! Today I'm going to
show you how I made my API 10x faster.

2
00:00:03,500 --> 00:00:07,200
The secret? Redis caching.
```
**Use Case**: Standard format, universally supported

### ASS (Advanced SubStation Alpha)
```
[Script Info]
Title: Redis Tutorial

[V4+ Styles]
Style: Default,Arial,48,&H00FFFFFF,&H000000FF,&H00000000,&H00000000,0,0,0,0,100,100,0,0,1,2,2,2,10,10,10,1

[Events]
Dialogue: 0,0:00:00.00,0:00:03.50,Default,,0,0,0,,Hey everyone! Today I'm going to\Nshow you how I made my API {\c&H00FFFF&}10x faster{\r}.
```
**Use Case**: Advanced styling, animations, positioning

### VTT (WebVTT)
```
WEBVTT

00:00.000 --> 00:03.500
Hey everyone! Today I'm going to
show you how I made my API 10x faster.

00:03.500 --> 00:07.200
The secret? Redis caching.
```
**Use Case**: Web-based players, HTML5 video

## Integration Points

Works with other Creator Studio plugins:

- **video-editor-ai**: Burn subtitles into video
- **audio-mixer-assistant**: Use clean audio for better transcription
- **script-to-teleprompter**: Compare script to actual spoken words
- **distribution-automator**: Platform-specific subtitle formats
- **batch-recording-scheduler**: Batch process multiple videos

## Best Practices

### Timing
1. **2-4 seconds per subtitle** - Comfortable reading speed
2. **Sync with natural pauses** - Don't break mid-sentence awkwardly
3. **Never exceed 5 seconds** - Viewers lose interest
4. **Word-by-word for high energy** - Mr Beast style for retention
5. **Full sentences for professional** - Ali Abdaal style for credibility

### Readability
1. **Max 2 lines per subtitle** - More is hard to read
2. **40 characters per line** - Optimal reading width
3. **High contrast colors** - White on black, or black on white
4. **Avoid pure white (#FFFFFF)** - Use off-white (#F0F0F0)
5. **Add text outline** - 2-3px stroke for visibility

### Styling
1. **Match brand identity** - Consistent across videos
2. **Less is more** - Don't over-animate
3. **Test on mobile** - Most viewers on phones
4. **Consider colorblind** - Don't rely only on color
5. **Professional for business** - Clean for LinkedIn

## Troubleshooting

### Poor Transcription Accuracy
```
⚠️ Transcription accuracy: 84.2% (below 95% target)

Common causes:
- Background noise
- Multiple speakers overlapping
- Heavy accent
- Technical jargon
- Poor audio quality

Solutions:
✓ Use audio-mixer-assistant first
✓ Manually review and correct
✓ Provide custom vocabulary list
✓ Use higher quality audio source
```

### Subtitles Out of Sync
```
⚠️ Subtitles drifting out of sync

Detected at: 5:34 (2.3 seconds off)

Causes:
- Variable framerate video
- Audio track separate from video
- Incorrect starting timestamp

Auto-fix:
- Detect drift points
- Adjust timing linearly
- Re-sync to audio peaks

Apply auto-fix? (y/n)
```

### Text Unreadable on Mobile
```
⚠️ Text too small for mobile viewing

Current: 32pt font at 1080p
Recommended: 48pt minimum

Mobile readability test:
- iPhone SE (4.7"): Hard to read ❌
- iPhone 14 (6.1"): Barely readable ⚠️
- iPad Mini (8.3"): Readable ✓

Increase font size to 48pt? (y/n)
```

## Example Workflow

```bash
# 1. Generate subtitles with Mr Beast style
User: /subtitles redis-tutorial.mp4 --style mr-beast

# 2. Preview result
User: /subtitles preview redis-tutorial.mp4 redis-tutorial-subtitles.srt

Claude: [Shows 10-second preview clip]
        Looks good? (y/n)

# 3. Generate for multiple platforms
User: /subtitles redis-tutorial.mp4 --platforms youtube,tiktok,linkedin

Claude: ✅ Generated platform-specific versions:
        - redis-tutorial-youtube.srt (separate file)
        - redis-tutorial-tiktok.mp4 (burned-in, vertical)
        - redis-tutorial-linkedin.mp4 (burned-in, clean)

# 4. Multi-language versions
User: /subtitles redis-tutorial.mp4 --languages en,es,fr

Claude: ✅ Generated 3 language versions
        Ready for distribution-automator
```

Your goal: Make every video accessible and engaging with professional, on-brand subtitles that boost retention and reach.
