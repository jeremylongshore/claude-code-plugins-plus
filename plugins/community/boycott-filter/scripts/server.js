#!/usr/bin/env node
/**
 * Boycott Filter — Local sync server
 *
 * Tiny HTTP server that serves the boycott list to the Chrome extension.
 * Claude Code writes to boycott-list.json, this serves it with CORS.
 *
 * Port 7847 (BOYCOTT on a phone keypad, close enough)
 */

import { createServer } from 'http';
import { readFileSync, writeFileSync } from 'fs';
import { join, dirname } from 'path';
import { fileURLToPath } from 'url';

const __dirname = dirname(fileURLToPath(import.meta.url));
const LIST_FILE = join(__dirname, '..', 'boycott-list.json');
const PORT = 7847;

function readList() {
  try {
    return JSON.parse(readFileSync(LIST_FILE, 'utf8'));
  } catch {
    return { companies: [], updated_at: null };
  }
}

function writeList(data) {
  data.updated_at = new Date().toISOString();
  writeFileSync(LIST_FILE, JSON.stringify(data, null, 2));
  return data;
}

const server = createServer((req, res) => {
  res.setHeader('Access-Control-Allow-Origin', '*');
  res.setHeader('Access-Control-Allow-Methods', 'GET, POST, DELETE, OPTIONS');
  res.setHeader('Access-Control-Allow-Headers', 'Content-Type');

  if (req.method === 'OPTIONS') {
    res.writeHead(204);
    res.end();
    return;
  }

  res.setHeader('Content-Type', 'application/json');

  if (req.method === 'GET' && req.url === '/list') {
    res.writeHead(200);
    res.end(JSON.stringify(readList()));
    return;
  }

  if (req.method === 'POST' && req.url === '/add') {
    let body = '';
    req.on('data', chunk => body += chunk);
    req.on('end', () => {
      try {
        const { name, reason, aliases } = JSON.parse(body);
        if (!name) {
          res.writeHead(400);
          res.end(JSON.stringify({ error: 'name required' }));
          return;
        }
        const list = readList();
        const existing = list.companies.find(c => c.name.toLowerCase() === name.toLowerCase());
        if (existing) {
          res.writeHead(409);
          res.end(JSON.stringify({ error: 'already boycotted', company: existing }));
          return;
        }
        list.companies.push({
          name,
          reason: reason || null,
          aliases: aliases || [],
          added_at: new Date().toISOString()
        });
        const updated = writeList(list);
        res.writeHead(201);
        res.end(JSON.stringify({ ok: true, list: updated }));
      } catch (e) {
        res.writeHead(400);
        res.end(JSON.stringify({ error: 'invalid JSON' }));
      }
    });
    return;
  }

  if (req.method === 'DELETE' && req.url === '/remove') {
    let body = '';
    req.on('data', chunk => body += chunk);
    req.on('end', () => {
      try {
        const { name } = JSON.parse(body);
        const list = readList();
        const before = list.companies.length;
        list.companies = list.companies.filter(c => c.name.toLowerCase() !== name.toLowerCase());
        if (list.companies.length === before) {
          res.writeHead(404);
          res.end(JSON.stringify({ error: 'not found' }));
          return;
        }
        const updated = writeList(list);
        res.writeHead(200);
        res.end(JSON.stringify({ ok: true, list: updated }));
      } catch (e) {
        res.writeHead(400);
        res.end(JSON.stringify({ error: 'invalid JSON' }));
      }
    });
    return;
  }

  if (req.method === 'GET' && req.url === '/health') {
    res.writeHead(200);
    res.end(JSON.stringify({ status: 'ok', companies: readList().companies.length }));
    return;
  }

  res.writeHead(404);
  res.end(JSON.stringify({ error: 'not found' }));
});

server.listen(PORT, '127.0.0.1', () => {
  console.log(`Boycott Filter server running on http://127.0.0.1:${PORT}`);
  console.log(`List file: ${LIST_FILE}`);
});
