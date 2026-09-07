import type { AccountLevel, KycStatus } from '@/types'

const ACCOUNT_LEVEL_LABELS: Record<AccountLevel, string> = {
  level_0: 'سطح صفر',
  level_1: 'سطح یک',
  level_2: 'سطح دو',
  level_3: 'سطح سه',
}

export function accountLevelLabel(level?: AccountLevel | null, emptyValue = ''): string {
  return level ? ACCOUNT_LEVEL_LABELS[level] : emptyValue
}

export function kycAttentionLabel(status?: KycStatus | null): string {
  if (!status || status === 'verified') return ''
  if (status === 'pending' || status === 'in_progress') return 'در حال بررسی'
  if (status === 'needs_correction' || status === 'rejected') return 'نیاز به اصلاح'
  return 'تکمیل حساب'
}

