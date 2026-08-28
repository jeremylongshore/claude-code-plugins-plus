#!/usr/bin/env node
/**
 * Learn from Analytics - Accumulates insights and extracts patterns
 * 
 * What it learns:
 * 1. Hook type performance (SHOCK vs CURIOSITY vs CONTRADICTION)
 * 2. Best words/phrases that appear in top performers
 * 3. Best emojis
 * 4. Best hours and days
 * 5. Patterns to AVOID (from low performers)
 * 
 * Output: learnings.json that feeds back into generate-hooks.sh
 */

const fs = require('fs');
const path = require('path');

const SKILL_DIR = path.dirname(__dirname);
const LEARNINGS_FILE = path.join(SKILL_DIR, 'learnings.json');
const HOOK_LEDGER_FILE = path.join(SKILL_DIR, 'hook-ledger.json');
const PERFORMANCE_FILE = '/home/node/clawd/tiktok-marketing/hook-performance.json';

// Common words to ignore when extracting patterns
const STOP_WORDS = new Set([
  'el', 'la', 'los', 'las', 'un', 'una', 'de', 'del', 'en', 'a', 'que', 'y', 'o', 'tu', 'tus',
  'the', 'a', 'an', 'in', 'on', 'at', 'to', 'for', 'of', 'and', 'or', 'your', 'you',
  'es', 'son', 'está', 'están', 'con', 'por', 'para', 'como', 'más', 'pero', 'si',
  'is', 'are', 'was', 'were', 'be', 'been', 'being', 'have', 'has', 'had', 'do', 'does',
  'this', 'that', 'these', 'those', 'my', 'his', 'her', 'its', 'our', 'their',
  'al', 'cada', 'todo', 'toda', 'todos', 'todas', 'muy', 'ya', 'se', 'lo', 'le'
]);

function loadLearnings() {
  try {
    return JSON.parse(fs.readFileSync(LEARNINGS_FILE, 'utf8'));
  } catch (e) {
    return {
      version: 3,
      created: new Date().toISOString(),
      updated: null,
      totalPostsAnalyzed: 0,
      
      // Performance by hook type
      hookTypes: {
        shock: { posts: 0, totalViews: 0, avgViews: 0, avgEngagement: 0, wins: 0 },
        curiosity: { posts: 0, totalViews: 0, avgViews: 0, avgEngagement: 0, wins: 0 },
        contradiction: { posts: 0, totalViews: 0, avgViews: 0, avgEngagement: 0, wins: 0 }
      },
      
      // Patterns that WORK (from top performers)
      winning: {
        words: [],      // [{word, count, avgViews}]
        emojis: [],     // [{emoji, count, avgViews}]
        phrases: [],    // [{phrase, count, avgViews}]
        hours: [],      // [{hour, count, avgViews}]
        days: []        // [{day, count, avgViews}]
      },
      
      // Patterns to AVOID (from low performers)
      avoid: {
        words: [],
        emojis: [],
        phrases: []
      },
      
      // Top 10 best performing hooks (for reference)
      topHooks: [],
      
      // Generated recommendations for next hooks
      recommendations: {
        preferHookType: null,
        useWords: [],
        useEmojis: [],
        avoidWords: [],
        bestHour: null,
        bestDay: null,
        promptBoost: ""  // Extra instructions for the AI based on learnings
      },
      
      // History of learning updates
      history: []
    };
  }
}

function loadPerformanceData() {
  try {
    return JSON.parse(fs.readFileSync(PERFORMANCE_FILE, 'utf8'));
  } catch (e) {
    console.error('❌ Cannot load performance data:', e.message);
    return null;
  }
}

function loadHookLedger() {
  try {
    return JSON.parse(fs.readFileSync(HOOK_LEDGER_FILE, 'utf8'));
  } catch (e) {
    return { hooks: [] };
  }
}

function extractEmojis(text) {
  if (!text) return [];
  const emojiRegex = /[\u{1F300}-\u{1F9FF}]|[\u{2600}-\u{26FF}]|[\u{2700}-\u{27BF}]|[\u{1F600}-\u{1F64F}]|[\u{1F680}-\u{1F6FF}]/gu;
  return text.match(emojiRegex) || [];
}

