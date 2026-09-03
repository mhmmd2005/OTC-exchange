<script setup>
import {computed} from 'vue'
import {
  ChevronDown,
  LogOut,
  MoonStar,
  Search,
  ShieldCheck,
  SunMedium,
  Menu,
} from 'lucide-vue-next'
import {useRoute, useRouter} from 'vue-router'
import {useAuthStore} from '../stores/auth'
import {useTheme} from '../composables/useTheme'
import NotificationCenter from './NotificationCenter.vue'

const emit = defineEmits(['toggle-sidebar', 'toggle-collapse'])

const auth = useAuthStore()
const route = useRoute()
const router = useRouter()

const {isDark, toggleTheme} = useTheme()

const userName = computed(() => auth.user?.fullName || 'کاربر')

/*
|--------------------------------------------------------------------------
| Page Titles
|--------------------------------------------------------------------------
| Only the current page title is shown in the header.
| No duplicated "پلتفرم OTC" kicker.
|--------------------------------------------------------------------------
*/

const pageMap = {
  '/dashboard': 'داشبورد',
  '/otc': 'میز OTC',
  '/orders': 'سفارش‌ها',
  '/trades': 'معاملات',
  '/wallet': 'کیف پول',
  '/transactions': 'تراکنش‌ها',
  '/kyc': 'احراز هویت',
  '/security': 'امنیت',
  '/support': 'مرکز پشتیبانی',
  '/settings': 'تنظیمات',
  '/deposit': 'واریز',
  '/withdraw': 'برداشت',
}

/*
|--------------------------------------------------------------------------
| Dynamic Current Page
|--------------------------------------------------------------------------
| Supports nested routes such as:
| /wallet/:id
|--------------------------------------------------------------------------
*/

const currentPage = computed(() => {
  const path = route.path

  if (pageMap[path]) {
    return pageMap[path]
  }

  if (path.startsWith('/wallet/')) {
    return 'جزئیات کیف پول'
  }

  if (path.startsWith('/trades/')) {
    return 'جزئیات معامله'
  }

  if (path.startsWith('/orders/')) {
    return 'جزئیات سفارش'
  }

  if (path.startsWith('/transactions/')) {
    return 'جزئیات تراکنش'
  }

  if (path.startsWith('/support/')) {
    return 'مرکز پشتیبانی'
  }

  return 'داشبورد'
})
</script>

<template>
  <header class="header">
    <!-- =====================================================
         LEFT SIDE
    ====================================================== -->

    <div class="header-left">
      <!-- Mobile menu -->
      <button
          class="icon-btn mobile-toggle"
          type="button"
          aria-label="باز کردن منو"
          title="باز کردن منو"
          @click="emit('toggle-sidebar')"
      >
        <Menu :size="18"/>
      </button>

      <!-- Desktop sidebar toggle -->
      <button
          class="icon-btn desktop-toggle"
          type="button"
          aria-label="جمع یا باز کردن سایدبار"
          title="جمع یا باز کردن سایدبار"
          @click="emit('toggle-collapse')"
      >
        <Menu :size="18"/>
      </button>

      <!-- Current page -->
      <div class="page-title-box">
        <h1>{{ currentPage }}</h1>
      </div>
    </div>

    <!-- =====================================================
         RIGHT SIDE
    ====================================================== -->

    <div class="header-right">

      <!-- Market status -->
      <div class="header-market">
        <span class="market-live-dot"/>
        <span>بازار فعال</span>
      </div>

      <!-- Search -->
      <div class="search-box">
        <Search :size="16"/>

        <input
            type="text"
            placeholder="جستجو یا رفتن به..."
            aria-label="جستجو یا رفتن به"
        />
      </div>

      <!-- KYC -->
      <div class="header-badge premium-badge">
        <ShieldCheck :size="14"/>

        <span>
          KYC:
          {{ auth.user?.kycStatus || 'در حال بررسی' }}
        </span>
      </div>

      <!-- Notifications -->
      <NotificationCenter/>

      <!-- Theme -->
      <button
          class="icon-btn"
          type="button"
          :title="isDark ? 'حالت روشن' : 'حالت تیره'"
          :aria-label="isDark ? 'تغییر به حالت روشن' : 'تغییر به حالت تیره'"
          @click="toggleTheme()"
      >
        <SunMedium v-if="isDark" :size="18"/>
        <MoonStar v-else :size="18"/>
      </button>

      <!-- User -->
      <div class="user-chip">
        <div class="avatar">
          {{ auth.user?.avatar || 'U' }}
        </div>

        <div class="user-copy">
          <div class="user-name">
            {{ userName }}
          </div>

          <div class="muted-small">
            {{ auth.user?.kycLevel || 'سطح ۱' }}
          </div>
        </div>

        <ChevronDown
            :size="16"
            class="user-chevron"
        />
      </div>

      <!-- Logout -->
      <button
          class="ghost-btn danger-btn"
          type="button"
          @click="auth.logout(); router.push('/login')"
      >
        <LogOut :size="16"/>
        <span>خروج</span>
      </button>

    </div>
  </header>
</template>