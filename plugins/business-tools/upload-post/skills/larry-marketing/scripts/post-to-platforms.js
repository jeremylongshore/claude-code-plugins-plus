#!/usr/bin/env node
/**
 * Post a slideshow to TikTok + Instagram via Upload-Post API.
 * 
 * Usage: node post-to-platforms.js --config <config.json> --dir <slides-dir> --caption "caption text" [--title "post title"]
 * 
 * Uploads slide images as a photo carousel to both TikTok and Instagram simultaneously
 * using a single Upload-Post API call. Uses async_upload=true for background processing.
 * 
 * The returned request_id is stored in meta.json for analytics tracking.
 * Upload-Post tracks posts automatically by request_id — no manual video-ID linking needed.
 */

const fs = require('fs');
const path = require('path');

const args = process.argv.slice(2);
function getArg(name) {
  const idx = args.indexOf(`--${name}`);
  return idx !== -1 ? args[idx + 1] : null;
}

const configPath = getArg('config');
const dir = getArg('dir');
const caption = getArg('caption');
const title = getArg('title') || '';

if (!configPath || !dir || !caption) {
  console.error('Usage: node post-to-platforms.js --config <config.json> --dir <dir> --caption "text" [--title "text"]');
  process.exit(1);
}

const config = JSON.parse(fs.readFileSync(configPath, 'utf-8'));

const BASE_URL = 'https://api.upload-post.com/api';
const API_KEY = config.uploadPost?.apiKey;
const PROFILE = config.uploadPost?.profile || 'upload_post';
const PLATFORMS = config.uploadPost?.platforms || ['tiktok', 'instagram'];

if (!API_KEY) {
  console.error('❌ Missing uploadPost.apiKey in config');
  process.exit(1);
}

(async () => {
  // Find all slide images in the directory (slide1.png through slide6.png or more)
  const slideFiles = [];
  for (let i = 1; i <= 35; i++) {
    const pngPath = path.join(dir, `slide${i}.png`);
    const jpgPath = path.join(dir, `slide${i}.jpg`);
    if (fs.existsSync(pngPath)) {
      slideFiles.push(pngPath);
    } else if (fs.existsSync(jpgPath)) {
      slideFiles.push(jpgPath);
    } else {
      break; // Stop at the first missing slide
    }
  }

  if (slideFiles.length === 0) {
    console.error('❌ No slide images found in', dir);
    console.error('   Expected: slide1.png, slide2.png, ... or slide1.jpg, slide2.jpg, ...');
    process.exit(1);
  }

  console.log(`📤 Uploading ${slideFiles.length} slides to ${PLATFORMS.join(' + ')}...`);
  console.log(`   Profile: ${PROFILE}`);
  console.log(`   Caption: ${caption.substring(0, 60)}...`);
  if (title) console.log(`   Title: ${title}`);

  // Build multipart form data
  const form = new FormData();
  form.append('user', PROFILE);
  form.append('title', caption);
  form.append('async_upload', 'true');

  // Add each platform
  for (const platform of PLATFORMS) {
    form.append('platform[]', platform);
  }

  // Add each slide image
  for (const filePath of slideFiles) {
    const fileBuffer = fs.readFileSync(filePath);
    const ext = path.extname(filePath).toLowerCase();
    const mimeType = ext === '.jpg' || ext === '.jpeg' ? 'image/jpeg' : 'image/png';
    const blob = new Blob([fileBuffer], { type: mimeType });
    form.append('photos[]', blob, path.basename(filePath));
    console.log(`   📎 ${path.basename(filePath)}`);
  }

  // Make the API call
  console.log('\n📱 Sending to Upload-Post...');
  
  try {
    const res = await fetch(`${BASE_URL}/upload_photos`, {
      method: 'POST',
      headers: {
        'Authorization': `Apikey ${API_KEY}`
      },
      body: form
    });

    const responseText = await res.text();
    let result;
    try {
      result = JSON.parse(responseText);
    } catch (e) {
      console.error(`❌ Non-JSON response (HTTP ${res.status}):`, responseText.substring(0, 500));
      process.exit(1);
    }

    if (!res.ok) {
      console.error(`❌ Upload failed (HTTP ${res.status}):`, JSON.stringify(result, null, 2));
      process.exit(1);
    }

    const requestId = result.request_id || result.requestId || null;

    console.log('✅ Upload submitted!');
    console.log(`   Request ID: ${requestId}`);
    console.log(`   Platforms: ${PLATFORMS.join(', ')}`);
    if (result.message) console.log(`   Message: ${result.message}`);

    // Save metadata for analytics tracking
    const metaPath = path.join(dir, 'meta.json');
    const meta = {
      requestId,
      caption,
      title,
      platforms: PLATFORMS,
      profile: PROFILE,
      postedAt: new Date().toISOString(),
      slides: slideFiles.length,
      asyncUpload: true
    };
    fs.writeFileSync(metaPath, JSON.stringify(meta, null, 2));
    console.log(`📋 Metadata saved to ${metaPath}`);

    // If async, show how to check status
    if (requestId) {
      console.log(`\n💡 Check status with:`);
      console.log(`   curl -H "Authorization: Apikey <key>" "${BASE_URL}/uploadposts/status?request_id=${requestId}"`);
    }

  } catch (err) {
    console.error('❌ Network error:', err.message);
    process.exit(1);
  }
})();
