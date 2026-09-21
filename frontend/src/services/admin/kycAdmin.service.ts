import {adminApi} from '@/services/admin/adminApi'

export interface AdminBankAccount {
    id: string
    bank?: {
        id?: number
        nameFa?: string
        nameEn?: string
        cardPrefixes?: string[]
        color?: string
        logoUrl?: string
    } | null
    ownerName: string
    cardNumber: string
    iban: string
    accountNumber?: string
    status: string
    preferred: boolean
    rejectionReason?: string | null
    createdAt?: string
    verifiedAt?: string | null
    isUsable?: boolean
}

export interface AdminKycApplication {
    id: number
    firstName: string
    lastName: string
    nationalId: string
    birthDate: string
    phoneNumber: string
    email?: string
    identityDocument?: string | null

    status: string
    statusLabel?: string

    basicInfoStatus: string
    basicInfoSubmittedAt?: string | null
    basicInfoReviewedAt?: string | null
    basicInfoReviewedBy?: string | null
    basicInfoRejectionReason?: string | null
    canEditBasicInfo?: boolean

    identityStatus: string
    identitySubmittedAt?: string | null
    identityReviewedAt?: string | null
    identityReviewedBy?: string | null
    identityRejectionReason?: string | null
    canEditIdentity?: boolean

    rejectionReason?: string | null
    submittedAt?: string | null
    reviewedAt?: string | null

    bankAccounts: AdminBankAccount[]

    createdAt: string
    updatedAt: string
}

function mapBankAccount(
    data: any,
): AdminBankAccount {
    return {
        id: String(data.id),

        bank: data.bank
            ? {
                id:
                    data.bank.id !== undefined
                        ? Number(data.bank.id)
                        : undefined,

                nameFa:
                    data.bank.nameFa ?? '',

                nameEn:
                    data.bank.nameEn ?? '',

                cardPrefixes:
                    data.bank.cardPrefixes ?? [],

                color:
                    data.bank.color ?? '',

                logoUrl:
                    data.bank.logoUrl ?? '',
            }
            : null,

        ownerName:
            data.ownerName ?? '',

        cardNumber:
            data.cardNumber ?? '',

        iban:
            data.iban ?? '',

        accountNumber:
            data.accountNumber ?? '',

        status:
            data.status ?? 'pending',

        preferred:
            Boolean(data.preferred),

        rejectionReason:
            data.rejectionReason ?? null,

        createdAt:
            data.createdAt ?? null,

        verifiedAt:
            data.verifiedAt ?? null,

        isUsable:
            Boolean(data.isUsable),
    }
}

function mapApplication(
    data: any,
): AdminKycApplication {
    return {
        id:
            Number(data.id),

        firstName:
            data.first_name ?? '',

        lastName:
            data.last_name ?? '',

        nationalId:
            data.national_id ?? '',

        birthDate:
            data.birth_date ?? '',

        phoneNumber:
            data.phone_number ?? '',

        email:
            data.email ?? '',

        identityDocument:
            data.identity_document ?? null,

        status:
            data.status ?? 'not_started',

        statusLabel:
            data.status_label ?? '',

        basicInfoStatus:
            data.basic_info_status ?? 'not_started',

        basicInfoSubmittedAt:
            data.basic_info_submitted_at ?? null,

        basicInfoReviewedAt:
            data.basic_info_reviewed_at ?? null,

        basicInfoReviewedBy:
            data.basic_info_reviewed_by ?? null,

        basicInfoRejectionReason:
            data.basic_info_rejection_reason ?? null,

        canEditBasicInfo:
            data.can_edit_basic_info ?? false,

        identityStatus:
            data.identity_status ?? 'not_started',

        identitySubmittedAt:
            data.identity_submitted_at ?? null,

        identityReviewedAt:
            data.identity_reviewed_at ?? null,

        identityReviewedBy:
            data.identity_reviewed_by ?? null,

        identityRejectionReason:
            data.identity_rejection_reason ?? null,

        canEditIdentity:
            data.can_edit_identity ?? false,

        rejectionReason:
            data.rejection_reason ?? null,

        submittedAt:
            data.submitted_at ?? null,

        reviewedAt:
            data.reviewed_at ?? null,

        bankAccounts:
            Array.isArray(data.bank_accounts)
                ? data.bank_accounts.map(
                    mapBankAccount,
                )
                : [],

        createdAt:
            data.created_at ?? '',

        updatedAt:
            data.updated_at ?? '',
    }
}

export const kycAdminService = {
    async list(): Promise<AdminKycApplication[]> {
        const data =
            await adminApi.get<unknown>(
                '/admin/kyc/',
            )

        const items =
            Array.isArray(data)
                ? data
                : Array.isArray(
                    (
                        data as {
                            results?: unknown[]
                        }
                    )?.results,
                )
                    ? (
                        data as {
                            results: unknown[]
                        }
                    ).results
                    : []

        return items.map(
            mapApplication,
        )
    },

    async detail(
        id: number,
    ): Promise<AdminKycApplication> {
        const data =
            await adminApi.get<
                Record<string, unknown>
            >(
                `/admin/kyc/${id}/`,
            )

        return mapApplication(data)
    },

    async approveBasicInfo(
        id: number,
    ): Promise<void> {
        await adminApi.post(
            `/admin/kyc/${id}/approve/basic-info/`,
        )
    },

    async rejectBasicInfo(
        id: number,
        reason: string,
    ): Promise<void> {
        await adminApi.post(
            `/admin/kyc/${id}/reject/basic-info/`,
            {
                reason,
            },
        )
    },

    async approveIdentity(
        id: number,
    ): Promise<void> {
        await adminApi.post(
            `/admin/kyc/${id}/approve/identity/`,
        )
    },

    async rejectIdentity(
        id: number,
        reason: string,
    ): Promise<void> {
        await adminApi.post(
            `/admin/kyc/${id}/reject/identity/`,
            {
                reason,
            },
        )
    },

    async approveBank(
        kycId: number,
        bankId: string,
    ): Promise<void> {
        await adminApi.post(
            `/admin/kyc/${kycId}/approve/bank/${bankId}/`,
        )
    },

    async rejectBank(
        kycId: number,
        bankId: string,
        reason: string,
    ): Promise<void> {
        await adminApi.post(
            `/admin/kyc/${kycId}/reject/bank/${bankId}/`,
            {
                reason,
            },
        )
    },

    async remove(
        id: number,
    ): Promise<void> {
        await adminApi.delete(
            `/admin/kyc/${id}/`,
        )
    },
}

export default kycAdminService