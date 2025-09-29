export interface User {
  id: string
  email: string
  name: string
  role: 'admin' | 'manager' | 'agent' | 'viewer'
  isActive: boolean
  createdAt: string
  lastLogin?: string
  twoFactorEnabled: boolean
}

export interface KOL {
  id: string
  name: string
  username: string
  email: string
  phone?: string
  avatar?: string
  contractStatus: 'active' | 'pending' | 'expired' | 'terminated'
  ratePerPost: number
  preferredCommunication: 'email' | 'discord' | 'line'
  createdAt: string
  updatedAt: string
  socialMediaAccounts: SocialMediaAccount[]
  location?: string
  bio?: string
}

export interface SocialMediaAccount {
  id: string
  kolId: string
  platform: 'instagram' | 'youtube' | 'tiktok' | 'twitter' | 'facebook'
  username: string
  platformUserId: string
  isVerified: boolean
  followersCount: number
  followingCount: number
  postsCount: number
  engagementRate: number
  lastSynced: string
}

export interface Campaign {
  id: string
  name: string
  description: string
  startDate: string
  endDate: string
  budget: number
  status: 'draft' | 'active' | 'paused' | 'completed' | 'cancelled'
  createdBy: string
  createdAt: string
  briefs: Brief[]
}

export interface Brief {
  id: string
  campaignId: string
  kolId: string
  title: string
  requirements: string
  deadline: string
  compensation: number
  status: 'draft' | 'sent' | 'accepted' | 'rejected' | 'completed'
  createdAt: string
}

export interface Content {
  id: string
  socialMediaAccountId: string
  platformPostId: string
  postType: 'post' | 'story' | 'video' | 'reel'
  contentText: string
  mediaUrls: string[]
  publishedAt: string
  likesCount: number
  commentsCount: number
  sharesCount: number
  viewsCount: number
  engagementRate: number
  sentimentScore: number
  brandSafetyScore: number
  complianceStatus: 'compliant' | 'non_compliant' | 'pending_review'
  analyzedAt: string
}

export interface TableState {
  globalFilter: string
  sorting: { id: string; desc: boolean }[]
  columnFilters: { id: string; value: any }[]
  rowSelection: Record<string, boolean>
  pagination: {
    pageIndex: number
    pageSize: number
  }
}

export interface ChatMessage {
  id: string
  role: 'user' | 'assistant'
  content: string
  timestamp: string
}