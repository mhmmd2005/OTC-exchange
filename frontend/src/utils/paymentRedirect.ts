export type PaymentRedirectBlockReason = 'invalid' | 'mock-disabled' | 'unapproved'

export type PaymentRedirectDecision =
  | { kind: 'internal-mock'; target: string }
  | { kind: 'external'; href: string }
  | { kind: 'blocked'; reason: PaymentRedirectBlockReason }

export function resolvePaymentRedirect(
  rawUrl: string,
  currentOrigin: string,
  mockEnabled: boolean,
  approvedHosts: ReadonlySet<string>,
): PaymentRedirectDecision {
  let destination: URL
  try {
    destination = new URL(rawUrl, currentOrigin)
  } catch {
    return { kind: 'blocked', reason: 'invalid' }
  }

  const isInternalMockPath = destination.origin === currentOrigin
    && /^\/mock-payment\/[A-Za-z0-9_-]+\/?$/.test(destination.pathname)
  if (isInternalMockPath) {
    return mockEnabled
      ? { kind: 'internal-mock', target: `${destination.pathname}${destination.search}` }
      : { kind: 'blocked', reason: 'mock-disabled' }
  }

  const isApprovedHost = destination.origin === currentOrigin
    || approvedHosts.has(destination.hostname.toLowerCase())
  if (
    destination.protocol !== 'https:'
    || Boolean(destination.port && destination.port !== '443')
    || Boolean(destination.username)
    || Boolean(destination.password)
    || !isApprovedHost
  ) {
    return { kind: 'blocked', reason: 'unapproved' }
  }

  return { kind: 'external', href: destination.href }
}

