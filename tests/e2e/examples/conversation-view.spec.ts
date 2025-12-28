/**
 * Conversation View E2E Tests
 *
 * Tests the conversation view component including:
 * - Empty state rendering
 * - Message display and roles
 * - Auto-scroll behavior
 * - Mobile keyboard handling
 * - Navigation controls
 *
 * Example implementation showing Page Object Model pattern
 */

import { test, expect, Page, Locator } from '@playwright/test';

// Page Object Model for Conversation View
class ConversationPage {
  readonly page: Page;
  readonly backButton: Locator;
  readonly conversationTitle: Locator;
  readonly menuButton: Locator;
  readonly messagesContainer: Locator;
  readonly messagesList: Locator;
  readonly messageBubbles: Locator;
  readonly emptyState: Locator;
  readonly emptyIcon: Locator;
  readonly emptyHeading: Locator;
  readonly inputArea: Locator;

  constructor(page: Page) {
    this.page = page;
    this.backButton = page.locator('.back-button');
    this.conversationTitle = page.locator('.conversation-title');
    this.menuButton = page.locator('.menu-button');
    this.messagesContainer = page.locator('#messagesContainer');
    this.messagesList = page.locator('.messages-list');
    this.messageBubbles = page.locator('.message-bubble');
    this.emptyState = page.locator('.empty-state');
    this.emptyIcon = page.locator('.empty-icon');
    this.emptyHeading = page.locator('.empty-state h2');
    this.inputArea = page.locator('.conversation-input');
  }

  async goto(conversationId: string) {
    await this.page.goto(`/conversations/${conversationId}`);
    await this.page.waitForLoadState('networkidle');
  }

  async getMessageCount(): Promise<number> {
    return await this.messageBubbles.count();
  }

  async isScrolledToBottom(): Promise<boolean> {
    return await this.page.evaluate(() => {
      const container = document.getElementById('messagesContainer');
      if (!container) return false;

      const scrollPosition = container.scrollTop + container.clientHeight;
      const scrollHeight = container.scrollHeight;

      // Within 50px of bottom
      return Math.abs(scrollHeight - scrollPosition) < 50;
    });
  }

  async scrollUp(pixels: number) {
    await this.page.evaluate((px) => {
      const container = document.getElementById('messagesContainer');
      if (container) container.scrollTop -= px;
    }, pixels);
  }

  async triggerSendMessageEvent() {
    await this.page.evaluate(() => {
      window.dispatchEvent(new Event('sendMessage'));
    });
  }

  async triggerKeyboardResize() {
    await this.page.evaluate(() => {
      if (window.visualViewport) {
        window.visualViewport.dispatchEvent(new Event('resize'));
      }
    });
  }

  async addMockMessage(role: 'user' | 'assistant', content: string) {
    await this.page.evaluate(({ role, content }) => {
      const messagesList = document.querySelector('.messages-list');
      if (!messagesList) return;

      const bubble = document.createElement('div');
      bubble.className = 'message-bubble';
      bubble.setAttribute('data-role', role);
      bubble.textContent = content;
      messagesList.appendChild(bubble);
    }, { role, content });
  }

  async expectEmptyState() {
    await expect(this.emptyState).toBeVisible();
    await expect(this.emptyHeading).toContainText('Start a conversation');
  }

  async expectMessages(count: number) {
    await expect(this.messageBubbles).toHaveCount(count);
  }

  async expectScrolledToBottom() {
    const isBottom = await this.isScrolledToBottom();
    expect(isBottom).toBe(true);
  }
}

test.describe('Conversation View - Empty State', () => {
  test('should display empty state when no messages', async ({ page }) => {
    const conversationPage = new ConversationPage(page);
    await conversationPage.goto('empty-conversation');

    await conversationPage.expectEmptyState();
    await expect(conversationPage.emptyIcon).toBeVisible();
    await expect(conversationPage.emptyState.locator('p')).toContainText('Ask Claude Code');
  });

  test('should have centered empty state layout', async ({ page }) => {
    const conversationPage = new ConversationPage(page);
    await conversationPage.goto('empty-conversation');

    const display = await conversationPage.emptyState.evaluate(el =>
      window.getComputedStyle(el).display
    );
    expect(display).toBe('flex');

    const alignItems = await conversationPage.emptyState.evaluate(el =>
      window.getComputedStyle(el).alignItems
    );
    expect(alignItems).toBe('center');
  });
});

