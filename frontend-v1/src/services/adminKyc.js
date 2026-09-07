import { isMockMode } from './mode'
import { mockAdminKycService } from './mockAdminKyc'
import { realAdminKycService } from './realAdminKyc'

function getService() {
  return isMockMode() ? mockAdminKycService : realAdminKycService
}

export const adminKycService = {
  async get() {
    return getService().get()
  },

  async getPending() {
    return getService().getPending()
  },

  async getById(id) {
    return getService().getById(id)
  },

  async approve(id) {
    return getService().approve(id)
  },

  async reject(id, reason) {
    return getService().reject(id, reason)
  },
}

export default adminKycService
