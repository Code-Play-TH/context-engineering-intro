const fs = require('fs-extra');
const path = require('path');

const createProjectsDatabase = async () => {
  try {
    console.log('🏗️ Creating Projects database...');

    const projects = [
      {
        id: 'PRJ001',
        name: 'Summer Lifestyle Campaign',
        description: 'Promote summer fashion and lifestyle products through lifestyle influencers targeting young adults aged 18-35',
        status: 'Active',
        budget: 250000,
        spent: 162500,
        startDate: '2025-06-01',
        endDate: '2025-08-31',
        assignedKOLs: ['Lifestyle_1', 'Lifestyle_3', 'Lifestyle_5', 'Lifestyle_8', 'Lifestyle_12'],
        assignedKOLCount: 12,
        category: 'Lifestyle',
        manager: 'Sarah Johnson',
        managerId: 'USR002',
        progress: 65,
        estimatedReach: '2.5M',
        actualReach: '1.8M',
        roi: 380,
        engagement: 145000,
        conversions: 2850,
        platforms: ['TikTok', 'Instagram'],
        targetAudience: {
          ageRange: '18-35',
          gender: 'All',
          location: 'Thailand',
          interests: ['Fashion', 'Lifestyle', 'Beauty']
        },
        kpis: {
          reachTarget: 2500000,
          engagementTarget: 150000,
          conversionTarget: 3000,
          roiTarget: 350
        },
        createdAt: '2025-05-15T09:00:00Z',
        updatedAt: '2025-09-28T14:30:00Z'
      },
      {
        id: 'PRJ002',
        name: 'Tech Product Launch',
        description: 'Launch new smartphone through tech reviewers and IT influencers with focus on features and performance',
        status: 'Planning',
        budget: 500000,
        spent: 125000,
        startDate: '2025-10-01',
        endDate: '2025-12-15',
        assignedKOLs: ['IT_1', 'IT_2', 'IT_4', 'IT_6'],
        assignedKOLCount: 8,
        category: 'IT',
        manager: 'Mike Chen',
        managerId: 'USR003',
        progress: 25,
        estimatedReach: '1.2M',
        actualReach: null,
        roi: null,
        engagement: null,
        conversions: null,
        platforms: ['YouTube', 'TikTok'],
        targetAudience: {
          ageRange: '25-45',
          gender: 'All',
          location: 'Thailand, Singapore',
          interests: ['Technology', 'Gadgets', 'Innovation']
        },
        kpis: {
          reachTarget: 1200000,
          engagementTarget: 84000,
          conversionTarget: 1500,
          roiTarget: 280
        },
        createdAt: '2025-09-01T10:00:00Z',
        updatedAt: '2025-09-29T11:15:00Z'
      },
      {
        id: 'PRJ003',
        name: 'Food Festival Promotion',
        description: 'Promote annual food festival through food bloggers and cooking channels to drive ticket sales',
        status: 'Completed',
        budget: 180000,
        spent: 178500,
        startDate: '2025-03-01',
        endDate: '2025-05-31',
        assignedKOLs: ['Food_cooking_1', 'Food_cooking_3', 'Food_cooking_5', 'Food_cooking_8'],
        assignedKOLCount: 15,
        category: 'Food_cooking',
        manager: 'Emma Thai',
        managerId: 'USR004',
        progress: 100,
        estimatedReach: '1.8M',
        actualReach: '2.1M',
        roi: 450,
        engagement: 189000,
        conversions: 4200,
        platforms: ['TikTok', 'Instagram', 'Facebook'],
        targetAudience: {
          ageRange: '20-50',
          gender: 'All',
          location: 'Bangkok, Chiang Mai',
          interests: ['Food', 'Cooking', 'Local Events']
        },
        kpis: {
          reachTarget: 1800000,
          engagementTarget: 144000,
          conversionTarget: 3500,
          roiTarget: 400
        },
        createdAt: '2025-02-01T08:30:00Z',
        updatedAt: '2025-06-01T16:45:00Z'
      },
      {
        id: 'PRJ004',
        name: 'Health & Wellness Series',
        description: 'Year-long health awareness campaign with fitness influencers promoting healthy lifestyle and supplements',
        status: 'Active',
        budget: 350000,
        spent: 157500,
        startDate: '2025-01-01',
        endDate: '2025-12-31',
        assignedKOLs: ['Healthy_1', 'Healthy_2', 'Healthy_4', 'Healthy_7'],
        assignedKOLCount: 20,
        category: 'Healthy',
        manager: 'David Kim',
        managerId: 'USR005',
        progress: 45,
        estimatedReach: '3.2M',
        actualReach: '1.5M',
        roi: 280,
        engagement: 168000,
        conversions: 2100,
        platforms: ['TikTok', 'Instagram', 'YouTube'],
        targetAudience: {
          ageRange: '20-45',
          gender: 'All',
          location: 'Thailand',
          interests: ['Fitness', 'Health', 'Nutrition', 'Wellness']
        },
        kpis: {
          reachTarget: 3200000,
          engagementTarget: 256000,
          conversionTarget: 4500,
          roiTarget: 320
        },
        createdAt: '2024-12-01T07:00:00Z',
        updatedAt: '2025-09-29T09:20:00Z'
      },
      {
        id: 'PRJ005',
        name: 'Travel Documentary',
        description: 'Document hidden gems in Thailand through travel vloggers to promote domestic tourism',
        status: 'Paused',
        budget: 400000,
        spent: 120000,
        startDate: '2025-04-01',
        endDate: '2025-09-30',
        assignedKOLs: ['Travel_1', 'Travel_3', 'Travel_5'],
        assignedKOLCount: 6,
        category: 'Travel',
        manager: 'Lisa Wong',
        managerId: 'USR006',
        progress: 30,
        estimatedReach: '1.5M',
        actualReach: '450K',
        roi: 150,
        engagement: 31500,
        conversions: 680,
        platforms: ['YouTube', 'Instagram'],
        targetAudience: {
          ageRange: '25-55',
          gender: 'All',
          location: 'Thailand, International',
          interests: ['Travel', 'Tourism', 'Culture', 'Adventure']
        },
        kpis: {
          reachTarget: 1500000,
          engagementTarget: 105000,
          conversionTarget: 2000,
          roiTarget: 250
        },
        createdAt: '2025-03-15T12:00:00Z',
        updatedAt: '2025-07-20T15:30:00Z'
      },
      {
        id: 'PRJ006',
        name: 'Pet Care Awareness',
        description: 'Educational campaign about pet care through cat and pet influencers',
        status: 'Active',
        budget: 150000,
        spent: 67500,
        startDate: '2025-07-01',
        endDate: '2025-11-30',
        assignedKOLs: ['Cat_1', 'Cat_2', 'Cat_4'],
        assignedKOLCount: 8,
        category: 'Cat',
        manager: 'Sarah Johnson',
        managerId: 'USR002',
        progress: 45,
        estimatedReach: '800K',
        actualReach: '380K',
        roi: 220,
        engagement: 42000,
        conversions: 920,
        platforms: ['TikTok', 'Instagram'],
        targetAudience: {
          ageRange: '20-50',
          gender: 'Female',
          location: 'Thailand',
          interests: ['Pets', 'Animals', 'Pet Care']
        },
        kpis: {
          reachTarget: 800000,
          engagementTarget: 64000,
          conversionTarget: 1200,
          roiTarget: 250
        },
        createdAt: '2025-06-15T11:30:00Z',
        updatedAt: '2025-09-29T13:45:00Z'
      },
      {
        id: 'PRJ007',
        name: 'POV Content Strategy',
        description: 'Creative POV content campaign for brand storytelling and engagement',
        status: 'Planning',
        budget: 220000,
        spent: 44000,
        startDate: '2025-11-01',
        endDate: '2026-02-28',
        assignedKOLs: ['POV_1', 'POV_3'],
        assignedKOLCount: 5,
        category: 'POV',
        manager: 'Alex Thompson',
        managerId: 'USR007',
        progress: 15,
        estimatedReach: '1.1M',
        actualReach: null,
        roi: null,
        engagement: null,
        conversions: null,
        platforms: ['TikTok', 'Instagram'],
        targetAudience: {
          ageRange: '16-30',
          gender: 'All',
          location: 'Thailand',
          interests: ['Entertainment', 'Storytelling', 'Creative Content']
        },
        kpis: {
          reachTarget: 1100000,
          engagementTarget: 88000,
          conversionTarget: 1800,
          roiTarget: 300
        },
        createdAt: '2025-09-20T14:00:00Z',
        updatedAt: '2025-09-29T10:15:00Z'
      }
    ];

    // Calculate project statistics
    const stats = {
      totalProjects: projects.length,
      byStatus: {},
      byCategory: {},
      byManager: {},
      totalBudget: 0,
      totalSpent: 0,
      avgProgress: 0,
      totalEstimatedReach: 0,
      totalActualReach: 0,
      avgROI: 0
    };

    projects.forEach(project => {
      // Count by status
      stats.byStatus[project.status] = (stats.byStatus[project.status] || 0) + 1;

      // Count by category
      stats.byCategory[project.category] = (stats.byCategory[project.category] || 0) + 1;

      // Count by manager
      stats.byManager[project.manager] = (stats.byManager[project.manager] || 0) + 1;

      // Sum budgets and spending
      stats.totalBudget += project.budget;
      stats.totalSpent += project.spent;

      // Progress calculation
      stats.avgProgress += project.progress;

      // Reach calculation
      const estimatedReach = parseFloat(project.estimatedReach.replace(/[MK]/g, match => match === 'M' ? '000000' : '000'));
      stats.totalEstimatedReach += estimatedReach;

      if (project.actualReach) {
        const actualReach = parseFloat(project.actualReach.replace(/[MK]/g, match => match === 'M' ? '000000' : '000'));
        stats.totalActualReach += actualReach;
      }

      // ROI calculation
      if (project.roi) {
        stats.avgROI += project.roi;
      }
    });

    stats.avgProgress = Math.round(stats.avgProgress / projects.length);
    stats.avgROI = Math.round(stats.avgROI / projects.filter(p => p.roi).length);

    // Create database object
    const database = {
      projects: projects,
      stats: stats,
      lastUpdated: new Date().toISOString(),
      version: '1.0.0'
    };

    // Save to database directory
    const dbPath = path.join(__dirname, '..', 'data', 'database', 'projects-database.json');
    await fs.writeFile(dbPath, JSON.stringify(database, null, 2));

    // Create frontend API endpoint
    const apiPath = path.join(__dirname, '..', 'frontend', 'public', 'api', 'projects.json');
    await fs.ensureDir(path.dirname(apiPath));
    await fs.writeFile(apiPath, JSON.stringify(database, null, 2));

    console.log('✅ Projects Database created successfully!');
    console.log(`📊 Total Projects: ${projects.length}`);
    console.log(`💰 Total Budget: ${(stats.totalBudget / 1000000).toFixed(1)}M THB`);
    console.log(`📈 Active Projects: ${stats.byStatus.Active || 0}`);
    console.log(`💾 Database saved to: ${dbPath}`);
    console.log(`🌐 API endpoint created: ${apiPath}`);

    return database;

  } catch (error) {
    console.error('❌ Error creating Projects database:', error);
    throw error;
  }
};

// Run the script
createProjectsDatabase().catch(console.error);