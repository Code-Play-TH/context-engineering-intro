'use client'

import { useState, useEffect } from 'react'

interface Project {
  id: string
  name: string
  description: string
  status: 'Planning' | 'Active' | 'Completed' | 'Paused'
  budget: number
  startDate: string
  endDate: string
  assignedKOLs: number
  category: string
  manager: string
  progress: number
  estimatedReach: string
  actualReach?: string
  roi?: number
}

const mockProjects: Project[] = [
  {
    id: 'PRJ001',
    name: 'Summer Lifestyle Campaign',
    description: 'Promote summer fashion and lifestyle products through lifestyle influencers',
    status: 'Active',
    budget: 250000,
    startDate: '2025-06-01',
    endDate: '2025-08-31',
    assignedKOLs: 12,
    category: 'Lifestyle',
    manager: 'Sarah Johnson',
    progress: 65,
    estimatedReach: '2.5M',
    actualReach: '1.8M',
    roi: 320
  },
  {
    id: 'PRJ002',
    name: 'Tech Product Launch',
    description: 'Launch new smartphone through tech reviewers and IT influencers',
    status: 'Planning',
    budget: 500000,
    startDate: '2025-10-01',
    endDate: '2025-12-15',
    assignedKOLs: 8,
    category: 'IT',
    manager: 'Mike Chen',
    progress: 25,
    estimatedReach: '1.2M'
  },
  {
    id: 'PRJ003',
    name: 'Food Festival Promotion',
    description: 'Promote annual food festival through food bloggers and cooking channels',
    status: 'Completed',
    budget: 180000,
    startDate: '2025-03-01',
    endDate: '2025-05-31',
    assignedKOLs: 15,
    category: 'Food_cooking',
    manager: 'Emma Thai',
    progress: 100,
    estimatedReach: '1.8M',
    actualReach: '2.1M',
    roi: 450
  },
  {
    id: 'PRJ004',
    name: 'Health & Wellness Series',
    description: 'Year-long health awareness campaign with fitness influencers',
    status: 'Active',
    budget: 350000,
    startDate: '2025-01-01',
    endDate: '2025-12-31',
    assignedKOLs: 20,
    category: 'Healthy',
    manager: 'David Kim',
    progress: 45,
    estimatedReach: '3.2M',
    actualReach: '1.5M',
    roi: 280
  },
  {
    id: 'PRJ005',
    name: 'Travel Documentary',
    description: 'Document hidden gems in Thailand through travel vloggers',
    status: 'Paused',
    budget: 400000,
    startDate: '2025-04-01',
    endDate: '2025-09-30',
    assignedKOLs: 6,
    category: 'Travel',
    manager: 'Lisa Wong',
    progress: 30,
    estimatedReach: '1.5M'
  }
]

