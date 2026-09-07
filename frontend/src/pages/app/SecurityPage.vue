<script setup lang="ts">
import { computed, defineAsyncComponent, onMounted, reactive, ref, watch } from 'vue'
import AppButton from '@/components/ui/AppButton.vue'
import AppCard from '@/components/ui/AppCard.vue'
import AppIcon from '@/components/ui/AppIcon.vue'
import AppInput from '@/components/ui/AppInput.vue'
import AppModal from '@/components/ui/AppModal.vue'
import AppSkeleton from '@/components/ui/AppSkeleton.vue'
import AppSwitch from '@/components/ui/AppSwitch.vue'
import CopyButton from '@/components/ui/CopyButton.vue'
import EmptyState from '@/components/ui/EmptyState.vue'
import PageHeader from '@/components/ui/PageHeader.vue'
import StatusBadge from '@/components/ui/StatusBadge.vue'
import QrCode from '@/components/wallet/QrCode.vue'
import { ApiError, securityService } from '@/services'
import type { ActiveSession, SecurityEvent, SecurityEventType, SecurityOverview, TwoFactorSetup } from '@/types'
import { formatPersianDateTime, formatRelativeTime, normalizeDigits, toPersianDigits } from '@/utils/formatters'

const DemoCodeHint = import.meta.env.DEV && import.meta.env.VITE_USE_MOCK_API === 'true'
  ? defineAsyncComponent(() => import('@/components/ui/DemoCodeHint.vue'))
  : null

type ConfirmationAction =
  | { kind: 'session'; session: ActiveSession }
  | { kind: 'other-sessions' }
  | { kind: 'disable-2fa' }
  | { kind: 'whitelist'; enabled: boolean }

const overview = ref<SecurityOverview | null>(null)
const sessions = ref<ActiveSession[]>([])
const events = ref<SecurityEvent[]>([])
const loading = ref(true)
const error = ref('')
const feedback = ref('')
const confirmation = ref<ConfirmationAction | null>(null)
const confirming = ref(false)

const passwordOpen = ref(false)
const changingPassword = ref(false)
const passwordError = ref('')
const passwordFields = reactive<Record<string, string>>({})
const passwordForm = reactive({ currentPassword: '', newPassword: '', newPasswordConfirmation: '' })

const twoFactorOpen = ref(false)
const twoFactorCode = ref('')
const twoFactorError = ref('')
const twoFactorLoading = ref(false)
const twoFactorSetup = ref<TwoFactorSetup | null>(null)

watch(twoFactorOpen, (open) => {
  if (open || twoFactorLoading.value) return
  // Setup secrets are deliberately ephemeral and discarded when the customer
  // leaves the enrollment dialog.
  twoFactorSetup.value = null
  twoFactorCode.value = ''
  twoFactorError.value = ''
})

const phishingOpen = ref(false)
const phishingCode = ref('')
const phishingError = ref('')
const phishingLoading = ref(false)

const otherSessionCount = computed(() => sessions.value.filter((session) => !session.current).length)
const scoreTone = computed(() => {
  const score = overview.value?.score ?? 0
  return score >= 85 ? 'strong' : score >= 65 ? 'medium' : 'weak'
})
const scoreLabel = computed(() => scoreTone.value === 'strong' ? 'امنیت عالی' : scoreTone.value === 'medium' ? 'امنیت خوب' : 'نیازمند توجه')

const confirmationCopy = computed(() => {
  const action = confirmation.value
  if (!action) return { title: '', description: '', confirm: '' }
  if (action.kind === 'session') return {
    title: 'خروج این دستگاه؟',
    description: `دسترسی ${action.session.deviceName} قطع می‌شود و برای ورود دوباره به رمز و کد تأیید نیاز دارد.`,
    confirm: 'بله، خارج شود',
  }
  if (action.kind === 'other-sessions') return {
    title: 'خروج از سایر دستگاه‌ها؟',
    description: `${toPersianDigits(otherSessionCount.value)} نشست دیگر پایان می‌یابد و فقط همین دستگاه متصل می‌ماند.`,
    confirm: 'خروج از همه',
  }
  if (action.kind === 'disable-2fa') return {
    title: 'غیرفعال‌کردن ورود دومرحله‌ای؟',
    description: 'با غیرفعال‌کردن این لایه، امنیت ورود حساب کمتر می‌شود.',
    confirm: 'غیرفعال شود',
  }
  return {
    title: action.enabled ? 'فعال‌کردن فهرست مجاز برداشت؟' : 'غیرفعال‌کردن فهرست مجاز؟',
    description: action.enabled
      ? 'پس از فعال‌سازی، برداشت فقط به آدرس‌های تأییدشده انجام می‌شود.'
      : 'پس از غیرفعال‌سازی، امکان برداشت به آدرس‌های تازه نیز وجود خواهد داشت.',
    confirm: action.enabled ? 'فعال شود' : 'غیرفعال شود',
  }
})

function readableError(caught: unknown, fallback: string): string {
  return caught instanceof Error ? caught.message : fallback
}

function deviceIcon(type: ActiveSession['deviceType']): string {
  return type === 'mobile' ? 'phone' : type === 'tablet' ? 'dashboard' : 'markets'
}

