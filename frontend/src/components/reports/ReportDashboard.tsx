'use client'

import { useState, useEffect } from 'react'

interface ReportData {
  reportInfo: {
    title: string
    period: string
    totalKOLs: number
    reportVersion: string
    generatedAt: string
  }
  analytics: {
    executiveSummary: any
    platformBreakdown: any
    tierAnalysis: any
    categoryPerformance: any
    engagementAnalysis: any
    costAnalysis: any
    recommendations: any[]
    competitorInsights: any
    campaignSuggestions: any[]
  }
}

export function ReportDashboard() {
  const [reportData, setReportData] = useState<ReportData | null>(null)
  const [loading, setLoading] = useState(true)
  const [activeTab, setActiveTab] = useState('executive')

  useEffect(() => {
    const fetchReportData = async () => {
      try {
        const response = await fetch('/api/report.json')
        const data = await response.json()
        setReportData(data)
      } catch (error) {
        console.error('Error fetching report data:', error)
      } finally {
        setLoading(false)
      }
    }

    fetchReportData()
  }, [])

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
        📊 Loading Performance Report...
      </div>
    )
  }

  if (!reportData) {
    return (
      <div style={{
        display: 'flex',
        justifyContent: 'center',
        alignItems: 'center',
        height: '400px',
        fontSize: '18px',
        color: '#ef4444'
      }}>
        ❌ Error loading report data
      </div>
    )
  }

  const tabs = [
    { id: 'executive', label: 'Executive Summary', icon: '📊' },
    { id: 'platforms', label: 'Platform Analysis', icon: '📱' },
    { id: 'tiers', label: 'Tier Breakdown', icon: '🏆' },
    { id: 'categories', label: 'Category Performance', icon: '📋' },
    { id: 'engagement', label: 'Engagement Analysis', icon: '💬' },
    { id: 'recommendations', label: 'Recommendations', icon: '💡' }
  ]

  return (
    <div style={{ padding: '24px', maxWidth: '1400px', margin: '0 auto' }}>
      {/* Report Header */}
      <div style={{
        background: 'rgba(255, 255, 255, 0.95)',
        backdropFilter: 'blur(20px)',
        borderRadius: '20px',
        padding: '32px',
        marginBottom: '24px',
        boxShadow: '0 20px 40px rgba(0, 0, 0, 0.1)',
        border: '1px solid rgba(229, 231, 235, 0.5)'
      }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '16px' }}>
          <h1 style={{
            fontSize: '32px',
            fontWeight: '700',
            background: 'linear-gradient(135deg, #1f2937, #3b82f6)',
            WebkitBackgroundClip: 'text',
            WebkitTextFillColor: 'transparent',
            margin: 0
          }}>
            📊 {reportData.reportInfo.title}
          </h1>
          <div style={{
            background: 'linear-gradient(135deg, #f3f4f6, #e5e7eb)',
            padding: '8px 16px',
            borderRadius: '12px',
            fontSize: '14px',
            fontWeight: '600',
            color: '#374151'
          }}>
            v{reportData.reportInfo.reportVersion}
          </div>
        </div>
        <p style={{
          fontSize: '16px',
          color: '#6b7280',
          margin: 0
        }}>
          {reportData.reportInfo.period} • {reportData.reportInfo.totalKOLs} Total KOLs
        </p>
      </div>

      {/* Tab Navigation */}
      <div style={{
        background: 'rgba(255, 255, 255, 0.95)',
        backdropFilter: 'blur(20px)',
        borderRadius: '16px',
        padding: '8px',
        marginBottom: '24px',
        boxShadow: '0 10px 20px rgba(0, 0, 0, 0.05)',
        border: '1px solid rgba(229, 231, 235, 0.5)',
        display: 'flex',
        gap: '8px',
        overflowX: 'auto'
      }}>
        {tabs.map(tab => (
          <button
            key={tab.id}
            onClick={() => setActiveTab(tab.id)}
            style={{
              padding: '12px 20px',
              borderRadius: '12px',
              border: 'none',
              background: activeTab === tab.id
                ? 'linear-gradient(135deg, #3b82f6, #1d4ed8)'
                : 'transparent',
              color: activeTab === tab.id ? 'white' : '#6b7280',
              fontSize: '14px',
              fontWeight: '600',
              cursor: 'pointer',
              transition: 'all 0.2s',
              whiteSpace: 'nowrap',
              boxShadow: activeTab === tab.id ? '0 4px 12px rgba(59, 130, 246, 0.3)' : 'none'
            }}
            onMouseOver={(e) => {
              if (activeTab !== tab.id) {
                e.currentTarget.style.background = 'rgba(59, 130, 246, 0.1)'
              }
            }}
            onMouseOut={(e) => {
              if (activeTab !== tab.id) {
                e.currentTarget.style.background = 'transparent'
              }
            }}
          >
            {tab.icon} {tab.label}
          </button>
        ))}
      </div>

      {/* Tab Content */}
      <div style={{
        background: 'rgba(255, 255, 255, 0.95)',
        backdropFilter: 'blur(20px)',
        borderRadius: '20px',
        padding: '32px',
        boxShadow: '0 20px 40px rgba(0, 0, 0, 0.1)',
        border: '1px solid rgba(229, 231, 235, 0.5)',
        minHeight: '600px'
      }}>
        {activeTab === 'executive' && (
          <ExecutiveSummary data={reportData.analytics.executiveSummary} />
        )}
        {activeTab === 'platforms' && (
          <PlatformAnalysis data={reportData.analytics.platformBreakdown} />
        )}
        {activeTab === 'tiers' && (
          <TierAnalysis data={reportData.analytics.tierAnalysis} />
        )}
        {activeTab === 'categories' && (
          <CategoryPerformance data={reportData.analytics.categoryPerformance} />
        )}
        {activeTab === 'engagement' && (
          <EngagementAnalysis data={reportData.analytics.engagementAnalysis} />
        )}
        {activeTab === 'recommendations' && (
          <Recommendations
            recommendations={reportData.analytics.recommendations}
            campaigns={reportData.analytics.campaignSuggestions}
            insights={reportData.analytics.competitorInsights}
          />
        )}
      </div>
    </div>
  )
}

