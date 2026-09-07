/**
 * Decimal-safe helpers for financial values.
 *
 * Public calculations accept strings, bigint values and safe/finite numbers, but
 * always return decimal strings. Keep values received from APIs as strings so no
 * precision has already been lost before reaching these helpers.
 */

export type DecimalInput = string | number | bigint

export type RoundingMode =
  | 'half-up'
  | 'half-even'
  | 'down'
  | 'up'
  | 'floor'
  | 'ceil'

export interface FinancialInputOptions {
  allowNegative?: boolean
  maxFractionDigits?: number
  roundingMode?: RoundingMode
}

interface DecimalParts {
  coefficient: bigint
  scale: number
}

const PERSIAN_DIGITS = '۰۱۲۳۴۵۶۷۸۹'
const ARABIC_DIGITS = '٠١٢٣٤٥٦٧٨٩'
const MAX_SCALE = 1_000
const POWERS_OF_TEN = new Map<number, bigint>([[0, 1n]])

export function normalizeDigits(value: string | number | bigint): string {
  return String(value).replace(/[۰-۹٠-٩]/g, (digit) => {
    const persianIndex = PERSIAN_DIGITS.indexOf(digit)
    return String(persianIndex >= 0 ? persianIndex : ARABIC_DIGITS.indexOf(digit))
  })
}

function powerOfTen(exponent: number): bigint {
  assertScale(exponent)
  const cached = POWERS_OF_TEN.get(exponent)
  if (cached !== undefined) return cached

  const value = BigInt(`1${'0'.repeat(exponent)}`)
  POWERS_OF_TEN.set(exponent, value)
  return value
}

function assertScale(scale: number): void {
  if (!Number.isInteger(scale) || scale < 0 || scale > MAX_SCALE) {
    throw new RangeError(`Decimal scale must be an integer between 0 and ${MAX_SCALE}.`)
  }
}

function expandScientificNotation(rawValue: string): string {
  const match = rawValue.match(/^([+-]?)(\d*)(?:\.(\d*))?(?:[eE]([+-]?\d+))?$/)
  if (!match || (!match[2] && !match[3])) {
    throw new TypeError(`Invalid decimal value: ${rawValue}`)
  }

  const sign = match[1] === '-' ? '-' : ''
  const integer = match[2] || '0'
  const fraction = match[3] || ''
  const exponent = Number(match[4] || '0')
  if (!Number.isSafeInteger(exponent) || Math.abs(exponent) > MAX_SCALE) {
    throw new RangeError(`Decimal exponent must be between -${MAX_SCALE} and ${MAX_SCALE}.`)
  }

  const digits = `${integer}${fraction}`
  const decimalIndex = integer.length + exponent
  if (decimalIndex <= 0) return `${sign}0.${'0'.repeat(-decimalIndex)}${digits}`
  if (decimalIndex >= digits.length) return `${sign}${digits}${'0'.repeat(decimalIndex - digits.length)}`
  return `${sign}${digits.slice(0, decimalIndex)}.${digits.slice(decimalIndex)}`
}

function decimalParts(value: DecimalInput): DecimalParts {
  if (typeof value === 'number' && !Number.isFinite(value)) {
    throw new TypeError('Financial values must be finite numbers.')
  }

  const normalized = normalizeDigits(value)
    .trim()
    .replace(/[\u061c\u200e\u200f\u202a-\u202e\u2066-\u2069]/g, '')
    .replace(/\u066b/g, '.')

  const expanded = expandScientificNotation(normalized)
  const negative = expanded.startsWith('-')
  const unsigned = expanded.replace(/^[+-]/, '')
  const [integer = '0', fraction = ''] = unsigned.split('.')
  const scale = fraction.length
  assertScale(scale)

  const coefficient = BigInt(`${integer}${fraction}` || '0') * (negative ? -1n : 1n)
  return stripTrailingZeroes({ coefficient, scale })
}