function eventIcon(type: SecurityEventType): string {
  const icons: Record<SecurityEventType, string> = {
    login_success: 'shield',
    login_failed: 'warning',
    password_changed: 'lock',
    two_factor_enabled: 'shield',
    session_revoked: 'logout',
    withdrawal_confirmed: 'wallet',
  }
  return icons[type]
}

function eventTone(type: SecurityEventType): string {
  if (type === 'login_failed') return 'danger'
  if (type === 'withdrawal_confirmed') return 'warning'
  if (type === 'two_factor_enabled' || type === 'password_changed') return 'success'
  return 'info'
}

async function load(): Promise<void> {
  loading.value = true
  error.value = ''
  try {
    const [securityOverview, activeSessions, securityEvents] = await Promise.all([
      securityService.getOverview(),
      securityService.listSessions(),
      securityService.listEvents(),
    ])
    overview.value = securityOverview
    sessions.value = activeSessions
    events.value = securityEvents
  } catch (caught) {
    error.value = readableError(caught, 'اطلاعات امنیتی بارگیری نشد.')
  } finally {
    loading.value = false
  }
}

function resetPasswordForm(): void {
  passwordForm.currentPassword = ''
  passwordForm.newPassword = ''
  passwordForm.newPasswordConfirmation = ''
  passwordError.value = ''
  Object.keys(passwordFields).forEach((key) => delete passwordFields[key])
}

function openPassword(): void {
  resetPasswordForm()
  passwordOpen.value = true
}

function validatePassword(): boolean {
  Object.keys(passwordFields).forEach((key) => delete passwordFields[key])
  if (passwordForm.currentPassword.length < 8) passwordFields.currentPassword = 'رمز عبور فعلی را کامل وارد کنید.'
  if (passwordForm.newPassword.length < 8) passwordFields.newPassword = 'رمز جدید باید حداقل ۸ کاراکتر باشد.'
  if (passwordForm.newPassword !== passwordForm.newPasswordConfirmation) passwordFields.newPasswordConfirmation = 'تکرار رمز با رمز جدید یکسان نیست.'
  if (passwordForm.currentPassword === passwordForm.newPassword) passwordFields.newPassword = 'رمز جدید باید با رمز فعلی متفاوت باشد.'
  return Object.keys(passwordFields).length === 0
}

async function changePassword(): Promise<void> {
  if (!validatePassword()) return
  changingPassword.value = true
  passwordError.value = ''
  try {
    await securityService.changePassword(passwordForm)
    passwordOpen.value = false
    resetPasswordForm()
    feedback.value = 'رمز عبور با موفقیت تغییر کرد.'
    events.value = await securityService.listEvents()
  } catch (caught) {
    if (caught instanceof ApiError && caught.details?.fields) Object.assign(passwordFields, caught.details.fields)
    passwordError.value = readableError(caught, 'تغییر رمز عبور انجام نشد.')
  } finally {
    changingPassword.value = false
  }
}

async function requestTwoFactorChange(): Promise<void> {
  if (overview.value?.twoFactorEnabled) {
    confirmation.value = { kind: 'disable-2fa' }
    return
  }
  twoFactorCode.value = ''
  twoFactorError.value = ''
  twoFactorLoading.value = true
  try {
    twoFactorSetup.value = await securityService.startTwoFactorSetup()
    twoFactorOpen.value = true
  } catch (caught) {
    error.value = readableError(caught, 'ساخت کد ورود دومرحله‌ای انجام نشد.')
  } finally {
    twoFactorLoading.value = false
  }
}

function updateTwoFactorCode(value: string): void {
  twoFactorCode.value = normalizeDigits(value).replace(/\D/g, '').slice(0, 6)
  twoFactorError.value = ''
}

async function enableTwoFactor(): Promise<void> {
  const code = normalizeDigits(twoFactorCode.value).replace(/\D/g, '')
  if (!twoFactorSetup.value) {
    twoFactorError.value = 'درخواست فعال‌سازی منقضی شده است؛ دوباره شروع کنید.'
    return
  }
  if (!/^\d{6}$/.test(code)) {
    twoFactorError.value = 'کد ۶ رقمی برنامه تأییدکننده را وارد کنید.'
    return
  }
  twoFactorLoading.value = true
  try {
    overview.value = await securityService.setTwoFactor(true, code, twoFactorSetup.value.setupToken)
    twoFactorOpen.value = false
    twoFactorSetup.value = null
    feedback.value = 'ورود دومرحله‌ای فعال شد.'
  } catch (caught) {
    twoFactorError.value = readableError(caught, 'فعال‌سازی ورود دومرحله‌ای انجام نشد.')
  } finally {
    twoFactorLoading.value = false
  }
}

function openPhishing(): void {
  phishingCode.value = overview.value?.antiPhishingCode ?? ''
  phishingError.value = ''
  phishingOpen.value = true
}

function updatePhishingCode(value: string): void {
  phishingCode.value = value.slice(0, 20)
  phishingError.value = ''
}

