import type {BasicIdentityInput, VerificationSubmission, VerificationSummary,} from '@/types'

import {api, ApiError, resolveApi} from './api'
import {createMockId, nowIso} from './mock/helpers'
import {mockDb} from './mock/state'

export interface VerificationService {
    getSummary(): Promise<VerificationSummary>

    submitBasicInfo(input: BasicIdentityInput): Promise<VerificationSubmission>

    submitIdentityDocument(file: File): Promise<VerificationSubmission>
}

function createSubmission(
    stepId: 'basic_info' | 'identity',
): VerificationSubmission {
    const step = mockDb.verification.steps.find(
        (item) => item.id === stepId,
    )

    if (!step) {
        throw new ApiError(
            'مرحله احراز هویت پیدا نشد.',
            'NOT_FOUND',
            404,
        )
    }

    step.status = 'pending'
    delete step.rejectionReason

    return {
        id: createMockId('kyc'),
        stepId,
        status: 'pending',
        submittedAt: nowIso(),
    }
}

export const verificationService: VerificationService = {
    getSummary() {
        return resolveApi(
            () => mockDb.verification,
            () => api.get<VerificationSummary>('/verification'),
        )
    },

    submitBasicInfo(input) {
        return resolveApi(
            () => {
                const nationalId = input.nationalId.replace(/\D/g, '')

                if (
                    !input.firstName.trim()
                    || !input.lastName.trim()
                    || !/^\d{10}$/.test(nationalId)
                    || !input.birthDate.trim()
                ) {
                    throw new ApiError(
                        'اطلاعات هویتی را کامل و صحیح وارد کنید.',
                        'VALIDATION_ERROR',
                        422,
                    )
                }

                Object.assign(mockDb.user, input, {
                    fullName: `${input.firstName.trim()} ${input.lastName.trim()}`,
                })

                return {
                    ...createSubmission('basic_info'),
                    nextStep: 'identity',
                    message: 'اطلاعات هویتی با موفقیت ثبت شد.',
                }
            },
            () => api.post<VerificationSubmission>(
                '/verification/basic-info',
                {
                    ...input,
                    nationalId: input.nationalId.replace(/\D/g, ''),
                },
            ),
        )
    },

    submitIdentityDocument(file) {
        return resolveApi(
            () => ({
                ...createSubmission('identity'),
                reviewPending: true,
                message: 'اطلاعات شما برای بررسی ادمین ارسال شد.',
            }),
            () => {
                const payload = new FormData()
                payload.append('document', file)

                return api.post<VerificationSubmission>(
                    '/verification/identity',
                    payload,
                )
            },
        )
    },
}

export default verificationService