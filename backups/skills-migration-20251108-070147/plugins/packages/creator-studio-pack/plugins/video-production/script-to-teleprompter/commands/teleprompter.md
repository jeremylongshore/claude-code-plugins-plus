---
name: teleprompter
description: Convert video scripts to teleprompter format with auto-scroll, timing marks, and delivery coaching
---

# Script to Teleprompter Command

Transform written scripts into teleprompter-ready formats with auto-scroll and delivery optimization.

## Usage

```bash
/teleprompter [script-file.md]              # Convert script to teleprompter
/teleprompter [script] --practice           # Practice mode with timing
/teleprompter start                         # Start teleprompter display
/teleprompter pause                         # Pause auto-scroll
/teleprompter speed [1-10]                  # Adjust scroll speed
/teleprompter export [script] --format pdf  # Export for physical prompter
```

## Purpose

Convert scripts to teleprompter format for:
- **Natural delivery** - Read while maintaining eye contact
- **Consistent pacing** - Auto-scroll at optimal speed
- **Timing practice** - Hit target video length
- **Professional presentation** - Smooth, confident delivery

## Script Processing

### Input: Raw Script

```markdown
# How I Made My API 10x Faster

Hey everyone! Today I'm going to show you how I took my API from 2000 milliseconds response time down to just 180 milliseconds. That's more than 10x faster, and it only took me about an hour to implement.

The secret? Redis caching. Let me walk you through exactly how I did it.

[Show terminal with slow API]

So here's the problem...
```

### Output: Teleprompter Format

```
╔════════════════════════════════════════════════╗
║                                                ║
║     Hey everyone! Today I'm going to show      ║
║     you how I took my API from 2000            ║
║     milliseconds response time down to         ║
║     just 180 milliseconds.                     ║
║                                                ║
║     [PAUSE - Show excitement]                  ║
║                                                ║
║     That's more than 10x faster, and it        ║
║     only took me about an hour to              ║
║     implement.                                 ║
║                                                ║
║     [SLOW DOWN - Key point]                    ║
║                                                ║
║     The secret? Redis caching.                 ║
║                                                ║
║     [PAUSE - Let it sink in]                   ║
║                                                ║
║     Let me walk you through exactly            ║
║     how I did it.                              ║
║                                                ║
║     >>> VISUAL: Terminal with slow API <<<     ║
║                                                ║
║     [TRANSITION - Move to screen]              ║
║                                                ║
║     So here's the problem...                   ║
║                                                ║
╚════════════════════════════════════════════════╝

Scroll Speed: ████████░░ 80%  [+] [-]
Elapsed: 00:32  Remaining: ~04:28  Total: ~05:00
```

## Format Features

### Text Optimization

**Line Breaks for Natural Breathing**
```
❌ BEFORE (Hard to read):
Hey everyone! Today I'm going to show you how I took my API from 2000 milliseconds response time down to just 180 milliseconds.

✓ AFTER (Natural pauses):
Hey everyone!

Today I'm going to show you how I took
my API from 2000 milliseconds response
time down to just 180 milliseconds.
```

**Delivery Cues**
```
[PAUSE]          - Stop for 1-2 seconds
[PAUSE LONG]     - Stop for 3-4 seconds
[SLOW DOWN]      - Decrease pace for emphasis
[SPEED UP]       - Increase pace for energy
[SMILE]          - Facial expression cue
[LOOK AT CAMERA] - Direct eye contact moment
[GESTURE]        - Use hand motion
[EMPHASIZE]      - Stress this word/phrase
```

**Visual Action Markers**
```
>>> VISUAL: Screen recording starts <<<
>>> VISUAL: Terminal command <<<
>>> VISUAL: Code editor <<<
>>> VISUAL: Show graph <<<
>>> VISUAL: Back to camera <<<
>>> B-ROLL: External footage <<<
```

**Timing Markers**
```
(00:15) - Hook delivered
(01:30) - Problem explained
(03:00) - Solution begins
(08:45) - Results shown
(09:30) - CTA (Call to action)
```

### Auto-Scroll Features

**Adaptive Speed**
```
Base Speed: 120 words per minute
Automatically adjusts based on:
- Sentence length (slower for long sentences)
- Complexity (slower for technical terms)
- Delivery cues (pauses stop scroll)
- User control (keyboard/foot pedal)
```

**Smooth Scrolling Algorithm**
```
├─ Ease-in at paragraph start
├─ Constant speed during reading
├─ Ease-out at delivery cues
├─ Full stop at [PAUSE] markers
└─ Resume with smooth acceleration
```

## Implementation

When user runs `/teleprompter script.md --practice`:

