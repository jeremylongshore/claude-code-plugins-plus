#!/usr/bin/env node
/**
 * Analytics Checker — Upload-Post API
 * 
 * Pulls platform analytics and upload history to track post performance.
 * 
 * How it works:
 * 1. Fetches platform-level analytics (followers, impressions, reach) from Upload-Post
 * 2. Fetches upload history filtered by profile to get per-post results
 * 3. Tracks views, likes, comments, shares per platform
 * 4. No manual video-ID linking needed — Upload-Post tracks by request_id automatically
 * 
 * Usage: node check-analytics.js --config <config.json> [--days 3] [--profile upload_post]
 * 
 * --days: How many days back to check upload history (default: 3)
 * --profile: Override profile from config
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
const profileOverride = getArg('profile');

if (!configPath) {
  console.error('Usage: node check-analytics.js --config <config.json> [--days 3] [--profile name]');
  process.exit(1);
}

const config = JSON.parse(fs.readFileSync(configPath, 'utf-8'));
const BASE_URL = 'https://api.upload-post.com/api';
const API_KEY = config.uploadPost?.apiKey;
const PROFILE = profileOverride || config.uploadPost?.profile || 'upload_post';
const PLATFORMS = config.uploadPost?.platforms || ['tiktok', 'instagram'];

if (!API_KEY) {
  console.error('❌ Missing uploadPost.apiKey in config');
  process.exit(1);
}

async function api(method, endpoint) {
  const res = await fetch(`${BASE_URL}${endpoint}`, {
    method,
    headers: { 'Authorization': `Apikey ${API_KEY}` }
  });
  if (!res.ok) {
    const text = await res.text();
    throw new Error(`API ${method} ${endpoint} failed (${res.status}): ${text.substring(0, 200)}`);
  }
  return res.json();
}

async function sleep(ms) { return new Promise(r => setTimeout(r, ms)); }

(async () => {
  const now = new Date();
  const startDate = new Date(now - days * 86400000);

  console.log(`📊 Checking analytics (last ${days} days)\n`);
  console.log(`   Profile: ${PROFILE}`);
  console.log(`   Platforms: ${PLATFORMS.join(', ')}\n`);

  // ==========================================
  // 1. Platform-level analytics
  // ==========================================
  console.log('📈 Platform Analytics:\n');

  try {
    const platformsParam = PLATFORMS.join(',');
    const analytics = await api('GET', `/analytics/${PROFILE}?platforms=${platformsParam}`);

    for (const platform of PLATFORMS) {
      const data = analytics[platform];
      if (!data) {
        console.log(`  ${platform}: No data available`);
        continue;
      }

      if (data.error || data.message) {
        console.log(`  ${platform}: ${data.error || data.message}`);
        continue;
      }

      console.log(`  📱 ${platform.toUpperCase()}:`);
      if (data.followers !== undefined) console.log(`     Followers: ${data.followers.toLocaleString()}`);
      if (data.impressions !== undefined) console.log(`     Impressions: ${data.impressions.toLocaleString()}`);
      if (data.reach !== undefined) console.log(`     Reach: ${data.reach.toLocaleString()}`);
      if (data.profileViews !== undefined) console.log(`     Profile Views: ${data.profileViews.toLocaleString()}`);

      // Show recent reach trend from timeseries
      if (data.reach_timeseries && data.reach_timeseries.length > 0) {
        const recent = data.reach_timeseries.slice(-7);
        const totalReach = recent.reduce((sum, d) => sum + (d.value || 0), 0);
        console.log(`     Reach (last 7 days): ${totalReach.toLocaleString()}`);
      }
      console.log('');
    }
  } catch (err) {
    console.log(`  ⚠️ Analytics error: ${err.message}\n`);
  }

  // ==========================================
  // 2. Upload history (per-post tracking)
  // ==========================================
  console.log('📋 Upload History (last ' + days + ' days):\n');

  const allUploads = [];
  let page = 1;
  const maxPages = 10;

  try {
    // Fetch upload history pages until we go past our date range
    while (page <= maxPages) {
      const history = await api('GET', `/uploadposts/history?page=${page}&limit=50&profile_username=${PROFILE}`);
      const items = history.history || [];

      if (items.length === 0) break;

      for (const item of items) {
        const uploadDate = new Date(item.upload_timestamp);
        if (uploadDate < startDate) {
          // We've gone past our date range
          page = maxPages + 1; // break outer loop
          break;
        }
        allUploads.push(item);
      }

      if (items.length < 50) break; // last page
      page++;
      await sleep(300);
    }
  } catch (err) {
    console.log(`  ⚠️ History error: ${err.message}\n`);
  }

  // Filter to our target platforms
  const relevantUploads = allUploads.filter(u => 
    PLATFORMS.includes(u.platform?.toLowerCase())
  );

  // Group by request_id (a single post can have multiple platform entries)
  const postsByRequestId = {};
  for (const upload of relevantUploads) {
    const rid = upload.request_id || 'unknown';
    if (!postsByRequestId[rid]) {
      postsByRequestId[rid] = {
        requestId: rid,
        caption: upload.post_title || upload.post_caption || '',
        uploadDate: upload.upload_timestamp,
        platforms: {},
        success: true
      };
    }
    postsByRequestId[rid].platforms[upload.platform] = {
      success: upload.success,
      postUrl: upload.post_url || null,
      postId: upload.platform_post_id || null,
      error: upload.error_message || null,
      mediaType: upload.media_type
    };
    if (!upload.success) postsByRequestId[rid].success = false;
  }

  const posts = Object.values(postsByRequestId);
  posts.sort((a, b) => new Date(b.uploadDate) - new Date(a.uploadDate));

  console.log(`  Found ${posts.length} posts across ${relevantUploads.length} platform uploads\n`);

  const results = [];
  for (const post of posts) {
    const date = post.uploadDate?.slice(0, 10) || 'unknown';
    const statusIcon = post.success ? '✅' : '❌';
    const platformList = Object.entries(post.platforms)
      .map(([p, info]) => `${p}${info.success ? '✅' : '❌'}`)
      .join(', ');

    console.log(`  ${statusIcon} ${date} | ${post.caption.substring(0, 55)}...`);
    console.log(`     Platforms: ${platformList}`);
    console.log(`     Request ID: ${post.requestId}`);

    // Show post URLs
    for (const [platform, info] of Object.entries(post.platforms)) {
      if (info.postUrl) {
        console.log(`     ${platform}: ${info.postUrl}`);
      }
      if (info.error) {
        console.log(`     ${platform} error: ${info.error}`);
      }
    }
    console.log('');

    results.push({
      requestId: post.requestId,
      date,
      caption: post.caption.substring(0, 70),
      platforms: post.platforms,
      success: post.success
    });
  }

  // ==========================================
  // 3. Save analytics snapshot
  // ==========================================
  const baseDir = path.dirname(configPath);
  const analyticsPath = path.join(baseDir, 'analytics-snapshot.json');
  const snapshot = {
    date: now.toISOString(),
    profile: PROFILE,
    platforms: PLATFORMS,
    posts: results,
    totalPosts: results.length,
    successfulPosts: results.filter(r => r.success).length,
    failedPosts: results.filter(r => !r.success).length
  };
  fs.writeFileSync(analyticsPath, JSON.stringify(snapshot, null, 2));
  console.log(`💾 Saved analytics snapshot to ${analyticsPath}`);

  // ==========================================
  // 4. Summary
  // ==========================================
  console.log('\n📊 Summary:');
  console.log(`  Posts tracked: ${results.length}`);
  console.log(`  Successful: ${snapshot.successfulPosts}`);
  console.log(`  Failed: ${snapshot.failedPosts}`);

  // Per-platform summary
  const platformCounts = {};
  for (const post of results) {
    for (const [platform, info] of Object.entries(post.platforms)) {
      if (!platformCounts[platform]) platformCounts[platform] = { success: 0, failed: 0 };
      if (info.success) platformCounts[platform].success++;
      else platformCounts[platform].failed++;
    }
  }
  for (const [platform, counts] of Object.entries(platformCounts)) {
    console.log(`  ${platform}: ${counts.success} ok, ${counts.failed} failed`);
  }
})();