function stripTrailingZeroes(parts: DecimalParts): DecimalParts {
  let { coefficient, scale } = parts
  if (coefficient === 0n) return { coefficient: 0n, scale: 0 }
  while (scale > 0 && coefficient % 10n === 0n) {
    coefficient /= 10n
    scale -= 1
  }
  return { coefficient, scale }
}

function partsToString(parts: DecimalParts, fixedScale?: number): string {
  const targetScale = fixedScale ?? parts.scale
  assertScale(targetScale)

  let coefficient = parts.coefficient
  if (targetScale > parts.scale) coefficient *= powerOfTen(targetScale - parts.scale)
  if (targetScale < parts.scale) coefficient /= powerOfTen(parts.scale - targetScale)

  const negative = coefficient < 0n
  const digits = (negative ? -coefficient : coefficient).toString().padStart(targetScale + 1, '0')
  const output = targetScale === 0
    ? digits
    : `${digits.slice(0, -targetScale)}.${digits.slice(-targetScale)}`
  return negative && coefficient !== 0n ? `-${output}` : output
}

function alignedCoefficients(left: DecimalParts, right: DecimalParts): [bigint, bigint, number] {
  const scale = Math.max(left.scale, right.scale)
  return [
    left.coefficient * powerOfTen(scale - left.scale),
    right.coefficient * powerOfTen(scale - right.scale),
    scale,
  ]
}

function shouldRound(
  quotient: bigint,
  remainder: bigint,
  divisor: bigint,
  sign: -1 | 1,
  mode: RoundingMode,
): boolean {
  if (remainder === 0n) return false
  if (mode === 'down') return false
  if (mode === 'up') return true
  if (mode === 'floor') return sign < 0
  if (mode === 'ceil') return sign > 0

  const comparison = remainder * 2n - divisor
  if (comparison > 0n) return true
  if (comparison < 0n) return false
  return mode === 'half-up' || quotient % 2n !== 0n
}

function divideAndRound(
  numerator: bigint,
  denominator: bigint,
  mode: RoundingMode,
): bigint {
  if (denominator === 0n) throw new RangeError('Cannot divide by zero.')

  const sign: -1 | 1 = (numerator < 0n) !== (denominator < 0n) ? -1 : 1
  const absoluteNumerator = numerator < 0n ? -numerator : numerator
  const absoluteDenominator = denominator < 0n ? -denominator : denominator
  let quotient = absoluteNumerator / absoluteDenominator
  const remainder = absoluteNumerator % absoluteDenominator

  if (shouldRound(quotient, remainder, absoluteDenominator, sign, mode)) quotient += 1n
  return sign < 0 ? -quotient : quotient
}

/** Return a canonical decimal string without redundant leading or trailing zeroes. */
export function normalizeDecimal(value: DecimalInput): string {
  return partsToString(decimalParts(value))
}

/**
 * Normalize a localized amount typed by a user. Invalid or empty input returns
 * an empty string, which is convenient for form state and validation.
 */
export function parseFinancialInput(
  value: string | number | bigint | null | undefined,
  options: FinancialInputOptions = {},
): string {
  if (value === null || value === undefined || String(value).trim() === '') return ''

  const cleaned = normalizeDigits(value)
    .replace(/[\u061c\u200e\u200f\u202a-\u202e\u2066-\u2069]/g, '')
    .replace(/[\s,_\u066c]/g, '')
    .replace(/\u066b/g, '.')
    .replace(/(?:تومان|تومن|ریال|irr|irt)/gi, '')

  try {
    const normalized = normalizeDecimal(cleaned)
    if (options.allowNegative === false && normalized.startsWith('-')) return ''
    if (options.maxFractionDigits === undefined) return normalized
    return roundDecimal(normalized, options.maxFractionDigits, options.roundingMode ?? 'down')
  } catch {
    return ''
  }
}

