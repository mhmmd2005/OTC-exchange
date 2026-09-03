<script setup>
import { computed, ref } from 'vue'
import {
  Bell,
  Check,
  Palette,
  RefreshCcw,
  Save,
  ShieldCheck,
  SlidersHorizontal,
  User,
} from 'lucide-vue-next'
import { mockUser } from '../mock/data'
import { useTheme } from '../composables/useTheme'
import { useNotificationStore } from '../stores/notification'
import PremiumSelect from '../components/PremiumSelect.vue'

const notification = useNotificationStore()
const { theme } = useTheme()

const sections = [
  { key: 'profile', label: 'حساب کاربری', icon: User },
  { key: 'appearance', label: 'ظاهر', icon: Palette },
  { key: 'notifications', label: 'اعلان‌ها', icon: Bell },
  { key: 'preferences', label: 'ترجیحات', icon: SlidersHorizontal },
]

const defaultSettings = {
  theme: 'dark',
  language: 'fa',
  notifications: {
    transactions: true,
    security: true,
    account: true,
    system: false,
  },
  preferences: {
    assetView: 'تومان',
    timezone: 'Asia/Tehran',
  },
}

const savedSettings = ref({ ...defaultSettings })
const activeSection = ref('profile')
const language = ref('fa')
const assetView = ref('تومان')
const timezone = ref('Asia/Tehran')
const notifications = ref({ ...defaultSettings.notifications })
const authUser = mockUser

const themeValue = computed({
  get: () => theme.value,
  set: (value) => {
    theme.value = value
    document.documentElement.setAttribute('data-theme', value)
    localStorage.setItem('otc-theme', value)
  },
})

const unsaved = computed(() => {
  const current = {
    theme: themeValue.value,
    language: language.value,
    notifications: notifications.value,
    preferences: { assetView: assetView.value, timezone: timezone.value },
  }

  return JSON.stringify(current) !== JSON.stringify(savedSettings.value)
})

const profile = ref({
  fullName: authUser.fullName,
  email: authUser.email,
  phone: authUser.phone,
})

function getStoredSettings() {
  const stored = JSON.parse(localStorage.getItem('otc-settings') || 'null')
  if (!stored) return

  if (stored.theme) themeValue.value = stored.theme
  if (stored.language) language.value = stored.language
  if (stored.notifications) notifications.value = { ...defaultSettings.notifications, ...stored.notifications }
  if (stored.preferences) {
    assetView.value = stored.preferences.assetView || defaultSettings.preferences.assetView
    timezone.value = stored.preferences.timezone || defaultSettings.preferences.timezone
  }

  savedSettings.value = {
    theme: themeValue.value,
    language: language.value,
    notifications: { ...notifications.value },
    preferences: { assetView: assetView.value, timezone: timezone.value },
  }
}

function handleSave() {
  const payload = {
    theme: themeValue.value,
    language: language.value,
    notifications: { ...notifications.value },
    preferences: { assetView: assetView.value, timezone: timezone.value },
  }

  localStorage.setItem('otc-settings', JSON.stringify(payload))
  savedSettings.value = JSON.parse(JSON.stringify(payload))
  notification.addToast({
    title: 'تنظیمات ذخیره شد',
    text: 'تغییرات حساب کاربری با موفقیت اعمال شد.',
    type: 'success',
  })
}

function handleReset() {
  themeValue.value = defaultSettings.theme
  language.value = defaultSettings.language
  notifications.value = { ...defaultSettings.notifications }
  assetView.value = defaultSettings.preferences.assetView
  timezone.value = defaultSettings.preferences.timezone
  localStorage.setItem('otc-settings', JSON.stringify({
    theme: themeValue.value,
    language: language.value,
    notifications: { ...notifications.value },
    preferences: { assetView: assetView.value, timezone: timezone.value },
  }))
  savedSettings.value = {
    theme: themeValue.value,
    language: language.value,
    notifications: { ...notifications.value },
    preferences: { assetView: assetView.value, timezone: timezone.value },
  }
  notification.addToast({
    title: 'تنظیمات بازنشانی شد',
    text: 'مقادیر پیش‌فرض دوباره اعمال شد.',
    type: 'warning',
  })
}

