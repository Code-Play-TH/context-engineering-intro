'use client'

import { useState } from 'react'

interface Settings {
  general: {
    companyName: string
    timezone: string
    language: string
    currency: string
    dateFormat: string
  }
  notifications: {
    emailNotifications: boolean
    pushNotifications: boolean
    reportReminders: boolean
    campaignAlerts: boolean
    weeklyDigest: boolean
  }
  security: {
    twoFactorAuth: boolean
    sessionTimeout: number
    passwordExpiry: number
    loginNotifications: boolean
  }
  integrations: {
    googleAnalytics: boolean
    facebookPixel: boolean
    tiktokPixel: boolean
    slackWebhook: string
    discordWebhook: string
  }
  appearance: {
    theme: 'light' | 'dark' | 'auto'
    sidebarCollapsed: boolean
    compactMode: boolean
    animationsEnabled: boolean
  }
}

const defaultSettings: Settings = {
  general: {
    companyName: 'KOL Management Co.',
    timezone: 'Asia/Bangkok',
    language: 'English',
    currency: 'THB',
    dateFormat: 'DD/MM/YYYY'
  },
  notifications: {
    emailNotifications: true,
    pushNotifications: true,
    reportReminders: true,
    campaignAlerts: true,
    weeklyDigest: false
  },
  security: {
    twoFactorAuth: false,
    sessionTimeout: 60,
    passwordExpiry: 90,
    loginNotifications: true
  },
  integrations: {
    googleAnalytics: false,
    facebookPixel: false,
    tiktokPixel: true,
    slackWebhook: '',
    discordWebhook: ''
  },
  appearance: {
    theme: 'light',
    sidebarCollapsed: false,
    compactMode: false,
    animationsEnabled: true
  }
}