function extractWords(text) {
  if (!text) return [];
  // Remove emojis and special chars, lowercase, split
  const cleaned = text
    .replace(/[\u{1F300}-\u{1F9FF}]|[\u{2600}-\u{26FF}]|[\u{2700}-\u{27BF}]|[\u{1F600}-\u{1F64F}]|[\u{1F680}-\u{1F6FF}]/gu, '')
    .toLowerCase()
    .replace(/[^\w\sáéíóúñü]/g, ' ')
    .split(/\s+/)
    .filter(w => w.length > 2 && !STOP_WORDS.has(w));
  return cleaned;
}

function extractPhrases(text) {
  if (!text) return [];
  // Extract 2-3 word phrases that might be hooks
  const cleaned = text.replace(/[\u{1F300}-\u{1F9FF}]|[\u{2600}-\u{26FF}]/gu, '').trim();
  const phrases = [];
  
  // Look for common hook patterns
  const patterns = [
    /¿[^?]+\?/g,           // Spanish questions
    /\b\w+\s+\w+\s+\w+(?=\s|$)/g,  // 3-word phrases
  ];
  
  patterns.forEach(pattern => {
    const matches = cleaned.match(pattern);
    if (matches) phrases.push(...matches.map(m => m.toLowerCase().trim()));
  });
  
  return phrases.slice(0, 3); // Max 3 phrases per post
}

function determineHookType(caption, ledgerHooks) {
  if (!caption) return 'unknown';
  
  // First try to match with ledger
  const ledgerMatch = ledgerHooks.find(h => 
    caption.toLowerCase().includes(h.hook_text?.toLowerCase()?.slice(0, 20))
  );
  if (ledgerMatch?.type) return ledgerMatch.type.toLowerCase();
  
  // Heuristic detection
  const lower = caption.toLowerCase();
  if (lower.includes('💀') || lower.includes('😱') || lower.includes('error') || lower.includes('muerto')) {
    return 'shock';
  }
  if (lower.includes('🤔') || lower.includes('?') || lower.includes('por qué') || lower.includes('cómo')) {
    return 'curiosity';
  }
  if (lower.includes('🤷') || lower.includes('menos') || lower.includes('but') || lower.includes('pero')) {
    return 'contradiction';
  }
  return 'unknown';
}

function updateWordStats(statsArray, items, views, engagement, isWinning) {
  items.forEach(item => {
    let existing = statsArray.find(s => s.item === item);
    if (!existing) {
      existing = { item, count: 0, totalViews: 0, totalEngagement: 0, avgViews: 0, avgEngagement: 0 };
      statsArray.push(existing);
    }
    existing.count++;
    existing.totalViews += views;
    existing.totalEngagement += engagement;
    existing.avgViews = Math.round(existing.totalViews / existing.count);
    existing.avgEngagement = (existing.totalEngagement / existing.count).toFixed(2);
  });
}

