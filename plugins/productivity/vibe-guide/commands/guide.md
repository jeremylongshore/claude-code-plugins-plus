---
name: guide
description: Show how to use vibe-guide with examples
allowed-tools: Read
---

# /vibe-guide:guide

Display usage guide for the vibe-guide plugin.

## Usage

```
/vibe-guide:guide
```

## Examples

```
/vibe-guide:guide
```

Shows the quick start guide below.

## Output

When this command runs, display the following:

---

# Vibe Guide - Quick Start

## Starting a Session

```
/vibe-guide:vibe Build a contact form
```

This creates a `.vibe/` folder and starts working on your goal.

---

## Check Progress Anytime

```
/vibe-guide:status
```

See where you are without doing more work.

---

## Keep Going Step by Step

```
/vibe-guide:continue
```

Runs ONE step, then shows what happened in plain language.

---

## Take a Break

```
/vibe-guide:stop
```

Pauses the session. Run again to resume.

---

## Learning Mode (Optional)

```
/vibe-guide:learn on
```

Adds mini-lessons after each step. Great for understanding what's happening!

```
/vibe-guide:learn off
```

Turns lessons off.

---

## More Details (Optional)

```
/vibe-guide:details on
```

Shows slightly more technical info (still no raw diffs).

```
/vibe-guide:details off
```

Back to simple mode.

---

## Example Workflow

```
> /vibe-guide:vibe Add dark mode to settings

1) Where we are
   Starting: adding dark mode to settings.

2) What changed
   - Set up session tracking
   - Found the Settings page

3) What's next
   Add the toggle switch.

5) Do you need to do anything?
   No, nothing needed right now.

> /vibe-guide:continue

1) Where we are
   Added the toggle switch.

2) What changed
   - Created toggle component
   - Added to settings page

3) What's next
   Add dark theme styles.

5) Do you need to do anything?
   No, nothing needed right now.

> /vibe-guide:continue

...and so on until done!
```

---

## If Something Goes Wrong

You'll see a friendly checklist:

```
Something went wrong, but it's fixable.

What happened: Database connection failed.

To fix this:
1. Check if database is running
2. Verify .env settings
3. Run /vibe-guide:status after fixing
```

---

## Files Created

Vibe Guide creates a `.vibe/` folder in your project:
- `session.json` - Your goal and settings
- `status.json` - Current progress
- `changelog.md` - Log of all steps

This folder is auto-added to `.gitignore`.

---
