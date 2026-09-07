import type { ISODateString } from './common'

export type BankAccountStatus = 'pending' | 'verified' | 'needs_correction' | 'rejected'

export interface IranianBank {
  id: string
  nameFa: string
  nameEn: string
  cardPrefixes: string[]
  color: string
  logoUrl?: string
}

export interface BankAccount {
  id: string
  bank: IranianBank
  ownerName: string
  cardNumber: string
  iban: string
  accountNumber?: string
  status: BankAccountStatus
  preferred: boolean
  rejectionReason?: string
  createdAt: ISODateString
  verifiedAt?: ISODateString
}

export interface AddBankAccountInput {
  cardNumber: string
  iban: string
  accountNumber?: string
}