export function SettingsManager() {
  const [settings, setSettings] = useState<Settings>(defaultSettings)
  const [activeTab, setActiveTab] = useState('general')
  const [hasUnsavedChanges, setHasUnsavedChanges] = useState(false)

  const tabs = [
    { id: 'general', label: 'General', icon: '⚙️' },
    { id: 'notifications', label: 'Notifications', icon: '🔔' },
    { id: 'security', label: 'Security', icon: '🔒' },
    { id: 'integrations', label: 'Integrations', icon: '🔗' },
    { id: 'appearance', label: 'Appearance', icon: '🎨' }
  ]

  const updateSetting = (section: keyof Settings, key: string, value: any) => {
    setSettings(prev => ({
      ...prev,
      [section]: {
        ...prev[section],
        [key]: value
      }
    }))
    setHasUnsavedChanges(true)
  }

  const saveSettings = () => {
    // Simulate saving settings
    console.log('Saving settings:', settings)
    setHasUnsavedChanges(false)
    // Add success notification here
  }

  const resetSettings = () => {
    setSettings(defaultSettings)
    setHasUnsavedChanges(false)
  }

  return (
    <div style={{ padding: '24px', maxWidth: '1200px', margin: '0 auto' }}>
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
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '8px' }}>
          <h1 style={{
            fontSize: '32px',
            fontWeight: '700',
            background: 'linear-gradient(135deg, #1f2937, #3b82f6)',
            WebkitBackgroundClip: 'text',
            WebkitTextFillColor: 'transparent',
            margin: 0
          }}>
            ⚙️ Settings
          </h1>
          <div style={{ display: 'flex', gap: '12px' }}>
            {hasUnsavedChanges && (
              <button
                onClick={resetSettings}
                style={{
                  background: 'rgba(239, 68, 68, 0.1)',
                  color: '#ef4444',
                  border: '1px solid rgba(239, 68, 68, 0.2)',
                  borderRadius: '8px',
                  padding: '8px 16px',
                  fontSize: '14px',
                  fontWeight: '500',
                  cursor: 'pointer'
                }}
              >
                Reset
              </button>
            )}
            <button
              onClick={saveSettings}
              disabled={!hasUnsavedChanges}
              style={{
                background: hasUnsavedChanges
                  ? 'linear-gradient(135deg, #3b82f6, #1d4ed8)'
                  : 'rgba(107, 114, 128, 0.3)',
                color: hasUnsavedChanges ? 'white' : '#6b7280',
                border: 'none',
                borderRadius: '8px',
                padding: '8px 16px',
                fontSize: '14px',
                fontWeight: '600',
                cursor: hasUnsavedChanges ? 'pointer' : 'not-allowed'
              }}
            >
              {hasUnsavedChanges ? 'Save Changes' : 'All Saved'}
            </button>
          </div>
        </div>
        <p style={{ fontSize: '16px', color: '#6b7280', margin: 0 }}>
          Configure your KOL management system preferences
        </p>
      </div>

      {/* Settings Content */}
      <div style={{ display: 'grid', gridTemplateColumns: '280px 1fr', gap: '24px' }}>
        {/* Sidebar Navigation */}
        <div style={{
          background: 'rgba(255, 255, 255, 0.95)',
          backdropFilter: 'blur(20px)',
          borderRadius: '20px',
          padding: '24px',
          boxShadow: '0 20px 40px rgba(0, 0, 0, 0.1)',
          border: '1px solid rgba(229, 231, 235, 0.5)',
          height: 'fit-content'
        }}>
          <nav style={{ display: 'flex', flexDirection: 'column', gap: '8px' }}>
            {tabs.map(tab => (
              <button
                key={tab.id}
                onClick={() => setActiveTab(tab.id)}
                style={{
                  width: '100%',
                  display: 'flex',
                  alignItems: 'center',
                  gap: '12px',
                  padding: '12px 16px',
                  borderRadius: '12px',
                  background: activeTab === tab.id
                    ? 'linear-gradient(135deg, rgba(59, 130, 246, 0.1), rgba(139, 92, 246, 0.05))'
                    : 'transparent',
                  color: activeTab === tab.id ? '#3b82f6' : '#6b7280',
                  border: 'none',
                  fontSize: '14px',
                  fontWeight: activeTab === tab.id ? '600' : '500',
                  cursor: 'pointer',
                  transition: 'all 0.2s',
                  textAlign: 'left'
                }}
                onMouseOver={(e) => {
                  if (activeTab !== tab.id) {
                    e.currentTarget.style.background = 'rgba(243, 244, 246, 0.5)'
                    e.currentTarget.style.color = '#374151'
                  }
                }}
                onMouseOut={(e) => {
                  if (activeTab !== tab.id) {
                    e.currentTarget.style.background = 'transparent'
                    e.currentTarget.style.color = '#6b7280'
                  }
                }}
              >
                <span style={{ fontSize: '16px' }}>{tab.icon}</span>
                {tab.label}
              </button>
            ))}
          </nav>
        </div>

        {/* Settings Panel */}
        <div style={{
          background: 'rgba(255, 255, 255, 0.95)',
          backdropFilter: 'blur(20px)',
          borderRadius: '20px',
          padding: '32px',
          boxShadow: '0 20px 40px rgba(0, 0, 0, 0.1)',
          border: '1px solid rgba(229, 231, 235, 0.5)',
          minHeight: '600px'
        }}>
          {activeTab === 'general' && (
            <GeneralSettings settings={settings.general} updateSetting={(key, value) => updateSetting('general', key, value)} />
          )}
          {activeTab === 'notifications' && (
            <NotificationSettings settings={settings.notifications} updateSetting={(key, value) => updateSetting('notifications', key, value)} />
          )}
          {activeTab === 'security' && (
            <SecuritySettings settings={settings.security} updateSetting={(key, value) => updateSetting('security', key, value)} />
          )}
          {activeTab === 'integrations' && (
            <IntegrationSettings settings={settings.integrations} updateSetting={(key, value) => updateSetting('integrations', key, value)} />
          )}
          {activeTab === 'appearance' && (
            <AppearanceSettings settings={settings.appearance} updateSetting={(key, value) => updateSetting('appearance', key, value)} />
          )}
        </div>
      </div>
    </div>
  )
}

