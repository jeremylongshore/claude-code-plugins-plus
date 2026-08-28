#!/usr/bin/env node
/**
 * Daily Marketing Report — Upload-Post API
 * 
 * Cross-references platform analytics (via Upload-Post) with RevenueCat conversions
 * to identify which hooks drive views AND revenue.
 * 
 * Data sources:
 * 1. Upload-Post Analytics API → platform-level stats (followers, impressions, reach)
 * 2. Upload-Post History API → per-post upload results with request_ids and post URLs
 * 3. RevenueCat API (optional) → trials, conversions, revenue
 * 
 * The diagnostic framework:
 * - High views + High conversions → SCALE (make variations of winning hooks)
 * - High views + Low conversions → FIX CTA (hook works, downstream is broken)  
 * - Low views + High conversions → FIX HOOKS (content converts, needs more eyeballs)
 * - Low views + Low conversions → FULL RESET (try radically different approach)
 * 
 * Usage: node daily-report.js --config <config.json> [--days 3]
 * Output: tiktok-marketing/reports/YYYY-MM-DD.md
 */

const fs = require('fs');
const path = require('path');

const args = process.argv.slice(2);
function getArg(name) {
  const idx = args.indexOf(`--${name}`);
  return idx !== -1 ? args[idx + 1] : null;
}

const configPath = getArg('config');
const days = parseInt(getArg('days') || '3');

if (!configPath) {
  console.error('Usage: node daily-report.js --config <config.json> [--days 3]');
  process.exit(1);
}

const config = JSON.parse(fs.readFileSync(configPath, 'utf-8'));
const baseDir = path.dirname(configPath);
const BASE_URL = 'https://api.upload-post.com/api';
const API_KEY = config.uploadPost?.apiKey;
const PROFILE = config.uploadPost?.profile || 'upload_post';
const PLATFORMS = config.uploadPost?.platforms || ['tiktok', 'instagram'];

if (!API_KEY) {
  console.error('❌ Missing uploadPost.apiKey in config');
  process.exit(1);
}

async function uploadPostAPI(endpoint) {
  const res = await fetch(`${BASE_URL}${endpoint}`, {
    headers: { 'Authorization': `Apikey ${API_KEY}` }
  });
  if (!res.ok) {
    const text = await res.text();
    throw new Error(`API ${endpoint} failed (${res.status}): ${text.substring(0, 200)}`);
  }
  return res.json();
}

async function sleep(ms) { return new Promise(r => setTimeout(r, ms)); }

// RevenueCat API (if configured)
async function getRevenueCatMetrics(startDate, endDate) {
  if (!config.revenuecat?.enabled || !config.revenuecat?.v2SecretKey) {
    return null;
  }
  
  const RC_URL = 'https://api.revenuecat.com/v2';
  const headers = {
    'Authorization': `Bearer ${config.revenuecat.v2SecretKey}`,
    'Content-Type': 'application/json'
  };

  try {
    const overviewRes = await fetch(`${RC_URL}/projects/${config.revenuecat.projectId}/metrics/overview`, { headers });
    const overview = await overviewRes.json();

    const txRes = await fetch(`${RC_URL}/projects/${config.revenuecat.projectId}/transactions?start_from=${startDate.toISOString()}&limit=100`, { headers });
    const transactions = await txRes.json();

    const metricsMap = {};
    if (overview.metrics) {
      overview.metrics.forEach(m => { metricsMap[m.id] = m.value; });
    }

    return {
      overview,
      transactions: transactions.items || [],
      mrr: metricsMap.mrr || 0,
      activeTrials: metricsMap.active_trials || 0,
      activeSubscribers: metricsMap.active_subscriptions || 0,
      activeUsers: metricsMap.active_users || 0,
      newCustomers: metricsMap.new_customers || 0,
      revenue: metricsMap.revenue || 0
    };
  } catch (e) {
    console.log(`  ⚠️ RevenueCat API error: ${e.message}`);
    return null;
  }
}

// Load previous platform stats for delta tracking
function loadPreviousPlatformStats() {
  const statsPath = path.join(baseDir, 'platform-stats.json');
  if (fs.existsSync(statsPath)) {
    return JSON.parse(fs.readFileSync(statsPath, 'utf-8'));
  }
  return null;
}

function savePlatformStats(stats) {
  const statsPath = path.join(baseDir, 'platform-stats.json');
  fs.writeFileSync(statsPath, JSON.stringify(stats, null, 2));
}