// Component implementations
function ExecutiveSummary({ data }: { data: any }) {
  return (
    <div>
      <h2 style={{ fontSize: '24px', fontWeight: '700', color: '#1f2937', marginBottom: '24px' }}>
        Executive Summary
      </h2>

      {/* Key Metrics */}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(250px, 1fr))', gap: '20px', marginBottom: '32px' }}>
        {Object.entries(data.keyMetrics).map(([key, metric]: [string, any]) => (
          <div key={key} style={{
            background: 'linear-gradient(135deg, #f8fafc, #e2e8f0)',
            padding: '24px',
            borderRadius: '16px',
            border: '1px solid rgba(229, 231, 235, 0.5)'
          }}>
            <h3 style={{ fontSize: '14px', fontWeight: '600', color: '#6b7280', textTransform: 'uppercase', marginBottom: '8px' }}>
              {key}
            </h3>
            <div style={{ fontSize: '28px', fontWeight: '700', color: '#1f2937', marginBottom: '4px' }}>
              {metric.value}
            </div>
            <div style={{ fontSize: '14px', color: metric.status === 'positive' ? '#10b981' : '#ef4444' }}>
              {metric.change} • {metric.metric}
            </div>
          </div>
        ))}
      </div>

      {/* Overview Stats */}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))', gap: '16px', marginBottom: '32px' }}>
        {Object.entries(data.overview).map(([key, value]: [string, any]) => (
          <div key={key} style={{
            background: 'rgba(255, 255, 255, 0.8)',
            padding: '20px',
            borderRadius: '12px',
            border: '1px solid rgba(229, 231, 235, 0.3)',
            textAlign: 'center'
          }}>
            <div style={{ fontSize: '20px', fontWeight: '700', color: '#3b82f6', marginBottom: '4px' }}>
              {typeof value === 'number' ? value.toLocaleString() : value}
            </div>
            <div style={{ fontSize: '12px', color: '#6b7280', textTransform: 'uppercase', fontWeight: '600' }}>
              {key.replace(/([A-Z])/g, ' $1').trim()}
            </div>
          </div>
        ))}
      </div>

      {/* Key Insights */}
      <div>
        <h3 style={{ fontSize: '18px', fontWeight: '600', color: '#1f2937', marginBottom: '16px' }}>
          Key Insights
        </h3>
        <div style={{ display: 'grid', gap: '12px' }}>
          {data.insights.map((insight: string, index: number) => (
            <div key={index} style={{
              background: 'rgba(59, 130, 246, 0.05)',
              padding: '16px',
              borderRadius: '12px',
              borderLeft: '4px solid #3b82f6',
              fontSize: '14px',
              color: '#374151'
            }}>
              💡 {insight}
            </div>
          ))}
        </div>
      </div>
    </div>
  )
}

