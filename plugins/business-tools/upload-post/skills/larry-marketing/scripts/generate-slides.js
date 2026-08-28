#!/usr/bin/env node
/**
 * Generate 6 TikTok slideshow images using the user's chosen image generation provider.
 * 
 * Supported providers:
 *   - openai (gpt-image-1.5 STRONGLY RECOMMENDED — never use gpt-image-1)
 *   - stability (Stable Diffusion via Stability AI API)
 *   - replicate (any model via Replicate API)
 *   - local (user provides pre-made images, skips generation)
 * 
 * Usage: node generate-slides.js --config <config.json> --output <dir> --prompts <prompts.json>
 * 
 * prompts.json format:
 * {
 *   "base": "Shared base prompt for all slides",
 *   "slides": ["Slide 1 additions", "Slide 2 additions", ...6 total]
 * }
 */

const fs = require('fs');
const path = require('path');

const args = process.argv.slice(2);
function getArg(name) {
  const idx = args.indexOf(`--${name}`);
  return idx !== -1 ? args[idx + 1] : null;
}

const configPath = getArg('config');
const outputDir = getArg('output');
const promptsPath = getArg('prompts');

if (!configPath || !outputDir || !promptsPath) {
  console.error('Usage: node generate-slides.js --config <config.json> --output <dir> --prompts <prompts.json>');
  process.exit(1);
}

const config = JSON.parse(fs.readFileSync(configPath, 'utf-8'));
const prompts = JSON.parse(fs.readFileSync(promptsPath, 'utf-8'));

if (!prompts.slides || prompts.slides.length !== 6) {
  console.error('ERROR: prompts.json must have exactly 6 slides');
  process.exit(1);
}

fs.mkdirSync(outputDir, { recursive: true });

const provider = config.imageGen?.provider || 'openai';
const model = config.imageGen?.model || 'gpt-image-1.5';
const apiKey = config.imageGen?.apiKey;

if (!apiKey && provider !== 'local') {
  console.error(`ERROR: No API key found in config.imageGen.apiKey for provider "${provider}"`);
  process.exit(1);
}

// Warn if using gpt-image-1 instead of 1.5
if (provider === 'openai' && model && !model.includes('1.5')) {
  console.warn(`\n⚠️  WARNING: You're using "${model}" — this produces noticeably AI-looking images.`);
  console.warn(`   STRONGLY RECOMMENDED: Switch to "gpt-image-1.5" in your config for photorealistic results.`);
  console.warn(`   The quality difference is massive and directly impacts views.\n`);
}

// ─── Provider: OpenAI ───────────────────────────────────────────────
async function generateOpenAI(prompt, outPath) {
  const res = await fetch('https://api.openai.com/v1/images/generations', {
    method: 'POST',
    headers: {
      'Authorization': `Bearer ${apiKey}`,
      'Content-Type': 'application/json'
    },
    body: JSON.stringify({
      model,
      prompt,
      n: 1,
      size: '1024x1536',
      quality: 'high'
    }),
    signal: global.__abortSignal
  });
  const data = await res.json();
  if (data.error) throw new Error(data.error.message);
  fs.writeFileSync(outPath, Buffer.from(data.data[0].b64_json, 'base64'));
}

// ─── Provider: Stability AI ─────────────────────────────────────────
async function generateStability(prompt, outPath) {
  const engineId = model || 'stable-diffusion-xl-1024-v1-0';
  const res = await fetch(`https://api.stability.ai/v1/generation/${engineId}/text-to-image`, {
    method: 'POST',
    headers: {
      'Authorization': `Bearer ${apiKey}`,
      'Content-Type': 'application/json',
      'Accept': 'application/json'
    },
    body: JSON.stringify({
      text_prompts: [{ text: prompt, weight: 1 }],
      cfg_scale: 7,
      height: 1536,
      width: 1024,
      steps: 30,
      samples: 1
    })
  });
  const data = await res.json();
  if (data.message) throw new Error(data.message);
  fs.writeFileSync(outPath, Buffer.from(data.artifacts[0].base64, 'base64'));
}

