/**
 * Unified analytics helper — fires events to GA4, Firebase, and Umami.
 * Include after the GA4/Firebase/Umami scripts in BaseLayout.astro.
 */
window.trackEvent = function trackEvent(eventName, params) {
  try {
    if (typeof gtag === 'function') {
      gtag('event', eventName, params);
    }
    if (typeof window.logFirebaseEvent === 'function') {
      window.logFirebaseEvent(eventName, params);
    }
    // Umami script is defer-loaded so window.umami may not exist on very early events
    if (window.umami && typeof window.umami.track === 'function') {
      window.umami.track(eventName, params);
    }
  } catch (e) {
    // Silently ignore analytics errors
  }
};
