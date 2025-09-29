const { test, expect } = require('@playwright/test');

test.describe('Authentication', () => {
  let authToken;

  test('should login with valid credentials', async ({ request }) => {
    const response = await request.post('/api/v1/auth/login', {
      data: {
        email: 'admin@test.com',
        password: 'testpassword123'
      }
    });

    expect(response.ok()).toBeTruthy();

    const data = await response.json();
    expect(data).toHaveProperty('access_token');
    expect(data).toHaveProperty('token_type', 'bearer');
    expect(data).toHaveProperty('user');
    expect(data.user).toHaveProperty('email', 'admin@test.com');

    // Store token for subsequent tests
    authToken = data.access_token;
  });

  test('should reject invalid credentials', async ({ request }) => {
    const response = await request.post('/api/v1/auth/login', {
      data: {
        email: 'admin@test.com',
        password: 'wrongpassword'
      }
    });

    expect(response.status()).toBe(401);

    const data = await response.json();
    expect(data).toHaveProperty('success', false);
    expect(data).toHaveProperty('error');
  });

  test('should access protected endpoint with valid token', async ({ request }) => {
    // First login to get token
    const loginResponse = await request.post('/api/v1/auth/login', {
      data: {
        email: 'admin@test.com',
        password: 'testpassword123'
      }
    });

    const loginData = await loginResponse.json();
    const token = loginData.access_token;

    // Access protected endpoint
    const response = await request.get('/api/v1/auth/me', {
      headers: {
        'Authorization': `Bearer ${token}`
      }
    });

    expect(response.ok()).toBeTruthy();

    const data = await response.json();
    expect(data).toHaveProperty('email', 'admin@test.com');
  });

  test('should reject access without token', async ({ request }) => {
    const response = await request.get('/api/v1/auth/me');

    expect(response.status()).toBe(401);
  });

  test('should reject access with invalid token', async ({ request }) => {
    const response = await request.get('/api/v1/auth/me', {
      headers: {
        'Authorization': 'Bearer invalid-token'
      }
    });

    expect(response.status()).toBe(401);
  });
});