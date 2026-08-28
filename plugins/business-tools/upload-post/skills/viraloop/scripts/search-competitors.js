#!/usr/bin/env node
/**
 * Search for competitors using multiple search engines
 */

const { chromium } = require('playwright');
const fs = require('fs');

const CAROUSEL_DIR = '/tmp/carousel';

async function searchBing(browser, query) {
  const page = await browser.newPage();
  try {
    const url = `https://www.bing.com/search?q=${encodeURIComponent(query)}`;
    await page.goto(url, { timeout: 15000 });
    await page.waitForTimeout(2000);
    
    const results = await page.evaluate(() => {
      const items = [];
      document.querySelectorAll('#b_results .b_algo, .b_algo').forEach(el => {
        const titleEl = el.querySelector('h2 a, h2');
        const title = titleEl?.textContent?.trim();
        const link = titleEl?.href;
        const snippet = el.querySelector('.b_caption p, p')?.textContent?.trim();
        if (title && items.length < 5) {
          items.push({ title, snippet: snippet?.substring(0, 200), link });
        }
      });
      return items;
    });
    
    return results;
  } finally {
    await page.close();
  }
}

async function searchDuckDuckGoHTML(browser, query) {
  const page = await browser.newPage();
  try {
    // HTML version without JS
    const url = `https://html.duckduckgo.com/html/?q=${encodeURIComponent(query)}`;
    await page.goto(url, { timeout: 15000 });
    
    const results = await page.evaluate(() => {
      const items = [];
      document.querySelectorAll('.result, .web-result').forEach(el => {
        const title = el.querySelector('.result__title, .result__a')?.textContent?.trim();
        const link = el.querySelector('.result__a')?.href;
        const snippet = el.querySelector('.result__snippet')?.textContent?.trim();
        if (title && items.length < 5) {
          items.push({ title, snippet: snippet?.substring(0, 200), link });
        }
      });
      return items;
    });
    
    return results;
  } finally {
    await page.close();
  }
}

async function main() {
  const analysisFile = `${CAROUSEL_DIR}/analysis.json`;
  let analysis = {};
  try {
    analysis = JSON.parse(fs.readFileSync(analysisFile, 'utf8'));
  } catch (e) {
    console.log('Error: analysis.json not found');
    process.exit(1);
  }
  
  // Get real product name
  let productName = analysis.storytelling?.productName || 'Upload-Post';
  // If name is generic, use the URL
  if (productName.toLowerCase().includes('social media api')) {
    productName = analysis.url?.replace(/https?:\/\//, '').split('.')[0] || 'upload-post';
  }
  
  console.log(`🔎 SEARCHING INFO ABOUT: ${productName}\n`);
  
  const browser = await chromium.launch({ headless: true });
  
  const queries = [
    `${productName} review`,
    `${productName} vs alternatives`,
    `${productName} competitors`,
    `social media posting API alternatives`
  ];
  
  const allResults = { competitors: [], reviews: [], mentions: [] };
  
  for (const query of queries) {
    console.log(`   → "${query}"`);
    try {
      // Intentar Bing primero
      let results = await searchBing(browser, query);
      
      // Si no hay resultados, probar DuckDuckGo HTML
      if (results.length === 0) {
        results = await searchDuckDuckGoHTML(browser, query);
      }
      
      console.log(`     ${results.length} resultados`);
      
      results.forEach(r => {
        if (query.includes('alternative') || query.includes('competitor')) {
          if (!allResults.competitors.find(c => c.title === r.title)) {
            allResults.competitors.push(r);
          }
        } else if (query.includes('review')) {
          allResults.reviews.push(r);
        } else {
          allResults.mentions.push(r);
        }
      });
    } catch (e) {
      console.log(`     ⚠️ Error: ${e.message.substring(0, 50)}`);
    }
  }
  
  await browser.close();
  
  // Extract competitor names from titles
  const competitorNames = [];
  const knownCompetitors = ['buffer', 'hootsuite', 'later', 'sprout', 'socialbee', 'publer', 'metricool', 'ayrshare', 'socialbu', 'postiz'];
  
  allResults.competitors.forEach(c => {
    const title = c.title.toLowerCase();
    knownCompetitors.forEach(comp => {
      if (title.includes(comp) && !competitorNames.includes(comp)) {
        competitorNames.push(comp);
      }
    });
  });
  
  // Update analysis
  analysis.marketResearch = allResults;
  analysis.competitors = competitorNames;
  
  // Update storytelling with competitor info
  if (competitorNames.length > 0) {
    analysis.storytelling.competitorDiff = `Unlike ${competitorNames.slice(0, 2).join(' and ')}, ${productName} offers a direct API with a single call.`;
  }
  
  fs.writeFileSync(analysisFile, JSON.stringify(analysis, null, 2));
  
  console.log('\n═══════════════════════════════════════════════════════════════');
  console.log('✅ SEARCH COMPLETED');
  console.log('═══════════════════════════════════════════════════════════════');
  console.log(`   Competitors detected: ${competitorNames.join(', ') || 'none'}`);
  console.log(`   Reviews found: ${allResults.reviews.length}`);
  console.log(`   Mentions: ${allResults.mentions.length}`);
  console.log(`\n💾 Updated: ${analysisFile}`);
}

main().catch(console.error);