function toggleSetting(key) {
  notifications.value[key] = !notifications.value[key]
}

function toStatusClass(value) {
  if (value === 'تأیید شده' || value === 'فعال') return 'success'
  if (value === 'در انتظار بررسی' || value === 'غیرفعال') return 'warning'
  return 'neutral'
}

getStoredSettings()
</script>

<template>
  <div class="settings-shell">
    <header class="page-header">
      <div>
        <div class="page-kicker">پلتفرم OTC</div>
        <h1 class="page-title">تنظیمات</h1>
        <p class="page-subtitle">مدیریت تنظیمات و ترجیحات حساب کاربری</p>
      </div>

      <div v-if="unsaved" class="header-status">
        <Check :size="14" />
        تغییرات ذخیره نشده است
      </div>
    </header>

    <main class="settings-layout">
      <aside class="panel-surface settings-nav">
        <div class="nav-label">منو</div>
        <button
          v-for="section in sections"
          :key="section.key"
          type="button"
          :class="['nav-item', { active: activeSection === section.key }]"
          @click="activeSection = section.key"
        >
          <component :is="section.icon" :size="17" />
          <span>{{ section.label }}</span>
        </button>
      </aside>

      <section class="settings-panel panel-surface">
        <div v-if="activeSection === 'profile'" class="settings-content">
          <div class="section-header">
            <div>
              <div class="panel-label">حساب کاربری</div>
              <h2>اطلاعات شخصی</h2>
            </div>
          </div>

          <div class="profile-box">
            <div class="profile-avatar">{{ authUser.avatar }}</div>
            <div class="profile-meta">
              <h3>{{ profile.fullName }}</h3>
              <p>@{{ authUser.username }}</p>
            </div>
            <div class="kyc-chip status-badge success">{{ authUser.kycStatus }}</div>
          </div>

          <div class="info-grid">
            <label class="field">
              <span>نام کامل</span>
              <input v-model="profile.fullName" class="premium-input" type="text" placeholder="نام کامل" />
            </label>
            <label class="field">
              <span>ایمیل</span>
              <input v-model="profile.email" class="premium-input" type="email" placeholder="ایمیل" />
            </label>
            <label class="field">
              <span>تلفن</span>
              <input v-model="profile.phone" class="premium-input" type="tel" placeholder="تلفن" />
            </label>
          </div>

          <div class="shortcut-row">
            <button type="button" class="shortcut-button" @click="$router.push('/security')">
              <ShieldCheck :size="17" />
              <span>امنیت حساب</span>
            </button>
            <button type="button" class="shortcut-button" @click="$router.push('/kyc')">
              <Check :size="17" />
              <span>احراز هویت</span>
            </button>
          </div>
        </div>

        <div v-else-if="activeSection === 'appearance'" class="settings-content">
          <div class="section-header">
            <div>
              <div class="panel-label">ظاهر</div>
              <h2>ظاهر و زبان</h2>
            </div>
          </div>

          <div class="stack-block">
            <div class="row-panel">
              <div class="row-copy">
                <strong>تم</strong>
                <small>حالت نمایش برنامه</small>
              </div>
              <div class="segmented-control">
                <button :class="['segment', { active: themeValue.value === 'dark' } ]" type="button" @click="themeValue = 'dark'">تیره</button>
                <button :class="['segment', { active: themeValue.value === 'light' } ]" type="button" @click="themeValue = 'light'">روشن</button>
              </div>
            </div>

            <div class="row-panel">
              <div class="row-copy">
                <strong>زبان</strong>
                <small>زبان رابط کاربری</small>
              </div>
              <div class="field compact-field">
                <PremiumSelect v-model="language" :options="[
                  { value: 'fa', label: 'فارسی' },
                  { value: 'en', label: 'English' },
                ]" placeholder="زبان" />
              </div>
            </div>
          </div>
        </div>

        <div v-else-if="activeSection === 'notifications'" class="settings-content">
          <div class="section-header">
            <div>
              <div class="panel-label">اعلان‌ها</div>
              <h2>پیش‌تنظیم‌های هشدار</h2>
            </div>
          </div>

          <div class="toggle-list">
            <div v-for="item in [
              { key: 'transactions', title: 'اعلان‌های تراکنش', caption: 'دریافت اعلان‌های واریز، برداشت و سفارش‌ها' },
              { key: 'security', title: 'اعلان‌های امنیتی', caption: 'هشدارهای مهم حساب و ورود جدید' },
              { key: 'account', title: 'اعلان‌های حساب', caption: 'به‌روزرسانی‌های وضعیت احراز هویت و حساب' },
              { key: 'system', title: 'اعلان‌های سیستم', caption: 'اطلاع‌رسانی درباره بروزرسانی‌ها و پشتیبانی' }
            ]" :key="item.key" class="toggle-row">
              <div class="row-copy">
                <strong>{{ item.title }}</strong>
                <small>{{ item.caption }}</small>
              </div>
              <button
                type="button"
                :class="['toggle', { on: notifications[item.key] } ]"
                :aria-label="item.title"
                @click="toggleSetting(item.key)"
              >
                <span class="toggle-thumb" />
              </button>
            </div>
          </div>
        </div>

        <div v-else class="settings-content">
          <div class="section-header">
            <div>
              <div class="panel-label">ترجیحات</div>
              <h2>نمایش و تنظیمات حساب</h2>
            </div>
          </div>

          <div class="stack-block">
            <div class="row-panel">
              <div class="row-copy">
                <strong>نمایش ارزش دارایی‌ها</strong>
                <small>واحد محاسبه‌ی پیش‌فرض</small>
              </div>
              <div class="field compact-field">
                <PremiumSelect v-model="assetView" :options="[
                  { value: 'تومان', label: 'تومان' },
                  { value: 'USDT', label: 'USDT' },
                ]" placeholder="واحد نمایش" />
              </div>
            </div>

            <div class="row-panel">
              <div class="row-copy">
                <strong>منطقه زمانی</strong>
                <small>برای زمان‌بندی تراکنش‌ها و گزارش‌ها</small>
              </div>
              <div class="field compact-field">
                <PremiumSelect v-model="timezone" :options="[
                  { value: 'Asia/Tehran', label: 'ایران (UTC+3:30)' },
                  { value: 'UTC', label: 'UTC' },
                ]" placeholder="منطقه زمانی" />
              </div>
            </div>
          </div>
        </div>

        <div class="settings-actions">
          <button type="button" class="secondary-button" @click="handleReset">
            <RefreshCcw :size="16" />
            بازنشانی
          </button>
          <button type="button" class="primary-button" @click="handleSave">
            <Save :size="16" />
            ذخیره تغییرات
          </button>
        </div>
      </section>
    </main>
  </div>