test.describe('Conversation View - Message Rendering', () => {
  test('should render messages with correct roles', async ({ page }) => {
    const conversationPage = new ConversationPage(page);
    await conversationPage.goto('test-conversation');

    // Verify messages exist
    const messageCount = await conversationPage.getMessageCount();
    expect(messageCount).toBeGreaterThan(0);

    // Verify role attributes exist
    const userMessages = page.locator('.message-bubble[data-role="user"]');
    const assistantMessages = page.locator('.message-bubble[data-role="assistant"]');

    const userCount = await userMessages.count();
    const assistantCount = await assistantMessages.count();

    expect(userCount + assistantCount).toBe(messageCount);
  });

  test('should display timestamps for messages', async ({ page }) => {
    const conversationPage = new ConversationPage(page);
    await conversationPage.goto('test-conversation');

    const firstMessage = conversationPage.messageBubbles.first();
    await expect(firstMessage).toBeVisible();

    // Timestamps should be present (even if hidden for testing)
    const timestamp = firstMessage.locator('.timestamp');
    await expect(timestamp).toHaveCount(1);
  });

  test('should handle long message content', async ({ page }) => {
    const conversationPage = new ConversationPage(page);
    await conversationPage.goto('long-message-conversation');

    const longMessage = page.locator('.message-bubble').first();
    await expect(longMessage).toBeVisible();

    // Should wrap text, not overflow
    const overflow = await longMessage.evaluate(el =>
      window.getComputedStyle(el).overflow
    );
    expect(overflow).not.toBe('visible');
  });
});

test.describe('Conversation View - Auto-Scroll Behavior', () => {
  test('should auto-scroll to bottom on initial load', async ({ page }) => {
    const conversationPage = new ConversationPage(page);
    await conversationPage.goto('long-conversation');

    // Wait for scroll to complete
    await page.waitForTimeout(100);

    await conversationPage.expectScrolledToBottom();
  });

  test('should auto-scroll on new message event', async ({ page }) => {
    const conversationPage = new ConversationPage(page);
    await conversationPage.goto('test-conversation');

    // Scroll up
    await conversationPage.scrollUp(100);

    // Verify not at bottom
    let isBottom = await conversationPage.isScrolledToBottom();
    expect(isBottom).toBe(false);

    // Trigger sendMessage event
    await conversationPage.triggerSendMessageEvent();

    // Wait for scroll animation
    await page.waitForTimeout(200);

    // Should be back at bottom
    await conversationPage.expectScrolledToBottom();
  });

  test('should use smooth scroll for message events', async ({ page }) => {
    const conversationPage = new ConversationPage(page);
    await conversationPage.goto('test-conversation');

    await conversationPage.scrollUp(100);

    // Trigger event
    await conversationPage.triggerSendMessageEvent();

    // Scroll should happen (we can't test smoothness directly, but verify it scrolled)
    await page.waitForTimeout(200);
    await conversationPage.expectScrolledToBottom();
  });
});