(async () => {
  const now = new Date();
  const startDate = new Date(now - days * 86400000);
  const dateStr = now.toISOString().slice(0, 10);

  console.log(`📊 Daily Report — ${dateStr} (last ${days} days)\n`);

  // ==========================================
  // 1. UPLOAD-POST: Platform analytics
  // ==========================================
  console.log(`  📈 Fetching platform analytics...`);
  
  const platformStats = {};
  try {
    const platformsParam = PLATFORMS.join(',');
    const analytics = await uploadPostAPI(`/analytics/${PROFILE}?platforms=${platformsParam}`);

    for (const platform of PLATFORMS) {
      const data = analytics[platform];
      if (data && !data.error) {
        platformStats[platform] = {
          followers: data.followers || 0,
          impressions: data.impressions || 0,
          reach: data.reach || 0,
          profileViews: data.profileViews || 0,
          reachTimeseries: data.reach_timeseries || []
        };
      }
    }
  } catch (err) {
    console.log(`  ⚠️ Analytics error: ${err.message}`);
  }

  const prevPlatformStats = loadPreviousPlatformStats();
  savePlatformStats({ date: dateStr, stats: platformStats });

  // ==========================================
  // 2. UPLOAD-POST: Upload history (per-post)
  // ==========================================
  console.log(`  📋 Fetching upload history...`);

  const allUploads = [];
  let page = 1;
  try {
    while (page <= 10) {
      const history = await uploadPostAPI(`/uploadposts/history?page=${page}&limit=50&profile_username=${PROFILE}`);
      const items = history.history || [];
      if (items.length === 0) break;

      for (const item of items) {
        const uploadDate = new Date(item.upload_timestamp);
        if (uploadDate < startDate) {
          page = 11;
          break;
        }
        allUploads.push(item);
      }

      if (items.length < 50) break;
      page++;
      await sleep(300);
    }
  } catch (err) {
    console.log(`  ⚠️ History error: ${err.message}`);
  }

  // Filter to target platforms and group by request_id
  const relevantUploads = allUploads.filter(u => PLATFORMS.includes(u.platform?.toLowerCase()));
  
  const postsByRequestId = {};
  for (const upload of relevantUploads) {
    const rid = upload.request_id || 'unknown';
    if (!postsByRequestId[rid]) {
      postsByRequestId[rid] = {
        requestId: rid,
        caption: upload.post_title || upload.post_caption || '',
        uploadDate: upload.upload_timestamp,
        platforms: {},
        success: true,
        mediaType: upload.media_type
      };
    }
    postsByRequestId[rid].platforms[upload.platform] = {
      success: upload.success,
      postUrl: upload.post_url || null,
      postId: upload.platform_post_id || null,
      error: upload.error_message || null
    };
    if (!upload.success) postsByRequestId[rid].success = false;
  }

  const postResults = Object.values(postsByRequestId);
  postResults.sort((a, b) => new Date(b.uploadDate) - new Date(a.uploadDate));

  console.log(`  📱 Found ${postResults.length} posts in the last ${days} days\n`);

  // ==========================================
  // 3. REVENUECAT: Conversion metrics (optional)
  // ==========================================
  let rcMetrics = null;
  let rcPrevMetrics = null;
  
  if (config.revenuecat?.enabled) {
    console.log(`  💰 Fetching RevenueCat metrics...`);
    rcMetrics = await getRevenueCatMetrics(startDate, now);
    
    const rcSnapshotPath = path.join(baseDir, 'rc-snapshot.json');
    if (fs.existsSync(rcSnapshotPath)) {
      rcPrevMetrics = JSON.parse(fs.readFileSync(rcSnapshotPath, 'utf-8'));
    }
    if (rcMetrics) {
      fs.writeFileSync(rcSnapshotPath, JSON.stringify({ date: dateStr, ...rcMetrics }, null, 2));
    }
  }

  // ==========================================
  // 4. GENERATE REPORT
  // ==========================================
  let report = `# Daily Marketing Report — ${dateStr}\n\n`;

  // Platform stats
  report += `## Platform Stats\n\n`;
  for (const platform of PLATFORMS) {
    const stats = platformStats[platform];
    if (!stats) {
      report += `**${platform}:** No data\n`;
      continue;
    }
    report += `**${platform.toUpperCase()}:**\n`;
    report += `- Followers: ${stats.followers.toLocaleString()}\n`;
    report += `- Impressions: ${stats.impressions.toLocaleString()}\n`;
    if (stats.reach) report += `- Reach: ${stats.reach.toLocaleString()}\n`;
    if (stats.profileViews) report += `- Profile Views: ${stats.profileViews.toLocaleString()}\n`;

    // Reach trend (last 7 days from timeseries)
    if (stats.reachTimeseries && stats.reachTimeseries.length > 0) {
      const recent7d = stats.reachTimeseries.slice(-7);
      const totalReach7d = recent7d.reduce((sum, d) => sum + (d.value || 0), 0);
      report += `- Reach (7d): ${totalReach7d.toLocaleString()}\n`;
    }

    // Delta from previous report
    if (prevPlatformStats?.stats?.[platform]) {
      const prev = prevPlatformStats.stats[platform];
      const followerDelta = stats.followers - (prev.followers || 0);
      const impressionDelta = stats.impressions - (prev.impressions || 0);
      report += `- Δ Followers: ${followerDelta >= 0 ? '+' : ''}${followerDelta}\n`;
      report += `- Δ Impressions: ${impressionDelta >= 0 ? '+' : ''}${impressionDelta.toLocaleString()}\n`;
    }
    report += '\n';
  }

  // Post history
  report += `## Posts (last ${days} days)\n\n`;
  report += `| Date | Caption | Platforms | Status |\n`;
  report += `|------|---------|-----------|--------|\n`;

  for (const p of postResults) {
    const date = p.uploadDate?.slice(0, 10) || 'unknown';
    const platforms = Object.entries(p.platforms)
      .map(([pl, info]) => `${pl}${info.success ? '✅' : '❌'}`)
      .join(', ');
    const status = p.success ? '✅' : '❌';
    report += `| ${date} | ${p.caption.substring(0, 45)}... | ${platforms} | ${status} |\n`;
  }

  report += `\n**Total posts:** ${postResults.length} | **Successful:** ${postResults.filter(p => p.success).length} | **Failed:** ${postResults.filter(p => !p.success).length}\n\n`;

  // RevenueCat section
  if (rcMetrics) {
    report += `## Conversions (RevenueCat)\n\n`;
    report += `- **MRR:** $${rcMetrics.mrr}\n`;
    report += `- **Active subscribers:** ${rcMetrics.activeSubscribers}\n`;
    report += `- **Active trials:** ${rcMetrics.activeTrials}\n`;
    report += `- **Active users (28d):** ${rcMetrics.activeUsers}\n`;
    report += `- **New customers (28d):** ${rcMetrics.newCustomers}\n`;
    report += `- **Revenue (28d):** $${rcMetrics.revenue}\n`;

    if (rcPrevMetrics) {
      const mrrDelta = rcMetrics.mrr - (rcPrevMetrics.mrr || 0);
      const subDelta = rcMetrics.activeSubscribers - (rcPrevMetrics.activeSubscribers || 0);
      const trialDelta = rcMetrics.activeTrials - (rcPrevMetrics.activeTrials || 0);
      const userDelta = rcMetrics.activeUsers - (rcPrevMetrics.activeUsers || 0);
      const customerDelta = rcMetrics.newCustomers - (rcPrevMetrics.newCustomers || 0);

      report += `\n**Changes since last report:**\n`;
      report += `- MRR: ${mrrDelta >= 0 ? '+' : ''}$${mrrDelta}\n`;
      report += `- Subscribers: ${subDelta >= 0 ? '+' : ''}${subDelta}\n`;
      report += `- Trials: ${trialDelta >= 0 ? '+' : ''}${trialDelta}\n`;
      report += `- Active users: ${userDelta >= 0 ? '+' : ''}${userDelta}\n`;
      report += `- New customers: ${customerDelta >= 0 ? '+' : ''}${customerDelta}\n`;

      // Funnel diagnostic
      report += `\n**Funnel health:**\n`;
      if (customerDelta > 10 && subDelta === 0) {
        report += `- ⚠️ Users are downloading (+${customerDelta} new customers) but nobody is subscribing → **App issue** (onboarding/paywall/pricing)\n`;
      } else if (customerDelta > 10 && subDelta > 0) {
        report += `- ✅ Funnel working: +${customerDelta} customers → +${subDelta} subscribers (${((subDelta / customerDelta) * 100).toFixed(1)}% conversion)\n`;
      } else if (customerDelta <= 5) {
        report += `- ⚠️ Few new customers (+${customerDelta}) → **Marketing issue** (views not converting to downloads)\n`;
      }
    }

    // Attribution
    if (rcMetrics.transactions?.length > 0) {
      report += `\n### Conversion Attribution (last ${days} days)\n\n`;
      report += `Found ${rcMetrics.transactions.length} transactions. Cross-referencing with post timing:\n\n`;

      for (const p of postResults.slice(0, 10)) {
        const postDate = new Date(p.uploadDate);
        const windowEnd = new Date(postDate.getTime() + 72 * 3600000);
        const nearbyTx = rcMetrics.transactions.filter(tx => {
          const txDate = new Date(tx.purchase_date || tx.created_at);
          return txDate >= postDate && txDate <= windowEnd;
        });
        if (nearbyTx.length > 0) {
          report += `- "${p.caption.substring(0, 40)}..." → **${nearbyTx.length} conversions within 72h**\n`;
        }
      }
    }
    report += '\n';
  }

  // ==========================================
  // 5. DIAGNOSTIC FRAMEWORK
  // ==========================================
  report += `## Diagnosis\n\n`;

  // Use platform reach data for view-based diagnosis
  for (const platform of PLATFORMS) {
    const stats = platformStats[platform];
    if (!stats) continue;

    const prev = prevPlatformStats?.stats?.[platform];
    const reachDelta = prev ? (stats.impressions - (prev.impressions || 0)) : stats.impressions;
    const viewsPerDay = Math.round(reachDelta / days);

    // Determine conversion quality (if RC available)
    let conversionGood = false;
    let hasConversionData = false;
    if (rcMetrics && rcPrevMetrics) {
      hasConversionData = true;
      const subDelta = rcMetrics.activeSubscribers - (rcPrevMetrics.activeSubscribers || 0);
      const trialDelta = rcMetrics.activeTrials - (rcPrevMetrics.activeTrials || 0);
      conversionGood = (subDelta + trialDelta) > 2;
    }

    const postsInPeriod = postResults.filter(p => p.platforms[platform]).length;
    const viewsGood = viewsPerDay > 3000; // ~3K+ impressions per day = good

    report += `### ${platform.toUpperCase()}\n\n`;
    report += `Impressions delta: +${reachDelta.toLocaleString()} (${viewsPerDay.toLocaleString()}/day) | Posts: ${postsInPeriod}\n\n`;

    if (viewsGood && (!hasConversionData || conversionGood)) {
      report += `🟢 **Views good${hasConversionData ? ' + Conversions good' : ''}** → SCALE IT\n`;
      report += `- Make 3 variations of the top-performing hooks\n`;
      report += `- Test different posting times for optimization\n`;
      report += `- Cross-post to more platforms for extra reach\n`;
    } else if (viewsGood && hasConversionData && !conversionGood) {
      report += `🟡 **Views good + Conversions poor** → FIX THE CTA\n`;
      report += `- People are watching but not converting\n`;
      report += `- Try different CTAs on the last slide\n`;
      report += `- Check if app landing page matches the slideshow promise\n`;
      report += `- DO NOT change the hooks — they're working\n`;
    } else if (!viewsGood && hasConversionData && conversionGood) {
      report += `🟡 **Views poor + Conversions good** → FIX THE HOOKS\n`;
      report += `- People who see it convert, but not enough see it\n`;
      report += `- Test radically different hook categories\n`;
      report += `- Try person+conflict, POV, listicle, mistakes formats\n`;
      report += `- DO NOT change the CTA — it's converting\n`;
    } else {
      report += `🔴 **Views poor${hasConversionData ? ' + Conversions poor' : ''}** → NEEDS WORK\n`;
      report += `- ${viewsPerDay.toLocaleString()} impressions/day is below target\n`;
      report += `- Try radically different format/approach\n`;
      report += `- Research what's trending in the niche RIGHT NOW\n`;
      report += `- Test new hook categories from scratch\n`;
      if (!hasConversionData) {
        report += `- ⚠️ No conversion data — consider connecting RevenueCat\n`;
      }
    }
    report += '\n';
  }

  // ==========================================
  // 6. HOOK + CTA PERFORMANCE TRACKING
  // ==========================================
  const hookPath = path.join(baseDir, 'hook-performance.json');
  let hookData = { hooks: [], ctas: [], rules: { doubleDown: [], testing: [], dropped: [] } };
  if (fs.existsSync(hookPath)) {
    hookData = JSON.parse(fs.readFileSync(hookPath, 'utf-8'));
    if (!hookData.ctas) hookData.ctas = [];
  }

  // Update hook performance
  for (const p of postResults) {
    let conversions = 0;
    if (rcMetrics?.transactions?.length > 0) {
      const postDate = new Date(p.uploadDate);
      const windowEnd = new Date(postDate.getTime() + 72 * 3600000);
      conversions = rcMetrics.transactions.filter(tx => {
        const txDate = new Date(tx.purchase_date || tx.created_at);
        return txDate >= postDate && txDate <= windowEnd;
      }).length;
    }

    const existing = hookData.hooks.find(h => h.requestId === p.requestId);
    if (existing) {
      existing.conversions = conversions;
      existing.lastChecked = dateStr;
      existing.platforms = p.platforms;
    } else {
      hookData.hooks.push({
        requestId: p.requestId,
        text: p.caption.substring(0, 70),
        date: p.uploadDate?.slice(0, 10),
        platforms: p.platforms,
        success: p.success,
        conversions,
        cta: '',
        lastChecked: dateStr
      });
    }
  }
  fs.writeFileSync(hookPath, JSON.stringify(hookData, null, 2));

  // ==========================================
  // 7. PER-POST FUNNEL DIAGNOSIS
  // ==========================================
  report += `## Per-Post Funnel Diagnosis\n\n`;

  const hasRC = rcMetrics && rcPrevMetrics;
  const recentHooks = hookData.hooks.filter(h => h.lastChecked === dateStr);

  if (recentHooks.length > 0 && hasRC) {
    for (const h of recentHooks) {
      const hasConversions = h.conversions > 0;
      const platformStatus = Object.entries(h.platforms || {})
        .map(([p, info]) => `${p}:${info.success ? '✅' : '❌'}`)
        .join(' ');

      report += `**"${h.text.substring(0, 55)}..."** — ${platformStatus}, ${h.conversions} conversions\n`;

      if (h.success && hasConversions) {
        report += `  🟢 Post delivered + converting → SCALE this hook\n`;
      } else if (h.success && !hasConversions) {
        report += `  🟡 Post delivered but no conversions → Try different CTA\n`;
      } else if (!h.success) {
        report += `  🔴 Post delivery failed → Check Upload-Post for errors\n`;
      }
      report += '\n';
    }
  } else if (!hasRC) {
    report += `⚠️ No RevenueCat data — can only track post delivery status. Connect RevenueCat for full funnel intelligence.\n\n`;
  }

  // ==========================================
  // 8. AUTO-GENERATED RECOMMENDATIONS
  // ==========================================
  report += `## Auto-Generated Recommendations\n\n`;

  const allHistorical = hookData.hooks.filter(h => h.success);

  if (allHistorical.length > 0) {
    // Winners = posts that converted
    const winners = allHistorical.filter(h => h.conversions > 0);
    const losers = allHistorical.filter(h => h.conversions === 0 && h.lastChecked);

    if (winners.length > 0) {
      report += `**Winning hooks (with conversions):**\n`;
      for (const w of winners.slice(0, 5)) {
        report += `- "${w.text.substring(0, 60)}..." — ${w.conversions} conversions\n`;
      }
      report += '\n';
    }

    if (losers.length > 3) {
      report += `**Consider dropping (no conversions):**\n`;
      for (const l of losers.slice(-3)) {
        report += `- "${l.text.substring(0, 60)}..."\n`;
      }
      report += '\n';
    }

    // CTA rotation advice
    if (hasRC) {
      const noConvertPosts = allHistorical.filter(h => h.success && h.conversions === 0);
      if (noConvertPosts.length > 3) {
        report += `**🔄 CTA rotation needed** — ${noConvertPosts.length} posts delivered but no conversions.\n`;
        report += `Try rotating through:\n`;
        report += `- "Download [app] — link in bio"\n`;
        report += `- "[app] is free to try — link in bio"\n`;
        report += `- "I used [app] for this — link in bio"\n`;
        report += `- "Search [app] on the App Store"\n`;
        report += `- No explicit CTA (just app name visible on last slide)\n\n`;
      }
    }
  }

  report += `---\n\n`;
  report += `*Report generated ${now.toISOString()} | Profile: ${PROFILE} | Platforms: ${PLATFORMS.join(', ')}*\n`;

  // ==========================================
  // 9. SAVE REPORT
  // ==========================================
  const reportsDir = path.join(baseDir, 'reports');
  fs.mkdirSync(reportsDir, { recursive: true });
  const reportPath = path.join(reportsDir, `${dateStr}.md`);
  fs.writeFileSync(reportPath, report);
  console.log(`\n📋 Report saved to ${reportPath}`);
  console.log('\n' + report);
})();