function GeneralSettings({ settings, updateSetting }: { settings: any, updateSetting: (key: string, value: any) => void }) {
  return (
    <div>
      <h2 style={{ fontSize: '20px', fontWeight: '700', color: '#1f2937', marginBottom: '24px' }}>
        General Settings
      </h2>

      <div style={{ display: 'grid', gap: '24px' }}>
        <div>
          <label style={{ fontSize: '14px', fontWeight: '600', color: '#374151', marginBottom: '8px', display: 'block' }}>
            Company Name
          </label>
          <input
            type="text"
            value={settings.companyName}
            onChange={(e) => updateSetting('companyName', e.target.value)}
            style={{
              width: '100%',
              padding: '12px 16px',
              border: '1px solid rgba(229, 231, 235, 0.5)',
              borderRadius: '8px',
              fontSize: '14px',
              background: 'rgba(255, 255, 255, 0.8)'
            }}
          />
        </div>

        <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '16px' }}>
          <div>
            <label style={{ fontSize: '14px', fontWeight: '600', color: '#374151', marginBottom: '8px', display: 'block' }}>
              Timezone
            </label>
            <select
              value={settings.timezone}
              onChange={(e) => updateSetting('timezone', e.target.value)}
              style={{
                width: '100%',
                padding: '12px 16px',
                border: '1px solid rgba(229, 231, 235, 0.5)',
                borderRadius: '8px',
                fontSize: '14px',
                background: 'rgba(255, 255, 255, 0.8)'
              }}
            >
              <option value="Asia/Bangkok">Asia/Bangkok (UTC+7)</option>
              <option value="America/New_York">America/New_York (EST)</option>
              <option value="Europe/London">Europe/London (GMT)</option>
              <option value="Asia/Tokyo">Asia/Tokyo (JST)</option>
            </select>
          </div>

          <div>
            <label style={{ fontSize: '14px', fontWeight: '600', color: '#374151', marginBottom: '8px', display: 'block' }}>
              Language
            </label>
            <select
              value={settings.language}
              onChange={(e) => updateSetting('language', e.target.value)}
              style={{
                width: '100%',
                padding: '12px 16px',
                border: '1px solid rgba(229, 231, 235, 0.5)',
                borderRadius: '8px',
                fontSize: '14px',
                background: 'rgba(255, 255, 255, 0.8)'
              }}
            >
              <option value="English">English</option>
              <option value="Thai">ไทย (Thai)</option>
              <option value="Chinese">中文 (Chinese)</option>
              <option value="Japanese">日本語 (Japanese)</option>
            </select>
          </div>
        </div>

        <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '16px' }}>
          <div>
            <label style={{ fontSize: '14px', fontWeight: '600', color: '#374151', marginBottom: '8px', display: 'block' }}>
              Currency
            </label>
            <select
              value={settings.currency}
              onChange={(e) => updateSetting('currency', e.target.value)}
              style={{
                width: '100%',
                padding: '12px 16px',
                border: '1px solid rgba(229, 231, 235, 0.5)',
                borderRadius: '8px',
                fontSize: '14px',
                background: 'rgba(255, 255, 255, 0.8)'
              }}
            >
              <option value="THB">THB (Thai Baht)</option>
              <option value="USD">USD (US Dollar)</option>
              <option value="EUR">EUR (Euro)</option>
              <option value="JPY">JPY (Japanese Yen)</option>
            </select>
          </div>

          <div>
            <label style={{ fontSize: '14px', fontWeight: '600', color: '#374151', marginBottom: '8px', display: 'block' }}>
              Date Format
            </label>
            <select
              value={settings.dateFormat}
              onChange={(e) => updateSetting('dateFormat', e.target.value)}
              style={{
                width: '100%',
                padding: '12px 16px',
                border: '1px solid rgba(229, 231, 235, 0.5)',
                borderRadius: '8px',
                fontSize: '14px',
                background: 'rgba(255, 255, 255, 0.8)'
              }}
            >
              <option value="DD/MM/YYYY">DD/MM/YYYY</option>
              <option value="MM/DD/YYYY">MM/DD/YYYY</option>
              <option value="YYYY-MM-DD">YYYY-MM-DD</option>
            </select>
          </div>
        </div>
      </div>
    </div>
  )
}