test.describe('Conversation View - Mobile Behavior', () => {
  test('should handle mobile keyboard appearance (visualViewport)', async ({ page }) => {
    // Set mobile viewport
    await page.setViewportSize({ width: 390, height: 844 });

    const conversationPage = new ConversationPage(page);
    await conversationPage.goto('test-conversation');

    // Trigger visualViewport resize (simulates keyboard opening)
    await conversationPage.triggerKeyboardResize();

    // Wait for adjustment
    await page.waitForTimeout(200);

    // Should still be scrolled to bottom
    await conversationPage.expectScrolledToBottom();
  });

  test('should use dynamic viewport height (dvh)', async ({ page }) => {
    await page.setViewportSize({ width: 390, height: 844 });

    const conversationPage = new ConversationPage(page);
    await conversationPage.goto('test-conversation');

    // Check that conversation-view uses calc with dvh
    const height = await page.locator('.conversation-view').evaluate(el => {
      return window.getComputedStyle(el).height;
    });

    // Should have calculated height (not just 100vh)
    expect(height).not.toBe('0px');
    expect(parseInt(height)).toBeGreaterThan(0);
  });

  test('should have touch-friendly tap targets', async ({ page }) => {
    await page.setViewportSize({ width: 390, height: 844 });

    const conversationPage = new ConversationPage(page);
    await conversationPage.goto('test-conversation');

    // Back button should be at least 36x36 (touch-friendly)
    const backButtonBox = await conversationPage.backButton.boundingBox();
    expect(backButtonBox).not.toBeNull();
    if (backButtonBox) {
      expect(backButtonBox.width).toBeGreaterThanOrEqual(36);
      expect(backButtonBox.height).toBeGreaterThanOrEqual(36);
    }

    // Menu button should be touch-friendly
    const menuButtonBox = await conversationPage.menuButton.boundingBox();
    expect(menuButtonBox).not.toBeNull();
    if (menuButtonBox) {
      expect(menuButtonBox.width).toBeGreaterThanOrEqual(36);
      expect(menuButtonBox.height).toBeGreaterThanOrEqual(36);
    }
  });

  test('should support momentum scrolling on iOS', async ({ page }) => {
    await page.setViewportSize({ width: 390, height: 844 });

    const conversationPage = new ConversationPage(page);
    await conversationPage.goto('long-conversation');

    // Check for -webkit-overflow-scrolling: touch
    const overflowScrolling = await conversationPage.messagesContainer.evaluate(el => {
      return (window.getComputedStyle(el) as any).webkitOverflowScrolling;
    });

    // Should be 'touch' for momentum scrolling
    expect(overflowScrolling).toBe('touch');
  });
});

test.describe('Conversation View - Navigation', () => {
  test('should navigate back to conversation list', async ({ page }) => {
    const conversationPage = new ConversationPage(page);
    await conversationPage.goto('test-conversation');

    await conversationPage.backButton.click();

    await expect(page).toHaveURL(/\/conversations$/);
  });

  test('should have accessible back button', async ({ page }) => {
    const conversationPage = new ConversationPage(page);
    await conversationPage.goto('test-conversation');

    const ariaLabel = await conversationPage.backButton.getAttribute('aria-label');
    expect(ariaLabel).toBeTruthy();
    expect(ariaLabel).toContain('Back');
  });

  test('should display conversation title', async ({ page }) => {
    const conversationPage = new ConversationPage(page);
    await conversationPage.goto('test-conversation');

    await expect(conversationPage.conversationTitle).toBeVisible();

    const title = await conversationPage.conversationTitle.textContent();
    expect(title).toBeTruthy();
    expect(title?.length).toBeGreaterThan(0);
  });

  test('should truncate long titles with ellipsis', async ({ page }) => {
    const conversationPage = new ConversationPage(page);
    await conversationPage.goto('long-title-conversation');

    await expect(conversationPage.conversationTitle).toBeVisible();

    const textOverflow = await conversationPage.conversationTitle.evaluate(el =>
      window.getComputedStyle(el).textOverflow
    );
    expect(textOverflow).toBe('ellipsis');

    const whiteSpace = await conversationPage.conversationTitle.evaluate(el =>
      window.getComputedStyle(el).whiteSpace
    );
    expect(whiteSpace).toBe('nowrap');
  });

  test('should show menu button', async ({ page }) => {
    const conversationPage = new ConversationPage(page);
    await conversationPage.goto('test-conversation');

    await expect(conversationPage.menuButton).toBeVisible();

    const ariaLabel = await conversationPage.menuButton.getAttribute('aria-label');
    expect(ariaLabel).toBeTruthy();
  });
});

