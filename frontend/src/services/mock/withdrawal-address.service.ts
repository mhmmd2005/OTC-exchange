import type {
    WithdrawalAddress,
    WithdrawalAddressConfirmation,
    WithdrawalAddressConfirmInput,
    WithdrawalAddressCreateInput,
    WithdrawalAddressCreateResponse,
} from '@/types'
import {createMockId, futureIso, nowIso} from './helpers'
import {mockDb} from './state'
import {ApiError} from '../api'

const DEV_OTP = '123456'
const MOCK_COOLDOWN_SECONDS = 60
const MOCK_CONFIRMATION_SECONDS = 120
const MOCK_RESEND_SECONDS = 60

interface MockConfirmationState {
    addressId: string
    confirmation: WithdrawalAddressConfirmation
    otp: string
    expiresAt: number
    resendAvailableAt: number
}

const confirmationState =
    new Map<string, MockConfirmationState>()

function normalizeAddress(
    address: string,
): string {
    const value =
        String(address || '').trim()

    if (value.startsWith('0x')) {
        return `0x${value.slice(2).toLowerCase()}`
    }

    if (
        value
            .toLowerCase()
            .startsWith('bc1')
    ) {
        return value.toLowerCase()
    }

    return value
}

function findNetwork(
    asset: string,
    networkCode: string,
) {
    const walletAsset =
        mockDb.wallet.assets.find(
            (item) =>
                item.symbol.toUpperCase() ===
                asset.toUpperCase(),
        )

    if (!walletAsset) {
        throw new ApiError(
            'ارز مورد نظر پیدا نشد.',
            'NOT_FOUND',
            404,
        )
    }

    const network =
        walletAsset.networks.find(
            (item) =>
                item.code.toUpperCase() ===
                networkCode.toUpperCase(),
        )

    if (!network) {
        throw new ApiError(
            'شبکه انتخاب‌شده برای این ارز معتبر نیست.',
            'VALIDATION_ERROR',
            422,
            {
                fields: {
                    network:
                        'شبکه انتخاب‌شده برای این ارز معتبر نیست.',
                },
            },
        )
    }

    if (!walletAsset.withdrawalEnabled) {
        throw new ApiError(
            'برداشت این ارز در حال حاضر فعال نیست.',
            'ASSET_DISABLED',
            422,
        )
    }

    if (!network.withdrawalEnabled) {
        throw new ApiError(
            'برداشت روی این شبکه در حال حاضر فعال نیست.',
            'NETWORK_DISABLED',
            422,
        )
    }

    if (
        network.status === 'disabled' ||
        network.status === 'maintenance'
    ) {
        throw new ApiError(
            'این شبکه در حال حاضر در دسترس نیست.',
            'NETWORK_DISABLED',
            422,
        )
    }

    return network
}

function validateAddress(
    address: string,
    network: {
        code: string
        addressRegex?: string
    },
): void {
    if (!address) {
        throw new ApiError(
            'آدرس برداشت را وارد کنید.',
            'VALIDATION_ERROR',
            422,
            {
                fields: {
                    address:
                        'آدرس برداشت را وارد کنید.',
                },
            },
        )
    }

    if (/\s/.test(address)) {
        throw new ApiError(
            'آدرس برداشت نباید فاصله داشته باشد.',
            'VALIDATION_ERROR',
            422,
            {
                fields: {
                    address:
                        'آدرس برداشت نباید فاصله داشته باشد.',
                },
            },
        )
    }

    if (network.addressRegex) {
        let pattern: RegExp

        try {
            pattern = new RegExp(
                `^(?:${network.addressRegex})$`,
            )
        } catch {
            throw new ApiError(
                `الگوی اعتبارسنجی شبکه ${network.code} نامعتبر است.`,
                'SERVER_ERROR',
                500,
            )
        }

        if (!pattern.test(address)) {
            throw new ApiError(
                'ساختار آدرس با شبکه انتخاب‌شده سازگار نیست.',
                'VALIDATION_ERROR',
                422,
                {
                    fields: {
                        address:
                            'ساختار آدرس با شبکه انتخاب‌شده سازگار نیست.',
                    },
                },
            )
        }

        return
    }

    if (address.length < 12) {
        throw new ApiError(
            'طول آدرس معتبر نیست.',
            'VALIDATION_ERROR',
            422,
            {
                fields: {
                    address:
                        'طول آدرس معتبر نیست.',
                },
            },
        )
    }
}

function activateDueAddresses(): void {
    const now = Date.now()

    for (
        const item of
        mockDb.withdrawalAddresses
    ) {
        if (
            item.status === 'cooling_down' &&
            item.cooldownUntil &&
            Date.parse(
                item.cooldownUntil,
            ) <= now
        ) {
            item.status = 'active'
            item.activatedAt = nowIso()
            item.cooldownUntil = null
            item.updatedAt = nowIso()
        }
    }
}

