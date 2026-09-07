<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import { useRouter } from 'vue-router'
import AppButton from '@/components/ui/AppButton.vue'
import AppCard from '@/components/ui/AppCard.vue'
import AppIcon from '@/components/ui/AppIcon.vue'
import AppModal from '@/components/ui/AppModal.vue'
import AppSkeleton from '@/components/ui/AppSkeleton.vue'
import PageHeader from '@/components/ui/PageHeader.vue'
import StatusBadge from '@/components/ui/StatusBadge.vue'
import VerificationStepForm from '@/components/verification/VerificationStepForm.vue'
import { userService, verificationService } from '@/services'
import { useAuthStore } from '@/stores/auth'
import type {
  UserProfile,
  VerificationStep,
  VerificationSummary,
} from '@/types'
import { formatPercentage, formatPersianDate, formatToman, toPersianDigits } from '@/utils/formatters'

interface LimitRow {
  key: string
  label: string
  icon: string
  limit: string
  used: string
}

const router = useRouter()
const auth = useAuthStore()
const summary = ref<VerificationSummary | null>(null)
const profile = ref<UserProfile | null>(null)
const loading = ref(true)
const error = ref('')
const feedback = ref('')
const activeStep = ref<VerificationStep | null>(null)

const currentLevel = computed(() => summary.value?.levels.find((level) => level.active))
const nextLevel = computed(() => {
  if (!summary.value) return undefined
  const activeIndex = summary.value.levels.findIndex((level) => level.active)
  return summary.value.levels[activeIndex + 1]
})
const requiredSteps = computed(() => summary.value?.steps.filter((step) => step.required) ?? [])
const verifiedRequiredSteps = computed(() => requiredSteps.value.filter((step) => step.status === 'verified').length)
const requiredProgress = computed(() => requiredSteps.value.length
  ? Math.round((verifiedRequiredSteps.value / requiredSteps.value.length) * 100)
  : 100)
const wizardCurrentStep = computed(() => requiredSteps.value.find((step) => step.status !== 'verified') ?? null)
const isWizardMode = computed(() => Boolean(
  summary.value
  && summary.value.status !== 'verified'
  && wizardCurrentStep.value,
))
const wizardStepIndex = computed(() => {
  if (!wizardCurrentStep.value) return 0
  return Math.max(0, requiredSteps.value.findIndex((step) => step.id === wizardCurrentStep.value?.id))
})
const wizardProgress = computed(() => {
  if (!requiredSteps.value.length) return 0
  return Math.round((requiredSteps.value.filter((step) => step.status === 'verified').length / requiredSteps.value.length) * 100)
})

const limitRows = computed<LimitRow[]>(() => {
  const limits = summary.value?.limits
  if (!limits) return []
  return [
    { key: 'buy', label: 'خرید روزانه', icon: 'arrowDown', limit: limits.dailyBuy, used: limits.usedBuy },
    { key: 'sell', label: 'فروش روزانه', icon: 'arrowUp', limit: limits.dailySell, used: limits.usedSell },
    { key: 'deposit', label: 'واریز تومان', icon: 'plus', limit: limits.dailyTomanDeposit, used: limits.usedTomanDeposit },
    { key: 'withdraw', label: 'برداشت تومان', icon: 'minus', limit: limits.dailyTomanWithdrawal, used: limits.usedTomanWithdrawal },
    { key: 'crypto', label: 'برداشت رمزارز', icon: 'wallet', limit: limits.dailyCryptoWithdrawalTomanEquivalent, used: limits.usedCryptoWithdrawalTomanEquivalent },
  ]
})

function readableError(caught: unknown, fallback: string): string {
  return caught instanceof Error ? caught.message : fallback
}

function levelLabel(level?: string): string {
  const labels: Record<string, string> = {
    level_0: 'سطح صفر', level_1: 'سطح یک', level_2: 'سطح دو', level_3: 'سطح سه',
  }
  return level ? labels[level] ?? level : '—'
}

function remaining(limit: string, used: string): string {
  try {
    const result = BigInt(limit) - BigInt(used)
    return (result < 0n ? 0n : result).toString()
  } catch {
    return '0'
  }
}

function usagePercent(limit: string, used: string): number {
  try {
    const total = BigInt(limit)
    if (total <= 0n) return 0
    const ratio = (BigInt(used) * 100n) / total
    return Math.min(100, Math.max(0, Number(ratio)))
  } catch {
    return 0
  }
}

function benefitValue(value: string): string {
  return /^\d+$/.test(value) ? formatToman(value) : value
}

