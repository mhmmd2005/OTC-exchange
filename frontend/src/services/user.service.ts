import type {DashboardSummary, UpdateProfileInput, UserPreferences, UserProfile,} from '@/types'
import {api, resolveApi} from './api'
import {authService} from './auth.service'
import {mockDb} from './mock/state'

export interface UserService {
    getProfile(): Promise<UserProfile>

    updateProfile(input: UpdateProfileInput): Promise<UserProfile>

    getDashboardSummary(): Promise<DashboardSummary>

    getPreferences(): Promise<UserPreferences>

    updatePreferences(input: Partial<UserPreferences>): Promise<UserPreferences>
}

export const userService: UserService = {
    getProfile() {
        return resolveApi(
            () => mockDb.user,
            () => authService.getCurrentUser(),
        )
    },

    updateProfile(input) {
        return resolveApi(
            () => {
                Object.assign(
                    mockDb.user,
                    input,
                )

                mockDb.user.fullName =
                    `${mockDb.user.firstName} ${mockDb.user.lastName}`.trim()

                return mockDb.user
            },
            () =>
                api.patch<UserProfile>(
                    '/users/me',
                    input,
                ),
        )
    },

    getDashboardSummary() {
        return resolveApi(
            () => ({
                user: mockDb.user,
                totalPortfolioToman:
                mockDb.wallet.totalValueToman,
                tomanBalance:
                mockDb.wallet.tomanBalance,
                cryptoValueToman:
                mockDb.wallet.cryptoValueToman,
                pendingOrdersCount:
                mockDb.orders.filter(
                    (order) =>
                        [
                            'pending_payment',
                            'payment_confirmed',
                            'processing',
                        ].includes(order.status),
                ).length,
                unreadNotificationsCount:
                mockDb.notifications.filter(
                    (item) => !item.read,
                ).length,
                kycStatus:
                mockDb.user.kycStatus,
                accountLevel:
                mockDb.user.accountLevel,
            }),
            () =>
                api.get<DashboardSummary>(
                    '/dashboard/summary',
                ),
        )
    },

    getPreferences() {
        return resolveApi(
            () => mockDb.preferences,
            () =>
                api.get<UserPreferences>(
                    '/users/me/preferences',
                ),
        )
    },

    updatePreferences(input) {
        return resolveApi(
            () => {
                mockDb.preferences = {
                    ...mockDb.preferences,
                    ...input,
                    notificationChannels: {
                        ...mockDb.preferences
                            .notificationChannels,
                        ...input.notificationChannels,
                    },
                }

                return mockDb.preferences
            },
            () =>
                api.patch<UserPreferences>(
                    '/users/me/preferences',
                    input,
                ),
        )
    },
}

export default userService