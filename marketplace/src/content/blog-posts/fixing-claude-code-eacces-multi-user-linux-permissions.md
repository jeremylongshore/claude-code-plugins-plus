---
title: "Fixing Claude Code EACCES: Multi-User Linux Permission Architecture"
description: "Deep dive into debugging and fixing Claude Code EACCES permission errors in a multi-user Linux environment. Learn how to implement shared configuration with symlinks, group permissions, and proper ownership."
date: "2025-10-23"
tags: ["claude-code", "linux", "permissions", "multi-user", "debugging", "troubleshooting"]
featured: false
---
When you're running Claude Code across multiple Linux user accounts and hit `EACCES: permission denied`, the solution isn't just `chmod 777`. This is the complete troubleshooting journey from error to production-ready multi-user architecture.

## The Problem: Two Users, One Claude Code Instance

**Initial symptom:** User `jeremy` couldn't start Claude Code:

```
EACCES: permission denied, open
syscall: "open",
  errno: -13,
   code: "EACCES"
```

**Context:**

- Two user accounts: `jeremy` (master) and `admincostplus` (admin)
- Both need to run Claude Code independently
- Shared configuration desired (plugins, MCP servers, slash commands)
- No permission conflicts or ownership battles

The naive approach? "Just give both users access." The correct approach? Architect a system that scales.

## Phase 1: Understanding the Problem (What We Discovered)

### Investigation Started with Basic Checks

```bash
# Check current user and home
whoami  # admincostplus
ls -la ~/.claude  # Owned by admincostplus, 700 permissions

# Try to identify what's failing
claude --dangerously-skip-permissions
# Still fails with EACCES on file open
```

**Key discovery:** The error wasn't about running Claude Code—it was about Claude Code trying to write logs and configuration files to directories it couldn't access.

### The Ownership Mess We Found

```bash
# Jeremy's directory had files owned by the wrong user
ls -la /home/jeremy/.claude/debug/
drwx------ 2 admincostplus admincostplus 12288 Oct 23 14:21 debug

# This meant:
# - admincostplus had created files in jeremy's home directory earlier
# - jeremy (the owner) couldn't write to his own .claude/debug directory
# - Claude Code failed when trying to append to log files
```

**Why this happened:** Earlier troubleshooting attempts ran Claude Code as `admincostplus`, which created directories and files in shared locations with the wrong ownership.

## Phase 2: The Architecture (What Actually Works)

The solution uses **three layers of Linux permissions magic:**

1. **Shared directory with setgid bit** - All files inherit group ownership
2. **Symlinks for admin user** - Transparent redirection to shared location
3. **Real directories for master user** - Jeremy keeps his own independent copy

### The Complete Script

Here's the production script. Run it as root or with `sudo`:

```bash
#!/bin/bash
# Multi-user Claude Code configuration
# Run as: sudo bash this-script.sh

# Variables
MASTER_USER=jeremy
ADMIN_USER=admincostplus
SHARED=/opt/claude-shared
GROUP=claudeusers
MASTER_HOME=$(getent passwd "$MASTER_USER" | cut -d: -f6)
ADMIN_HOME=$(getent passwd "$ADMIN_USER" | cut -d: -f6)
DIRS=(".claude" ".claude-code" ".config/claude-code" ".local/share/claude-code")

# 1) Create group and add both users
getent group "$GROUP" >/dev/null || groupadd "$GROUP"
usermod -a -G "$GROUP" "$MASTER_USER"
usermod -a -G "$GROUP" "$ADMIN_USER"

# 2) Create shared directory and seed from master user
mkdir -p "$SHARED"
chown -R "$MASTER_USER:$GROUP" "$SHARED"
chmod 2775 "$SHARED"  # setgid bit ensures group inheritance

for rel in "${DIRS[@]}"; do
  src="$MASTER_HOME/$rel"
  dst="$SHARED/$rel"
  mkdir -p "$(dirname "$dst")"

  if [ -d "$src" ]; then
    rsync -a --delete "$src"/ "$dst"/
  else
    mkdir -p "$dst"
  fi
done

# 3) Replace admin's real directories with symlinks
for rel in "${DIRS[@]}"; do
  link="$ADMIN_HOME/$rel"
  target="$SHARED/$rel"

  # Backup existing directory if it's not already a symlink
  [ -e "$link" ] && [ ! -L "$link" ] && \
    mv "$link" "$link.bak-$(date +%Y%m%d-%H%M%S)"

  mkdir -p "$(dirname "$link")"
  rm -rf "$link"
  ln -s "$target" "$link"
done

# 4) Set group permissions with setgid on all directories
chown -R "$MASTER_USER:$GROUP" "$SHARED"
chmod -R g+rX "$SHARED"
find "$SHARED" -type d -exec chmod 2775 {} +

# 5) Optional: Set ACLs for belt-and-suspenders approach
command -v setfacl >/dev/null && \
  setfacl -R -m g:$GROUP:rwx -m d:g:$GROUP:rwx "$SHARED" || true

# 6) Environment variable for admin user only
cat >/etc/profile.d/claude-code-admin.sh <<'EOF'
[ "$USER" = "admincostplus" ] && export CLAUDE_CODE_HOME="/opt/claude-shared/.claude-code"
EOF
chmod 644 /etc/profile.d/claude-code-admin.sh

# 7) Kill any stale processes
pkill -f 'claude|node .*claude' || true

echo "✅ Multi-user Claude Code setup complete"
echo "   Master user: $MASTER_USER (uses real directories)"
echo "   Admin user: $ADMIN_USER (uses symlinks to shared)"
```

