# Deployment Checklist for claudecodeplugins.io

**Last Updated:** 2025-10-16
**Domain:** claudecodeplugins.io
**Repository:** jeremylongshore/claude-code-plugins
**Deployment Method:** GitHub Pages
**Build System:** Astro 5 + Tailwind CSS v4

---

## Pre-Deployment Checks

### 1. Local Build Verification
- [ ] Navigate to marketplace directory: `cd /home/jeremy/000-projects/claude-code-plugins/marketplace/`
- [ ] Install dependencies: `npm install`
- [ ] Run development server: `npm run dev` (verify at http://localhost:4321)
- [ ] Build for production: `npm run build`
- [ ] Preview production build: `npm run preview`
- [ ] Verify CNAME file exists in dist: `cat dist/CNAME` (should show "claudecodeplugins.io")
- [ ] Check dist/index.html has correct metadata and title
- [ ] Verify all assets are in `dist/_astro/` directory

### 2. Configuration Files Verification

#### astro.config.mjs
- [x] Site URL is `https://claudecodeplugins.io`
- [x] Base path is `/` (root domain)
- [x] Output mode is `static`
- [x] Build assets directory is `_astro`
- [x] HTML compression is enabled

#### CNAME File
- [x] Location: `marketplace/public/CNAME`
- [x] Content: `claudecodeplugins.io`
- [x] No trailing newline issues
- [x] File is copied to `dist/CNAME` during build

#### package.json
- [x] Scripts are defined: `dev`, `build`, `preview`
- [x] Dependencies are up to date
- [x] Version is 3.0.0

### 3. GitHub Actions Workflow Verification

#### File: `.github/workflows/deploy-marketplace.yml`
- [x] Triggers on push to main branch (paths: marketplace/**)
- [x] Manual trigger enabled (workflow_dispatch)
- [x] Permissions are correct (contents: read, pages: write, id-token: write)
- [x] Node version is 20
- [x] Uses npm (not pnpm) with `npm ci`
- [x] Builds from `./marketplace` directory
- [x] Uploads artifact from `./marketplace/dist`
- [x] Deploys to GitHub Pages

---

## GitHub Repository Setup

### 1. Enable GitHub Pages
1. Go to: https://github.com/jeremylongshore/claude-code-plugins/settings/pages
2. Under "Build and deployment":
   - Source: **GitHub Actions**
   - Branch: NOT used (GitHub Actions deployment)
3. Custom domain: `claudecodeplugins.io`
4. Enforce HTTPS: **Enabled**

### 2. Repository Settings
- [ ] Repository is public (required for GitHub Pages)
- [ ] Actions are enabled: Settings > Actions > General
- [ ] Workflow permissions: Settings > Actions > General > Workflow permissions
  - Set to: "Read and write permissions"
  - Enable: "Allow GitHub Actions to create and approve pull requests"

---

## DNS Configuration

### Domain Registrar: [Your Registrar Here]

**IMPORTANT:** DNS changes can take 24-48 hours to propagate fully.

### DNS Records to Configure

1. **A Records (for root domain)**
   ```
   Type: A
   Name: @
   Value: 185.199.108.153
   TTL: 3600

   Type: A
   Name: @
   Value: 185.199.109.153
   TTL: 3600

   Type: A
   Name: @
   Value: 185.199.110.153
   TTL: 3600

   Type: A
   Name: @
   Value: 185.199.111.153
   TTL: 3600
   ```

2. **CNAME Record (for www subdomain - optional)**
   ```
   Type: CNAME
   Name: www
   Value: jeremylongshore.github.io
   TTL: 3600
   ```

3. **CAA Record (optional but recommended for security)**
   ```
   Type: CAA
   Name: @
   Value: 0 issue "letsencrypt.org"
   TTL: 3600
   ```

### DNS Verification Commands
```bash
# Check A records
dig claudecodeplugins.io A +short

# Check CNAME
dig www.claudecodeplugins.io CNAME +short

# Full DNS lookup
nslookup claudecodeplugins.io

# Check SSL certificate
openssl s_client -connect claudecodeplugins.io:443 -servername claudecodeplugins.io < /dev/null
```

---

## Deployment Process

### Automatic Deployment (Recommended)
1. Make changes in `marketplace/` directory
2. Commit and push to main branch:
   ```bash
   cd /home/jeremy/000-projects/claude-code-plugins
   git add marketplace/
   git commit -m "Update marketplace: [description]"
   git push origin main
   ```
3. GitHub Actions will automatically:
   - Build the site with `npm run build`
   - Upload the dist/ artifact
   - Deploy to GitHub Pages
4. Monitor deployment:
   - https://github.com/jeremylongshore/claude-code-plugins/actions
5. Verify deployment at: https://claudecodeplugins.io

### Manual Deployment (if needed)
1. Navigate to: https://github.com/jeremylongshore/claude-code-plugins/actions/workflows/deploy-marketplace.yml
2. Click "Run workflow"
3. Select branch: `main`
4. Click "Run workflow" button
5. Monitor progress in Actions tab

---

## Post-Deployment Verification

### 1. Site Accessibility
- [ ] Visit https://claudecodeplugins.io
- [ ] Check HTTPS is working (green padlock in browser)
- [ ] Verify no mixed content warnings
- [ ] Test on multiple browsers (Chrome, Firefox, Safari, Edge)
- [ ] Test on mobile devices (responsive design)

### 2. Content Verification
- [ ] Homepage loads correctly
- [ ] All plugin cards display
- [ ] Search functionality works
- [ ] Category filters work
- [ ] Spotlight page loads: https://claudecodeplugins.io/spotlight
- [ ] All links work (no 404s)
- [ ] Images load correctly
- [ ] Favicon displays

### 3. SEO & Metadata
- [ ] Page title is correct: "Claude Code Plugins Marketplace - 227 Plugins"
- [ ] Meta description is present
- [ ] Open Graph tags are correct (check with https://www.opengraph.xyz/)
- [ ] Twitter card tags are correct
- [ ] Canonical URL is `https://claudecodeplugins.io/`

### 4. Performance
- [ ] Run Lighthouse audit (Chrome DevTools)
  - Target scores: Performance 90+, Accessibility 95+, Best Practices 95+, SEO 95+
- [ ] Check page load time < 3 seconds
- [ ] Verify assets are compressed
- [ ] Check CSS/JS minification

### 5. Analytics & Monitoring (Optional)
- [ ] Add Google Analytics or Plausible Analytics
- [ ] Set up uptime monitoring (UptimeRobot, Pingdom)
- [ ] Configure error tracking (Sentry)

---

## Troubleshooting

### Build Fails in GitHub Actions
1. Check Actions logs: https://github.com/jeremylongshore/claude-code-plugins/actions
2. Common issues:
   - Missing dependencies: Check `package.json` and `package-lock.json`
   - Node version mismatch: Verify Node 20 is used
   - Build errors: Run `npm run build` locally first
   - Working directory: Ensure `working-directory: ./marketplace` is set

### Site Not Updating
1. Check deployment status in Actions tab
2. Clear browser cache (Ctrl+Shift+R or Cmd+Shift+R)
3. Check GitHub Pages settings (custom domain configured)
4. Verify CNAME file in repository root (should NOT exist - only in marketplace/public/)
5. Wait 5-10 minutes for CDN cache to clear

### Custom Domain Not Working
1. Verify DNS records with `dig claudecodeplugins.io`
2. Check CNAME file exists in `marketplace/public/CNAME`
3. Verify CNAME file is in `dist/CNAME` after build
4. Re-save custom domain in GitHub Pages settings
5. Wait 24-48 hours for DNS propagation
6. Check for DNS configuration errors: https://www.whatsmydns.net/#A/claudecodeplugins.io

### HTTPS Not Working
1. Ensure "Enforce HTTPS" is enabled in GitHub Pages settings
2. Wait 10-15 minutes for certificate provisioning
3. Check certificate status: `openssl s_client -connect claudecodeplugins.io:443`
4. Clear browser cache
5. Try incognito/private browsing mode

### 404 Errors
1. Verify base path in `astro.config.mjs` is `/`
2. Check that `dist/` contains `index.html`
3. Verify GitHub Pages source is set to "GitHub Actions"
4. Clear GitHub Pages cache by re-saving custom domain

---

## Rollback Procedure

### If Deployment Fails or Site is Broken
1. **Quick Fix:** Revert to previous commit
   ```bash
   cd /home/jeremy/000-projects/claude-code-plugins
   git log marketplace/ --oneline -10  # Find last working commit
   git revert <commit-hash>
   git push origin main
   ```

2. **Emergency Rollback:** Re-deploy previous version
   ```bash
   git reset --hard <last-working-commit>
   git push --force origin main  # Use with caution!
   ```

3. **Local Testing Before Fix:**
   ```bash
   cd marketplace/
   npm run build
   npm run preview  # Test at http://localhost:4321
   ```

---

## Maintenance Tasks

### Regular Updates
- [ ] Update Astro: `npm update astro`
- [ ] Update Tailwind CSS: `npm update tailwindcss @tailwindcss/vite`
- [ ] Update all dependencies: `npm update`
- [ ] Test after updates: `npm run build && npm run preview`
- [ ] Update plugin count in metadata (currently 227)

### Monthly Checks
- [ ] Review GitHub Actions usage (free tier limits)
- [ ] Check domain expiration date
- [ ] Verify SSL certificate is auto-renewing
- [ ] Run security audit: `npm audit`
- [ ] Test on latest browsers

### Quarterly Reviews
- [ ] Review and update deployment documentation
- [ ] Check for Astro/Tailwind CSS major version updates
- [ ] Performance audit and optimization
- [ ] SEO review and updates

---

## Contact & Support

### Repository
- **GitHub Repo:** https://github.com/jeremylongshore/claude-code-plugins
- **Issues:** https://github.com/jeremylongshore/claude-code-plugins/issues

### Documentation
- **Astro Docs:** https://docs.astro.build
- **GitHub Pages Docs:** https://docs.github.com/en/pages
- **Tailwind CSS Docs:** https://tailwindcss.com/docs

### Deployment URLs
- **Production:** https://claudecodeplugins.io
- **GitHub Actions:** https://github.com/jeremylongshore/claude-code-plugins/actions
- **GitHub Pages Settings:** https://github.com/jeremylongshore/claude-code-plugins/settings/pages

---

## Summary of Current Status

### ✅ Configured Correctly
- [x] Astro config with correct site URL and base path
- [x] CNAME file in marketplace/public/CNAME
- [x] GitHub Actions workflow for deployment
- [x] Static output mode for GitHub Pages
- [x] Build process working locally
- [x] Metadata and SEO tags present

### ⚠️ Requires Action
- [ ] Verify GitHub Pages is enabled in repository settings
- [ ] Configure DNS records at domain registrar
- [ ] Test deployment workflow (push to main or manual trigger)
- [ ] Verify custom domain in GitHub Pages settings

### 📝 Next Steps
1. Enable GitHub Pages in repository settings (source: GitHub Actions)
2. Configure DNS records at domain registrar
3. Add custom domain `claudecodeplugins.io` in GitHub Pages settings
4. Push changes to trigger deployment
5. Wait for DNS propagation (24-48 hours)
6. Verify site is live at https://claudecodeplugins.io

---

**Deployment Ready!** Follow the steps above to complete the deployment process.
