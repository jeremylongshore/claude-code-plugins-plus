---
name: granola-performance-tuning
description: |
  Optimize Granola transcription accuracy, note quality, and processing speed.
  Use when improving transcription quality, reducing processing time,
  optimizing templates for better AI output, or tuning audio setup.
  Trigger: "granola performance", "granola accuracy", "granola quality",
  "improve granola", "granola transcription better".
allowed-tools: Read, Write, Edit
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code, codex, openclaw
tags: [saas, granola, performance, transcription]

---
# Granola Performance Tuning

## Overview
Optimize Granola output quality across three dimensions: audio/transcription accuracy, AI enhancement quality, and integration speed. Granola's AI (GPT-4o/Claude) produces better output when it has clean audio, well-typed notes, and structured templates.

## Prerequisites
- Working Granola installation with meetings captured
- Willingness to improve audio setup and meeting practices
- At least 3-5 meetings captured to establish baseline quality

## Instructions

### Step 1 — Optimize Audio for Transcription

Granola captures system audio from your device. Transcription accuracy depends entirely on audio quality:

**Hardware recommendations (by priority):**

| Setup | Accuracy Impact | Recommendation |
|-------|----------------|----------------|
| Wired headset with mic | Highest | Best for solo/remote meetings |
| USB condenser mic | High | Best for in-office, multiple speakers |
| Laptop built-in mic | Medium | Acceptable for quiet environments |
| Bluetooth headset | Variable | May cause dropouts — test first |
| Speakerphone in room | Low | Echo and distance degrade accuracy |

**Audio configuration checklist:**
- [ ] Correct input device selected in System Settings > Sound > Input
- [ ] Input volume at 75-100% (not too low, not clipping)
- [ ] Audio enhancements disabled (Windows: right-click device > Properties > disable enhancements)
- [ ] No conflicting virtual audio software (Loopback, BlackHole, etc.)
- [ ] Bluetooth device stable (or switch to wired if experiencing drops)

**Room setup:**
- [ ] Minimal background noise (close doors, turn off fans)
- [ ] Soft surfaces to reduce echo (avoid glass-walled conference rooms)
- [ ] Mic within 12 inches of speaker(s)
- [ ] Meeting participants using headsets (reduces echo and crosstalk)

### Step 2 — Improve Meeting Practices

These behaviors directly improve Granola's output:

| Practice | Impact | Why It Helps |
|----------|--------|-------------|
| State names when assigning work | High | "Sarah, can you handle the API spec?" enables correct attribution |
| Use explicit action language | High | "Action item: review by Friday" — AI detects structured language |
| One speaker at a time | High | Crosstalk confuses speaker diarization |
| Summarize decisions verbally | Medium | "So we've decided to go with option B" — AI captures decisions |
| Spell technical terms first time | Medium | "We'll use Kubernetes, K-U-B-E-R-N-E-T-E-S" — improves accuracy |
| Type notes during the meeting | High | Your notes give the AI critical context for enhancement |
| Brief recap at meeting end | Medium | "To summarize, we agreed on X, Y, and Z" — improves summary |

### Step 3 — Optimize Templates for AI Quality

Template structure directly affects the quality of enhanced output:

**High-quality template design:**
```markdown
## Summary
[2-3 sentence overview of the meeting]

## Key Decisions
[Bullet list of decisions made, with reasoning]

## Action Items
[Format: - [ ] @person: task (due date)]

## Open Questions
[Items that need follow-up or weren't resolved]

## Next Steps
[What happens after this meeting]
```

**Template optimization tips:**
1. **Use 5-7 sections max** — too many sections dilute content
2. **Include format hints** — `[Format: - [ ] @person: task]` guides the AI
3. **Put Action Items near the end** — AI processes sequentially, actions at the end capture the full meeting
4. **Add "Verbatim Quotes" section for customer calls** — AI will pull exact language from the transcript
5. **Avoid generic sections** — "Notes" and "Discussion" produce vague output; be specific

### Step 4 — Post-Meeting Quality Review (5 Minutes)

After enhancing notes, spend 5 minutes on quality assurance:

- [ ] **Summary accurate?** Does it reflect what actually happened?
- [ ] **Action items complete?** Are all commitments captured with correct owners?
- [ ] **Decisions correct?** No hallucinated decisions or mixed-up attributions?
- [ ] **Sensitive content?** Remove anything that shouldn't be shared before posting
- [ ] **Missing context?** Add background the AI couldn't know

### Step 5 — Use Granola Chat to Fill Gaps

After enhancement, use Chat to improve the notes:

```
"What did Mike say about the timeline?"
→ Searches transcript for Mike's statements about timeline

"Were there any disagreements that aren't captured in the summary?"
→ Analyzes transcript for conflicting viewpoints

"Add the budget numbers that were discussed"
→ Pulls specific figures from the transcript

"Rewrite the action items with more detail"
→ Expands terse action items with transcript context
```

### Step 6 — Measure and Track Quality

| Metric | Target | How to Measure |
|--------|--------|----------------|
| Transcription accuracy | >95% word accuracy | Spot-check 2-3 min of transcript vs. audio |
| Action item detection | >90% captured | Compare enhanced notes to manual list |
| Decision accuracy | 100% correct | Verify all listed decisions actually happened |
| Processing time | <2 min for 30-min meeting | Timestamp when meeting ends vs. when notes are ready |
| Enhancement usefulness | 4+/5 team rating | Monthly survey: "How useful are Granola notes?" |

Track these monthly. If accuracy drops below target:
1. Check audio setup (most common cause)
2. Review template structure
3. Verify meeting practices are being followed
4. Contact Granola support for persistent issues

## Output
- Audio setup optimized for maximum transcription accuracy
- Meeting practices improving AI output quality
- Templates structured for effective enhancement
- Quality measurement process established

## Error Handling

| Issue | Cause | Fix |
|-------|-------|-----|
| <85% transcription accuracy | Poor microphone or noisy room | Upgrade to wired headset, reduce background noise |
| Action items missed | Vague language ("someone should...") | Use explicit format: "Action item: @person does X by Y" |
| Wrong speaker attribution | Crosstalk or no name usage | State names, avoid overlapping speech |
| Slow processing (>5 min) | Long meeting or server load | Normal for 2+ hour meetings; check status.granola.ai |
| Hallucinated decisions | AI filling template sections | Review before sharing; remove decisions that didn't happen |

## Resources
- [Get the Best from Granola](https://www.granola.ai/blog/get-the-best-from-granola)
- [How Transcription Works](https://docs.granola.ai/help-center/taking-notes/how-transcription-works)
- [Customize Templates](https://docs.granola.ai/help-center/taking-notes/customise-notes-with-templates)

## Next Steps
Proceed to `granola-cost-tuning` for cost optimization and plan selection.
