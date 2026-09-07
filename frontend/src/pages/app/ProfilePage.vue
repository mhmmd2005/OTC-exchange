<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import AppButton from '@/components/ui/AppButton.vue'
import AppCard from '@/components/ui/AppCard.vue'
import AppIcon from '@/components/ui/AppIcon.vue'
import AppInput from '@/components/ui/AppInput.vue'
import AppModal from '@/components/ui/AppModal.vue'
import AppSkeleton from '@/components/ui/AppSkeleton.vue'
import EmptyState from '@/components/ui/EmptyState.vue'
import PageHeader from '@/components/ui/PageHeader.vue'
import StatusBadge from '@/components/ui/StatusBadge.vue'
import { securityService, userService } from '@/services'
import { useAuthStore } from '@/stores/auth'
import type { SecurityOverview, UserProfile } from '@/types'
import { formatPersianDate, formatPersianDateTime, toPersianDigits } from '@/utils/formatters'

const auth = useAuthStore()
const profile = ref<UserProfile | null>(null)
const security = ref<SecurityOverview | null>(null)
const loading = ref(true)
const error = ref('')
const feedback = ref('')
const emailOpen = ref(false)
const email = ref('')
const emailError = ref('')
const saving = ref(false)

const initials = computed(() => profile.value
  ? `${profile.value.firstName.charAt(0)}${profile.value.lastName.charAt(0)}`
  : 'ر')

const levelLabel = computed(() => {
  const labels: Record<string, string> = { level_0: 'سطح صفر', level_1: 'سطح یک', level_2: 'سطح دو', level_3: 'سطح سه' }
  return profile.value ? labels[profile.value.accountLevel] ?? profile.value.accountLevel : '—'
})

const completionItems = computed(() => {
  if (!profile.value) return []
  return [
    { label: 'شماره موبایل', complete: profile.value.mobileVerified, icon: 'phone' },
    { label: 'اطلاعات هویتی', complete: profile.value.kycStatus === 'verified', icon: 'verify' },
    { label: 'حساب بانکی', complete: profile.value.bankVerified, icon: 'bank' },
    { label: 'ایمیل', complete: profile.value.emailVerified, icon: 'mail' },
    { label: 'ورود دومرحله‌ای', complete: Boolean(security.value?.twoFactorEnabled), icon: 'shield' },
  ]
})

const completionPercent = computed(() => {
  if (!completionItems.value.length) return 0
  const complete = completionItems.value.filter((item) => item.complete).length
  return Math.round((complete / completionItems.value.length) * 100)
})

function readableError(caught: unknown, fallback: string): string {
  return caught instanceof Error ? caught.message : fallback
}

function maskMobile(value: string): string {
  const digits = value.replace(/\D/g, '')
  return digits.length >= 11 ? `${digits.slice(0, 4)} ${digits.slice(4, 7)} ${digits.slice(7)}` : value
}

async function load(): Promise<void> {
  loading.value = true
  error.value = ''
  try {
    const [user, securityOverview] = await Promise.all([
      userService.getProfile(),
      securityService.getOverview(),
    ])
    profile.value = user
    security.value = securityOverview
    email.value = user.email ?? ''
  } catch (caught) {
    error.value = readableError(caught, 'اطلاعات پروفایل بارگیری نشد.')
  } finally {
    loading.value = false
  }
}

function openEmail(): void {
  email.value = profile.value?.email ?? ''
  emailError.value = ''
  emailOpen.value = true
}

async function saveEmail(): Promise<void> {
  const normalized = email.value.trim().toLowerCase()
  if (!/^\S+@\S+\.\S+$/.test(normalized)) {
    emailError.value = 'یک نشانی ایمیل معتبر وارد کنید.'
    return
  }
  saving.value = true
  emailError.value = ''
  try {
    const updated = await userService.updateProfile({ email: normalized })
    profile.value = updated
    auth.user = updated
    emailOpen.value = false
    feedback.value = 'نشانی ایمیل به‌روزرسانی شد.'
  } catch (caught) {
    emailError.value = readableError(caught, 'به‌روزرسانی ایمیل انجام نشد.')
  } finally {
    saving.value = false
  }
}

onMounted(load)
</script>

