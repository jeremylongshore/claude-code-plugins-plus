# DNS Setup Instructions for claudecodeskills.io

**Date:** December 5, 2024
**Domain:** claudecodeskills.io
**Target:** GitHub Pages (jeremylongshore/claude-code-plugins-plus)
**Status:** Ready for DNS configuration

---

## 🎯 Quick Setup: Option 1 - Redirect (RECOMMENDED FOR NOW)

This captures Skills SEO traffic immediately with minimal setup.

### At Your Domain Registrar (GoDaddy/Namecheap/etc)

1. **Add URL Redirect Record:**
   ```
   Type: URL Redirect (301 Permanent)
   Host: @
   Destination: https://claudecodeplugins.io
   ```

2. **Add WWW Redirect:**
   ```
   Type: URL Redirect (301 Permanent)
   Host: www
   Destination: https://claudecodeplugins.io
   ```

**Time to propagate:** 5-30 minutes
**Result:** claudecodeskills.io → claudecodeplugins.io

---

## 🌐 Option 2: Full GitHub Pages Setup (Future)

If you want both domains serving the same content:

### Step 1: DNS Records at Registrar

Add these A records for apex domain:
```
Type: A
Host: @
Points to: 185.199.108.153

Type: A
Host: @
Points to: 185.199.109.153

Type: A
Host: @
Points to: 185.199.110.153

Type: A
Host: @
Points to: 185.199.111.153
```

Add CNAME for www:
```
Type: CNAME
Host: www
Points to: jeremylongshore.github.io
```

### Step 2: Multiple Domains Issue

**⚠️ LIMITATION:** GitHub Pages only supports ONE custom domain per repository.

**Solutions:**
1. Use Cloudflare Pages (free, supports multiple domains)
2. Use Netlify (free tier, multiple domains)
3. Keep redirect setup (Option 1)

---

## ✅ Recommended Action Plan

### Today: Implement Option 1 (Redirect)
1. Log into your domain registrar
2. Add 301 redirect: claudecodeskills.io → claudecodeplugins.io
3. Test in 30 minutes

### Benefits:
- ✅ Immediate SEO capture for "Claude Skills" searches
- ✅ No changes to existing setup
- ✅ 5 minute implementation
- ✅ Can upgrade later

### Future: Consider Cloudflare Pages
- Free hosting
- Multiple custom domains
- Better performance
- Full control

---

## 🧪 Testing Your Setup

After DNS propagates (5-30 mins):

```bash
# Test redirect
curl -I https://claudecodeskills.io

# Expected response:
HTTP/2 301
Location: https://claudecodeplugins.io

# Test in browser
open https://claudecodeskills.io
# Should redirect to claudecodeplugins.io
```

---

## 📊 SEO Impact

Once redirect is live:
- Google will start associating "Claude Skills" searches with your site
- Search console will show traffic from both domains
- Rankings will improve for Skills-related keywords

---

## 🔧 Registrar-Specific Instructions

### GoDaddy
1. Domain Settings → Manage DNS
2. Add → Forwarding
3. Forward to: https://claudecodeplugins.io
4. Type: Permanent (301)
5. Save

### Namecheap
1. Domain List → Manage
2. Advanced DNS
3. Add New Record → URL Redirect Record
4. Value: https://claudecodeplugins.io
5. Save

### Cloudflare
1. DNS → Records
2. Add Record → Type: CNAME
3. Name: @
4. Target: claudecodeplugins.io
5. Add Page Rule for 301 redirect

---

## 📈 Next Steps After DNS

1. **Submit to Google Search Console**
   - Add claudecodeskills.io as property
   - Verify ownership
   - Submit sitemap

2. **Update Marketing**
   - Add claudecodeskills.io to social bios
   - Include in documentation
   - Mention in announcements

3. **Track Performance**
   - Monitor traffic from new domain
   - Watch Skills-related keywords
   - Measure conversion improvement

---

**Status:** Ready for implementation
**Estimated Time:** 5 minutes
**Recommendation:** Start with Option 1 (Redirect) TODAY