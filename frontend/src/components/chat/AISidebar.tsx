'use client'

import { useState, useRef, useEffect } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import ReactMarkdown from 'react-markdown'
import { cn } from '@/lib/utils'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import {
  XMarkIcon,
  SparklesIcon,
  PaperAirplaneIcon,
  MicrophoneIcon,
  PaperClipIcon,
} from '@heroicons/react/24/outline'

interface Message {
  id: string
  role: 'user' | 'assistant'
  content: string
  timestamp: Date
}

interface AISidebarProps {
  isOpen: boolean
  onToggle: () => void
}

export function AISidebar({ isOpen, onToggle }: AISidebarProps) {
  const [messages, setMessages] = useState<Message[]>([
    {
      id: '1',
      role: 'assistant',
      content: `Hi! I'm your AI assistant for KOL management. I can help you with:

• **Find KOLs** - Search and filter influencers based on your criteria
• **Analyze Performance** - Get insights on engagement rates and ROI
• **Create Campaigns** - Generate campaign briefs and strategies
• **Generate Reports** - Export data and create performance summaries

What would you like to know about your KOLs today?`,
      timestamp: new Date(),
    },
  ])
  const [input, setInput] = useState('')
  const [isLoading, setIsLoading] = useState(false)
  const messagesEndRef = useRef<HTMLDivElement>(null)

  const quickActions = [
    {
      label: 'Find top KOLs',
      query: 'Show me KOLs with the highest engagement rates in beauty category',
      icon: '🎯',
    },
    {
      label: 'Campaign ideas',
      query: 'Generate campaign ideas for promoting a new skincare product',
      icon: '💡',
    },
    {
      label: 'Performance analysis',
      query: 'Analyze the performance of my top 5 KOLs this month',
      icon: '📊',
    },
    {
      label: 'Export report',
      query: 'Create a performance report for all active campaigns',
      icon: '📄',
    },
  ]

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }

  useEffect(() => {
    scrollToBottom()
  }, [messages])

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!input.trim() || isLoading) return

    const userMessage: Message = {
      id: Date.now().toString(),
      role: 'user',
      content: input,
      timestamp: new Date(),
    }

    setMessages((prev) => [...prev, userMessage])
    setInput('')
    setIsLoading(true)

    // Simulate AI response (replace with actual API call)
    setTimeout(() => {
      const aiResponse: Message = {
        id: (Date.now() + 1).toString(),
        role: 'assistant',
        content: getAIResponse(input),
        timestamp: new Date(),
      }
      setMessages((prev) => [...prev, aiResponse])
      setIsLoading(false)
    }, 1000 + Math.random() * 2000)
  }

  const handleQuickAction = (query: string) => {
    setInput(query)
  }

  // Mock AI response generator
  const getAIResponse = (query: string): string => {
    const lowerQuery = query.toLowerCase()

    if (lowerQuery.includes('kol') || lowerQuery.includes('influencer')) {
      return `Based on your current KOL database, here are some insights:

**Top Performing KOLs:**
- Sarah Johnson (@sarahjstyle) - 850K followers, 4.2% engagement
- Mike Chen (@mikechentech) - 1.2M followers, 5.5% engagement

**Recommendations:**
- Focus on micro-influencers (10K-100K) for better engagement rates
- Beauty category shows 20% higher ROI than tech
- Video content performs 3x better than static posts

Would you like me to dive deeper into any specific metrics?`
    }

    if (lowerQuery.includes('campaign')) {
      return `Here are some campaign strategy suggestions:

**Campaign Ideas:**
1. **Seasonal Beauty Challenge** - Partner with 5-10 beauty KOLs for a 30-day skincare routine
2. **Tech Review Series** - Collaborate with tech reviewers for product launches
3. **Lifestyle Integration** - Work with lifestyle influencers to show product in daily routines

**Best Practices:**
- Set clear KPIs: reach, engagement, conversions
- Provide creative freedom while maintaining brand guidelines
- Track performance with UTM codes and affiliate links

Would you like me to create a detailed brief for any of these campaigns?`
    }

    if (lowerQuery.includes('performance') || lowerQuery.includes('analytic')) {
      return `Here's your performance summary:

**This Month's Metrics:**
- Total Reach: 2.3M impressions (+15% vs last month)
- Engagement Rate: 4.8% average across all KOLs
- Campaign ROI: 3.2x return on investment
- Top Platform: Instagram (65% of engagement)

**Key Insights:**
- Video content generates 40% more engagement
- Posts with user-generated content perform 25% better
- Optimal posting time: 7-9 PM on weekdays

**Action Items:**
- Increase video content allocation
- Encourage more UGC in campaigns
- Optimize posting schedules

Need a detailed breakdown for any specific KOL or campaign?`
    }

    if (lowerQuery.includes('report') || lowerQuery.includes('export')) {
      return `I can generate several types of reports for you:

**Available Reports:**
- **KOL Performance Report** - Individual influencer metrics and ROI
- **Campaign Summary** - Complete campaign analytics with visuals
- **Monthly Overview** - Aggregated performance across all activities
- **Competitive Analysis** - Benchmarking against industry standards

**Export Formats:**
- PDF (formatted reports)
- Excel (raw data + charts)
- CSV (data only)
- PowerPoint (presentation ready)

Which report would you like me to prepare? I can have it ready in a few minutes.`
    }

    return `I understand you're asking about "${query}".

I can help you with KOL management tasks including:
- Finding and analyzing influencers
- Creating campaign strategies
- Performance tracking and reporting
- ROI analysis and optimization

Could you be more specific about what you'd like to know? For example:
- "Show me KOLs in the fashion category"
- "Create a campaign brief for product launch"
- "Analyze performance of recent campaigns"`
  }

  const TypingIndicator = () => (
    <div className="flex items-center gap-1">
      <div className="flex gap-1">
        {[0, 1, 2].map((i) => (
          <motion.div
            key={i}
            className="w-2 h-2 bg-gray-400 rounded-full"
            animate={{ y: [-2, 2, -2] }}
            transition={{
              duration: 0.6,
              repeat: Infinity,
              delay: i * 0.1,
            }}
          />
        ))}
      </div>
      <span className="text-sm text-gray-500 ml-2">AI is thinking...</span>
    </div>
  )

  return (
    <AnimatePresence>
      {isOpen && (
        <>
          {/* Backdrop */}
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            className="fixed inset-0 bg-black/20 z-40 lg:hidden"
            onClick={onToggle}
          />

          {/* Sidebar */}
          <motion.div
            initial={{ x: '100%' }}
            animate={{ x: 0 }}
            exit={{ x: '100%' }}
            transition={{ type: 'spring', damping: 25, stiffness: 200 }}
            className="fixed right-0 top-0 h-full w-96 bg-white shadow-2xl z-50 flex flex-col border-l border-gray-200"
          >
            {/* Header */}
            <div className="p-4 border-b border-gray-200 flex items-center justify-between bg-gradient-to-r from-blue-50 to-purple-50">
              <div className="flex items-center gap-3">
                <div className="w-8 h-8 bg-gradient-to-r from-blue-500 to-purple-600 rounded-full flex items-center justify-center">
                  <SparklesIcon className="w-4 h-4 text-white" />
                </div>
                <div>
                  <h2 className="font-semibold text-gray-900">AI Assistant</h2>
                  <p className="text-xs text-gray-500">KOL Management Helper</p>
                </div>
              </div>
              <Button variant="ghost" size="sm" onClick={onToggle}>
                <XMarkIcon className="w-5 h-5" />
              </Button>
            </div>

            {/* Quick Actions */}
            <div className="p-4 border-b border-gray-100 bg-gray-50">
              <p className="text-sm font-medium text-gray-700 mb-3">Quick actions:</p>
              <div className="grid grid-cols-2 gap-2">
                {quickActions.map((action, index) => (
                  <motion.button
                    key={index}
                    onClick={() => handleQuickAction(action.query)}
                    className="p-3 text-left bg-white hover:bg-gray-50 rounded-lg border border-gray-200 transition-colors group"
                    whileHover={{ scale: 1.02 }}
                    whileTap={{ scale: 0.98 }}
                  >
                    <div className="flex items-center gap-2 mb-1">
                      <span className="text-sm">{action.icon}</span>
                      <span className="text-xs font-medium text-gray-900 group-hover:text-blue-600">
                        {action.label}
                      </span>
                    </div>
                  </motion.button>
                ))}
              </div>
            </div>

            {/* Messages */}
            <div className="flex-1 overflow-y-auto p-4 space-y-4">
              <AnimatePresence>
                {messages.map((message) => (
                  <motion.div
                    key={message.id}
                    initial={{ opacity: 0, y: 20 }}
                    animate={{ opacity: 1, y: 0 }}
                    exit={{ opacity: 0, y: -20 }}
                    className={cn(
                      'flex',
                      message.role === 'user' ? 'justify-end' : 'justify-start'
                    )}
                  >
                    <div
                      className={cn(
                        'max-w-[85%] rounded-lg px-4 py-3',
                        message.role === 'user'
                          ? 'bg-blue-500 text-white'
                          : 'bg-gray-100 text-gray-900'
                      )}
                    >
                      <ReactMarkdown className="prose prose-sm max-w-none prose-headings:mt-2 prose-headings:mb-1 prose-p:mb-2">
                        {message.content}
                      </ReactMarkdown>
                      <div className="text-xs opacity-70 mt-2">
                        {message.timestamp.toLocaleTimeString([], {
                          hour: '2-digit',
                          minute: '2-digit',
                        })}
                      </div>
                    </div>
                  </motion.div>
                ))}
              </AnimatePresence>

              {isLoading && (
                <motion.div
                  initial={{ opacity: 0 }}
                  animate={{ opacity: 1 }}
                  className="flex justify-start"
                >
                  <div className="bg-gray-100 rounded-lg px-4 py-3">
                    <TypingIndicator />
                  </div>
                </motion.div>
              )}

              <div ref={messagesEndRef} />
            </div>

            {/* Input */}
            <form onSubmit={handleSubmit} className="p-4 border-t border-gray-200 bg-white">
              <div className="flex gap-2 mb-2">
                <Button
                  type="button"
                  variant="ghost"
                  size="sm"
                  className="text-gray-500 hover:text-gray-700"
                >
                  <PaperClipIcon className="w-4 h-4" />
                </Button>
                <Button
                  type="button"
                  variant="ghost"
                  size="sm"
                  className="text-gray-500 hover:text-gray-700"
                >
                  <MicrophoneIcon className="w-4 h-4" />
                </Button>
              </div>
              <div className="flex gap-2">
                <Input
                  value={input}
                  onChange={(e) => setInput(e.target.value)}
                  placeholder="Ask me anything about your KOLs..."
                  className="flex-1 focus:ring-blue-500"
                  disabled={isLoading}
                />
                <Button
                  type="submit"
                  disabled={isLoading || !input.trim()}
                  className="gradient-primary hover:opacity-90"
                >
                  <PaperAirplaneIcon className="w-4 h-4" />
                </Button>
              </div>
              <p className="text-xs text-gray-500 mt-2">
                AI can make mistakes. Verify important information.
              </p>
            </form>
          </motion.div>
        </>
      )}
    </AnimatePresence>
  )
}