</template>

<style scoped>
.settings-shell {
  display: flex;
  flex-direction: column;
  gap: 20px;
}

.page-header {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 18px;
  padding: 4px 4px 0;
}

.page-kicker {
  color: #f1d089;
  font-size: 0.72rem;
  font-weight: 700;
  letter-spacing: 0.08em;
  text-transform: uppercase;
}

.page-title {
  margin: 10px 0 0;
  font-size: clamp(2rem, 3vw, 2.7rem);
  line-height: 1.15;
  letter-spacing: -0.05em;
  color: var(--text);
}

.page-subtitle {
  margin: 8px 0 0;
  color: var(--text-muted);
  font-size: 0.85rem;
}

.header-status {
  display: inline-flex;
  align-items: center;
  gap: 8px;
  padding: 8px 12px;
  border-radius: 999px;
  background: rgba(212, 169, 90, 0.08);
  border: 1px solid rgba(212, 169, 90, 0.2);
  color: var(--primary-2);
  font-size: 0.74rem;
  font-weight: 700;
}

.settings-layout {
  display: grid;
  grid-template-columns: 240px minmax(0, 1fr);
  gap: 20px;
  align-items: start;
}

.settings-nav,
.settings-panel {
  background: var(--surface-card);
  border: 1px solid var(--border-subtle);
  border-radius: 24px;
  box-shadow: var(--shadow-card);
  backdrop-filter: blur(20px);
}