async function load(): Promise<void> {
  loading.value = true
  error.value = ''
  const [verificationResult, profileResult] = await Promise.allSettled([
    verificationService.getSummary(),
    userService.getProfile(),
  ])
  if (verificationResult.status === 'fulfilled') summary.value = verificationResult.value
  else {
    summary.value = null
    error.value = readableError(verificationResult.reason, 'اطلاعات احراز هویت بارگیری نشد.')
  }
  if (profileResult.status === 'fulfilled') profile.value = profileResult.value
  else {
    profile.value = null
    if (verificationResult.status === 'fulfilled') {
      error.value = readableError(profileResult.reason, 'اطلاعات پروفایل بارگیری نشد؛ وضعیت احراز هویت همچنان به‌روز است.')
    }
  }
  loading.value = false
}

async function openStep(step: VerificationStep): Promise<void> {
  feedback.value = ''

  if (step.id === 'bank' && step.status === 'verified') {
    void router.push(step.actionRoute || '/app/bank-accounts')
    return
  }
  if (step.id === 'mobile' && step.status === 'verified') return
  activeStep.value = step
}

async function handleStepSubmitted(message: string): Promise<void> {
  activeStep.value = null
  feedback.value = message
  await Promise.allSettled([load(), auth.refreshUser()])
}

function maskedNationalId(value: string): string {
  const digits = value.replace(/\D/g, '')
  if (!digits) return '—'
  if (digits.length < 6) return toPersianDigits('•'.repeat(digits.length))
  return toPersianDigits(`${digits.slice(0, 2)}${'•'.repeat(Math.max(1, digits.length - 5))}${digits.slice(-3)}`)
}

onMounted(load)
</script>

