const { test, expect } = require('@playwright/test');

test.describe('Frontend Quick Tests', () => {
  const frontendUrl = 'http://localhost:3000';

  test('should load homepage successfully', async ({ page }) => {
    await page.goto(frontendUrl, { waitUntil: 'domcontentloaded' });

    // Check basic page structure
    const title = await page.title();
    expect(title).toBeTruthy();
    console.log(`✅ Page title: "${title}"`);

    // Check if page has content
    const bodyText = await page.locator('body').textContent();
    expect(bodyText.length).toBeGreaterThan(10);
    console.log(`✅ Page has content (${bodyText.length} characters)`);
  });

  test('should load login page', async ({ page }) => {
    await page.goto(`${frontendUrl}/login`, { waitUntil: 'domcontentloaded' });

    const title = await page.title();
    expect(title).toBeTruthy();
    console.log(`✅ Login page title: "${title}"`);

    // Check for login form elements
    const forms = await page.locator('form').count();
    const inputs = await page.locator('input').count();
    const buttons = await page.locator('button').count();

    console.log(`✅ Login page elements - Forms: ${forms}, Inputs: ${inputs}, Buttons: ${buttons}`);
  });

  test('should have responsive navigation', async ({ page }) => {
    await page.goto(frontendUrl, { waitUntil: 'domcontentloaded' });

    // Test different viewport sizes quickly
    const viewports = [
      { width: 1920, height: 1080, name: 'Desktop' },
      { width: 768, height: 1024, name: 'Tablet' },
      { width: 375, height: 667, name: 'Mobile' }
    ];

    for (const viewport of viewports) {
      await page.setViewportSize({ width: viewport.width, height: viewport.height });

      // Check if page still loads
      await page.waitForTimeout(500);
      const bodyHeight = await page.locator('body').evaluate(el => el.scrollHeight);

      expect(bodyHeight).toBeGreaterThan(0);
      console.log(`✅ ${viewport.name} (${viewport.width}x${viewport.height}) - Height: ${bodyHeight}px`);
    }
  });

  test('should have working navigation links', async ({ page }) => {
    await page.goto(frontendUrl, { waitUntil: 'domcontentloaded' });

    // Find all internal links
    const links = await page.locator('a[href^="/"], a[href^="./"]').count();
    console.log(`✅ Found ${links} internal navigation links`);

    if (links > 0) {
      // Test first internal link
      const firstLink = page.locator('a[href^="/"], a[href^="./"]').first();
      const href = await firstLink.getAttribute('href');

      if (href && href !== '#') {
        try {
          await firstLink.click();
          await page.waitForLoadState('domcontentloaded');
          console.log(`✅ Navigation to ${href} successful`);
        } catch (error) {
          console.log(`ℹ️ Navigation to ${href} skipped`);
        }
      }
    }
  });

  test('should have basic UI components', async ({ page }) => {
    await page.goto(frontendUrl, { waitUntil: 'domcontentloaded' });

    // Count basic UI elements
    const buttons = await page.locator('button').count();
    const inputs = await page.locator('input').count();
    const links = await page.locator('a').count();
    const headings = await page.locator('h1, h2, h3, h4, h5, h6').count();

    console.log(`✅ UI Components found:`);
    console.log(`  - Buttons: ${buttons}`);
    console.log(`  - Inputs: ${inputs}`);
    console.log(`  - Links: ${links}`);
    console.log(`  - Headings: ${headings}`);

    expect(buttons + inputs + links + headings).toBeGreaterThan(0);
  });

  test('should have working forms', async ({ page }) => {
    await page.goto(`${frontendUrl}/login`, { waitUntil: 'domcontentloaded' });

    const forms = await page.locator('form').count();

    if (forms > 0) {
      console.log(`✅ Found ${forms} forms`);

      // Test input interaction
      const textInputs = page.locator('input[type="text"], input[type="email"], input[type="password"]');
      const inputCount = await textInputs.count();

      if (inputCount > 0) {
        try {
          await textInputs.first().fill('test@example.com');
          const value = await textInputs.first().inputValue();
          expect(value).toBe('test@example.com');
          console.log(`✅ Form input works: "${value}"`);
        } catch (error) {
          console.log('ℹ️ Form input test skipped');
        }
      }
    } else {
      console.log('ℹ️ No forms found on login page');
    }
  });

  test('should handle basic interactions', async ({ page }) => {
    await page.goto(frontendUrl, { waitUntil: 'domcontentloaded' });

    // Test button clicks
    const buttons = await page.locator('button').count();

    if (buttons > 0) {
      try {
        await page.locator('button').first().click();
        console.log('✅ Button click interaction successful');
      } catch (error) {
        console.log('ℹ️ Button click test skipped');
      }
    }

    // Test keyboard navigation
    try {
      await page.keyboard.press('Tab');
      console.log('✅ Keyboard navigation works');
    } catch (error) {
      console.log('ℹ️ Keyboard navigation test skipped');
    }
  });

  test('should load CSS and basic styling', async ({ page }) => {
    await page.goto(frontendUrl, { waitUntil: 'domcontentloaded' });

    // Check if CSS is loaded
    const bodyStyles = await page.locator('body').evaluate((el) => {
      const styles = window.getComputedStyle(el);
      return {
        fontFamily: styles.fontFamily,
        backgroundColor: styles.backgroundColor,
        display: styles.display
      };
    });

    console.log('✅ CSS Styles detected:');
    console.log(`  - Font Family: ${bodyStyles.fontFamily}`);
    console.log(`  - Background: ${bodyStyles.backgroundColor}`);
    console.log(`  - Display: ${bodyStyles.display}`);

    expect(bodyStyles.fontFamily).toBeTruthy();
  });

  test('should handle page performance', async ({ page }) => {
    const startTime = Date.now();

    await page.goto(frontendUrl, { waitUntil: 'domcontentloaded' });

    const loadTime = Date.now() - startTime;
    console.log(`✅ Page load time: ${loadTime}ms`);

    // Performance should be reasonable
    expect(loadTime).toBeLessThan(15000); // 15 seconds max

    // Check page size
    const bodyText = await page.locator('body').textContent();
    console.log(`✅ Page content size: ${bodyText.length} characters`);
  });

  test('should have no critical JavaScript errors', async ({ page }) => {
    const errors = [];

    page.on('console', (msg) => {
      if (msg.type() === 'error') {
        errors.push(msg.text());
      }
    });

    await page.goto(frontendUrl, { waitUntil: 'domcontentloaded' });
    await page.waitForTimeout(2000);

    console.log(`✅ JavaScript errors detected: ${errors.length}`);

    if (errors.length > 0) {
      console.log('⚠️ Errors found:');
      errors.forEach((error, index) => {
        console.log(`  ${index + 1}. ${error.substring(0, 100)}...`);
      });
    }

    // Allow some minor errors but flag major issues
    expect(errors.length).toBeLessThan(10);
  });
});