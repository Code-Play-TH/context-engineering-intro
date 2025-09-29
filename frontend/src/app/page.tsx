'use client'

import { useEffect } from 'react'
import { useRouter } from 'next/navigation'
import { useAuthStore } from '@/stores/auth'

export default function HomePage() {
  const router = useRouter()
  const { isAuthenticated, isLoading } = useAuthStore()

  useEffect(() => {
    if (!isLoading) {
      if (isAuthenticated) {
        router.replace('/dashboard')
      } else {
        router.replace('/login')
      }
    }
  }, [isAuthenticated, isLoading, router])

  return (
    <div style={{
      minHeight: '100vh',
      display: 'flex',
      alignItems: 'center',
      justifyContent: 'center',
      background: 'linear-gradient(135deg, #f8fafc 0%, #e2e8f0 100%)',
      padding: '20px'
    }}>
      <div style={{ textAlign: 'center' }}>
        <div style={{
          width: '80px',
          height: '80px',
          background: 'linear-gradient(135deg, #3b82f6, #8b5cf6)',
          borderRadius: '20px',
          margin: '0 auto 24px',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          boxShadow: '0 20px 40px rgba(59, 130, 246, 0.3)',
          animation: 'pulse 2s infinite'
        }}>
          <span style={{ color: 'white', fontSize: '36px', fontWeight: 'bold' }}>KOL</span>
        </div>
        <h1 style={{
          fontSize: '24px',
          fontWeight: '600',
          background: 'linear-gradient(135deg, #1f2937, #6b7280)',
          WebkitBackgroundClip: 'text',
          WebkitTextFillColor: 'transparent',
          margin: '0 0 8px 0'
        }}>
          KOL Management System
        </h1>
        <p style={{ color: '#6b7280', fontSize: '14px', margin: '0 0 24px 0' }}>
          Loading your dashboard...
        </p>
        <div style={{ display: 'flex', justifyContent: 'center', gap: '4px' }}>
          <div style={{
            width: '8px',
            height: '8px',
            background: '#3b82f6',
            borderRadius: '50%',
            animation: 'bounce 1.4s infinite ease-in-out',
            animationDelay: '-0.32s'
          }}></div>
          <div style={{
            width: '8px',
            height: '8px',
            background: '#3b82f6',
            borderRadius: '50%',
            animation: 'bounce 1.4s infinite ease-in-out',
            animationDelay: '-0.16s'
          }}></div>
          <div style={{
            width: '8px',
            height: '8px',
            background: '#3b82f6',
            borderRadius: '50%',
            animation: 'bounce 1.4s infinite ease-in-out'
          }}></div>
        </div>
      </div>
      <style jsx>{`
        @keyframes pulse {
          0%, 100% { transform: scale(1); }
          50% { transform: scale(1.05); }
        }
        @keyframes bounce {
          0%, 80%, 100% { transform: scale(0); }
          40% { transform: scale(1); }
        }
      `}</style>
    </div>
  )
}
