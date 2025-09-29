const fs = require('fs-extra');
const path = require('path');

const createUsersDatabase = async () => {
  try {
    console.log('👥 Creating Users database...');

    const users = [
      {
        id: 'USR001',
        name: 'John Doe',
        email: 'john.doe@company.com',
        role: 'Admin',
        status: 'Active',
        avatar: '👨‍💼',
        department: 'IT',
        lastLogin: '2025-09-29T10:30:00Z',
        joinDate: '2024-01-15',
        projects: ['PRJ001', 'PRJ002', 'PRJ003'],
        projectCount: 8,
        permissions: ['all'],
        phone: '+66-2-123-4567',
        location: 'Bangkok, Thailand',
        manager: null,
        directReports: ['USR002', 'USR003'],
        skills: ['System Administration', 'Project Management', 'Database Management'],
        certifications: ['PMP', 'AWS Certified', 'CISSP'],
        salary: 75000,
        employeeId: 'EMP001',
        emergencyContact: {
          name: 'Jane Doe',
          relationship: 'Spouse',
          phone: '+66-81-123-4567'
        },
        createdAt: '2024-01-15T09:00:00Z',
        updatedAt: '2025-09-29T10:30:00Z'
      },
      {
        id: 'USR002',
        name: 'Sarah Johnson',
        email: 'sarah.johnson@company.com',
        role: 'Manager',
        status: 'Active',
        avatar: '👩‍💼',
        department: 'Marketing',
        lastLogin: '2025-09-29T09:15:00Z',
        joinDate: '2024-03-22',
        projects: ['PRJ001', 'PRJ006'],
        projectCount: 5,
        permissions: ['projects.manage', 'kols.manage', 'reports.view'],
        phone: '+66-2-234-5678',
        location: 'Bangkok, Thailand',
        manager: 'USR001',
        directReports: ['USR004'],
        skills: ['Digital Marketing', 'Campaign Management', 'KOL Relations'],
        certifications: ['Google Ads', 'Facebook Blueprint'],
        salary: 55000,
        employeeId: 'EMP002',
        emergencyContact: {
          name: 'Robert Johnson',
          relationship: 'Father',
          phone: '+66-81-234-5678'
        },
        createdAt: '2024-03-22T08:30:00Z',
        updatedAt: '2025-09-29T09:15:00Z'
      },
      {
        id: 'USR003',
        name: 'Mike Chen',
        email: 'mike.chen@company.com',
        role: 'Manager',
        status: 'Active',
        avatar: '👨‍💻',
        department: 'Product',
        lastLogin: '2025-09-28T16:45:00Z',
        joinDate: '2024-02-10',
        projects: ['PRJ002'],
        projectCount: 3,
        permissions: ['projects.manage', 'kols.view', 'reports.view'],
        phone: '+66-2-345-6789',
        location: 'Bangkok, Thailand',
        manager: 'USR001',
        directReports: ['USR005'],
        skills: ['Product Management', 'Tech Strategy', 'Data Analysis'],
        certifications: ['Scrum Master', 'Product Owner'],
        salary: 58000,
        employeeId: 'EMP003',
        emergencyContact: {
          name: 'Linda Chen',
          relationship: 'Spouse',
          phone: '+66-81-345-6789'
        },
        createdAt: '2024-02-10T10:15:00Z',
        updatedAt: '2025-09-28T16:45:00Z'
      },
      {
        id: 'USR004',
        name: 'Emma Thai',
        email: 'emma.thai@company.com',
        role: 'Editor',
        status: 'Active',
        avatar: '👩‍🎨',
        department: 'Creative',
        lastLogin: '2025-09-29T08:20:00Z',
        joinDate: '2024-05-18',
        projects: ['PRJ003'],
        projectCount: 7,
        permissions: ['projects.edit', 'kols.edit', 'reports.view'],
        phone: '+66-2-456-7890',
        location: 'Bangkok, Thailand',
        manager: 'USR002',
        directReports: [],
        skills: ['Content Creation', 'Graphic Design', 'Video Editing'],
        certifications: ['Adobe Certified', 'Google Analytics'],
        salary: 42000,
        employeeId: 'EMP004',
        emergencyContact: {
          name: 'Somchai Thai',
          relationship: 'Brother',
          phone: '+66-81-456-7890'
        },
        createdAt: '2024-05-18T11:20:00Z',
        updatedAt: '2025-09-29T08:20:00Z'
      },
      {
        id: 'USR005',
        name: 'David Kim',
        email: 'david.kim@company.com',
        role: 'Editor',
        status: 'Active',
        avatar: '👨‍🏫',
        department: 'Content',
        lastLogin: '2025-09-29T11:10:00Z',
        joinDate: '2024-04-12',
        projects: ['PRJ004'],
        projectCount: 4,
        permissions: ['projects.edit', 'kols.view', 'reports.view'],
        phone: '+66-2-567-8901',
        location: 'Bangkok, Thailand',
        manager: 'USR003',
        directReports: [],
        skills: ['Content Strategy', 'Copywriting', 'SEO'],
        certifications: ['Content Marketing', 'HubSpot'],
        salary: 40000,
        employeeId: 'EMP005',
        emergencyContact: {
          name: 'Grace Kim',
          relationship: 'Sister',
          phone: '+66-81-567-8901'
        },
        createdAt: '2024-04-12T09:45:00Z',
        updatedAt: '2025-09-29T11:10:00Z'
      },
      {
        id: 'USR006',
        name: 'Lisa Wong',
        email: 'lisa.wong@company.com',
        role: 'Viewer',
        status: 'Inactive',
        avatar: '👩‍📊',
        department: 'Analytics',
        lastLogin: '2025-09-25T14:30:00Z',
        joinDate: '2024-06-05',
        projects: ['PRJ005'],
        projectCount: 2,
        permissions: ['reports.view', 'kols.view'],
        phone: '+66-2-678-9012',
        location: 'Bangkok, Thailand',
        manager: 'USR001',
        directReports: [],
        skills: ['Data Analysis', 'Reporting', 'Excel'],
        certifications: ['Google Analytics', 'Tableau'],
        salary: 38000,
        employeeId: 'EMP006',
        emergencyContact: {
          name: 'Peter Wong',
          relationship: 'Husband',
          phone: '+66-81-678-9012'
        },
        createdAt: '2024-06-05T13:15:00Z',
        updatedAt: '2025-09-25T14:30:00Z'
      },
      {
        id: 'USR007',
        name: 'Alex Thompson',
        email: 'alex.thompson@company.com',
        role: 'Manager',
        status: 'Pending',
        avatar: '👨‍💼',
        department: 'Sales',
        lastLogin: 'Never',
        joinDate: '2025-09-28',
        projects: ['PRJ007'],
        projectCount: 0,
        permissions: ['projects.view', 'kols.view'],
        phone: '+66-2-789-0123',
        location: 'Bangkok, Thailand',
        manager: 'USR001',
        directReports: [],
        skills: ['Sales Management', 'Client Relations', 'Business Development'],
        certifications: ['Salesforce Admin'],
        salary: 52000,
        employeeId: 'EMP007',
        emergencyContact: {
          name: 'Maria Thompson',
          relationship: 'Spouse',
          phone: '+66-81-789-0123'
        },
        createdAt: '2025-09-28T16:00:00Z',
        updatedAt: '2025-09-29T12:00:00Z'
      },
      {
        id: 'USR008',
        name: 'Niran Patel',
        email: 'niran.patel@company.com',
        role: 'Editor',
        status: 'Active',
        avatar: '👨‍🎬',
        department: 'Creative',
        lastLogin: '2025-09-29T07:45:00Z',
        joinDate: '2024-07-20',
        projects: ['PRJ001', 'PRJ004'],
        projectCount: 6,
        permissions: ['projects.edit', 'kols.edit', 'reports.view'],
        phone: '+66-2-890-1234',
        location: 'Chiang Mai, Thailand',
        manager: 'USR002',
        directReports: [],
        skills: ['Video Production', 'Motion Graphics', 'Photography'],
        certifications: ['Final Cut Pro', 'Adobe Premiere'],
        salary: 43000,
        employeeId: 'EMP008',
        emergencyContact: {
          name: 'Priya Patel',
          relationship: 'Wife',
          phone: '+66-81-890-1234'
        },
        createdAt: '2024-07-20T14:30:00Z',
        updatedAt: '2025-09-29T07:45:00Z'
      },
      {
        id: 'USR009',
        name: 'Mei Zhang',
        email: 'mei.zhang@company.com',
        role: 'Viewer',
        status: 'Active',
        avatar: '👩‍🔬',
        department: 'Analytics',
        lastLogin: '2025-09-29T12:20:00Z',
        joinDate: '2024-08-15',
        projects: [],
        projectCount: 1,
        permissions: ['reports.view', 'kols.view'],
        phone: '+66-2-901-2345',
        location: 'Bangkok, Thailand',
        manager: 'USR006',
        directReports: [],
        skills: ['Statistical Analysis', 'Machine Learning', 'Python'],
        certifications: ['Google Data Analytics', 'Python Certification'],
        salary: 35000,
        employeeId: 'EMP009',
        emergencyContact: {
          name: 'Wei Zhang',
          relationship: 'Father',
          phone: '+66-81-901-2345'
        },
        createdAt: '2024-08-15T10:00:00Z',
        updatedAt: '2025-09-29T12:20:00Z'
      },
      {
        id: 'USR010',
        name: 'Carlos Rodriguez',
        email: 'carlos.rodriguez@company.com',
        role: 'Manager',
        status: 'Active',
        avatar: '👨‍🚀',
        department: 'Operations',
        lastLogin: '2025-09-29T13:15:00Z',
        joinDate: '2024-01-30',
        projects: ['PRJ002', 'PRJ005'],
        projectCount: 4,
        permissions: ['projects.manage', 'kols.manage', 'reports.view'],
        phone: '+66-2-012-3456',
        location: 'Bangkok, Thailand',
        manager: 'USR001',
        directReports: ['USR008', 'USR009'],
        skills: ['Operations Management', 'Process Optimization', 'Team Leadership'],
        certifications: ['Lean Six Sigma', 'PMP'],
        salary: 60000,
        employeeId: 'EMP010',
        emergencyContact: {
          name: 'Isabella Rodriguez',
          relationship: 'Daughter',
          phone: '+66-81-012-3456'
        },
        createdAt: '2024-01-30T15:20:00Z',
        updatedAt: '2025-09-29T13:15:00Z'
      }
    ];

    // Calculate user statistics
    const stats = {
      totalUsers: users.length,
      byRole: {},
      byStatus: {},
      byDepartment: {},
      avgProjectsPerUser: 0,
      totalProjects: 0,
      activeSince: {},
      avgSalary: 0,
      totalSalary: 0
    };

    users.forEach(user => {
      // Count by role
      stats.byRole[user.role] = (stats.byRole[user.role] || 0) + 1;

      // Count by status
      stats.byStatus[user.status] = (stats.byStatus[user.status] || 0) + 1;

      // Count by department
      stats.byDepartment[user.department] = (stats.byDepartment[user.department] || 0) + 1;

      // Project count
      stats.totalProjects += user.projectCount;

      // Salary calculation
      stats.totalSalary += user.salary;

      // Calculate how long they've been active
      const joinYear = new Date(user.joinDate).getFullYear();
      stats.activeSince[joinYear] = (stats.activeSince[joinYear] || 0) + 1;
    });

    stats.avgProjectsPerUser = Math.round(stats.totalProjects / users.length * 10) / 10;
    stats.avgSalary = Math.round(stats.totalSalary / users.length);

    // Create database object
    const database = {
      users: users,
      stats: stats,
      lastUpdated: new Date().toISOString(),
      version: '1.0.0'
    };

    // Save to database directory
    const dbPath = path.join(__dirname, '..', 'data', 'database', 'users-database.json');
    await fs.writeFile(dbPath, JSON.stringify(database, null, 2));

    // Create frontend API endpoint
    const apiPath = path.join(__dirname, '..', 'frontend', 'public', 'api', 'users.json');
    await fs.ensureDir(path.dirname(apiPath));
    await fs.writeFile(apiPath, JSON.stringify(database, null, 2));

    console.log('✅ Users Database created successfully!');
    console.log(`👥 Total Users: ${users.length}`);
    console.log(`👨‍💼 Managers: ${stats.byRole.Manager || 0}`);
    console.log(`🔧 Active Users: ${stats.byStatus.Active || 0}`);
    console.log(`🏢 Departments: ${Object.keys(stats.byDepartment).length}`);
    console.log(`💾 Database saved to: ${dbPath}`);
    console.log(`🌐 API endpoint created: ${apiPath}`);

    return database;

  } catch (error) {
    console.error('❌ Error creating Users database:', error);
    throw error;
  }
};

// Run the script
createUsersDatabase().catch(console.error);