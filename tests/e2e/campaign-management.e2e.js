const { test, expect } = require('@playwright/test');

test.describe('Campaign Management', () => {
  let authToken;
  let createdCampaignId;
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

    // Create a test KOL for campaign assignment
    const kolResponse = await request.post('/api/v1/kols', {
      headers: {
        'Authorization': `Bearer ${authToken}`,
        'Content-Type': 'application/json'
      },
      data: {
        name: 'Campaign Test KOL',
        email: 'campaign_kol@test.com',
        social_media_accounts: {
          instagram: {
            handle: 'campaign_test_kol',
            verified: false
          }
        },
        niche: ['fashion'],
        communication_preferences: ['email']
      }
    });

    if (kolResponse.ok()) {
      const kolData = await kolResponse.json();
      createdKolId = kolData.data.id;
    }
  });

  test('should create a new campaign', async ({ request }) => {
    const campaignData = {
      name: 'Test Fashion Campaign',
      description: 'A test campaign for fashion products',
      start_date: '2024-12-01T00:00:00Z',
      end_date: '2024-12-31T23:59:59Z',
      budget: 10000.00,
      target_kpis: {
        total_reach: 100000,
        engagement_rate: 0.05,
        roi_percentage: 200
      },
      required_keywords: ['fashion', 'style'],
      required_hashtags: ['#fashion', '#style'],
      brand_names: ['TestBrand']
    };

    const response = await request.post('/api/v1/campaigns', {
      headers: {
        'Authorization': `Bearer ${authToken}`,
        'Content-Type': 'application/json'
      },
      data: campaignData
    });

    expect(response.ok()).toBeTruthy();

    const data = await response.json();
    expect(data).toHaveProperty('success', true);
    expect(data.data).toHaveProperty('id');
    expect(data.data).toHaveProperty('name', 'Test Fashion Campaign');
    expect(data.data).toHaveProperty('budget', 10000.00);

    createdCampaignId = data.data.id;
  });

  test('should list campaigns with filters', async ({ request }) => {
    const response = await request.get('/api/v1/campaigns?status=draft', {
      headers: {
        'Authorization': `Bearer ${authToken}`
      }
    });

    expect(response.ok()).toBeTruthy();

    const data = await response.json();
    expect(data).toHaveProperty('success', true);
    expect(data.data).toHaveProperty('items');
    expect(Array.isArray(data.data.items)).toBeTruthy();
  });

  test('should get campaign by ID', async ({ request }) => {
    if (!createdCampaignId) {
      test.skip('No campaign created in previous test');
    }

    const response = await request.get(`/api/v1/campaigns/${createdCampaignId}`, {
      headers: {
        'Authorization': `Bearer ${authToken}`
      }
    });

    expect(response.ok()).toBeTruthy();

    const data = await response.json();
    expect(data).toHaveProperty('success', true);
    expect(data.data).toHaveProperty('id', createdCampaignId);
    expect(data.data).toHaveProperty('name', 'Test Fashion Campaign');
  });

  test('should assign KOL to campaign', async ({ request }) => {
    if (!createdCampaignId || !createdKolId) {
      test.skip('Campaign or KOL not created');
    }

    const assignmentData = {
      kol_id: createdKolId,
      compensation: 2000.00,
      currency: 'USD',
      deliverables_total: 3,
      notes: 'Test assignment for campaign'
    };

    const response = await request.post(`/api/v1/campaigns/${createdCampaignId}/assign-kol`, {
      headers: {
        'Authorization': `Bearer ${authToken}`,
        'Content-Type': 'application/json'
      },
      data: assignmentData
    });

    expect(response.ok()).toBeTruthy();

    const data = await response.json();
    expect(data).toHaveProperty('success', true);
    expect(data.data).toHaveProperty('campaign_id', createdCampaignId);
    expect(data.data).toHaveProperty('kol_id', createdKolId);
    expect(data.data).toHaveProperty('compensation', 2000.00);
  });

  test('should get campaign performance', async ({ request }) => {
    if (!createdCampaignId) {
      test.skip('No campaign created');
    }

    const response = await request.get(`/api/v1/campaigns/${createdCampaignId}/performance`, {
      headers: {
        'Authorization': `Bearer ${authToken}`
      }
    });

    expect(response.ok()).toBeTruthy();

    const data = await response.json();
    expect(data).toHaveProperty('success', true);
    expect(data.data).toHaveProperty('campaign_id', createdCampaignId);
    expect(data.data).toHaveProperty('total_reach');
    expect(data.data).toHaveProperty('total_engagement');
    expect(data.data).toHaveProperty('engagement_rate');
    expect(data.data).toHaveProperty('roi_percentage');
  });

  test('should update campaign status', async ({ request }) => {
    if (!createdCampaignId) {
      test.skip('No campaign created');
    }

    const updateData = {
      status: 'active'
    };

    const response = await request.put(`/api/v1/campaigns/${createdCampaignId}`, {
      headers: {
        'Authorization': `Bearer ${authToken}`,
        'Content-Type': 'application/json'
      },
      data: updateData
    });

    expect(response.ok()).toBeTruthy();

    const data = await response.json();
    expect(data).toHaveProperty('success', true);
    expect(data.data).toHaveProperty('status', 'active');
  });

  test('should generate campaign report', async ({ request }) => {
    if (!createdCampaignId) {
      test.skip('No campaign created');
    }

    const reportData = {
      report_type: 'comprehensive',
      include_comparisons: false,
      include_forecasts: false,
      format: 'json',
      sections: ['executive_summary', 'performance_metrics']
    };

    const response = await request.post(`/api/v1/campaigns/${createdCampaignId}/generate-report`, {
      headers: {
        'Authorization': `Bearer ${authToken}`,
        'Content-Type': 'application/json'
      },
      data: reportData
    });

    expect(response.ok()).toBeTruthy();

    const data = await response.json();
    expect(data).toHaveProperty('success', true);
    expect(data.data).toHaveProperty('report_data');
    expect(data.data.report_data).toHaveProperty('executive_summary');
    expect(data.data.report_data).toHaveProperty('performance_metrics');
  });

  test.afterAll(async ({ request }) => {
    // Clean up created resources
    if (createdCampaignId) {
      await request.delete(`/api/v1/campaigns/${createdCampaignId}`, {
        headers: {
          'Authorization': `Bearer ${authToken}`
        }
      });
    }

    if (createdKolId) {
      await request.delete(`/api/v1/kols/${createdKolId}`, {
        headers: {
          'Authorization': `Bearer ${authToken}`
        }
      });
    }
  });
});