export function addDecimal(left: DecimalInput, right: DecimalInput): string {
  const [leftCoefficient, rightCoefficient, scale] = alignedCoefficients(
    decimalParts(left),
    decimalParts(right),
  )
  return partsToString(stripTrailingZeroes({ coefficient: leftCoefficient + rightCoefficient, scale }))
}

export function subtractDecimal(left: DecimalInput, right: DecimalInput): string {
  const [leftCoefficient, rightCoefficient, scale] = alignedCoefficients(
    decimalParts(left),
    decimalParts(right),
  )
  return partsToString(stripTrailingZeroes({ coefficient: leftCoefficient - rightCoefficient, scale }))
}

export function multiplyDecimal(left: DecimalInput, right: DecimalInput): string {
  const a = decimalParts(left)
  const b = decimalParts(right)
  assertScale(a.scale + b.scale)
  return partsToString(stripTrailingZeroes({
    coefficient: a.coefficient * b.coefficient,
    scale: a.scale + b.scale,
  }))
}

/** Divide to a bounded number of fractional digits (18 by default). */
export function divideDecimal(
  dividend: DecimalInput,
  divisor: DecimalInput,
  fractionDigits = 18,
  roundingMode: RoundingMode = 'half-up',
): string {
  assertScale(fractionDigits)
  const a = decimalParts(dividend)
  const b = decimalParts(divisor)
  if (b.coefficient === 0n) throw new RangeError('Cannot divide by zero.')

  const numerator = a.coefficient * powerOfTen(b.scale + fractionDigits)
  const denominator = b.coefficient * powerOfTen(a.scale)
  const coefficient = divideAndRound(numerator, denominator, roundingMode)
  return partsToString(stripTrailingZeroes({ coefficient, scale: fractionDigits }))
}

export function compareDecimal(left: DecimalInput, right: DecimalInput): -1 | 0 | 1 {
  const [a, b] = alignedCoefficients(decimalParts(left), decimalParts(right))
  return a === b ? 0 : a < b ? -1 : 1
}

/** Round and return a canonical decimal string (for example 1.20 becomes 1.2). */
export function roundDecimal(
  value: DecimalInput,
  fractionDigits = 0,
  roundingMode: RoundingMode = 'half-up',
): string {
  assertScale(fractionDigits)
  const parts = decimalParts(value)
  if (parts.scale <= fractionDigits) return partsToString(parts)

  const divisor = powerOfTen(parts.scale - fractionDigits)
  const coefficient = divideAndRound(parts.coefficient, divisor, roundingMode)
  return partsToString(stripTrailingZeroes({ coefficient, scale: fractionDigits }))
}

/** Toman total for a crypto amount and a Toman-per-unit quote. */
export function calculateQuoteTotal(
  cryptoAmount: DecimalInput,
  tomanRate: DecimalInput,
  tomanFractionDigits = 0,
): string {
  return roundDecimal(multiplyDecimal(cryptoAmount, tomanRate), tomanFractionDigits, 'half-up')
}

/** Crypto amount obtainable for a Toman total at the supplied quote. */
export function calculateQuoteAmount(
  tomanTotal: DecimalInput,
  tomanRate: DecimalInput,
  cryptoFractionDigits = 8,
): string {
  return divideDecimal(tomanTotal, tomanRate, cryptoFractionDigits, 'down')
}

/** Percentage of an amount; percent=0.25 means 0.25%, not 25%. */
export function calculatePercentageAmount(
  amount: DecimalInput,
  percent: DecimalInput,
  fractionDigits = 8,
): string {
  return roundDecimal(divideDecimal(multiplyDecimal(amount, percent), '100', fractionDigits + 2), fractionDigits)
}

export const decimal = Object.freeze({
  normalize: normalizeDecimal,
  add: addDecimal,
  subtract: subtractDecimal,
  multiply: multiplyDecimal,
  divide: divideDecimal,
  compare: compareDecimal,
  round: roundDecimal,
})
