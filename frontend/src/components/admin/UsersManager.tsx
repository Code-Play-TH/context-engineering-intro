'use client'

import { useState, useEffect } from 'react'

interface User {
  id: string
  name: string
  email: string
  role: 'Admin' | 'Manager' | 'Editor' | 'Viewer'
  status: 'Active' | 'Inactive' | 'Pending'
  avatar: string
  department: string
  lastLogin: string
  joinDate: string
  projects: string[]
  projectCount: number
  permissions: string[]
  phone?: string
  location?: string
  manager?: string
  directReports?: string[]
  skills?: string[]
  certifications?: string[]
  salary?: number
  employeeId?: string
}

const mockUsers: User[] = [
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
    projects: 8,
    permissions: ['all']
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
    projects: 5,
    permissions: ['projects.manage', 'kols.manage', 'reports.view']
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
    projects: 3,
    permissions: ['projects.manage', 'kols.view', 'reports.view']
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
    projects: 7,
    permissions: ['projects.edit', 'kols.edit', 'reports.view']
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
    projects: 4,
    permissions: ['projects.edit', 'kols.view', 'reports.view']
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
    projects: 2,
    permissions: ['reports.view', 'kols.view']
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
    projects: 0,
    permissions: ['projects.view', 'kols.view']
  }
]

