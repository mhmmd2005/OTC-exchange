import { mockKyc } from '../mock/data'

export const kycService = {
  async getKycStatus() { return { data: mockKyc } },
  async submitKyc(payload) { return { data: { success: true, payload } } },
}

export default kycService
