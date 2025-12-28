/**
 * BackstopJS Configuration File
 *
 * This is an example configuration file for BackstopJS.  Customize it to fit your project's needs.
 *
 * For detailed documentation, visit: https://github.com/garris/BackstopJS
 */

module.exports = {
  id: 'my-project', // A unique ID for your project, used for report naming.  Change this!

  viewports: [
    {
      label: 'desktop',
      width: 1920,
      height: 1080,
    },
    {
      label: 'mobile',
      width: 320,
      height: 480,
    },
  ],

  onBeforeScript: 'puppet/onBefore.js',
  onReadyScript: 'puppet/onReady.js',

  scenarios: [
    {
      label: 'Example Homepage', // A descriptive label for this scenario
      url: 'https://example.com', // The URL to test
      referenceUrl: '', // Optional: URL for the baseline/reference screenshots.  Leave empty for first run.
      readyEvent: '', // Optional: Wait for a specific event to fire before taking the screenshot.
      readySelector: '', // Optional: Wait for a specific selector to be present before taking the screenshot.
      delay: 0, // Optional: Wait for a specified number of milliseconds before taking the screenshot. Useful for animations.
      hideSelectors: [], // Optional: Hide elements before taking the screenshot.  Useful for dynamic content.
      removeSelectors: [], // Optional: Remove elements before taking the screenshot.  Useful for dynamic content.
      selectorExpansion: true, // Optional: Expand selectors to include all matching elements.
      selectors: [
        'document', // Take a screenshot of the entire document
      ],
      misMatchThreshold: 0.1, // Percentage of acceptable pixel difference between the baseline and the test screenshot.
      requireSameDimensions: true, // Ensure that the baseline and test screenshots have the same dimensions.
    },
    // Add more scenarios here to test different pages and components.
    // Example:
    // {
    //   label: 'Example Contact Page',
    //   url: 'https://example.com/contact',
    //   selectors: [
    //     '.contact-form',
    //   ],
    // },
  ],

  paths: {
    bitmaps_reference: 'backstop_data/bitmaps_reference',
    bitmaps_test: 'backstop_data/bitmaps_test',
    html_report: 'backstop_data/html_report',
    ci_report: 'backstop_data/ci_report',
  },

  report: ['browser'], // Generate a browser-based HTML report.
  engine: 'puppeteer', // Use Puppeteer as the browser automation engine.
  engineOptions: {
    args: ['--no-sandbox'], // Required for running Puppeteer in some environments (e.g., Docker).
  },
  asyncCaptureLimit: 5, // Limit the number of concurrent screenshots to avoid overloading the system.
  asyncCompareLimit: 50, // Limit the number of concurrent comparisons to avoid overloading the system.
  debug: false, // Enable debug mode for more verbose logging.
  debugWindow: false, // Open the browser window in debug mode.
};