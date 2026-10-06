export type PaymentRedirectBlockReason =
  | 'invalid'
  | 'mock-disabled'
  | 'unapproved'

export type PaymentRedirectDecision =
  | { kind: 'internal-mock'; target: string }
  | { kind: 'external'; href: string }
  | { kind: 'blocked'; reason: PaymentRedirectBlockReason }

const LOCALHOST_HOSTS = new Set([
  'localhost',
  '127.0.0.1',
  '[::1]',
])

const INTERNAL_PAYMENT_PATH =
  /^\/(?:payment-test|mock-payment)\/[A-Za-z0-9_-]+\/?$/

export function resolvePaymentRedirect(
  rawUrl: string,
  currentOrigin: string,
  mockEnabled: boolean,
  approvedHosts: ReadonlySet<string>,
): PaymentRedirectDecision {
  let destination: URL
  let current: URL

  try {
    destination = new URL(rawUrl, currentOrigin)
    current = new URL(currentOrigin)
  } catch {
    return {
      kind: 'blocked',
      reason: 'invalid',
    }
  }

  const currentHost = current.hostname.toLowerCase()
  const destinationHost = destination.hostname.toLowerCase()

  const isLocalhostPair =
    LOCALHOST_HOSTS.has(currentHost) &&
    LOCALHOST_HOSTS.has(destinationHost)

  const isInternalMockPath =
    INTERNAL_PAYMENT_PATH.test(destination.pathname) &&
    (
      destination.origin === currentOrigin ||
      isLocalhostPair
    )

  if (isInternalMockPath) {
    return mockEnabled
      ? {
          kind: 'internal-mock',
          target: `${destination.pathname}${destination.search}`,
        }
      : {
          kind: 'blocked',
          reason: 'mock-disabled',
        }
  }

  const isApprovedHost =
    destination.origin === currentOrigin ||
    approvedHosts.has(destinationHost)

  if (
    destination.protocol !== 'https:' ||
    Boolean(destination.port && destination.port !== '443') ||
    Boolean(destination.username) ||
    Boolean(destination.password) ||
    !isApprovedHost
  ) {
    return {
      kind: 'blocked',
      reason: 'unapproved',
    }
  }

  return {
    kind: 'external',
    href: destination.href,
  }
}