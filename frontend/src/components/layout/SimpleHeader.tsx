'use client'

import { useState, useEffect } from 'react'

interface SimpleHeaderProps {
  onMenuToggle: () => void
  title?: string
}

export function SimpleHeader({ onMenuToggle, title = 'Dashboard' }: SimpleHeaderProps) {
  const [showNotifications, setShowNotifications] = useState(false)
  const [showProfile, setShowProfile] = useState(false)
  const [isDesktop, setIsDesktop] = useState(false)

  useEffect(() => {
    const checkScreenSize = () => {
      setIsDesktop(window.innerWidth > 768)
    }

    // Check initial screen size
    checkScreenSize()

    // Add event listener for window resize
    window.addEventListener('resize', checkScreenSize)

    // Cleanup
    return () => window.removeEventListener('resize', checkScreenSize)
  }, [])

  const notifications = [
    {
      id: 1,
      title: 'New KOL Application',
      message: 'Sarah Johnson submitted a new application',
      time: '2m ago',
      type: 'info',
      icon: '👤'
    },
    {
      id: 2,
      title: 'Campaign Completed',
      message: 'Summer Beauty campaign reached 150% ROI',
      time: '1h ago',
      type: 'success',
      icon: '✅'
    },
    {
      id: 3,
      title: 'Payment Due',
      message: 'Monthly payment for 5 KOLs is pending',
      time: '3h ago',
      type: 'warning',
      icon: '💰'
    }
  ]

  return (
    <div style={{ position: 'relative' }}>
      <header style={{
        background: 'rgba(255, 255, 255, 0.95)',
        backdropFilter: 'blur(20px)',
        borderBottom: '1px solid rgba(229, 231, 235, 0.5)',
        padding: '12px 24px',
        position: 'sticky',
        top: 0,
        zIndex: 30,
        boxShadow: '0 1px 3px rgba(0, 0, 0, 0.1)'
      }}>
        <div style={{
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'space-between'
        }}>
          {/* Left side */}
          <div style={{ display: 'flex', alignItems: 'center', gap: '16px' }}>
            <button
              onClick={onMenuToggle}
              style={{
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                width: '40px',
                height: '40px',
                border: 'none',
                borderRadius: '8px',
                background: 'transparent',
                cursor: 'pointer',
                transition: 'background 0.2s'
              }}
              onMouseOver={(e) => {
                e.currentTarget.style.background = '#f3f4f6'
              }}
              onMouseOut={(e) => {
                e.currentTarget.style.background = 'transparent'
              }}
            >
              <span style={{ fontSize: '18px' }}>☰</span>
            </button>

            <div>
              <h1 style={{
                fontSize: '20px',
                fontWeight: 'bold',
                background: 'linear-gradient(135deg, #1f2937, #6b7280)',
                WebkitBackgroundClip: 'text',
                WebkitTextFillColor: 'transparent',
                margin: '0 0 2px 0'
              }}>
                {title}
              </h1>
              <p style={{
                fontSize: '12px',
                color: '#6b7280',
                margin: 0
              }}>
                KOL Management System
              </p>
            </div>
          </div>

          {/* Center - Search */}
          <div style={{
            flex: 1,
            maxWidth: '400px',
            margin: '0 32px',
            position: 'relative',
            display: isDesktop ? 'block' : 'none'
          }}>
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
              placeholder="Search KOLs, campaigns, analytics..."
              style={{
                width: '100%',
                height: '40px',
                paddingLeft: '40px',
                paddingRight: '80px',
                border: '1px solid #e5e7eb',
                borderRadius: '10px',
                fontSize: '14px',
                backgroundColor: 'rgba(243, 244, 246, 0.5)',
                transition: 'all 0.2s',
                outline: 'none'
              }}
              onFocus={(e) => {
                e.target.style.borderColor = '#3b82f6'
                e.target.style.backgroundColor = 'white'
                e.target.style.boxShadow = '0 0 0 3px rgba(59, 130, 246, 0.1)'
              }}
              onBlur={(e) => {
                e.target.style.borderColor = '#e5e7eb'
                e.target.style.backgroundColor = 'rgba(243, 244, 246, 0.5)'
                e.target.style.boxShadow = 'none'
              }}
            />
            <div style={{
              position: 'absolute',
              right: '12px',
              top: '50%',
              transform: 'translateY(-50%)',
              padding: '4px 8px',
              background: '#f3f4f6',
              borderRadius: '4px',
              fontSize: '10px',
              color: '#6b7280',
              fontFamily: 'monospace'
            }}>
              ⌘K
            </div>
          </div>

          {/* Right side */}
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
            {/* Mobile Search */}
            <button style={{
              display: window.innerWidth <= 768 ? 'flex' : 'none',
              alignItems: 'center',
              justifyContent: 'center',
              width: '40px',
              height: '40px',
              border: 'none',
              borderRadius: '8px',
              background: 'transparent',
              cursor: 'pointer',
              transition: 'background 0.2s'
            }}
            onMouseOver={(e) => {
              e.currentTarget.style.background = '#f3f4f6'
            }}
            onMouseOut={(e) => {
              e.currentTarget.style.background = 'transparent'
            }}>
              <span style={{ fontSize: '16px' }}>🔍</span>
            </button>

            {/* Notifications */}
            <div style={{ position: 'relative' }}>
              <button
                onClick={() => setShowNotifications(!showNotifications)}
                style={{
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center',
                  width: '40px',
                  height: '40px',
                  border: 'none',
                  borderRadius: '8px',
                  background: 'transparent',
                  cursor: 'pointer',
                  transition: 'background 0.2s',
                  position: 'relative'
                }}
                onMouseOver={(e) => {
                  e.currentTarget.style.background = '#f3f4f6'
                }}
                onMouseOut={(e) => {
                  e.currentTarget.style.background = 'transparent'
                }}
              >
                <span style={{ fontSize: '16px' }}>🔔</span>
                <div style={{
                  position: 'absolute',
                  top: '8px',
                  right: '8px',
                  width: '8px',
                  height: '8px',
                  background: '#ef4444',
                  borderRadius: '50%',
                  fontSize: '10px',
                  color: 'white',
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center'
                }}></div>
              </button>

              {/* Notifications Dropdown */}
              {showNotifications && (
                <div style={{
                  position: 'absolute',
                  top: '50px',
                  right: '0',
                  width: '320px',
                  background: 'white',
                  borderRadius: '12px',
                  boxShadow: '0 10px 30px rgba(0, 0, 0, 0.15)',
                  border: '1px solid #e5e7eb',
                  overflow: 'hidden',
                  zIndex: 50
                }}>
                  <div style={{
                    padding: '16px',
                    borderBottom: '1px solid #f3f4f6',
                    background: '#f9fafb'
                  }}>
                    <h3 style={{
                      fontSize: '16px',
                      fontWeight: '600',
                      color: '#1f2937',
                      margin: 0
                    }}>
                      Notifications
                    </h3>
                  </div>
                  <div style={{ maxHeight: '300px', overflowY: 'auto' }}>
                    {notifications.map((notification) => (
                      <div key={notification.id} style={{
                        padding: '16px',
                        borderBottom: '1px solid #f3f4f6',
                        cursor: 'pointer',
                        transition: 'background 0.2s'
                      }}
                      onMouseOver={(e) => {
                        e.currentTarget.style.background = '#f9fafb'
                      }}
                      onMouseOut={(e) => {
                        e.currentTarget.style.background = 'transparent'
                      }}>
                        <div style={{ display: 'flex', alignItems: 'flex-start', gap: '12px' }}>
                          <div style={{
                            width: '8px',
                            height: '8px',
                            borderRadius: '50%',
                            background: notification.type === 'success' ? '#10b981' :
                                       notification.type === 'warning' ? '#f59e0b' : '#3b82f6',
                            marginTop: '6px'
                          }}></div>
                          <div style={{ flex: 1 }}>
                            <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '4px' }}>
                              <span style={{ fontSize: '14px' }}>{notification.icon}</span>
                              <span style={{
                                fontSize: '14px',
                                fontWeight: '500',
                                color: '#1f2937'
                              }}>
                                {notification.title}
                              </span>
                              <span style={{
                                fontSize: '12px',
                                color: '#6b7280',
                                marginLeft: 'auto'
                              }}>
                                {notification.time}
                              </span>
                            </div>
                            <p style={{
                              fontSize: '12px',
                              color: '#6b7280',
                              margin: 0
                            }}>
                              {notification.message}
                            </p>
                          </div>
                        </div>
                      </div>
                    ))}
                  </div>
                  <div style={{
                    padding: '12px 16px',
                    borderTop: '1px solid #f3f4f6',
                    background: '#f9fafb'
                  }}>
                    <button style={{
                      width: '100%',
                      padding: '8px',
                      border: 'none',
                      background: 'transparent',
                      color: '#3b82f6',
                      fontSize: '14px',
                      fontWeight: '500',
                      cursor: 'pointer',
                      borderRadius: '6px',
                      transition: 'background 0.2s'
                    }}
                    onMouseOver={(e) => {
                      e.currentTarget.style.background = '#eff6ff'
                    }}
                    onMouseOut={(e) => {
                      e.currentTarget.style.background = 'transparent'
                    }}>
                      View all notifications
                    </button>
                  </div>
                </div>
              )}
            </div>

            {/* Profile */}
            <div style={{ position: 'relative' }}>
              <button
                onClick={() => setShowProfile(!showProfile)}
                style={{
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center',
                  width: '40px',
                  height: '40px',
                  border: '2px solid #e5e7eb',
                  borderRadius: '10px',
                  background: 'linear-gradient(135deg, #3b82f6, #8b5cf6)',
                  cursor: 'pointer',
                  transition: 'transform 0.2s'
                }}
                onMouseOver={(e) => {
                  e.currentTarget.style.transform = 'scale(1.05)'
                }}
                onMouseOut={(e) => {
                  e.currentTarget.style.transform = 'scale(1)'
                }}
              >
                <span style={{
                  color: 'white',
                  fontSize: '16px',
                  fontWeight: 'bold'
                }}>
                  JD
                </span>
              </button>

              {/* Profile Dropdown */}
              {showProfile && (
                <div style={{
                  position: 'absolute',
                  top: '50px',
                  right: '0',
                  width: '240px',
                  background: 'white',
                  borderRadius: '12px',
                  boxShadow: '0 10px 30px rgba(0, 0, 0, 0.15)',
                  border: '1px solid #e5e7eb',
                  overflow: 'hidden',
                  zIndex: 50
                }}>
                  <div style={{
                    padding: '16px',
                    borderBottom: '1px solid #f3f4f6'
                  }}>
                    <div style={{ display: 'flex', flexDirection: 'column', gap: '4px' }}>
                      <p style={{
                        fontSize: '14px',
                        fontWeight: '500',
                        color: '#1f2937',
                        margin: 0
                      }}>
                        John Doe
                      </p>
                      <p style={{
                        fontSize: '12px',
                        color: '#6b7280',
                        margin: 0
                      }}>
                        john@kolsystem.com
                      </p>
                      <span style={{
                        display: 'inline-block',
                        padding: '2px 8px',
                        background: '#dbeafe',
                        color: '#1d4ed8',
                        fontSize: '11px',
                        fontWeight: '500',
                        borderRadius: '4px',
                        width: 'fit-content',
                        marginTop: '4px'
                      }}>
                        Admin
                      </span>
                    </div>
                  </div>
                  <div style={{ padding: '8px' }}>
                    {[
                      { icon: '👤', label: 'Profile', onClick: () => {} },
                      { icon: '⚙️', label: 'Settings', onClick: () => {} },
                      { icon: '🚪', label: 'Sign out', onClick: () => {}, color: '#ef4444' }
                    ].map((item, index) => (
                      <button key={index}
                        onClick={item.onClick}
                        style={{
                          width: '100%',
                          display: 'flex',
                          alignItems: 'center',
                          gap: '12px',
                          padding: '12px',
                          border: 'none',
                          background: 'transparent',
                          color: item.color || '#374151',
                          fontSize: '14px',
                          cursor: 'pointer',
                          borderRadius: '8px',
                          transition: 'background 0.2s',
                          textAlign: 'left'
                        }}
                        onMouseOver={(e) => {
                          e.currentTarget.style.background = '#f3f4f6'
                        }}
                        onMouseOut={(e) => {
                          e.currentTarget.style.background = 'transparent'
                        }}
                      >
                        <span style={{ fontSize: '16px' }}>{item.icon}</span>
                        {item.label}
                      </button>
                    ))}
                  </div>
                </div>
              )}
            </div>
          </div>
        </div>
      </header>

      {/* Overlay for dropdowns */}
      {(showNotifications || showProfile) && (
        <div
          style={{
            position: 'fixed',
            inset: 0,
            zIndex: 40
          }}
          onClick={() => {
            setShowNotifications(false)
            setShowProfile(false)
          }}
        />
      )}
    </div>
  )
}