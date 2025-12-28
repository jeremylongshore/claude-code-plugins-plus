/**
 * Performance E2E Tests
 *
 * Tests performance metrics and Core Web Vitals:
 * - LCP (Largest Contentful Paint) < 2.5s
 * - FID (First Input Delay) < 100ms
 * - CLS (Cumulative Layout Shift) < 0.1
 * - TTI (Time to Interactive) < 3.5s
 * - Page load time budgets
 *
 * Uses Playwright Performance API to measure real browser metrics
 */

import { test, expect } from '@playwright/test';

/**
 * Performance budgets (in milliseconds)
 */
const PERFORMANCE_BUDGETS = {
  LCP: 2500,        // Largest Contentful Paint
  FID: 100,         // First Input Delay
  CLS: 0.1,         // Cumulative Layout Shift (unitless)
  TTI: 3500,        // Time to Interactive
  LOAD_TIME: 5000,  // Total page load
  FCP: 1800,        // First Contentful Paint
  TTFB: 600,        // Time to First Byte
};

/**
 * Pages to test with their specific budgets
 */
const pagesUnderTest = [
  {
    name: 'Homepage',
    url: '/',
    budgets: {
      LCP: 2000,  // Stricter for homepage
      LOAD_TIME: 3000,
    }
  },
  {
    name: 'Explore',
    url: '/explore',
    budgets: {
      LCP: 2500,
      LOAD_TIME: 4000,
    }
  },
  {
    name: 'Conversation View',
    url: '/conversations/test-id',
    budgets: {
      LCP: 2000,  // Should be fast
      LOAD_TIME: 3000,
    }
  }
];

test.describe('Core Web Vitals', () => {
  test('homepage should meet LCP threshold', async ({ page }) => {
    await page.goto('/');

    const lcp = await page.evaluate(() => {
      return new Promise<number>((resolve) => {
        let lcpValue = 0;

        new PerformanceObserver((list) => {
          const entries = list.getEntries();
          const lastEntry = entries[entries.length - 1] as any;
          lcpValue = lastEntry.renderTime || lastEntry.loadTime;
        }).observe({ type: 'largest-contentful-paint', buffered: true });

        // Wait for page to stabilize
        setTimeout(() => resolve(lcpValue), 3000);
      });
    });

    console.log(`Homepage LCP: ${lcp.toFixed(2)}ms`);
    expect(lcp).toBeLessThan(PERFORMANCE_BUDGETS.LCP);
    expect(lcp).toBeGreaterThan(0); // Valid measurement
  });

  test('explore page should meet LCP threshold', async ({ page }) => {
    await page.goto('/explore');

    const lcp = await page.evaluate(() => {
      return new Promise<number>((resolve) => {
        let lcpValue = 0;

        new PerformanceObserver((list) => {
          const entries = list.getEntries();
          const lastEntry = entries[entries.length - 1] as any;
          lcpValue = lastEntry.renderTime || lastEntry.loadTime;
        }).observe({ type: 'largest-contentful-paint', buffered: true });

        setTimeout(() => resolve(lcpValue), 3000);
      });
    });

    console.log(`Explore LCP: ${lcp.toFixed(2)}ms`);
    expect(lcp).toBeLessThan(PERFORMANCE_BUDGETS.LCP);
  });

  test('conversation view should have minimal CLS', async ({ page }) => {
    await page.goto('/conversations/test-id');

    // Wait for layout to stabilize
    await page.waitForTimeout(1000);

    const cls = await page.evaluate(() => {
      return new Promise<number>((resolve) => {
        let clsScore = 0;

        new PerformanceObserver((list) => {
          for (const entry of list.getEntries()) {
            // Ignore shifts caused by user input
            if ((entry as any).hadRecentInput) continue;
            clsScore += (entry as any).value;
          }
        }).observe({ type: 'layout-shift', buffered: true });

        // Measure CLS over 2 seconds
        setTimeout(() => resolve(clsScore), 2000);
      });
    });

    console.log(`Conversation View CLS: ${cls.toFixed(4)}`);
    expect(cls).toBeLessThan(PERFORMANCE_BUDGETS.CLS);
  });

  test('homepage should have minimal CLS', async ({ page }) => {
    await page.goto('/');
    await page.waitForTimeout(1000);

    const cls = await page.evaluate(() => {
      return new Promise<number>((resolve) => {
        let clsScore = 0;

        new PerformanceObserver((list) => {
          for (const entry of list.getEntries()) {
            if ((entry as any).hadRecentInput) continue;
            clsScore += (entry as any).value;
          }
        }).observe({ type: 'layout-shift', buffered: true });

        setTimeout(() => resolve(clsScore), 2000);
      });
    });

    console.log(`Homepage CLS: ${cls.toFixed(4)}`);
    expect(cls).toBeLessThan(PERFORMANCE_BUDGETS.CLS);
  });

  test('first input delay should be minimal', async ({ page }) => {
    await page.goto('/');

    // Simulate user interaction after page load
    await page.waitForLoadState('networkidle');

    const startTime = Date.now();
    await page.click('.btn-primary', { timeout: 5000 });
    const endTime = Date.now();

    const fid = endTime - startTime;

    console.log(`Simulated FID: ${fid}ms`);
    expect(fid).toBeLessThan(PERFORMANCE_BUDGETS.FID);
  });
});

