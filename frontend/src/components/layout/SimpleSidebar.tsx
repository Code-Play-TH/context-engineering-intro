'use client'

import { useState, useEffect } from 'react'
import { usePathname } from 'next/navigation'
import Link from 'next/link'

interface SimpleSidebarProps {
  isOpen: boolean
  onToggle: () => void
  onAIToggle: () => void
}

export function SimpleSidebar({ isOpen, onToggle, onAIToggle }: SimpleSidebarProps) {
  const pathname = usePathname()
  const [isDarkMode, setIsDarkMode] = useState(false)
  const [isMobile, setIsMobile] = useState(false)

  useEffect(() => {
    const checkMobile = () => {
      setIsMobile(window.innerWidth < 1024)
    }

    // Check initial screen size
    checkMobile()

    // Add event listener for window resize
    window.addEventListener('resize', checkMobile)

    // Cleanup
    return () => window.removeEventListener('resize', checkMobile)
  }, [])

  const navigation = [
    { name: 'Dashboard', href: '/dashboard', icon: '📊' },
    { name: 'KOLs', href: '/kols', icon: '👥' },
    { name: 'Reports', href: '/reports', icon: '📋' },
    { name: 'Projects', href: '/projects', icon: '📁' },
    { name: 'Users', href: '/admin/users', icon: '👤' },
    { name: 'Analytics', href: '/analytics', icon: '📈' },
    { name: 'Settings', href: '/settings', icon: '⚙️' },
  ]

  const isActive = (href: string) => pathname === href

  return (
    <>
      {/* Mobile backdrop */}
      {isOpen && (
        <div
          style={{
            position: 'fixed',
            inset: 0,
            background: 'rgba(0, 0, 0, 0.3)',
            zIndex: 30,
            display: isMobile ? 'block' : 'none'
          }}
          onClick={onToggle}
        />
      )}

      {/* Sidebar */}
      <div
        style={{
          position: 'fixed',
          left: 0,
          top: 0,
          height: '100vh',
          width: isOpen ? '280px' : '0',
          background: 'linear-gradient(180deg, rgba(255, 255, 255, 0.95) 0%, rgba(249, 250, 251, 0.9) 100%)',
          backdropFilter: 'blur(20px)',
          borderRight: '1px solid rgba(229, 231, 235, 0.5)',
          boxShadow: '2px 0 10px rgba(0, 0, 0, 0.1)',
          zIndex: 40,
          transition: 'width 0.3s ease-in-out',
          overflow: 'hidden',
          display: 'flex',
          flexDirection: 'column'
        }}
      >
        {/* Header */}
        <div style={{
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'space-between',
          padding: '24px',
          borderBottom: '1px solid rgba(229, 231, 235, 0.3)'
        }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
            <div style={{
              width: '40px',
              height: '40px',
              background: 'linear-gradient(135deg, #3b82f6, #8b5cf6)',
              borderRadius: '12px',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              boxShadow: '0 4px 12px rgba(59, 130, 246, 0.3)'
            }}>
              <span style={{ color: 'white', fontSize: '16px', fontWeight: 'bold' }}>KOL</span>
            </div>
            <div>
              <span style={{
                fontSize: '18px',
                fontWeight: 'bold',
                background: 'linear-gradient(135deg, #1f2937, #6b7280)',
                WebkitBackgroundClip: 'text',
                WebkitTextFillColor: 'transparent'
              }}>
                KOL System
              </span>
              <p style={{
                fontSize: '12px',
                color: '#6b7280',
                margin: '2px 0 0 0'
              }}>
                Management Platform
              </p>
            </div>
          </div>
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
            {/* Theme Toggle */}
            <button
              onClick={() => setIsDarkMode(!isDarkMode)}
              style={{
                width: '32px',
                height: '32px',
                border: 'none',
                borderRadius: '8px',
                background: 'transparent',
                cursor: 'pointer',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                transition: 'background 0.2s'
              }}
              onMouseOver={(e) => {
                e.currentTarget.style.background = '#f3f4f6'
              }}
              onMouseOut={(e) => {
                e.currentTarget.style.background = 'transparent'
              }}
            >
              <span style={{ fontSize: '16px' }}>{isDarkMode ? '🌞' : '🌙'}</span>
            </button>
            {/* Close button (mobile) */}
            <button
              onClick={onToggle}
              style={{
                width: '32px',
                height: '32px',
                border: 'none',
                borderRadius: '8px',
                background: 'transparent',
                cursor: 'pointer',
                display: isMobile ? 'flex' : 'none',
                alignItems: 'center',
                justifyContent: 'center',
                transition: 'background 0.2s'
              }}
              onMouseOver={(e) => {
                e.currentTarget.style.background = '#f3f4f6'
              }}
              onMouseOut={(e) => {
                e.currentTarget.style.background = 'transparent'
              }}
            >
              <span style={{ fontSize: '16px' }}>✕</span>
            </button>
          </div>
        </div>

        {/* Navigation */}
        <nav style={{
          flex: 1,
          padding: '16px',
          display: 'flex',
          flexDirection: 'column',
          gap: '8px'
        }}>
          {navigation.map((item) => {
            const active = isActive(item.href)
            return (
              <Link key={item.name} href={item.href} style={{ textDecoration: 'none' }}>
                <div
                  style={{
                    width: '100%',
                    display: 'flex',
                    alignItems: 'center',
                    gap: '12px',
                    padding: '12px 16px',
                    borderRadius: '12px',
                    background: active
                      ? 'linear-gradient(135deg, rgba(59, 130, 246, 0.1), rgba(139, 92, 246, 0.05))'
                      : 'transparent',
                    color: active ? '#3b82f6' : '#6b7280',
                    fontWeight: active ? '600' : '500',
                    fontSize: '14px',
                    cursor: 'pointer',
                    transition: 'all 0.2s',
                    borderLeft: active ? '3px solid #3b82f6' : '3px solid transparent',
                    boxShadow: active ? '0 2px 8px rgba(59, 130, 246, 0.15)' : 'none',
                    transform: 'translateX(0)'
                  }}
                  onMouseOver={(e) => {
                    if (!active) {
                      e.currentTarget.style.background = 'rgba(243, 244, 246, 0.5)'
                      e.currentTarget.style.color = '#374151'
                      e.currentTarget.style.transform = 'translateX(4px)'
                    }
                  }}
                  onMouseOut={(e) => {
                    if (!active) {
                      e.currentTarget.style.background = 'transparent'
                      e.currentTarget.style.color = '#6b7280'
                      e.currentTarget.style.transform = 'translateX(0)'
                    }
                  }}
                >
                  <span style={{
                    fontSize: '20px',
                    transition: 'transform 0.2s'
                  }}>
                    {item.icon}
                  </span>
                  {item.name}
                </div>
              </Link>
            )
          })}
        </nav>

        <div style={{
          height: '1px',
          background: 'rgba(229, 231, 235, 0.5)',
          margin: '0 16px'
        }}></div>

        {/* AI Assistant Button */}
        <div style={{ padding: '16px' }}>
          <button
            onClick={onAIToggle}
            style={{
              width: '100%',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              gap: '12px',
              padding: '16px',
              borderRadius: '12px',
              background: 'linear-gradient(135deg, #3b82f6, #8b5cf6)',
              color: 'white',
              border: 'none',
              fontSize: '14px',
              fontWeight: '600',
              cursor: 'pointer',
              transition: 'all 0.2s',
              boxShadow: '0 4px 12px rgba(59, 130, 246, 0.3)'
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
            <span style={{ fontSize: '20px' }}>✨</span>
            AI Assistant
          </button>
        </div>

        <div style={{
          height: '1px',
          background: 'rgba(229, 231, 235, 0.5)',
          margin: '0 16px'
        }}></div>

        {/* User info */}
        <div style={{
          padding: '16px',
          borderTop: '1px solid rgba(229, 231, 235, 0.3)'
        }}>
          <div style={{
            display: 'flex',
            alignItems: 'center',
            gap: '12px',
            padding: '12px',
            borderRadius: '12px',
            transition: 'background 0.2s',
            cursor: 'pointer'
          }}
          onMouseOver={(e) => {
            e.currentTarget.style.background = 'rgba(243, 244, 246, 0.5)'
            e.currentTarget.style.transform = 'scale(1.02)'
          }}
          onMouseOut={(e) => {
            e.currentTarget.style.background = 'transparent'
            e.currentTarget.style.transform = 'scale(1)'
          }}>
            <div style={{
              width: '40px',
              height: '40px',
              borderRadius: '10px',
              background: 'linear-gradient(135deg, #3b82f6, #8b5cf6)',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              border: '2px solid rgba(59, 130, 246, 0.2)'
            }}>
              <span style={{
                color: 'white',
                fontSize: '16px',
                fontWeight: 'bold'
              }}>
                JD
              </span>
            </div>
            <div style={{ flex: 1, minWidth: 0 }}>
              <p style={{
                fontSize: '14px',
                fontWeight: '500',
                color: '#1f2937',
                margin: '0 0 4px 0'
              }}>
                John Doe
              </p>
              <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                <span style={{
                  padding: '2px 8px',
                  background: 'rgba(59, 130, 246, 0.1)',
                  color: '#3b82f6',
                  fontSize: '11px',
                  fontWeight: '500',
                  borderRadius: '4px',
                  border: '1px solid rgba(59, 130, 246, 0.2)'
                }}>
                  Admin
                </span>
                <div style={{
                  width: '8px',
                  height: '8px',
                  background: '#10b981',
                  borderRadius: '50%'
                }}></div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </>
  )
}