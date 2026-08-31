import { mockTransactions } from '../mock/data'

export const transactionsService = {
  async getTransactions() {
    return { data: mockTransactions }
  },
  async createTransaction(payload) {
    return { data: { success: true, payload } }
  },
}

export default transactionsService