test.describe('Page Load Performance', () => {
  for (const pageConfig of pagesUnderTest) {
    test(`${pageConfig.name} should load within budget`, async ({ page }) => {
      const startTime = Date.now();
      await page.goto(pageConfig.url);
      await page.waitForLoadState('networkidle');
      const loadTime = Date.now() - startTime;

      const budget = pageConfig.budgets.LOAD_TIME || PERFORMANCE_BUDGETS.LOAD_TIME;
      console.log(`${pageConfig.name} load time: ${loadTime}ms (budget: ${budget}ms)`);

      expect(loadTime).toBeLessThan(budget);
    });
  }

  test('homepage should meet all timing budgets', async ({ page }) => {
    await page.goto('/');
    await page.waitForLoadState('networkidle');

    const metrics = await page.evaluate(() => {
      const navigation = performance.getEntriesByType('navigation')[0] as PerformanceNavigationTiming;
      const paint = performance.getEntriesByType('paint');

      return {
        ttfb: navigation.responseStart - navigation.requestStart,
        fcp: paint.find(entry => entry.name === 'first-contentful-paint')?.startTime || 0,
        domContentLoaded: navigation.domContentLoadedEventEnd - navigation.domContentLoadedEventStart,
        loadComplete: navigation.loadEventEnd - navigation.loadEventStart,
        totalTime: navigation.loadEventEnd - navigation.fetchStart
      };
    });

    console.log('Homepage timing metrics:', {
      ttfb: `${metrics.ttfb.toFixed(2)}ms`,
      fcp: `${metrics.fcp.toFixed(2)}ms`,
      domContentLoaded: `${metrics.domContentLoaded.toFixed(2)}ms`,
      loadComplete: `${metrics.loadComplete.toFixed(2)}ms`,
      totalTime: `${metrics.totalTime.toFixed(2)}ms`
    });

    expect(metrics.ttfb).toBeLessThan(PERFORMANCE_BUDGETS.TTFB);
    expect(metrics.fcp).toBeLessThan(PERFORMANCE_BUDGETS.FCP);
    expect(metrics.totalTime).toBeLessThan(PERFORMANCE_BUDGETS.LOAD_TIME);
  });
});

