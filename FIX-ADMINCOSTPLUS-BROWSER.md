# 🌐 Fix admincostplus Default Browser

**Problem:** Terminal browser opening instead of GUI browser, Ctrl+Click not working
**Solution:** Configure Chromium as default + fix terminal URL handler
**Time:** ~30 seconds

---

## ⚡ Quick Fix for Ctrl+Click URLs (RECOMMENDED)

```bash
sudo bash /tmp/fix-terminal-url-handler.sh
```

This will:
- ✅ Set Chromium as default browser
- ✅ Configure xdg-open to use Chromium
- ✅ Fix terminal Ctrl+Click URL handler
- ✅ Configure GNOME terminal settings
- ✅ Set environment variables

**After running, close and reopen your terminal, then Ctrl+Click should work!**

---

## 🔧 Alternative: Basic Browser Fix Only

```bash
sudo bash /tmp/fix-admincostplus-browser.sh
```

This will:
- ✅ Set Chromium as default browser
- ✅ Configure BROWSER environment variable
- ✅ Set xdg-open to use Chromium
- ✅ Override terminal browser aliases

---

## 🔧 What It Configures

### 1. Environment Variables (in ~/.bashrc)
```bash
export BROWSER="chromium"
export CHROME_EXECUTABLE="chromium"
```

### 2. xdg-open Settings (in ~/.config/mimeapps.list)
```ini
[Default Applications]
text/html=chromium.desktop
x-scheme-handler/http=chromium.desktop
x-scheme-handler/https=chromium.desktop
```

### 3. Terminal Browser Overrides
```bash
alias lynx="chromium"
alias w3m="chromium"
alias links="chromium"
```

---

## ✅ Apply Changes

After running the script:

```bash
# Switch to admincostplus
sudo su - admincostplus

# Reload configuration
source ~/.bashrc

# Test it works
xdg-open https://google.com
# Should open Chromium, not terminal browser!
```

---

## 🧪 Test Commands

```bash
# Test 1: Environment variable
echo $BROWSER
# Expected: chromium

# Test 2: Open URL with xdg-open
xdg-open https://claude.ai

# Test 3: Open URL with $BROWSER
$BROWSER https://google.com

# Test 4: Direct chromium command
chromium https://github.com
```

All should open **Chromium GUI browser**, not terminal browser!

---

## 🔍 If Still Opening Terminal Browser

### Check Current Default
```bash
sudo su - admincostplus
xdg-settings get default-web-browser
```

### Force Set Chromium
```bash
xdg-settings set default-web-browser chromium.desktop
```

### Check BROWSER Variable
```bash
echo $BROWSER
# Should show: chromium
```

If it's empty or shows something else:
```bash
export BROWSER="chromium"
```

---

## 📋 Manual Configuration (If Script Fails)

### 1. Edit ~/.bashrc
```bash
sudo nano /home/admincostplus/.bashrc
```

Add at the end:
```bash
# Default browser
export BROWSER="chromium"
export CHROME_EXECUTABLE="chromium"
```

### 2. Create mimeapps.list
```bash
sudo mkdir -p /home/admincostplus/.config
sudo nano /home/admincostplus/.config/mimeapps.list
```

Add:
```ini
[Default Applications]
text/html=chromium.desktop
x-scheme-handler/http=chromium.desktop
x-scheme-handler/https=chromium.desktop
```

### 3. Set Ownership
```bash
sudo chown -R admincostplus:admincostplus /home/admincostplus/.bashrc
sudo chown -R admincostplus:admincostplus /home/admincostplus/.config
```

### 4. Reload
```bash
sudo su - admincostplus
source ~/.bashrc
```

---

## 🚨 Troubleshooting

### "Chromium not found"
Install it:
```bash
sudo snap install chromium
# OR
sudo apt install chromium-browser
```

### "Still opens lynx/w3m"
Check what's calling it:
```bash
type -a xdg-open
which lynx w3m links
```

Temporarily rename terminal browsers:
```bash
sudo mv /usr/bin/lynx /usr/bin/lynx.bak
sudo mv /usr/bin/w3m /usr/bin/w3m.bak
```

### "Browser opens but then terminal browser also opens"
You might have wrapper scripts. Check:
```bash
cat $(which xdg-open)
```

---

## 📊 Summary

```
┌──────────────────────────────────────────┐
│ Browser Fix: admincostplus User          │
├──────────────────────────────────────────┤
│ Default Browser:  Chromium (GUI)         │
│ Method:          Environment vars        │
│ Config File:     ~/.bashrc               │
│ xdg-open:        chromium.desktop        │
│ Status:          ✅ Ready to apply        │
└──────────────────────────────────────────┘
```

---

## 🎯 One-Line Solution

```bash
sudo bash /tmp/fix-admincostplus-browser.sh && sudo su - admincostplus -c "source ~/.bashrc && xdg-open https://google.com"
```

This will:
1. Configure Chromium as default
2. Switch to admincostplus user
3. Reload configuration
4. Test by opening Google in Chromium

**No more terminal browsers!** 🎉

---

**Browser detected on your system:** `/snap/bin/chromium` ✅