// ─── Provider: Replicate ────────────────────────────────────────────
async function generateReplicate(prompt, outPath) {
  const replicateModel = model || 'black-forest-labs/flux-1.1-pro';
  
  // Create prediction
  const createRes = await fetch('https://api.replicate.com/v1/predictions', {
    method: 'POST',
    headers: {
      'Authorization': `Token ${apiKey}`,
      'Content-Type': 'application/json'
    },
    body: JSON.stringify({
      model: replicateModel,
      input: {
        prompt,
        width: 1024,
        height: 1536,
        num_outputs: 1
      }
    })
  });
  let prediction = await createRes.json();
  if (prediction.error) throw new Error(prediction.error.detail || prediction.error);

  // Poll for completion
  while (prediction.status !== 'succeeded' && prediction.status !== 'failed') {
    await new Promise(r => setTimeout(r, 2000));
    const pollRes = await fetch(prediction.urls.get, {
      headers: { 'Authorization': `Token ${apiKey}` }
    });
    prediction = await pollRes.json();
  }
  if (prediction.status === 'failed') throw new Error(prediction.error || 'Prediction failed');

  // Download image
  const imageUrl = Array.isArray(prediction.output) ? prediction.output[0] : prediction.output;
  const imgRes = await fetch(imageUrl);
  const buf = Buffer.from(await imgRes.arrayBuffer());
  fs.writeFileSync(outPath, buf);
}

// ─── Provider: Local (skip generation) ──────────────────────────────
async function generateLocal(prompt, outPath) {
  const slideNum = path.basename(outPath).match(/\d+/)?.[0];
  const localPath = path.join(outputDir, `local_slide${slideNum}.png`);
  if (fs.existsSync(localPath)) {
    fs.copyFileSync(localPath, outPath);
  } else {
    throw new Error(`Place your image at ${localPath} — local provider skips generation`);
  }
}

// ─── Retry with timeout ─────────────────────────────────────────────
async function withRetry(fn, retries = 2, timeoutMs = 120000) {
  for (let attempt = 0; attempt <= retries; attempt++) {
    try {
      const controller = new AbortController();
      const timer = setTimeout(() => controller.abort(), timeoutMs);
      // Pass abort signal via global (providers use fetch which supports it)
      global.__abortSignal = controller.signal;
      const result = await fn();
      clearTimeout(timer);
      return result;
    } catch (e) {
      if (attempt < retries) {
        const isTimeout = e.name === 'AbortError' || e.message?.includes('timeout') || e.message?.includes('abort');
        console.log(`  ⚠️ ${isTimeout ? 'Timeout' : 'Error'}: ${e.message}. Retrying (${attempt + 1}/${retries})...`);
        await new Promise(r => setTimeout(r, 3000 * (attempt + 1)));
      } else {
        throw e;
      }
    }
  }
}

// ─── Router ─────────────────────────────────────────────────────────
const providers = {
  openai: generateOpenAI,
  stability: generateStability,
  replicate: generateReplicate,
  local: generateLocal
};

async function generate(prompt, outPath) {
  const fn = providers[provider];
  if (!fn) {
    console.error(`Unknown provider: "${provider}". Supported: ${Object.keys(providers).join(', ')}`);
    process.exit(1);
  }
  console.log(`  Generating ${path.basename(outPath)} [${provider}/${model}]...`);
  await withRetry(() => fn(prompt, outPath));
  console.log(`  ✅ ${path.basename(outPath)}`);
}

(async () => {
  console.log(`🎬 Generating 6 slides for ${config.app?.name || 'app'} using ${provider}/${model}\n`);
  let success = 0;
  let skipped = 0;
  for (let i = 0; i < 6; i++) {
    const outPath = path.join(outputDir, `slide${i + 1}_raw.png`);
    // Skip if already exists (resume from partial run)
    if (fs.existsSync(outPath) && fs.statSync(outPath).size > 10000) {
      console.log(`  ⏭ slide${i + 1}_raw.png already exists, skipping`);
      success++;
      skipped++;
      continue;
    }
    const fullPrompt = `${prompts.base}\n\n${prompts.slides[i]}`;
    try {
      await generate(fullPrompt, outPath);
      success++;
    } catch (e) {
      console.error(`  ❌ Slide ${i + 1} failed after retries: ${e.message}`);
      console.error(`     Re-run this script to retry — completed slides will be skipped.`);
    }
  }
  console.log(`\n✨ Generated ${success}/6 slides in ${outputDir}${skipped > 0 ? ` (${skipped} skipped — already existed)` : ''}`);
  if (success < 6) {
    console.error(`\n⚠️  ${6 - success} slides failed. Re-run to retry — completed slides are preserved.`);
    process.exit(1);
  }
})();
