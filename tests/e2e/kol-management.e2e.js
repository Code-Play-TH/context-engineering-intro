const { test, expect } = require('@playwright/test');

test.describe('KOL Management', () => {
  let authToken;
  let createdKolId;

  test.beforeAll(async ({ request }) => {
    // Login to get auth token
    const loginResponse = await request.post('/api/v1/auth/login', {
      data: {
        email: 'admin@test.com',
        password: 'testpassword123'
      }
    });

    const loginData = await loginResponse.json();
    authToken = loginData.access_token;
  });

  test('should create a new KOL', async ({ request }) => {
    const kolData = {
      name: 'Test Influencer',
      email: 'influencer@test.com',
      social_media_accounts: {
        instagram: {
          handle: 'test_influencer',
          verified: false
        }
      },
      niche: ['fashion', 'lifestyle'],
      communication_preferences: ['email']
    };

    const response = await request.post('/api/v1/kols', {
      headers: {
        'Authorization': `Bearer ${authToken}`,
        'Content-Type': 'application/json'
      },
      data: kolData
    });

    expect(response.ok()).toBeTruthy();

    const data = await response.json();
    expect(data).toHaveProperty('success', true);
    expect(data.data).toHaveProperty('id');
    expect(data.data).toHaveProperty('name', 'Test Influencer');
    expect(data.data).toHaveProperty('email', 'influencer@test.com');

    createdKolId = data.data.id;
  });

  test('should list KOLs with pagination', async ({ request }) => {
    const response = await request.get('/api/v1/kols?page=1&size=10', {
      headers: {
        'Authorization': `Bearer ${authToken}`
      }
    });

    expect(response.ok()).toBeTruthy();

    const data = await response.json();
    expect(data).toHaveProperty('success', true);
    expect(data.data).toHaveProperty('items');
    expect(data.data).toHaveProperty('total');
    expect(data.data).toHaveProperty('page', 1);
    expect(data.data).toHaveProperty('size', 10);
    expect(Array.isArray(data.data.items)).toBeTruthy();
  });

  test('should get KOL by ID', async ({ request }) => {
    if (!createdKolId) {
      test.skip('No KOL created in previous test');
    }

    const response = await request.get(`/api/v1/kols/${createdKolId}`, {
      headers: {
        'Authorization': `Bearer ${authToken}`
      }
    });

    expect(response.ok()).toBeTruthy();

    const data = await response.json();
    expect(data).toHaveProperty('success', true);
    expect(data.data).toHaveProperty('id', createdKolId);
    expect(data.data).toHaveProperty('name', 'Test Influencer');
  });

  test('should update KOL information', async ({ request }) => {
    if (!createdKolId) {
      test.skip('No KOL created in previous test');
    }

    const updateData = {
      name: 'Updated Test Influencer',
      niche: ['fashion', 'lifestyle', 'beauty']
    };

    const response = await request.put(`/api/v1/kols/${createdKolId}`, {
      headers: {
        'Authorization': `Bearer ${authToken}`,
        'Content-Type': 'application/json'
      },
      data: updateData
    });

    expect(response.ok()).toBeTruthy();

    const data = await response.json();
    expect(data).toHaveProperty('success', true);
    expect(data.data).toHaveProperty('name', 'Updated Test Influencer');
    expect(data.data.niche).toContain('beauty');
  });

  test('should filter KOLs by status', async ({ request }) => {
    const response = await request.get('/api/v1/kols?status=active', {
      headers: {
        'Authorization': `Bearer ${authToken}`
      }
    });

    expect(response.ok()).toBeTruthy();

    const data = await response.json();
    expect(data).toHaveProperty('success', true);
    expect(data.data).toHaveProperty('items');

    // All returned KOLs should have active status
    data.data.items.forEach(kol => {
      expect(kol).toHaveProperty('status', 'active');
    });
  });

  test('should filter KOLs by niche', async ({ request }) => {
    const response = await request.get('/api/v1/kols?niche=fashion', {
      headers: {
        'Authorization': `Bearer ${authToken}`
      }
    });

    expect(response.ok()).toBeTruthy();

    const data = await response.json();
    expect(data).toHaveProperty('success', true);
    expect(data.data).toHaveProperty('items');

    // All returned KOLs should have fashion in their niche
    data.data.items.forEach(kol => {
      expect(kol.niche).toContain('fashion');
    });
  });

  test('should return 404 for non-existent KOL', async ({ request }) => {
    const response = await request.get('/api/v1/kols/99999', {
      headers: {
        'Authorization': `Bearer ${authToken}`
      }
    });

    expect(response.status()).toBe(404);

    const data = await response.json();
    expect(data).toHaveProperty('success', false);
  });

  test('should delete KOL', async ({ request }) => {
    if (!createdKolId) {
      test.skip('No KOL created in previous test');
    }

    const response = await request.delete(`/api/v1/kols/${createdKolId}`, {
      headers: {
        'Authorization': `Bearer ${authToken}`
      }
    });

    expect(response.status()).toBe(204);

    // Verify KOL is deleted
    const getResponse = await request.get(`/api/v1/kols/${createdKolId}`, {
      headers: {
        'Authorization': `Bearer ${authToken}`
      }
    });

    expect(getResponse.status()).toBe(404);
  });
});