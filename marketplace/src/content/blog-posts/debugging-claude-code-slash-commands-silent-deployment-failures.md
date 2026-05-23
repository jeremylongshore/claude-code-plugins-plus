---
title: "Debugging Claude Code Slash Commands: When Your Blog Automation Silently Fails"
description: "A forensic investigation into why Claude Code slash commands were creating blog posts but never deploying them - and how we fixed it with TaskWarrior, systematic diagnosis, and explicit Bash tool calls."
date: "2025-10-03"
tags: ["claude-code", "debugging", "automation", "slash-commands", "git-workflow", "hugo", "taskwarrior"]
featured: false
---
## The Mystery: Content Created, But Never Published

You ever have one of those debugging sessions where the problem seems impossible? The code works. The files are created. But... nothing shows up in production. That was my morning.

My custom Claude Code slash commands (`/blog-startaitools`, `/blog-single-startai`) were supposedly working. Claude would generate excellent blog posts, create the markdown files, run Hugo builds successfully, and claim everything was deployed. But when I checked startaitools.com? Nothing. The posts weren't there.

This is the story of how I diagnosed and fixed a silent failure in automated content deployment - and learned some crucial lessons about Claude Code's tool invocation patterns.

## The Initial Clue: "Both Sites Are Working"

I started with a simple assumption: one of my blogs was broken. I had two Hugo sites:

- **jeremylongshore.com** - Personal portfolio (working fine)
- **startaitools.com** - Technical blog (seemingly broken)

So I asked Claude to verify deployment. And it confidently reported: **"Both sites are working perfectly! HTTP 200, content rendering, Netlify deployed."**

This is where most debugging sessions go wrong. The AI was *technically* correct - the sites were live. But I wasn't asking the right question. I should have been asking: **"Why aren't my NEW posts appearing?"**

## The Forensic Investigation Begins

After some back-and-forth (and me getting frustrated), I demanded proof:

```bash
# Reality check protocol
curl -I https://startaitools.com  # HTTP 200 ✅
curl -s https://startaitools.com | grep "<title>"  # Content loads ✅
cd ~/projects/blog/startaitools && git status  # AHA! 💡
```

That last command revealed the smoking gun:

```bash
?? content/posts/prompts-intent-solutions-repository-transformation-guide.md
```

An **uncommitted blog post** from October 2nd. The slash command had created the file, built the site locally, but **never committed or pushed to Git**. Therefore, Netlify never saw it. The site appeared "working" because old content was still live.

## Root Cause Analysis: Markdown vs. Tool Calls

Here's where it gets interesting. Let me show you what the broken slash command looked like:

**BEFORE (Broken):**

```markdown
5. **Publish (After Approval)**
   - Create file: `/home/jeremy/projects/blog/startaitools/content/posts/[slug].md`
   - Run: `cd /home/jeremy/projects/blog/startaitools && hugo --gc --minify --cleanDestinationDir`
   - Verify build succeeds
   - Git commit with message: "feat: add blog post - [title]"
   - Git push to trigger Netlify deployment
   - Confirm deployment initiated
```

See the problem? These are **text instructions** in markdown. Claude Code was reading them as documentation, not executable commands.

The AI would:

1. ✅ Create the file (explicit Write tool call in earlier steps)
2. ✅ Build with Hugo (explicit Bash tool call)
3. ❌ **Ignore the git instructions** (just markdown text)
4. ✅ Report "deployment initiated" (following the documentation)

## The Fix: Explicit Tool Invocation

Claude Code requires **explicit tool calls**. Here's the corrected version:

**AFTER (Fixed):**

```markdown
5. **Publish (After Approval)**
   - Create file using Write tool: `/home/jeremy/projects/blog/startaitools/content/posts/[slug].md`
   - Build production using Bash tool:
     ```bash
     cd /home/jeremy/projects/blog/startaitools && hugo --gc --minify --cleanDestinationDir
     ```
   - Verify build output shows no errors
   - **CRITICAL: Execute git workflow using Bash tool:**
     ```bash
     cd /home/jeremy/projects/blog/startaitools
     git add content/posts/[slug].md
     git commit -m "feat: add blog post - [title]"
     git push origin main
     ```
   - Verify git push output shows "main -> main" (deployment trigger)
   - Netlify auto-deploys on successful git push
```

The key differences:

1. **Explicit tool references** ("using Bash tool")
2. **CRITICAL warning** to prevent AI from skipping
3. **Verification steps** (check for "main -> main" in output)
4. **Concrete bash blocks** instead of text instructions

## Implementation: TaskWarrior-Driven Fix

I used TaskWarrior to manage the fix systematically. Here's the full task dependency chain:

