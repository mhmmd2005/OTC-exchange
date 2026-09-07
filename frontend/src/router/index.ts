import { createRouter, createWebHistory, type RouteRecordRaw } from 'vue-router'
import { useAuthStore } from '@/stores/auth'
import { isMockApiEnabled } from '@/services/api'
import { prefersReducedMotion } from '@/utils/motion'

declare module 'vue-router' {
  interface RouteMeta {
    title?: string
    requiresAuth?: boolean
    guestOnly?: boolean
    requiresResetProof?: boolean
    mobileNav?: 'home' | 'trade' | 'wallet' | 'orders' | 'more'
    mobileHeader?: 'default' | 'contextual'
  }
}

const authChildren: RouteRecordRaw[] = [
  { path: 'login', name: 'login', component: () => import('@/pages/auth/Login.vue'), meta: { title: 'ورود' } },
  { path: 'register', name: 'register', component: () => import('@/pages/auth/Register.vue'), meta: { title: 'ثبت‌نام' } },
  { path: 'verify', name: 'verify', component: () => import('@/pages/auth/Verify.vue'), meta: { title: 'تأیید شماره موبایل' } },
  { path: 'forgot-password', name: 'forgot-password', component: () => import('@/pages/auth/ForgotPassword.vue'), meta: { title: 'بازیابی رمز عبور' } },
  { path: 'reset-password', name: 'reset-password', component: () => import('@/pages/auth/ResetPassword.vue'), meta: { title: 'تنظیم رمز جدید', requiresResetProof: true } },
  { path: 'reset-success', name: 'reset-success', component: () => import('@/pages/auth/ResetSuccess.vue'), meta: { title: 'رمز عبور تغییر کرد' } },
  { path: 'session-expired', name: 'session-expired', component: () => import('@/pages/auth/SessionExpired.vue'), meta: { title: 'نشست منقضی شده' } },
]

const appChildren: RouteRecordRaw[] = [
  { path: 'dashboard', name: 'dashboard', component: () => import('@/pages/app/DashboardPage.vue'), meta: { title: 'داشبورد', mobileNav: 'home' } },
  { path: 'trade', name: 'trade', component: () => import('@/pages/app/TradePage.vue'), meta: { title: 'خرید و فروش', mobileNav: 'trade' } },
  { path: 'markets', name: 'markets', component: () => import('@/pages/app/MarketsPage.vue'), meta: { title: 'ارزها', mobileNav: 'more' } },
  { path: 'markets/:symbol', name: 'asset-detail', component: () => import('@/pages/app/AssetDetailPage.vue'), meta: { title: 'جزئیات ارز', mobileNav: 'more', mobileHeader: 'contextual' } },
  { path: 'wallet', name: 'wallet', component: () => import('@/pages/app/WalletPage.vue'), meta: { title: 'کیف پول', mobileNav: 'wallet' } },
  { path: 'wallet/:symbol', name: 'wallet-detail', component: () => import('@/pages/app/WalletDetailPage.vue'), meta: { title: 'جزئیات کیف پول', mobileNav: 'wallet', mobileHeader: 'contextual' } },
  { path: 'deposit/toman', name: 'toman-deposit', component: () => import('@/pages/app/TomanDepositPage.vue'), meta: { title: 'واریز تومان', mobileNav: 'wallet', mobileHeader: 'contextual' } },
  { path: 'withdraw/toman', name: 'toman-withdrawal', component: () => import('@/pages/app/TomanWithdrawalPage.vue'), meta: { title: 'برداشت تومان', mobileNav: 'wallet', mobileHeader: 'contextual' } },
  { path: 'deposit/crypto/:symbol?', name: 'crypto-deposit', component: () => import('@/pages/app/CryptoDepositPage.vue'), meta: { title: 'واریز رمزارز', mobileNav: 'wallet', mobileHeader: 'contextual' } },
  { path: 'withdraw/crypto/:symbol?', name: 'crypto-withdrawal', component: () => import('@/pages/app/CryptoWithdrawalPage.vue'), meta: { title: 'برداشت رمزارز', mobileNav: 'wallet', mobileHeader: 'contextual' } },
  { path: 'orders', name: 'orders', component: () => import('@/pages/app/OrdersPage.vue'), meta: { title: 'سفارش‌ها', mobileNav: 'orders' } },
  { path: 'orders/:id', name: 'order-detail', component: () => import('@/pages/app/OrderDetailPage.vue'), meta: { title: 'جزئیات سفارش', mobileNav: 'orders', mobileHeader: 'contextual' } },
  { path: 'transactions', name: 'transactions', component: () => import('@/pages/app/TransactionsPage.vue'), meta: { title: 'تراکنش‌ها', mobileNav: 'more' } },
  { path: 'bank-accounts', name: 'bank-accounts', component: () => import('@/pages/app/BankAccountsPage.vue'), meta: { title: 'حساب‌های بانکی', mobileNav: 'more' } },
  { path: 'verification', name: 'verification', component: () => import('@/pages/app/VerificationPage.vue'), meta: { title: 'احراز هویت', mobileNav: 'more' } },
  { path: 'notifications', name: 'notifications', component: () => import('@/pages/app/NotificationsPage.vue'), meta: { title: 'اعلان‌ها', mobileNav: 'more' } },
  { path: 'support', name: 'support', component: () => import('@/pages/app/SupportPage.vue'), meta: { title: 'پشتیبانی', mobileNav: 'more' } },
  { path: 'support/tickets/:id', name: 'ticket-detail', component: () => import('@/pages/app/TicketDetailPage.vue'), meta: { title: 'جزئیات درخواست', mobileNav: 'more', mobileHeader: 'contextual' } },
  { path: 'profile', name: 'profile', component: () => import('@/pages/app/ProfilePage.vue'), meta: { title: 'حساب کاربری', mobileNav: 'more' } },
  { path: 'security', name: 'security', component: () => import('@/pages/app/SecurityPage.vue'), meta: { title: 'امنیت', mobileNav: 'more' } },
  { path: 'settings', name: 'settings', component: () => import('@/pages/app/SettingsPage.vue'), meta: { title: 'تنظیمات', mobileNav: 'more' } },
]