async function savePhishing(): Promise<void> {
  const code = phishingCode.value.trim()
  if (code && (code.length < 4 || code.length > 20)) {
    phishingError.value = 'عبارت باید بین ۴ تا ۲۰ کاراکتر باشد.'
    return
  }
  phishingLoading.value = true
  phishingError.value = ''
  try {
    overview.value = await securityService.setAntiPhishingCode(code || null)
    phishingOpen.value = false
    feedback.value = code ? 'کد ضد فیشینگ ذخیره شد.' : 'کد ضد فیشینگ حذف شد.'
  } catch (caught) {
    phishingError.value = readableError(caught, 'ذخیره کد ضد فیشینگ انجام نشد.')
  } finally {
    phishingLoading.value = false
  }
}

async function runConfirmation(): Promise<void> {
  const action = confirmation.value
  if (!action) return
  confirming.value = true
  error.value = ''
  try {
    if (action.kind === 'session') {
      await securityService.revokeSession(action.session.id)
      sessions.value = sessions.value.filter((session) => session.id !== action.session.id)
      feedback.value = `دسترسی ${action.session.deviceName} قطع شد.`
    } else if (action.kind === 'other-sessions') {
      await securityService.revokeOtherSessions()
      sessions.value = sessions.value.filter((session) => session.current)
      feedback.value = 'همه نشست‌های دیگر پایان یافتند.'
    } else if (action.kind === 'disable-2fa') {
      overview.value = await securityService.setTwoFactor(false)
      feedback.value = 'ورود دومرحله‌ای غیرفعال شد.'
    } else {
      overview.value = await securityService.setWithdrawalWhitelist(action.enabled)
      feedback.value = action.enabled ? 'فهرست مجاز برداشت فعال شد.' : 'فهرست مجاز برداشت غیرفعال شد.'
    }
    if (action.kind === 'session' || action.kind === 'other-sessions') {
      overview.value = await securityService.getOverview()
      events.value = await securityService.listEvents()
    }
    confirmation.value = null
  } catch (caught) {
    error.value = readableError(caught, 'تغییر امنیتی انجام نشد.')
    confirmation.value = null
  } finally {
    confirming.value = false
  }
}

function onWhitelistInput(enabled: boolean): void {
  if (!overview.value || enabled === overview.value.withdrawalWhitelistEnabled) return
  confirmation.value = { kind: 'whitelist', enabled }
}

onMounted(load)
</script>

