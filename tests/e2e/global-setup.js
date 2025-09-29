const { chromium } = require('@playwright/test');

async function globalSetup(config) {
  console.log('🚀 Global setup: Starting KOL Management System...');

  // Wait for services to be ready
  const browser = await chromium.launch();
  const page = await browser.newPage();

  // Wait for health endpoint to be ready
  let retries = 0;
  const maxRetries = 30;

  while (retries < maxRetries) {
    try {
      const response = await page.goto('http://localhost:8000/health', {
        timeout: 5000,
        waitUntil: 'networkidle'
      });

      if (response.ok()) {
        console.log('✅ KOL Management System is ready!');
        break;
      }
    } catch (error) {
      console.log(`⏳ Waiting for services... (${retries + 1}/${maxRetries})`);
      await new Promise(resolve => setTimeout(resolve, 2000));
      retries++;
    }
  }

  if (retries >= maxRetries) {
    throw new Error('❌ Services failed to start within timeout');
  }

  await browser.close();

  // Set up test database if needed
  console.log('🗄️ Setting up test database...');

  // Create admin user for testing
  try {
    const adminSetupResponse = await fetch('http://localhost:8000/api/v1/auth/setup-admin', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        email: 'admin@test.com',
        password: 'testpassword123',
        username: 'admin',
        full_name: 'Test Admin'
      }),
    });

    if (adminSetupResponse.ok) {
      console.log('✅ Test admin user created');
    }
  } catch (error) {
    console.log('⚠️ Admin user might already exist or setup failed');
  }

  console.log('🎭 Global setup completed!');
}

module.exports = globalSetup;