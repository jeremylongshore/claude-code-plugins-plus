/**
 * Unified analytics helper — fires events to both GA4 (gtag) and Firebase.
 * Include after the GA4/Firebase scripts in BaseLayout.astro.
 */
window.trackEvent = function trackEvent(eventName, params) {
  try {
    if (typeof gtag === 'function') {
      gtag('event', eventName, params);
    }
    if (typeof window.logFirebaseEvent === 'function') {
      window.logFirebaseEvent(eventName, params);
    }
  } catch (e) {
    // Silently ignore analytics errors
  }
};