<template>
  <div class="page security-page">
    <PageHeader title="امنیت حساب" description="ورودها، دستگاه‌ها و لایه‌های حفاظتی دارایی خود را مدیریت کنید." />

    <div v-if="feedback" class="notice success" role="status"><AppIcon name="check" :size="19" /><span>{{ feedback }}</span><button type="button" aria-label="بستن" @click="feedback = ''"><AppIcon name="close" :size="16" /></button></div>
    <div v-if="error" class="notice danger" role="alert"><AppIcon name="warning" :size="19" /><span>{{ error }}</span><button type="button" @click="load">تلاش دوباره</button></div>

    <template v-if="loading">
      <AppCard padding="lg"><div class="score-skeleton"><AppSkeleton width="7rem" height="7rem" radius="50%" /><div><AppSkeleton width="12rem" height="1.6rem" /><AppSkeleton width="21rem" height=".9rem" /></div></div></AppCard>
      <div class="security-grid"><AppCard v-for="i in 2" :key="i" padding="lg"><AppSkeleton v-for="j in 4" :key="j" height="4.5rem" :style="{ marginBottom: '1rem' }" /></AppCard></div>
    </template>

    <template v-else-if="overview">
      <AppCard class="score-card" padding="lg" :class="`score-${scoreTone}`">
        <div class="score-ring" :style="{ '--score-angle': `${overview.score * 3.6}deg` }" role="progressbar" aria-label="امتیاز امنیت حساب" aria-valuemin="0" aria-valuemax="100" :aria-valuenow="overview.score"><span><strong>{{ toPersianDigits(overview.score) }}</strong><small>از ۱۰۰</small></span></div>
        <div class="score-copy"><span>وضعیت حفاظت حساب</span><h2>{{ scoreLabel }}</h2><p>با فعال‌کردن ورود دومرحله‌ای و کنترل نشست‌های ناشناس، امنیت حساب را بالاتر ببرید.</p></div>
        <div class="score-facts"><div><AppIcon name="phone" :size="19" /><span><small>موبایل</small><strong>{{ overview.mobileVerified ? 'تأییدشده' : 'تأییدنشده' }}</strong></span></div><div><AppIcon name="shield" :size="19" /><span><small>ورود دومرحله‌ای</small><strong>{{ overview.twoFactorEnabled ? 'فعال' : 'غیرفعال' }}</strong></span></div><div><AppIcon name="markets" :size="19" /><span><small>نشست فعال</small><strong>{{ toPersianDigits(overview.activeSessionsCount) }} دستگاه</strong></span></div></div>
      </AppCard>

      <div class="security-grid">
        <AppCard padding="lg" class="protection-card">
          <div class="section-heading"><span><AppIcon name="lock" :size="21" /></span><div><h2>ورود و بازیابی</h2><p>راه‌های ورود و تأیید هویت حساب</p></div></div>
          <div class="setting-list">
            <div class="setting-row"><span class="setting-icon"><AppIcon name="lock" :size="21" /></span><div><strong>رمز عبور</strong><small>برای حساب شما تنظیم شده است</small></div><StatusBadge domain="security" status="secure" /><AppButton variant="secondary" size="sm" icon="edit" @click="openPassword">تغییر رمز</AppButton></div>
            <div class="setting-row featured"><span class="setting-icon"><AppIcon name="shield" :size="21" /></span><div><strong>ورود دومرحله‌ای</strong><small>تأیید ورود با کد برنامه Authenticator</small></div><StatusBadge domain="security" :status="overview.twoFactorEnabled ? 'enabled' : 'disabled'" /><AppButton :variant="overview.twoFactorEnabled ? 'ghost' : 'primary'" size="sm" @click="requestTwoFactorChange">{{ overview.twoFactorEnabled ? 'غیرفعال‌سازی' : 'فعال‌سازی' }}</AppButton></div>
            <div class="setting-row"><span class="setting-icon"><AppIcon name="phone" :size="21" /></span><div><strong>شماره موبایل</strong><small>برای کدهای امنیتی و بازیابی</small></div><StatusBadge domain="security" :status="overview.mobileVerified ? 'verified' : 'unverified'" /><span class="row-note">{{ overview.mobileVerified ? 'نیاز به اقدام نیست' : 'تکمیل در احراز هویت' }}</span></div>
            <div class="setting-row"><span class="setting-icon"><AppIcon name="mail" :size="21" /></span><div><strong>نشانی ایمیل</strong><small>برای هشدارهای ورود و بازیابی</small></div><StatusBadge domain="security" :status="overview.emailVerified ? 'verified' : 'unverified'" /><AppButton v-if="!overview.emailVerified" to="/app/profile" variant="ghost" size="sm">بررسی ایمیل</AppButton><span v-else class="row-note">تأییدشده</span></div>
          </div>
        </AppCard>

        <AppCard padding="lg" class="withdrawal-security">
          <div class="section-heading"><span><AppIcon name="wallet" :size="21" /></span><div><h2>امنیت برداشت</h2><p>کنترل‌های تکمیلی برای خروج دارایی</p></div></div>
          <div class="feature-block"><div class="feature-title"><span><AppIcon name="mail" :size="21" /></span><div><strong>کد ضد فیشینگ</strong><small>نمایش عبارت اختصاصی شما در پیام‌های معتبر روشا</small></div><StatusBadge domain="security" :status="overview.antiPhishingEnabled ? 'enabled' : 'disabled'" /></div><div v-if="overview.antiPhishingCode" class="phishing-preview"><small>عبارت فعلی</small><strong>{{ overview.antiPhishingCode }}</strong></div><AppButton block variant="secondary" size="sm" icon="edit" @click="openPhishing">{{ overview.antiPhishingEnabled ? 'ویرایش عبارت' : 'تنظیم عبارت' }}</AppButton></div>
          <div class="feature-block"><div class="feature-title"><span><AppIcon name="check" :size="21" /></span><div><strong>فهرست مجاز آدرس برداشت</strong><small>برداشت فقط به آدرس‌هایی که از قبل تأیید کرده‌اید</small></div></div><AppSwitch :model-value="overview.withdrawalWhitelistEnabled" :label="overview.withdrawalWhitelistEnabled ? 'فهرست مجاز فعال است' : 'فهرست مجاز غیرفعال است'" description="تغییر این گزینه نیازمند تأیید شماست." @update:model-value="onWhitelistInput" /></div>
        </AppCard>
      </div>

      <AppCard padding="none" class="sessions-card">
        <header class="list-header"><div><span><AppIcon name="markets" :size="21" /></span><div><h2>دستگاه‌های فعال</h2><p>اگر دستگاهی را نمی‌شناسید، فوراً دسترسی آن را قطع و رمز عبور را تغییر دهید.</p></div></div><AppButton v-if="otherSessionCount" variant="danger" size="sm" icon="logout" @click="confirmation = { kind: 'other-sessions' }">خروج از سایر دستگاه‌ها</AppButton></header>
        <div class="session-list">
          <article v-for="session in sessions" :key="session.id" class="session-row" :class="{ current: session.current }">
            <span class="device-icon"><AppIcon :name="deviceIcon(session.deviceType)" :size="23" /></span>
            <div class="session-copy"><div><h3>{{ session.deviceName }}</h3><StatusBadge v-if="session.current" domain="security" status="current" /></div><p>{{ session.browser }} روی {{ session.os }}</p><span><bdi dir="ltr">{{ session.ipAddress }}</bdi><i v-if="session.approximateLocation" />{{ session.approximateLocation }}</span></div>
            <div class="session-time"><small>آخرین فعالیت</small><strong :title="formatPersianDateTime(session.lastActiveAt)">{{ session.current ? 'همین حالا' : formatRelativeTime(session.lastActiveAt) }}</strong></div>
            <AppButton v-if="!session.current" variant="ghost" size="sm" icon="logout" @click="confirmation = { kind: 'session', session }">خروج دستگاه</AppButton>
          </article>
        </div>
      </AppCard>

      <AppCard padding="none" class="events-card">
        <header class="list-header"><div><span><AppIcon name="clock" :size="21" /></span><div><h2>تاریخچه امنیتی</h2><p>آخرین ورودها و تغییرات مهم حساب</p></div></div></header>
        <div v-if="events.length" class="event-list"><article v-for="event in events" :key="event.id"><span class="event-icon" :class="`tone-${eventTone(event.type)}`"><AppIcon :name="eventIcon(event.type)" :size="20" /></span><div><h3>{{ event.title }}</h3><p>{{ event.description }}</p><small>{{ event.deviceName }} · <bdi dir="ltr">{{ event.ipAddress }}</bdi></small></div><time :datetime="event.createdAt" :title="formatPersianDateTime(event.createdAt)">{{ formatRelativeTime(event.createdAt) }}</time></article></div>
        <EmptyState v-else icon="clock" title="رویداد امنیتی ثبت نشده" description="ورودها و تغییرات امنیتی مهم در این بخش نمایش داده می‌شوند." />
      </AppCard>
    </template>

    <AppModal v-model="passwordOpen" title="تغییر رمز عبور" description="رمزی انتخاب کنید که در سرویس دیگری استفاده نمی‌کنید." size="sm" :dismissible="!changingPassword">
      <form class="modal-form" @submit.prevent="changePassword"><div v-if="passwordError" class="modal-error" role="alert">{{ passwordError }}</div><AppInput v-model="passwordForm.currentPassword" type="password" label="رمز عبور فعلی" autocomplete="current-password" :error="passwordFields.currentPassword" /><AppInput v-model="passwordForm.newPassword" type="password" label="رمز عبور جدید" autocomplete="new-password" hint="حداقل ۸ کاراکتر" :error="passwordFields.newPassword" /><AppInput v-model="passwordForm.newPasswordConfirmation" type="password" label="تکرار رمز عبور جدید" autocomplete="new-password" :error="passwordFields.newPasswordConfirmation" /></form>
      <template #footer><AppButton block :loading="changingPassword" @click="changePassword">تغییر رمز عبور</AppButton><AppButton variant="secondary" :disabled="changingPassword" @click="passwordOpen = false">انصراف</AppButton></template>
    </AppModal>

    <AppModal v-model="twoFactorOpen" title="فعال‌سازی ورود دومرحله‌ای" description="کد QR را فقط در برنامه Authenticator خود اسکن کنید." size="sm" :dismissible="!twoFactorLoading">
      <form class="modal-form" @submit.prevent="enableTwoFactor">
        <div v-if="twoFactorSetup" class="two-factor-setup">
          <QrCode :value="twoFactorSetup.otpauthUri" :size="156" label="کد QR راه‌اندازی ورود دومرحله‌ای" />
          <div><strong>۱. اسکن یا ورود دستی</strong><p>کد را در Google Authenticator، Microsoft Authenticator یا برنامه مشابه وارد کنید.</p><span class="setup-secret"><bdi>{{ twoFactorSetup.secret }}</bdi><CopyButton :value="twoFactorSetup.secret" label="کپی کلید" /></span></div>
        </div>
        <div class="auth-guide"><span><AppIcon name="shield" :size="27" /></span><div><strong>۲. تأیید اتصال برنامه</strong><DemoCodeHint v-if="DemoCodeHint" context="two-factor" /><p v-else>کد شش‌رقمی فعلی برنامه را برای تکمیل اتصال وارد کنید.</p></div></div>
        <AppInput :model-value="twoFactorCode" label="کد ۶ رقمی برنامه" inputmode="numeric" autocomplete="one-time-code" maxlength="6" ltr :error="twoFactorError" placeholder="••••••" @update:model-value="updateTwoFactorCode" />
      </form>
      <template #footer><AppButton block :loading="twoFactorLoading" @click="enableTwoFactor">تأیید و فعال‌سازی</AppButton><AppButton variant="secondary" :disabled="twoFactorLoading" @click="twoFactorOpen = false">انصراف</AppButton></template>
    </AppModal>

    <AppModal v-model="phishingOpen" title="کد ضد فیشینگ" description="این عبارت باید در پیام‌های معتبر روشا نمایش داده شود." size="sm" :dismissible="!phishingLoading">
      <form class="modal-form" @submit.prevent="savePhishing"><AppInput :model-value="phishingCode" label="عبارت اختصاصی" placeholder="مثلاً: rosha-arya" ltr :error="phishingError" hint="بین ۴ تا ۲۰ کاراکتر و قابل تشخیص برای خودتان" @update:model-value="updatePhishingCode" /><div class="phishing-help"><AppIcon name="warning" :size="18" />اگر پیامی این عبارت را نداشت، روی لینک‌های آن کلیک نکنید.</div></form>
      <template #footer><AppButton block :loading="phishingLoading" @click="savePhishing">ذخیره عبارت</AppButton><AppButton v-if="overview?.antiPhishingEnabled" variant="danger" :disabled="phishingLoading" @click="phishingCode = ''; savePhishing()">حذف کد</AppButton><AppButton v-else variant="secondary" :disabled="phishingLoading" @click="phishingOpen = false">انصراف</AppButton></template>
    </AppModal>

    <AppModal :model-value="Boolean(confirmation)" :title="confirmationCopy.title" :description="confirmationCopy.description" size="sm" :dismissible="!confirming" @update:model-value="(value) => { if (!value && !confirming) confirmation = null }">
      <div class="confirmation-visual"><span><AppIcon name="warning" :size="25" /></span><p>این عملیات فوراً روی امنیت حساب اعمال می‌شود.</p></div>
      <template #footer><AppButton variant="danger" block :loading="confirming" @click="runConfirmation">{{ confirmationCopy.confirm }}</AppButton><AppButton variant="secondary" :disabled="confirming" @click="confirmation = null">انصراف</AppButton></template>
    </AppModal>
  </div>