.settings-nav {
  padding: 18px 14px;
  position: sticky;
  top: 24px;
}

.nav-label {
  padding: 0 10px 10px;
  color: var(--text-muted);
  font-size: 0.68rem;
  font-weight: 700;
  letter-spacing: 0.08em;
  text-transform: uppercase;
}

.nav-item {
  width: 100%;
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 12px 12px;
  border: 1px solid transparent;
  border-radius: 14px;
  background: transparent;
  color: var(--text-soft);
  font-size: 0.9rem;
  font-weight: 600;
  text-align: right;
  transition: all 0.2s ease;
}

.nav-item + .nav-item {
  margin-top: 8px;
}

.nav-item.active {
  background: rgba(212, 169, 90, 0.08);
  border-color: rgba(212, 169, 90, 0.2);
  color: var(--primary-2);
  box-shadow: inset 0 0 0 1px rgba(212, 169, 90, 0.08);
}

.nav-item:hover {
  background: rgba(255, 255, 255, 0.02);
}

.settings-panel {
  padding: 26px;
}

.settings-content {
  display: flex;
  flex-direction: column;
  gap: 20px;
}

.section-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
}

.panel-label {
  color: var(--text-muted);
  font-size: 0.68rem;
  font-weight: 700;
  letter-spacing: 0.08em;
  text-transform: uppercase;
}

.section-header h2 {
  margin: 6px 0 0;
  font-size: clamp(1.35rem, 2vw, 1.8rem);
  letter-spacing: -0.04em;
  color: var(--text);
}

.profile-box {
  display: flex;
  align-items: center;
  gap: 16px;
  padding: 18px 20px;
  background: rgba(255, 255, 255, 0.02);
  border: 1px solid rgba(255, 255, 255, 0.06);
  border-radius: 18px;
}

.profile-avatar {
  width: 52px;
  height: 52px;
  border-radius: 16px;
  display: grid;
  place-items: center;
  background: linear-gradient(135deg, rgba(212, 169, 90, 0.18), rgba(58, 111, 248, 0.14));
  border: 1px solid rgba(212, 169, 90, 0.22);
  font-size: 0.9rem;
  font-weight: 800;
  color: var(--primary-2);
}

.profile-meta {
  flex: 1;
}

.profile-meta h3 {
  margin: 0;
  font-size: 1.1rem;
}

.profile-meta p {
  margin: 4px 0 0;
  color: var(--text-muted);
  font-size: 0.82rem;
}

.status-badge {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  min-height: 28px;
  padding: 0 10px;
  border-radius: 999px;
  font-size: 0.68rem;
  font-weight: 700;
}

.status-badge.success {
  background: rgba(22, 199, 132, 0.08);
  border: 1px solid rgba(22, 199, 132, 0.2);
  color: #8fe0bc;
}

.status-badge.warning {
  background: rgba(212, 169, 90, 0.08);
  border: 1px solid rgba(212, 169, 90, 0.2);
  color: #e7c678;
}

.status-badge.neutral {
  background: rgba(255, 255, 255, 0.04);
  border: 1px solid rgba(255, 255, 255, 0.08);
  color: var(--text-soft);
}

.info-grid {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 18px;
}

.field {
  display: flex;
  flex-direction: column;
  gap: 9px;
  min-width: 0;
}

.field span {
  color: var(--text-soft);
  font-size: 0.74rem;
  font-weight: 700;
}

.premium-input,
.premium-select {
  width: 100%;
  min-height: 48px;
  padding: 0 14px;
  border: 1px solid rgba(255, 255, 255, 0.08);
  border-radius: 14px;
  background: rgba(13, 23, 40, 0.9);
  color: var(--text);
  outline: none;
  transition: border-color 0.2s ease, box-shadow 0.2s ease;
}

.premium-input::placeholder {
  color: var(--text-muted);
}