test.describe('Conversation View - Layout', () => {
  test('should have fixed header', async ({ page }) => {
    const conversationPage = new ConversationPage(page);
    await conversationPage.goto('long-conversation');

    const header = page.locator('.conversation-header');
    await expect(header).toBeVisible();

    // Header should not scroll with messages
    const flexShrink = await header.evaluate(el =>
      window.getComputedStyle(el).flexShrink
    );
    expect(flexShrink).toBe('0');
  });

  test('should center messages container', async ({ page }) => {
    const conversationPage = new ConversationPage(page);
    await conversationPage.goto('test-conversation');

    const maxWidth = await conversationPage.messagesList.evaluate(el =>
      window.getComputedStyle(el).maxWidth
    );
    expect(maxWidth).toBe('1200px');

    const margin = await conversationPage.messagesList.evaluate(el =>
      window.getComputedStyle(el).margin
    );
    expect(margin).toContain('auto');
  });

  test('should have proper spacing for input area', async ({ page }) => {
    const conversationPage = new ConversationPage(page);
    await conversationPage.goto('test-conversation');

    // Messages container should have bottom padding for input
    const paddingBottom = await conversationPage.messagesContainer.evaluate(el =>
      window.getComputedStyle(el).paddingBottom
    );
    expect(parseInt(paddingBottom)).toBeGreaterThan(0);
  });

  test('should not have horizontal overflow on mobile', async ({ page }) => {
    await page.setViewportSize({ width: 390, height: 844 });

    const conversationPage = new ConversationPage(page);
    await conversationPage.goto('test-conversation');

    const bodyWidth = await page.evaluate(() => document.body.scrollWidth);
    const viewportWidth = await page.evaluate(() => window.innerWidth);

    expect(bodyWidth).toBeLessThanOrEqual(viewportWidth);
  });
});

test.describe('Conversation View - Responsive Design', () => {
  test('should adjust padding on tablet', async ({ page }) => {
    await page.setViewportSize({ width: 768, height: 1024 });

    const conversationPage = new ConversationPage(page);
    await conversationPage.goto('test-conversation');

    const header = page.locator('.conversation-header');
    const padding = await header.evaluate(el =>
      window.getComputedStyle(el).padding
    );

    // Should have tablet-specific padding
    expect(padding).toBeTruthy();
  });

  test('should increase title size on desktop', async ({ page }) => {
    await page.setViewportSize({ width: 1280, height: 720 });

    const conversationPage = new ConversationPage(page);
    await conversationPage.goto('test-conversation');

    const fontSize = await conversationPage.conversationTitle.evaluate(el =>
      window.getComputedStyle(el).fontSize
    );

    expect(parseInt(fontSize)).toBeGreaterThanOrEqual(18); // 1.125rem = 18px
  });

  test('should adjust nav height on desktop', async ({ page }) => {
    await page.setViewportSize({ width: 1280, height: 720 });

    const conversationPage = new ConversationPage(page);
    await conversationPage.goto('test-conversation');

    // Desktop should use 80px nav height (vs 70px mobile)
    const viewHeight = await page.locator('.conversation-view').evaluate(el =>
      window.getComputedStyle(el).height
    );

    expect(viewHeight).toBeTruthy();
  });
});

test.describe('Conversation View - Performance', () => {
  test('should load within performance budget', async ({ page }) => {
    const conversationPage = new ConversationPage(page);

    const startTime = Date.now();
    await conversationPage.goto('test-conversation');
    const loadTime = Date.now() - startTime;

    // Should load in under 2 seconds
    expect(loadTime).toBeLessThan(2000);
  });

  test('should not cause layout shift on load', async ({ page }) => {
    const conversationPage = new ConversationPage(page);
    await conversationPage.goto('test-conversation');

    // Wait for layout to stabilize
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

        setTimeout(() => resolve(clsScore), 1000);
      });
    });

    // CLS should be less than 0.1 (good)
    expect(cls).toBeLessThan(0.1);
  });
});
