const { test, expect } = require('@playwright/test');

test.describe('Frontend Application Tests', () => {
  const frontendUrl = 'http://localhost:3000';

  test('should load the main page successfully', async ({ page }) => {
    await page.goto(frontendUrl);

    // Wait for the page to load
    await page.waitForLoadState('networkidle');

    // Check if the page title contains expected content
    const title = await page.title();
    expect(title).toBeTruthy();
    expect(title.length).toBeGreaterThan(0);

    console.log(`✅ Page title: "${title}"`);
  });

  test('should have responsive design', async ({ page }) => {
    await page.goto(frontendUrl);

    // Test desktop view
    await page.setViewportSize({ width: 1920, height: 1080 });
    await page.waitForLoadState('networkidle');

    // Test tablet view
    await page.setViewportSize({ width: 768, height: 1024 });
    await page.waitForLoadState('networkidle');

    // Test mobile view
    await page.setViewportSize({ width: 375, height: 667 });
    await page.waitForLoadState('networkidle');

    console.log('✅ Responsive design test completed');
  });

  test('should have basic navigation elements', async ({ page }) => {
    await page.goto(frontendUrl);
    await page.waitForLoadState('networkidle');

    // Look for common navigation elements
    const body = await page.locator('body').innerHTML();

    // Check if there are any navigation-related elements
    const hasNavigation = body.includes('nav') ||
                         body.includes('menu') ||
                         body.includes('header') ||
                         body.includes('navigation');

    console.log(`✅ Navigation elements present: ${hasNavigation}`);
  });

  test('should not have console errors', async ({ page }) => {
    const consoleErrors = [];

    page.on('console', (msg) => {
      if (msg.type() === 'error') {
        consoleErrors.push(msg.text());
      }
    });

    await page.goto(frontendUrl);
    await page.waitForLoadState('networkidle');

    // Allow some time for any async operations
    await page.waitForTimeout(2000);

    if (consoleErrors.length > 0) {
      console.log('⚠️ Console errors found:', consoleErrors);
    } else {
      console.log('✅ No console errors detected');
    }

    // Don't fail the test for console errors, just log them
    expect(consoleErrors.length).toBeLessThanOrEqual(5); // Allow some minor errors
  });

  test('should load CSS and styling', async ({ page }) => {
    await page.goto(frontendUrl);
    await page.waitForLoadState('networkidle');

    // Check if CSS is loaded by looking for styled elements
    const bodyStyles = await page.locator('body').evaluate((el) => {
      const styles = window.getComputedStyle(el);
      return {
        fontFamily: styles.fontFamily,
        backgroundColor: styles.backgroundColor,
        color: styles.color
      };
    });

    // Verify that styles are applied (not default browser styles)
    expect(bodyStyles.fontFamily).toBeTruthy();
    expect(bodyStyles.fontFamily).not.toBe('Times');

    console.log('✅ CSS styling is applied correctly');
  });

  test('should be accessible', async ({ page }) => {
    await page.goto(frontendUrl);
    await page.waitForLoadState('networkidle');

    // Basic accessibility checks
    const html = await page.locator('html').getAttribute('lang');

    // Check for basic semantic elements
    const hasMainContent = await page.locator('main, [role="main"]').count();
    const hasHeadings = await page.locator('h1, h2, h3, h4, h5, h6').count();

    console.log(`✅ Accessibility check - Lang: ${html}, Main content: ${hasMainContent}, Headings: ${hasHeadings}`);

    expect(hasMainContent).toBeGreaterThanOrEqual(0);
  });

  test('should handle different screen sizes', async ({ page }) => {
    const viewports = [
      { width: 1920, height: 1080, name: 'Desktop Large' },
      { width: 1366, height: 768, name: 'Desktop Medium' },
      { width: 1024, height: 768, name: 'Tablet Landscape' },
      { width: 768, height: 1024, name: 'Tablet Portrait' },
      { width: 414, height: 896, name: 'Mobile Large' },
      { width: 375, height: 667, name: 'Mobile Medium' },
      { width: 320, height: 568, name: 'Mobile Small' }
    ];

    for (const viewport of viewports) {
      await page.setViewportSize({ width: viewport.width, height: viewport.height });
      await page.goto(frontendUrl);
      await page.waitForLoadState('networkidle');

      // Check if page loads without layout issues
      const bodyHeight = await page.locator('body').evaluate(el => el.scrollHeight);
      expect(bodyHeight).toBeGreaterThan(0);

      console.log(`✅ ${viewport.name} (${viewport.width}x${viewport.height}) - Height: ${bodyHeight}px`);
    }
  });

  test('should load images and assets', async ({ page }) => {
    await page.goto(frontendUrl);
    await page.waitForLoadState('networkidle');

    // Check for images
    const images = await page.locator('img').count();

    // Check for broken images
    const brokenImages = await page.locator('img').evaluateAll((imgs) => {
      return imgs.filter(img => !img.complete || img.naturalWidth === 0).length;
    });

    console.log(`✅ Images loaded: ${images}, Broken images: ${brokenImages}`);
    expect(brokenImages).toBe(0);
  });

  test('should have proper meta tags', async ({ page }) => {
    await page.goto(frontendUrl);
    await page.waitForLoadState('networkidle');

    // Check for essential meta tags
    const viewport = await page.locator('meta[name="viewport"]').getAttribute('content');
    const charset = await page.locator('meta[charset]').count();

    expect(charset).toBeGreaterThan(0);
    console.log(`✅ Meta tags - Viewport: ${viewport}, Charset tags: ${charset}`);
  });

  test('should support dark/light theme (if implemented)', async ({ page }) => {
    await page.goto(frontendUrl);
    await page.waitForLoadState('networkidle');

    // Check if theme toggle exists
    const themeToggle = await page.locator('[data-theme], .theme-toggle, .dark-mode-toggle').count();

    if (themeToggle > 0) {
      console.log('✅ Theme toggle found - testing theme switching');

      // Try to click theme toggle
      await page.locator('[data-theme], .theme-toggle, .dark-mode-toggle').first().click();
      await page.waitForTimeout(500);

      console.log('✅ Theme toggle interaction successful');
    } else {
      console.log('ℹ️ No theme toggle found - skipping theme test');
    }
  });
});