import type {
  CreateTicketInput,
  FaqItem,
  PaginatedResult,
  SupportCategory,
  SupportTicket,
  TicketFilters,
  TicketMessage,
} from '@/types'
import { ApiError, api, resolveApi } from './api'
import { mockFaqs } from './mock/data'
import { createMockId, normalizedSearch, nowIso, paginate } from './mock/helpers'
import { mockDb } from './mock/state'

export interface SupportService {
  listFaqs(search?: string, category?: SupportCategory): Promise<FaqItem[]>
  listTickets(filters?: TicketFilters): Promise<PaginatedResult<SupportTicket>>
  getTicket(id: string): Promise<SupportTicket>
  createTicket(input: CreateTicketInput): Promise<SupportTicket>
  reply(ticketId: string, body: string): Promise<TicketMessage>
  close(ticketId: string): Promise<SupportTicket>
}

function findTicket(id: string): SupportTicket {
  const ticket = mockDb.tickets.find((item) => item.id === id || item.ticketNumber === id)
  if (!ticket) throw new ApiError('درخواست پشتیبانی پیدا نشد.', 'NOT_FOUND', 404)
  return ticket
}

export const supportService: SupportService = {
  listFaqs(search, category) {
    return resolveApi(() => {
      const query = normalizedSearch(search)
      return mockFaqs.filter((item) => {
        const matchesCategory = !category || item.category === category
        const matchesSearch = !query || item.question.includes(query) || item.answer.includes(query)
          || item.tags.some((tag) => tag.includes(query))
        return matchesCategory && matchesSearch
      })
    }, () => api.get<FaqItem[]>('/support/faqs', { query: { search, category } }))
  },

  listTickets(filters = {}) {
    return resolveApi(() => {
      const query = normalizedSearch(filters.search)
      const filtered = mockDb.tickets.filter((ticket) =>
        (!filters.status || ticket.status === filters.status)
        && (!filters.category || ticket.category === filters.category)
        && (!query || ticket.subject.includes(query) || ticket.ticketNumber.toLowerCase().includes(query)))
      return paginate(filtered, filters)
    }, () => api.get<PaginatedResult<SupportTicket>>('/support/tickets', {
      query: {
        page: filters.page,
        pageSize: filters.pageSize,
        status: filters.status,
        category: filters.category,
        search: filters.search,
      },
    }))
  },

  getTicket(id) {
    return resolveApi(() => findTicket(id), () => api.get<SupportTicket>(`/support/tickets/${id}`))
  },

  createTicket(input) {
    return resolveApi(() => {
      if (input.subject.trim().length < 5 || input.body.trim().length < 10) {
        throw new ApiError('موضوع و توضیحات درخواست را کامل‌تر بنویسید.', 'VALIDATION_ERROR', 422)
      }
      const createdAt = nowIso()
      const ticket: SupportTicket = {
        id: createMockId('tkt'),
        ticketNumber: `TK-${Date.now().toString().slice(-5)}`,
        subject: input.subject.trim(),
        category: input.category,
        priority: 'normal',
        status: 'open',
        orderId: input.orderId,
        createdAt,
        updatedAt: createdAt,
        messages: [{
          id: createMockId('msg'),
          sender: 'user',
          senderName: mockDb.user.fullName,
          body: input.body.trim(),
          createdAt,
        }],
      }
      mockDb.tickets.unshift(ticket)
      return ticket
    }, () => api.post<SupportTicket>('/support/tickets', input))
  },

  reply(ticketId, body) {
    return resolveApi(() => {
      const ticket = findTicket(ticketId)
      if (ticket.status === 'closed') {
        throw new ApiError('این درخواست بسته شده است. یک درخواست جدید ثبت کنید.', 'BAD_REQUEST', 409)
      }
      if (body.trim().length < 2) {
        throw new ApiError('متن پیام را وارد کنید.', 'VALIDATION_ERROR', 422)
      }
      const message: TicketMessage = {
        id: createMockId('msg'),
        sender: 'user',
        senderName: mockDb.user.fullName,
        body: body.trim(),
        createdAt: nowIso(),
      }
      ticket.messages.push(message)
      ticket.updatedAt = message.createdAt
      ticket.status = 'open'
      return message
    }, () => api.post<TicketMessage>(`/support/tickets/${ticketId}/messages`, { body }))
  },

  close(ticketId) {
    return resolveApi(() => {
      const ticket = findTicket(ticketId)
      ticket.status = 'closed'
      ticket.updatedAt = nowIso()
      return ticket
    }, () => api.post<SupportTicket>(`/support/tickets/${ticketId}/close`))
  },
}

export default supportService

