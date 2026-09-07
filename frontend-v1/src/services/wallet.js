import { mockWallets } from '../mock/data'

export const walletService = {
  async getWallets() { return { data: mockWallets } },
  async getWalletById(id) { return { data: mockWallets.find((wallet) => wallet.id === id) } },
  async deposit(payload) { return { data: { success: true, payload } } },
  async withdraw(payload) { return { data: { success: true, payload } } },
}

export default walletService