**Step 1: Process Script**
```
📝 PROCESSING SCRIPT

File: redis-tutorial-script.md
Word count: 1,247 words
Estimated time: 9:22 at 130 WPM

Analyzing for optimization...
- Added 34 natural line breaks
- Inserted 12 delivery cues
- Marked 7 visual transitions
- Set 5 timing checkpoints

Readability Score: 8.7/10 (good for teleprompter)
```

**Step 2: Practice Mode**
```
🎯 PRACTICE MODE

Get ready in: 3... 2... 1... GO!

╔════════════════════════════════════════════════╗
║                                                ║
║     Hey everyone!                              ║
║                                                ║
║     [Current line appears here]                ║
║                                                ║
║     [Next line preview below]                  ║
║                                                ║
╚════════════════════════════════════════════════╝

[Press SPACE to pause/resume]
[Press ↑/↓ to adjust speed]
[Press R to restart]
[Press ESC to exit]

Real-time Feedback:
├─ Current pace: 125 WPM (target: 130 WPM) ✓
├─ Time elapsed: 02:15 / 09:22 estimated
├─ Energy level: Good, maintain energy
└─ Delivery: Natural, good pauses
```

**Step 3: Live Teleprompter**
```
Starting teleprompter in:
3...
2...
1...

╔═══════════════════════════════════════════════════╗
║                                                   ║
║                                                   ║
║         Hey everyone!                             ║
║                                                   ║
║         Today I'm going to show you               ║
║         how I took my API from 2000               ║
║         milliseconds response time down           ║
║         to just 180 milliseconds.                 ║
║                                                   ║
║         [PAUSE - Show excitement]                 ║
║                                                   ║
║         That's more than 10x faster, and          ║
║         it only took me about an hour             ║
║         to implement.                             ║
║                                                   ║
║                                                   ║
╚═══════════════════════════════════════════════════╝
```

## Advanced Features

### Timing Practice Mode

Practice hitting exact time targets:

```
🎯 TIMING PRACTICE

Target: 10:00 video
Script: 1,247 words
Pace needed: 125 WPM

Checkpoints:
├─ 02:30 - Hook complete ⏱️
├─ 05:00 - Problem explained ⏱️
├─ 08:00 - Solution shown ⏱️
└─ 09:30 - Wrap-up before CTA ⏱️

[Starting practice run...]

Checkpoint 1 (02:30 target)
Actual: 02:42
Difference: +12 seconds (Speed up slightly)

Recommendation: Increase pace to 132 WPM for next section
```

### Energy Level Coaching

Real-time delivery feedback:

```
📊 ENERGY MONITORING

Current section: "Hook" (First 30 seconds)
Required energy: HIGH (8/10)
Your energy: Medium (5/10)

Suggestions:
🎤 Increase vocal volume 20%
😊 More facial expression
💪 Add hand gestures
⚡ Faster pace in this section

Target: Grab attention in first 10 seconds
```

### Multi-Take Comparison

Compare multiple recording attempts:

```
📹 TAKE COMPARISON

Take 1: 10:15 (target 10:00)
├─ Pace: 122 WPM (target: 125 WPM)
├─ Energy: 6/10 (target: 8/10)
├─ Pauses: Too long (avg 3.2s)
└─ Rating: 6.5/10

Take 2: 09:52 ✓ (within target)
├─ Pace: 126 WPM ✓ (target: 125 WPM)
├─ Energy: 7/10 (good improvement)
├─ Pauses: Good (avg 2.1s)
└─ Rating: 8.2/10 ⭐ BEST

Take 3: 09:45 (slightly fast)
├─ Pace: 131 WPM (bit fast)
├─ Energy: 8/10 ✓ (great energy)
├─ Pauses: Too short (avg 1.5s)
└─ Rating: 7.8/10

Recommendation: Use Take 2
```

### Physical Teleprompter Export

Export for use with actual teleprompter hardware:

```bash
/teleprompter export script.md --format pdf --device physical
```

```
📄 EXPORTING FOR PHYSICAL PROMPTER

Format: PDF (Letter size, portrait)
Font: 48pt Arial (high contrast)
Layout: 6 words per line (optimal reading)
Margins: 2 inches (visible from 6 feet)

Generated:
- redis-script-prompter.pdf (12 pages)
- redis-script-prompter-mirror.pdf (for mirror prompters)

Print settings:
├─ Paper: Letter (8.5" x 11")
├─ Orientation: Portrait
├─ Font size: 48pt
├─ Double-spaced
└─ High contrast black on white
```

## Keyboard Shortcuts

Essential controls during recording:

```
SPACE         - Pause/Resume scroll
↑             - Increase scroll speed
↓             - Decrease scroll speed
→             - Skip forward 10 seconds
←             - Skip backward 10 seconds
R             - Restart from beginning
M             - Add marker at current position
ESC           - Exit teleprompter
F             - Toggle fullscreen
C             - Toggle delivery cues
T             - Toggle timing markers
```