.premium-input:focus,
.premium-select:focus {
  border-color: rgba(212, 169, 90, 0.6);
  box-shadow: 0 0 0 3px rgba(212, 169, 90, 0.14);
}

.compact-field {
  min-width: 180px;
}

.shortcut-row {
  display: flex;
  flex-wrap: wrap;
  gap: 12px;
}

.shortcut-button {
  display: inline-flex;
  align-items: center;
  gap: 8px;
  padding: 10px 14px;
  border-radius: 12px;
  border: 1px solid rgba(255, 255, 255, 0.08);
  background: rgba(255, 255, 255, 0.02);
  color: var(--text);
  font-weight: 700;
}

.stack-block,
.toggle-list {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.row-panel,
.toggle-row {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 14px;
  padding: 16px 18px;
  border-radius: 18px;
  background: rgba(255, 255, 255, 0.02);
  border: 1px solid rgba(255, 255, 255, 0.06);
}

.row-copy {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.row-copy strong {
  color: var(--text);
  font-size: 0.96rem;
}

.row-copy small {
  color: var(--text-muted);
  font-size: 0.76rem;
}

.segmented-control {
  display: inline-flex;
  gap: 6px;
  padding: 6px;
  border-radius: 12px;
  background: rgba(255, 255, 255, 0.02);
  border: 1px solid rgba(255, 255, 255, 0.06);
}

.segment {
  padding: 8px 12px;
  border-radius: 10px;
  border: 1px solid transparent;
  background: transparent;
  color: var(--text-soft);
  font-weight: 700;
}

.segment.active {
  background: rgba(212, 169, 90, 0.08);
  border-color: rgba(212, 169, 90, 0.18);
  color: var(--primary-2);
}

.toggle {
  position: relative;
  width: 48px;
  height: 28px;
  border-radius: 999px;
  border: 1px solid rgba(255, 255, 255, 0.08);
  background: rgba(255, 255, 255, 0.06);
  transition: all 0.25s ease;
}

.toggle.on {
  background: rgba(212, 169, 90, 0.12);
  border-color: rgba(212, 169, 90, 0.2);
}

.toggle-thumb {
  position: absolute;
  top: 3px;
  right: 4px;
  width: 18px;
  height: 18px;
  border-radius: 50%;
  background: rgba(255, 255, 255, 0.7);
  transition: all 0.25s ease;
}

.toggle.on .toggle-thumb {
  right: 24px;
  background: var(--primary-2);
}

.settings-actions {
  display: flex;
  justify-content: flex-end;
  gap: 12px;
  padding-top: 12px;
  border-top: 1px solid rgba(255, 255, 255, 0.06);
}

.primary-button,
.secondary-button {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
  min-height: 46px;
  padding: 0 18px;
  border-radius: 12px;
  border: 1px solid transparent;
  font-weight: 800;
  transition: all 0.2s ease;
}

.primary-button {
  background: linear-gradient(135deg, rgba(212, 169, 90, 0.2), rgba(212, 169, 90, 0.08));
  border-color: rgba(212, 169, 90, 0.26);
  color: #f3d79a;
}

.secondary-button {
  background: rgba(255, 255, 255, 0.02);
  border-color: rgba(255, 255, 255, 0.08);
  color: var(--text);
}

.primary-button:hover,
.secondary-button:hover,
.shortcut-button:hover,
.nav-item:hover,
.segment:hover {
  transform: translateY(-1px);
}

@media (max-width: 1024px) {
  .settings-layout {
    grid-template-columns: 1fr;
  }

  .settings-nav {
    position: static;
  }
}

@media (max-width: 768px) {
  .page-header {
    flex-direction: column;
    align-items: flex-start;
  }

  .settings-panel {
    padding: 20px 16px;
  }

  .info-grid {
    grid-template-columns: 1fr;
  }

  .profile-box,
  .row-panel,
  .toggle-row {
    flex-direction: column;
    align-items: flex-start;
  }

  .settings-actions {
    flex-direction: column-reverse;
  }

  .primary-button,
  .secondary-button {
    width: 100%;
  }
}
</style>