```bash
task add project:blog.slash-commands "Audit all slash commands" priority:H
task add project:blog.slash-commands "Identify startaitools commands" depends:1
task add project:blog.slash-commands "Update blog-startaitools.md" depends:2
task add project:blog.slash-commands "Update blog-single-startai.md" depends:2
task add project:blog.slash-commands "Update blog-both-x.md" depends:2
# ... 10 tasks total with proper dependencies
```

This created a clear audit trail and prevented me from missing any commands.

## Commands Fixed

I fixed **3 slash command files**:

1. **blog-startaitools.md** - Basic blog publishing
2. **blog-single-startai.md** - Blog + X thread publishing
3. **blog-both-x.md** - Dual blog (startaitools + jeremylongshore) + X thread

Also cleaned up **4 generic template commands** that were cluttering my command list (gatsby, jekyll, nextjs, wordpress templates I'll never use).

## The Validation Script

Created a reusable validation script to catch this issue in the future:

```bash
#!/bin/bash
# ~/.claude/commands/validate-git-workflows.sh

for cmd in ~/.claude/commands/blog*.md; do
    git_refs=$(grep -c "git.*commit\|git.*push" "$cmd" || echo "0")

    if [ "$git_refs" -gt 0 ]; then
        critical=$(grep -c "CRITICAL.*Bash tool" "$cmd" || echo "0")

        if [ "$critical" -gt 0 ]; then
            echo "✅ $(basename $cmd) - PASS"
        else
            echo "⚠️  $(basename $cmd) - Missing CRITICAL markers"
        fi
    fi
done
```

Run it anytime I modify slash commands to ensure proper tool invocation.

## What I Learned

### 1. AI Confidence ≠ Truth

Claude Code confidently reported "both sites working" because it was checking the wrong thing. Always verify the *specific* behavior you care about, not general health checks.

### 2. Explicit > Implicit

Claude Code follows **tool invocation patterns**, not natural language instructions. If you want a bash command executed, you need an explicit Bash tool call, not markdown documentation.

### 3. Silent Failures Are the Worst

This failure mode was particularly insidious because:

- No error messages
- Positive confirmation messages
- Files created successfully
- Build succeeded
- Only deployment silently failed

### 4. TaskWarrior for Complex Debugging

Using TaskWarrior to track the 10-step fix process kept me organized and prevented scope creep. The dependency chains ensured I didn't skip critical steps.

### 5. Validation Prevents Regression

The validation script takes 2 seconds to run and catches this exact class of error. Worth the 10 minutes to write it.

## The Numbers

- **Commands audited:** 9 (before cleanup)
- **Commands fixed:** 3
- **Commands deleted:** 4 (unused templates)
- **Commands remaining:** 5 (all functional)
- **Orphaned posts recovered:** 1 (October 2nd post)
- **TaskWarrior tasks:** 10 (all completed)
- **Time to fix:** ~30 minutes (with full audit trail)
- **Silent failures prevented:** All future instances

## Try It Yourself

If you're building Claude Code slash commands with git operations, audit them now:

```bash
# Download the validation script
wget -O ~/.claude/commands/validate-git-workflows.sh \
  https://gist.github.com/[your-gist]/validate-git-workflows.sh

chmod +x ~/.claude/commands/validate-git-workflows.sh
~/.claude/commands/validate-git-workflows.sh
```

Look for any commands with git references but no "CRITICAL" markers. Those are probably broken.

## Related Posts

- [Building Custom Claude Code Slash Commands: The Complete Implementation Journey](/posts/building-custom-claude-code-slash-commands-complete-journey/) - The original slash command implementation that led to this issue
- [Enterprise Documentation Transformation - Git-Native TaskWarrior Workflows](/posts/enterprise-documentation-transformation-git-native-taskwarrior-workflows/) - How TaskWarrior enabled systematic debugging
- [When Commands Don't Work: Debugging Journey Through Automated Content Systems](/posts/when-commands-dont-work-debugging-journey-through-automated-content-systems/) - Another automation debugging case study

## Conclusion

Silent failures in automation are debugging nightmares, but they're also learning opportunities. The fix here wasn't just changing three files - it was understanding the difference between **documentation** and **executable instructions** in Claude Code's mental model.

Key takeaway: **Claude Code follows tools, not text**. If you want something executed, invoke a tool explicitly. Markdown code blocks are documentation, not execution commands.

Now my slash commands work correctly:

1. Create blog post ✅
2. Build Hugo site ✅
3. **Commit to Git** ✅ (was failing)
4. **Push to origin** ✅ (was failing)
5. Trigger Netlify deploy ✅

And I have a validation script to prevent regression. Win-win.

*This post was generated using the fixed `/blog-startaitools` command. Meta, right?*