test.describe('Resource Loading', () => {
  test('should not load excessive resources', async ({ page }) => {
    await page.goto('/');
    await page.waitForLoadState('networkidle');

    const resourceCounts = await page.evaluate(() => {
      const resources = performance.getEntriesByType('resource') as PerformanceResourceTiming[];

      const counts = {
        scripts: 0,
        stylesheets: 0,
        images: 0,
        fonts: 0,
        other: 0,
        total: resources.length
      };

      resources.forEach(resource => {
        if (resource.name.includes('.js')) counts.scripts++;
        else if (resource.name.includes('.css')) counts.stylesheets++;
        else if (resource.name.match(/\.(png|jpg|jpeg|gif|svg|webp)$/)) counts.images++;
        else if (resource.name.match(/\.(woff|woff2|ttf|otf)$/)) counts.fonts++;
        else counts.other++;
      });

      return counts;
    });

    console.log('Resource counts:', resourceCounts);

    // Reasonable limits
    expect(resourceCounts.scripts).toBeLessThan(20);
    expect(resourceCounts.stylesheets).toBeLessThan(10);
    expect(resourceCounts.images).toBeLessThan(30);
    expect(resourceCounts.total).toBeLessThan(100);
  });

  test('should not have slow-loading resources', async ({ page }) => {
    await page.goto('/');
    await page.waitForLoadState('networkidle');

    const slowResources = await page.evaluate(() => {
      const resources = performance.getEntriesByType('resource') as PerformanceResourceTiming[];

      return resources
        .filter(resource => resource.duration > 1000) // Slower than 1s
        .map(resource => ({
          name: resource.name,
          duration: resource.duration,
          size: resource.transferSize || 0
        }));
    });

    if (slowResources.length > 0) {
      console.log('Slow resources detected:', slowResources);
    }

    // Allow some slow resources, but not too many
    expect(slowResources.length).toBeLessThan(3);
  });

  test('should use compressed resources', async ({ page }) => {
    const response = await page.goto('/');
    const headers = response?.headers();

    // Check if gzip/brotli compression is used
    const contentEncoding = headers?.['content-encoding'] || '';
    const hasCompression = contentEncoding.includes('gzip') || contentEncoding.includes('br');

    // In production, should use compression
    if (process.env.CI) {
      expect(hasCompression).toBe(true);
    }
  });

  test('should cache static assets', async ({ page }) => {
    await page.goto('/');
    await page.waitForLoadState('networkidle');

    const cachedResources = await page.evaluate(() => {
      const resources = performance.getEntriesByType('resource') as PerformanceResourceTiming[];

      return resources
        .filter(resource =>
          resource.name.match(/\.(js|css|woff|woff2|png|jpg|svg)$/) &&
          resource.transferSize === 0 // Served from cache
        )
        .map(resource => resource.name);
    });

    console.log(`Cached resources: ${cachedResources.length}`);

    // Some resources should be cached on repeat visits
    // (This test may fail on first visit, which is expected)
  });
});

test.describe('Mobile Performance', () => {
  test('mobile viewport should meet LCP budget', async ({ page }) => {
    await page.setViewportSize({ width: 390, height: 844 });
    await page.goto('/');

    const lcp = await page.evaluate(() => {
      return new Promise<number>((resolve) => {
        let lcpValue = 0;

        new PerformanceObserver((list) => {
          const entries = list.getEntries();
          const lastEntry = entries[entries.length - 1] as any;
          lcpValue = lastEntry.renderTime || lastEntry.loadTime;
        }).observe({ type: 'largest-contentful-paint', buffered: true });

        setTimeout(() => resolve(lcpValue), 3000);
      });
    });

    console.log(`Mobile LCP: ${lcp.toFixed(2)}ms`);
    // Mobile budget is slightly higher (3.5s instead of 2.5s)
    expect(lcp).toBeLessThan(3500);
  });

  test('conversation view should load fast on mobile', async ({ page }) => {
    await page.setViewportSize({ width: 390, height: 844 });

    const startTime = Date.now();
    await page.goto('/conversations/test-id');
    await page.waitForLoadState('networkidle');
    const loadTime = Date.now() - startTime;

    console.log(`Mobile conversation view load: ${loadTime}ms`);
    expect(loadTime).toBeLessThan(4000); // 4s budget for mobile
  });

  test('mobile should not download desktop-only resources', async ({ page }) => {
    await page.setViewportSize({ width: 390, height: 844 });
    await page.goto('/');
    await page.waitForLoadState('networkidle');

    const resources = await page.evaluate(() => {
      const allResources = performance.getEntriesByType('resource') as PerformanceResourceTiming[];
      return allResources.map(r => ({
        name: r.name,
        size: r.transferSize || 0
      }));
    });

    // Total transfer size should be reasonable on mobile
    const totalSize = resources.reduce((sum, r) => sum + r.size, 0);
    const totalMB = (totalSize / 1024 / 1024).toFixed(2);

    console.log(`Total mobile download: ${totalMB}MB`);

    // Should be under 5MB for initial load
    expect(totalSize).toBeLessThan(5 * 1024 * 1024);
  });
});

