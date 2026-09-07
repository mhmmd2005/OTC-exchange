export function normalizeDigits(value: string): string {
  return value
    .replace(/[۰-۹]/g, digit => String('۰۱۲۳۴۵۶۷۸۹'.indexOf(digit)))
    .replace(/[٠-٩]/g, digit => String('٠١٢٣٤٥٦٧٨٩'.indexOf(digit)))
}

export function normalizeMobile(value: string): string {
  let mobile = normalizeDigits(value).replace(/\D/g, '')

  if (mobile.startsWith('0098')) mobile = `0${mobile.slice(4)}`
  else if (mobile.startsWith('98')) mobile = `0${mobile.slice(2)}`
  else if (mobile.length === 10 && mobile.startsWith('9')) mobile = `0${mobile}`

  return mobile.slice(0, 11)
}

export function isValidMobile(value: string): boolean {
  return /^09\d{9}$/.test(normalizeMobile(value))
}

export function maskMobile(value: string): string {
  const mobile = normalizeMobile(value)
  if (!isValidMobile(mobile)) return 'شماره موبایل شما'
  return `${mobile.slice(0, 4)} *** ${mobile.slice(-4)}`
}

export function passwordValidation(value: string): string {
  if (!value) return 'رمز عبور را وارد کنید.'
  if (value.length < 8) return 'رمز عبور باید حداقل ۸ نویسه باشد.'
  return ''
}

export function queryValue(value: unknown): string {
  return Array.isArray(value) ? String(value[0] ?? '') : String(value ?? '')
}

/**
 * Auth redirects are deliberately constrained to authenticated application
 * routes. Keeping this check in one place prevents query-string return paths
 * from becoming an open redirect.
 */
export function safeAppRedirect(value: unknown, fallback = '/app/dashboard'): string {
  const candidate = queryValue(value).trim()
  if (!candidate.startsWith('/app/') || candidate.startsWith('/app//') || candidate.includes('\\')) return fallback

  try {
    const base = new URL('https://rosha.invalid')
    const target = new URL(candidate, base)
    return target.origin === base.origin && target.pathname.startsWith('/app/')
      ? `${target.pathname}${target.search}${target.hash}`
      : fallback
  } catch {
    return fallback
  }
}

export function mockDelay(milliseconds = 700): Promise<void> {
  return new Promise(resolve => window.setTimeout(resolve, milliseconds))
}
