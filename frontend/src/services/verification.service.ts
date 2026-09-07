import type {
  BasicIdentityInput,
  VerificationStepId,
  VerificationSubmission,
  VerificationSummary,
} from '@/types'
import { ApiError, api, resolveApi } from './api'
import { createMockId, nowIso } from './mock/helpers'
import { mockDb } from './mock/state'

export interface VerificationService {
  getSummary(): Promise<VerificationSummary>
  submitBasicInfo(input: BasicIdentityInput): Promise<VerificationSubmission>
  submitStep(stepId: VerificationStepId, payload: FormData | Record<string, unknown>): Promise<VerificationSubmission>
}

function createSubmission(stepId: VerificationStepId): VerificationSubmission {
  const step = mockDb.verification.steps.find((item) => item.id === stepId)
  if (!step) throw new ApiError('مرحله احراز هویت پیدا نشد.', 'NOT_FOUND', 404)
  step.status = 'pending'
  delete step.rejectionReason
  mockDb.verification.status = 'pending'
  mockDb.user.kycStatus = 'pending'
  return {
    id: createMockId('kyc'),
    stepId,
    status: 'pending',
    submittedAt: nowIso(),
  }
}

export const verificationService: VerificationService = {
  getSummary() {
    return resolveApi(() => mockDb.verification, () => api.get<VerificationSummary>('/verification'))
  },

  submitBasicInfo(input) {
    return resolveApi(() => {
      if (!input.firstName.trim() || !input.lastName.trim() || !/^\d{10}$/.test(input.nationalId)) {
        throw new ApiError('اطلاعات هویتی را کامل و صحیح وارد کنید.', 'VALIDATION_ERROR', 422)
      }
      Object.assign(mockDb.user, input, {
        fullName: `${input.firstName.trim()} ${input.lastName.trim()}`,
      })
      return createSubmission('basic_info')
    }, () => api.post<VerificationSubmission>('/verification/basic-info', input))
  },

  submitStep(stepId, payload) {
    return resolveApi(() => createSubmission(stepId), () =>
      api.post<VerificationSubmission>(`/verification/${stepId}`, payload))
  },
}

export default verificationService