function createConfirmation(
    addressId: string,
): WithdrawalAddressConfirmation {
    return {
        challengeId: String(
            100000000 +
            Math.floor(
                Math.random() *
                900000000,
            ),
        ),
        expiresIn:
            MOCK_CONFIRMATION_SECONDS,
        resendAvailableIn:
            MOCK_RESEND_SECONDS,
        destinationHint:
            '0912***1234',
    }
}

function ensureConfirmationState(
    id: string,
): MockConfirmationState {
    const state =
        confirmationState.get(id)

    if (!state) {
        throw new ApiError(
            'درخواست تأیید آدرس معتبر نیست.',
            'BAD_REQUEST',
            422,
        )
    }

    if (
        state.expiresAt <=
        Date.now()
    ) {
        confirmationState.delete(id)

        throw new ApiError(
            'مهلت کد تأیید تمام شده است.',
            'VALIDATION_ERROR',
            422,
            {
                fields: {
                    otp:
                        'مهلت کد تأیید تمام شده است.',
                },
            },
        )
    }

    return state
}

export const mockWithdrawalAddressService = {
    list(): WithdrawalAddress[] {
        activateDueAddresses()

        return mockDb.withdrawalAddresses
    },

    create(
        input: WithdrawalAddressCreateInput,
    ): WithdrawalAddressCreateResponse {
        const asset =
            String(
                input.asset || '',
            )
                .trim()
                .toUpperCase()

        const networkCode =
            String(
                input.network || '',
            )
                .trim()
                .toUpperCase()

        const address =
            String(
                input.address || '',
            ).trim()

        const memo =
            String(
                input.memo || '',
            ).trim()

        const label =
            String(
                input.label || '',
            ).trim()

        const network =
            findNetwork(
                asset,
                networkCode,
            )

        if (
            network.memoRequired &&
            !memo
        ) {
            throw new ApiError(
                'برای این شبکه وارد کردن ممو یا تگ الزامی است.',
                'VALIDATION_ERROR',
                422,
                {
                    fields: {
                        memo:
                            'برای این شبکه وارد کردن ممو یا تگ الزامی است.',
                    },
                },
            )
        }

        validateAddress(
            address,
            network,
        )

        const normalizedAddress =
            normalizeAddress(address)

        const duplicate =
            mockDb.withdrawalAddresses.find(
                (item) =>
                    item.assetSymbol
                        .toUpperCase() ===
                        asset &&
                    item.networkCode
                        .toUpperCase() ===
                        networkCode &&
                    normalizeAddress(
                        item.address,
                    ) ===
                        normalizedAddress &&
                    item.memo === memo,
            )

        if (duplicate) {
            throw new ApiError(
                'این آدرس قبلاً در فهرست شما ثبت شده است.',
                'BAD_REQUEST',
                409,
                {
                    fields: {
                        address:
                            'این آدرس قبلاً ثبت شده است.',
                    },
                },
            )
        }

        const now = nowIso()

        const sourceAsset =
            mockDb.wallet.assets.find(
                (item) =>
                    item.symbol
                        .toUpperCase() ===
                    asset,
            )

        const created: WithdrawalAddress =
            {
                id: createMockId(
                    'waddr',
                ),
                assetSymbol: asset,
                assetNameFa:
                    sourceAsset?.nameFa ||
                    asset,
                assetNameEn:
                    sourceAsset?.nameEn ||
                    asset,
                networkCode,
                networkName:
                    network.name,
                networkDisplayName:
                    network.displayName,
                address,
                memo,
                label,
                status:
                    'pending_confirmation',
                verificationMethod:
                    'security_confirmation',
                isDefault: false,
                confirmationRequestedAt:
                    now,
                confirmedAt: null,
                cooldownUntil: null,
                activatedAt: null,
                lastUsedAt: null,
                revokedAt: null,
                blockedReason: '',
                createdAt: now,
                updatedAt: now,
            }

        mockDb.withdrawalAddresses.unshift(
            created,
        )

        const confirmation =
            createConfirmation(
                created.id,
            )

        confirmationState.set(
            created.id,
            {
                addressId: created.id,
                confirmation,
                otp: DEV_OTP,
                expiresAt:
                    Date.now() +
                    MOCK_CONFIRMATION_SECONDS *
                    1000,
                resendAvailableAt:
                    Date.now() +
                    MOCK_RESEND_SECONDS *
                    1000,
            },
        )

        return {
            address: created,
            confirmation,
        }
    },

    confirm(
        id: string,
        input: WithdrawalAddressConfirmInput,
    ): WithdrawalAddress {
        activateDueAddresses()

        const address =
            mockDb.withdrawalAddresses.find(
                (item) =>
                    item.id === id,
            )

        if (!address) {
            throw new ApiError(
                'آدرس برداشت پیدا نشد.',
                'NOT_FOUND',
                404,
            )
        }

        if (
            address.status !==
            'pending_confirmation'
        ) {
            throw new ApiError(
                'این آدرس در وضعیت قابل تأیید نیست.',
                'BAD_REQUEST',
                409,
            )
        }

        const state =
            ensureConfirmationState(id)

        if (
            state.confirmation.challengeId !==
            input.challengeId
        ) {
            throw new ApiError(
                'کد تأیید به این آدرس برداشت تعلق ندارد.',
                'VALIDATION_ERROR',
                422,
            )
        }

        if (input.otp !== DEV_OTP) {
            throw new ApiError(
                'کد تأیید صحیح نیست.',
                'VALIDATION_ERROR',
                422,
                {
                    fields: {
                        otp:
                            'کد تأیید صحیح نیست.',
                    },
                },
            )
        }

        if (
            input.twoFactorCode &&
            input.twoFactorCode !==
                DEV_OTP
        ) {
            throw new ApiError(
                'کد Authenticator صحیح نیست.',
                'VALIDATION_ERROR',
                422,
                {
                    fields: {
                        twoFactorCode:
                            'کد Authenticator صحیح نیست.',
                    },
                },
            )
        }

        const network =
            findNetwork(
                address.assetSymbol,
                address.networkCode,
            )

        validateAddress(
            address.address,
            network,
        )

        if (
            normalizeAddress(
                address.address,
            ) !==
            normalizeAddress(
                address.address,
            )
        ) {
            throw new ApiError(
                'اطلاعات آدرس برداشت با وضعیت فعلی شبکه سازگار نیست.',
                'VALIDATION_ERROR',
                422,
            )
        }

        const now = nowIso()

        address.confirmedAt = now
        address.status =
            'cooling_down'
        address.cooldownUntil =
            futureIso(
                MOCK_COOLDOWN_SECONDS,
            )
        address.activatedAt = null
        address.revokedAt = null
        address.blockedReason = ''
        address.updatedAt = now

        confirmationState.delete(id)

        return address
    },

    resendConfirmation(
        id: string,
    ): WithdrawalAddressCreateResponse {
        const address =
            mockDb.withdrawalAddresses.find(
                (item) =>
                    item.id === id,
            )

        if (!address) {
            throw new ApiError(
                'آدرس برداشت پیدا نشد.',
                'NOT_FOUND',
                404,
            )
        }

        if (
            address.status !==
            'pending_confirmation'
        ) {
            throw new ApiError(
                'این آدرس در وضعیت قابل تأیید نیست.',
                'BAD_REQUEST',
                409,
            )
        }

        const existing =
            confirmationState.get(id)

        if (
            existing &&
            existing.resendAvailableAt >
                Date.now()
        ) {
            throw new ApiError(
                'هنوز امکان ارسال مجدد کد وجود ندارد.',
                'RATE_LIMITED',
                429,
            )
        }

        const confirmation =
            createConfirmation(id)

        confirmationState.set(
            id,
            {
                addressId: id,
                confirmation,
                otp: DEV_OTP,
                expiresAt:
                    Date.now() +
                    MOCK_CONFIRMATION_SECONDS *
                    1000,
                resendAvailableAt:
                    Date.now() +
                    MOCK_RESEND_SECONDS *
                    1000,
            },
        )

        address.confirmationRequestedAt =
            nowIso()

        address.updatedAt =
            nowIso()

        return {
            address,
            confirmation,
        }
    },

    remove(id: string): void {
        const index =
            mockDb.withdrawalAddresses.findIndex(
                (item) =>
                    item.id === id,
            )

        if (index === -1) {
            throw new ApiError(
                'آدرس برداشت پیدا نشد.',
                'NOT_FOUND',
                404,
            )
        }

        const address =
            mockDb.withdrawalAddresses[
                index
            ]

        if (
            address.status ===
            'blocked'
        ) {
            throw new ApiError(
                'آدرس مسدودشده را نمی‌توان حذف کرد.',
                'BAD_REQUEST',
                409,
            )
        }

        if (
            address.status ===
            'pending_confirmation'
        ) {
            mockDb.withdrawalAddresses.splice(
                index,
                1,
            )

            confirmationState.delete(
                id,
            )

            return
        }

        address.status = 'revoked'
        address.isDefault = false
        address.revokedAt = nowIso()
        address.updatedAt = nowIso()
    },

    setDefault(
        id: string,
    ): WithdrawalAddress {
        activateDueAddresses()

        const address =
            mockDb.withdrawalAddresses.find(
                (item) =>
                    item.id === id,
            )

        if (!address) {
            throw new ApiError(
                'آدرس برداشت پیدا نشد.',
                'NOT_FOUND',
                404,
            )
        }

        if (
            address.status !==
            'active'
        ) {
            throw new ApiError(
                'فقط آدرس فعال می‌تواند به‌عنوان آدرس پیش‌فرض انتخاب شود.',
                'BAD_REQUEST',
                409,
            )
        }

        for (
            const item of
            mockDb.withdrawalAddresses
        ) {
            item.isDefault = false
        }

        address.isDefault = true
        address.updatedAt = nowIso()

        return address
    },
}