function generateRecommendations(learnings) {
  const rec = learnings.recommendations;
  
  // 1. Best hook type
  const types = learnings.hookTypes;
  const typeRanking = Object.entries(types)
    .filter(([_, data]) => data.posts >= 2) // Need at least 2 posts
    .sort((a, b) => b[1].avgViews - a[1].avgViews);
  
  if (typeRanking.length > 0) {
    rec.preferHookType = typeRanking[0][0];
    
    // Calculate if there's a significant winner (>30% better)
    if (typeRanking.length > 1) {
      const best = typeRanking[0][1].avgViews;
      const second = typeRanking[1][1].avgViews;
      if (best > second * 1.3) {
        types[typeRanking[0][0]].wins++;
      }
    }
  }
  
  // 2. Best words (top 5 by avgViews with count >= 2)
  rec.useWords = learnings.winning.words
    .filter(w => w.count >= 2)
    .sort((a, b) => b.avgViews - a.avgViews)
    .slice(0, 5)
    .map(w => w.item);
  
  // 3. Best emojis
  rec.useEmojis = learnings.winning.emojis
    .filter(e => e.count >= 2)
    .sort((a, b) => b.avgViews - a.avgViews)
    .slice(0, 3)
    .map(e => e.item);
  
  // 4. Words to avoid (from low performers)
  rec.avoidWords = learnings.avoid.words
    .filter(w => w.count >= 2)
    .sort((a, b) => a.avgViews - b.avgViews)
    .slice(0, 5)
    .map(w => w.item);
  
  // 5. Best hour
  const hourStats = learnings.winning.hours
    .filter(h => h.count >= 2)
    .sort((a, b) => b.avgViews - a.avgViews);
  rec.bestHour = hourStats.length > 0 ? hourStats[0].item : null;
  
  // 6. Best day
  const dayStats = learnings.winning.days
    .filter(d => d.count >= 2)
    .sort((a, b) => b.avgViews - a.avgViews);
  rec.bestDay = dayStats.length > 0 ? dayStats[0].item : null;
  
  // 7. Generate prompt boost for AI
  let boost = [];
  if (rec.useWords.length > 0) {
    boost.push(`Use these HIGH-PERFORMING words: ${rec.useWords.join(', ')}`);
  }
  if (rec.useEmojis.length > 0) {
    boost.push(`Include these emojis that get engagement: ${rec.useEmojis.join(' ')}`);
  }
  if (rec.avoidWords.length > 0) {
    boost.push(`AVOID these low-performing words: ${rec.avoidWords.join(', ')}`);
  }
  if (rec.preferHookType) {
    boost.push(`Preferred hook style: ${rec.preferHookType.toUpperCase()} (best performing)`);
  }
  rec.promptBoost = boost.join('. ');
  
  return rec;
}

