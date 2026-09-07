import {
  normalizeDecimal,
  normalizeDigits,
  parseFinancialInput,
  roundDecimal,
  type DecimalInput,
  type RoundingMode,
} from './financial'

export { normalizeDigits, parseFinancialInput }

export const LTR_ISOLATE = '\u2066'
export const FIRST_STRONG_ISOLATE = '\u2068'
export const POP_DIRECTIONAL_ISOLATE = '\u2069'

export interface NumberFormatOptions {
  minimumFractionDigits?: number
  maximumFractionDigits?: number
  useGrouping?: boolean
  usePersianDigits?: boolean
  roundingMode?: RoundingMode
}

export interface TomanFormatOptions extends NumberFormatOptions {
  showCurrency?: boolean
  emptyValue?: string
}

export interface CryptoFormatOptions extends NumberFormatOptions {
  symbol?: string
  isolate?: boolean
  emptyValue?: string
}

export interface TechnicalNumberFormatOptions {
  usePersianDigits?: boolean
  isolate?: boolean
  masked?: boolean
}

export type DateInput = Date | string | number | null | undefined

export interface PersianDateOptions {
  timeZone?: string
  emptyValue?: string
  month?: '2-digit' | 'numeric' | 'long' | 'short'
}

const PERSIAN_DIGITS = '۰۱۲۳۴۵۶۷۸۹'
const DEFAULT_TIME_ZONE = 'Asia/Tehran'
const DEFAULT_EMPTY_VALUE = '—'
let usePersianUiDigits = true

export function setUiDigitPreference(enabled: boolean): void {
  usePersianUiDigits = enabled
}

export function toPersianDigits(value: string | number | bigint): string {
  const normalized = normalizeDigits(value)
  return usePersianUiDigits
    ? normalized.replace(/\d/g, (digit) => PERSIAN_DIGITS[Number(digit)] ?? digit)
    : normalized
}

export function toEnglishDigits(value: string | number | bigint): string {
  return normalizeDigits(value)
}

/** Wrap technical LTR content so it stays readable inside Persian text. */
export function bidiIsolate(value: string | number | bigint, direction: 'ltr' | 'auto' = 'ltr'): string {
  const text = String(value).replace(/^[\u2066\u2068]|\u2069$/g, '')
  return `${direction === 'ltr' ? LTR_ISOLATE : FIRST_STRONG_ISOLATE}${text}${POP_DIRECTIONAL_ISOLATE}`
}

function formatDecimal(value: DecimalInput, options: NumberFormatOptions = {}): string {
  const maximum = options.maximumFractionDigits ?? 0
  const minimum = Math.min(options.minimumFractionDigits ?? 0, maximum)
  const rounded = roundDecimal(value, maximum, options.roundingMode ?? 'half-up')
  const negative = rounded.startsWith('-')
  const [rawInteger, rawFraction = ''] = rounded.replace(/^-/, '').split('.')
  const integer = options.useGrouping === false
    ? rawInteger
    : rawInteger.replace(/\B(?=(\d{3})+(?!\d))/g, ',')
  const fraction = rawFraction.padEnd(minimum, '0')
  const result = `${negative ? '-' : ''}${integer}${fraction ? `.${fraction}` : ''}`
  return options.usePersianDigits === false ? result : toPersianDigits(result)
}

function hasValue(value: unknown): value is DecimalInput {
  return value !== null && value !== undefined && String(value).trim() !== ''
}

export function formatToman(
  value: DecimalInput | null | undefined,
  options: TomanFormatOptions = {},
): string {
  if (!hasValue(value)) return options.emptyValue ?? DEFAULT_EMPTY_VALUE
  try {
    const amount = formatDecimal(value, {
      maximumFractionDigits: options.maximumFractionDigits ?? 0,
      minimumFractionDigits: options.minimumFractionDigits ?? 0,
      useGrouping: options.useGrouping ?? true,
      usePersianDigits: options.usePersianDigits ?? true,
      roundingMode: options.roundingMode,
    })
    return options.showCurrency === false ? amount : `${amount} تومان`
  } catch {
    return options.emptyValue ?? DEFAULT_EMPTY_VALUE
  }
}