export function ProjectsManager() {
  const [projects, setProjects] = useState<Project[]>([])
  const [loading, setLoading] = useState(true)
  const [selectedStatus, setSelectedStatus] = useState<string>('All')
  const [searchTerm, setSearchTerm] = useState('')
  const [showCreateModal, setShowCreateModal] = useState(false)

  useEffect(() => {
    const fetchProjects = async () => {
      try {
        const response = await fetch('/api/projects.json')
        const data = await response.json()
        setProjects(data.projects || [])
      } catch (error) {
        console.error('Error fetching projects:', error)
        setProjects(mockProjects) // Fallback to mock data
      } finally {
        setLoading(false)
      }
    }

    fetchProjects()
  }, [])

  const statuses = ['All', 'Planning', 'Active', 'Completed', 'Paused']

  const filteredProjects = projects.filter(project => {
    const matchesStatus = selectedStatus === 'All' || project.status === selectedStatus
    const matchesSearch = project.name.toLowerCase().includes(searchTerm.toLowerCase()) ||
                         project.description.toLowerCase().includes(searchTerm.toLowerCase()) ||
                         project.category.toLowerCase().includes(searchTerm.toLowerCase())
    return matchesStatus && matchesSearch
  })

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'Planning': return '#f59e0b'
      case 'Active': return '#10b981'
      case 'Completed': return '#3b82f6'
      case 'Paused': return '#ef4444'
      default: return '#6b7280'
    }
  }

  const getProgressColor = (progress: number) => {
    if (progress >= 80) return '#10b981'
    if (progress >= 50) return '#f59e0b'
    return '#ef4444'
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
        📁 Loading Projects...
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
              📁 Project Management
            </h1>
            <p style={{ fontSize: '16px', color: '#6b7280', margin: 0 }}>
              Manage KOL campaigns and marketing projects
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
            ➕ New Project
          </button>
        </div>

        {/* Filters */}
        <div style={{ display: 'flex', gap: '16px', alignItems: 'center', flexWrap: 'wrap' }}>
          <div style={{ flex: 1, minWidth: '300px' }}>
            <input
              type="text"
              placeholder="Search projects..."
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
            {statuses.map(status => (
              <button
                key={status}
                onClick={() => setSelectedStatus(status)}
                style={{
                  padding: '8px 16px',
                  border: '1px solid rgba(229, 231, 235, 0.5)',
                  borderRadius: '8px',
                  background: selectedStatus === status
                    ? 'linear-gradient(135deg, #3b82f6, #1d4ed8)'
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

      {/* Project Stats */}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))', gap: '16px', marginBottom: '24px' }}>
        {[
          { label: 'Total Projects', value: projects.length, color: '#3b82f6' },
          { label: 'Active Projects', value: projects.filter(p => p.status === 'Active').length, color: '#10b981' },
          { label: 'Total Budget', value: `${(projects.reduce((sum, p) => sum + p.budget, 0) / 1000000).toFixed(1)}M THB`, color: '#f59e0b' },
          { label: 'Avg ROI', value: `${Math.round(projects.filter(p => p.roi).reduce((sum, p) => sum + (p.roi || 0), 0) / projects.filter(p => p.roi).length)}%`, color: '#8b5cf6' }
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

      {/* Projects Grid */}
      <div style={{ display: 'grid', gap: '20px' }}>
        {filteredProjects.map(project => (
          <div key={project.id} style={{
            background: 'rgba(255, 255, 255, 0.95)',
            backdropFilter: 'blur(20px)',
            borderRadius: '20px',
            padding: '24px',
            boxShadow: '0 20px 40px rgba(0, 0, 0, 0.1)',
            border: '1px solid rgba(229, 231, 235, 0.5)',
            transition: 'transform 0.2s, box-shadow 0.2s',
            cursor: 'pointer'
          }}
          onMouseOver={(e) => {
            e.currentTarget.style.transform = 'translateY(-4px)'
            e.currentTarget.style.boxShadow = '0 24px 48px rgba(0, 0, 0, 0.15)'
          }}
          onMouseOut={(e) => {
            e.currentTarget.style.transform = 'translateY(0)'
            e.currentTarget.style.boxShadow = '0 20px 40px rgba(0, 0, 0, 0.1)'
          }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: '16px' }}>
              <div style={{ flex: 1 }}>
                <div style={{ display: 'flex', alignItems: 'center', gap: '12px', marginBottom: '8px' }}>
                  <h3 style={{ fontSize: '20px', fontWeight: '700', color: '#1f2937', margin: 0 }}>
                    {project.name}
                  </h3>
                  <span style={{
                    background: getStatusColor(project.status),
                    color: 'white',
                    padding: '4px 12px',
                    borderRadius: '8px',
                    fontSize: '12px',
                    fontWeight: '600'
                  }}>
                    {project.status}
                  </span>
                </div>
                <p style={{ fontSize: '14px', color: '#6b7280', margin: '0 0 12px 0' }}>
                  {project.description}
                </p>
                <div style={{ fontSize: '12px', color: '#374151' }}>
                  <strong>ID:</strong> {project.id} • <strong>Manager:</strong> {project.manager} • <strong>Category:</strong> {project.category}
                </div>
              </div>
            </div>

            {/* Progress Bar */}
            <div style={{ marginBottom: '16px' }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '4px' }}>
                <span style={{ fontSize: '12px', color: '#6b7280', fontWeight: '600' }}>Progress</span>
                <span style={{ fontSize: '12px', color: getProgressColor(project.progress), fontWeight: '700' }}>
                  {project.progress}%
                </span>
              </div>
              <div style={{
                width: '100%',
                height: '8px',
                background: 'rgba(229, 231, 235, 0.5)',
                borderRadius: '4px',
                overflow: 'hidden'
              }}>
                <div style={{
                  width: `${project.progress}%`,
                  height: '100%',
                  background: `linear-gradient(90deg, ${getProgressColor(project.progress)}, ${getProgressColor(project.progress)}dd)`,
                  transition: 'width 0.3s ease'
                }}></div>
              </div>
            </div>

            {/* Project Details */}
            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(120px, 1fr))', gap: '16px' }}>
              <div style={{ textAlign: 'center' }}>
                <div style={{ fontSize: '16px', fontWeight: '700', color: '#3b82f6' }}>
                  {(project.budget / 1000).toFixed(0)}K
                </div>
                <div style={{ fontSize: '11px', color: '#6b7280', textTransform: 'uppercase' }}>
                  Budget (THB)
                </div>
              </div>
              <div style={{ textAlign: 'center' }}>
                <div style={{ fontSize: '16px', fontWeight: '700', color: '#10b981' }}>
                  {project.assignedKOLs}
                </div>
                <div style={{ fontSize: '11px', color: '#6b7280', textTransform: 'uppercase' }}>
                  KOLs
                </div>
              </div>
              <div style={{ textAlign: 'center' }}>
                <div style={{ fontSize: '16px', fontWeight: '700', color: '#f59e0b' }}>
                  {project.actualReach || project.estimatedReach}
                </div>
                <div style={{ fontSize: '11px', color: '#6b7280', textTransform: 'uppercase' }}>
                  {project.actualReach ? 'Actual Reach' : 'Est. Reach'}
                </div>
              </div>
              {project.roi && (
                <div style={{ textAlign: 'center' }}>
                  <div style={{ fontSize: '16px', fontWeight: '700', color: '#8b5cf6' }}>
                    {project.roi}%
                  </div>
                  <div style={{ fontSize: '11px', color: '#6b7280', textTransform: 'uppercase' }}>
                    ROI
                  </div>
                </div>
              )}
              <div style={{ textAlign: 'center' }}>
                <div style={{ fontSize: '16px', fontWeight: '700', color: '#6b7280' }}>
                  {new Date(project.endDate).toLocaleDateString()}
                </div>
                <div style={{ fontSize: '11px', color: '#6b7280', textTransform: 'uppercase' }}>
                  End Date
                </div>
              </div>
            </div>
          </div>
        ))}
      </div>

      {filteredProjects.length === 0 && (
        <div style={{
          background: 'rgba(255, 255, 255, 0.95)',
          backdropFilter: 'blur(20px)',
          borderRadius: '20px',
          padding: '48px',
          textAlign: 'center',
          boxShadow: '0 20px 40px rgba(0, 0, 0, 0.1)',
          border: '1px solid rgba(229, 231, 235, 0.5)'
        }}>
          <div style={{ fontSize: '48px', marginBottom: '16px' }}>📁</div>
          <h3 style={{ fontSize: '18px', fontWeight: '600', color: '#1f2937', marginBottom: '8px' }}>
            No projects found
          </h3>
          <p style={{ fontSize: '14px', color: '#6b7280', margin: 0 }}>
            Try adjusting your filters or create a new project
          </p>
        </div>
      )}

      {/* Create Project Modal Placeholder */}
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
              Create New Project
            </h3>
            <p style={{ fontSize: '14px', color: '#6b7280', marginBottom: '24px' }}>
              Project creation form would be implemented here with fields for name, description, budget, timeline, and KOL assignment.
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
                Create Project
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}