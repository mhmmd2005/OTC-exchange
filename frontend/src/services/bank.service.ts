import type { AddBankAccountInput, BankAccount, IranianBank } from '@/types'
import { formatIban, normalizeDigits } from '@/utils/formatters'
import { isValidIranianCardNumber, isValidIranianIban } from '@/utils/validators'
import { ApiError, api, resolveApi } from './api'
import { mockBanks } from './mock/data'
import { createMockId, nowIso } from './mock/helpers'
import { mockDb } from './mock/state'

export interface BankService {
  listBanks(): Promise<IranianBank[]>
  listAccounts(): Promise<BankAccount[]>
  detectBank(cardNumber: string): Promise<IranianBank | null>
  addAccount(input: AddBankAccountInput): Promise<BankAccount>
  setPreferred(id: string): Promise<BankAccount>
  removeAccount(id: string): Promise<void>
}

function cleanCardNumber(value: string): string {
  return normalizeDigits(value).replace(/\D/g, '')
}

function cleanIban(value: string): string {
  return formatIban(value).replace(/\s/g, '')
}

function detectBankSync(cardNumber: string): IranianBank | null {
  const digits = cleanCardNumber(cardNumber)
  return mockBanks.find((bank) => bank.cardPrefixes.some((prefix) => digits.startsWith(prefix))) ?? null
}

function findAccount(id: string): BankAccount {
  const account = mockDb.bankAccounts.find((item) => item.id === id)
  if (!account) throw new ApiError('حساب بانکی مورد نظر پیدا نشد.', 'NOT_FOUND', 404)
  return account
}

export const bankService: BankService = {
  listBanks() {
    return resolveApi(() => mockBanks, () => api.get<IranianBank[]>('/banks'))
  },

  listAccounts() {
    return resolveApi(() => mockDb.bankAccounts, () => api.get<BankAccount[]>('/bank-accounts'))
  },

  detectBank(cardNumber) {
    const bin = cleanCardNumber(cardNumber).slice(0, 6)
    return resolveApi(() => detectBankSync(bin), () => api.post<IranianBank | null>('/banks/detect', { bin }))
  },

  addAccount(input) {
    return resolveApi(() => {
      const cardNumber = cleanCardNumber(input.cardNumber)
      const iban = cleanIban(input.iban)
      const fields: Record<string, string> = {}
      if (!/^\d{16}$/.test(cardNumber)) fields.cardNumber = 'شماره کارت باید ۱۶ رقم باشد.'
      else if (!isValidIranianCardNumber(cardNumber)) fields.cardNumber = 'شماره کارت معتبر نیست؛ رقم‌ها را دوباره بررسی کنید.'
      if (!/^IR\d{24}$/.test(iban)) fields.iban = 'شماره شبا باید با IR شروع شود و ۲۴ رقم داشته باشد.'
      else if (!isValidIranianIban(iban)) fields.iban = 'شماره شبای واردشده معتبر نیست.'
      const bank = detectBankSync(cardNumber)
      if (!bank && !fields.cardNumber) fields.cardNumber = 'بانک صادرکننده این کارت شناسایی نشد.'
      if (Object.keys(fields).length) {
        throw new ApiError('اطلاعات حساب بانکی را بررسی کنید.', 'VALIDATION_ERROR', 422, { fields })
      }
      if (mockDb.bankAccounts.some((account) => account.cardNumber === cardNumber || account.iban === iban)) {
        throw new ApiError('این حساب بانکی قبلا ثبت شده است.', 'VALIDATION_ERROR', 422)
      }

      const account: BankAccount = {
        id: createMockId('bank_acc'),
        bank: bank as IranianBank,
        ownerName: mockDb.user.fullName,
        cardNumber,
        iban,
        accountNumber: input.accountNumber ? normalizeDigits(input.accountNumber).replace(/\D/g, '') : undefined,
        status: 'pending',
        preferred: false,
        createdAt: nowIso(),
      }
      mockDb.bankAccounts.unshift(account)
      return account
    }, () => api.post<BankAccount>('/bank-accounts', input))
  },

  setPreferred(id) {
    return resolveApi(() => {
      const account = findAccount(id)
      if (account.status !== 'verified') {
        throw new ApiError('فقط حساب تأییدشده می‌تواند حساب منتخب باشد.', 'BAD_REQUEST', 409)
      }
      mockDb.bankAccounts.forEach((item) => { item.preferred = item.id === id })
      return account
    }, () => api.post<BankAccount>(`/bank-accounts/${id}/preferred`))
  },

  removeAccount(id) {
    return resolveApi(() => {
      const account = findAccount(id)
      if (account.preferred) {
        throw new ApiError('ابتدا یک حساب دیگر را به‌عنوان حساب منتخب تعیین کنید.', 'BAD_REQUEST', 409)
      }
      const index = mockDb.bankAccounts.findIndex((item) => item.id === id)
      mockDb.bankAccounts.splice(index, 1)
    }, () => api.delete<void>(`/bank-accounts/${id}`))
  },
}

export default bankService