export function formatCrypto(
  value: DecimalInput | null | undefined,
  options: CryptoFormatOptions = {},
): string {
  if (!hasValue(value)) return options.emptyValue ?? DEFAULT_EMPTY_VALUE
  try {
    const amount = formatDecimal(value, {
      maximumFractionDigits: options.maximumFractionDigits ?? 8,
      minimumFractionDigits: options.minimumFractionDigits ?? 0,
      useGrouping: options.useGrouping ?? true,
      usePersianDigits: options.usePersianDigits ?? true,
      roundingMode: options.roundingMode,
    })
    const result = options.symbol ? `${amount} ${options.symbol.toUpperCase()}` : amount
    return options.isolate ? bidiIsolate(result) : result
  } catch {
    return options.emptyValue ?? DEFAULT_EMPTY_VALUE
  }
}

export function formatPercentage(
  value: DecimalInput | null | undefined,
  options: NumberFormatOptions & { showSign?: boolean; emptyValue?: string } = {},
): string {
  if (!hasValue(value)) return options.emptyValue ?? DEFAULT_EMPTY_VALUE
  try {
    let formatted = formatDecimal(value, {
      maximumFractionDigits: options.maximumFractionDigits ?? 2,
      minimumFractionDigits: options.minimumFractionDigits ?? 0,
      useGrouping: options.useGrouping ?? false,
      usePersianDigits: options.usePersianDigits ?? true,
      roundingMode: options.roundingMode,
    })
    if (options.showSign && !normalizeDecimal(value).startsWith('-') && normalizeDecimal(value) !== '0') {
      formatted = `+${formatted}`
    }
    return `${formatted}٪`
  } catch {
    return options.emptyValue ?? DEFAULT_EMPTY_VALUE
  }
}

export function formatCardNumber(
  value: string | number | bigint | null | undefined,
  options: TechnicalNumberFormatOptions = {},
): string {
  if (value === null || value === undefined) return ''
  const digits = normalizeDigits(value).replace(/\D/g, '').slice(0, 16)
  if (!digits) return ''

  let display = options.masked && digits.length >= 8
    ? `${digits.slice(0, 6)}${'•'.repeat(Math.max(0, digits.length - 10))}${digits.slice(-4)}`
    : digits
  display = display.replace(/(.{4})(?=.)/g, '$1 ')
  if (options.usePersianDigits) display = toPersianDigits(display)
  return options.isolate ? bidiIsolate(display) : display
}

/** Mask a stored card for overview surfaces without revealing the six-digit BIN. */
export function formatMaskedCardOverview(
  value: string | number | bigint | null | undefined,
  options: Pick<TechnicalNumberFormatOptions, 'usePersianDigits' | 'isolate'> = {},
): string {
  if (value === null || value === undefined) return ''
  const digits = normalizeDigits(value).replace(/\D/g, '').slice(0, 16)
  if (!digits) return ''
  const visibleStart = digits.slice(0, Math.min(4, digits.length))
  const visibleEnd = digits.length > 4 ? digits.slice(-Math.min(4, digits.length - 4)) : ''
  const hiddenLength = Math.max(0, digits.length - visibleStart.length - visibleEnd.length)
  let display = `${visibleStart}${'•'.repeat(hiddenLength)}${visibleEnd}`.replace(/(.{4})(?=.)/g, '$1 ')
  if (options.usePersianDigits) display = toPersianDigits(display)
  return options.isolate ? bidiIsolate(display) : display
}

export function formatIban(
  value: string | number | bigint | null | undefined,
  options: Omit<TechnicalNumberFormatOptions, 'masked'> = {},
): string {
  if (value === null || value === undefined) return ''
  const compact = normalizeDigits(value)
    .toUpperCase()
    .replace(/[^A-Z0-9]/g, '')
    .replace(/^IR/, '')
    .slice(0, 24)
  if (!compact) return ''

  let display = `IR${compact}`.replace(/(.{4})(?=.)/g, '$1 ')
  if (options.usePersianDigits) display = toPersianDigits(display)
  return options.isolate ? bidiIsolate(display) : display
}