export function UsersManager() {
  const [users, setUsers] = useState<User[]>([])
  const [loading, setLoading] = useState(true)
  const [selectedRole, setSelectedRole] = useState<string>('All')
  const [selectedStatus, setSelectedStatus] = useState<string>('All')
  const [searchTerm, setSearchTerm] = useState('')
  const [showCreateModal, setShowCreateModal] = useState(false)
  const [selectedUser, setSelectedUser] = useState<User | null>(null)

  useEffect(() => {
    const fetchUsers = async () => {
      try {
        const response = await fetch('/api/users.json')
        const data = await response.json()
        setUsers(data.users || [])
      } catch (error) {
        console.error('Error fetching users:', error)
        setUsers(mockUsers) // Fallback to mock data
      } finally {
        setLoading(false)
      }
    }

    fetchUsers()
  }, [])

  const roles = ['All', 'Admin', 'Manager', 'Editor', 'Viewer']
  const statuses = ['All', 'Active', 'Inactive', 'Pending']

  const filteredUsers = users.filter(user => {
    const matchesRole = selectedRole === 'All' || user.role === selectedRole
    const matchesStatus = selectedStatus === 'All' || user.status === selectedStatus
    const matchesSearch = user.name.toLowerCase().includes(searchTerm.toLowerCase()) ||
                         user.email.toLowerCase().includes(searchTerm.toLowerCase()) ||
                         user.department.toLowerCase().includes(searchTerm.toLowerCase())
    return matchesRole && matchesStatus && matchesSearch
  })

  const getRoleColor = (role: string) => {
    switch (role) {
      case 'Admin': return '#dc2626'
      case 'Manager': return '#3b82f6'
      case 'Editor': return '#f59e0b'
      case 'Viewer': return '#10b981'
      default: return '#6b7280'
    }
  }

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'Active': return '#10b981'
      case 'Inactive': return '#6b7280'
      case 'Pending': return '#f59e0b'
      default: return '#6b7280'
    }
  }

  const formatLastLogin = (lastLogin: string) => {
    if (lastLogin === 'Never') return 'Never'
    const date = new Date(lastLogin)
    const now = new Date()
    const diffInHours = Math.floor((now.getTime() - date.getTime()) / (1000 * 60 * 60))

    if (diffInHours < 1) return 'Just now'
    if (diffInHours < 24) return `${diffInHours}h ago`
    const diffInDays = Math.floor(diffInHours / 24)
    if (diffInDays === 1) return '1 day ago'
    if (diffInDays < 7) return `${diffInDays} days ago`
    return date.toLocaleDateString()
  }

  if (loading) {
    return (
      <div style={{
        display: 'flex',
        justifyContent: 'center',
        alignItems: 'center',
        height: '400px',
        fontSize: '18px',
        color: '#6b7280'
      }}>
        👥 Loading Users...
      </div>
    )
  }

  return (
    <div style={{ padding: '24px', maxWidth: '1400px', margin: '0 auto' }}>
      {/* Header */}
      <div style={{
        background: 'rgba(255, 255, 255, 0.95)',
        backdropFilter: 'blur(20px)',
        borderRadius: '20px',
        padding: '32px',
        marginBottom: '24px',
        boxShadow: '0 20px 40px rgba(0, 0, 0, 0.1)',
        border: '1px solid rgba(229, 231, 235, 0.5)'
      }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '24px' }}>
          <div>
            <h1 style={{
              fontSize: '32px',
              fontWeight: '700',
              background: 'linear-gradient(135deg, #1f2937, #3b82f6)',
              WebkitBackgroundClip: 'text',
              WebkitTextFillColor: 'transparent',
              margin: '0 0 8px 0'
            }}>
              👥 User Management
            </h1>
            <p style={{ fontSize: '16px', color: '#6b7280', margin: 0 }}>
              Manage team members and their permissions
            </p>
          </div>
          <button
            onClick={() => setShowCreateModal(true)}
            style={{
              background: 'linear-gradient(135deg, #3b82f6, #8b5cf6)',
              color: 'white',
              border: 'none',
              borderRadius: '12px',
              padding: '12px 24px',
              fontSize: '14px',
              fontWeight: '600',
              cursor: 'pointer',
              boxShadow: '0 4px 12px rgba(59, 130, 246, 0.3)',
              transition: 'transform 0.2s'
            }}
            onMouseOver={(e) => {
              e.currentTarget.style.transform = 'translateY(-2px)'
              e.currentTarget.style.boxShadow = '0 6px 16px rgba(59, 130, 246, 0.4)'
            }}
            onMouseOut={(e) => {
              e.currentTarget.style.transform = 'translateY(0)'
              e.currentTarget.style.boxShadow = '0 4px 12px rgba(59, 130, 246, 0.3)'
            }}
          >
            ➕ Invite User
          </button>
        </div>

        {/* Filters */}
        <div style={{ display: 'flex', gap: '16px', alignItems: 'center', flexWrap: 'wrap' }}>
          <div style={{ flex: 1, minWidth: '300px' }}>
            <input
              type="text"
              placeholder="Search users..."
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              style={{
                width: '100%',
                padding: '12px 16px',
                border: '1px solid rgba(229, 231, 235, 0.5)',
                borderRadius: '12px',
                fontSize: '14px',
                background: 'rgba(255, 255, 255, 0.8)',
                backdropFilter: 'blur(10px)'
              }}
            />
          </div>
          <div style={{ display: 'flex', gap: '8px', flexWrap: 'wrap' }}>
            {roles.map(role => (
              <button
                key={role}
                onClick={() => setSelectedRole(role)}
                style={{
                  padding: '8px 16px',
                  border: '1px solid rgba(229, 231, 235, 0.5)',
                  borderRadius: '8px',
                  background: selectedRole === role
                    ? 'linear-gradient(135deg, #3b82f6, #1d4ed8)'
                    : 'rgba(255, 255, 255, 0.8)',
                  color: selectedRole === role ? 'white' : '#6b7280',
                  fontSize: '14px',
                  fontWeight: '500',
                  cursor: 'pointer',
                  transition: 'all 0.2s'
                }}
              >
                {role}
              </button>
            ))}
          </div>
          <div style={{ display: 'flex', gap: '8px', flexWrap: 'wrap' }}>
            {statuses.map(status => (
              <button
                key={status}
                onClick={() => setSelectedStatus(status)}
                style={{
                  padding: '8px 16px',
                  border: '1px solid rgba(229, 231, 235, 0.5)',
                  borderRadius: '8px',
                  background: selectedStatus === status
                    ? 'linear-gradient(135deg, #10b981, #059669)'
                    : 'rgba(255, 255, 255, 0.8)',
                  color: selectedStatus === status ? 'white' : '#6b7280',
                  fontSize: '14px',
                  fontWeight: '500',
                  cursor: 'pointer',
                  transition: 'all 0.2s'
                }}
              >
                {status}
              </button>
            ))}
          </div>
        </div>
      </div>

      {/* User Stats */}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))', gap: '16px', marginBottom: '24px' }}>
        {[
          { label: 'Total Users', value: users.length, color: '#3b82f6' },
          { label: 'Active Users', value: users.filter(u => u.status === 'Active').length, color: '#10b981' },
          { label: 'Pending Users', value: users.filter(u => u.status === 'Pending').length, color: '#f59e0b' },
          { label: 'Admin Users', value: users.filter(u => u.role === 'Admin').length, color: '#dc2626' }
        ].map((stat, index) => (
          <div key={index} style={{
            background: 'rgba(255, 255, 255, 0.95)',
            backdropFilter: 'blur(20px)',
            padding: '20px',
            borderRadius: '16px',
            boxShadow: '0 10px 20px rgba(0, 0, 0, 0.05)',
            border: '1px solid rgba(229, 231, 235, 0.5)',
            textAlign: 'center'
          }}>
            <div style={{ fontSize: '24px', fontWeight: '700', color: stat.color, marginBottom: '4px' }}>
              {stat.value}
            </div>
            <div style={{ fontSize: '12px', color: '#6b7280', textTransform: 'uppercase', fontWeight: '600' }}>
              {stat.label}
            </div>
          </div>
        ))}
      </div>

      {/* Users Table */}
      <div style={{
        background: 'rgba(255, 255, 255, 0.95)',
        backdropFilter: 'blur(20px)',
        borderRadius: '20px',
        padding: '24px',
        boxShadow: '0 20px 40px rgba(0, 0, 0, 0.1)',
        border: '1px solid rgba(229, 231, 235, 0.5)',
        overflowX: 'auto'
      }}>
        <table style={{ width: '100%', borderCollapse: 'collapse' }}>
          <thead>
            <tr style={{ borderBottom: '2px solid rgba(229, 231, 235, 0.5)' }}>
              <th style={{ textAlign: 'left', padding: '16px 12px', fontSize: '12px', fontWeight: '600', color: '#6b7280', textTransform: 'uppercase' }}>User</th>
              <th style={{ textAlign: 'left', padding: '16px 12px', fontSize: '12px', fontWeight: '600', color: '#6b7280', textTransform: 'uppercase' }}>Role</th>
              <th style={{ textAlign: 'left', padding: '16px 12px', fontSize: '12px', fontWeight: '600', color: '#6b7280', textTransform: 'uppercase' }}>Status</th>
              <th style={{ textAlign: 'left', padding: '16px 12px', fontSize: '12px', fontWeight: '600', color: '#6b7280', textTransform: 'uppercase' }}>Department</th>
              <th style={{ textAlign: 'left', padding: '16px 12px', fontSize: '12px', fontWeight: '600', color: '#6b7280', textTransform: 'uppercase' }}>Projects</th>
              <th style={{ textAlign: 'left', padding: '16px 12px', fontSize: '12px', fontWeight: '600', color: '#6b7280', textTransform: 'uppercase' }}>Last Login</th>
              <th style={{ textAlign: 'right', padding: '16px 12px', fontSize: '12px', fontWeight: '600', color: '#6b7280', textTransform: 'uppercase' }}>Actions</th>
            </tr>
          </thead>
          <tbody>
            {filteredUsers.map(user => (
              <tr key={user.id} style={{
                borderBottom: '1px solid rgba(229, 231, 235, 0.3)',
                transition: 'background 0.2s'
              }}
              onMouseOver={(e) => {
                e.currentTarget.style.background = 'rgba(59, 130, 246, 0.05)'
              }}
              onMouseOut={(e) => {
                e.currentTarget.style.background = 'transparent'
              }}>
                <td style={{ padding: '16px 12px' }}>
                  <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
                    <div style={{
                      width: '40px',
                      height: '40px',
                      borderRadius: '10px',
                      background: 'linear-gradient(135deg, #3b82f6, #8b5cf6)',
                      display: 'flex',
                      alignItems: 'center',
                      justifyContent: 'center',
                      fontSize: '16px'
                    }}>
                      {user.avatar}
                    </div>
                    <div>
                      <div style={{ fontSize: '14px', fontWeight: '600', color: '#1f2937' }}>
                        {user.name}
                      </div>
                      <div style={{ fontSize: '12px', color: '#6b7280' }}>
                        {user.email}
                      </div>
                    </div>
                  </div>
                </td>
                <td style={{ padding: '16px 12px' }}>
                  <span style={{
                    background: getRoleColor(user.role),
                    color: 'white',
                    padding: '4px 12px',
                    borderRadius: '8px',
                    fontSize: '12px',
                    fontWeight: '600'
                  }}>
                    {user.role}
                  </span>
                </td>
                <td style={{ padding: '16px 12px' }}>
                  <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                    <div style={{
                      width: '8px',
                      height: '8px',
                      borderRadius: '50%',
                      background: getStatusColor(user.status)
                    }}></div>
                    <span style={{ fontSize: '14px', color: '#374151' }}>
                      {user.status}
                    </span>
                  </div>
                </td>
                <td style={{ padding: '16px 12px', fontSize: '14px', color: '#374151' }}>
                  {user.department}
                </td>
                <td style={{ padding: '16px 12px', fontSize: '14px', color: '#374151', textAlign: 'center' }}>
                  {user.projectCount}
                </td>
                <td style={{ padding: '16px 12px', fontSize: '14px', color: '#6b7280' }}>
                  {formatLastLogin(user.lastLogin)}
                </td>
                <td style={{ padding: '16px 12px', textAlign: 'right' }}>
                  <button
                    onClick={() => setSelectedUser(user)}
                    style={{
                      background: 'rgba(59, 130, 246, 0.1)',
                      color: '#3b82f6',
                      border: '1px solid rgba(59, 130, 246, 0.2)',
                      borderRadius: '8px',
                      padding: '6px 12px',
                      fontSize: '12px',
                      fontWeight: '500',
                      cursor: 'pointer',
                      transition: 'all 0.2s'
                    }}
                    onMouseOver={(e) => {
                      e.currentTarget.style.background = 'rgba(59, 130, 246, 0.2)'
                    }}
                    onMouseOut={(e) => {
                      e.currentTarget.style.background = 'rgba(59, 130, 246, 0.1)'
                    }}
                  >
                    Edit
                  </button>
                </td>
              </tr>
            ))}
          </tbody>
        </table>

        {filteredUsers.length === 0 && (
          <div style={{
            textAlign: 'center',
            padding: '48px',
            color: '#6b7280'
          }}>
            <div style={{ fontSize: '48px', marginBottom: '16px' }}>👥</div>
            <h3 style={{ fontSize: '18px', fontWeight: '600', color: '#1f2937', marginBottom: '8px' }}>
              No users found
            </h3>
            <p style={{ fontSize: '14px', margin: 0 }}>
              Try adjusting your filters or invite new team members
            </p>
          </div>
        )}
      </div>

      {/* Create User Modal */}
      {showCreateModal && (
        <div style={{
          position: 'fixed',
          inset: 0,
          background: 'rgba(0, 0, 0, 0.5)',
          zIndex: 50,
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          padding: '24px'
        }}
        onClick={() => setShowCreateModal(false)}>
          <div style={{
            background: 'rgba(255, 255, 255, 0.95)',
            backdropFilter: 'blur(20px)',
            borderRadius: '20px',
            padding: '32px',
            maxWidth: '500px',
            width: '100%',
            boxShadow: '0 20px 40px rgba(0, 0, 0, 0.2)'
          }}
          onClick={(e) => e.stopPropagation()}>
            <h3 style={{ fontSize: '20px', fontWeight: '700', color: '#1f2937', marginBottom: '16px' }}>
              Invite New User
            </h3>
            <p style={{ fontSize: '14px', color: '#6b7280', marginBottom: '24px' }}>
              User invitation form would be implemented here with fields for email, role, department, and permissions.
            </p>
            <div style={{ display: 'flex', gap: '12px', justifyContent: 'flex-end' }}>
              <button
                onClick={() => setShowCreateModal(false)}
                style={{
                  padding: '8px 16px',
                  border: '1px solid rgba(229, 231, 235, 0.5)',
                  borderRadius: '8px',
                  background: 'rgba(255, 255, 255, 0.8)',
                  color: '#6b7280',
                  fontSize: '14px',
                  cursor: 'pointer'
                }}
              >
                Cancel
              </button>
              <button
                onClick={() => setShowCreateModal(false)}
                style={{
                  padding: '8px 16px',
                  border: 'none',
                  borderRadius: '8px',
                  background: 'linear-gradient(135deg, #3b82f6, #1d4ed8)',
                  color: 'white',
                  fontSize: '14px',
                  cursor: 'pointer'
                }}
              >
                Send Invitation
              </button>
            </div>
          </div>
        </div>
      )}

      {/* User Details Modal */}
      {selectedUser && (
        <div style={{
          position: 'fixed',
          inset: 0,
          background: 'rgba(0, 0, 0, 0.5)',
          zIndex: 50,
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          padding: '24px'
        }}
        onClick={() => setSelectedUser(null)}>
          <div style={{
            background: 'rgba(255, 255, 255, 0.95)',
            backdropFilter: 'blur(20px)',
            borderRadius: '20px',
            padding: '32px',
            maxWidth: '600px',
            width: '100%',
            boxShadow: '0 20px 40px rgba(0, 0, 0, 0.2)'
          }}
          onClick={(e) => e.stopPropagation()}>
            <div style={{ display: 'flex', alignItems: 'center', gap: '16px', marginBottom: '24px' }}>
              <div style={{
                width: '60px',
                height: '60px',
                borderRadius: '15px',
                background: 'linear-gradient(135deg, #3b82f6, #8b5cf6)',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                fontSize: '24px'
              }}>
                {selectedUser.avatar}
              </div>
              <div>
                <h3 style={{ fontSize: '24px', fontWeight: '700', color: '#1f2937', margin: '0 0 4px 0' }}>
                  {selectedUser.name}
                </h3>
                <p style={{ fontSize: '14px', color: '#6b7280', margin: 0 }}>
                  {selectedUser.email}
                </p>
              </div>
            </div>

            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '16px', marginBottom: '24px' }}>
              <div>
                <label style={{ fontSize: '12px', color: '#6b7280', textTransform: 'uppercase', fontWeight: '600' }}>Role</label>
                <div style={{ fontSize: '14px', color: '#1f2937', marginTop: '4px' }}>{selectedUser.role}</div>
              </div>
              <div>
                <label style={{ fontSize: '12px', color: '#6b7280', textTransform: 'uppercase', fontWeight: '600' }}>Status</label>
                <div style={{ fontSize: '14px', color: '#1f2937', marginTop: '4px' }}>{selectedUser.status}</div>
              </div>
              <div>
                <label style={{ fontSize: '12px', color: '#6b7280', textTransform: 'uppercase', fontWeight: '600' }}>Department</label>
                <div style={{ fontSize: '14px', color: '#1f2937', marginTop: '4px' }}>{selectedUser.department}</div>
              </div>
              <div>
                <label style={{ fontSize: '12px', color: '#6b7280', textTransform: 'uppercase', fontWeight: '600' }}>Projects</label>
                <div style={{ fontSize: '14px', color: '#1f2937', marginTop: '4px' }}>{selectedUser.projectCount}</div>
              </div>
            </div>

            <div style={{ marginBottom: '24px' }}>
              <label style={{ fontSize: '12px', color: '#6b7280', textTransform: 'uppercase', fontWeight: '600', marginBottom: '8px', display: 'block' }}>Permissions</label>
              <div style={{ display: 'flex', gap: '8px', flexWrap: 'wrap' }}>
                {selectedUser.permissions.map((permission, index) => (
                  <span key={index} style={{
                    background: 'rgba(59, 130, 246, 0.1)',
                    color: '#3b82f6',
                    padding: '4px 8px',
                    borderRadius: '6px',
                    fontSize: '12px',
                    fontWeight: '500'
                  }}>
                    {permission}
                  </span>
                ))}
              </div>
            </div>

            <div style={{ display: 'flex', gap: '12px', justifyContent: 'flex-end' }}>
              <button
                onClick={() => setSelectedUser(null)}
                style={{
                  padding: '8px 16px',
                  border: '1px solid rgba(229, 231, 235, 0.5)',
                  borderRadius: '8px',
                  background: 'rgba(255, 255, 255, 0.8)',
                  color: '#6b7280',
                  fontSize: '14px',
                  cursor: 'pointer'
                }}
              >
                Close
              </button>
              <button
                style={{
                  padding: '8px 16px',
                  border: 'none',
                  borderRadius: '8px',
                  background: 'linear-gradient(135deg, #3b82f6, #1d4ed8)',
                  color: 'white',
                  fontSize: '14px',
                  cursor: 'pointer'
                }}
              >
                Edit User
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}