function PlatformAnalysis({ data }: { data: any }) {
  return (
    <div>
      <h2 style={{ fontSize: '24px', fontWeight: '700', color: '#1f2937', marginBottom: '24px' }}>
        Platform Performance Breakdown
      </h2>

      <div style={{ display: 'grid', gap: '24px' }}>
        {Object.entries(data).map(([platform, stats]: [string, any]) => (
          <div key={platform} style={{
            background: 'linear-gradient(135deg, #f8fafc, #e2e8f0)',
            padding: '24px',
            borderRadius: '16px',
            border: '1px solid rgba(229, 231, 235, 0.5)'
          }}>
            <div style={{ display: 'flex', alignItems: 'center', marginBottom: '20px' }}>
              <div style={{
                width: '48px',
                height: '48px',
                borderRadius: '12px',
                background: platform === 'TikTok' ? '#fe2c55' :
                           platform === 'Instagram' ? '#e4405f' :
                           platform === 'YouTube' ? '#ff0000' :
                           platform === 'Facebook' ? '#1877f2' : '#6b7280',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                color: 'white',
                fontSize: '20px',
                fontWeight: '700',
                marginRight: '16px'
              }}>
                {platform.charAt(0)}
              </div>
              <div>
                <h3 style={{ fontSize: '20px', fontWeight: '700', color: '#1f2937', margin: 0 }}>
                  {platform}
                </h3>
                <p style={{ fontSize: '14px', color: '#6b7280', margin: 0 }}>
                  {stats.count} KOLs • {(stats.totalFollowers / 1000000).toFixed(1)}M Total Reach
                </p>
              </div>
            </div>

            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(150px, 1fr))', gap: '16px' }}>
              <div style={{ textAlign: 'center' }}>
                <div style={{ fontSize: '24px', fontWeight: '700', color: '#3b82f6' }}>
                  {stats.avgEngagement}%
                </div>
                <div style={{ fontSize: '12px', color: '#6b7280', textTransform: 'uppercase' }}>
                  Avg Engagement
                </div>
              </div>
              <div style={{ textAlign: 'center' }}>
                <div style={{ fontSize: '24px', fontWeight: '700', color: '#10b981' }}>
                  {(stats.avgFollowers / 1000).toFixed(0)}K
                </div>
                <div style={{ fontSize: '12px', color: '#6b7280', textTransform: 'uppercase' }}>
                  Avg Followers
                </div>
              </div>
              <div style={{ textAlign: 'center' }}>
                <div style={{ fontSize: '24px', fontWeight: '700', color: '#f59e0b' }}>
                  {stats.tiers.MACRO + stats.tiers.MEGA}
                </div>
                <div style={{ fontSize: '12px', color: '#6b7280', textTransform: 'uppercase' }}>
                  Top Tier KOLs
                </div>
              </div>
            </div>
          </div>
        ))}
      </div>
    </div>
  )
}