function main() {
  console.log('═══════════════════════════════════════════════════════════════');
  console.log('🧠 LEARNING FROM ANALYTICS');
  console.log('═══════════════════════════════════════════════════════════════\n');
  
  const perfData = loadPerformanceData();
  if (!perfData || !perfData.allPosts) {
    console.log('❌ No performance data found. Run check-analytics.sh first.');
    process.exit(1);
  }
  
  const ledger = loadHookLedger();
  const learnings = loadLearnings();
  
  // Filter out test posts (views < 10 or caption too short)
  const validPosts = perfData.allPosts.filter(p => 
    p.views >= 10 && p.caption && p.caption.length > 20
  );
  
  console.log(`📊 Analyzing ${validPosts.length} valid posts (excluded ${perfData.allPosts.length - validPosts.length} test posts)\n`);
  
  if (validPosts.length === 0) {
    console.log('❌ No valid posts to analyze.');
    process.exit(1);
  }
  
  // Calculate average for top/bottom classification
  const avgViews = validPosts.reduce((sum, p) => sum + (p.views || 0), 0) / validPosts.length;
  const avgEngagement = validPosts.reduce((sum, p) => sum + parseFloat(p.engagementRate || 0), 0) / validPosts.length;
  
  console.log(`📈 Average views: ${Math.round(avgViews)}`);
  console.log(`📈 Average engagement: ${avgEngagement.toFixed(2)}%\n`);
  
  // Classify posts
  const topPosts = validPosts.filter(p => p.views > avgViews * 1.2); // 20% above average
  const lowPosts = validPosts.filter(p => p.views < avgViews * 0.5); // 50% below average
  
  console.log(`🏆 Top performers: ${topPosts.length}`);
  console.log(`📉 Low performers: ${lowPosts.length}\n`);
  
  // Reset stats for fresh calculation
  learnings.winning.words = [];
  learnings.winning.emojis = [];
  learnings.winning.hours = [];
  learnings.winning.days = [];
  learnings.avoid.words = [];
  learnings.avoid.emojis = [];
  
  // Reset hook type stats
  Object.keys(learnings.hookTypes).forEach(type => {
    learnings.hookTypes[type] = { posts: 0, totalViews: 0, avgViews: 0, avgEngagement: 0, wins: learnings.hookTypes[type].wins || 0 };
  });
  
  // Process all valid posts
  validPosts.forEach(post => {
    const views = post.views || 0;
    const engagement = parseFloat(post.engagementRate || 0);
    const hookType = determineHookType(post.caption, ledger.hooks);
    const isTop = views > avgViews * 1.2;
    const isLow = views < avgViews * 0.5;
    
    // Update hook type stats
    if (hookType !== 'unknown' && learnings.hookTypes[hookType]) {
      const typeStats = learnings.hookTypes[hookType];
      typeStats.posts++;
      typeStats.totalViews += views;
      typeStats.avgViews = Math.round(typeStats.totalViews / typeStats.posts);
      typeStats.avgEngagement = ((typeStats.avgEngagement * (typeStats.posts - 1) + engagement) / typeStats.posts).toFixed(2);
    }
    
    // Extract patterns
    const words = extractWords(post.caption);
    const emojis = extractEmojis(post.caption);
    const hour = post.hour;
    const day = post.dayOfWeek;
    
    // Update winning patterns (from top posts)
    if (isTop) {
      updateWordStats(learnings.winning.words, words, views, engagement, true);
      updateWordStats(learnings.winning.emojis, emojis, views, engagement, true);
      if (hour !== undefined) updateWordStats(learnings.winning.hours, [hour], views, engagement, true);
      if (day) updateWordStats(learnings.winning.days, [day], views, engagement, true);
    }
    
    // Update avoid patterns (from low posts)
    if (isLow) {
      updateWordStats(learnings.avoid.words, words, views, engagement, false);
      updateWordStats(learnings.avoid.emojis, emojis, views, engagement, false);
    }
  });
  
  // Store top hooks for reference
  learnings.topHooks = topPosts
    .sort((a, b) => b.views - a.views)
    .slice(0, 10)
    .map(p => ({
      caption: p.caption?.slice(0, 100),
      views: p.views,
      engagement: p.engagementRate,
      hour: p.hour,
      day: p.dayOfWeek
    }));
  
  // Generate recommendations
  learnings.totalPostsAnalyzed = validPosts.length;
  generateRecommendations(learnings);
  
  // Add to history
  learnings.history.push({
    date: new Date().toISOString(),
    postsAnalyzed: validPosts.length,
    avgViews: Math.round(avgViews),
    topHookType: learnings.recommendations.preferHookType
  });
  
  // Keep only last 10 history entries
  if (learnings.history.length > 10) {
    learnings.history = learnings.history.slice(-10);
  }
  
  // Save
  learnings.updated = new Date().toISOString();
  fs.writeFileSync(LEARNINGS_FILE, JSON.stringify(learnings, null, 2));
  
  // Print summary
  console.log('═══════════════════════════════════════════════════════════════');
  console.log('📋 LEARNINGS SUMMARY');
  console.log('═══════════════════════════════════════════════════════════════\n');
  
  console.log('🎯 HOOK TYPE PERFORMANCE:');
  Object.entries(learnings.hookTypes).forEach(([type, data]) => {
    if (data.posts > 0) {
      console.log(`   ${type.toUpperCase()}: ${data.posts} posts, avg ${data.avgViews} views, ${data.avgEngagement}% eng`);
    }
  });
  
  console.log('\n✅ WINNING PATTERNS:');
  if (learnings.recommendations.useWords.length > 0) {
    console.log(`   Words: ${learnings.recommendations.useWords.join(', ')}`);
  }
  if (learnings.recommendations.useEmojis.length > 0) {
    console.log(`   Emojis: ${learnings.recommendations.useEmojis.join(' ')}`);
  }
  if (learnings.recommendations.bestHour !== null) {
    console.log(`   Best hour: ${learnings.recommendations.bestHour}:00 UTC`);
  }
  
  console.log('\n❌ PATTERNS TO AVOID:');
  if (learnings.recommendations.avoidWords.length > 0) {
    console.log(`   Words: ${learnings.recommendations.avoidWords.join(', ')}`);
  }
  
  console.log('\n💡 RECOMMENDATION:');
  console.log(`   Prefer: ${learnings.recommendations.preferHookType?.toUpperCase() || 'need more data'} hooks`);
  
  console.log('\n📝 PROMPT BOOST FOR AI:');
  console.log(`   "${learnings.recommendations.promptBoost || 'Need more data'}"`);
  
  console.log('\n✅ Saved to:', LEARNINGS_FILE);
}

main();
