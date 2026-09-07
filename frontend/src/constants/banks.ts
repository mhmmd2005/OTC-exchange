import type { IranianBank } from '@/types'

export type BankMark = 'saman' | 'mellat' | 'pasargad' | 'melli' | 'generic'

export interface BankIdentity {
  id: string
  mark: BankMark
  monogram: string
  primary: string
  secondary: string
}

const BANK_IDENTITIES: Readonly<Record<string, BankIdentity>> = Object.freeze({
  saman: Object.freeze({ id: 'saman', mark: 'saman', monogram: 'س', primary: '#008d91', secondary: '#5bd4ce' }),
  mellat: Object.freeze({ id: 'mellat', mark: 'mellat', monogram: 'م', primary: '#cf2635', secondary: '#f2b63c' }),
  pasargad: Object.freeze({ id: 'pasargad', mark: 'pasargad', monogram: 'پ', primary: '#bd861e', secondary: '#f1c75b' }),
  melli: Object.freeze({ id: 'melli', mark: 'melli', monogram: 'ملی', primary: '#00728c', secondary: '#69c5d7' }),
})

const BANK_ALIASES: Readonly<Record<string, string>> = Object.freeze({
  samanbank: 'saman',
  'بانکسامان': 'saman',
  bankmellat: 'mellat',
  'بانکملت': 'mellat',
  bankpasargad: 'pasargad',
  'بانکپاسارگاد': 'pasargad',
  bankmelliiran: 'melli',
  'بانکملی': 'melli',
  'بانکملیایران': 'melli',
})

const DEFAULT_IDENTITY: BankIdentity = Object.freeze({
  id: 'generic',
  mark: 'generic',
  monogram: 'ب',
  primary: '#3d78be',
  secondary: '#8ab8e9',
})

function normalizeBankKey(value: string): string {
  return value.trim().toLocaleLowerCase('fa-IR').replace(/[\s_-]+/g, '')
}

/** Central source for bank marks and brand accents; API colors never determine the logo itself. */
export function getBankIdentity(bank: Pick<IranianBank, 'id' | 'nameFa' | 'nameEn'>): BankIdentity {
  const candidates = [bank.id, bank.nameFa, bank.nameEn]
  for (const candidate of candidates) {
    const normalized = normalizeBankKey(candidate)
    const resolvedId = BANK_IDENTITIES[normalized] ? normalized : BANK_ALIASES[normalized]
    if (resolvedId && BANK_IDENTITIES[resolvedId]) return BANK_IDENTITIES[resolvedId]
  }
  return DEFAULT_IDENTITY
}
