<script setup lang="ts">
import { computed, defineAsyncComponent, ref, watch } from 'vue'
import { RouterLink, useRoute, useRouter } from 'vue-router'
import { useAuthStore } from '@/stores/auth'
import AppButton from '@/components/ui/AppButton.vue'
import AppCard from '@/components/ui/AppCard.vue'
import AppIcon from '@/components/ui/AppIcon.vue'
import OtpInput from '@/components/ui/OtpInput.vue'
import type { OtpPurpose } from '@/types'
import { maskMobile, queryValue, safeAppRedirect } from './auth.utils'

const DemoCodeHint = import.meta.env.DEV && import.meta.env.VITE_USE_MOCK_API === 'true'
  ? defineAsyncComponent(() => import('@/components/ui/DemoCodeHint.vue'))
  : null

const route = useRoute()
const router = useRouter()
const auth = useAuthStore()
const code = ref('')
const loading = ref(false)
const resendLoading = ref(false)
const otpError = ref('')
const resendMessage = ref('')

const purpose = computed<OtpPurpose>(() => {
  const requested = queryValue(route.query.purpose)
  return requested === 'reset_password' || requested === 'login' ? requested : 'register'
})
const activeChallenge = computed(() => {
  const challenge = auth.otpChallenge
  return challenge?.purpose === purpose.value ? challenge : null
})
const mobile = computed(() => activeChallenge.value?.mobile ?? '')
const isPasswordReset = computed(() => purpose.value === 'reset_password')
const isAccountVerification = computed(() => queryValue(route.query.context) === 'kyc')
const returnTo = computed(() => safeAppRedirect(
  route.query.returnTo,
  isAccountVerification.value ? '/app/verification' : '/app/dashboard?welcome=1',
))
const maskedMobile = computed(() => maskMobile(mobile.value))
const editRoute = computed(() => isPasswordReset.value
  ? '/auth/forgot-password'
  : isAccountVerification.value ? '/app/verification' : '/auth/register')
const backLabel = computed(() => isPasswordReset.value
  ? 'بازگشت به بازیابی رمز عبور'
  : isAccountVerification.value ? 'بازگشت به احراز هویت' : 'بازگشت به ثبت‌نام')
const challengeMissing = computed(() => !activeChallenge.value)

watch(code, () => {
  otpError.value = ''
  resendMessage.value = ''
})

async function verifyCode() {
  if (loading.value) return
  if (!activeChallenge.value) {
    otpError.value = 'درخواست کد در دسترس نیست یا منقضی شده است؛ دوباره کد بگیرید.'
    return
  }
  if (code.value.length !== 6) {
    otpError.value = 'کد تأیید باید ۶ رقم باشد.'
    return
  }

  loading.value = true
  otpError.value = ''
  try {
    if (isPasswordReset.value) {
      await auth.verifyPasswordResetOtp({ challengeId: activeChallenge.value.challengeId, mobile: mobile.value, purpose: 'reset_password', code: code.value })
      await router.push('/auth/reset-password')
    } else {
      await auth.verifyOtp({
        challengeId: activeChallenge.value.challengeId,
        mobile: mobile.value,
        purpose: purpose.value,
        code: code.value,
      })
      await router.push(returnTo.value)
    }
  } catch (error) {
    otpError.value = error instanceof Error ? error.message : 'بررسی کد انجام نشد. لطفاً دوباره تلاش کنید.'
  } finally {
    loading.value = false
  }
}

async function resendCode() {
  if (resendLoading.value) return
  if (!activeChallenge.value) {
    otpError.value = 'برای ارسال کد، شماره موبایل را دوباره وارد کنید.'
    return
  }
  resendLoading.value = true
  otpError.value = ''
  resendMessage.value = ''
  try {
    await auth.requestOtp({ mobile: mobile.value, purpose: purpose.value })
    resendMessage.value = 'کد جدید با موفقیت ارسال شد.'
  } catch (error) {
    otpError.value = error instanceof Error ? error.message : 'ارسال دوباره کد ممکن نشد. چند لحظه دیگر تلاش کنید.'
  } finally {
    resendLoading.value = false
  }
}
</script>