### Why This Architecture Works

**For `admincostplus` (admin user):**

- Symlinks redirect all Claude Code file operations to `/opt/claude-shared`
- Writes go to shared location where group permissions grant access
- Transparent to Claude Code—it doesn't know it's writing to shared storage

**For `jeremy` (master user):**

- Uses real directories at `/home/jeremy/.claude`
- Full ownership and control
- Changes sync to shared directory (manual rsync when needed)

**The setgid bit (2775):**

```bash
chmod 2775 /opt/claude-shared
# The '2' is the setgid bit
# Effect: All new files/directories inherit the group 'claudeusers'
# Result: No ownership conflicts when both users write
```

## Phase 3: The Critical Bug We Hit

After running the script, Jeremy **still got EACCES errors**. Why?

### Debugging the "It Should Work But Doesn't" Moment

```bash
# Check symlinks - ✅ Correct
ls -la /home/admincostplus/.claude
lrwxrwxrwx 1 root root 26 Oct 23 14:33 .claude -> /opt/claude-shared/.claude

# Check group membership - ✅ Correct
id jeremy
groups=1001(admincostplus),27(sudo),1000(jeremy),1002(claudeusers)

# Check permissions on shared - ✅ Correct
ls -ld /opt/claude-shared/.claude
drwxrwsr-x 13 jeremy claudeusers 4096 Oct 23 14:35 .

# Test write to shared - ✅ Works
sudo -iu admincostplus bash -lc 'touch ~/.claude/debug/test.txt'
# Success!
```

Everything looked perfect. So why did Claude Code still fail for Jeremy?

### The Real Problem: Ownership Pollution

```bash
# Check Jeremy's actual .claude directory
ls -la /home/jeremy/.claude/debug/
drwx------ 2 admincostplus admincostplus 12288 Oct 23 14:21 debug

# ❌ Jeremy's own directory was owned by admincostplus!
# Jeremy couldn't write to his own home directory
```

**Root cause:** During earlier troubleshooting, `admincostplus` had run commands that created files in Jeremy's home directory. Those files retained `admincostplus` ownership.

### The Fix

```bash
# Reclaim ownership of Jeremy's directories
sudo chown -R jeremy:jeremy /home/jeremy/.claude
sudo chown -R jeremy:jeremy /home/jeremy/.claude-code
sudo chown -R jeremy:jeremy /home/jeremy/.config/claude
sudo chown -R jeremy:jeremy /home/jeremy/.local/share/claude-code

# Fix permissions
sudo chmod 755 /home/jeremy/.claude
```

**Critical lesson:** In multi-user debugging, always check ownership of the actual directories, not just the symlinks and shared locations.

## Phase 4: The Environment Variable Bug

After fixing ownership, we found the `CLAUDE_CODE_HOME` environment variable wasn't being set.

### The Escaping Issue

```bash
# What the script wrote (WRONG):
cat /etc/profile.d/claude-code-admin.sh
[ "\$USER" = "admincostplus" ] && export CLAUDE_CODE_HOME="/opt/claude-shared/.claude-code"
#  ^^^ Escaped dollar sign prevents variable expansion

# Testing confirmed it didn't work:
sudo -iu admincostplus bash -lc 'echo $CLAUDE_CODE_HOME'
# (empty output)
```

### The Fix

```bash
# Use double quotes with escaped backslash for heredoc
cat >/etc/profile.d/claude-code-admin.sh <<'EOF'
[ "$USER" = "admincostplus" ] && export CLAUDE_CODE_HOME="/opt/claude-shared/.claude-code"
EOF

# Or use echo with proper escaping:
echo '[ "$USER" = "admincostplus" ] && export CLAUDE_CODE_HOME="/opt/claude-shared/.claude-code"' \
  | sudo tee /etc/profile.d/claude-code-admin.sh

# Verify it works:
sudo -iu admincostplus bash -lc 'echo $CLAUDE_CODE_HOME'
/opt/claude-shared/.claude-code  # ✅ Success
```

## Phase 5: Verification (How to Know It Actually Works)

### Comprehensive Smoke Tests

