'use client'

import { SimpleLayout } from '@/components/layout/SimpleLayout'
import { useState, useEffect } from 'react'

interface KOL {
  id: string
  name: string
  tier: string
  category: string
  platform: string
  followers: number
  contact: string
  cost: string
  engagement: string
  status: string
  lastActive: string
  avatar: string
  createdAt: string
  updatedAt: string
}

interface KOLData {
  kols: KOL[]
  pagination: {
    page: number
    limit: number
    total: number
    totalPages: number
  }
  stats: {
    totalKOLs: number
    byTier: Record<string, number>
    byCategory: Record<string, number>
    byPlatform: Record<string, number>
    byStatus: Record<string, number>
    totalFollowers: number
    avgEngagement: string
  }
}

export function SimpleKOLsPageWithLayout() {
  const [kolData, setKolData] = useState<KOLData | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [filteredKOLs, setFilteredKOLs] = useState<KOL[]>([])
  const [selectedPlatform, setSelectedPlatform] = useState('All')
  const [searchTerm, setSearchTerm] = useState('')

  useEffect(() => {
    const fetchKOLData = async () => {
      try {
        const response = await fetch('/api/kols.json')
        if (!response.ok) {
          throw new Error('Failed to fetch KOL data')
        }
        const data = await response.json()
        setKolData(data)
        setFilteredKOLs(data.kols)
      } catch (err) {
        setError(err instanceof Error ? err.message : 'Unknown error')
      } finally {
        setLoading(false)
      }
    }

    fetchKOLData()
  }, [])

  useEffect(() => {
    if (!kolData) return

    let filtered = kolData.kols

    // Filter by platform
    if (selectedPlatform !== 'All') {
      filtered = filtered.filter(kol => kol.platform === selectedPlatform)
    }

    // Filter by search term
    if (searchTerm) {
      filtered = filtered.filter(kol =>
        kol.name.toLowerCase().includes(searchTerm.toLowerCase()) ||
        kol.category.toLowerCase().includes(searchTerm.toLowerCase()) ||
        kol.platform.toLowerCase().includes(searchTerm.toLowerCase())
      )
    }

    setFilteredKOLs(filtered)
  }, [kolData, selectedPlatform, searchTerm])

  const formatFollowers = (followers: number) => {
    if (followers >= 1000000) {
      return `${(followers / 1000000).toFixed(1)}M`
    } else if (followers >= 1000) {
      return `${(followers / 1000).toFixed(1)}K`
    }
    return followers.toString()
  }

  if (loading) {
    return (
      <SimpleLayout title="KOL Management">
        <div style={{
          display: 'flex',
          justifyContent: 'center',
          alignItems: 'center',
          height: '400px',
          fontSize: '18px',
          color: '#6b7280'
        }}>
          Loading KOL data...
        </div>
      </SimpleLayout>
    )
  }

  if (error) {
    return (
      <SimpleLayout title="KOL Management">
        <div style={{
          display: 'flex',
          justifyContent: 'center',
          alignItems: 'center',
          height: '400px',
          fontSize: '18px',
          color: '#ef4444'
        }}>
          Error: {error}
        </div>
      </SimpleLayout>
    )
  }

  if (!kolData) return null

  const stats = [
    {
      title: 'Total KOLs',
      value: kolData.stats.totalKOLs.toLocaleString(),
      change: `${Object.keys(kolData.stats.byCategory).length} Categories`,
      icon: '👥',
      color: '#3b82f6'
    },
    {
      title: 'Active KOLs',
      value: (kolData.stats.byStatus.Active || 0).toLocaleString(),
      change: `${((kolData.stats.byStatus.Active || 0) / kolData.stats.totalKOLs * 100).toFixed(1)}%`,
      icon: '✅',
      color: '#10b981'
    },
    {
      title: 'Total Followers',
      value: formatFollowers(kolData.stats.totalFollowers),
      change: `${kolData.stats.avgEngagement}% Avg Engagement`,
      icon: '🎯',
      color: '#f59e0b'
    }
  ]

  const platforms = ['All', ...Object.keys(kolData.stats.byPlatform)]

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
    <SimpleLayout title="KOL Management">
      <div style={{ padding: '32px' }}>
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
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
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
                border: platform === selectedPlatform ? 'none' : '1px solid #e5e7eb',
                background: platform === selectedPlatform ? '#3b82f6' : 'white',
                color: platform === selectedPlatform ? 'white' : '#374151',
                fontSize: '14px',
                fontWeight: '500',
                cursor: 'pointer',
                transition: 'all 0.2s'
              }}
              onClick={() => setSelectedPlatform(platform)}
              onMouseOver={(e) => {
                if (platform !== selectedPlatform) {
                  e.currentTarget.style.background = '#f3f4f6'
                }
              }}
              onMouseOut={(e) => {
                if (platform !== selectedPlatform) {
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
            gridTemplateColumns: '1fr 100px 100px 100px 120px 80px 80px 80px',
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
            <div>Tier</div>
            <div>Platform</div>
            <div>Followers</div>
            <div>Engagement</div>
            <div>Category</div>
            <div>Status</div>
            <div>Actions</div>
          </div>

          {filteredKOLs.map((kol, index) => (
            <div key={kol.id} style={{
              display: 'grid',
              gridTemplateColumns: '1fr 100px 100px 100px 120px 80px 80px 80px',
              gap: '16px',
              padding: '16px',
              borderBottom: index < filteredKOLs.length - 1 ? '1px solid #f3f4f6' : 'none',
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
                    {kol.contact.substring(0, 30)}{kol.contact.length > 30 ? '...' : ''}
                  </p>
                </div>
              </div>

              <span style={{
                padding: '3px 6px',
                borderRadius: '4px',
                background: kol.tier === 'MEGA' ? '#dc2626' : kol.tier === 'MACRO' ? '#f59e0b' : kol.tier === 'MICRO' ? '#10b981' : '#6b7280',
                color: 'white',
                fontSize: '10px',
                fontWeight: '700',
                textAlign: 'center'
              }}>
                {kol.tier}
              </span>

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
                {formatFollowers(kol.followers)}
              </span>

              <span style={{
                fontSize: '14px',
                fontWeight: '600',
                color: '#1f2937'
              }}>
                {kol.engagement}%
              </span>

              <span style={{
                fontSize: '11px',
                color: '#6b7280',
                textAlign: 'center'
              }}>
                {kol.category.length > 10 ? kol.category.substring(0, 10) + '...' : kol.category}
              </span>

              <span style={{
                padding: '4px 6px',
                borderRadius: '4px',
                background: getStatusColor(kol.status) + '20',
                color: getStatusColor(kol.status),
                fontSize: '10px',
                fontWeight: '600',
                textAlign: 'center'
              }}>
                {kol.status}
              </span>

              <button style={{
                width: '28px',
                height: '28px',
                borderRadius: '6px',
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
            Showing {Math.min(50, filteredKOLs.length)} of {filteredKOLs.length} KOLs
            {selectedPlatform !== 'All' && ` (filtered by ${selectedPlatform})`}
            {searchTerm && ` (search: "${searchTerm}")`}
          </p>
          <div style={{ display: 'flex', gap: '8px' }}>
            <button style={{
              padding: '8px 12px',
              border: '1px solid #e5e7eb',
              borderRadius: '8px',
              background: 'white',
              color: '#6b7280',
              fontSize: '14px',
              cursor: 'pointer',
              opacity: 0.5
            }} disabled>
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
            {filteredKOLs.length > 50 && (
              <>
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
              </>
            )}
          </div>
        </div>
      </div>
    </SimpleLayout>
  )
}