#!/usr/bin/env node
/**
 * Fix empty email fields in plugin JSON files
 * Removes email field if it's empty
 */

import fs from 'fs';
import path from 'path';
import { fileURLToPath } from 'url';

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);

const contentDir = path.join(__dirname, 'src', 'content', 'plugins');
const files = fs.readdirSync(contentDir).filter(f => f.endsWith('.json'));

let fixed = 0;

files.forEach(file => {
  const filepath = path.join(contentDir, file);
  const content = JSON.parse(fs.readFileSync(filepath, 'utf8'));

  if (content.author && content.author.email === '[email protected]') {
    // Remove empty email field
    delete content.author.email;

    // Remove empty url field if present
    if (content.author.url === '') {
      delete content.author.url;
    }

    // Write back
    fs.writeFileSync(filepath, JSON.stringify(content, null, 2));
    fixed++;
  }
});

console.log(`Fixed ${fixed} files with empty email fields`);