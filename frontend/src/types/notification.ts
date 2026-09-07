import type { ActionLink, ISODateString, PaginationParams } from './common'

export type NotificationCategory =
  | 'order'
  | 'deposit'
  | 'withdrawal'
  | 'verification'
  | 'security'
  | 'support'
  | 'system'

export interface NotificationItem {
  id: string
  category: NotificationCategory
  title: string
  message: string
  read: boolean
  createdAt: ISODateString
  action?: ActionLink
}

export interface NotificationFilters extends PaginationParams {
  category?: NotificationCategory
  read?: boolean
}

