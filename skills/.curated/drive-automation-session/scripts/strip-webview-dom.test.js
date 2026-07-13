import {describe, it, expect} from 'vitest'
import {readFileSync} from 'node:fs'
import {fileURLToPath} from 'node:url'
import {dirname, join} from 'node:path'
import {stripWebviewDom} from './strip-webview-dom.js'

const __dirname = dirname(fileURLToPath(import.meta.url))
const FIXTURE = join(__dirname, '__fixtures__', 'webview-mobile-sample.xml')

describe('stripWebviewDom', () => {
  describe('byte reduction floor (synthetic mobile webview fixture)', () => {
    it('shrinks the ~50KB synthetic webview source by at least 80%', () => {
      const src = readFileSync(FIXTURE, 'utf8')
      const out = stripWebviewDom(src)
      const reduction = 1 - out.length / src.length
      expect(reduction).toBeGreaterThanOrEqual(0.8)
    })

    it('finishes in well under one second', () => {
      const src = readFileSync(FIXTURE, 'utf8')
      const t = Date.now()
      stripWebviewDom(src)
      expect(Date.now() - t).toBeLessThan(500)
    })
  })

  describe('strips noise tags wholesale', () => {
    it('removes <script>...</script> blocks including their content', () => {
      const src = '<html><body><script>var x = 1;</script><div>keep</div></body></html>'
      const out = stripWebviewDom(src)
      expect(out).not.toMatch(/<script/i)
      expect(out).not.toContain('var x = 1')
      expect(out).toContain('<div>keep</div>')
    })

    it('removes <style>...</style> blocks', () => {
      const src = '<html><body><style>.a{color:red}</style><div>keep</div></body></html>'
      const out = stripWebviewDom(src)
      expect(out).not.toMatch(/<style/i)
      expect(out).not.toContain('.a{color:red}')
    })

    it('removes the <head>...</head> block', () => {
      const src = '<html><head><title>X</title><meta name="viewport"/></head><body><div>keep</div></body></html>'
      const out = stripWebviewDom(src)
      expect(out).not.toMatch(/<head/i)
      expect(out).not.toContain('<title>')
    })

    it('removes <noscript>...</noscript> blocks', () => {
      const src = '<html><body><noscript>fallback</noscript><div>keep</div></body></html>'
      const out = stripWebviewDom(src)
      expect(out).not.toMatch(/<noscript/i)
      expect(out).not.toContain('fallback')
    })
  })

  describe('strips inline base64 images', () => {
    it('removes <img src="data:image/png;base64,...">', () => {
      const src = '<html><body><img src="data:image/png;base64,AAAA" alt="x"/><img src="/cdn/logo.png" alt="y"/></body></html>'
      const out = stripWebviewDom(src)
      expect(out).not.toContain('base64')
      expect(out).toContain('/cdn/logo.png')
    })
  })

  describe('attribute pruning', () => {
    it('drops attributes outside the whitelist on generic elements', () => {
      const src = '<html><body><div jsdata="abc" class="hd" data-context="xyz" id="root">x</div></body></html>'
      const out = stripWebviewDom(src)
      expect(out).not.toContain('jsdata=')
      expect(out).not.toContain('data-context=')
      expect(out).toContain('class="hd"')
      expect(out).toContain('id="root"')
    })

    it('keeps aria-label and role on buttons (via attribute whitelist, before KEEP_ALL passthrough)', () => {
      const src = '<html><body><div role="button" aria-label="Search YouTube" jsdata="x">icon</div></body></html>'
      const out = stripWebviewDom(src)
      expect(out).toContain('role="button"')
      expect(out).toContain('aria-label="Search YouTube"')
      expect(out).not.toContain('jsdata=')
    })

    it('keeps href on anchor tags', () => {
      const src = '<html><body><a href="/watch?v=abc123" jsdata="x">title</a></body></html>'
      const out = stripWebviewDom(src)
      expect(out).toContain('href="/watch?v=abc123"')
      expect(out).not.toContain('jsdata=')
    })

    it('keeps data-testid', () => {
      const src = '<html><body><div data-testid="search-result-1" tracking="abc">x</div></body></html>'
      const out = stripWebviewDom(src)
      expect(out).toContain('data-testid="search-result-1"')
      expect(out).not.toContain('tracking=')
    })

    it('passes through all attributes on form controls (KEEP_ALL_TAG_NAMES)', () => {
      const src = '<html><body><input type="search" name="search_query" placeholder="Search" jsdata="x" tabindex="0" autocomplete="off"/></body></html>'
      const out = stripWebviewDom(src)
      // KEEP_ALL bypasses the whitelist, so even non-whitelisted attrs like
      // tabindex and autocomplete survive on form controls.
      expect(out).toContain('type="search"')
      expect(out).toContain('name="search_query"')
      expect(out).toContain('placeholder="Search"')
      expect(out).toContain('jsdata="x"')
      expect(out).toContain('tabindex="0"')
      expect(out).toContain('autocomplete="off"')
    })
  })

  describe('edge cases', () => {
    it('returns empty string unchanged', () => {
      expect(stripWebviewDom('')).toBe('')
    })

    it('returns non-string input unchanged', () => {
      expect(stripWebviewDom(null)).toBe(null)
      expect(stripWebviewDom(undefined)).toBe(undefined)
    })
  })
})