function NotificationSettings({ settings, updateSetting }: { settings: any, updateSetting: (key: string, value: any) => void }) {
  const toggles = [
    { key: 'emailNotifications', label: 'Email Notifications', description: 'Receive notifications via email' },
    { key: 'pushNotifications', label: 'Push Notifications', description: 'Receive browser push notifications' },
    { key: 'reportReminders', label: 'Report Reminders', description: 'Get reminded about pending reports' },
    { key: 'campaignAlerts', label: 'Campaign Alerts', description: 'Alerts for campaign milestones and issues' },
    { key: 'weeklyDigest', label: 'Weekly Digest', description: 'Weekly summary of activities and performance' }
  ]

  return (
    <div>
      <h2 style={{ fontSize: '20px', fontWeight: '700', color: '#1f2937', marginBottom: '24px' }}>
        Notification Preferences
      </h2>

      <div style={{ display: 'grid', gap: '16px' }}>
        {toggles.map(toggle => (
          <div key={toggle.key} style={{
            display: 'flex',
            justifyContent: 'space-between',
            alignItems: 'center',
            padding: '16px',
            background: 'rgba(248, 250, 252, 0.5)',
            borderRadius: '12px',
            border: '1px solid rgba(229, 231, 235, 0.3)'
          }}>
            <div>
              <div style={{ fontSize: '14px', fontWeight: '600', color: '#1f2937', marginBottom: '4px' }}>
                {toggle.label}
              </div>
              <div style={{ fontSize: '12px', color: '#6b7280' }}>
                {toggle.description}
              </div>
            </div>
            <label style={{
              position: 'relative',
              display: 'inline-block',
              width: '44px',
              height: '24px',
              cursor: 'pointer'
            }}>
              <input
                type="checkbox"
                checked={settings[toggle.key]}
                onChange={(e) => updateSetting(toggle.key, e.target.checked)}
                style={{ opacity: 0, width: 0, height: 0 }}
              />
              <span style={{
                position: 'absolute',
                cursor: 'pointer',
                top: 0,
                left: 0,
                right: 0,
                bottom: 0,
                background: settings[toggle.key] ? '#3b82f6' : '#cbd5e1',
                transition: '0.3s',
                borderRadius: '24px'
              }}>
                <span style={{
                  position: 'absolute',
                  content: '',
                  height: '18px',
                  width: '18px',
                  left: settings[toggle.key] ? '23px' : '3px',
                  bottom: '3px',
                  background: 'white',
                  transition: '0.3s',
                  borderRadius: '50%'
                }}></span>
              </span>
            </label>
          </div>
        ))}
      </div>
    </div>
  )
}