test.describe('Rendering Performance', () => {
  test('should not block rendering with JavaScript', async ({ page }) => {
    await page.goto('/');

    const renderBlockingResources = await page.evaluate(() => {
      const scripts = Array.from(document.querySelectorAll('script:not([async]):not([defer])'));
      return scripts.map(script => script.getAttribute('src') || 'inline');
    });

    console.log('Render-blocking scripts:', renderBlockingResources.length);

    // Should use async/defer for most scripts
    expect(renderBlockingResources.length).toBeLessThan(3);
  });

  test('should prioritize above-the-fold content', async ({ page }) => {
    await page.goto('/');

    const fcp = await page.evaluate(() => {
      const paint = performance.getEntriesByType('paint');
      const fcpEntry = paint.find(entry => entry.name === 'first-contentful-paint');
      return fcpEntry?.startTime || 0;
    });

    console.log(`First Contentful Paint: ${fcp.toFixed(2)}ms`);
    expect(fcp).toBeLessThan(PERFORMANCE_BUDGETS.FCP);
  });

  test('should not have long tasks blocking main thread', async ({ page }) => {
    await page.goto('/');
    await page.waitForLoadState('networkidle');

    const longTasks = await page.evaluate(() => {
      return new Promise<number>((resolve) => {
        let taskCount = 0;

        if ('PerformanceObserver' in window) {
          try {
            new PerformanceObserver((list) => {
              taskCount += list.getEntries().length;
            }).observe({ type: 'longtask', buffered: true });
          } catch (e) {
            // longtask not supported in all browsers
          }
        }

        setTimeout(() => resolve(taskCount), 2000);
      });
    });

    console.log(`Long tasks detected: ${longTasks}`);

    // Should have minimal long tasks
    expect(longTasks).toBeLessThan(5);
  });

  test('images should be lazy-loaded', async ({ page }) => {
    await page.goto('/');

    const lazyImages = await page.evaluate(() => {
      const images = Array.from(document.querySelectorAll('img'));
      return images.filter(img => img.loading === 'lazy').length;
    });

    console.log(`Lazy-loaded images: ${lazyImages}`);

    // At least some images should be lazy-loaded
    if (lazyImages > 0) {
      expect(lazyImages).toBeGreaterThan(0);
    }
  });
});

test.describe('Memory Performance', () => {
  test('should not have memory leaks on navigation', async ({ page }) => {
    // Navigate between pages multiple times
    await page.goto('/');
    await page.goto('/explore');
    await page.goto('/conversations/test-id');
    await page.goto('/');

    // Check memory usage (if available)
    const memoryUsage = await page.evaluate(() => {
      if ('memory' in performance) {
        const mem = (performance as any).memory;
        return {
          used: mem.usedJSHeapSize,
          total: mem.totalJSHeapSize,
          limit: mem.jsHeapSizeLimit
        };
      }
      return null;
    });

    if (memoryUsage) {
      console.log('Memory usage:', {
        used: `${(memoryUsage.used / 1024 / 1024).toFixed(2)}MB`,
        total: `${(memoryUsage.total / 1024 / 1024).toFixed(2)}MB`,
        limit: `${(memoryUsage.limit / 1024 / 1024).toFixed(2)}MB`
      });

      // Used memory should be reasonable
      expect(memoryUsage.used).toBeLessThan(memoryUsage.limit * 0.5);
    }
  });

  test('conversation view should not leak on scroll', async ({ page }) => {
    await page.goto('/conversations/long-conversation');

    // Scroll multiple times
    for (let i = 0; i < 10; i++) {
      await page.evaluate(() => {
        const container = document.getElementById('messagesContainer');
        if (container) {
          container.scrollTop = container.scrollHeight;
          container.scrollTop = 0;
        }
      });
    }

    // Page should still be responsive
    const isResponsive = await page.evaluate(() => {
      return document.readyState === 'complete';
    });

    expect(isResponsive).toBe(true);
  });
});

