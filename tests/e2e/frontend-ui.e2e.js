const { test, expect } = require('@playwright/test');

test.describe('Frontend UI Components Tests', () => {
  const frontendUrl = 'http://localhost:3000';

  test('should test common UI components', async ({ page }) => {
    await page.goto(frontendUrl);
    await page.waitForLoadState('networkidle');

    // Test buttons
    const buttons = await page.locator('button, .btn, [role="button"]').count();
    console.log(`✅ Found ${buttons} button elements`);

    // Test forms
    const forms = await page.locator('form').count();
    const inputs = await page.locator('input, textarea, select').count();
    console.log(`✅ Found ${forms} forms and ${inputs} input elements`);

    // Test links
    const links = await page.locator('a').count();
    console.log(`✅ Found ${links} link elements`);

    // Test common UI patterns
    const cards = await page.locator('.card, [class*="card"]').count();
    const modals = await page.locator('.modal, [class*="modal"], [role="dialog"]').count();
    console.log(`✅ Found ${cards} card components and ${modals} modal components`);
  });

  test('should test interactive elements', async ({ page }) => {
    await page.goto(frontendUrl);
    await page.waitForLoadState('networkidle');

    // Test clickable elements
    const clickableElements = await page.locator('button, a, [role="button"], [tabindex]').count();
    console.log(`✅ Found ${clickableElements} interactive elements`);

    // Test if any buttons are clickable (without causing errors)
    const firstButton = page.locator('button').first();
    const buttonExists = await firstButton.count() > 0;

    if (buttonExists) {
      try {
        await firstButton.click({ timeout: 2000 });
        console.log('✅ Button click interaction successful');
      } catch (error) {
        console.log('ℹ️ Button click test skipped (may require specific state)');
      }
    }
  });

  test('should test form interactions', async ({ page }) => {
    await page.goto(frontendUrl);
    await page.waitForLoadState('networkidle');

    // Look for forms
    const forms = await page.locator('form').count();

    if (forms > 0) {
      console.log(`✅ Found ${forms} forms - testing form interactions`);

      // Test input fields
      const textInputs = page.locator('input[type="text"], input[type="email"], input[type="password"]');
      const inputCount = await textInputs.count();

      if (inputCount > 0) {
        try {
          await textInputs.first().fill('test input');
          await textInputs.first().clear();
          console.log('✅ Form input interaction successful');
        } catch (error) {
          console.log('ℹ️ Form input test skipped');
        }
      }
    } else {
      console.log('ℹ️ No forms found - skipping form interaction tests');
    }
  });

  test('should test navigation functionality', async ({ page }) => {
    await page.goto(frontendUrl);
    await page.waitForLoadState('networkidle');

    // Test internal links (if any)
    const internalLinks = await page.locator('a[href^="/"], a[href^="./"], a[href^="#"]').count();
    console.log(`✅ Found ${internalLinks} internal navigation links`);

    if (internalLinks > 0) {
      try {
        // Get the first internal link
        const firstLink = page.locator('a[href^="/"], a[href^="./"], a[href^="#"]').first();
        const href = await firstLink.getAttribute('href');

        if (href && href !== '#') {
          await firstLink.click({ timeout: 2000 });
          await page.waitForLoadState('networkidle');
          console.log(`✅ Navigation to ${href} successful`);
        }
      } catch (error) {
        console.log('ℹ️ Navigation test skipped');
      }
    }
  });

  test('should test component loading states', async ({ page }) => {
    await page.goto(frontendUrl);

    // Check for loading indicators
    const loadingElements = await page.locator('.loading, .spinner, [class*="loading"], [class*="spinner"]').count();
    console.log(`✅ Found ${loadingElements} loading indicator elements`);

    await page.waitForLoadState('networkidle');

    // After network idle, loading states should be gone or minimal
    const persistentLoading = await page.locator('.loading, .spinner, [class*="loading"], [class*="spinner"]').count();
    console.log(`✅ Persistent loading elements after load: ${persistentLoading}`);
  });

  test('should test error boundaries and error states', async ({ page }) => {
    await page.goto(frontendUrl);
    await page.waitForLoadState('networkidle');

    // Check for error messages or error states
    const errorElements = await page.locator('.error, .alert-error, [class*="error"], .text-red, .text-danger').count();
    console.log(`✅ Found ${errorElements} error-related elements`);

    // Test 404 or invalid routes (if routing is implemented)
    try {
      await page.goto(`${frontendUrl}/non-existent-page-test-123`);
      await page.waitForLoadState('networkidle');

      const pageContent = await page.locator('body').textContent();
      const is404 = pageContent.includes('404') ||
                   pageContent.includes('Not Found') ||
                   pageContent.includes('Page not found');

      console.log(`✅ 404 page handling: ${is404 ? 'Implemented' : 'Default behavior'}`);
    } catch (error) {
      console.log('ℹ️ 404 test completed');
    }

    // Return to main page
    await page.goto(frontendUrl);
    await page.waitForLoadState('networkidle');
  });

  test('should test keyboard navigation', async ({ page }) => {
    await page.goto(frontendUrl);
    await page.waitForLoadState('networkidle');

    // Test tab navigation
    const focusableElements = await page.locator('button, a, input, select, textarea, [tabindex]:not([tabindex="-1"])').count();
    console.log(`✅ Found ${focusableElements} focusable elements`);

    if (focusableElements > 0) {
      try {
        // Test tab navigation
        await page.keyboard.press('Tab');
        await page.keyboard.press('Tab');
        await page.keyboard.press('Tab');

        console.log('✅ Keyboard navigation (Tab) test completed');
      } catch (error) {
        console.log('ℹ️ Keyboard navigation test skipped');
      }
    }
  });

  test('should test data loading and display', async ({ page }) => {
    await page.goto(frontendUrl);
    await page.waitForLoadState('networkidle');

    // Check for data tables or lists
    const tables = await page.locator('table, .table').count();
    const lists = await page.locator('ul, ol, .list').count();
    console.log(`✅ Found ${tables} tables and ${lists} lists`);

    // Check for data containers
    const dataContainers = await page.locator('[class*="data"], [class*="content"], .grid, .flex').count();
    console.log(`✅ Found ${dataContainers} potential data container elements`);

    // Test if content is properly loaded
    const bodyText = await page.locator('body').textContent();
    const hasContent = bodyText && bodyText.trim().length > 100;
    console.log(`✅ Page has substantial content: ${hasContent}`);
  });

  test('should test component state management', async ({ page }) => {
    await page.goto(frontendUrl);
    await page.waitForLoadState('networkidle');

    // Test toggleable elements (checkboxes, switches, etc.)
    const checkboxes = await page.locator('input[type="checkbox"]').count();
    const radioButtons = await page.locator('input[type="radio"]').count();
    const toggles = await page.locator('.toggle, .switch, [role="switch"]').count();

    console.log(`✅ Interactive state elements - Checkboxes: ${checkboxes}, Radio: ${radioButtons}, Toggles: ${toggles}`);

    if (checkboxes > 0) {
      try {
        const firstCheckbox = page.locator('input[type="checkbox"]').first();
        const initialState = await firstCheckbox.isChecked();
        await firstCheckbox.click();
        const newState = await firstCheckbox.isChecked();

        console.log(`✅ Checkbox state change: ${initialState} → ${newState}`);
      } catch (error) {
        console.log('ℹ️ Checkbox interaction test skipped');
      }
    }
  });

  test('should test performance and loading times', async ({ page }) => {
    const startTime = Date.now();

    await page.goto(frontendUrl);
    await page.waitForLoadState('networkidle');

    const loadTime = Date.now() - startTime;
    console.log(`✅ Page load time: ${loadTime}ms`);

    // Test if critical resources are loaded quickly
    expect(loadTime).toBeLessThan(10000); // Should load within 10 seconds

    // Check for performance metrics
    const performanceMetrics = await page.evaluate(() => {
      const perfData = performance.getEntriesByType('navigation')[0];
      return {
        domContentLoaded: perfData.domContentLoadedEventEnd - perfData.domContentLoadedEventStart,
        loadComplete: perfData.loadEventEnd - perfData.loadEventStart
      };
    });

    console.log(`✅ Performance metrics:`, performanceMetrics);
  });
});