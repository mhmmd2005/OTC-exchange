import type {
    ActiveSession,
    BankAccount,
    NotificationItem,
    OtcOrder,
    SecurityEvent,
    SupportTicket,
    Transaction,
    UserPreferences,
    UserProfile,
    VerificationSummary,
    WalletSummary,
    WithdrawalAddress,
} from '@/types'
import {cloneMock} from '../api'
import {
    mockBankAccounts,
    mockNotifications,
    mockOrders,
    mockPreferences,
    mockSecurityEvents,
    mockSessions,
    mockTickets,
    mockTransactions,
    mockUser,
    mockVerification,
    mockWallet,
    mockWithdrawalAddresses,
} from './data'

export interface MockDatabase {
    user: UserProfile
    wallet: WalletSummary
    orders: OtcOrder[]
    transactions: Transaction[]
    bankAccounts: BankAccount[]
    verification: VerificationSummary
    notifications: NotificationItem[]
    tickets: SupportTicket[]
    sessions: ActiveSession[]
    securityEvents: SecurityEvent[]
    preferences: UserPreferences
    withdrawalAddresses: WithdrawalAddress[]
}

function createDatabase(): MockDatabase {
    return cloneMock({
        user: mockUser,
        wallet: mockWallet,
        orders: mockOrders,
        transactions: mockTransactions,
        bankAccounts: mockBankAccounts,
        verification: mockVerification,
        notifications: mockNotifications,
        tickets: mockTickets,
        sessions: mockSessions,
        securityEvents: mockSecurityEvents,
        preferences: mockPreferences,
        withdrawalAddresses: mockWithdrawalAddresses,
    })
}

export const mockDb: MockDatabase = createDatabase()

/** Intended for component tests and Storybook-style isolated scenarios. */
export function resetMockDatabase(): void {
    Object.assign(mockDb, createDatabase())
}