function SecuritySettings({ settings, updateSetting }: { settings: any, updateSetting: (key: string, value: any) => void }) {
  return (
    <div>
      <h2 style={{ fontSize: '20px', fontWeight: '700', color: '#1f2937', marginBottom: '24px' }}>
        Security Settings
      </h2>

      <div style={{ display: 'grid', gap: '24px' }}>
        <div style={{
          display: 'flex',
          justifyContent: 'space-between',
          alignItems: 'center',
          padding: '16px',
          background: 'rgba(248, 250, 252, 0.5)',
          borderRadius: '12px',
          border: '1px solid rgba(229, 231, 235, 0.3)'
        }}>
          <div>
            <div style={{ fontSize: '14px', fontWeight: '600', color: '#1f2937', marginBottom: '4px' }}>
              Two-Factor Authentication
            </div>
            <div style={{ fontSize: '12px', color: '#6b7280' }}>
              Add an extra layer of security to your account
            </div>
          </div>
          <label style={{
            position: 'relative',
            display: 'inline-block',
            width: '44px',
            height: '24px',
            cursor: 'pointer'
          }}>
            <input
              type="checkbox"
              checked={settings.twoFactorAuth}
              onChange={(e) => updateSetting('twoFactorAuth', e.target.checked)}
              style={{ opacity: 0, width: 0, height: 0 }}
            />
            <span style={{
              position: 'absolute',
              cursor: 'pointer',
              top: 0,
              left: 0,
              right: 0,
              bottom: 0,
              background: settings.twoFactorAuth ? '#3b82f6' : '#cbd5e1',
              transition: '0.3s',
              borderRadius: '24px'
            }}>
              <span style={{
                position: 'absolute',
                content: '',
                height: '18px',
                width: '18px',
                left: settings.twoFactorAuth ? '23px' : '3px',
                bottom: '3px',
                background: 'white',
                transition: '0.3s',
                borderRadius: '50%'
              }}></span>
            </span>
          </label>
        </div>

        <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '16px' }}>
          <div>
            <label style={{ fontSize: '14px', fontWeight: '600', color: '#374151', marginBottom: '8px', display: 'block' }}>
              Session Timeout (minutes)
            </label>
            <input
              type="number"
              value={settings.sessionTimeout}
              onChange={(e) => updateSetting('sessionTimeout', parseInt(e.target.value))}
              min="15"
              max="480"
              style={{
                width: '100%',
                padding: '12px 16px',
                border: '1px solid rgba(229, 231, 235, 0.5)',
                borderRadius: '8px',
                fontSize: '14px',
                background: 'rgba(255, 255, 255, 0.8)'
              }}
            />
          </div>

          <div>
            <label style={{ fontSize: '14px', fontWeight: '600', color: '#374151', marginBottom: '8px', display: 'block' }}>
              Password Expiry (days)
            </label>
            <input
              type="number"
              value={settings.passwordExpiry}
              onChange={(e) => updateSetting('passwordExpiry', parseInt(e.target.value))}
              min="30"
              max="365"
              style={{
                width: '100%',
                padding: '12px 16px',
                border: '1px solid rgba(229, 231, 235, 0.5)',
                borderRadius: '8px',
                fontSize: '14px',
                background: 'rgba(255, 255, 255, 0.8)'
              }}
            />
          </div>
        </div>

        <div style={{
          display: 'flex',
          justifyContent: 'space-between',
          alignItems: 'center',
          padding: '16px',
          background: 'rgba(248, 250, 252, 0.5)',
          borderRadius: '12px',
          border: '1px solid rgba(229, 231, 235, 0.3)'
        }}>
          <div>
            <div style={{ fontSize: '14px', fontWeight: '600', color: '#1f2937', marginBottom: '4px' }}>
              Login Notifications
            </div>
            <div style={{ fontSize: '12px', color: '#6b7280' }}>
              Get notified of new login attempts
            </div>
          </div>
          <label style={{
            position: 'relative',
            display: 'inline-block',
            width: '44px',
            height: '24px',
            cursor: 'pointer'
          }}>
            <input
              type="checkbox"
              checked={settings.loginNotifications}
              onChange={(e) => updateSetting('loginNotifications', e.target.checked)}
              style={{ opacity: 0, width: 0, height: 0 }}
            />
            <span style={{
              position: 'absolute',
              cursor: 'pointer',
              top: 0,
              left: 0,
              right: 0,
              bottom: 0,
              background: settings.loginNotifications ? '#3b82f6' : '#cbd5e1',
              transition: '0.3s',
              borderRadius: '24px'
            }}>
              <span style={{
                position: 'absolute',
                content: '',
                height: '18px',
                width: '18px',
                left: settings.loginNotifications ? '23px' : '3px',
                bottom: '3px',
                background: 'white',
                transition: '0.3s',
                borderRadius: '50%'
              }}></span>
            </span>
          </label>
        </div>
      </div>
    </div>
  )
}