<template>
  <div class="page profile-page">
    <PageHeader title="حساب کاربری" description="اطلاعات هویتی، وضعیت حساب و راه‌های ارتباطی خود را مرور کنید." />

    <template v-if="loading">
      <AppCard padding="lg"><div class="profile-skeleton"><AppSkeleton width="5rem" height="5rem" radius="1.5rem" /><div><AppSkeleton width="10rem" height="1.5rem" /><AppSkeleton width="15rem" height=".9rem" /></div></div></AppCard>
      <div class="profile-layout"><AppCard padding="lg"><AppSkeleton v-for="i in 5" :key="i" height="3.7rem" :style="{ marginBottom: '1rem' }" /></AppCard><AppCard padding="lg"><AppSkeleton v-for="i in 4" :key="i" height="3rem" :style="{ marginBottom: '1rem' }" /></AppCard></div>
    </template>

    <AppCard v-else-if="error || !profile" padding="none">
      <EmptyState icon="warning" title="پروفایل بارگیری نشد" :description="error"><AppButton variant="secondary" icon="refresh" @click="load">تلاش دوباره</AppButton></EmptyState>
    </AppCard>

    <template v-else>
      <div v-if="feedback" class="feedback" role="status"><AppIcon name="check" :size="18" /><span>{{ feedback }}</span><button type="button" aria-label="بستن" @click="feedback = ''"><AppIcon name="close" :size="16" /></button></div>

      <AppCard class="profile-hero" padding="lg">
        <div class="avatar-wrap">
          <img v-if="profile.avatarUrl" :src="profile.avatarUrl" :alt="profile.fullName" />
          <span v-else>{{ initials }}</span>
          <i v-if="profile.kycStatus === 'verified'"><AppIcon name="check" :size="14" /></i>
        </div>
        <div class="hero-copy">
          <div><h2>{{ profile.fullName }}</h2><StatusBadge domain="kyc" :status="profile.kycStatus" /></div>
          <p><span class="ltr">{{ toPersianDigits(maskMobile(profile.mobile)) }}</span><i />عضو روشا از {{ formatPersianDate(profile.joinedAt, { month: 'long' }) }}</p>
        </div>
        <div class="level-card-mini"><span><AppIcon name="star" :size="19" /></span><div><small>سطح حساب</small><strong>{{ levelLabel }}</strong></div><RouterLink to="/app/verification" aria-label="مشاهده احراز هویت"><AppIcon name="chevronLeft" :size="18" /></RouterLink></div>
      </AppCard>

      <div class="profile-layout">
        <AppCard padding="lg" class="identity-section">
          <div class="section-heading"><div><span><AppIcon name="profile" :size="21" /></span><div><h2>اطلاعات هویتی</h2><p>اطلاعات تطبیق‌داده‌شده با ثبت احوال</p></div></div><span class="locked-label"><AppIcon name="lock" :size="14" />فقط خواندنی</span></div>
          <div class="legal-note"><AppIcon name="shield" :size="18" /><span>برای حفظ امنیت و انطباق قانونی، اطلاعات هویتی تأییدشده از این صفحه قابل ویرایش نیست.</span></div>
          <div class="identity-grid">
            <AppInput :model-value="profile.firstName" label="نام" readonly />
            <AppInput :model-value="profile.lastName" label="نام خانوادگی" readonly />
            <AppInput :model-value="toPersianDigits(profile.nationalId)" label="کد ملی" readonly ltr />
            <AppInput :model-value="toPersianDigits(profile.birthDate)" label="تاریخ تولد" readonly ltr />
            <AppInput :model-value="toPersianDigits(maskMobile(profile.mobile))" label="شماره موبایل" readonly ltr>
              <template #action><span class="field-check"><AppIcon name="check" :size="15" />تأییدشده</span></template>
            </AppInput>
            <AppInput :model-value="profile.email || 'ثبت نشده'" label="ایمیل" readonly ltr>
              <template #action><button type="button" class="field-edit" aria-label="ویرایش ایمیل" @click.prevent="openEmail"><AppIcon name="edit" :size="17" /></button></template>
            </AppInput>
          </div>
          <div class="identity-help"><span>نیاز به اصلاح اطلاعات قانونی دارید؟</span><AppButton to="/app/support?new=1" variant="ghost" size="sm" icon="help">تماس با پشتیبانی</AppButton></div>
        </AppCard>

        <aside class="profile-aside">
          <AppCard padding="lg" class="completion-card">
            <div class="completion-head"><div><h2>آمادگی حساب</h2><p>موارد پیشنهادی برای حساب کامل‌تر</p></div><strong>{{ toPersianDigits(completionPercent) }}٪</strong></div>
            <div class="completion-track" role="progressbar" aria-label="درصد آمادگی حساب" aria-valuemin="0" aria-valuemax="100" :aria-valuenow="completionPercent"><i :style="{ width: `${completionPercent}%` }" /></div>
            <ul><li v-for="item in completionItems" :key="item.label" :class="{ complete: item.complete }"><span><AppIcon :name="item.icon" :size="18" />{{ item.label }}</span><AppIcon :name="item.complete ? 'check' : 'clock'" :size="17" /></li></ul>
            <AppButton v-if="completionPercent < 100" to="/app/security" block variant="secondary">تکمیل امنیت حساب</AppButton>
          </AppCard>

          <AppCard padding="none" class="account-links">
            <RouterLink to="/app/verification"><span class="link-icon"><AppIcon name="verify" :size="21" /></span><div><strong>احراز هویت</strong><small>{{ levelLabel }}</small></div><StatusBadge domain="kyc" :status="profile.kycStatus" /><AppIcon name="chevronLeft" :size="18" /></RouterLink>
            <RouterLink to="/app/bank-accounts"><span class="link-icon"><AppIcon name="bank" :size="21" /></span><div><strong>حساب‌های بانکی</strong><small>{{ profile.bankVerified ? 'حساب تأییدشده دارید' : 'نیاز به تکمیل' }}</small></div><StatusBadge domain="bank" :status="profile.bankVerified ? 'verified' : 'pending'" /><AppIcon name="chevronLeft" :size="18" /></RouterLink>
            <RouterLink to="/app/security"><span class="link-icon"><AppIcon name="shield" :size="21" /></span><div><strong>امنیت</strong><small>امتیاز {{ toPersianDigits(security?.score ?? 0) }} از ۱۰۰</small></div><StatusBadge domain="security" :status="(security?.score ?? 0) >= 80 ? 'secure' : 'attention'" /><AppIcon name="chevronLeft" :size="18" /></RouterLink>
          </AppCard>

          <AppCard padding="lg" class="login-card"><span><AppIcon name="clock" :size="20" /></span><div><small>آخرین ورود به حساب</small><strong>{{ formatPersianDateTime(profile.lastLoginAt) }}</strong></div></AppCard>
        </aside>
      </div>
    </template>

    <AppModal v-model="emailOpen" title="ویرایش نشانی ایمیل" description="اطلاعیه‌های امنیتی و بازیابی حساب به این نشانی ارسال می‌شوند." size="sm">
      <form class="email-form" @submit.prevent="saveEmail">
        <AppInput v-model="email" label="نشانی ایمیل" type="email" inputmode="email" autocomplete="email" ltr :error="emailError" placeholder="name@example.com" />
        <div class="email-note"><AppIcon name="info" :size="17" />پس از تغییر ایمیل، ممکن است برای تأیید آن یک پیام دریافت کنید.</div>
      </form>
      <template #footer><AppButton block :loading="saving" @click="saveEmail">ذخیره ایمیل</AppButton><AppButton variant="secondary" :disabled="saving" @click="emailOpen = false">انصراف</AppButton></template>
    </AppModal>
  </div>
