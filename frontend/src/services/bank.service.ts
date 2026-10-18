import type {AddBankAccountInput, BankAccount, IranianBank} from '@/types'
import {formatIban, normalizeDigits} from '@/utils/formatters'
import {api} from './api'

export interface BankService {
    listBanks(): Promise<IranianBank[]>

    listAccounts(): Promise<BankAccount[]>

    detectBank(cardNumber: string): Promise<IranianBank | null>

    addAccount(input: AddBankAccountInput): Promise<BankAccount>

    setTemporaryAvailability(
        id: string,
        input: {
            isTemporarilyDisabled: boolean
            twoFactorCode?: string
        },
    ): Promise<BankAccount>

    setPreferred(id: string): Promise<BankAccount>

    removeAccount(id: string): Promise<void>
}

function cleanCardNumber(value: string): string {
    return normalizeDigits(value).replace(/\D/g, '')
}

function cleanIban(value: string): string {
    return formatIban(value).replace(/\s/g, '')
}

function cleanAccountNumber(value: string | undefined): string | undefined {
    if (!value) return undefined

    const digits = normalizeDigits(value).replace(/\D/g, '')
    return digits || undefined
}

export const bankService: BankService = {
    async listBanks() {
        return api.get<IranianBank[]>('/banks')
    },

    async setTemporaryAvailability(id, input) {
        const twoFactorCode = input.twoFactorCode
            ? normalizeDigits(input.twoFactorCode).replace(/\D/g, '')
            : ''

        return api.patch<BankAccount>(
            `/bank-accounts/${encodeURIComponent(id)}/availability`,
            {
                isTemporarilyDisabled: input.isTemporarilyDisabled,
                ...(twoFactorCode ? {twoFactorCode} : {}),
            },
        )
    },

    async listAccounts() {
        return api.get<BankAccount[]>('/bank-accounts')
    },

    async detectBank(cardNumber) {
        const digits = cleanCardNumber(cardNumber)

        if (digits.length < 6) {
            return null
        }

        return api.post<IranianBank | null>('/banks/detect', {
            bin: digits,
        })
    },

    async addAccount(input) {
        const cardNumber = cleanCardNumber(input.cardNumber)
        const iban = cleanIban(input.iban)
        const accountNumber = cleanAccountNumber(input.accountNumber)

        return api.post<BankAccount>('/bank-accounts', {
            cardNumber,
            iban,
            ...(accountNumber ? {accountNumber} : {}),
        })
    },

    async setPreferred(id) {
        return api.post<BankAccount>(`/bank-accounts/${id}/preferred`)
    },
    async removeAccount(id) {
        await api.delete(`/bank-accounts/${id}`)
    },
}