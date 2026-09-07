import { mockTickets } from '../mock/data'

export const supportService = {
  async listTickets() {
    return { data: mockTickets }
  },
  async createTicket(payload) {
    return { data: { success: true, ticket: payload } }
  },
}

export default supportService