## Foot Pedal Support

Use USB foot pedal for hands-free control:

```
🦶 FOOT PEDAL DETECTED

Left Pedal:  Pause/Resume
Middle Pedal: Scroll backward
Right Pedal:  Scroll forward

Custom mapping:
/teleprompter config pedal --left pause --right speed-up --middle restart
```

## Display Modes

### Standard Mode (Default)
```
╔══════════════════════════════╗
║                              ║
║  Hey everyone! Today I'm     ║
║  going to show you how I     ║
║  made my API 10x faster.     ║
║                              ║
╚══════════════════════════════╝

Best for: Desktop, laptop recording
Font: 36pt, white on black
Visible distance: 3-5 feet
```

### Presentation Mode
```
╔══════════════════════════════╗
║                              ║
║       Hey everyone!          ║
║                              ║
║  Today I'm going to show     ║
║  you how I made my API       ║
║  10x faster.                 ║
║                              ║
╚══════════════════════════════╝

Best for: Standing presentations
Font: 48pt, centered
Visible distance: 6-8 feet
```

### Mobile Mode
```
┌──────────────┐
│              │
│ Hey everyone │
│              │
│ Today I'm    │
│ going to     │
│ show you how │
│              │
└──────────────┘

Best for: Phone/tablet prompter
Font: 24pt, optimized for small screen
Portrait orientation
```

### Mirror Mode (for physical prompters)
```
╔══════════════════════════════╗
║                              ║
║     .retsaf x01 IPA ym edam  ║
║     I woh uoy wohs ot        ║
║     !enoyreve yeH            ║
║                              ║
╚══════════════════════════════╝

Best for: Mirror-based teleprompters
Horizontally flipped text
High contrast for reflection
```

## Integration Points

Works with other Creator Studio plugins:

- **script-writer-pro**: Generate scripts optimized for teleprompter
- **video-editor-ai**: Sync teleprompter timing with edited video
- **audio-mixer-assistant**: Analyze pacing from audio recording
- **batch-recording-scheduler**: Queue multiple scripts for recording
- **content-calendar-ai**: Schedule recording sessions

## Best Practices

### Script Preparation
1. **Write conversationally** - Use contractions, natural speech
2. **Short sentences** - 10-15 words per sentence
3. **Clear structure** - Intro, body, conclusion
4. **Add pauses** - Mark natural breathing points
5. **Include cues** - Delivery instructions for yourself

### Delivery Tips
1. **Practice 2-3 times** - Get comfortable with flow
2. **Maintain eye contact** - Look at camera, not just prompter
3. **Natural pace** - Don't race, breathe normally
4. **Energy in voice** - Smile, it comes through in audio
5. **Use markers** - Hit timing checkpoints consistently

### Setup Optimization
1. **Position prompter** - Eye level with camera
2. **Adjust brightness** - Readable without squinting
3. **Test scroll speed** - Find comfortable pace
4. **Clear distractions** - Full screen, notifications off
5. **Good lighting** - Front-lit, no harsh shadows

## Troubleshooting

### Scroll Too Fast
```
⚠️ Scroll pace too fast for comfortable reading

Current: 150 WPM
Recommended: 120-130 WPM for natural delivery

Auto-adjust to 125 WPM? (y/n)
```

### Missing Timing Checkpoints
```
⚠️ You're behind schedule

Checkpoint 2 (05:00 target)
Actual: 05:47
Difference: +47 seconds

Recommendations:
- Speed up next section to 138 WPM
- Or cut 45 seconds from script
- Or accept 10:45 total (instead of 10:00)
```

### Text Not Visible
```
❌ Text may not be visible from recording distance

Current setup:
Font: 24pt
Distance: 6 feet
Screen: 15" laptop

Recommendations:
- Increase font to 36pt minimum
- Move closer (4 feet recommended)
- Use external monitor (24"+)
```

## Example Workflow

```bash
# 1. Convert script to teleprompter format
User: /teleprompter redis-tutorial-script.md

# 2. Practice mode
User: /teleprompter --practice

Claude: Starting practice mode...
        Target: 10:00 | Pace: 125 WPM
        [Telepro mpter starts scrolling]

# 3. Record with live prompter
User: /record start redis-tutorial
User: /teleprompter start

# [User records video while reading from teleprompter]

# 4. Stop recording
User: /teleprompter pause
User: /record stop

Claude: ✅ Recording complete: 10:12 (target was 10:00)
        Timing accuracy: 98%
        Great take! 🎬
```

Your goal: Help creators deliver confident, natural, well-paced video narration with professional teleprompter support.