</template>

<style scoped>
.security-page { display: grid; align-content: start; gap: var(--space-5); }.security-page :deep(.page-header) { margin-bottom: 0; }.notice { display: flex; align-items: center; gap: var(--space-2); padding: var(--space-3) var(--space-4); border: 1px solid; border-radius: var(--radius-md); font-size: var(--font-size-sm); }.notice span { flex: 1; }.notice button { border: 0; background: transparent; color: inherit; font-weight: 600; }.notice.success { border-color: rgba(53,201,149,.23); background: var(--color-success-soft); color: var(--color-success); }.notice.danger { border-color: rgba(240,108,117,.23); background: var(--color-danger-soft); color: var(--color-danger); }.score-skeleton { display: flex; align-items: center; gap: var(--space-5); }.score-skeleton > div { display: grid; grid-template-columns: minmax(0, 1fr); min-width: 0; flex: 1; gap: var(--space-3); }.score-skeleton :deep(.skeleton) { max-width: 100%; }
.score-card { display: flex; align-items: center; gap: var(--space-6); background: linear-gradient(120deg,var(--color-surface-1),var(--color-primary-soft)); }.score-ring { position: relative; display: grid; width: 7.5rem; height: 7.5rem; flex: 0 0 auto; border-radius: 50%; background: conic-gradient(var(--score-color) var(--score-angle),var(--color-surface-3) 0); place-items: center; }.score-ring::before { position: absolute; inset: .5rem; border-radius: 50%; background: var(--color-surface-1); content: ''; }.score-ring span { position: relative; display: grid; text-align: center; }.score-ring strong { font-size: var(--font-size-2xl); }.score-ring small { color: var(--color-text-muted); font-size: var(--font-size-xs); }.score-strong { --score-color: var(--color-success); }.score-medium { --score-color: var(--color-warning); }.score-weak { --score-color: var(--color-danger); }.score-copy { min-width: 0; flex: 1; }.score-copy > span { color: var(--score-color); font-size: var(--font-size-xs); font-weight: 600; }.score-copy h2 { margin: .15rem 0; font-size: var(--font-size-2xl); }.score-copy p { max-width: 35rem; margin: 0; color: var(--color-text-muted); font-size: var(--font-size-sm); }.score-facts { display: grid; grid-template-columns: repeat(3,1fr); gap: var(--space-2); }.score-facts > div { display: flex; align-items: center; gap: var(--space-2); min-width: 8.5rem; padding: var(--space-3); border: 1px solid var(--color-border-soft); border-radius: var(--radius-md); background: var(--color-surface-2); color: var(--color-primary); }.score-facts span { display: grid; color: var(--color-text-primary); }.score-facts small { color: var(--color-text-muted); font-size: .66rem; }.score-facts strong { font-size: var(--font-size-xs); }
.security-grid { display: grid; grid-template-columns: minmax(0,1.25fr) minmax(20rem,.75fr); align-items: start; gap: var(--space-5); }.section-heading { display: flex; align-items: center; gap: var(--space-3); margin-bottom: var(--space-4); }.section-heading > span { display: grid; width: 2.75rem; height: 2.75rem; flex: 0 0 auto; border-radius: .85rem; background: var(--color-primary-soft); color: var(--color-primary); place-items: center; }.section-heading h2 { margin: 0; font-size: var(--font-size-lg); }.section-heading p { margin: .1rem 0 0; color: var(--color-text-muted); font-size: var(--font-size-xs); }
.setting-list { display: grid; }.setting-row { display: grid; grid-template-columns: auto minmax(0,1fr) auto auto; align-items: center; gap: var(--space-3); padding-block: var(--space-4); }.setting-row + .setting-row { border-top: 1px solid var(--color-border-soft); }.setting-row.featured { margin-inline: calc(var(--space-2) * -1); padding-inline: var(--space-2); border-radius: var(--radius-md); background: linear-gradient(90deg,var(--color-primary-soft),transparent); }.setting-icon { display: grid; width: 2.75rem; height: 2.75rem; border-radius: .85rem; background: var(--color-surface-2); color: var(--color-text-secondary); place-items: center; }.setting-row.featured .setting-icon { background: var(--color-primary-soft); color: var(--color-primary); }.setting-row > div { display: grid; }.setting-row small,.row-note { color: var(--color-text-muted); font-size: var(--font-size-xs); }
.withdrawal-security { display: grid; gap: var(--space-4); }.feature-block { display: grid; gap: var(--space-3); padding: var(--space-4); border: 1px solid var(--color-border-soft); border-radius: var(--radius-lg); background: var(--color-surface-2); }.feature-title { display: grid; grid-template-columns: auto 1fr auto; align-items: start; gap: var(--space-3); }.feature-title > span { display: grid; width: 2.5rem; height: 2.5rem; border-radius: .75rem; background: var(--color-primary-soft); color: var(--color-primary); place-items: center; }.feature-title > div { display: grid; }.feature-title small { color: var(--color-text-muted); font-size: var(--font-size-xs); }.phishing-preview { display: flex; align-items: center; justify-content: space-between; gap: var(--space-3); padding: var(--space-2) var(--space-3); border-radius: var(--radius-sm); background: var(--color-surface-3); }.phishing-preview small { color: var(--color-text-muted); }.phishing-preview strong { color: var(--color-gold); direction: ltr; }
.sessions-card,.events-card { overflow: hidden; }.list-header { display: flex; align-items: center; justify-content: space-between; gap: var(--space-4); padding: var(--space-5); border-bottom: 1px solid var(--color-border-soft); }.list-header > div { display: flex; align-items: center; gap: var(--space-3); }.list-header > div > span { display: grid; width: 2.75rem; height: 2.75rem; border-radius: .85rem; background: var(--color-primary-soft); color: var(--color-primary); place-items: center; }.list-header h2 { margin: 0; font-size: var(--font-size-lg); }.list-header p { margin: .1rem 0 0; color: var(--color-text-muted); font-size: var(--font-size-xs); }.session-list { display: grid; }.session-row { display: grid; grid-template-columns: auto minmax(0,1fr) auto auto; align-items: center; gap: var(--space-4); padding: var(--space-5); }.session-row + .session-row { border-top: 1px solid var(--color-border-soft); }.session-row.current { background: linear-gradient(90deg,var(--color-success-soft),transparent 55%); }.device-icon { display: grid; width: 3rem; height: 3rem; border-radius: 1rem; background: var(--color-surface-2); color: var(--color-text-secondary); place-items: center; }.current .device-icon { background: var(--color-success-soft); color: var(--color-success); }.session-copy { min-width: 0; }.session-copy > div { display: flex; align-items: center; gap: var(--space-2); }.session-copy h3 { margin: 0; font-size: var(--font-size-md); }.session-copy p { margin: .1rem 0; color: var(--color-text-secondary); font-size: var(--font-size-xs); }.session-copy > span { display: flex; align-items: center; gap: var(--space-2); color: var(--color-text-muted); font-size: .68rem; }.session-copy > span i { width: .25rem; height: .25rem; border-radius: 50%; background: var(--color-border-hover); }.session-time { display: grid; min-width: 8rem; text-align: end; }.session-time small { color: var(--color-text-muted); font-size: .68rem; }.session-time strong { font-size: var(--font-size-xs); }
.event-list { display: grid; }.event-list article { display: grid; grid-template-columns: auto minmax(0,1fr) auto; align-items: center; gap: var(--space-4); padding: var(--space-4) var(--space-5); }.event-list article + article { border-top: 1px solid var(--color-border-soft); }.event-icon { display: grid; width: 2.75rem; height: 2.75rem; border-radius: .85rem; place-items: center; }.tone-info { background: var(--color-info-soft); color: var(--color-info); }.tone-success { background: var(--color-success-soft); color: var(--color-success); }.tone-warning { background: var(--color-warning-soft); color: var(--color-warning); }.tone-danger { background: var(--color-danger-soft); color: var(--color-danger); }.event-list h3 { margin: 0; font-size: var(--font-size-sm); }.event-list p { margin: .05rem 0; color: var(--color-text-secondary); font-size: var(--font-size-xs); }.event-list small { color: var(--color-text-muted); font-size: .68rem; }.event-list time { color: var(--color-text-muted); font-size: var(--font-size-xs); }
.modal-form { display: grid; gap: var(--space-4); }.modal-error { padding: var(--space-3); border-radius: var(--radius-md); background: var(--color-danger-soft); color: var(--color-danger); font-size: var(--font-size-sm); }.two-factor-setup { display: grid; grid-template-columns: auto minmax(0,1fr); align-items: center; gap: var(--space-4); padding: var(--space-4); border: 1px solid var(--color-border-soft); border-radius: var(--radius-lg); background: var(--color-surface-2); }.two-factor-setup > div { min-width: 0; }.two-factor-setup p { margin: .2rem 0 var(--space-3); color: var(--color-text-muted); font-size: var(--font-size-xs); }.setup-secret { display: flex; min-width: 0; align-items: center; justify-content: space-between; gap: var(--space-2); padding: var(--space-2); border: 1px dashed var(--color-border); border-radius: var(--radius-sm); background: var(--color-surface-3); }.setup-secret bdi { overflow: hidden; direction: ltr; font-size: var(--font-size-xs); font-weight: 700; text-overflow: ellipsis; }.auth-guide { display: flex; align-items: center; gap: var(--space-3); padding: var(--space-4); border-radius: var(--radius-md); background: var(--color-primary-soft); }.auth-guide > span { display: grid; width: 3rem; height: 3rem; flex: 0 0 auto; border-radius: .9rem; background: var(--color-surface-2); color: var(--color-primary); place-items: center; }.auth-guide p { margin: .1rem 0 0; color: var(--color-text-muted); font-size: var(--font-size-xs); }.phishing-help { display: flex; align-items: flex-start; gap: var(--space-2); padding: var(--space-3); border-radius: var(--radius-md); background: var(--color-warning-soft); color: var(--color-text-secondary); font-size: var(--font-size-xs); }.phishing-help svg { color: var(--color-warning); }.confirmation-visual { display: flex; align-items: center; gap: var(--space-3); padding: var(--space-4); border-radius: var(--radius-md); background: var(--color-danger-soft); }.confirmation-visual > span { display: grid; width: 2.75rem; height: 2.75rem; border-radius: .8rem; background: rgba(240,108,117,.12); color: var(--color-danger); place-items: center; }.confirmation-visual p { margin: 0; color: var(--color-text-secondary); }
.notice button { display: inline-grid; min-width: 2.75rem; min-height: 2.75rem; padding-inline: var(--space-2); border-radius: var(--radius-sm); place-items: center; }
.notice button:focus-visible { outline: 2px solid currentColor; outline-offset: 2px; }
.score-card { position: relative; overflow: hidden; }
.score-card::after { position: absolute; inset-block: 16%; inset-inline-start: 0; width: 2px; border-radius: var(--radius-pill); background: linear-gradient(180deg,transparent,var(--score-color),transparent); content: ''; opacity: .8; }
.score-card > * { position: relative; z-index: 1; }
.score-facts > div:nth-child(1) { color: var(--color-success); }
.score-facts > div:nth-child(2) { color: var(--color-primary); }
.score-facts > div:nth-child(3) { color: var(--color-gold); }
.setting-row,.feature-block,.session-row,.event-list article { transition: background var(--transition-fast), border-color var(--transition-fast); }
@media (hover: hover) {
  .setting-row:hover,.session-row:hover,.event-list article:hover { background: color-mix(in srgb, var(--color-primary-soft) 45%, transparent); }
  .feature-block:hover { border-color: var(--color-border-hover); }
}
@media (max-width: 1150px) { .score-card { flex-wrap: wrap; }.score-facts { width: 100%; }.security-grid { grid-template-columns: 1fr; } }
@media (max-width: 767px) { .score-card { align-items: flex-start; gap: var(--space-4); }.score-ring { width: 5.5rem; height: 5.5rem; }.score-copy { width: calc(100% - 7rem); }.score-copy h2 { font-size: var(--font-size-xl); }.score-copy p { display: none; }.score-facts { grid-template-columns: 1fr; }.score-facts > div { min-width: 0; }.setting-row { grid-template-columns: auto minmax(0,1fr) auto; }.setting-row > :deep(.status) { display: none; }.setting-row :deep(.app-button),.setting-row .row-note { grid-column: 2 / -1; justify-self: start; }.setting-row :deep(.app-button) { min-height: 2.75rem; }.feature-title { grid-template-columns: auto 1fr; }.feature-title :deep(.status) { grid-column: 2; }.list-header { align-items: flex-start; flex-direction: column; }.list-header :deep(.app-button) { width: 100%; min-height: 2.75rem; }.session-row { grid-template-columns: auto minmax(0,1fr); gap: var(--space-3); padding: var(--space-4); }.session-time { grid-column: 2; min-width: 0; text-align: start; }.session-row :deep(.app-button) { grid-column: 2; justify-self: start; min-height: 2.75rem; }.event-list article { grid-template-columns: auto minmax(0,1fr); gap: var(--space-3); padding: var(--space-4); }.event-list time { grid-column: 2; }.event-list p { line-height: 1.8; }.two-factor-setup { grid-template-columns: 1fr; justify-items: center; }.two-factor-setup > div { width: 100%; } }
@media (max-width: 399px) {
  .score-ring { width: 4.75rem; height: 4.75rem; }
  .score-ring strong { font-size: var(--font-size-xl); }
  .score-copy { width: calc(100% - 5.75rem); }
  .score-copy h2 { font-size: var(--font-size-lg); }
  .score-facts { gap: var(--space-2); }
  .setting-row { grid-template-columns: auto minmax(0, 1fr); }
  .setting-row > :deep(.status) { display: inline-flex; grid-column: 2; justify-self: start; }
  .setting-row :deep(.app-button),.setting-row .row-note { grid-column: 1 / -1; width: 100%; }
  .feature-title :deep(.status) { grid-column: 1 / -1; justify-self: start; margin-inline-start: calc(2.5rem + var(--space-3)); }
  .session-copy > span { align-items: flex-start; flex-direction: column; gap: 0; }
  .session-copy > span i { display: none; }
  .session-row :deep(.app-button) { grid-column: 1 / -1; width: 100%; }
  .event-icon { width: 2.5rem; height: 2.5rem; }
}
</style>
