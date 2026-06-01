---
title: "The Unicode Layer Your Validator Can't See"
description: "Schema validation can't see invisible Unicode. A stdlib-only CI gate that catches tag-char injection, Trojan Source bidi overrides, and homoglyph attacks."
date: "2026-05-24"
tags: ["ci-cd", "python", "security", "claude-code", "automation"]
featured: false
---
A schema validator reads parsed structure. It never sees the bytes.

That gap is where a whole class of supply-chain attack lives. The `claude-code-plugins` marketplace already ran a schema validator over every skill, agent, command, and catalog file — confirming required fields, enum values, shapes. All of it operating on the *parsed* document. None of it looking at the raw codepoints underneath.

An attacker can hide an instruction in characters that are invisible to a human reviewer and invisible to a structural validator, yet fully meaningful to an LLM that parses the file as text — or to a shell that executes a line copied out of it. The reviewer sees `npm install left-pad`. The model sees something else.

On 2026-05-24 the Socket "TrapDoor" advisory described exactly this: invisible Unicode tag characters smuggling instructions into LLM-parsed content. The same day, we shipped a CI gate for it — and folded in the older Trojan Source class (CVE-2021-42574) while we were at it.

## The threat model has three shapes

The detection model is built around three distinct attack surfaces, each with a different blast radius and a different rate of legitimate false positives. That asymmetry is the whole reason the gate is tiered instead of binary.

**Tag characters (U+E0000–U+E007F).** These render as nothing. A human sees an empty span. An LLM reading the file as a token stream reads them as text — they can carry a complete hidden instruction inside what looks like an innocent line of documentation. This is the TrapDoor vector. There is no legitimate reason for a tag character to appear in a skill file. Unambiguous attack.

**Bidirectional (bidi) overrides and isolates (U+202A–U+202E, U+2066–U+2069).** Trojan Source. These reorder how text *renders* without changing how it *parses*. The classic demonstration: code that displays as a benign comment to a reviewer but executes as an active statement. Renders as one thing, parses as another. Also unambiguous.

**Homoglyphs.** A Cyrillic `а` (U+0430) is pixel-identical to a Latin `a` (U+0061) in most fonts. Drop one into `npm install pаckage` and the reviewer reads the right name while the resolver fetches a different one. This is a real attack — but mixing scripts is also completely normal in human prose. Cyrillic next to Latin in a sentence is not suspicious. The signal only matters in a narrow context.

## The artifact

`scripts/validate-unicode-hygiene.py` — 317 lines, stdlib only. `argparse`, `pathlib`, `re`, `unicodedata`, `dataclasses`. No third-party dependency, nothing to pin, nothing to audit transitively. The detection rules are original, derived from the public Unicode Standard, the CVE-2021-42574 advisory, and the TrapDoor advisory. Not a fork of any existing scanner.

The codepoint classes map straight onto the threat model:

```python
TAG_CHARS = range(0xE0000, 0xE0080)  # exclusive end -> U+E0000-U+E007F inclusive
BIDI_CONTROLS = frozenset({0x202A, 0x202B, 0x202C, 0x202D, 0x202E,
                           0x2066, 0x2067, 0x2068, 0x2069})
ZERO_WIDTH_MAJOR = frozenset({0x200B, 0x200C, 0x200D, 0x2060, 0xFEFF})
OTHER_INVISIBLE = frozenset({0x00AD, 0x034F, 0x115F, 0x1160, 0x17B4, 0x17B5})
HOMOGLYPH_SCRIPTS = frozenset({"Cyrillic", "Greek", "Armenian", "Cherokee"})
```

## Tiered severity, not a single verdict

A binary pass/fail gate forces a bad choice: either it's too loud (every zero-width space halts the build) or too quiet (you skip the ambiguous cases and miss the homoglyph in an install line). Three tiers resolve the tension.

**BLOCKER** — tag characters and bidi controls. These fail CI by default. There is no benign use, so there is no false-positive cost to refusing them outright.

**MAJOR** — zero-width and format characters (U+200B, U+200C, U+200D, U+2060, U+FEFF) anywhere they don't belong, plus other invisibles like soft hyphen (U+00AD), combining grapheme joiner (U+034F), Hangul fillers, and Khmer zero-width vowels. These *can* be attacks, but they also show up in legitimate-if-messy authoring. So they warn by default and only fail under `--strict`.

**MINOR** — mixed-script identifiers, but scoped hard. The homoglyph pass fires only inside URLs, package-manager install lines, and code-fence language tags. Never on prose.

That scoping is a deliberate design call. The line patterns the homoglyph pass inspects: `https?://`, `npm`/`pnpm`/`yarn`/`bun install`, `pip`/`uv install`, `cargo install`/`add`, `brew`/`gem`/`composer`/`go install`, and `gh repo clone`. Those are the lines a reader copies and runs. Prose is left alone because flagging every Greek letter in a math explanation would bury the one finding that matters.

### Severity tiers at a glance

| Tier | Character class | Examples | Action | False-positive cost |
|------|-----------------|----------|--------|---------------------|
| **BLOCKER** | Tag chars, bidi controls | U+E0000–U+E007F, U+202A–U+202E | Fail CI immediately | None — no legitimate use |
| **MAJOR** | Zero-width / format chars | U+200B, U+FEFF (non-BOM), U+00AD | Warn by default; fail under `--strict` | Possible in legitimate authoring |
| **MINOR** | Mixed-script identifiers | Cyrillic `а`, Greek `α` in URLs / install lines | Warn in narrow contexts only | Low — scoped to package lines |

