#!/usr/bin/env node
/**
 * Review generated slides using the AI agent's vision capabilities.
 * 
 * This script prepares slides for review and outputs instructions
 * for the agent to verify each slide using its image-to-text model.
 * 
 * Checks: text legibility, correct spelling, visual coherence, image quality.
 */

const fs = require('fs');
const path = require('path');

const CAROUSEL_DIR = '/tmp/carousel';
const ANALYSIS_FILE = path.join(CAROUSEL_DIR, 'analysis.json');

function getSlideExpectations(analysis) {
  const productName = analysis?.storytelling?.productName || 'Product';
  const hook = analysis?.storytelling?.hooks?.[0] || 'Hook text';
  
  return [
    { slide: 1, type: 'HOOK', expect: hook, check: 'Must grab attention. Text should be large, bold, and fully readable. No words cut off.' },
    { slide: 2, type: 'PROBLEM', expect: 'Pain point / frustration', check: 'Should agitate a pain point. Text must be legible against background.' },
    { slide: 3, type: 'AGITATION', expect: 'Competition / urgency', check: 'Should create urgency. Visual style must match slide 1.' },
    { slide: 4, type: 'SOLUTION', expect: `${productName} reveal`, check: 'Product name must be spelled correctly and prominent. Style consistent with previous slides.' },
    { slide: 5, type: 'FEATURE', expect: 'Key benefit', check: 'Feature text must be accurate and readable. Visual coherence with other slides.' },
    { slide: 6, type: 'CTA', expect: 'Call to action', check: 'CTA must be clear and prominent. "Link in bio" or similar must be visible.' }
  ];
}

async function main() {
  console.log('═══════════════════════════════════════════════════════════════');
  console.log('🔍 SLIDE REVIEW - Vision Verification');
  console.log('═══════════════════════════════════════════════════════════════\n');
  
  // Load analysis for context
  let analysis = {};
  try {
    analysis = JSON.parse(fs.readFileSync(ANALYSIS_FILE, 'utf8'));
  } catch (e) {
    console.log('⚠️  Could not load analysis.json - review will use generic expectations.\n');
  }
  
  const expectations = getSlideExpectations(analysis);
  const results = [];
  
  for (const exp of expectations) {
    const slidePath = path.join(CAROUSEL_DIR, `slide-${exp.slide}.jpg`);
    
    if (!fs.existsSync(slidePath)) {
      results.push({ ...exp, status: 'MISSING', path: null, sizeMB: 0 });
      console.log(`❌ Slide ${exp.slide} (${exp.type}): FILE MISSING`);
      continue;
    }
    
    const stats = fs.statSync(slidePath);
    const sizeMB = (stats.size / 1024 / 1024).toFixed(2);
    
    // Check basic image validity (non-zero size)
    if (stats.size < 1000) {
      results.push({ ...exp, status: 'CORRUPT', path: slidePath, sizeMB });
      console.log(`❌ Slide ${exp.slide} (${exp.type}): File too small (${sizeMB}MB) - likely corrupt`);
      continue;
    }
    
    results.push({ ...exp, status: 'READY', path: slidePath, sizeMB });
    console.log(`✓  Slide ${exp.slide} (${exp.type}): ${sizeMB}MB - ready for vision review`);
  }
  
  const readySlides = results.filter(r => r.status === 'READY');
  const missingSlides = results.filter(r => r.status !== 'READY');
  
  console.log(`\n📊 Summary: ${readySlides.length}/6 slides ready, ${missingSlides.length} issues\n`);
  
  if (readySlides.length === 0) {
    console.log('❌ No slides available for review. Run generate-slides.sh first.');
    process.exit(1);
  }
  
  // Output instructions for the agent
  console.log('═══════════════════════════════════════════════════════════════');
  console.log('📋 AGENT: Review each slide using your vision model.');
  console.log('   Use view_file or equivalent to see each image and verify:');
  console.log('═══════════════════════════════════════════════════════════════\n');
  
  for (const slide of readySlides) {
    console.log(`📱 Slide ${slide.slide} (${slide.type}): ${slide.path}`);
    console.log(`   Expected: ${slide.expect}`);
    console.log(`   Verify: ${slide.check}`);
    console.log('');
  }
  
  console.log('Checklist for EVERY slide:');
  console.log('  ✓ Text is fully legible (no words cut off at edges)');
  console.log('  ✓ Spelling is correct (especially product name)');
  console.log('  ✓ Visual style is consistent across all slides');
  console.log('  ✓ Image quality is good (not blurry or distorted)');
  console.log('  ✓ Text has enough contrast against background');
  console.log('  ✓ No text in bottom 20% (TikTok controls area)');
  console.log('');
  console.log('If any slide fails, regenerate it with generate-slides.sh');
  
  // Save review data for the agent
  fs.writeFileSync(
    path.join(CAROUSEL_DIR, 'review-pending.json'),
    JSON.stringify({
      timestamp: new Date().toISOString(),
      slides: results,
      instructions: 'Use your vision/image-to-text capability to view each slide image and verify the checklist above.'
    }, null, 2)
  );
  
  console.log(`\n💾 Review data saved to: ${CAROUSEL_DIR}/review-pending.json`);
}

main().catch(console.error);
