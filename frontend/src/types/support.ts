import type { ISODateString, PaginationParams } from './common'

export type SupportCategory =
  | 'trade'
  | 'deposit'
  | 'withdrawal'
  | 'verification'
  | 'bank'
  | 'security'
  | 'technical'
  | 'other'

export type TicketStatus = 'open' | 'waiting_for_user' | 'answered' | 'closed'
export type TicketPriority = 'normal' | 'high'

export interface FaqItem {
  id: string
  category: SupportCategory
  question: string
  answer: string
  tags: string[]
}

export interface TicketMessage {
  id: string
  sender: 'user' | 'support'
  senderName: string
  body: string
  createdAt: ISODateString
  attachments?: Array<{ name: string; url: string }>
}

export interface SupportTicket {
  id: string
  ticketNumber: string
  subject: string
  category: SupportCategory
  priority: TicketPriority
  status: TicketStatus
  orderId?: string
  createdAt: ISODateString
  updatedAt: ISODateString
  messages: TicketMessage[]
}

export interface TicketFilters extends PaginationParams {
  status?: TicketStatus
  category?: SupportCategory
  search?: string
}

export interface CreateTicketInput {
  subject: string
  category: SupportCategory
  body: string
  orderId?: string
}

