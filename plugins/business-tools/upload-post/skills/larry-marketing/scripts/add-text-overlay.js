#!/usr/bin/env node
/**
 * Add text overlays to slideshow images using node-canvas.
 * 
 * Usage: node add-text-overlay.js --input <dir> --texts <texts.json>
 * 
 * texts.json format:
 * [
 *   "Slide 1 text with manual\nline breaks preferred",
 *   "Slide 2 text",
 *   ... 6 total
 * ]
 * 
 * TEXT RULES:
 * - Use \n for manual line breaks (PREFERRED — gives you control)
 * - If no \n provided, the script auto-wraps to fit within maxWidth
 * - Keep lines to 4-6 words max for readability
 * - Text is REACTIONS not labels ("Wait... this is nice??" not "Modern style")
 * - No emoji (canvas can't render them)
 * 
 * Reads slide1_raw.png through slide6_raw.png (or slide_1.png etc)
 * Outputs slide1.png through slide6.png (or final_1.png etc)
 */

const { createCanvas, loadImage } = require('canvas');
const fs = require('fs');
const path = require('path');

const args = process.argv.slice(2);
function getArg(name) {
  const idx = args.indexOf(`--${name}`);
  return idx !== -1 ? args[idx + 1] : null;
}

const inputDir = getArg('input');
const textsPath = getArg('texts');

if (!inputDir || !textsPath) {
  console.error('Usage: node add-text-overlay.js --input <dir> --texts <texts.json>');
  process.exit(1);
}

const texts = JSON.parse(fs.readFileSync(textsPath, 'utf-8'));
if (texts.length !== 6) {
  console.error('ERROR: texts.json must have exactly 6 entries');
  process.exit(1);
}

/**
 * Word-wrap text to fit within maxWidth.
 * If the text already contains \n, splits on those first,
 * then wraps any lines that are still too wide.
 */
function wrapText(ctx, text, maxWidth) {
  // Strip emoji (canvas can't render them reliably)
  const cleanText = text.replace(/[\u{1F300}-\u{1FAFF}\u{2600}-\u{27BF}]/gu, '').trim();
  
  // Split on manual line breaks first
  const manualLines = cleanText.split('\n');
  const wrappedLines = [];

  for (const line of manualLines) {
    // Check if this line fits as-is
    if (ctx.measureText(line.trim()).width <= maxWidth) {
      wrappedLines.push(line.trim());
      continue;
    }

    // Auto-wrap: split into words, build lines that fit
    const words = line.trim().split(/\s+/);
    let currentLine = '';

    for (const word of words) {
      const testLine = currentLine ? `${currentLine} ${word}` : word;
      if (ctx.measureText(testLine).width <= maxWidth) {
        currentLine = testLine;
      } else {
        if (currentLine) wrappedLines.push(currentLine);
        currentLine = word;
      }
    }
    if (currentLine) wrappedLines.push(currentLine);
  }

  return wrappedLines;
}

async function addTextOverlay(imgPath, text, outPath) {
  const img = await loadImage(imgPath);
  const canvas = createCanvas(img.width, img.height);
  const ctx = canvas.getContext('2d');
  ctx.drawImage(img, 0, 0);

  // ─── Text settings (match our proven viral format) ───
  const fontSize = Math.round(img.width * 0.065);   // 6.5% of image width (~66px on 1024w)
  const outlineWidth = Math.round(fontSize * 0.15);  // 15% of font size for thick outline
  const maxWidth = img.width * 0.75;                  // 75% of image width (padding for TikTok UI)
  const lineHeight = fontSize * 1.25;                 // 125% line height for readability

  ctx.font = `bold ${fontSize}px Arial`;
  ctx.textAlign = 'center';
  ctx.textBaseline = 'top';

  // Wrap text to fit within maxWidth
  const lines = wrapText(ctx, text, maxWidth);

  // Calculate vertical position
  // Center the text block at 30% from top
  const totalTextHeight = lines.length * lineHeight;
  const startY = (img.height * 0.30) - (totalTextHeight / 2) + (lineHeight / 2);

  // Ensure text stays in safe zones (not top 10%, not bottom 20%)
  const minY = img.height * 0.10;
  const maxY = img.height * 0.80 - totalTextHeight;
  const safeY = Math.max(minY, Math.min(startY, maxY));

  const x = img.width / 2; // Center horizontally

  for (let i = 0; i < lines.length; i++) {
    const y = safeY + (i * lineHeight);

    // Black outline (stroke first, then fill on top)
    ctx.strokeStyle = '#000000';
    ctx.lineWidth = outlineWidth;
    ctx.lineJoin = 'round';
    ctx.miterLimit = 2;
    ctx.strokeText(lines[i], x, y);

    // White fill
    ctx.fillStyle = '#FFFFFF';
    ctx.fillText(lines[i], x, y);
  }

  fs.writeFileSync(outPath, canvas.toBuffer('image/png'));

  // Log the actual text layout for debugging
  console.log(`  ✅ ${path.basename(outPath)} — ${lines.length} lines:`);
  lines.forEach(l => console.log(`     "${l}"`));
}

// Find input files (supports multiple naming conventions)
function findSlideFile(dir, num) {
  const candidates = [
    `slide${num}_raw.png`,
    `slide_${num}.png`,
    `slide${num}.png`,
    `raw_${num}.png`,
    `${num}.png`
  ];
  for (const name of candidates) {
    const p = path.join(dir, name);
    if (fs.existsSync(p)) return p;
  }
  return null;
}

function outputName(dir, num, inputName) {
  // If input is slide1_raw.png → output slide1.png
  // If input is slide_1.png → output final_1.png
  if (inputName.includes('_raw')) {
    return path.join(dir, inputName.replace('_raw', ''));
  }
  if (inputName.startsWith('slide_')) {
    return path.join(dir, `final_${num}.png`);
  }
  return path.join(dir, `slide${num}_final.png`);
}

(async () => {
  console.log('📝 Adding text overlays...\n');
  console.log('Settings:');
  console.log('  Font size: 6.5% of image width');
  console.log('  Position: centered at ~30% from top');
  console.log('  Max width: 75% of image');
  console.log('  Style: white fill, black outline\n');

  let success = 0;
  for (let i = 0; i < 6; i++) {
    const num = i + 1;
    const inputFile = findSlideFile(inputDir, num);
    if (!inputFile) {
      console.error(`  ❌ Slide ${num}: no input file found in ${inputDir}`);
      continue;
    }
    const outPath = outputName(inputDir, num, path.basename(inputFile));
    await addTextOverlay(inputFile, texts[i], outPath);
    success++;
  }

  console.log(`\n✨ ${success}/6 overlays complete!`);
  if (success < 6) process.exit(1);
})();