function TierAnalysis({ data }: { data: any }) {
  const tierColors = {
    MEGA: '#dc2626',
    MACRO: '#f59e0b',
    MICRO: '#10b981',
    NANO: '#6366f1'
  }

  return (
    <div>
      <h2 style={{ fontSize: '24px', fontWeight: '700', color: '#1f2937', marginBottom: '24px' }}>
        Tier Performance Analysis
      </h2>

      <div style={{ display: 'grid', gap: '20px' }}>
        {Object.entries(data).map(([tier, stats]: [string, any]) => (
          <div key={tier} style={{
            background: 'linear-gradient(135deg, #f8fafc, #e2e8f0)',
            padding: '24px',
            borderRadius: '16px',
            border: '1px solid rgba(229, 231, 235, 0.5)'
          }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '20px' }}>
              <div style={{ display: 'flex', alignItems: 'center' }}>
                <div style={{
                  width: '12px',
                  height: '40px',
                  borderRadius: '6px',
                  background: tierColors[tier as keyof typeof tierColors] || '#6b7280',
                  marginRight: '16px'
                }}></div>
                <div>
                  <h3 style={{ fontSize: '20px', fontWeight: '700', color: '#1f2937', margin: 0 }}>
                    {tier} Tier
                  </h3>
                  <p style={{ fontSize: '14px', color: '#6b7280', margin: 0 }}>
                    {stats.count} KOLs ({stats.percentage}% of portfolio)
                  </p>
                </div>
              </div>
            </div>

            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(180px, 1fr))', gap: '16px' }}>
              <div style={{
                background: 'rgba(255, 255, 255, 0.8)',
                padding: '16px',
                borderRadius: '12px',
                textAlign: 'center'
              }}>
                <div style={{ fontSize: '20px', fontWeight: '700', color: '#3b82f6' }}>
                  {(stats.avgFollowers / 1000).toFixed(0)}K
                </div>
                <div style={{ fontSize: '12px', color: '#6b7280', textTransform: 'uppercase' }}>
                  Avg Followers
                </div>
              </div>
              <div style={{
                background: 'rgba(255, 255, 255, 0.8)',
                padding: '16px',
                borderRadius: '12px',
                textAlign: 'center'
              }}>
                <div style={{ fontSize: '20px', fontWeight: '700', color: '#10b981' }}>
                  {stats.avgEngagement}%
                </div>
                <div style={{ fontSize: '12px', color: '#6b7280', textTransform: 'uppercase' }}>
                  Avg Engagement
                </div>
              </div>
              <div style={{
                background: 'rgba(255, 255, 255, 0.8)',
                padding: '16px',
                borderRadius: '12px',
                textAlign: 'center'
              }}>
                <div style={{ fontSize: '20px', fontWeight: '700', color: '#f59e0b' }}>
                  {Object.keys(stats.platforms).length}
                </div>
                <div style={{ fontSize: '12px', color: '#6b7280', textTransform: 'uppercase' }}>
                  Platforms
                </div>
              </div>
            </div>
          </div>
        ))}
      </div>
    </div>
  )
}

function CategoryPerformance({ data }: { data: any }) {
  return (
    <div>
      <h2 style={{ fontSize: '24px', fontWeight: '700', color: '#1f2937', marginBottom: '24px' }}>
        Category Performance Analysis
      </h2>

      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(300px, 1fr))', gap: '20px' }}>
        {Object.entries(data).map(([category, stats]: [string, any]) => (
          <div key={category} style={{
            background: 'linear-gradient(135deg, #f8fafc, #e2e8f0)',
            padding: '24px',
            borderRadius: '16px',
            border: '1px solid rgba(229, 231, 235, 0.5)'
          }}>
            <h3 style={{ fontSize: '18px', fontWeight: '700', color: '#1f2937', marginBottom: '16px' }}>
              {category}
            </h3>

            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '12px', marginBottom: '16px' }}>
              <div style={{ textAlign: 'center' }}>
                <div style={{ fontSize: '20px', fontWeight: '700', color: '#3b82f6' }}>
                  {stats.count}
                </div>
                <div style={{ fontSize: '11px', color: '#6b7280', textTransform: 'uppercase' }}>
                  Total KOLs
                </div>
              </div>
              <div style={{ textAlign: 'center' }}>
                <div style={{ fontSize: '20px', fontWeight: '700', color: '#10b981' }}>
                  {stats.avgEngagement}%
                </div>
                <div style={{ fontSize: '11px', color: '#6b7280', textTransform: 'uppercase' }}>
                  Avg Engagement
                </div>
              </div>
              <div style={{ textAlign: 'center' }}>
                <div style={{ fontSize: '20px', fontWeight: '700', color: '#f59e0b' }}>
                  {stats.topTiers}
                </div>
                <div style={{ fontSize: '11px', color: '#6b7280', textTransform: 'uppercase' }}>
                  Top Tier KOLs
                </div>
              </div>
              <div style={{ textAlign: 'center' }}>
                <div style={{ fontSize: '20px', fontWeight: '700', color: '#ef4444' }}>
                  {stats.performanceScore}
                </div>
                <div style={{ fontSize: '11px', color: '#6b7280', textTransform: 'uppercase' }}>
                  Performance Score
                </div>
              </div>
            </div>

            <div style={{ fontSize: '12px', color: '#6b7280' }}>
              <strong>Platforms:</strong> {Object.keys(stats.platforms).join(', ')}
            </div>
          </div>
        ))}
      </div>
    </div>
  )
}

