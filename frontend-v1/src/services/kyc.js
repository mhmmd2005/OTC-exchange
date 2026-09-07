import { isMockMode, isRealMode } from './mode'
import { realKycService } from './realKyc'
import { mockKycService } from './mockKyc'

function getService() {
  return isMockMode() ? mockKycService : realKycService
}

export const kycService = {
  async get() {
    return getService().get()
  },

  async submit(data) {
    return getService().submit(data)
  },

  async update(data) {
    return getService().update(data)
  },

  async status() {
    return getService().status()
  },
}

export default kycService
