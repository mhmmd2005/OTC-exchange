import { normalizeDigits } from './formatters'

export function isValidIranianCardNumber(value: string): boolean {
  const digits = normalizeDigits(value).replace(/\D/g, '')
  if (!/^\d{16}$/.test(digits) || /^0{8}/.test(digits) || /0{8}$/.test(digits)) return false

  const checksum = [...digits].reduce((sum, digit, index) => {
    let product = Number(digit) * (index % 2 === 0 ? 2 : 1)
    if (product > 9) product -= 9
    return sum + product
  }, 0)
  return checksum % 10 === 0
}

export function isValidIranianIban(value: string): boolean {
  const compact = normalizeDigits(value).toUpperCase().replace(/\s/g, '')
  if (!/^IR\d{24}$/.test(compact)) return false

  // ISO 13616: move IR + check digits to the end, map I=18 and R=27,
  // then calculate mod 97 incrementally so the value never becomes unsafe.
  const rearranged = `${compact.slice(4)}1827${compact.slice(2, 4)}`
  let remainder = 0
  for (const digit of rearranged) remainder = (remainder * 10 + Number(digit)) % 97
  return remainder === 1
}
