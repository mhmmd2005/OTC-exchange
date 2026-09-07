import api from './api'

export const realAdminKycService = {
  async get() {
    return api.get('/kyc/admin/')
  },

  async getPending() {
    return api.get('/kyc/admin/?status=pending')
  },

  async getById(id) {
    return api.get(`/kyc/admin/${id}/`)
  },

  async approve(id) {
    return api.post(`/kyc/admin/${id}/approve/`)
  },

  async reject(id, reason) {
    return api.post(`/kyc/admin/${id}/reject/`, { reason })
  },
}

export default realAdminKycService
