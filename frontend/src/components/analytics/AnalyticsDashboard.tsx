'use client'

import { useState, useEffect } from 'react'

interface AnalyticsData {
  overview: {
    totalReach: number
    totalEngagement: number
    activeCampaigns: number
    totalSpend: number
    avgROI: number
    conversionRate: number
  }
  performance: {
    weekly: Array<{ week: string; reach: number; engagement: number; spend: number }>
    monthly: Array<{ month: string; reach: number; engagement: number; spend: number }>
  }
  platforms: {
    [platform: string]: {
      reach: number
      engagement: number
      spend: number
      roi: number
      growth: number
    }
  }
  demographics: {
    ageGroups: { [age: string]: number }
    genders: { [gender: string]: number }
    locations: { [location: string]: number }
  }
  campaigns: Array<{
    id: string
    name: string
    reach: number
    engagement: number
    spend: number
    roi: number
    status: string
  }>
}

const mockAnalyticsData: AnalyticsData = {
  overview: {
    totalReach: 15750000,
    totalEngagement: 1260000,
    activeCampaigns: 12,
    totalSpend: 2850000,
    avgROI: 340,
    conversionRate: 3.2
  },
  performance: {
    weekly: [
      { week: 'Week 1', reach: 2100000, engagement: 168000, spend: 380000 },
      { week: 'Week 2', reach: 2350000, engagement: 188000, spend: 420000 },
      { week: 'Week 3', reach: 2800000, engagement: 224000, spend: 510000 },
      { week: 'Week 4', reach: 3200000, engagement: 256000, spend: 580000 },
      { week: 'Week 5', reach: 2900000, engagement: 232000, spend: 520000 },
      { week: 'Week 6', reach: 2400000, engagement: 192000, spend: 440000 }
    ],
    monthly: [
      { month: 'Jan', reach: 8500000, engagement: 680000, spend: 1200000 },
      { month: 'Feb', reach: 9200000, engagement: 736000, spend: 1350000 },
      { month: 'Mar', reach: 10100000, engagement: 808000, spend: 1480000 },
      { month: 'Apr', reach: 11800000, engagement: 944000, spend: 1720000 },
      { month: 'May', reach: 13200000, engagement: 1056000, spend: 1950000 },
      { month: 'Jun', reach: 15750000, engagement: 1260000, spend: 2850000 }
    ]
  },
  platforms: {
    TikTok: { reach: 8200000, engagement: 656000, spend: 1150000, roi: 380, growth: 15.2 },
    Instagram: { reach: 4100000, engagement: 328000, spend: 820000, roi: 320, growth: 8.5 },
    YouTube: { reach: 2800000, engagement: 196000, spend: 650000, roi: 280, growth: 12.1 },
    Facebook: { reach: 650000, engagement: 45500, spend: 230000, roi: 200, growth: -2.3 }
  },
  demographics: {
    ageGroups: {
      '18-24': 35,
      '25-34': 42,
      '35-44': 18,
      '45-54': 4,
      '55+': 1
    },
    genders: {
      Female: 68,
      Male: 30,
      Other: 2
    },
    locations: {
      Bangkok: 45,
      'Chiang Mai': 12,
      Phuket: 8,
      Pattaya: 6,
      'Other Thailand': 29
    }
  },
  campaigns: [
    { id: 'C001', name: 'Summer Lifestyle', reach: 2500000, engagement: 200000, spend: 450000, roi: 380, status: 'Active' },
    { id: 'C002', name: 'Tech Product Launch', reach: 1200000, engagement: 84000, spend: 320000, roi: 280, status: 'Active' },
    { id: 'C003', name: 'Food Festival', reach: 1800000, engagement: 144000, spend: 280000, roi: 450, status: 'Completed' },
    { id: 'C004', name: 'Health & Wellness', reach: 3200000, engagement: 256000, spend: 680000, roi: 320, status: 'Active' },
    { id: 'C005', name: 'Travel Documentary', reach: 1500000, engagement: 105000, spend: 420000, roi: 250, status: 'Paused' }
  ]
}

