import { mockOrders, mockTransactions } from '../mock/data'

export const ordersService = {
  async getOrders() { return { data: mockOrders } },
  async getTransactions() { return { data: mockTransactions } },
  async createOrder(payload) { return { data: { success: true, order: payload } } },
}

export default ordersService
