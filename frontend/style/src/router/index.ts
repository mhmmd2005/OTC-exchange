import { createRouter, createWebHistory } from 'vue-router';
import MainRoutes from './MainRoutes';
import AuthRoutes from './AuthRoutes';
import { useAuthStore } from '@/stores/auth';

export const router = createRouter({
  history: createWebHistory(import.meta.env.BASE_URL),
  routes: [
    { path: '/', redirect: '/login' },
    MainRoutes,
    AuthRoutes,
    { path: '/:pathMatch(.*)*', component: () => import('@/views/authentication/Error.vue') },
  ],
});

const PUBLIC_NAMES = new Set([
  'Side Login', 'Side Register', 'Side Forgot Password',
  'VerifyEmail', 'ResetPasswordConfirm',
  'Landing Page', 'FrontPage', 'About Us', 'Contact',
  'Pricing1', 'Portfolio', 'Blog', 'Blog Details',
  'Maintenance', 'Error',
]);

router.beforeEach(async (to, from, next) => {
  const auth = useAuthStore();

  // 2FA gate (must run first)
  if (to.matched.some((r) => r.meta?.requiresTwoFATicket === true)) {
    const raw = typeof window !== 'undefined' ? sessionStorage.getItem('twofa_ctx') : null;
    let ctx: { ticket: string; ts: number } | null = null;

    try { ctx = raw ? JSON.parse(raw) : null } catch {}

    // if ctx missing, fallback to legacy twofa_ticket and build ctx
    if (!ctx) {
      const ticket = typeof window !== 'undefined' ? sessionStorage.getItem('twofa_ticket') : null;
      if (ticket) {
        ctx = { ticket, ts: Date.now() };
        try { sessionStorage.setItem('twofa_ctx', JSON.stringify(ctx)) } catch {}
      }
    }

    if (auth.isAuthenticated) {
      return next({ path: '/dashboard1' });
    }

    const fresh = ctx && ctx.ticket && (Date.now() - ctx.ts) <= 5 * 60 * 1000;
    if (!fresh) {
      try {
        sessionStorage.removeItem('twofa_ctx');
        sessionStorage.removeItem('twofa_ticket');
      } catch {}
      return next({ path: '/login', query: { notice: 'twofa' } });
    }

    return next();
  }

  // block login/register when authenticated
  if ((to.path === '/login' || to.path === '/register') && auth.isAuthenticated) {
    return next({ path: '/dashboard1' });
  }

  // normal auth protection
  const needsAuth = to.matched.some((r) => r.meta?.requiresAuth === true);
  const isPublic =
    !needsAuth ||
    PUBLIC_NAMES.has(to.name as string) ||
    /^\/(login|register|forgot-password)$/.test(to.path) ||
    /^\/verify-email\/[^/]+\/?$/.test(to.path) ||
    /^\/reset-password-confirm\/[^/]+\/?$/.test(to.path);

  if (isPublic) return next();

  const hasAccess = !!auth.user?.access || auth.isAuthenticated;
  if (hasAccess) return next();

  if (auth.user?.refresh) {
    const newAccess = await auth.tryRefresh();
    if (newAccess) return next();
  }

  auth.returnUrl = to.fullPath;
  return next('/login');
});

export default router;