/** Keep only the country/check digits and final four characters visible in account overviews. */
export function formatMaskedIbanOverview(
  value: string | number | bigint | null | undefined,
  options: Pick<TechnicalNumberFormatOptions, 'usePersianDigits' | 'isolate'> = {},
): string {
  if (value === null || value === undefined) return ''
  const normalized = normalizeDigits(value).toUpperCase().replace(/[^A-Z0-9]/g, '')
  const compact = normalized.startsWith('IR') ? normalized.slice(0, 26) : `IR${normalized}`.slice(0, 26)
  if (compact.length <= 4) return options.usePersianDigits ? toPersianDigits(compact) : compact
  const visibleEnd = compact.length >= 8 ? compact.slice(-4) : ''
  const hiddenLength = Math.max(0, compact.length - 4 - visibleEnd.length)
  const hiddenGroups = '•'.repeat(hiddenLength).replace(/(.{4})(?=.)/g, '$1 ')
  let display = [compact.slice(0, 4), hiddenGroups, visibleEnd].filter(Boolean).join(' ')
  if (options.usePersianDigits) display = toPersianDigits(display)
  return options.isolate ? bidiIsolate(display) : display
}

function parseDate(value: DateInput): Date | null {
  if (value === null || value === undefined || value === '') return null
  const date = value instanceof Date ? new Date(value.getTime()) : new Date(value)
  return Number.isNaN(date.getTime()) ? null : date
}

function datePart(parts: Intl.DateTimeFormatPart[], type: Intl.DateTimeFormatPartTypes): string {
  return parts.find((part) => part.type === type)?.value ?? ''
}

export function formatPersianDate(value: DateInput, options: PersianDateOptions = {}): string {
  const date = parseDate(value)
  if (!date) return options.emptyValue ?? DEFAULT_EMPTY_VALUE

  const formatter = new Intl.DateTimeFormat('fa-IR-u-ca-persian-nu-latn', {
    year: 'numeric',
    month: options.month ?? '2-digit',
    day: '2-digit',
    timeZone: options.timeZone ?? DEFAULT_TIME_ZONE,
  })
  const parts = formatter.formatToParts(date)
  if (options.month === 'long' || options.month === 'short') {
    return toPersianDigits(`${datePart(parts, 'day')} ${datePart(parts, 'month')} ${datePart(parts, 'year')}`)
  }
  return toPersianDigits(`${datePart(parts, 'year')}/${datePart(parts, 'month')}/${datePart(parts, 'day')}`)
}

export function formatTime(
  value: DateInput,
  options: Pick<PersianDateOptions, 'timeZone' | 'emptyValue'> & { includeSeconds?: boolean } = {},
): string {
  const date = parseDate(value)
  if (!date) return options.emptyValue ?? DEFAULT_EMPTY_VALUE
  const formatter = new Intl.DateTimeFormat('fa-IR-u-nu-latn', {
    hour: '2-digit',
    minute: '2-digit',
    second: options.includeSeconds ? '2-digit' : undefined,
    hourCycle: 'h23',
    timeZone: options.timeZone ?? DEFAULT_TIME_ZONE,
  })
  return toPersianDigits(formatter.format(date))
}

export function formatPersianDateTime(
  value: DateInput,
  options: PersianDateOptions & { includeSeconds?: boolean } = {},
): string {
  const date = parseDate(value)
  if (!date) return options.emptyValue ?? DEFAULT_EMPTY_VALUE
  return `${formatPersianDate(date, options)}، ساعت ${formatTime(date, options)}`
}

export function formatRelativeTime(
  value: DateInput,
  now: DateInput = new Date(),
  options: Pick<PersianDateOptions, 'emptyValue'> = {},
): string {
  const date = parseDate(value)
  const reference = parseDate(now)
  if (!date || !reference) return options.emptyValue ?? DEFAULT_EMPTY_VALUE

  const seconds = Math.round((date.getTime() - reference.getTime()) / 1_000)
  const intervals: ReadonlyArray<[Intl.RelativeTimeFormatUnit, number]> = [
    ['year', 31_536_000],
    ['month', 2_592_000],
    ['week', 604_800],
    ['day', 86_400],
    ['hour', 3_600],
    ['minute', 60],
    ['second', 1],
  ]
  const [unit, divisor] = intervals.find(([, size]) => Math.abs(seconds) >= size) ?? ['second', 1]
  return new Intl.RelativeTimeFormat('fa-IR', { numeric: 'auto' }).format(Math.round(seconds / divisor), unit)
}