export function AnalyticsDashboard() {
  const [data, setData] = useState<AnalyticsData>(mockAnalyticsData)
  const [selectedTimeframe, setSelectedTimeframe] = useState<'weekly' | 'monthly'>('monthly')
  const [selectedMetric, setSelectedMetric] = useState<'reach' | 'engagement' | 'spend'>('reach')

  const formatNumber = (num: number) => {
    if (num >= 1000000) {
      return (num / 1000000).toFixed(1) + 'M'
    } else if (num >= 1000) {
      return (num / 1000).toFixed(1) + 'K'
    }
    return num.toString()
  }

  const formatCurrency = (num: number) => {
    return (num / 1000).toFixed(0) + 'K THB'
  }

  const getMetricColor = (metric: string) => {
    switch (metric) {
      case 'reach': return '#3b82f6'
      case 'engagement': return '#10b981'
      case 'spend': return '#f59e0b'
      default: return '#6b7280'
    }
  }

  const getChangeColor = (change: number) => {
    return change >= 0 ? '#10b981' : '#ef4444'
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
              📈 Campaign Analytics
            </h1>
            <p style={{ fontSize: '16px', color: '#6b7280', margin: 0 }}>
              Track performance across all KOL campaigns and platforms
            </p>
          </div>
          <div style={{ display: 'flex', gap: '12px', alignItems: 'center' }}>
            <select
              value={selectedTimeframe}
              onChange={(e) => setSelectedTimeframe(e.target.value as 'weekly' | 'monthly')}
              style={{
                padding: '8px 16px',
                border: '1px solid rgba(229, 231, 235, 0.5)',
                borderRadius: '8px',
                background: 'rgba(255, 255, 255, 0.8)',
                fontSize: '14px',
                cursor: 'pointer'
              }}
            >
              <option value="weekly">Weekly View</option>
              <option value="monthly">Monthly View</option>
            </select>
            <button style={{
              background: 'linear-gradient(135deg, #3b82f6, #8b5cf6)',
              color: 'white',
              border: 'none',
              borderRadius: '8px',
              padding: '8px 16px',
              fontSize: '14px',
              fontWeight: '600',
              cursor: 'pointer'
            }}>
              📊 Export Report
            </button>
          </div>
        </div>

        {/* KPI Overview */}
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))', gap: '16px' }}>
          {[
            { label: 'Total Reach', value: formatNumber(data.overview.totalReach), change: '+12.5%', color: '#3b82f6' },
            { label: 'Total Engagement', value: formatNumber(data.overview.totalEngagement), change: '+8.2%', color: '#10b981' },
            { label: 'Total Spend', value: formatCurrency(data.overview.totalSpend), change: '+15.1%', color: '#f59e0b' },
            { label: 'Avg ROI', value: `${data.overview.avgROI}%`, change: '+3.7%', color: '#8b5cf6' },
            { label: 'Active Campaigns', value: data.overview.activeCampaigns.toString(), change: '+2', color: '#ef4444' },
            { label: 'Conversion Rate', value: `${data.overview.conversionRate}%`, change: '+0.3%', color: '#06b6d4' }
          ].map((kpi, index) => (
            <div key={index} style={{
              background: 'linear-gradient(135deg, #f8fafc, #e2e8f0)',
              padding: '20px',
              borderRadius: '16px',
              border: '1px solid rgba(229, 231, 235, 0.5)',
              textAlign: 'center'
            }}>
              <div style={{ fontSize: '24px', fontWeight: '700', color: kpi.color, marginBottom: '4px' }}>
                {kpi.value}
              </div>
              <div style={{ fontSize: '12px', color: '#6b7280', textTransform: 'uppercase', fontWeight: '600', marginBottom: '4px' }}>
                {kpi.label}
              </div>
              <div style={{ fontSize: '12px', color: getChangeColor(parseFloat(kpi.change)), fontWeight: '600' }}>
                {kpi.change}
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* Performance Chart */}
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
          <h2 style={{ fontSize: '20px', fontWeight: '700', color: '#1f2937', margin: 0 }}>
            Performance Trends
          </h2>
          <div style={{ display: 'flex', gap: '8px' }}>
            {['reach', 'engagement', 'spend'].map(metric => (
              <button
                key={metric}
                onClick={() => setSelectedMetric(metric as 'reach' | 'engagement' | 'spend')}
                style={{
                  padding: '6px 12px',
                  border: '1px solid rgba(229, 231, 235, 0.5)',
                  borderRadius: '6px',
                  background: selectedMetric === metric
                    ? getMetricColor(metric)
                    : 'rgba(255, 255, 255, 0.8)',
                  color: selectedMetric === metric ? 'white' : '#6b7280',
                  fontSize: '12px',
                  fontWeight: '500',
                  cursor: 'pointer',
                  textTransform: 'capitalize'
                }}
              >
                {metric}
              </button>
            ))}
          </div>
        </div>

        {/* Simple Chart Representation */}
        <div style={{ height: '200px', display: 'flex', alignItems: 'end', gap: '8px', padding: '20px 0' }}>
          {data.performance[selectedTimeframe].map((period, index) => {
            const value = period[selectedMetric]
            const maxValue = Math.max(...data.performance[selectedTimeframe].map(p => p[selectedMetric]))
            const height = (value / maxValue) * 150

            return (
              <div key={index} style={{ flex: 1, display: 'flex', flexDirection: 'column', alignItems: 'center' }}>
                <div style={{
                  width: '100%',
                  height: `${height}px`,
                  background: `linear-gradient(180deg, ${getMetricColor(selectedMetric)}, ${getMetricColor(selectedMetric)}aa)`,
                  borderRadius: '4px 4px 0 0',
                  marginBottom: '8px',
                  transition: 'all 0.3s ease'
                }}></div>
                <div style={{ fontSize: '12px', color: '#6b7280', textAlign: 'center' }}>
                  {'week' in period ? period.week : period.month}
                </div>
                <div style={{ fontSize: '11px', color: getMetricColor(selectedMetric), fontWeight: '600' }}>
                  {selectedMetric === 'spend' ? formatCurrency(value) : formatNumber(value)}
                </div>
              </div>
            )
          })}
        </div>
      </div>

      {/* Platform Performance & Demographics */}
      <div style={{ display: 'grid', gridTemplateColumns: '2fr 1fr', gap: '24px', marginBottom: '24px' }}>
        {/* Platform Performance */}
        <div style={{
          background: 'rgba(255, 255, 255, 0.95)',
          backdropFilter: 'blur(20px)',
          borderRadius: '20px',
          padding: '32px',
          boxShadow: '0 20px 40px rgba(0, 0, 0, 0.1)',
          border: '1px solid rgba(229, 231, 235, 0.5)'
        }}>
          <h2 style={{ fontSize: '20px', fontWeight: '700', color: '#1f2937', marginBottom: '24px' }}>
            Platform Performance
          </h2>
          <div style={{ display: 'grid', gap: '16px' }}>
            {Object.entries(data.platforms).map(([platform, stats]) => (
              <div key={platform} style={{
                background: 'linear-gradient(135deg, #f8fafc, #e2e8f0)',
                padding: '20px',
                borderRadius: '12px',
                border: '1px solid rgba(229, 231, 235, 0.5)'
              }}>
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '12px' }}>
                  <h3 style={{ fontSize: '16px', fontWeight: '600', color: '#1f2937', margin: 0 }}>
                    {platform}
                  </h3>
                  <span style={{
                    fontSize: '12px',
                    fontWeight: '600',
                    color: getChangeColor(stats.growth)
                  }}>
                    {stats.growth > 0 ? '+' : ''}{stats.growth}%
                  </span>
                </div>
                <div style={{ display: 'grid', gridTemplateColumns: 'repeat(4, 1fr)', gap: '12px' }}>
                  <div style={{ textAlign: 'center' }}>
                    <div style={{ fontSize: '14px', fontWeight: '700', color: '#3b82f6' }}>
                      {formatNumber(stats.reach)}
                    </div>
                    <div style={{ fontSize: '10px', color: '#6b7280', textTransform: 'uppercase' }}>
                      Reach
                    </div>
                  </div>
                  <div style={{ textAlign: 'center' }}>
                    <div style={{ fontSize: '14px', fontWeight: '700', color: '#10b981' }}>
                      {formatNumber(stats.engagement)}
                    </div>
                    <div style={{ fontSize: '10px', color: '#6b7280', textTransform: 'uppercase' }}>
                      Engagement
                    </div>
                  </div>
                  <div style={{ textAlign: 'center' }}>
                    <div style={{ fontSize: '14px', fontWeight: '700', color: '#f59e0b' }}>
                      {formatCurrency(stats.spend)}
                    </div>
                    <div style={{ fontSize: '10px', color: '#6b7280', textTransform: 'uppercase' }}>
                      Spend
                    </div>
                  </div>
                  <div style={{ textAlign: 'center' }}>
                    <div style={{ fontSize: '14px', fontWeight: '700', color: '#8b5cf6' }}>
                      {stats.roi}%
                    </div>
                    <div style={{ fontSize: '10px', color: '#6b7280', textTransform: 'uppercase' }}>
                      ROI
                    </div>
                  </div>
                </div>
              </div>
            ))}
          </div>
        </div>

        {/* Demographics */}
        <div style={{
          background: 'rgba(255, 255, 255, 0.95)',
          backdropFilter: 'blur(20px)',
          borderRadius: '20px',
          padding: '32px',
          boxShadow: '0 20px 40px rgba(0, 0, 0, 0.1)',
          border: '1px solid rgba(229, 231, 235, 0.5)'
        }}>
          <h2 style={{ fontSize: '20px', fontWeight: '700', color: '#1f2937', marginBottom: '24px' }}>
            Audience Demographics
          </h2>

          {/* Age Groups */}
          <div style={{ marginBottom: '24px' }}>
            <h3 style={{ fontSize: '14px', fontWeight: '600', color: '#6b7280', marginBottom: '12px', textTransform: 'uppercase' }}>
              Age Groups
            </h3>
            {Object.entries(data.demographics.ageGroups).map(([age, percentage]) => (
              <div key={age} style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '8px' }}>
                <span style={{ fontSize: '14px', color: '#374151' }}>{age}</span>
                <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                  <div style={{
                    width: '60px',
                    height: '6px',
                    background: 'rgba(229, 231, 235, 0.5)',
                    borderRadius: '3px',
                    overflow: 'hidden'
                  }}>
                    <div style={{
                      width: `${percentage}%`,
                      height: '100%',
                      background: '#3b82f6',
                      borderRadius: '3px'
                    }}></div>
                  </div>
                  <span style={{ fontSize: '12px', color: '#6b7280', minWidth: '30px' }}>{percentage}%</span>
                </div>
              </div>
            ))}
          </div>

          {/* Genders */}
          <div style={{ marginBottom: '24px' }}>
            <h3 style={{ fontSize: '14px', fontWeight: '600', color: '#6b7280', marginBottom: '12px', textTransform: 'uppercase' }}>
              Gender Split
            </h3>
            {Object.entries(data.demographics.genders).map(([gender, percentage]) => (
              <div key={gender} style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '8px' }}>
                <span style={{ fontSize: '14px', color: '#374151' }}>{gender}</span>
                <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                  <div style={{
                    width: '60px',
                    height: '6px',
                    background: 'rgba(229, 231, 235, 0.5)',
                    borderRadius: '3px',
                    overflow: 'hidden'
                  }}>
                    <div style={{
                      width: `${percentage}%`,
                      height: '100%',
                      background: '#10b981',
                      borderRadius: '3px'
                    }}></div>
                  </div>
                  <span style={{ fontSize: '12px', color: '#6b7280', minWidth: '30px' }}>{percentage}%</span>
                </div>
              </div>
            ))}
          </div>

          {/* Locations */}
          <div>
            <h3 style={{ fontSize: '14px', fontWeight: '600', color: '#6b7280', marginBottom: '12px', textTransform: 'uppercase' }}>
              Top Locations
            </h3>
            {Object.entries(data.demographics.locations).map(([location, percentage]) => (
              <div key={location} style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '8px' }}>
                <span style={{ fontSize: '14px', color: '#374151' }}>{location}</span>
                <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                  <div style={{
                    width: '60px',
                    height: '6px',
                    background: 'rgba(229, 231, 235, 0.5)',
                    borderRadius: '3px',
                    overflow: 'hidden'
                  }}>
                    <div style={{
                      width: `${(percentage / 45) * 100}%`,
                      height: '100%',
                      background: '#f59e0b',
                      borderRadius: '3px'
                    }}></div>
                  </div>
                  <span style={{ fontSize: '12px', color: '#6b7280', minWidth: '30px' }}>{percentage}%</span>
                </div>
              </div>
            ))}
          </div>
        </div>
      </div>

      {/* Campaign Performance */}
      <div style={{
        background: 'rgba(255, 255, 255, 0.95)',
        backdropFilter: 'blur(20px)',
        borderRadius: '20px',
        padding: '32px',
        boxShadow: '0 20px 40px rgba(0, 0, 0, 0.1)',
        border: '1px solid rgba(229, 231, 235, 0.5)'
      }}>
        <h2 style={{ fontSize: '20px', fontWeight: '700', color: '#1f2937', marginBottom: '24px' }}>
          Campaign Performance
        </h2>
        <div style={{ display: 'grid', gap: '16px' }}>
          {data.campaigns.map(campaign => (
            <div key={campaign.id} style={{
              background: 'linear-gradient(135deg, #f8fafc, #e2e8f0)',
              padding: '20px',
              borderRadius: '12px',
              border: '1px solid rgba(229, 231, 235, 0.5)',
              display: 'flex',
              justifyContent: 'space-between',
              alignItems: 'center'
            }}>
              <div>
                <h3 style={{ fontSize: '16px', fontWeight: '600', color: '#1f2937', margin: '0 0 4px 0' }}>
                  {campaign.name}
                </h3>
                <p style={{ fontSize: '12px', color: '#6b7280', margin: 0 }}>
                  ID: {campaign.id} • Status: {campaign.status}
                </p>
              </div>
              <div style={{ display: 'grid', gridTemplateColumns: 'repeat(4, 1fr)', gap: '24px', textAlign: 'center' }}>
                <div>
                  <div style={{ fontSize: '16px', fontWeight: '700', color: '#3b82f6' }}>
                    {formatNumber(campaign.reach)}
                  </div>
                  <div style={{ fontSize: '10px', color: '#6b7280', textTransform: 'uppercase' }}>
                    Reach
                  </div>
                </div>
                <div>
                  <div style={{ fontSize: '16px', fontWeight: '700', color: '#10b981' }}>
                    {formatNumber(campaign.engagement)}
                  </div>
                  <div style={{ fontSize: '10px', color: '#6b7280', textTransform: 'uppercase' }}>
                    Engagement
                  </div>
                </div>
                <div>
                  <div style={{ fontSize: '16px', fontWeight: '700', color: '#f59e0b' }}>
                    {formatCurrency(campaign.spend)}
                  </div>
                  <div style={{ fontSize: '10px', color: '#6b7280', textTransform: 'uppercase' }}>
                    Spend
                  </div>
                </div>
                <div>
                  <div style={{ fontSize: '16px', fontWeight: '700', color: '#8b5cf6' }}>
                    {campaign.roi}%
                  </div>
                  <div style={{ fontSize: '10px', color: '#6b7280', textTransform: 'uppercase' }}>
                    ROI
                  </div>
                </div>
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  )
}