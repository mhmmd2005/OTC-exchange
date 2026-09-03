import { createRouter, createWebHistory } from 'vue-router'
import { useAuthStore } from '../stores/auth'
import DashboardLayout from '../layouts/DashboardLayout.vue'
import LoginView from '../views/LoginView.vue'
import DashboardView from '../views/DashboardView.vue'
import OtcView from '../views/OtcView.vue'
import OrdersView from '../views/OrdersView.vue'
import WalletView from '../views/WalletView.vue'
import WalletDetailView from '../views/WalletDetailView.vue'
import TransactionsView from '../views/TransactionsView.vue'
import KycView from '../views/KycView.vue'
import SecurityView from '../views/SecurityView.vue'
import SupportView from '../views/SupportView.vue'
import SettingsView from '../views/SettingsView.vue'
import DepositView from '../views/DepositView.vue'
import WithdrawView from '../views/WithdrawView.vue'
import TradesView from '../views/TradesView.vue'
import LandingView from '../views/LandingView.vue'
import RegisterView from '../views/RegisterView.vue'
import ForgotPasswordView from '../views/ForgotPasswordView.vue'
import ResetPasswordView from '../views/ResetPasswordView.vue'
import NotFoundView from '../views/NotFoundView.vue'

const routes = [
  { path: '/', name: 'landing', component: LandingView },
  { path: '/login', name: 'login', component: LoginView },
  { path: '/register', name: 'register', component: RegisterView },
  { path: '/forgot-password', name: 'forgot-password', component: ForgotPasswordView },
  { path: '/reset-password', name: 'reset-password', component: ResetPasswordView },
  {
    path: '/',
    component: DashboardLayout,
    meta: { requiresAuth: true },
    children: [
      { path: 'dashboard', name: 'dashboard', component: DashboardView },
      { path: 'otc', name: 'otc', component: OtcView },
      { path: 'orders', name: 'orders', component: OrdersView },
      { path: 'wallet', name: 'wallet', component: WalletView },
      { path: 'wallet/:id', name: 'wallet-detail', component: WalletDetailView },
      { path: 'deposit', name: 'deposit', component: DepositView },
      { path: 'withdraw', name: 'withdraw', component: WithdrawView },
      { path: 'transactions', name: 'transactions', component: TransactionsView },
      { path: 'kyc', name: 'kyc', component: KycView },
      { path: 'security', name: 'security', component: SecurityView },
      { path: 'support', name: 'support', component: SupportView },
      { path: 'settings', name: 'settings', component: SettingsView },
      { path: 'trades', name: 'trades', component: TradesView },
    ],
  },
  { path: '/:pathMatch(.*)*', name: 'not-found', component: NotFoundView },
]

const router = createRouter({ history: createWebHistory(), routes })
router.beforeEach((to, from, next) => {
  const auth = useAuthStore()
  if (to.meta.requiresAuth && !auth.isAuthenticated) {
    next('/login')
    return
  }
  if (to.path === '/' && auth.isAuthenticated) {
    next('/dashboard')
    return
  }
  if (to.path === '/login' && auth.isAuthenticated) {
    next('/dashboard')
    return
  }
  next()
})

export default router