<template>
  <div class="page verification-page">
    <PageHeader title="احراز هویت" description="وضعیت حساب، مراحل باقی‌مانده و سقف‌های روزانه را یک‌جا ببینید." />

    <div v-if="feedback" class="page-notice success" role="status">
      <AppIcon name="check" :size="20" /><span>{{ feedback }}</span>
      <button type="button" aria-label="بستن" @click="feedback = ''"><AppIcon name="close" :size="17" /></button>
    </div>
    <div v-if="error" class="page-notice danger" role="alert">
      <AppIcon name="warning" :size="20" /><span>{{ error }}</span>
      <button type="button" @click="load">تلاش دوباره</button>
    </div>

    <template v-if="loading">
      <AppCard padding="lg"><div class="hero-skeleton"><AppSkeleton height="5rem" width="5rem" radius="1.4rem" /><div><AppSkeleton height="1.7rem" width="11rem" /><AppSkeleton height="1rem" width="18rem" /></div></div></AppCard>
      <div class="verification-layout">
        <AppCard padding="lg"><AppSkeleton v-for="i in 4" :key="i" height="4.5rem" :style="{ marginBottom: '1rem' }" /></AppCard>
        <AppCard padding="lg"><AppSkeleton v-for="i in 4" :key="i" height="3.5rem" :style="{ marginBottom: '1rem' }" /></AppCard>
      </div>
    </template>

    <template v-else-if="summary">
      <section v-if="isWizardMode && wizardCurrentStep" class="verification-wizard" aria-labelledby="verification-wizard-title">
        <AppCard class="wizard-progress" padding="lg">
          <div class="wizard-progress__copy">
            <span>مرحله {{ toPersianDigits(wizardStepIndex + 1) }} از {{ toPersianDigits(requiredSteps.length) }}</span>
            <h2 id="verification-wizard-title">تکمیل احراز هویت</h2>
            <p>هر بار فقط اطلاعات لازم همین مرحله را کامل کنید؛ وضعیت مراحل قبلی حفظ می‌شود.</p>
          </div>
          <div
            class="wizard-progress__value"
            role="progressbar"
            aria-label="پیشرفت احراز هویت"
            aria-valuemin="0"
            aria-valuemax="100"
            :aria-valuenow="wizardProgress"
          >
            <strong>{{ toPersianDigits(wizardProgress) }}٪</strong>
            <span>تکمیل‌شده</span>
          </div>
          <ol
            class="wizard-steps"
            aria-label="مراحل احراز هویت"
            :style="{ '--wizard-count': requiredSteps.length }"
          >
            <li
              v-for="(step, index) in requiredSteps"
              :key="step.id"
              :class="{
                complete: step.status === 'verified',
                current: step.id === wizardCurrentStep.id,
              }"
              :aria-current="step.id === wizardCurrentStep.id ? 'step' : undefined"
            >
              <span><AppIcon v-if="step.status === 'verified'" name="check" :size="16" /><template v-else>{{ toPersianDigits(index + 1) }}</template></span>
              <b>{{ step.title }}</b>
            </li>
          </ol>
        </AppCard>

        <div class="wizard-layout">
          <AppCard class="wizard-form-card" padding="lg">
            <header class="wizard-form-heading">
              <span class="heading-icon"><AppIcon :name="wizardCurrentStep.id === 'bank' ? 'bank' : wizardCurrentStep.id === 'mobile' ? 'phone' : 'verify'" :size="22" /></span>
              <div>
                <span>مرحله جاری</span>
                <h2>{{ wizardCurrentStep.title }}</h2>
                <p>{{ wizardCurrentStep.description }}</p>
              </div>
              <StatusBadge domain="kyc" :status="wizardCurrentStep.status" />
            </header>
            <VerificationStepForm
              :step="wizardCurrentStep"
              :profile="profile"
              @submitted="handleStepSubmitted"
            />
          </AppCard>

          <aside class="wizard-aside">
            <AppCard padding="lg" class="wizard-trust-card">
              <span class="wizard-trust-icon"><AppIcon name="shield" :size="28" /></span>
              <div><h2>اطلاعات شما امن است</h2><p>اطلاعات هویتی فقط برای تطبیق مالکیت حساب و رعایت الزامات مالی استفاده می‌شود.</p></div>
              <ul>
                <li><AppIcon name="check" :size="16" />ارتباط رمزنگاری‌شده</li>
                <li><AppIcon name="check" :size="16" />بررسی فقط توسط سامانه احراز هویت</li>
                <li><AppIcon name="check" :size="16" />اعلام نتیجه از طریق اعلان حساب</li>
              </ul>
            </AppCard>
            <AppCard padding="lg" class="wizard-help-card">
              <AppIcon name="help" :size="22" />
              <div><strong>در این مرحله مشکلی دارید؟</strong><p>پشتیبانی روشا برای تکمیل احراز هویت همراه شماست.</p><RouterLink to="/app/support">ارتباط با پشتیبانی</RouterLink></div>
            </AppCard>
          </aside>
        </div>
      </section>

      <template v-else>
      <AppCard class="verification-hero" padding="lg">
        <div
          class="level-orbit"
          :style="{ '--progress': `${requiredProgress * 3.6}deg` }"
          role="progressbar"
          aria-label="درصد تکمیل احراز هویت"
          aria-valuemin="0"
          aria-valuemax="100"
          :aria-valuenow="requiredProgress"
        >
          <span><strong>{{ toPersianDigits(requiredProgress) }}٪</strong><small>ضروری</small></span>
        </div>
        <div class="hero-copy">
          <div class="hero-title">
            <span class="eyebrow">سطح فعلی حساب</span>
            <h2>{{ currentLevel?.title || levelLabel(summary.currentLevel) }}</h2>
            <StatusBadge domain="kyc" :status="summary.status" />
          </div>
          <p>{{ summary.message }}</p>
          <div v-if="nextLevel" class="next-level">
            <AppIcon name="sparkle" :size="19" />
            <span>گام بعدی: <strong>{{ nextLevel.title }}</strong>؛ {{ nextLevel.description }}</span>
          </div>
        </div>
        <div class="trust-mark"><AppIcon name="shield" :size="30" /><span>اطلاعات شما<br />رمزنگاری می‌شود</span></div>
      </AppCard>

      <div class="verification-layout">
        <AppCard padding="lg" class="steps-card">
          <div class="card-heading">
            <div><span class="heading-icon"><AppIcon name="verify" :size="21" /></span><div><h2>مراحل احراز هویت</h2><p>هر مرحله وضعیت و اقدام بعدی را شفاف نشان می‌دهد.</p></div></div>
            <span>{{ toPersianDigits(verifiedRequiredSteps) }} از {{ toPersianDigits(requiredSteps.length) }} ضروری</span>
          </div>
          <ol class="steps-list">
            <li v-for="(step, index) in summary.steps" :key="step.id" :class="[`status-${step.status}`, { optional: !step.required }]">
              <span class="step-index">
                <AppIcon v-if="step.status === 'verified'" name="check" :size="17" />
                <span v-else>{{ toPersianDigits(index + 1) }}</span>
              </span>
              <div class="step-copy">
                <div class="step-title"><h3>{{ step.title }}</h3><span v-if="!step.required">اختیاری</span></div>
                <p>{{ step.description }}</p>
                <div v-if="step.rejectionReason" class="rejection-reason">
                  <AppIcon name="warning" :size="17" />
                  <span><strong>علت نیاز به اصلاح:</strong> {{ step.rejectionReason }}</span>
                </div>
                <small v-if="step.completedAt">تکمیل در {{ formatPersianDate(step.completedAt) }}</small>
              </div>
              <div class="step-action">
                <StatusBadge domain="kyc" :status="step.status" />
                <AppButton
                  v-if="step.actionLabel || ['not_started', 'needs_correction', 'rejected'].includes(step.status)"
                  variant="secondary"
                  size="sm"
                  :icon="step.status === 'needs_correction' || step.status === 'rejected' ? 'refresh' : 'chevronLeft'"
                  @click="openStep(step)"
                >{{ step.status === 'needs_correction' || step.status === 'rejected' ? 'ارسال مجدد' : step.actionLabel || 'شروع مرحله' }}</AppButton>
              </div>
            </li>
          </ol>
        </AppCard>

        <div class="side-stack">
          <AppCard padding="lg" class="limits-card">
            <div class="card-heading compact">
              <div><span class="heading-icon"><AppIcon name="wallet" :size="20" /></span><div><h2>سقف‌های امروز</h2><p>{{ levelLabel(summary.limits.accountLevel) }}</p></div></div>
            </div>
            <div class="limit-list">
              <div v-for="row in limitRows" :key="row.key" class="limit-row">
                <div class="limit-title"><span><AppIcon :name="row.icon" :size="17" />{{ row.label }}</span><strong>{{ formatPercentage(usagePercent(row.limit, row.used), { maximumFractionDigits: 0 }) }} مصرف</strong></div>
                <div
                  class="progress-track"
                  role="progressbar"
                  :aria-label="`مصرف سقف ${row.label}`"
                  aria-valuemin="0"
                  aria-valuemax="100"
                  :aria-valuenow="usagePercent(row.limit, row.used)"
                ><i :style="{ width: `${usagePercent(row.limit, row.used)}%` }" /></div>
                <div class="limit-values"><span>باقی‌مانده {{ formatToman(remaining(row.limit, row.used)) }}</span><small>از {{ formatToman(row.limit) }}</small></div>
              </div>
            </div>
          </AppCard>

          <AppCard v-if="profile" padding="lg" class="identity-card">
            <div class="identity-avatar">{{ profile.firstName.charAt(0) }}{{ profile.lastName.charAt(0) }}</div>
            <div><strong>{{ profile.fullName }}</strong><bdi dir="ltr">{{ maskedNationalId(profile.nationalId) }}</bdi></div>
            <span class="verified-seal"><AppIcon name="check" :size="15" />هویت تأییدشده</span>
          </AppCard>
        </div>
      </div>

      <section class="levels-section">
        <div class="section-heading"><div><h2>سطوح کاربری</h2><p>با تکمیل مراحل بعدی، سقف‌ها و خدمات بیشتری در دسترس قرار می‌گیرد.</p></div></div>
        <div class="levels-grid">
          <AppCard v-for="level in summary.levels" :key="level.level" padding="lg" class="level-card" :class="{ active: level.active }">
            <header><span class="level-badge"><AppIcon :name="level.active ? 'star' : 'shield'" :size="20" /></span><div><h3>{{ level.title }}</h3><p>{{ level.description }}</p></div><span v-if="level.active" class="active-label">سطح شما</span></header>
            <div class="level-section"><span>نیازمندی‌ها</span><ul><li v-for="item in level.requirements" :key="item"><AppIcon name="check" :size="15" />{{ item }}</li></ul></div>
            <div class="benefit-list"><div v-for="benefit in level.benefits" :key="benefit.label"><span>{{ benefit.label }}</span><strong>{{ benefitValue(String(benefit.value)) }}</strong></div></div>
          </AppCard>
        </div>
      </section>
      </template>
    </template>

    <AppModal
      v-if="!isWizardMode"
      :model-value="Boolean(activeStep)"
      :title="activeStep?.title"
      :description="activeStep?.status === 'needs_correction' ? 'اطلاعات اصلاح‌شده را دوباره ارسال کنید.' : 'اطلاعات این مرحله پس از ارسال بررسی می‌شود.'"
      size="md"
      @update:model-value="(value) => { if (!value) activeStep = null }"
    >
      <VerificationStepForm
        v-if="activeStep"
        :step="activeStep"
        :profile="profile"
        allow-cancel
        @submitted="handleStepSubmitted"
        @cancel="activeStep = null"
      />
    </AppModal>
  </div>
