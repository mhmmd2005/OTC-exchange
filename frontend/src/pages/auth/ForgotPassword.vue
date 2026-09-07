<script setup lang="ts">
import { computed, ref } from 'vue'
import { RouterLink, useRoute, useRouter } from 'vue-router'
import { useAuthStore } from '@/stores/auth'
import AppButton from '@/components/ui/AppButton.vue'
import AppCard from '@/components/ui/AppCard.vue'
import AppIcon from '@/components/ui/AppIcon.vue'
import AppInput from '@/components/ui/AppInput.vue'
import { isValidMobile, normalizeMobile } from './auth.utils'

const router = useRouter()
const route = useRoute()
const auth = useAuthStore()
const rawMobile = ref('')
const loading = ref(false)
const touched = ref(false)
const submitted = ref(false)
const formError = ref('')
const resetProofExpired = computed(() => route.query.proof === 'expired')

const mobile = computed({
  get: () => rawMobile.value,
  set: (value: string) => { rawMobile.value = normalizeMobile(value) },
})

const mobileError = computed(() => {
  if (!submitted.value && !touched.value) return ''
  if (!mobile.value) return 'شماره موبایل را وارد کنید.'
  return isValidMobile(mobile.value) ? '' : 'شماره موبایل معتبر نیست؛ مانند ۰۹۱۲۱۲۳۴۵۶۷ وارد کنید.'
})

async function requestResetCode() {
  submitted.value = true
  formError.value = ''
  if (mobileError.value) return

  loading.value = true
  try {
    await auth.requestOtp({ mobile: mobile.value, purpose: 'reset_password' })
    await router.push({
      path: '/auth/verify',
      query: { purpose: 'reset_password' },
    })
  } catch (error) {
    formError.value = error instanceof Error ? error.message : 'ارسال کد ممکن نشد. اتصال اینترنت خود را بررسی کنید.'
  } finally {
    loading.value = false
  }
}
</script>

<template>
  <AppCard padding="lg" class="auth-view">
    <div class="reset-icon" aria-hidden="true"><AppIcon name="lock" :size="25" /></div>

    <div class="auth-intro">
      <span class="auth-kicker">بازیابی امن حساب</span>
      <h1 class="auth-title">رمز عبور را فراموش کرده‌اید؟</h1>
      <p class="auth-description">
        شماره موبایل حساب خود را وارد کنید تا کد تأیید برایتان ارسال شود.
      </p>
    </div>

    <ol class="reset-steps" aria-label="مراحل بازیابی رمز عبور">
      <li class="active"><span>۱</span><small>شماره موبایل</small></li>
      <li><span>۲</span><small>تأیید کد</small></li>
      <li><span>۳</span><small>رمز جدید</small></li>
    </ol>

    <div v-if="resetProofExpired" class="auth-alert" role="status">
      <AppIcon name="clock" :size="18" />
      <span>مهلت تغییر رمز عبور به پایان رسیده است. برای ادامه یک کد تازه بگیرید.</span>
    </div>

    <form class="auth-form" novalidate @submit.prevent="requestResetCode">
      <AppInput
        v-model="mobile"
        label="شماره موبایل"
        placeholder="۰۹۱۲۱۲۳۴۵۶۷"
        inputmode="tel"
        autocomplete="tel"
        name="mobile"
        icon="phone"
        ltr
        :error="mobileError"
        hint="همان شماره‌ای که با آن ثبت‌نام کرده‌اید."
        @blur="touched = true"
      />

      <div v-if="formError" class="auth-alert" role="alert">
        <AppIcon name="warning" :size="18" />
        <span>{{ formError }}</span>
      </div>

      <AppButton type="submit" size="lg" block :loading="loading">
        دریافت کد تأیید
      </AppButton>
    </form>

    <p class="auth-footer">
      رمز عبور را به یاد آوردید؟
      <RouterLink class="auth-link" to="/auth/login">بازگشت به ورود</RouterLink>
    </p>
  </AppCard>
</template>

<style scoped>
.reset-icon {
  display: grid;
  width: 3.5rem;
  height: 3.5rem;
  margin-bottom: var(--space-5);
  border: 1px solid rgba(221, 183, 110, .22);
  border-radius: 1.1rem;
  background: var(--color-gold-soft);
  color: var(--color-gold);
  place-items: center;
}

.reset-steps {
  position: relative;
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  margin: 0 0 var(--space-7);
  padding: 0;
  list-style: none;
}

.reset-steps::before {
  position: absolute;
  inset: 1rem 16.66% auto;
  height: 1px;
  background: var(--color-border);
  content: '';
}

.reset-steps li {
  position: relative;
  display: grid;
  justify-items: center;
  gap: var(--space-1);
  color: var(--color-text-muted);
}

.reset-steps span {
  z-index: 1;
  display: grid;
  width: 2rem;
  height: 2rem;
  border: 1px solid var(--color-border);
  border-radius: 50%;
  background: var(--color-surface-1);
  font-size: var(--font-size-xs);
  font-weight: 600;
  place-items: center;
}

.reset-steps small { font-size: .67rem; }
.reset-steps .active { color: var(--color-primary); }
.reset-steps .active span { border-color: var(--color-primary); background: var(--color-primary-soft); }
.auth-alert { margin-bottom: var(--space-5); }
</style>