const router = createRouter({
  history: createWebHistory(import.meta.env.BASE_URL),
  routes: [
    { path: '/', redirect: '/app/dashboard' },
    { path: '/auth', component: () => import('@/layouts/AuthShell.vue'), meta: { guestOnly: true }, children: authChildren },
    { path: '/legal/terms', name: 'legal-terms', component: () => import('@/pages/LegalPage.vue'), props: { document: 'terms' }, meta: { title: 'شرایط استفاده' } },
    { path: '/legal/privacy', name: 'legal-privacy', component: () => import('@/pages/LegalPage.vue'), props: { document: 'privacy' }, meta: { title: 'سیاست حریم خصوصی' } },
    { path: '/app', component: () => import('@/layouts/AppShell.vue'), redirect: '/app/dashboard', meta: { requiresAuth: true }, children: appChildren },
    ...(import.meta.env.DEV && import.meta.env.VITE_USE_MOCK_API === 'true'
      ? [{ path: '/mock-payment/:id', name: 'mock-payment', component: () => import('@/pages/MockPaymentPage.vue'), meta: { title: 'درگاه پرداخت آزمایشی' } }]
      : []),
    { path: '/:pathMatch(.*)*', name: 'not-found', component: () => import('@/pages/NotFoundPage.vue'), meta: { title: 'صفحه پیدا نشد' } },
  ],
  scrollBehavior: () => ({ top: 0, behavior: prefersReducedMotion() ? 'auto' : 'smooth' }),
})

router.beforeEach(async (to, from) => {
  const auth = useAuthStore()
  if (!auth.initialized) await auth.hydrate()
  const resetProofIsValid = Boolean(
    auth.passwordResetProof
    && Number.isFinite(Date.parse(auth.passwordResetProof.expiresAt))
    && Date.parse(auth.passwordResetProof.expiresAt) > Date.now(),
  )
  if (auth.passwordResetProof && !resetProofIsValid) auth.clearPasswordResetProof()
  if (to.meta.requiresResetProof && !resetProofIsValid) {
    return { name: 'forgot-password', query: { proof: 'expired' } }
  }
  if (
    to.name === 'verify'
    && to.query.purpose === 'reset_password'
    && resetProofIsValid
  ) {
    // A browser Back action from the reset form targets the now-consumed OTP
    // screen. Cancel that pop navigation so the verified reset proof and form
    // stay intact; other attempts to open the stale OTP route are replaced.
    if (from.name === 'reset-password') return false
    return { name: 'reset-password', replace: true }
  }
  if (to.meta.requiresAuth && !isMockApiEnabled && !auth.isAuthenticated) {
    return { name: 'login', query: { redirect: to.fullPath } }
  }
  if (to.meta.guestOnly && !isMockApiEnabled && auth.isAuthenticated && to.name !== 'verify') return { name: 'dashboard' }
  return true
})

router.afterEach((to) => {
  document.title = `${to.meta.title || 'روشا'} | روشا`
})

export default router
