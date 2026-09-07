export type StatusTone = 'neutral' | 'info' | 'warning' | 'success' | 'danger'

export type StatusDomain =
  | 'order'
  | 'transaction'
  | 'kyc'
  | 'bank'
  | 'ticket'
  | 'network'
  | 'security'

export interface StatusDefinition {
  readonly label: string
  readonly tone: StatusTone
}

const status = (label: string, tone: StatusTone): StatusDefinition => Object.freeze({ label, tone })

export const ORDER_STATUSES = Object.freeze({
  draft: status('پیش‌نویس', 'neutral'),
  pending: status('در انتظار بررسی', 'warning'),
  pending_payment: status('در انتظار پرداخت', 'warning'),
  awaiting_payment: status('در انتظار پرداخت', 'warning'),
  payment_pending: status('در حال تأیید پرداخت', 'info'),
  payment_confirmed: status('پرداخت تأیید شد', 'info'),
  processing: status('در حال انجام', 'info'),
  completed: status('تکمیل‌شده', 'success'),
  cancelled: status('لغوشده', 'neutral'),
  expired: status('مهلت تمام‌شده', 'neutral'),
  failed: status('ناموفق', 'danger'),
  refunded: status('مبلغ بازگردانده شد', 'info'),
})

export const TRANSACTION_STATUSES = Object.freeze({
  pending: status('در انتظار بررسی', 'warning'),
  awaiting_confirmation: status('در انتظار تأیید شبکه', 'warning'),
  processing: status('در حال پردازش', 'info'),
  completed: status('تکمیل‌شده', 'success'),
  failed: status('ناموفق', 'danger'),
  cancelled: status('لغوشده', 'neutral'),
  reversed: status('بازگشت‌خورده', 'info'),
})

export const KYC_STATUSES = Object.freeze({
  not_started: status('تکمیل نشده', 'neutral'),
  in_progress: status('در حال تکمیل', 'info'),
  pending: status('در انتظار بررسی', 'warning'),
  verified: status('تأییدشده', 'success'),
  needs_correction: status('نیاز به اصلاح', 'warning'),
  rejected: status('رد شده', 'danger'),
})

export const BANK_STATUSES = Object.freeze({
  pending: status('در انتظار بررسی', 'warning'),
  verified: status('تأییدشده', 'success'),
  needs_correction: status('نیاز به اصلاح', 'warning'),
  rejected: status('رد شده', 'danger'),
  disabled: status('غیرفعال', 'neutral'),
})

export const TICKET_STATUSES = Object.freeze({
  open: status('باز', 'info'),
  in_progress: status('در حال بررسی', 'info'),
  awaiting_support: status('در انتظار پاسخ پشتیبانی', 'warning'),
  awaiting_user: status('در انتظار پاسخ شما', 'warning'),
  waiting_for_user: status('در انتظار پاسخ شما', 'warning'),
  answered: status('پاسخ داده‌شده', 'success'),
  resolved: status('پاسخ داده‌شده', 'success'),
  closed: status('بسته‌شده', 'neutral'),
})

export const NETWORK_STATUSES = Object.freeze({
  active: status('فعال', 'success'),
  congested: status('شبکه شلوغ است', 'warning'),
  maintenance: status('در حال به‌روزرسانی', 'warning'),
  deposit_only: status('فقط واریز', 'info'),
  withdrawal_only: status('فقط برداشت', 'info'),
  disabled: status('موقتاً غیرفعال', 'danger'),
})

export const SECURITY_STATUSES = Object.freeze({
  enabled: status('فعال', 'success'),
  disabled: status('غیرفعال', 'neutral'),
  verified: status('تأییدشده', 'success'),
  unverified: status('تأییدنشده', 'warning'),
  secure: status('ایمن', 'success'),
  attention: status('نیازمند توجه', 'warning'),
  current: status('نشست فعلی', 'success'),
  expired: status('منقضی‌شده', 'neutral'),
  revoked: status('دسترسی قطع‌شده', 'danger'),
})

export const STATUS_DEFINITIONS = Object.freeze({
  order: ORDER_STATUSES,
  transaction: TRANSACTION_STATUSES,
  kyc: KYC_STATUSES,
  bank: BANK_STATUSES,
  ticket: TICKET_STATUSES,
  network: NETWORK_STATUSES,
  security: SECURITY_STATUSES,
})

const STATUS_ALIASES: Readonly<Record<StatusDomain, Readonly<Record<string, string>>>> = Object.freeze({
  order: Object.freeze({ success: 'completed', done: 'completed', canceled: 'cancelled', rejected: 'failed' }),
  transaction: Object.freeze({ success: 'completed', confirmed: 'completed', done: 'completed', canceled: 'cancelled' }),
  kyc: Object.freeze({ approved: 'verified', completed: 'verified', incomplete: 'not_started', correction_required: 'needs_correction' }),
  bank: Object.freeze({ approved: 'verified', correction_required: 'needs_correction', inactive: 'disabled' }),
  ticket: Object.freeze({ pending: 'awaiting_support', answered: 'resolved' }),
  network: Object.freeze({ available: 'active', inactive: 'disabled', unavailable: 'disabled' }),
  security: Object.freeze({ active: 'enabled', inactive: 'disabled', pending: 'unverified' }),
})

const UNKNOWN_STATUS = status('نامشخص', 'neutral')

/** Resolve backend status variants without duplicating labels or colors in views. */
export function getStatusDefinition(domain: StatusDomain, value: string | null | undefined): StatusDefinition {
  if (!value) return UNKNOWN_STATUS
  const key = value.trim().toLowerCase().replace(/[\s-]+/g, '_')
  const resolved = STATUS_ALIASES[domain][key] ?? key
  const definitions = STATUS_DEFINITIONS[domain] as Readonly<Record<string, StatusDefinition>>
  return definitions[resolved] ?? UNKNOWN_STATUS
}

export function getStatusLabel(domain: StatusDomain, value: string | null | undefined): string {
  return getStatusDefinition(domain, value).label
}

export function getStatusTone(domain: StatusDomain, value: string | null | undefined): StatusTone {
  return getStatusDefinition(domain, value).tone
}
