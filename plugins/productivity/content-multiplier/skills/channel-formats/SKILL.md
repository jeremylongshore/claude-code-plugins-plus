---
name: channel-formats
description: |
  Transforms one piece of content into each marketing channel's native format —
  length, structure, hooks, and conventions — across LinkedIn, X threads,
  newsletters, Instagram, YouTube, short video, and blogs. Use when reformatting
  content for a specific channel. Trigger with "channel format", "adapt for LinkedIn", or "/multiply".
allowed-tools: Read, Write, Glob
argument-hint: '[--channels linkedin,x-thread,newsletter,...]'
version: "0.2.1"
author: localplugins <localplugins@proton.me>
license: MIT
compatibility: Designed for Claude Code
tags:
  - marketing
  - content
  - social-media
  - repurposing
  - formatting
---

# Channel Formats

## Overview

Channel Formats adapts a single source into the shape each platform expects, then hands the draft to the brand layer. Format is the container; brand voice is the content.

Every channel has its own limits and conventions: a LinkedIn post is not an X thread, and a YouTube description is not an Instagram caption.
This skill reads the spec for the requested channel from the plugin's bundled `channels/<id>.md` files, drafts to that spec, and enforces the length limit.
It is instruction-driven and writes ready-to-paste files, with no accounts, keys, or network access.

## Prerequisites

- The source content to adapt (a file path or pasted text) and one or more target channels.
- The bundled channel specs, which ship inside this skill at `channels/`. The skill uses Glob and Read to load the right spec and Write to save each derivative.
- An active brand profile so the `brand-voice` skill can run on top; if none exists, the caller is pointed to `/brand-setup`.

## Channels (canonical IDs)

The channel ID is also the output filename (for example `linkedin.md`).

- `linkedin` — professional single post — [channels/linkedin.md](channels/linkedin.md)
- `x-thread` — multi-post thread — [channels/x-thread.md](channels/x-thread.md)
- `newsletter` — email newsletter section — [channels/newsletter.md](channels/newsletter.md)
- `instagram` — caption plus hashtags — [channels/instagram.md](channels/instagram.md)
- `youtube` — description with timestamped chapters — [channels/youtube.md](channels/youtube.md)
- `short-video` — TikTok, Reels, or Shorts script — [channels/short-video.md](channels/short-video.md)
- `blog` — short post or excerpt — [channels/blog.md](channels/blog.md)

## Instructions

1. Identify the target channel by its canonical ID from the list above.
2. Read that channel's spec in `channels/<id>.md` — each spec defines Format, Length, Structure, Do, and Avoid.
3. Draft the derivative to the spec, mapping the source's core message onto that channel's hook and structure.
4. Check the character or word count and enforce the channel's limit; trim or split as the spec requires.
5. Run the `brand-voice` self-check so the draft obeys the brand's tone, glossary, and compliance rules.
6. For localized copy, re-fit after transcreation because text expands or contracts across languages.
7. Write one file per derivative, named after the channel ID.

## Output

One ready-to-paste file per channel, named by the channel ID (`linkedin.md`, `x-thread.md`, and so on). Each file holds the fully drafted asset, already inside the channel's limit and already run through the brand self-check. Threads and multi-part formats are numbered as the platform expects.

## Error Handling

| Condition | Behavior |
|-----------|----------|
| Unknown channel ID | List the supported IDs and ask which to use; do not guess a format |
| Source too thin for a channel | Draft what the source supports and flag the gap rather than inventing facts |
| Draft exceeds the channel limit | Trim or split per the spec; never ship over-limit copy |
| No brand profile available | Draft to format, then note that the brand self-check was skipped |
| Localized text overflows after transcreation | Re-fit to the channel limit before writing the file |

## Examples

**Example: adapt one source to several channels**
> /multiply launch-note.md --channels linkedin,x-thread,instagram

Reads each channel spec, drafts three derivatives, runs the brand self-check, and writes `linkedin.md`, `x-thread.md`, and `instagram.md`.

**Example: single channel from pasted text**
> Turn this paragraph into an X thread

Loads `channels/x-thread.md`, splits the idea into hooked, numbered posts within the per-post limit.

**Example: re-fit localized copy**
> Fit the German LinkedIn draft back under the limit

Applies the LinkedIn spec to the expanded German text and trims it back within range.

## Related skills

See also the companion skills `brand-voice` (apply the brand on top of each format) and `transcreation` (localize before re-fitting to a channel).

## Resources

- [references/worked-examples.md](references/worked-examples.md) — one source turned into a fully drafted asset per channel, so each spec can be seen applied end to end.
- [references/adaptation-rules.md](references/adaptation-rules.md) — how to carry one core message across channels without repeating yourself, hook patterns, CTA-per-channel guidance, hashtag and length discipline, and common mistakes.
- Channel specs bundled with this skill: `channels/<id>.md`.