</template>

<style scoped>
.hero-copy h2 { margin: 0; font-size: var(--font-size-2xl); }
@media (max-width: 767px) { .hero-copy h2 { font-size: var(--font-size-xl); } }
.profile-page { display: grid; align-content: start; gap: var(--space-5); }.profile-page :deep(.page-header) { margin-bottom: 0; }.profile-skeleton { display: flex; align-items: center; gap: var(--space-4); }.profile-skeleton > div { display: grid; grid-template-columns: minmax(0, 1fr); min-width: 0; flex: 1; gap: var(--space-2); }.profile-skeleton :deep(.skeleton) { max-width: 100%; }.feedback { display: flex; align-items: center; gap: var(--space-2); padding: var(--space-3) var(--space-4); border: 1px solid rgba(53,201,149,.22); border-radius: var(--radius-md); background: var(--color-success-soft); color: var(--color-success); font-size: var(--font-size-sm); }.feedback span { flex: 1; }.feedback button { border: 0; background: transparent; color: inherit; }
.profile-hero { display: flex; align-items: center; gap: var(--space-5); background: linear-gradient(120deg,var(--color-surface-1),var(--color-primary-soft)); }.avatar-wrap { position: relative; display: grid; width: 5.5rem; height: 5.5rem; flex: 0 0 auto; border: 1px solid rgba(67,139,255,.22); border-radius: 1.5rem; background: var(--color-primary-soft); color: var(--color-primary); font-size: var(--font-size-2xl); font-weight: 700; place-items: center; }.avatar-wrap img { width: 100%; height: 100%; border-radius: inherit; object-fit: cover; }.avatar-wrap i { position: absolute; inset-block-end: -.25rem; inset-inline-start: -.25rem; display: grid; width: 1.65rem; height: 1.65rem; border: 3px solid var(--color-surface-1); border-radius: 50%; background: var(--color-success); color: white; place-items: center; }.hero-copy { min-width: 0; flex: 1; }.hero-copy > div { display: flex; align-items: center; flex-wrap: wrap; gap: var(--space-3); }.hero-copy h1 { margin: 0; font-size: var(--font-size-2xl); }.hero-copy p { display: flex; align-items: center; gap: var(--space-2); margin: var(--space-2) 0 0; color: var(--color-text-muted); font-size: var(--font-size-sm); }.hero-copy p i { width: .25rem; height: .25rem; border-radius: 50%; background: var(--color-border-hover); }.level-card-mini { display: flex; align-items: center; gap: var(--space-3); min-width: 14rem; padding: var(--space-3) var(--space-4); border: 1px solid rgba(221,183,110,.2); border-radius: var(--radius-lg); background: var(--color-gold-soft); }.level-card-mini > span { display: grid; width: 2.4rem; height: 2.4rem; border-radius: .75rem; background: var(--color-gold-soft); color: var(--color-gold); place-items: center; }.level-card-mini > div { display: grid; flex: 1; }.level-card-mini small { color: var(--color-text-muted); }.level-card-mini a { color: var(--color-gold); }
.profile-layout { display: grid; grid-template-columns: minmax(0,1.45fr) minmax(20rem,.72fr); align-items: start; gap: var(--space-5); }.section-heading { display: flex; align-items: center; justify-content: space-between; gap: var(--space-4); margin-bottom: var(--space-4); }.section-heading > div { display: flex; align-items: center; gap: var(--space-3); }.section-heading > div > span { display: grid; width: 2.7rem; height: 2.7rem; border-radius: .85rem; background: var(--color-primary-soft); color: var(--color-primary); place-items: center; }.section-heading h2 { margin: 0; font-size: var(--font-size-lg); }.section-heading p { margin: .1rem 0 0; color: var(--color-text-muted); font-size: var(--font-size-xs); }.locked-label { display: inline-flex; align-items: center; gap: .3rem; color: var(--color-text-muted); font-size: var(--font-size-xs); }.legal-note { display: flex; align-items: flex-start; gap: var(--space-2); margin-bottom: var(--space-5); padding: var(--space-3); border-radius: var(--radius-md); background: var(--color-info-soft); color: var(--color-info); font-size: var(--font-size-xs); }.legal-note span { color: var(--color-text-secondary); }.identity-grid { display: grid; grid-template-columns: 1fr 1fr; gap: var(--space-4); }.identity-grid :deep(.field__control:has(input[readonly])) { background: var(--color-surface-2); }.identity-grid :deep(input[readonly]) { color: var(--color-text-secondary); cursor: default; }.field-check { display: inline-flex; align-items: center; gap: .2rem; flex: 0 0 auto; color: var(--color-success); font-size: .67rem; }.field-edit { display: grid; width: 2rem; height: 2rem; flex: 0 0 auto; border: 0; border-radius: .6rem; background: var(--color-primary-soft); color: var(--color-primary); place-items: center; }.identity-help { display: flex; align-items: center; justify-content: space-between; gap: var(--space-3); margin-top: var(--space-5); padding-top: var(--space-4); border-top: 1px solid var(--color-border-soft); color: var(--color-text-muted); font-size: var(--font-size-xs); }
.profile-aside { display: grid; gap: var(--space-4); }.completion-head { display: flex; align-items: center; justify-content: space-between; gap: var(--space-3); }.completion-head h2 { margin: 0; font-size: var(--font-size-md); }.completion-head p { margin: .1rem 0 0; color: var(--color-text-muted); font-size: var(--font-size-xs); }.completion-head > strong { color: var(--color-primary); font-size: var(--font-size-xl); }.completion-track { height: .45rem; margin-block: var(--space-4); overflow: hidden; border-radius: var(--radius-pill); background: var(--color-surface-3); }.completion-track i { display: block; height: 100%; border-radius: inherit; background: linear-gradient(90deg,var(--color-primary),var(--color-success)); }.completion-card ul { display: grid; gap: var(--space-1); margin: 0 0 var(--space-4); padding: 0; list-style: none; }.completion-card li { display: flex; align-items: center; justify-content: space-between; gap: var(--space-2); padding: var(--space-2); border-radius: var(--radius-sm); color: var(--color-text-muted); font-size: var(--font-size-sm); }.completion-card li > span { display: flex; align-items: center; gap: var(--space-2); }.completion-card li.complete { color: var(--color-text-secondary); }.completion-card li.complete > svg { color: var(--color-success); }
.account-links { overflow: hidden; }.account-links a { display: grid; grid-template-columns: auto minmax(0,1fr) auto auto; align-items: center; gap: var(--space-3); padding: var(--space-4); transition: background var(--transition-fast); }.account-links a + a { border-top: 1px solid var(--color-border-soft); }.account-links a:hover { background: var(--color-surface-2); }.link-icon { display: grid; width: 2.7rem; height: 2.7rem; border-radius: .8rem; background: var(--color-primary-soft); color: var(--color-primary); place-items: center; }.account-links a > div { display: grid; }.account-links small { color: var(--color-text-muted); font-size: var(--font-size-xs); }.account-links a > svg { color: var(--color-text-muted); }.login-card { display: flex; align-items: center; gap: var(--space-3); }.login-card > span { display: grid; width: 2.5rem; height: 2.5rem; border-radius: .75rem; background: var(--color-surface-2); color: var(--color-text-muted); place-items: center; }.login-card > div { display: grid; }.login-card small { color: var(--color-text-muted); }.login-card strong { font-size: var(--font-size-xs); }.email-form { display: grid; gap: var(--space-3); }.email-note { display: flex; align-items: flex-start; gap: var(--space-2); padding: var(--space-3); border-radius: var(--radius-md); background: var(--color-info-soft); color: var(--color-text-secondary); font-size: var(--font-size-xs); }.email-note svg { color: var(--color-info); }
.profile-hero { position: relative; overflow: hidden; }
.profile-hero::after { position: absolute; inset-block: 18%; inset-inline-start: 0; width: 2px; border-radius: var(--radius-pill); background: linear-gradient(180deg,transparent,var(--color-gold),transparent); content: ''; opacity: .7; }
.avatar-wrap,.hero-copy,.level-card-mini { position: relative; z-index: 1; }
.feedback button { display: inline-grid; min-width: 2.75rem; min-height: 2.75rem; border-radius: var(--radius-sm); place-items: center; }
.feedback button:focus-visible { outline: 2px solid currentColor; outline-offset: 2px; }
.field-edit { width: 2.75rem; height: 2.75rem; border-radius: .7rem; }
.field-edit:focus-visible,.level-card-mini a:focus-visible { outline: 2px solid var(--color-border-focus); outline-offset: 2px; }
.level-card-mini a { display: grid; width: 2.75rem; height: 2.75rem; border-radius: var(--radius-sm); place-items: center; }
@media (max-width: 1000px) { .profile-layout { grid-template-columns: 1fr; }.profile-aside { grid-template-columns: 1fr 1fr; }.completion-card { grid-row: span 2; } }
@media (max-width: 767px) { .profile-hero { align-items: flex-start; flex-wrap: wrap; }.avatar-wrap { width: 4.25rem; height: 4.25rem; border-radius: 1.15rem; font-size: var(--font-size-xl); }.hero-copy { width: calc(100% - 6rem); }.hero-copy h1 { font-size: var(--font-size-xl); }.hero-copy p { align-items: flex-start; flex-direction: column; gap: 0; }.hero-copy p i { display: none; }.level-card-mini { width: 100%; min-width: 0; }.identity-grid,.profile-aside { grid-template-columns: 1fr; }.completion-card { grid-row: auto; }.section-heading { align-items: flex-start; }.locked-label { flex: 0 0 auto; }.identity-help { align-items: flex-start; flex-direction: column; }.account-links a { grid-template-columns: auto minmax(0,1fr) auto; }.account-links a :deep(.status) { display: none; } }
@media (max-width: 399px) {
  .profile-hero { column-gap: var(--space-3); }
  .avatar-wrap { width: 3.75rem; height: 3.75rem; }
  .hero-copy { width: calc(100% - 4.75rem); }
  .hero-copy h2 { font-size: var(--font-size-lg); }
  .section-heading { flex-wrap: wrap; }
  .locked-label { width: 100%; padding-inline-start: calc(2.7rem + var(--space-3)); }
  .identity-help :deep(.app-button) { width: 100%; }
  .account-links a { gap: var(--space-2); padding: var(--space-3); }
  .link-icon { width: 2.5rem; height: 2.5rem; }
}
</style>
