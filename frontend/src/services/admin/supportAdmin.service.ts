import { adminApi } from './adminApi'

export type AdminTicketStatus =
    | 'open'
    | 'pending'
    | 'resolved'
    | 'closed'

export type AdminTicketCategory =
    | 'trade'
    | 'deposit'
    | 'withdrawal'
    | 'verification'
    | 'bank'
    | 'security'
    | 'technical'
    | 'other'

export type AdminTicketPriority =
    | 'low'
    | 'medium'
    | 'high'
    | 'urgent'

export interface AdminTicketMessage {
    id: number
    sender: 'user' | 'support'
    senderName: string
    body: string
    createdAt: string
}

export interface AdminTicket {
    id: number
    ticketNumber: string
    subject: string
    category: AdminTicketCategory
    status: AdminTicketStatus
    priority: AdminTicketPriority
    userName: string
    userPhone: string
    userEmail: string | null
    createdAt: string
    updatedAt: string
    messageCount: number
    messages?: AdminTicketMessage[]
}

export interface AdminTicketFilters {
    page?: number
    pageSize?: number
    search?: string
    status?: AdminTicketStatus | ''
    category?: AdminTicketCategory | ''
    priority?: AdminTicketPriority | ''
}

export interface AdminTicketListResponse {
    items: AdminTicket[]
    total: number
    page: number
    pageSize: number
}

function buildQuery(
    filters: AdminTicketFilters = {},
): string {
    const params = new URLSearchParams()

    params.set('page', String(filters.page ?? 1))
    params.set('pageSize', String(filters.pageSize ?? 20))

    if (filters.search?.trim()) {
        params.set('search', filters.search.trim())
    }

    if (filters.status) {
        params.set('status', filters.status)
    }

    if (filters.category) {
        params.set('category', filters.category)
    }

    if (filters.priority) {
        params.set('priority', filters.priority)
    }

    return params.toString()
}

const basePath = '/admin/support/tickets/'

export const supportAdminService = {
    list(filters: AdminTicketFilters = {}) {
        return adminApi.get<AdminTicketListResponse>(
            `${basePath}?${buildQuery(filters)}`,
        )
    },

    get(id: number) {
        return adminApi.get<AdminTicket>(
            `${basePath}${id}/`,
        )
    },

    reply(id: number, body: string) {
        return adminApi.post<AdminTicket>(
            `${basePath}${id}/reply/`,
            { body },
        )
    },

    updateStatus(
        id: number,
        ticketStatus: AdminTicketStatus,
    ) {
        return adminApi.patch<AdminTicket>(
            `${basePath}${id}/status/`,
            { status: ticketStatus },
        )
    },
}

export default supportAdminService