```bash
# Test 1: Verify symlinks resolve correctly
sudo -iu admincostplus bash -lc 'readlink -f ~/.claude'
/opt/claude-shared/.claude  # ✅

# Test 2: Verify Jeremy uses real directories
sudo -iu jeremy bash -lc 'readlink -f ~/.claude || echo "Real directory"'
/home/jeremy/.claude  # ✅

# Test 3: Write permissions for admincostplus
sudo -iu admincostplus bash -lc 'touch ~/.claude/test.txt && rm ~/.claude/test.txt'
# ✅ Success

# Test 4: Write permissions for jeremy
sudo -iu jeremy bash -lc 'touch ~/.claude/test.txt && rm ~/.claude/test.txt'
# ✅ Success

# Test 5: Claude Code runs for both users
sudo -iu jeremy bash -lc 'claude --version'
2.0.25 (Claude Code)  # ✅

sudo -iu admincostplus bash -lc 'claude --version'
2.0.8 (Claude Code)  # ✅

# Test 6: Environment variable is set
sudo -iu admincostplus bash -lc 'echo $CLAUDE_CODE_HOME'
/opt/claude-shared/.claude-code  # ✅
```

### What Success Looks Like

**For `admincostplus`:**

```bash
$ whoami
admincostplus

$ ls -la ~/.claude
lrwxrwxrwx 1 root root 26 Oct 23 14:33 .claude -> /opt/claude-shared/.claude

$ claude --version
2.0.8 (Claude Code)

$ echo $CLAUDE_CODE_HOME
/opt/claude-shared/.claude-code
```

**For `jeremy`:**

```bash
$ whoami
jeremy

$ ls -la ~/.claude
drwxr-xr-x 13 jeremy jeremy 4096 Oct 23 14:35 .claude

$ claude --version
2.0.25 (Claude Code)

$ echo $CLAUDE_CODE_HOME
(empty - uses default ~/.claude-code)
```

## Key Lessons from This Debugging Journey

### 1. EACCES Doesn't Mean "Wrong Permissions"

It means "wrong ownership, wrong permissions, wrong user, wrong directory, or wrong architecture." You have to investigate systematically:

- Check file ownership: `ls -la`
- Check group membership: `id username`
- Check directory permissions: `stat -c "%U:%G %a" /path`
- Check what's failing: Read the actual system call in the error

### 2. The Setgid Bit Is Your Friend

```bash
chmod 2775 /opt/claude-shared
# This bit (2) makes all new files inherit the directory's group
# Without it, files created by different users have different groups
# With it, all files in the directory get the same group ownership
```

### 3. Symlinks Are Transparent Permission Redirects

When you symlink `~/.claude` → `/opt/claude-shared/.claude`:

- All file operations follow the symlink
- Permissions are checked at the **target** location
- The source link doesn't need special permissions (just read/traverse)

### 4. Test Each Layer Independently

Don't assume the script worked. Verify:

1. Group exists and users are members: `getent group claudeusers`
2. Shared directory has correct ownership: `ls -ld /opt/claude-shared`
3. Symlinks point to correct targets: `readlink -f ~/.claude`
4. Both users can write: `touch ~/.claude/test.txt`
5. Environment variables are set: `echo $CLAUDE_CODE_HOME`
6. Application runs: `claude --version`

### 5. Ownership Pollution Is Silent and Deadly

During debugging, running commands as different users can leave landmines:

```bash
# This creates files owned by admincostplus in jeremy's home
sudo -u admincostplus touch /home/jeremy/.claude/test.txt

# Later, jeremy can't delete or modify them
# The solution: Always clean up after debugging
sudo chown -R jeremy:jeremy /home/jeremy/
```

## Production Checklist

Before deploying this architecture:

- [ ] Backup existing `.claude` directories for both users
- [ ] Create the `claudeusers` group and add members
- [ ] Test write access with `touch` commands before running Claude Code
- [ ] Verify symlinks are correct with `readlink -f`
- [ ] Check environment variables are set with `echo $VAR`
- [ ] Kill existing Claude Code processes before testing
- [ ] Test Claude Code runs successfully for both users
- [ ] Document which user is "master" (owns shared directory)
- [ ] Set up a sync script if master user makes changes
- [ ] Add monitoring for permission drift over time

## Related Reading

- [Intent Solutions Portfolio 2025: Production Deployment Velocity](https://startaitools.com/posts/intent-solutions-portfolio-2025-production-deployment-velocity/) - Multi-platform production architecture patterns
- [Linux File Permissions Deep Dive](https://www.linux.com/training-tutorials/understanding-linux-file-permissions/) - Understanding chmod, chown, and permission bits
- [Setgid Bit Explained](https://linuxconfig.org/how-to-use-special-permissions-the-setuid-setgid-and-sticky-bits) - Why the '2' in 2775 matters

## The Result

Two users, zero permission conflicts, shared configuration, independent Claude Code instances. This pattern scales to any number of users—just add them to the `claudeusers` group and create symlinks.

**Before:** EACCES errors, manual permission fixes, confusion about ownership.

**After:** Transparent multi-user access, automatic group inheritance, architectural clarity.

The difference between "just make it work" and "make it work correctly" is architecture. This is the latter.