### The BOM exception

One codepoint sits on a fence. U+FEFF is a byte-order mark when it's the very first byte of a file — legitimate. The same codepoint anywhere else is a zero-width no-break space, which is exactly the kind of invisible an attacker reaches for. So the rule grants a pass to exactly one position and flags every other occurrence:

```python
elif cp in ZERO_WIDTH_MAJOR:
    # A single U+FEFF at the very first byte of the file is a
    # legitimate BOM and gets a pass.
    if cp == 0xFEFF and line_no == 1 and col_idx == 1:
        continue
    findings.append(Finding(severity="MAJOR", ..., rule="zero-width-or-format", ...))
```

Position-aware, not codepoint-aware. The byte is fine at offset 0 and suspect everywhere else.

## Make the invisible visible in the log

A finding that says "MAJOR at line 14, column 22" is useless if the reviewer opens the file and sees nothing there — because the offending character is, by definition, invisible. Every finding carries `file:line:column`, the codepoint's `unicodedata.name()` label, the rule name, and a ~32-character context window with every invisible escaped to `<U+XXXX>`:

```python
def _escape_context(line, column, width=32):
    ...
    for ch in window:
        cp = ord(ch)
        if cp in TAG_CHARS or cp in BIDI_CONTROLS or cp in ZERO_WIDTH_MAJOR \
           or cp in OTHER_INVISIBLE or cp < 0x20:
            out_chars.append(f"<U+{cp:04X}>")
        else:
            out_chars.append(ch)
    return "".join(out_chars)
```

Now the CI log shows `npm install p<U+0430>ckage` instead of a line that looks identical to the clean one. The reviewer can actually see the attack.

## Ship report-only, then ratchet

The gate has two rollout switches. `--warn-only` always exits 0 — it reports findings without failing the build, for the window where you're still learning what's in the corpus. `--strict` flips MAJOR findings into build failures once you've cleaned up the known-benign noise.

This is the same self-expiring report-only pattern we use elsewhere: land a gate in advisory mode, let it observe production traffic, then enforce once you've proven it won't false-positive your own contributors into a wall. BLOCKER fires from day one because it has no false-positive cost; MAJOR waits behind `--strict` until the corpus is clean.

## The result

Wired into `.github/workflows/validate-plugins.yml` next to the existing schema validator. Scanned 4,776 files.

Zero blockers. Clean main.

Eight MAJOR findings — and the honest detail is the interesting one. All eight traced to a single community-contributed file that intentionally used a zero-width space inside a fenced code block as a rendering workaround. Not an attack. A legitimate-but-messy authoring choice. That is precisely why MAJOR sits behind `--strict` and isn't flipped on yet: the ratchet waits until that one file is cleaned up, so the first enforced run doesn't punish a contributor for a cosmetic hack.

Tests cover the boundaries with six byte-precise fixtures — `blocker-tag-chars`, `blocker-bidi-override`, `bom-allowed`, `clean-skill`, `major-zero-width`, `minor-homoglyph-install` — driving an 8-test regression suite in `tests/test_validate_unicode_hygiene.py`. The whole thing shipped as PR #777 closing #776: ~317 lines of validator, one workflow edit, one test file.

## Also shipped

Same day, part of a wider CI-hardening campaign:

- An after-action review (PR #775) closed a 2026-05-22→24 hardening sequence: 11 PRs landing v4.32.0 with 10 blocking required gates and zero report-only, plus cleanup of 974 Python errors, 223 shellcheck warnings, ~60k markdown issues, and 970 MB freed.
- Doc-quality gate "round 2" in two other repos (`intentional-cognition-os`, `qmd-team-intent-kb`): fixed Vale by scoping via per-directory `.vale.ini` sections instead of the action's broken single-path `files:` input, and lychee by passing `.` as the required positional argument. Scoping refinements, not policy loosening — the gates stay BLOCKING.
- `intentional-cognition-os` also got an `ico audit verify` SHA-256 chain verifier. The audit log had carried a tamper-evident hash chain since launch, but nothing actually walked it — so the tamper-evidence was theoretical. Now `ico audit verify` exits 2 on `AUDIT_TAMPERED`.

## Related posts

- [Self-Expiring Report-Only CI Gates](/blog/self-expiring-report-only-ci-gates/) — the `--warn-only` → `--strict` ratchet is the same advisory-to-enforced pattern, generalized.
- [Safety Model First: 16-Tool Ops MCP in One Day](/blog/server-ops-mcp-safety-before-tools/) — designing the threat model before the surface, applied to an ops MCP server.

<script type="application/ld+json">
{
  "@context": "https://schema.org",
  "@type": "BlogPosting",
  "headline": "The Unicode Layer Your Validator Can't See",
  "description": "Schema validation can't see invisible Unicode. A stdlib-only CI gate that catches tag-char injection, Trojan Source bidi overrides, and homoglyph attacks.",
  "image": "https://startaitools.com/images/og-image.png",
  "datePublished": "2026-05-24",
  "author": {
    "@type": "Person",
    "name": "Jeremy Longshore"
  },
  "publisher": {
    "@type": "Organization",
    "name": "Start AI Tools"
  },
  "url": "https://startaitools.com/posts/unicode-hygiene-gate-same-day-trapdoor-defense/"
}
</script>