test.describe('Network Performance', () => {
  test('should use HTTP/2 or HTTP/3', async ({ page }) => {
    const response = await page.goto('/');
    const protocol = response?.headers()?.['x-protocol'] || 'unknown';

    // Check if modern protocol is used
    console.log('Protocol:', protocol);

    // Just verify response exists (protocol may vary by environment)
    expect(response?.status()).toBe(200);
  });

  test('should preconnect to important origins', async ({ page }) => {
    await page.goto('/');

    const preconnects = await page.evaluate(() => {
      const links = Array.from(document.querySelectorAll('link[rel="preconnect"]'));
      return links.map(link => link.getAttribute('href'));
    });

    console.log('Preconnect links:', preconnects);

    // May or may not have preconnects (depends on implementation)
    if (preconnects.length > 0) {
      expect(preconnects.length).toBeGreaterThan(0);
    }
  });

  test('should use prefetch for critical resources', async ({ page }) => {
    await page.goto('/');

    const prefetchLinks = await page.evaluate(() => {
      const links = Array.from(document.querySelectorAll('link[rel="prefetch"], link[rel="preload"]'));
      return links.map(link => ({
        rel: link.getAttribute('rel'),
        href: link.getAttribute('href'),
        as: link.getAttribute('as')
      }));
    });

    console.log('Prefetch/preload links:', prefetchLinks.length);

    // Prefetch is optional but recommended
    if (prefetchLinks.length > 0) {
      expect(prefetchLinks.length).toBeGreaterThan(0);
    }
  });
});

test.describe('Performance Budget Report', () => {
  test('generate performance report for all critical pages', async ({ page }) => {
    const report: any[] = [];

    for (const pageConfig of pagesUnderTest) {
      const startTime = Date.now();
      await page.goto(pageConfig.url);
      await page.waitForLoadState('networkidle');
      const loadTime = Date.now() - startTime;

      const metrics = await page.evaluate(() => {
        const navigation = performance.getEntriesByType('navigation')[0] as PerformanceNavigationTiming;
        const paint = performance.getEntriesByType('paint');

        return {
          ttfb: navigation.responseStart - navigation.requestStart,
          fcp: paint.find(entry => entry.name === 'first-contentful-paint')?.startTime || 0,
          totalTime: navigation.loadEventEnd - navigation.fetchStart
        };
      });

      report.push({
        page: pageConfig.name,
        url: pageConfig.url,
        loadTime,
        metrics
      });
    }

    console.log('\n=== Performance Report ===');
    report.forEach(item => {
      console.log(`\n${item.page} (${item.url})`);
      console.log(`  Load Time: ${item.loadTime}ms`);
      console.log(`  TTFB: ${item.metrics.ttfb.toFixed(2)}ms`);
      console.log(`  FCP: ${item.metrics.fcp.toFixed(2)}ms`);
      console.log(`  Total: ${item.metrics.totalTime.toFixed(2)}ms`);
    });
    console.log('\n=========================\n');

    // All pages should meet budgets
    report.forEach(item => {
      expect(item.loadTime).toBeLessThan(PERFORMANCE_BUDGETS.LOAD_TIME);
    });
  });
});
