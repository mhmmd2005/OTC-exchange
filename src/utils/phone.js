export function normalizePhone(value = '') {
  const raw = String(value || '').trim()
  if (!raw) return ''

  const digits = raw.replace(/\D/g, '')
  if (!digits) return ''

  if (digits.startsWith('98') && digits.length === 11) {
    return `+${digits}`
  }

  if (digits.startsWith('0') && digits.length === 11) {
    return `+98${digits.slice(1)}`
  }

  if (digits.length === 10 && digits.startsWith('9')) {
    return `+98${digits}`
  }

  if (raw.startsWith('+')) {
    return `+${digits}`
  }

  return `+${digits}`
}

export function isValidIranianMobile(value = '') {
  const normalized = normalizePhone(value)
  return /^\+989\d{9}$/.test(normalized)
}
