// Strip a webview /source response down to interactable elements + identifying
// attributes. Pure regex, no deps. Caller decides webview-vs-native; this
// assumes the input is webview HTML. Whitelists are sized for raw Appium
// /source responses (no Kobiton-injected bounds/visible attrs); the goal is
// byte reduction for the AI host's context window, not semantic filtering.

const UNUSED_TAG_NAMES = ['head', 'script', 'noscript', 'style']

// Attributes to keep on most elements. Form controls (KEEP_ALL_TAG_NAMES)
// bypass this list and retain all their attributes.
const ATTR_WHITELIST = new Set([
  // Text / identification
  'text', 'value', 'id', 'name', 'class', 'alt', 'title', 'placeholder',
  // Accessibility
  'role', 'aria-label', 'aria-labelledby', 'aria-describedby', 'aria-checked',
  'aria-expanded', 'aria-pressed', 'aria-selected', 'aria-hidden', 'aria-controls',
  // Navigation
  'href', 'url', 'src',
  // Form control state
  'type', 'for', 'disabled', 'readonly', 'checked', 'selected',
  // Test hooks
  'data-testid', 'data-test-id', 'data-qa'
])

// Tags whose attribute set is too varied to enumerate; pass through whole.
const KEEP_ALL_TAG_NAMES = new Set([
  'input', 'select', 'textarea', 'button', 'option', 'label', 'iframe'
])

// Matches an inline base64 image data URI.
const BASE64_IMG_REGEX = /data:image\/[\w+]+;base64/i

function stripPairedTag(source, tag) {
  const re = new RegExp(`<${tag}\\b[^>]*>[\\s\\S]*?<\\/${tag}>`, 'gi')
  return source.replace(re, '')
}

function stripBase64Images(source) {
  const re = /<img\b[^>]*\bsrc=("[^"]*"|'[^']*')[^>]*\/?>/gi
  return source.replace(re, (match, srcAttr) => {
    return BASE64_IMG_REGEX.test(srcAttr) ? '' : match
  })
}

function pruneAttributes(source) {
  // Groups: 1=tag name, 2=raw attribute list, 3=optional self-closing slash.
  const TAG_OPEN = /<([a-zA-Z][\w:-]*)((?:\s+[\w:-]+(?:\s*=\s*(?:"[^"]*"|'[^']*'|[^\s"'<>`]+))?)*)\s*(\/?)>/g
  return source.replace(TAG_OPEN, (full, tag, attrs, selfClose) => {
    if (KEEP_ALL_TAG_NAMES.has(tag.toLowerCase())) return full
    if (!attrs) return full
    const ATTR = /\s+([\w:-]+)(?:\s*=\s*("[^"]*"|'[^']*'|[^\s"'<>`]+))?/g
    let kept = ''
    let m
    while ((m = ATTR.exec(attrs)) !== null) {
      const name = m[1].toLowerCase()
      if (ATTR_WHITELIST.has(name)) {
        kept += m[2] !== undefined ? ` ${m[1]}=${m[2]}` : ` ${m[1]}`
      }
    }
    return `<${tag}${kept}${selfClose ? ' /' : ''}>`
  })
}

export function stripWebviewDom(source) {
  if (typeof source !== 'string' || source.length === 0) return source
  let out = source
  for (const tag of UNUSED_TAG_NAMES) out = stripPairedTag(out, tag)
  out = stripBase64Images(out)
  out = pruneAttributes(out)
  out = out.replace(/>\s+</g, '><')
  return out
}
