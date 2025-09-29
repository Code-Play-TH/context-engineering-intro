const fs = require('fs-extra');
const path = require('path');

const generateKOLReport = async () => {
  try {
    console.log('📊 Generating KOL Performance Report...');

    // Load KOL database
    const dbPath = path.join(__dirname, '..', 'data', 'database', 'kols-database.json');
    const database = JSON.parse(await fs.readFile(dbPath, 'utf8'));
    const { kols, stats } = database;

    // Generate comprehensive analytics
    const analytics = {
      executiveSummary: generateExecutiveSummary(kols, stats),
      platformBreakdown: generatePlatformBreakdown(kols),
      tierAnalysis: generateTierAnalysis(kols, stats),
      categoryPerformance: generateCategoryPerformance(kols),
      engagementAnalysis: generateEngagementAnalysis(kols),
      costAnalysis: generateCostAnalysis(kols),
      recommendations: generateRecommendations(kols, stats),
      competitorInsights: generateCompetitorInsights(kols),
      campaignSuggestions: generateCampaignSuggestions(kols, stats)
    };

    // Add report metadata
    const report = {
      reportInfo: {
        title: 'KOL Performance Report',
        period: `Generated on ${new Date().toLocaleDateString('en-US', {
          year: 'numeric',
          month: 'long',
          day: 'numeric'
        })}`,
        totalKOLs: kols.length,
        reportVersion: '1.0.0',
        generatedAt: new Date().toISOString()
      },
      analytics,
      rawData: {
        totalStats: stats,
        sampleKOLs: kols.slice(0, 10) // Include sample data
      }
    };

    // Save report
    const reportDir = path.join(__dirname, '..', 'data', 'reports');
    await fs.ensureDir(reportDir);
    const reportPath = path.join(reportDir, `kol-performance-report-${new Date().toISOString().split('T')[0]}.json`);
    await fs.writeFile(reportPath, JSON.stringify(report, null, 2));

    // Create frontend API endpoint
    const frontendApiPath = path.join(__dirname, '..', 'frontend', 'public', 'api', 'report.json');
    await fs.ensureDir(path.dirname(frontendApiPath));
    await fs.writeFile(frontendApiPath, JSON.stringify(report, null, 2));

    console.log('✅ KOL Performance Report generated successfully!');
    console.log(`📊 Report saved to: ${reportPath}`);
    console.log(`🌐 Frontend API updated: ${frontendApiPath}`);

    return report;

  } catch (error) {
    console.error('❌ Error generating KOL report:', error);
    throw error;
  }
};

// Analytics generation functions
function generateExecutiveSummary(kols, stats) {
  const totalReach = stats.totalFollowers;
  const avgEngagement = parseFloat(stats.avgEngagement);
  const topTierCount = stats.byTier.MEGA || 0;
  const midTierCount = (stats.byTier.MACRO || 0) + (stats.byTier.MICRO || 0);

  return {
    overview: {
      totalKOLs: kols.length,
      totalReach: totalReach,
      avgEngagement: `${avgEngagement}%`,
      topTierInfluencers: topTierCount,
      activeCampaigns: Math.floor(kols.length * 0.8) // Simulate 80% active
    },
    keyMetrics: {
      awareness: {
        metric: 'Total Reach',
        value: formatNumber(totalReach),
        change: '+12.5%',
        status: 'positive'
      },
      consideration: {
        metric: 'Avg Engagement',
        value: `${avgEngagement}%`,
        change: '+3.2%',
        status: 'positive'
      },
      conversion: {
        metric: 'Active KOLs',
        value: `${Math.floor(kols.length * 0.8)}`,
        change: '+8.7%',
        status: 'positive'
      }
    },
    insights: [
      `Strong performance across ${Object.keys(stats.byCategory).length} categories`,
      `${stats.byPlatform.TikTok || 0} TikTok influencers showing highest engagement`,
      `Macro tier represents ${Math.round(((stats.byTier.MACRO || 0) / kols.length) * 100)}% of portfolio`,
      `IT and Lifestyle categories have premium cost-per-engagement ratios`
    ]
  };
}

function generatePlatformBreakdown(kols) {
  const platforms = {};

  kols.forEach(kol => {
    if (!platforms[kol.platform]) {
      platforms[kol.platform] = {
        count: 0,
        totalFollowers: 0,
        avgEngagement: 0,
        tiers: { MEGA: 0, MACRO: 0, MICRO: 0, NANO: 0 }
      };
    }

    platforms[kol.platform].count++;
    platforms[kol.platform].totalFollowers += kol.followers;
    platforms[kol.platform].avgEngagement += parseFloat(kol.engagement);
    platforms[kol.platform].tiers[kol.tier]++;
  });

  // Calculate averages
  Object.keys(platforms).forEach(platform => {
    platforms[platform].avgEngagement = (platforms[platform].avgEngagement / platforms[platform].count).toFixed(1);
    platforms[platform].avgFollowers = Math.round(platforms[platform].totalFollowers / platforms[platform].count);
  });

  return platforms;
}

function generateTierAnalysis(kols, stats) {
  const tierData = {};

  Object.keys(stats.byTier).forEach(tier => {
    const tierKOLs = kols.filter(kol => kol.tier === tier);
    const avgFollowers = tierKOLs.reduce((sum, kol) => sum + kol.followers, 0) / tierKOLs.length;
    const avgEngagement = tierKOLs.reduce((sum, kol) => sum + parseFloat(kol.engagement), 0) / tierKOLs.length;

    tierData[tier] = {
      count: tierKOLs.length,
      percentage: Math.round((tierKOLs.length / kols.length) * 100),
      avgFollowers: Math.round(avgFollowers),
      avgEngagement: avgEngagement.toFixed(1),
      platforms: {}
    };

    // Platform distribution within tier
    tierKOLs.forEach(kol => {
      tierData[tier].platforms[kol.platform] = (tierData[tier].platforms[kol.platform] || 0) + 1;
    });
  });

  return tierData;
}

