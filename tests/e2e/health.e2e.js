const { test, expect } = require('@playwright/test');

test.describe('Health Endpoints', () => {
  test('should return healthy status for basic health check', async ({ request }) => {
    const response = await request.get('/health');

    expect(response.ok()).toBeTruthy();

    const data = await response.json();
    expect(data).toEqual({
      status: 'healthy',
      timestamp: expect.any(String),
      version: expect.any(String)
    });
  });

  test('should return detailed health information', async ({ request }) => {
    const response = await request.get('/health/detailed');

    expect(response.ok()).toBeTruthy();

    const data = await response.json();
    expect(data).toHaveProperty('status', 'healthy');
    expect(data).toHaveProperty('services');
    expect(data.services).toHaveProperty('database');
    expect(data.services).toHaveProperty('redis');
  });

  test('should return API information', async ({ request }) => {
    const response = await request.get('/info');

    expect(response.ok()).toBeTruthy();

    const data = await response.json();
    expect(data).toHaveProperty('name');
    expect(data).toHaveProperty('version');
    expect(data).toHaveProperty('environment');
  });
});