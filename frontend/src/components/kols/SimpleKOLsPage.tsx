'use client'

export function SimpleKOLsPage() {
  const stats = [
    {
      title: 'Total KOLs',
      value: '2,847',
      change: '+12.5%',
      icon: '👥',
      color: '#3b82f6'
    },
    {
      title: 'Active KOLs',
      value: '1,923',
      change: '+8.3%',
      icon: '✅',
      color: '#10b981'
    },
    {
      title: 'Pending Review',
      value: '124',
      change: 'Needs Attention',
      icon: '⏰',
      color: '#f59e0b'
    }
  ]

  const platforms = ['All', 'Instagram', 'TikTok', 'YouTube', 'Twitter']

  const mockKOLs = [
    {
      id: 1,
      name: 'Emma Wilson',
      platform: 'Instagram',
      followers: '2.5M',
      engagement: '4.2%',
      category: 'Beauty',
      status: 'Active',
      avatar: '👩‍💼'
    },
    {
      id: 2,
      name: 'John Smith',
      platform: 'YouTube',
      followers: '1.8M',
      engagement: '3.8%',
      category: 'Tech',
      status: 'Active',
      avatar: '👨‍💻'
    },
    {
      id: 3,
      name: 'Sarah Johnson',
      platform: 'TikTok',
      followers: '3.2M',
      engagement: '5.1%',
      category: 'Lifestyle',
      status: 'Pending',
      avatar: '👩‍🎨'
    },
    {
      id: 4,
      name: 'Mike Chen',
      platform: 'Instagram',
      followers: '980K',
      engagement: '4.7%',
      category: 'Fitness',
      status: 'Active',
      avatar: '💪'
    },
    {
      id: 5,
      name: 'Lisa Park',
      platform: 'YouTube',
      followers: '1.2M',
      engagement: '3.5%',
      category: 'Food',
      status: 'Active',
      avatar: '👩‍🍳'
    }
  ]

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'Active': return '#10b981'
      case 'Pending': return '#f59e0b'
      case 'Inactive': return '#ef4444'
      default: return '#6b7280'
    }
  }

  const getPlatformColor = (platform: string) => {
    switch (platform) {
      case 'Instagram': return '#e1306c'
      case 'YouTube': return '#ff0000'
      case 'TikTok': return '#000000'
      case 'Twitter': return '#1da1f2'
      default: return '#6b7280'
    }
  }

  return (
    <div style={{
      minHeight: '100vh',
      background: 'linear-gradient(135deg, #f8fafc 0%, #e2e8f0 100%)',
      padding: '20px'
    }}>
      {/* Header */}
      <div style={{
        display: 'flex',
        justifyContent: 'space-between',
        alignItems: 'center',
        marginBottom: '40px',
        flexWrap: 'wrap',
        gap: '20px'
      }}>
        <div>
          <h1 style={{
            fontSize: '32px',
            fontWeight: 'bold',
            background: 'linear-gradient(135deg, #1f2937, #6b7280)',
            WebkitBackgroundClip: 'text',
            WebkitTextFillColor: 'transparent',
            margin: '0 0 8px 0'
          }}>
            KOL Database
          </h1>
          <p style={{ color: '#6b7280', margin: 0 }}>
            Manage and analyze your influencer relationships
          </p>
        </div>
        <div style={{ display: 'flex', gap: '12px', flexWrap: 'wrap' }}>
          <button style={{
            padding: '12px 24px',
            border: '1px solid #d1d5db',
            borderRadius: '12px',
            background: 'white',
            color: '#374151',
            fontSize: '14px',
            fontWeight: '500',
            cursor: 'pointer',
            transition: 'all 0.2s',
            display: 'flex',
            alignItems: 'center',
            gap: '8px'
          }}>
            🔍 Filters
          </button>
          <button style={{
            padding: '12px 24px',
            borderRadius: '12px',
            background: 'linear-gradient(135deg, #3b82f6, #8b5cf6)',
            color: 'white',
            border: 'none',
            fontSize: '14px',
            fontWeight: '500',
            cursor: 'pointer',
            transition: 'all 0.2s',
            boxShadow: '0 4px 12px rgba(59, 130, 246, 0.3)',
            display: 'flex',
            alignItems: 'center',
            gap: '8px'
          }}>
            ➕ Add New KOL
          </button>
        </div>
      </div>

      {/* Stats Grid */}
      <div style={{
        display: 'grid',
        gridTemplateColumns: 'repeat(auto-fit, minmax(250px, 1fr))',
        gap: '24px',
        marginBottom: '40px'
      }}>
        {stats.map((stat, index) => (
          <div key={index} style={{
            background: 'rgba(255, 255, 255, 0.9)',
            backdropFilter: 'blur(20px)',
            borderRadius: '16px',
            padding: '24px',
            boxShadow: '0 10px 30px rgba(0, 0, 0, 0.1)',
            border: '1px solid rgba(255, 255, 255, 0.2)',
            transition: 'transform 0.2s',
            cursor: 'pointer'
          }}
          onMouseOver={(e) => {
            e.currentTarget.style.transform = 'translateY(-4px)'
          }}
          onMouseOut={(e) => {
            e.currentTarget.style.transform = 'translateY(0)'
          }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
              <div>
                <p style={{
                  fontSize: '12px',
                  fontWeight: '600',
                  color: '#6b7280',
                  textTransform: 'uppercase',
                  letterSpacing: '0.05em',
                  margin: '0 0 8px 0'
                }}>
                  {stat.title}
                </p>
                <p style={{
                  fontSize: '28px',
                  fontWeight: 'bold',
                  color: '#1f2937',
                  margin: '0 0 8px 0'
                }}>
                  {stat.value}
                </p>
                <span style={{
                  padding: '4px 8px',
                  borderRadius: '6px',
                  background: stat.title === 'Pending Review' ? '#fef3c7' : '#dcfce7',
                  color: stat.title === 'Pending Review' ? '#d97706' : '#16a34a',
                  fontSize: '12px',
                  fontWeight: '600'
                }}>
                  {stat.change}
                </span>
              </div>
              <div style={{
                width: '56px',
                height: '56px',
                borderRadius: '16px',
                background: stat.color,
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                fontSize: '24px',
                boxShadow: `0 8px 16px ${stat.color}40`
              }}>
                {stat.icon}
              </div>
            </div>
          </div>
        ))}
      </div>

      {/* Search and Filters */}
      <div style={{
        display: 'flex',
        justifyContent: 'space-between',
        alignItems: 'center',
        marginBottom: '24px',
        flexWrap: 'wrap',
        gap: '16px'
      }}>
        <div style={{ position: 'relative', flex: '1', maxWidth: '400px' }}>
          <span style={{
            position: 'absolute',
            left: '12px',
            top: '50%',
            transform: 'translateY(-50%)',
            fontSize: '16px',
            color: '#6b7280'
          }}>🔍</span>
          <input
            type="search"
            placeholder="Search KOLs by name, platform, or category..."
            style={{
              width: '100%',
              height: '48px',
              paddingLeft: '40px',
              paddingRight: '16px',
              border: '1px solid #d1d5db',
              borderRadius: '12px',
              fontSize: '14px',
              backgroundColor: 'rgba(255, 255, 255, 0.8)',
              transition: 'all 0.2s',
              outline: 'none'
            }}
            onFocus={(e) => {
              e.target.style.borderColor = '#3b82f6'
              e.target.style.backgroundColor = 'white'
              e.target.style.boxShadow = '0 0 0 3px rgba(59, 130, 246, 0.1)'
            }}
            onBlur={(e) => {
              e.target.style.borderColor = '#d1d5db'
              e.target.style.backgroundColor = 'rgba(255, 255, 255, 0.8)'
              e.target.style.boxShadow = 'none'
            }}
          />
        </div>
        <div style={{ display: 'flex', gap: '8px', flexWrap: 'wrap' }}>
          {platforms.map((platform, index) => (
            <button key={index} style={{
              padding: '8px 16px',
              borderRadius: '8px',
              border: index === 0 ? 'none' : '1px solid #e5e7eb',
              background: index === 0 ? '#3b82f6' : 'white',
              color: index === 0 ? 'white' : '#374151',
              fontSize: '14px',
              fontWeight: '500',
              cursor: 'pointer',
              transition: 'all 0.2s'
            }}
            onMouseOver={(e) => {
              if (index !== 0) {
                e.currentTarget.style.background = '#f3f4f6'
              }
            }}
            onMouseOut={(e) => {
              if (index !== 0) {
                e.currentTarget.style.background = 'white'
              }
            }}>
              {platform}
            </button>
          ))}
        </div>
      </div>

      {/* KOL Table */}
      <div style={{
        background: 'rgba(255, 255, 255, 0.9)',
        backdropFilter: 'blur(20px)',
        borderRadius: '16px',
        padding: '24px',
        boxShadow: '0 10px 30px rgba(0, 0, 0, 0.1)',
        border: '1px solid rgba(255, 255, 255, 0.2)',
        overflow: 'hidden'
      }}>
        <div style={{
          display: 'grid',
          gridTemplateColumns: '1fr 120px 120px 120px 100px 100px 80px',
          gap: '16px',
          padding: '16px',
          borderBottom: '1px solid #e5e7eb',
          background: '#f9fafb',
          borderRadius: '8px',
          marginBottom: '16px',
          fontSize: '12px',
          fontWeight: '600',
          color: '#6b7280',
          textTransform: 'uppercase',
          letterSpacing: '0.05em'
        }}>
          <div>KOL</div>
          <div>Platform</div>
          <div>Followers</div>
          <div>Engagement</div>
          <div>Category</div>
          <div>Status</div>
          <div>Actions</div>
        </div>

        {mockKOLs.map((kol, index) => (
          <div key={kol.id} style={{
            display: 'grid',
            gridTemplateColumns: '1fr 120px 120px 120px 100px 100px 80px',
            gap: '16px',
            padding: '16px',
            borderBottom: index < mockKOLs.length - 1 ? '1px solid #f3f4f6' : 'none',
            transition: 'background 0.2s',
            cursor: 'pointer',
            alignItems: 'center'
          }}
          onMouseOver={(e) => {
            e.currentTarget.style.background = '#f9fafb'
          }}
          onMouseOut={(e) => {
            e.currentTarget.style.background = 'transparent'
          }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
              <div style={{
                width: '40px',
                height: '40px',
                borderRadius: '10px',
                background: 'linear-gradient(135deg, #f3f4f6, #e5e7eb)',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                fontSize: '18px'
              }}>
                {kol.avatar}
              </div>
              <div>
                <p style={{
                  fontSize: '14px',
                  fontWeight: '600',
                  color: '#1f2937',
                  margin: '0 0 4px 0'
                }}>
                  {kol.name}
                </p>
                <p style={{
                  fontSize: '12px',
                  color: '#6b7280',
                  margin: 0
                }}>
                  ID: {kol.id}
                </p>
              </div>
            </div>

            <span style={{
              padding: '4px 8px',
              borderRadius: '6px',
              background: getPlatformColor(kol.platform) + '20',
              color: getPlatformColor(kol.platform),
              fontSize: '12px',
              fontWeight: '600'
            }}>
              {kol.platform}
            </span>

            <span style={{
              fontSize: '14px',
              fontWeight: '600',
              color: '#1f2937'
            }}>
              {kol.followers}
            </span>

            <span style={{
              fontSize: '14px',
              fontWeight: '600',
              color: '#1f2937'
            }}>
              {kol.engagement}
            </span>

            <span style={{
              fontSize: '12px',
              color: '#6b7280'
            }}>
              {kol.category}
            </span>

            <span style={{
              padding: '4px 8px',
              borderRadius: '6px',
              background: getStatusColor(kol.status) + '20',
              color: getStatusColor(kol.status),
              fontSize: '12px',
              fontWeight: '600'
            }}>
              {kol.status}
            </span>

            <button style={{
              width: '32px',
              height: '32px',
              borderRadius: '8px',
              border: '1px solid #e5e7eb',
              background: 'white',
              cursor: 'pointer',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              transition: 'all 0.2s'
            }}
            onMouseOver={(e) => {
              e.currentTarget.style.background = '#f3f4f6'
              e.currentTarget.style.borderColor = '#d1d5db'
            }}
            onMouseOut={(e) => {
              e.currentTarget.style.background = 'white'
              e.currentTarget.style.borderColor = '#e5e7eb'
            }}>
              ⋮
            </button>
          </div>
        ))}
      </div>

      {/* Pagination */}
      <div style={{
        display: 'flex',
        justifyContent: 'space-between',
        alignItems: 'center',
        marginTop: '24px'
      }}>
        <p style={{
          fontSize: '14px',
          color: '#6b7280',
          margin: 0
        }}>
          Showing 1-5 of 2,847 KOLs
        </p>
        <div style={{ display: 'flex', gap: '8px' }}>
          <button style={{
            padding: '8px 12px',
            border: '1px solid #e5e7eb',
            borderRadius: '8px',
            background: 'white',
            color: '#6b7280',
            fontSize: '14px',
            cursor: 'pointer'
          }}>
            Previous
          </button>
          <button style={{
            padding: '8px 12px',
            border: 'none',
            borderRadius: '8px',
            background: '#3b82f6',
            color: 'white',
            fontSize: '14px',
            cursor: 'pointer'
          }}>
            1
          </button>
          <button style={{
            padding: '8px 12px',
            border: '1px solid #e5e7eb',
            borderRadius: '8px',
            background: 'white',
            color: '#6b7280',
            fontSize: '14px',
            cursor: 'pointer'
          }}>
            2
          </button>
          <button style={{
            padding: '8px 12px',
            border: '1px solid #e5e7eb',
            borderRadius: '8px',
            background: 'white',
            color: '#6b7280',
            fontSize: '14px',
            cursor: 'pointer'
          }}>
            Next
          </button>
        </div>
      </div>
    </div>
  )
}