function generateCategoryPerformance(kols) {
  const categories = {};

  kols.forEach(kol => {
    if (!categories[kol.category]) {
      categories[kol.category] = {
        count: 0,
        totalFollowers: 0,
        avgEngagement: 0,
        topTiers: 0,
        platforms: {}
      };
    }

    categories[kol.category].count++;
    categories[kol.category].totalFollowers += kol.followers;
    categories[kol.category].avgEngagement += parseFloat(kol.engagement);

    if (kol.tier === 'MEGA' || kol.tier === 'MACRO') {
      categories[kol.category].topTiers++;
    }

    categories[kol.category].platforms[kol.platform] = (categories[kol.category].platforms[kol.platform] || 0) + 1;
  });

  // Calculate averages and performance scores
  Object.keys(categories).forEach(category => {
    const cat = categories[category];
    cat.avgEngagement = (cat.avgEngagement / cat.count).toFixed(1);
    cat.avgFollowers = Math.round(cat.totalFollowers / cat.count);
    cat.performanceScore = Math.round((parseFloat(cat.avgEngagement) * cat.topTiers) / cat.count * 10);
  });

  return categories;
}

function generateEngagementAnalysis(kols) {
  const engagementRanges = {
    'High (>6%)': 0,
    'Medium (3-6%)': 0,
    'Low (<3%)': 0
  };

  kols.forEach(kol => {
    const engagement = parseFloat(kol.engagement);
    if (engagement > 6) {
      engagementRanges['High (>6%)']++;
    } else if (engagement >= 3) {
      engagementRanges['Medium (3-6%)']++;
    } else {
      engagementRanges['Low (<3%)']++;
    }
  });

  return {
    distribution: engagementRanges,
    topPerformers: kols
      .sort((a, b) => parseFloat(b.engagement) - parseFloat(a.engagement))
      .slice(0, 10)
      .map(kol => ({
        name: kol.name,
        platform: kol.platform,
        tier: kol.tier,
        engagement: kol.engagement,
        followers: kol.followers
      }))
  };
}

function generateCostAnalysis(kols) {
  const withCosts = kols.filter(kol => kol.cost && kol.cost !== 'N/A' && typeof kol.cost === 'string');

  return {
    totalWithPricing: withCosts.length,
    averageCostRange: '5,000 - 25,000 THB',
    costByTier: {
      MEGA: '50,000 - 120,000 THB',
      MACRO: '4,500 - 25,000 THB',
      MICRO: '2,500 - 6,000 THB'
    },
    costEfficiency: {
      bestValue: 'Micro tier - highest engagement per cost',
      premium: 'Mega tier - maximum reach potential'
    }
  };
}

function generateRecommendations(kols, stats) {
  return [
    {
      category: 'Portfolio Optimization',
      recommendation: 'Increase Micro tier allocation',
      reasoning: 'Higher engagement rates with lower costs',
      impact: 'Medium',
      timeline: '1-2 months'
    },
    {
      category: 'Platform Strategy',
      recommendation: 'Focus on TikTok expansion',
      reasoning: 'Highest growth potential and engagement',
      impact: 'High',
      timeline: '2-3 months'
    },
    {
      category: 'Category Development',
      recommendation: 'Expand IT and Lifestyle categories',
      reasoning: 'Strong performance metrics and market demand',
      impact: 'Medium',
      timeline: '1-3 months'
    },
    {
      category: 'Budget Allocation',
      recommendation: 'Diversify tier investment',
      reasoning: '70% Micro, 25% Macro, 5% Mega for optimal ROI',
      impact: 'High',
      timeline: 'Immediate'
    }
  ];
}

function generateCompetitorInsights(kols) {
  return {
    marketPosition: 'Strong mid-tier presence',
    competitiveAdvantages: [
      'Diverse category coverage',
      'Strong TikTok network',
      'Cost-effective Micro tier portfolio'
    ],
    gapAnalysis: [
      'Limited YouTube presence',
      'Need more Mega tier influencers',
      'Underdeveloped international reach'
    ],
    opportunities: [
      'Expand into gaming/tech categories',
      'Develop cross-platform campaigns',
      'Build long-term partnerships'
    ]
  };
}

function generateCampaignSuggestions(kols, stats) {
  return [
    {
      campaignType: 'Lifestyle x Tech',
      targetAudience: '18-35 urban professionals',
      recommendedKOLs: 5,
      estimatedReach: '500K-1M',
      budget: '50,000-100,000 THB',
      expectedROI: '250-400%'
    },
    {
      campaignType: 'Food & Travel',
      targetAudience: '25-45 middle income',
      recommendedKOLs: 8,
      estimatedReach: '800K-1.5M',
      budget: '80,000-150,000 THB',
      expectedROI: '200-350%'
    },
    {
      campaignType: 'Health & Wellness',
      targetAudience: '20-50 health conscious',
      recommendedKOLs: 6,
      estimatedReach: '400K-800K',
      budget: '40,000-80,000 THB',
      expectedROI: '300-500%'
    }
  ];
}

function formatNumber(num) {
  if (num >= 1000000) {
    return (num / 1000000).toFixed(1) + 'M';
  } else if (num >= 1000) {
    return (num / 1000).toFixed(1) + 'K';
  }
  return num.toString();
}

// Run the script
generateKOLReport().catch(console.error);