function IntegrationSettings({ settings, updateSetting }: { settings: any, updateSetting: (key: string, value: any) => void }) {
  const integrations = [
    { key: 'googleAnalytics', label: 'Google Analytics', description: 'Track website analytics' },
    { key: 'facebookPixel', label: 'Facebook Pixel', description: 'Track Facebook ad conversions' },
    { key: 'tiktokPixel', label: 'TikTok Pixel', description: 'Track TikTok ad performance' }
  ]

  return (
    <div>
      <h2 style={{ fontSize: '20px', fontWeight: '700', color: '#1f2937', marginBottom: '24px' }}>
        Third-party Integrations
      </h2>

      <div style={{ display: 'grid', gap: '24px' }}>
        {integrations.map(integration => (
          <div key={integration.key} style={{
            display: 'flex',
            justifyContent: 'space-between',
            alignItems: 'center',
            padding: '16px',
            background: 'rgba(248, 250, 252, 0.5)',
            borderRadius: '12px',
            border: '1px solid rgba(229, 231, 235, 0.3)'
          }}>
            <div>
              <div style={{ fontSize: '14px', fontWeight: '600', color: '#1f2937', marginBottom: '4px' }}>
                {integration.label}
              </div>
              <div style={{ fontSize: '12px', color: '#6b7280' }}>
                {integration.description}
              </div>
            </div>
            <label style={{
              position: 'relative',
              display: 'inline-block',
              width: '44px',
              height: '24px',
              cursor: 'pointer'
            }}>
              <input
                type="checkbox"
                checked={settings[integration.key]}
                onChange={(e) => updateSetting(integration.key, e.target.checked)}
                style={{ opacity: 0, width: 0, height: 0 }}
              />
              <span style={{
                position: 'absolute',
                cursor: 'pointer',
                top: 0,
                left: 0,
                right: 0,
                bottom: 0,
                background: settings[integration.key] ? '#3b82f6' : '#cbd5e1',
                transition: '0.3s',
                borderRadius: '24px'
              }}>
                <span style={{
                  position: 'absolute',
                  content: '',
                  height: '18px',
                  width: '18px',
                  left: settings[integration.key] ? '23px' : '3px',
                  bottom: '3px',
                  background: 'white',
                  transition: '0.3s',
                  borderRadius: '50%'
                }}></span>
              </span>
            </label>
          </div>
        ))}

        <div>
          <label style={{ fontSize: '14px', fontWeight: '600', color: '#374151', marginBottom: '8px', display: 'block' }}>
            Slack Webhook URL
          </label>
          <input
            type="url"
            value={settings.slackWebhook}
            onChange={(e) => updateSetting('slackWebhook', e.target.value)}
            placeholder="https://hooks.slack.com/services/..."
            style={{
              width: '100%',
              padding: '12px 16px',
              border: '1px solid rgba(229, 231, 235, 0.5)',
              borderRadius: '8px',
              fontSize: '14px',
              background: 'rgba(255, 255, 255, 0.8)'
            }}
          />
        </div>

        <div>
          <label style={{ fontSize: '14px', fontWeight: '600', color: '#374151', marginBottom: '8px', display: 'block' }}>
            Discord Webhook URL
          </label>
          <input
            type="url"
            value={settings.discordWebhook}
            onChange={(e) => updateSetting('discordWebhook', e.target.value)}
            placeholder="https://discord.com/api/webhooks/..."
            style={{
              width: '100%',
              padding: '12px 16px',
              border: '1px solid rgba(229, 231, 235, 0.5)',
              borderRadius: '8px',
              fontSize: '14px',
              background: 'rgba(255, 255, 255, 0.8)'
            }}
          />
        </div>
      </div>
    </div>
  )
}

