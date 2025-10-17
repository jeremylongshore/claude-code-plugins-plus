# Quick Deploy Guide - claudecodeplugins.io

**Last Updated:** 2025-10-16
**Time to Deploy:** 3-5 minutes (after initial setup)

---

## 🚀 Deploy Now (3 Steps)

### Step 1: Commit Workflow Fix
```bash
cd /home/jeremy/000-projects/claude-code-plugins
git add .github/workflows/deploy-marketplace.yml
git add DEPLOYMENT_CHECKLIST.md
git add marketplace/DEPLOYMENT_*.md
git add marketplace/QUICK_DEPLOY_GUIDE.md
git commit -m "fix: update GitHub Actions workflow to use npm and add deployment docs"
git push origin main
```

### Step 2: Enable GitHub Pages
1. Visit: https://github.com/jeremylongshore/claude-code-plugins/settings/pages
2. Source: **GitHub Actions**
3. Custom domain: `claudecodeplugins.io`
4. Enable: **Enforce HTTPS**
5. Click **Save**

### Step 3: Configure DNS (at domain registrar)
Add these 4 A records:
```
Type: A    Name: @    Value: 185.199.108.153
Type: A    Name: @    Value: 185.199.109.153
Type: A    Name: @    Value: 185.199.110.153
Type: A    Name: @    Value: 185.199.111.153
```

**Done!** Site will be live in 24-48 hours (DNS propagation time)

---

## ✅ Verify Deployment

```bash
# Check if site is live
curl -I https://claudecodeplugins.io

# Check DNS
dig claudecodeplugins.io A +short

# View GitHub Actions
# Visit: https://github.com/jeremylongshore/claude-code-plugins/actions
```

---

## 📝 Quick Reference

### Local Commands
```bash
cd /home/jeremy/000-projects/claude-code-plugins/marketplace
npm run dev      # Start dev server
npm run build    # Build for production
npm run preview  # Preview build
```

### Deploy Commands
```bash
cd /home/jeremy/000-projects/claude-code-plugins
git add marketplace/
git commit -m "Update marketplace: [description]"
git push origin main  # Auto-deploys via GitHub Actions
```

### Verification
- **Site:** https://claudecodeplugins.io
- **Actions:** https://github.com/jeremylongshore/claude-code-plugins/actions
- **Settings:** https://github.com/jeremylongshore/claude-code-plugins/settings/pages

---

## 🆘 Quick Troubleshooting

### Site not updating?
```bash
# Clear cache: Ctrl+Shift+R (Windows/Linux) or Cmd+Shift+R (Mac)
# Check Actions: https://github.com/jeremylongshore/claude-code-plugins/actions
# Wait 5 minutes for CDN cache
```

### Build failing?
```bash
cd /home/jeremy/000-projects/claude-code-plugins/marketplace
npm run build  # Test locally first
# Fix errors, then commit and push
```

### DNS not working?
```bash
dig claudecodeplugins.io A +short
# Should show 4 GitHub Pages IPs
# Wait 24-48 hours for DNS propagation
# Check: https://www.whatsmydns.net/#A/claudecodeplugins.io
```

---

## 📚 Full Documentation

For detailed guides, see:
- **Comprehensive Checklist:** `/home/jeremy/000-projects/claude-code-plugins/DEPLOYMENT_CHECKLIST.md`
- **Deployment Status:** `/home/jeremy/000-projects/claude-code-plugins/marketplace/DEPLOYMENT_STATUS.md`
- **Deployment Summary:** `/home/jeremy/000-projects/claude-code-plugins/marketplace/DEPLOYMENT_SUMMARY.md`

---

## ⏱️ Timeline

- **Push to GitHub:** Instant
- **GitHub Actions Build:** 2-3 minutes
- **GitHub Pages Deploy:** 1-2 minutes
- **DNS Propagation (first time):** 24-48 hours
- **HTTPS Certificate:** 10-15 minutes (after DNS)

---

**Status:** ✅ Ready to deploy!
