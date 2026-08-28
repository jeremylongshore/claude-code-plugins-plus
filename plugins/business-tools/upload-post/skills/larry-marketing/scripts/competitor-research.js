#!/usr/bin/env node
/**
 * Competitor Research — Save & Query Findings
 * 
 * The actual research is done by the agent using the browser.
 * This script manages the competitor-research.json file.
 * 
 * Usage:
 *   node competitor-research.js --dir tiktok-marketing/ --summary
 *   node competitor-research.js --dir tiktok-marketing/ --add-competitor '{"name":"AppX","tiktokHandle":"@appx",...}'
 *   node competitor-research.js --dir tiktok-marketing/ --gaps
 */

const fs = require('fs');
const path = require('path');

const args = process.argv.slice(2);
const dir = args.includes('--dir') ? args[args.indexOf('--dir') + 1] : 'tiktok-marketing';
const filePath = path.join(dir, 'competitor-research.json');

function loadData() {
  if (!fs.existsSync(filePath)) {
    return {
      researchDate: '',
      competitors: [],
      nicheInsights: { trendingSounds: [], commonFormats: [], gapOpportunities: '', avoidPatterns: '' }
    };
  }
  return JSON.parse(fs.readFileSync(filePath, 'utf-8'));
}

function saveData(data) {
  fs.writeFileSync(filePath, JSON.stringify(data, null, 2));
}

if (args.includes('--summary')) {
  const data = loadData();
  if (data.competitors.length === 0) {
    console.log('No competitor research yet. Use the browser to research competitors first.');
    process.exit(0);
  }
  console.log(`📊 Competitor Research (${data.researchDate})\n`);
  console.log(`Found ${data.competitors.length} competitors:\n`);
  data.competitors.forEach(c => {
    console.log(`  ${c.name} (${c.tiktokHandle || 'no handle'})`);
    console.log(`    Followers: ${c.followers || '?'} | Avg views: ${c.avgViews || '?'}`);
    if (c.bestVideo) console.log(`    Best: ${c.bestVideo.views} views — "${c.bestVideo.hook}"`);
    if (c.strengths) console.log(`    Strengths: ${c.strengths}`);
    if (c.weaknesses) console.log(`    Weaknesses: ${c.weaknesses}`);
    console.log('');
  });
  if (data.nicheInsights?.gapOpportunities) {
    console.log(`💡 Gap opportunities: ${data.nicheInsights.gapOpportunities}`);
  }
  if (data.nicheInsights?.avoidPatterns) {
    console.log(`⚠️  Avoid: ${data.nicheInsights.avoidPatterns}`);
  }
}

if (args.includes('--add-competitor')) {
  const idx = args.indexOf('--add-competitor');
  const json = args[idx + 1];
  try {
    const competitor = JSON.parse(json);
    const data = loadData();
    data.competitors.push(competitor);
    data.researchDate = new Date().toISOString().split('T')[0];
    saveData(data);
    console.log(`✅ Added competitor: ${competitor.name}`);
  } catch (e) {
    console.error('Invalid JSON for competitor:', e.message);
    process.exit(1);
  }
}

if (args.includes('--gaps')) {
  const data = loadData();
  if (!data.nicheInsights) {
    console.log('No niche insights yet.');
    process.exit(0);
  }
  console.log('Gap Analysis:\n');
  console.log(`  Opportunities: ${data.nicheInsights.gapOpportunities || 'None recorded'}`);
  console.log(`  Avoid: ${data.nicheInsights.avoidPatterns || 'None recorded'}`);
  console.log(`  Common formats: ${(data.nicheInsights.commonFormats || []).join(', ') || 'None recorded'}`);
  console.log(`  Trending sounds: ${(data.nicheInsights.trendingSounds || []).join(', ') || 'None recorded'}`);
}
