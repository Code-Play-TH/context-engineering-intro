const fs = require('fs-extra');
const path = require('path');

// Database schema for KOLs
const createKOLDatabase = async () => {
  try {
    console.log('🏗️ Creating KOL database schema...');

    // Read all CSV data
    const csvDir = path.join(__dirname, '..', 'data', 'csv');
    const dbDir = path.join(__dirname, '..', 'data', 'database');
    await fs.ensureDir(dbDir);

    // Load all JSON data
    const categories = ['Lifestyle', 'Healthy', 'Food_cooking', 'Travel', 'Cat', 'POV', 'IT'];
    let allKOLs = [];

    for (const category of categories) {
      const jsonPath = path.join(csvDir, `${category}.json`);

      if (fs.existsSync(jsonPath)) {
        console.log(`📊 Processing ${category} data...`);
        const data = JSON.parse(await fs.readFile(jsonPath, 'utf8'));

        // Clean and process data
        const processedKOLs = data
          .filter(item => item.TIER || item.Tier) // Filter valid KOL entries
          .map((item, index) => {
            const tier = item.TIER || item.Tier || 'UNKNOWN';
            const categories = item.Categories || item.Catagories || category;
            const name = item['List / Link'] || item['List / Link'] || `KOL_${index}`;
            const contact = item.Contact || 'N/A';
            let followers = item.Follower || 0;

            // Clean followers data
            if (typeof followers === 'string') {
              followers = followers.replace(/[^\d.MKk]/g, '');
              if (followers.includes('M')) {
                followers = parseFloat(followers) * 1000000;
              } else if (followers.includes('K') || followers.includes('k')) {
                followers = parseFloat(followers) * 1000;
              } else {
                followers = parseFloat(followers) || 0;
              }
            }

            let cost = item.Cost || 'N/A';
            if (typeof cost === 'string' && cost.length > 500) {
              cost = cost.substring(0, 500) + '...';
            }

            return {
              id: `${category}_${index + 1}`,
              name: name,
              tier: tier.toUpperCase(),
              category: categories,
              platform: detectPlatform(name, contact),
              followers: Math.round(followers),
              contact: contact,
              cost: cost,
              engagement: generateEngagement(followers),
              status: Math.random() > 0.2 ? 'Active' : 'Pending',
              lastActive: generateLastActive(),
              avatar: generateAvatar(category),
              createdAt: new Date().toISOString(),
              updatedAt: new Date().toISOString()
            };
          });

        allKOLs = allKOLs.concat(processedKOLs);
        console.log(`✅ Processed ${processedKOLs.length} KOLs from ${category}`);
      }
    }

    // Add some statistics
    const stats = {
      totalKOLs: allKOLs.length,
      byTier: {},
      byCategory: {},
      byPlatform: {},
      byStatus: {},
      totalFollowers: 0,
      avgEngagement: 0
    };

    allKOLs.forEach(kol => {
      // Count by tier
      stats.byTier[kol.tier] = (stats.byTier[kol.tier] || 0) + 1;

      // Count by category
      stats.byCategory[kol.category] = (stats.byCategory[kol.category] || 0) + 1;

      // Count by platform
      stats.byPlatform[kol.platform] = (stats.byPlatform[kol.platform] || 0) + 1;

      // Count by status
      stats.byStatus[kol.status] = (stats.byStatus[kol.status] || 0) + 1;

      // Sum followers
      stats.totalFollowers += kol.followers;
    });

    stats.avgEngagement = (allKOLs.reduce((sum, kol) => sum + parseFloat(kol.engagement), 0) / allKOLs.length).toFixed(2);

    // Save database
    const database = {
      kols: allKOLs,
      stats: stats,
      lastUpdated: new Date().toISOString(),
      version: '1.0.0'
    };

    const dbPath = path.join(dbDir, 'kols-database.json');
    await fs.writeFile(dbPath, JSON.stringify(database, null, 2));

    console.log('\n🎉 KOL Database created successfully!');
    console.log(`📊 Total KOLs: ${allKOLs.length}`);
    console.log(`📈 Stats:`, stats);
    console.log(`💾 Database saved to: ${dbPath}`);

    // Create API endpoint data
    const apiData = {
      kols: allKOLs.slice(0, 50), // Limit for demo
      pagination: {
        page: 1,
        limit: 50,
        total: allKOLs.length,
        totalPages: Math.ceil(allKOLs.length / 50)
      },
      stats: stats
    };

    const apiPath = path.join(__dirname, '..', 'frontend', 'public', 'api', 'kols.json');
    await fs.ensureDir(path.dirname(apiPath));
    await fs.writeFile(apiPath, JSON.stringify(apiData, null, 2));

    console.log(`🌐 API data saved to: ${apiPath}`);

    return database;

  } catch (error) {
    console.error('❌ Error creating KOL database:', error);
    throw error;
  }
};

// Helper functions
function detectPlatform(name, contact) {
  const text = (name + ' ' + contact).toLowerCase();

  if (text.includes('tiktok') || text.includes('@')) return 'TikTok';
  if (text.includes('instagram') || text.includes('ig')) return 'Instagram';
  if (text.includes('youtube') || text.includes('yt')) return 'YouTube';
  if (text.includes('facebook') || text.includes('fb')) return 'Facebook';
  if (text.includes('line')) return 'Line';

  // Default based on patterns
  if (name.includes('_')) return 'Instagram';
  return 'TikTok';
}

function generateEngagement(followers) {
  // Generate realistic engagement rate based on followers
  if (followers > 1000000) return (Math.random() * 2 + 2).toFixed(1); // 2-4%
  if (followers > 100000) return (Math.random() * 3 + 3).toFixed(1); // 3-6%
  if (followers > 10000) return (Math.random() * 4 + 4).toFixed(1); // 4-8%
  return (Math.random() * 6 + 5).toFixed(1); // 5-11%
}

function generateLastActive() {
  const days = Math.floor(Math.random() * 30);
  const date = new Date();
  date.setDate(date.getDate() - days);
  return date.toISOString().split('T')[0];
}

function generateAvatar(category) {
  const avatars = {
    'Lifestyle': ['👩‍💼', '👨‍💼', '🌟', '✨', '💫'],
    'Healthy': ['💪', '🏃‍♀️', '🏃‍♂️', '🥗', '🧘‍♀️'],
    'Food_cooking': ['👩‍🍳', '👨‍🍳', '🍽️', '🥘', '🍜'],
    'Travel': ['✈️', '🌍', '📸', '🎒', '🗺️'],
    'Cat': ['🐱', '😺', '😸', '😹', '😻'],
    'POV': ['🎭', '🎪', '🎨', '🎬', '📱'],
    'IT': ['👨‍💻', '👩‍💻', '💻', '📱', '⚙️']
  };

  const categoryAvatars = avatars[category] || ['👤', '👥', '🌟'];
  return categoryAvatars[Math.floor(Math.random() * categoryAvatars.length)];
}

// Run the script
createKOLDatabase().catch(console.error);