'use client'

import { useState, useEffect } from 'react'
import { SimpleHeader } from './SimpleHeader'
import { SimpleSidebar } from './SimpleSidebar'

interface SimpleLayoutProps {
  children: React.ReactNode
  title?: string
}

export function SimpleLayout({ children, title }: SimpleLayoutProps) {
  const [sidebarOpen, setSidebarOpen] = useState(false)
  const [aiChatOpen, setAiChatOpen] = useState(false)
  const [isDesktop, setIsDesktop] = useState(false)

  useEffect(() => {
    const checkScreenSize = () => {
      setIsDesktop(window.innerWidth >= 1024)
    }

    // Check initial screen size
    checkScreenSize()

    // Add event listener for window resize
    window.addEventListener('resize', checkScreenSize)

    // Cleanup
    return () => window.removeEventListener('resize', checkScreenSize)
  }, [])

  return (
    <div style={{ minHeight: '100vh', background: '#f8fafc' }}>
      {/* Sidebar */}
      <SimpleSidebar
        isOpen={sidebarOpen}
        onToggle={() => setSidebarOpen(!sidebarOpen)}
        onAIToggle={() => setAiChatOpen(true)}
      />

      {/* Main content */}
      <div style={{
        marginLeft: isDesktop ? '280px' : '0',
        display: 'flex',
        flexDirection: 'column',
        minHeight: '100vh',
        transition: 'margin-left 0.3s ease-in-out'
      }}>
        {/* Header */}
        <SimpleHeader
          onMenuToggle={() => setSidebarOpen(!sidebarOpen)}
          title={title}
        />

        {/* Page content */}
        <main style={{
          flex: 1,
          background: 'linear-gradient(135deg, #f8fafc 0%, #e2e8f0 100%)',
          position: 'relative',
          overflow: 'hidden'
        }}>
          {/* Background Pattern */}
          <div style={{
            position: 'absolute',
            inset: 0,
            backgroundImage: 'radial-gradient(circle, rgba(255, 255, 255, 0.1) 1px, transparent 1px)',
            backgroundSize: '20px 20px',
            pointerEvents: 'none'
          }}></div>

          <div style={{
            position: 'relative',
            zIndex: 10,
            padding: '0'
          }}>
            {children}
          </div>
        </main>
      </div>

      {/* AI Chat Sidebar Placeholder */}
      {aiChatOpen && (
        <div style={{
          position: 'fixed',
          right: 0,
          top: 0,
          width: '400px',
          height: '100vh',
          background: 'rgba(255, 255, 255, 0.95)',
          backdropFilter: 'blur(20px)',
          borderLeft: '1px solid rgba(229, 231, 235, 0.5)',
          boxShadow: '-2px 0 10px rgba(0, 0, 0, 0.1)',
          zIndex: 50,
          padding: '24px',
          display: 'flex',
          flexDirection: 'column'
        }}>
          <div style={{
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'space-between',
            marginBottom: '24px'
          }}>
            <h3 style={{
              fontSize: '18px',
              fontWeight: '600',
              color: '#1f2937',
              margin: 0
            }}>
              AI Assistant
            </h3>
            <button
              onClick={() => setAiChatOpen(false)}
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
              <span style={{ fontSize: '16px' }}>✕</span>
            </button>
          </div>

          <div style={{
            flex: 1,
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            flexDirection: 'column',
            gap: '16px',
            color: '#6b7280'
          }}>
            <div style={{
              width: '80px',
              height: '80px',
              borderRadius: '20px',
              background: 'linear-gradient(135deg, #f3f4f6, #e5e7eb)',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              fontSize: '32px'
            }}>
              🤖
            </div>
            <p style={{ textAlign: 'center', margin: 0 }}>
              AI Assistant coming soon...
            </p>
          </div>
        </div>
      )}

      {/* AI Chat Overlay */}
      {aiChatOpen && (
        <div
          style={{
            position: 'fixed',
            inset: 0,
            background: 'rgba(0, 0, 0, 0.3)',
            zIndex: 45
          }}
          onClick={() => setAiChatOpen(false)}
        />
      )}
    </div>
  )
}