<template>
  <AppCard padding="lg" class="auth-view verify-card">
    <div class="verify-symbol" aria-hidden="true">
      <AppIcon name="phone" :size="26" />
      <span><AppIcon name="check" :size="13" /></span>
    </div>

    <div class="auth-intro verify-intro">
      <span class="auth-kicker">تأیید شماره موبایل</span>
      <h1 class="auth-title">کد پیامک‌شده را وارد کنید</h1>
      <p class="auth-description">
        <template v-if="!challengeMissing">یک کد ۶ رقمی به <strong class="mobile-number" dir="ltr">{{ maskedMobile }}</strong> فرستادیم.</template>
        <template v-else>درخواست قبلی در این مرورگر در دسترس نیست.</template>
        <RouterLink class="auth-link edit-number" :to="editRoute">{{ challengeMissing ? 'دریافت کد تازه' : 'اصلاح شماره' }}</RouterLink>
      </p>
    </div>

    <form class="auth-form" novalidate @submit.prevent="verifyCode">
      <OtpInput
        v-model="code"
        :loading="loading"
        :resend-loading="resendLoading"
        :error="otpError"
        :countdown-seconds="activeChallenge ? Math.max(0, Math.ceil((Date.parse(activeChallenge.resendAt) - Date.now()) / 1000)) : 0"
        :disabled="challengeMissing"
        @complete="verifyCode"
        @resend="resendCode"
      />

      <DemoCodeHint v-if="DemoCodeHint && !challengeMissing" context="otp" />

      <p v-if="resendMessage" class="resend-success" role="status">
        <AppIcon name="check" :size="17" />
        {{ resendMessage }}
      </p>

      <AppButton
        type="submit"
        size="lg"
        block
        :loading="loading"
        :disabled="challengeMissing || code.length !== 6"
      >
        {{ isPasswordReset ? 'تأیید و ادامه' : isAccountVerification ? 'تأیید و بازگشت به احراز هویت' : 'تأیید و ورود به پنل' }}
      </AppButton>

      <div class="auth-security-note">
        <AppIcon name="lock" :size="18" />
        <span>این کد شخصی است. کارشناسان روشا هرگز آن را از شما درخواست نمی‌کنند.</span>
      </div>
    </form>

    <p class="auth-footer">
      <RouterLink class="auth-link back-link" :to="editRoute">
        <AppIcon name="chevronRight" :size="17" />
        {{ backLabel }}
      </RouterLink>
    </p>
  </AppCard>
</template>

<style scoped>
.verify-card { text-align: right; }

.verify-symbol {
  position: relative;
  display: grid;
  width: 3.5rem;
  height: 3.5rem;
  margin-bottom: var(--space-5);
  border: 1px solid rgba(67, 139, 255, .22);
  border-radius: 1.1rem;
  background: var(--color-primary-soft);
  color: #83b4ff;
  place-items: center;
}

.verify-symbol > span {
  position: absolute;
  inset: auto auto -.25rem -.25rem;
  display: grid;
  width: 1.35rem;
  height: 1.35rem;
  border: 2px solid var(--color-surface-1);
  border-radius: 50%;
  background: var(--color-success);
  color: #061b14;
  place-items: center;
}

.verify-intro { margin-bottom: var(--space-6); }
.mobile-number { display: inline-block; color: var(--color-text-secondary); font-variant-numeric: tabular-nums; }
.edit-number { display: inline-block; margin-inline-start: var(--space-1); font-size: var(--font-size-xs); }

.resend-success {
  display: flex;
  align-items: center;
  gap: var(--space-2);
  margin: calc(var(--space-2) * -1) 0 0;
  color: var(--color-success);
  font-size: var(--font-size-xs);
}
.demo-hint { display: flex; align-items: center; justify-content: center; gap: var(--space-2); margin: calc(var(--space-1) * -1) 0 0; padding: var(--space-2); border-radius: var(--radius-sm); background: var(--color-info-soft); color: var(--color-info); font-size: var(--font-size-xs); }

.back-link { display: inline-flex; align-items: center; gap: var(--space-1); }
</style>
