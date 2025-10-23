# 🐙 Fix GitHub CLI (gh auth login) Browser Issue

**Problem:** `gh auth login` opens terminal browser (lynx/w3m) instead of GUI browser
**Solution:** Configure gh to use Chromium
**Time:** 10 seconds

---

## ⚡ One-Line Fix

```bash
sudo bash /tmp/fix-gh-browser.sh
```

**Then reload your shell:**
```bash
source ~/.bashrc
```

**Now test:**
```bash
gh auth login
```

✅ Should now open **Chromium** (GUI browser), not terminal browser!

---

## 🔍 What This Fixes

### Before Fix
```bash
$ gh auth login
# Press Enter to authorize...
# ❌ Opens lynx or w3m (terminal browser)
```

### After Fix
```bash
$ gh auth login
# Press Enter to authorize...
# ✅ Opens Chromium (GUI browser)
```

---

## 🔧 What Gets Configured

### 1. GitHub CLI Config File
**Location:** `~/.config/gh/config.yml`

```yaml
# GitHub CLI Configuration
browser: chromium
git_protocol: https
editor: nano
pager: less
prompt: enabled
```

### 2. Environment Variables
**Added to:** `~/.bashrc`

```bash
export GH_BROWSER="chromium"
export BROWSER="chromium"
```

---

## 🧪 Test It Works

### Step 1: Reload Shell
```bash
source ~/.bashrc
```

### Step 2: Check Configuration
```bash
# Check environment
echo $GH_BROWSER
# Expected: chromium

echo $BROWSER
# Expected: chromium

# Check gh config
cat ~/.config/gh/config.yml | grep browser
# Expected: browser: chromium
```

### Step 3: Test Authentication
```bash
gh auth login
```

Select options:
1. GitHub.com
2. HTTPS
3. Login with a web browser
4. **Press Enter** ← This should now open Chromium!

---

## 📋 Manual Configuration (If Script Fails)

### 1. Create gh config directory
```bash
mkdir -p ~/.config/gh
```

### 2. Create config file
```bash
nano ~/.config/gh/config.yml
```

Add:
```yaml
browser: chromium
git_protocol: https
```

### 3. Add to ~/.bashrc
```bash
echo 'export GH_BROWSER="chromium"' >> ~/.bashrc
echo 'export BROWSER="chromium"' >> ~/.bashrc
```

### 4. Reload
```bash
source ~/.bashrc
```

---

## 🚨 Troubleshooting

### Still Opening Terminal Browser?

**Check gh config:**
```bash
cat ~/.config/gh/config.yml
```

**Manually set browser:**
```bash
gh config set browser chromium
```

**Check environment:**
```bash
echo $GH_BROWSER
echo $BROWSER
```

If empty, reload:
```bash
source ~/.bashrc
```

### "chromium: command not found"

Install Chromium:
```bash
sudo snap install chromium
```

Or use Firefox:
```bash
# Edit config
nano ~/.config/gh/config.yml
# Change: browser: firefox

# Update environment
export GH_BROWSER="firefox"
export BROWSER="firefox"
```

### "Permission denied on config file"

Fix ownership:
```bash
sudo chown -R admincostplus:admincostplus ~/.config/gh
chmod 644 ~/.config/gh/config.yml
```

---

## 🎯 Complete Browser Fix (All Tools)

To fix browser issues for **all tools** (gh, xdg-open, terminal clicks):

```bash
# Run all fixes
sudo bash /tmp/fix-gh-browser.sh
sudo bash /tmp/fix-terminal-url-handler.sh

# Reload shell
source ~/.bashrc

# Close and reopen terminal for full effect
```

Now:
- ✅ `gh auth login` opens Chromium
- ✅ Ctrl+Click URLs opens Chromium
- ✅ `xdg-open` uses Chromium
- ✅ All browser commands use GUI browser

---

## 📊 Summary

```
┌──────────────────────────────────────────┐
│ GitHub CLI Browser Fix                   │
├──────────────────────────────────────────┤
│ Tool:           gh (GitHub CLI)          │
│ Browser:        Chromium (GUI)           │
│ Config:         ~/.config/gh/config.yml  │
│ Env vars:       GH_BROWSER, BROWSER      │
│ Status:         ✅ Ready to apply         │
└──────────────────────────────────────────┘
```

---

## ✅ Quick Test Checklist

After running the fix:

```bash
# 1. Reload shell
source ~/.bashrc

# 2. Verify config
cat ~/.config/gh/config.yml | grep browser

# 3. Verify environment
echo $GH_BROWSER

# 4. Test gh auth
gh auth status
# If not logged in, run:
gh auth login
# Should open Chromium when you press Enter!
```

**No more terminal browser for gh auth!** 🎉
