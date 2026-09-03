<script setup>
import { computed } from 'vue'
import { useRoute } from 'vue-router'
import {
  ArrowDownLeft,
  ArrowRightLeft,
  ArrowUpRight,
  BarChart3,
  ChevronLeft,
  ChevronRight,
  CreditCard,
  Gauge,
  LifeBuoy,
  LogOut,
  ReceiptText,
  Settings,
  Shield,
  ShieldCheck,
  Sparkles,
  Wallet,
} from 'lucide-vue-next'

const props = defineProps({ open: { type: Boolean, default: false }, collapsed: { type: Boolean, default: false } })
const emit = defineEmits(['close', 'toggle-collapse'])
const route = useRoute()

const sections = [
  {
    title: 'نمای کلی',
    items: [{ label: 'داشبورد', icon: Gauge, to: '/dashboard' }],
  },
  {
    title: 'معاملات',
    items: [
      { label: 'میز OTC', icon: BarChart3, to: '/otc' },
      { label: 'سفارش‌ها', icon: ReceiptText, to: '/orders' },
     {
  label: 'معاملات',
  icon: ArrowRightLeft,
  to: '/trades'
},
    ],
  },
  {
    title: 'دارایی‌ها',
    items: [
      { label: 'کیف پول', icon: Wallet, to: '/wallet' },
      { label: 'واریز', icon: ArrowDownLeft, to: '/deposit' },
      { label: 'برداشت', icon: ArrowUpRight, to: '/withdraw' },
      { label: 'تراکنش‌ها', icon: CreditCard, to: '/transactions' },
    ],
  },
  {
    title: 'حساب کاربری',
    items: [
      { label: 'احراز هویت', icon: ShieldCheck, to: '/kyc' },
      { label: 'امنیت', icon: Shield, to: '/security' },
      { label: 'تنظیمات', icon: Settings, to: '/settings' },
    ],
  },
  {
    title: 'پشتیبانی',
    items: [{ label: 'مرکز پشتیبانی', icon: LifeBuoy, to: '/support' }],
  },
]

const isActive = (to) => route.path === to || route.path.startsWith(`${to}/`)
const accountState = computed(() => (route.path === '/kyc' ? 'احراز هویت سطح ۲' : 'حساب فعال'))
</script>

<template>
  <aside :class="['sidebar', { open: props.open, collapsed: props.collapsed }]">
    <div class="sidebar-header">
      <div class="brand-wrap">
        <div class="brand-mark">
          <Sparkles :size="16" />
        </div>
        <div v-if="!props.collapsed" class="brand-copy">
          <span class="brand-name">OTC</span>
          <small>Institutional Desk</small>
        </div>
      </div>

      <button class="sidebar-collapse-btn" type="button" :title="props.collapsed ? 'باز کردن منو' : 'جمع کردن منو'" @click="emit('toggle-collapse')">
        <ChevronRight v-if="!props.collapsed" :size="16" />
        <ChevronLeft v-else :size="16" />
      </button>
    </div>

    <div class="sidebar-profile" v-if="!props.collapsed">
      <div class="profile-identity">
        <div class="profile-avatar">MG</div>
        <div class="profile-meta">
          <strong>مهدی قاسمی</strong>
          <span>m.ghasemi@otcdesk.ir</span>
        </div>
      </div>

      <div class="kyc-chip">
        <span class="kyc-dot" />
        احراز هویت شده
      </div>
    </div>

    <div class="sidebar-scroll">
      <nav class="sidebar-nav" aria-label="منوی اصلی">
        <template v-for="section in sections" :key="section.title">
          <div v-if="!props.collapsed" class="nav-section-title">{{ section.title }}</div>
          <router-link
            v-for="item in section.items"
            :key="item.to"
            :to="item.to"
            :class="['nav-item', { active: isActive(item.to) }]"
            :title="props.collapsed ? item.label : undefined"
            @click="emit('close')"
          >
            <span class="nav-icon">
              <component :is="item.icon" :size="18" />
            </span>
            <span class="nav-label">{{ item.label }}</span>
          </router-link>
        </template>
      </nav>

      <div class="sidebar-security" v-if="!props.collapsed">
        <div class="security-head">
          <span>امنیت حساب</span>
          <strong>۸۰٪</strong>
        </div>
        <div class="security-meter">
          <span style="width: 80%" />
        </div>
        <ul class="security-list">
          <li>✓ احراز هویت</li>
          <li>✓ ورود امن</li>
          <li>✓ 2FA فعال</li>
        </ul>
      </div>
    </div>

    <div class="sidebar-footer">
      <button type="button" class="sidebar-footer-btn secondary" @click="$router.push('/settings')">
        <Settings :size="15" />
        <span>تنظیمات</span>
      </button>
      <button type="button" class="sidebar-footer-btn danger" @click="$router.push('/login')">
        <LogOut :size="15" />
        <span>خروج</span>
      </button>
    </div>
  </aside>
</template>