function EngagementAnalysis({ data }: { data: any }) {
  return (
    <div>
      <h2 style={{ fontSize: '24px', fontWeight: '700', color: '#1f2937', marginBottom: '24px' }}>
        Engagement Analysis
      </h2>

      {/* Engagement Distribution */}
      <div style={{
        background: 'linear-gradient(135deg, #f8fafc, #e2e8f0)',
        padding: '24px',
        borderRadius: '16px',
        border: '1px solid rgba(229, 231, 235, 0.5)',
        marginBottom: '24px'
      }}>
        <h3 style={{ fontSize: '18px', fontWeight: '600', color: '#1f2937', marginBottom: '16px' }}>
          Engagement Rate Distribution
        </h3>
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(150px, 1fr))', gap: '16px' }}>
          {Object.entries(data.distribution).map(([range, count]: [string, any]) => (
            <div key={range} style={{
              background: 'rgba(255, 255, 255, 0.8)',
              padding: '20px',
              borderRadius: '12px',
              textAlign: 'center'
            }}>
              <div style={{
                fontSize: '24px',
                fontWeight: '700',
                color: range.includes('High') ? '#10b981' :
                       range.includes('Medium') ? '#f59e0b' : '#ef4444'
              }}>
                {count}
              </div>
              <div style={{ fontSize: '12px', color: '#6b7280', textTransform: 'uppercase' }}>
                {range}
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* Top Performers */}
      <div>
        <h3 style={{ fontSize: '18px', fontWeight: '600', color: '#1f2937', marginBottom: '16px' }}>
          Top 10 Performers by Engagement
        </h3>
        <div style={{ display: 'grid', gap: '12px' }}>
          {data.topPerformers.map((kol: any, index: number) => (
            <div key={index} style={{
              background: 'rgba(255, 255, 255, 0.8)',
              padding: '16px',
              borderRadius: '12px',
              border: '1px solid rgba(229, 231, 235, 0.3)',
              display: 'flex',
              justifyContent: 'space-between',
              alignItems: 'center'
            }}>
              <div style={{ display: 'flex', alignItems: 'center' }}>
                <div style={{
                  width: '32px',
                  height: '32px',
                  borderRadius: '8px',
                  background: index < 3 ? '#f59e0b' : '#e5e7eb',
                  color: index < 3 ? 'white' : '#6b7280',
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center',
                  fontSize: '14px',
                  fontWeight: '700',
                  marginRight: '12px'
                }}>
                  {index + 1}
                </div>
                <div>
                  <div style={{ fontSize: '14px', fontWeight: '600', color: '#1f2937' }}>
                    {kol.name}
                  </div>
                  <div style={{ fontSize: '12px', color: '#6b7280' }}>
                    {kol.platform} • {kol.tier} Tier
                  </div>
                </div>
              </div>
              <div style={{ textAlign: 'right' }}>
                <div style={{ fontSize: '16px', fontWeight: '700', color: '#10b981' }}>
                  {kol.engagement}%
                </div>
                <div style={{ fontSize: '12px', color: '#6b7280' }}>
                  {(kol.followers / 1000).toFixed(0)}K followers
                </div>
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  )
}

function Recommendations({ recommendations, campaigns, insights }: { recommendations: any[], campaigns: any[], insights: any }) {
  return (
    <div>
      <h2 style={{ fontSize: '24px', fontWeight: '700', color: '#1f2937', marginBottom: '24px' }}>
        Strategic Recommendations
      </h2>

      {/* Action Items */}
      <div style={{ marginBottom: '32px' }}>
        <h3 style={{ fontSize: '18px', fontWeight: '600', color: '#1f2937', marginBottom: '16px' }}>
          Priority Action Items
        </h3>
        <div style={{ display: 'grid', gap: '16px' }}>
          {recommendations.map((rec: any, index: number) => (
            <div key={index} style={{
              background: 'linear-gradient(135deg, #f8fafc, #e2e8f0)',
              padding: '20px',
              borderRadius: '12px',
              border: '1px solid rgba(229, 231, 235, 0.5)'
            }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: '12px' }}>
                <h4 style={{ fontSize: '16px', fontWeight: '600', color: '#1f2937', margin: 0 }}>
                  {rec.recommendation}
                </h4>
                <span style={{
                  background: rec.impact === 'High' ? '#10b981' : rec.impact === 'Medium' ? '#f59e0b' : '#6b7280',
                  color: 'white',
                  padding: '4px 8px',
                  borderRadius: '6px',
                  fontSize: '12px',
                  fontWeight: '600'
                }}>
                  {rec.impact} Impact
                </span>
              </div>
              <p style={{ fontSize: '14px', color: '#6b7280', marginBottom: '8px' }}>
                {rec.reasoning}
              </p>
              <div style={{ fontSize: '12px', color: '#374151' }}>
                <strong>Timeline:</strong> {rec.timeline} • <strong>Category:</strong> {rec.category}
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* Campaign Suggestions */}
      <div style={{ marginBottom: '32px' }}>
        <h3 style={{ fontSize: '18px', fontWeight: '600', color: '#1f2937', marginBottom: '16px' }}>
          Suggested Campaign Strategies
        </h3>
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(320px, 1fr))', gap: '16px' }}>
          {campaigns.map((campaign: any, index: number) => (
            <div key={index} style={{
              background: 'linear-gradient(135deg, #f8fafc, #e2e8f0)',
              padding: '20px',
              borderRadius: '12px',
              border: '1px solid rgba(229, 231, 235, 0.5)'
            }}>
              <h4 style={{ fontSize: '16px', fontWeight: '600', color: '#1f2937', marginBottom: '12px' }}>
                {campaign.campaignType}
              </h4>
              <div style={{ fontSize: '14px', color: '#6b7280', marginBottom: '16px' }}>
                <div><strong>Target:</strong> {campaign.targetAudience}</div>
                <div><strong>KOLs:</strong> {campaign.recommendedKOLs}</div>
                <div><strong>Reach:</strong> {campaign.estimatedReach}</div>
              </div>
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                <div style={{ fontSize: '16px', fontWeight: '700', color: '#3b82f6' }}>
                  {campaign.budget}
                </div>
                <div style={{ fontSize: '14px', color: '#10b981' }}>
                  ROI: {campaign.expectedROI}
                </div>
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* Competitive Insights */}
      <div>
        <h3 style={{ fontSize: '18px', fontWeight: '600', color: '#1f2937', marginBottom: '16px' }}>
          Market Position & Opportunities
        </h3>
        <div style={{
          background: 'linear-gradient(135deg, #f8fafc, #e2e8f0)',
          padding: '24px',
          borderRadius: '16px',
          border: '1px solid rgba(229, 231, 235, 0.5)'
        }}>
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(250px, 1fr))', gap: '20px' }}>
            <div>
              <h4 style={{ fontSize: '14px', fontWeight: '600', color: '#6b7280', textTransform: 'uppercase', marginBottom: '12px' }}>
                Competitive Advantages
              </h4>
              <ul style={{ fontSize: '14px', color: '#374151', margin: 0, paddingLeft: '16px' }}>
                {insights.competitiveAdvantages.map((advantage: string, index: number) => (
                  <li key={index} style={{ marginBottom: '4px' }}>✅ {advantage}</li>
                ))}
              </ul>
            </div>
            <div>
              <h4 style={{ fontSize: '14px', fontWeight: '600', color: '#6b7280', textTransform: 'uppercase', marginBottom: '12px' }}>
                Gap Analysis
              </h4>
              <ul style={{ fontSize: '14px', color: '#374151', margin: 0, paddingLeft: '16px' }}>
                {insights.gapAnalysis.map((gap: string, index: number) => (
                  <li key={index} style={{ marginBottom: '4px' }}>⚠️ {gap}</li>
                ))}
              </ul>
            </div>
            <div>
              <h4 style={{ fontSize: '14px', fontWeight: '600', color: '#6b7280', textTransform: 'uppercase', marginBottom: '12px' }}>
                Growth Opportunities
              </h4>
              <ul style={{ fontSize: '14px', color: '#374151', margin: 0, paddingLeft: '16px' }}>
                {insights.opportunities.map((opportunity: string, index: number) => (
                  <li key={index} style={{ marginBottom: '4px' }}>🚀 {opportunity}</li>
                ))}
              </ul>
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}