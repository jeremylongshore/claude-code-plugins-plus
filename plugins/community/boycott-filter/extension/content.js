/**
 * Boycott Filter — Content Script
 *
 * Scans page text for boycotted company names.
 * Shows a warning banner at the top of the page when matches found.
 */

const BANNER_ID = 'boycott-filter-banner';

// Build search terms from company list
function getSearchTerms(companies) {
  const terms = [];
  for (const company of companies) {
    terms.push({ term: company.name, company });
    if (company.aliases) {
      for (const alias of company.aliases) {
        terms.push({ term: alias, company });
      }
    }
  }
  return terms;
}

// Scan page for matches
function scanPage(companies) {
  if (!companies || companies.length === 0) return [];

  const searchTerms = getSearchTerms(companies);
  const pageText = document.body?.innerText?.toLowerCase() || '';
  const pageTitle = document.title?.toLowerCase() || '';
  const url = window.location.href.toLowerCase();

  const matched = new Map(); // company name -> company object

  for (const { term, company } of searchTerms) {
    const lower = term.toLowerCase();
    // Check URL, title, and page body
    if (url.includes(lower) || pageTitle.includes(lower) || pageText.includes(lower)) {
      if (!matched.has(company.name)) {
        matched.set(company.name, company);
      }
    }
  }

  return Array.from(matched.values());
}

// Show or hide the warning banner
function showBanner(matches) {
  // Remove existing banner
  const existing = document.getElementById(BANNER_ID);
  if (existing) existing.remove();

  if (matches.length === 0) return;

  const banner = document.createElement('div');
  banner.id = BANNER_ID;

  const names = matches.map(m => m.name).join(', ');
  const reasons = matches
    .filter(m => m.reason)
    .map(m => `<span class="boycott-reason"><strong>${m.name}:</strong> ${m.reason}</span>`)
    .join(' · ');

  banner.innerHTML = `
    <div class="boycott-banner-content">
      <div class="boycott-banner-icon">⛔</div>
      <div class="boycott-banner-text">
        <div class="boycott-banner-title">Boycott Alert — ${names}</div>
        ${reasons ? `<div class="boycott-banner-reasons">${reasons}</div>` : ''}
      </div>
      <button class="boycott-banner-close" id="boycott-close-btn">✕</button>
    </div>
  `;

  document.body.prepend(banner);

  // Push page content down
  document.body.style.marginTop = (banner.offsetHeight) + 'px';

  document.getElementById('boycott-close-btn').addEventListener('click', () => {
    banner.remove();
    document.body.style.marginTop = '';
  });
}

// Main scan logic
async function run() {
  const stored = await chrome.storage.local.get('boycottList');
  const companies = stored?.boycottList?.companies || [];

  const matches = scanPage(companies);

  // Report to background for badge
  chrome.runtime.sendMessage({ type: 'MATCH_REPORT', matches });

  // Show banner
  showBanner(matches);
}

// Listen for list updates from background
chrome.runtime.onMessage.addListener((msg) => {
  if (msg.type === 'LIST_UPDATED') {
    run();
  }
});

// Run on page load (with a small delay for SPAs)
run();

// Re-scan on major DOM changes (SPA navigation)
let scanTimeout;
const observer = new MutationObserver(() => {
  clearTimeout(scanTimeout);
  scanTimeout = setTimeout(run, 2000);
});

observer.observe(document.body || document.documentElement, {
  childList: true,
  subtree: true
});