</template>

<style scoped>
.verification-page { display: grid; align-content: start; gap: var(--space-5); }
.verification-page :deep(.page-header) { margin-bottom: 0; }
.page-notice { display: flex; align-items: center; gap: var(--space-3); padding: var(--space-3) var(--space-4); border: 1px solid; border-radius: var(--radius-md); font-size: var(--font-size-sm); }
.page-notice span { flex: 1; }.page-notice button { border: 0; background: transparent; color: inherit; font-weight: 600; }
.page-notice.success { border-color: rgba(53,201,149,.24); background: var(--color-success-soft); color: var(--color-success); }
.page-notice.danger { border-color: rgba(240,108,117,.24); background: var(--color-danger-soft); color: var(--color-danger); }
.hero-skeleton { display: flex; align-items: center; gap: var(--space-5); }.hero-skeleton > div { display: grid; grid-template-columns: minmax(0, 1fr); min-width: 0; flex: 1; gap: var(--space-3); }.hero-skeleton :deep(.skeleton) { max-width: 100%; }
.verification-wizard { display: grid; gap: var(--space-5); }
.wizard-progress { display: grid; grid-template-columns: minmax(0, 1fr) auto; gap: var(--space-5); overflow: hidden; background: linear-gradient(120deg, var(--color-surface-1) 45%, var(--color-primary-soft)); }
.wizard-progress__copy > span,.wizard-form-heading > div > span { color: var(--color-primary); font-size: var(--font-size-xs); font-weight: 700; }
.wizard-progress__copy h2 { margin: var(--space-1) 0; font-size: var(--font-size-2xl); }
.wizard-progress__copy p { max-width: 42rem; margin: 0; color: var(--color-text-muted); font-size: var(--font-size-sm); }
.wizard-progress__value { display: grid; min-width: 6.5rem; align-content: center; padding-inline: var(--space-5); border-inline-start: 1px solid var(--color-border-soft); text-align: center; }
.wizard-progress__value strong { color: var(--color-primary); font-size: var(--font-size-2xl); }
.wizard-progress__value span { color: var(--color-text-muted); font-size: var(--font-size-xs); }
.wizard-steps { grid-column: 1 / -1; display: grid; grid-template-columns: repeat(var(--wizard-count, 5), minmax(0, 1fr)); margin: 0; padding: var(--space-4) 0 0; border-top: 1px solid var(--color-border-soft); list-style: none; }
.wizard-steps li { position: relative; display: grid; justify-items: center; gap: var(--space-2); color: var(--color-text-muted); font-size: var(--font-size-xs); text-align: center; }
.wizard-steps li::before { position: absolute; z-index: 0; inset-block-start: 1.05rem; inset-inline: calc(50% + 1.1rem) calc(-50% + 1.1rem); height: 1px; background: var(--color-border-hover); content: ''; }
.wizard-steps li:first-child::before { display: none; }
.wizard-steps li > span { z-index: 1; display: grid; width: 2.1rem; height: 2.1rem; border: 2px solid var(--color-border-hover); border-radius: 50%; background: var(--color-surface-1); place-items: center; }
.wizard-steps li.complete > span { border-color: var(--color-success); background: var(--color-success); color: var(--on-success); }
.wizard-steps li.complete::before { background: var(--color-success); }
.wizard-steps li.current { color: var(--color-text-primary); }
.wizard-steps li.current > span { border-color: var(--color-primary); box-shadow: 0 0 0 4px var(--color-primary-soft); color: var(--color-primary); }
.wizard-layout { display: grid; grid-template-columns: minmax(0, 1.4fr) minmax(18rem, .6fr); align-items: start; gap: var(--space-5); }
.wizard-form-heading { display: flex; align-items: flex-start; gap: var(--space-3); margin-bottom: var(--space-5); padding-bottom: var(--space-4); border-bottom: 1px solid var(--color-border-soft); }
.wizard-form-heading > div { min-width: 0; flex: 1; }
.wizard-form-heading h2 { margin: .15rem 0; font-size: var(--font-size-xl); }
.wizard-form-heading p { margin: 0; color: var(--color-text-muted); font-size: var(--font-size-sm); }
.wizard-aside { display: grid; gap: var(--space-4); }
.wizard-trust-card { display: grid; gap: var(--space-4); background: linear-gradient(145deg, var(--color-surface-1), var(--color-success-soft)); }
.wizard-trust-icon { display: grid; width: 3.5rem; height: 3.5rem; border-radius: 1rem; background: var(--color-success-soft); color: var(--color-success); place-items: center; }
.wizard-trust-card h2 { margin: 0; font-size: var(--font-size-lg); }
.wizard-trust-card p,.wizard-help-card p { margin: .25rem 0 0; color: var(--color-text-muted); font-size: var(--font-size-xs); }
.wizard-trust-card ul { display: grid; gap: var(--space-2); margin: 0; padding: var(--space-4) 0 0; border-top: 1px solid var(--color-border-soft); list-style: none; }
.wizard-trust-card li { display: flex; align-items: center; gap: var(--space-2); color: var(--color-text-secondary); font-size: var(--font-size-xs); }
.wizard-trust-card li svg { color: var(--color-success); }
.wizard-help-card { display: flex; align-items: flex-start; gap: var(--space-3); }
.wizard-help-card > svg { flex: 0 0 auto; color: var(--color-primary); }
.wizard-help-card a { display: inline-block; margin-top: var(--space-2); color: var(--color-primary); font-size: var(--font-size-xs); font-weight: 700; }
.verification-hero { position: relative; display: flex; align-items: center; gap: var(--space-6); overflow: hidden; background: linear-gradient(120deg, var(--color-surface-1) 45%, var(--color-primary-soft)); }
.verification-hero::after { position: absolute; width: 18rem; height: 18rem; inset-block-start: -10rem; inset-inline-end: -6rem; border: 1px solid rgba(67,139,255,.12); border-radius: 50%; content: ''; }
.level-orbit { position: relative; display: grid; width: 7rem; height: 7rem; flex: 0 0 auto; border-radius: 50%; background: conic-gradient(var(--color-primary) var(--progress), var(--color-surface-3) 0); place-items: center; }
.level-orbit::before { position: absolute; inset: .45rem; border-radius: 50%; background: var(--color-surface-1); content: ''; }
.level-orbit span { position: relative; display: grid; text-align: center; }.level-orbit strong { font-size: var(--font-size-xl); }.level-orbit small { color: var(--color-text-muted); font-size: var(--font-size-xs); }
.hero-copy { min-width: 0; flex: 1; }.hero-title { display: flex; align-items: center; flex-wrap: wrap; gap: var(--space-3); }.eyebrow { width: 100%; color: var(--color-primary); font-size: var(--font-size-xs); font-weight: 600; }.hero-title h2 { margin: 0; font-size: var(--font-size-2xl); }.hero-copy > p { margin: var(--space-2) 0; color: var(--color-text-secondary); }
.next-level { display: inline-flex; align-items: center; gap: var(--space-2); margin-top: var(--space-2); padding: .55rem .8rem; border-radius: var(--radius-md); background: var(--color-gold-soft); color: var(--color-gold); font-size: var(--font-size-xs); }.next-level span { color: var(--color-text-secondary); }.next-level strong { color: var(--color-gold); }
.trust-mark { position: relative; z-index: 1; display: flex; align-items: center; gap: var(--space-2); padding: var(--space-4); border: 1px solid rgba(67,139,255,.16); border-radius: var(--radius-lg); background: rgba(7,17,30,.32); color: var(--color-primary); }.trust-mark span { color: var(--color-text-muted); font-size: var(--font-size-xs); line-height: 1.7; }
.verification-layout { display: grid; grid-template-columns: minmax(0, 1.55fr) minmax(20rem, .75fr); align-items: start; gap: var(--space-5); }.side-stack { display: grid; gap: var(--space-5); }
.card-heading { display: flex; align-items: center; justify-content: space-between; gap: var(--space-4); margin-bottom: var(--space-5); }.card-heading > div { display: flex; align-items: center; gap: var(--space-3); }.heading-icon { display: grid; width: 2.65rem; height: 2.65rem; flex: 0 0 auto; border-radius: .85rem; background: var(--color-primary-soft); color: var(--color-primary); place-items: center; }.card-heading h2 { margin: 0; font-size: var(--font-size-lg); }.card-heading p { margin: .15rem 0 0; color: var(--color-text-muted); font-size: var(--font-size-xs); }.card-heading > span { color: var(--color-text-muted); font-size: var(--font-size-sm); }.card-heading.compact { margin-bottom: var(--space-4); }
.steps-list { display: grid; margin: 0; padding: 0; list-style: none; }.steps-list li { position: relative; display: grid; grid-template-columns: auto minmax(0, 1fr) auto; gap: var(--space-3); padding-block: var(--space-4); }.steps-list li + li { border-top: 1px solid var(--color-border-soft); }.step-index { display: grid; width: 2rem; height: 2rem; margin-top: .1rem; border: 2px solid var(--color-border-hover); border-radius: 50%; background: var(--color-surface-2); color: var(--color-text-muted); font-size: var(--font-size-xs); place-items: center; }.status-verified .step-index { border-color: var(--color-success); background: var(--color-success); color: white; }.status-needs_correction .step-index,.status-rejected .step-index { border-color: var(--color-warning); background: var(--color-warning-soft); color: var(--color-warning); }.status-pending .step-index { border-color: var(--color-warning); color: var(--color-warning); }
.step-copy h3 { margin: 0; font-size: var(--font-size-md); }.step-title { display: flex; align-items: center; gap: var(--space-2); }.step-title > span { padding: .05rem .42rem; border-radius: var(--radius-pill); background: var(--color-surface-3); color: var(--color-text-muted); font-size: .66rem; }.step-copy p { margin: .25rem 0; color: var(--color-text-muted); font-size: var(--font-size-sm); }.step-copy small { color: var(--color-success); font-size: var(--font-size-xs); }.step-action { display: grid; justify-items: end; align-content: start; gap: var(--space-2); }.rejection-reason { display: flex; align-items: start; gap: var(--space-2); margin-block: var(--space-2); padding: var(--space-2) var(--space-3); border-radius: var(--radius-sm); background: var(--color-warning-soft); color: var(--color-warning); font-size: var(--font-size-xs); }.rejection-reason strong { color: var(--color-warning); }
.limit-list { display: grid; gap: var(--space-4); }.limit-row { display: grid; gap: var(--space-2); }.limit-title,.limit-values { display: flex; align-items: center; justify-content: space-between; gap: var(--space-3); }.limit-title > span { display: flex; align-items: center; gap: var(--space-2); color: var(--color-text-secondary); font-size: var(--font-size-sm); }.limit-title svg { color: var(--color-primary); }.limit-title strong { color: var(--color-text-muted); font-size: .68rem; }.progress-track { height: .4rem; overflow: hidden; border-radius: var(--radius-pill); background: var(--color-surface-3); }.progress-track i { display: block; height: 100%; border-radius: inherit; background: linear-gradient(90deg, var(--color-primary), var(--color-info)); }.limit-values span { font-size: var(--font-size-xs); }.limit-values small { color: var(--color-text-muted); font-size: .68rem; }
.identity-card { display: flex; align-items: center; gap: var(--space-3); }.identity-avatar { display: grid; width: 3rem; height: 3rem; flex: 0 0 auto; border-radius: 50%; background: var(--color-primary-soft); color: var(--color-primary); font-weight: 700; place-items: center; }.identity-card > div:nth-child(2) { display: grid; flex: 1; }.identity-card > div bdi { color: var(--color-text-muted); font-size: var(--font-size-xs); }.verified-seal { display: inline-flex; align-items: center; gap: .2rem; color: var(--color-success); font-size: var(--font-size-xs); }
.levels-section { display: grid; gap: var(--space-4); }.section-heading h2 { margin: 0; font-size: var(--font-size-xl); }.section-heading p { margin: .15rem 0 0; color: var(--color-text-muted); font-size: var(--font-size-sm); }.levels-grid { display: grid; grid-template-columns: repeat(3, minmax(0, 1fr)); gap: var(--space-5); }.level-card { position: relative; }.level-card.active { border-color: rgba(221,183,110,.4); background: linear-gradient(145deg, var(--color-surface-1), var(--color-gold-soft)); }.level-card header { display: flex; align-items: flex-start; gap: var(--space-3); }.level-badge { display: grid; width: 2.75rem; height: 2.75rem; flex: 0 0 auto; border-radius: .85rem; background: var(--color-surface-3); color: var(--color-text-muted); place-items: center; }.active .level-badge { background: var(--color-gold-soft); color: var(--color-gold); }.level-card h3 { margin: 0; }.level-card header p { margin: .15rem 0 0; color: var(--color-text-muted); font-size: var(--font-size-xs); }.active-label { margin-inline-start: auto; padding: .22rem .55rem; border-radius: var(--radius-pill); background: var(--color-gold-soft); color: var(--color-gold); font-size: var(--font-size-xs); }.level-section { margin-block: var(--space-5); }.level-section > span { color: var(--color-text-muted); font-size: var(--font-size-xs); }.level-section ul { display: grid; gap: var(--space-2); margin: var(--space-2) 0 0; padding: 0; list-style: none; }.level-section li { display: flex; align-items: center; gap: var(--space-2); color: var(--color-text-secondary); font-size: var(--font-size-sm); }.level-section li svg { color: var(--color-success); }.benefit-list { display: grid; gap: var(--space-2); padding-top: var(--space-4); border-top: 1px solid var(--color-border-soft); }.benefit-list > div { display: flex; align-items: center; justify-content: space-between; gap: var(--space-2); }.benefit-list span { color: var(--color-text-muted); font-size: var(--font-size-xs); }.benefit-list strong { font-size: var(--font-size-sm); }
.page-notice button { display: inline-grid; min-width: 2.75rem; min-height: 2.75rem; padding-inline: var(--space-2); border-radius: var(--radius-sm); place-items: center; }
.page-notice button:focus-visible { outline: 2px solid currentColor; outline-offset: 2px; }
.steps-list li { margin-inline: calc(var(--space-2) * -1); padding-inline: var(--space-2); border-radius: var(--radius-md); }
.steps-list li.status-needs_correction,.steps-list li.status-rejected { background: linear-gradient(90deg, var(--color-warning-soft), transparent 72%); }
.limit-values span,.limit-values small { min-width: 0; overflow-wrap: anywhere; }
.level-card { transition: border-color var(--transition-fast), box-shadow var(--transition-fast), transform var(--transition-fast); }
.file-drop:focus-within { border-color: var(--color-border-focus); box-shadow: var(--shadow-focus); }
@media (hover: hover) { .level-card:hover { border-color: var(--color-border-hover); box-shadow: var(--shadow-sm); transform: translateY(-2px); } }
@media (max-width: 1100px) { .verification-layout,.wizard-layout { grid-template-columns: 1fr; }.side-stack,.wizard-aside { grid-template-columns: 1fr 1fr; }.levels-grid { grid-template-columns: 1fr 1fr; } }
@media (max-width: 1199px) {
  .wizard-form-card :deep(.form-actions) { position: sticky; z-index: 2; bottom: calc(var(--mobile-nav-height) + var(--safe-bottom) + var(--space-2)); margin: var(--space-2) calc(var(--space-4) * -1) calc(var(--space-4) * -1); padding: var(--space-3) var(--space-4) var(--space-4); border-top: 1px solid var(--color-border); background: color-mix(in srgb, var(--color-surface-1) 94%, transparent); backdrop-filter: blur(14px); }
}
@media (max-width: 767px) {
  .wizard-progress { grid-template-columns: minmax(0, 1fr) auto; gap: var(--space-4); }
  .wizard-progress__copy h2 { font-size: var(--font-size-xl); }
  .wizard-progress__value { min-width: 4.5rem; padding-inline: var(--space-3); }
  .wizard-progress__value strong { font-size: var(--font-size-xl); }
  .wizard-steps { display: none; }
  .wizard-aside,.side-stack,.levels-grid { grid-template-columns: 1fr; }
  .verification-hero { align-items: flex-start; flex-wrap: wrap; gap: var(--space-4); }.level-orbit { width: 5.5rem; height: 5.5rem; }.hero-copy { width: calc(100% - 7rem); }.hero-title h2 { font-size: var(--font-size-xl); }.trust-mark { width: 100%; justify-content: center; }.steps-list li { grid-template-columns: auto minmax(0,1fr); }.step-action { grid-column: 2; grid-template-columns: auto auto; align-items: center; justify-content: start; justify-items: start; }.step-action :deep(.app-button) { min-height: 2.25rem; }.identity-card { flex-wrap: wrap; }.verified-seal { width: 100%; padding-inline-start: 4rem; }
}
@media (max-width: 399px) {
  .wizard-progress { grid-template-columns: minmax(0, 1fr); }
  .wizard-progress__value { grid-row: 1; grid-column: 1; justify-self: end; border-inline-start: 0; }
  .wizard-progress__copy { padding-inline-end: 4.5rem; }
  .wizard-progress__copy p { display: none; }
  .wizard-form-heading { display: grid; grid-template-columns: auto minmax(0, 1fr); }
  .wizard-form-heading :deep(.status-badge) { grid-column: 2; justify-self: start; }
  .verification-hero { display: grid; grid-template-columns: auto minmax(0, 1fr); }
  .level-orbit { width: 4.75rem; height: 4.75rem; }
  .level-orbit strong { font-size: var(--font-size-lg); }
  .hero-copy { width: auto; }
  .hero-title { gap: var(--space-2); }
  .hero-title h2 { font-size: var(--font-size-lg); }
  .next-level { align-items: flex-start; }
  .trust-mark { grid-column: 1 / -1; }
  .card-heading { align-items: flex-start; }
  .card-heading > span { white-space: nowrap; }
  .step-action { grid-template-columns: 1fr; width: 100%; }
  .step-action :deep(.app-button) { width: 100%; min-height: 2.75rem; }
  .limit-title,.limit-values { align-items: flex-start; }
  .limit-values { flex-direction: column; gap: .1rem; }
}
</style>
