import { normalizeDigits } from './financial'

export interface PersianDateParts {
  year: number
  month: number
  day: number
}

const PERSIAN_DATE_FORMATTER = new Intl.DateTimeFormat('en-US-u-ca-persian-nu-latn', {
  year: 'numeric',
  month: '2-digit',
  day: '2-digit',
  timeZone: 'UTC',
})

const TEHRAN_DATE_TIME_FORMATTER = new Intl.DateTimeFormat('en-GB-u-nu-latn', {
  year: 'numeric',
  month: '2-digit',
  day: '2-digit',
  hour: '2-digit',
  minute: '2-digit',
  second: '2-digit',
  hourCycle: 'h23',
  timeZone: 'Asia/Tehran',
})

function numericPart(parts: Intl.DateTimeFormatPart[], type: Intl.DateTimeFormatPartTypes): number {
  return Number(parts.find((part) => part.type === type)?.value ?? Number.NaN)
}

export function parsePersianDateInput(value: string): PersianDateParts | null {
  const normalized = normalizeDigits(value).trim().replace(/[.\-]/g, '/')
  const match = /^(\d{4})\/(\d{1,2})\/(\d{1,2})$/.exec(normalized)
  if (!match) return null

  const year = Number(match[1])
  const month = Number(match[2])
  const day = Number(match[3])
  if (year < 1200 || year > 1700 || month < 1 || month > 12 || day < 1 || day > 31) return null
  return { year, month, day }
}

export function serializePersianDateInput(value: string): string | null {
  const parts = parsePersianDateInput(value)
  if (!parts) return null
  return `${parts.year.toString().padStart(4, '0')}-${parts.month.toString().padStart(2, '0')}-${parts.day.toString().padStart(2, '0')}`
}

function persianPartsAt(timestamp: number): PersianDateParts {
  const parts = PERSIAN_DATE_FORMATTER.formatToParts(new Date(timestamp))
  return {
    year: numericPart(parts, 'year'),
    month: numericPart(parts, 'month'),
    day: numericPart(parts, 'day'),
  }
}

function gregorianDateForPersian(parts: PersianDateParts): PersianDateParts | null {
  // نوروز همیشه در نزدیکی ۲۰ مارسِ سال میلادی متناظر است. جست‌وجوی روزانه
  // از همین نقطه، قواعد کبیسه تقویم فارسی را به موتور استاندارد Intl می‌سپارد.
  const searchStart = Date.UTC(parts.year + 621, 2, 18)
  for (let offset = 0; offset < 371; offset += 1) {
    const timestamp = searchStart + offset * 86_400_000
    const candidate = persianPartsAt(timestamp)
    if (candidate.year === parts.year && candidate.month === parts.month && candidate.day === parts.day) {
      const date = new Date(timestamp)
      return {
        year: date.getUTCFullYear(),
        month: date.getUTCMonth() + 1,
        day: date.getUTCDate(),
      }
    }
  }
  return null
}

function tehranWallTimeToUtc(
  date: PersianDateParts,
  hour = 0,
  minute = 0,
  second = 0,
): number {
  const targetWallTime = Date.UTC(date.year, date.month - 1, date.day, hour, minute, second)
  let guess = targetWallTime

  // Two passes are normally enough; the third keeps this correct across any
  // historical offset transition represented by the runtime's timezone data.
  for (let pass = 0; pass < 3; pass += 1) {
    const rendered = TEHRAN_DATE_TIME_FORMATTER.formatToParts(new Date(guess))
    const renderedWallTime = Date.UTC(
      numericPart(rendered, 'year'),
      numericPart(rendered, 'month') - 1,
      numericPart(rendered, 'day'),
      numericPart(rendered, 'hour'),
      numericPart(rendered, 'minute'),
      numericPart(rendered, 'second'),
    )
    const correction = targetWallTime - renderedWallTime
    guess += correction
    if (correction === 0) break
  }
  return guess
}

/**
 * Converts a user-entered Persian calendar day to an inclusive ISO boundary
 * in the business timezone. Returns null for malformed or impossible dates.
 */
export function persianDateBoundaryIso(value: string, boundary: 'start' | 'end'): string | null {
  const parsed = parsePersianDateInput(value)
  if (!parsed) return null
  const gregorian = gregorianDateForPersian(parsed)
  if (!gregorian) return null

  const start = tehranWallTimeToUtc(gregorian)
  if (boundary === 'start') return new Date(start).toISOString()

  const nextDate = new Date(Date.UTC(gregorian.year, gregorian.month - 1, gregorian.day + 1))
  const nextStart = tehranWallTimeToUtc({
    year: nextDate.getUTCFullYear(),
    month: nextDate.getUTCMonth() + 1,
    day: nextDate.getUTCDate(),
  })
  return new Date(nextStart - 1).toISOString()
}