function AppearanceSettings({ settings, updateSetting }: { settings: any, updateSetting: (key: string, value: any) => void }) {
  const toggles = [
    { key: 'sidebarCollapsed', label: 'Collapsed Sidebar', description: 'Show sidebar in compact mode by default' },
    { key: 'compactMode', label: 'Compact Mode', description: 'Reduce spacing and padding throughout the interface' },
    { key: 'animationsEnabled', label: 'Animations', description: 'Enable smooth transitions and animations' }
  ]

  return (
    <div>
      <h2 style={{ fontSize: '20px', fontWeight: '700', color: '#1f2937', marginBottom: '24px' }}>
        Appearance & Interface
      </h2>

      <div style={{ display: 'grid', gap: '24px' }}>
        <div>
          <label style={{ fontSize: '14px', fontWeight: '600', color: '#374151', marginBottom: '8px', display: 'block' }}>
            Theme
          </label>
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: '12px' }}>
            {['light', 'dark', 'auto'].map(theme => (
              <button
                key={theme}
                onClick={() => updateSetting('theme', theme)}
                style={{
                  padding: '16px',
                  border: settings.theme === theme ? '2px solid #3b82f6' : '1px solid rgba(229, 231, 235, 0.5)',
                  borderRadius: '12px',
                  background: settings.theme === theme
                    ? 'rgba(59, 130, 246, 0.1)'
                    : 'rgba(255, 255, 255, 0.8)',
                  color: settings.theme === theme ? '#3b82f6' : '#6b7280',
                  fontSize: '14px',
                  fontWeight: '500',
                  cursor: 'pointer',
                  textAlign: 'center',
                  textTransform: 'capitalize',
                  transition: 'all 0.2s'
                }}
              >
                {theme === 'light' && '☀️'} {theme === 'dark' && '🌙'} {theme === 'auto' && '🔄'}
                <br />
                {theme}
              </button>
            ))}
          </div>
        </div>

        {toggles.map(toggle => (
          <div key={toggle.key} style={{
            display: 'flex',
            justifyContent: 'space-between',
            alignItems: 'center',
            padding: '16px',
            background: 'rgba(248, 250, 252, 0.5)',
            borderRadius: '12px',
            border: '1px solid rgba(229, 231, 235, 0.3)'
          }}>
            <div>
              <div style={{ fontSize: '14px', fontWeight: '600', color: '#1f2937', marginBottom: '4px' }}>
                {toggle.label}
              </div>
              <div style={{ fontSize: '12px', color: '#6b7280' }}>
                {toggle.description}
              </div>
            </div>
            <label style={{
              position: 'relative',
              display: 'inline-block',
              width: '44px',
              height: '24px',
              cursor: 'pointer'
            }}>
              <input
                type="checkbox"
                checked={settings[toggle.key]}
                onChange={(e) => updateSetting(toggle.key, e.target.checked)}
                style={{ opacity: 0, width: 0, height: 0 }}
              />
              <span style={{
                position: 'absolute',
                cursor: 'pointer',
                top: 0,
                left: 0,
                right: 0,
                bottom: 0,
                background: settings[toggle.key] ? '#3b82f6' : '#cbd5e1',
                transition: '0.3s',
                borderRadius: '24px'
              }}>
                <span style={{
                  position: 'absolute',
                  content: '',
                  height: '18px',
                  width: '18px',
                  left: settings[toggle.key] ? '23px' : '3px',
                  bottom: '3px',
                  background: 'white',
                  transition: '0.3s',
                  borderRadius: '50%'
                }}></span>
              </span>
            </label>
          </div>
        ))}
      </div>
    </div>
  )
}