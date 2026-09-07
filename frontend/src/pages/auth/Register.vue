<script setup lang="ts">
import { computed, reactive, ref } from 'vue'
import { RouterLink, useRouter } from 'vue-router'
import { useAuthStore } from '@/stores/auth'
import AppButton from '@/components/ui/AppButton.vue'
import AppCard from '@/components/ui/AppCard.vue'
import AppIcon from '@/components/ui/AppIcon.vue'
import AppInput from '@/components/ui/AppInput.vue'
import { LEGAL_DOCUMENTS } from '@/constants/legal'
import { isValidMobile, normalizeDigits, normalizeMobile, passwordValidation } from './auth.utils'

const router = useRouter()
const auth = useAuthStore()
const rawMobile = ref('')
const password = ref('')
const passwordConfirmation = ref('')
const referralCode = ref('')
const acceptedTerms = ref(false)
const loading = ref(false)
const submitted = ref(false)
const formError = ref('')
const touched = reactive({ mobile: false, password: false, confirmation: false, terms: false })

const mobile = computed({
  get: () => rawMobile.value,
  set: (value: string) => { rawMobile.value = normalizeMobile(value) },
})

const mobileError = computed(() => {
  if (!submitted.value && !touched.mobile) return ''
  if (!mobile.value) return 'شماره موبایل را وارد کنید.'
  return isValidMobile(mobile.value) ? '' : 'شماره موبایل معتبر نیست؛ مانند ۰۹۱۲۱۲۳۴۵۶۷ وارد کنید.'
})

const passwordError = computed(() => {
  if (!submitted.value && !touched.password) return ''
  return passwordValidation(password.value)
})

const confirmationError = computed(() => {
  if (!submitted.value && !touched.confirmation) return ''
  if (!passwordConfirmation.value) return 'تکرار رمز عبور را وارد کنید.'
  return passwordConfirmation.value === password.value ? '' : 'تکرار رمز عبور یکسان نیست.'
})

const termsError = computed(() => {
  if (!submitted.value && !touched.terms) return ''
  return acceptedTerms.value ? '' : 'برای ساخت حساب، پذیرش قوانین الزامی است.'
})

const passwordScore = computed(() => {
  let score = 0
  if (password.value.length >= 8) score += 1
  if (/[a-z]/i.test(password.value) && /\d/.test(normalizeDigits(password.value))) score += 1
  if (/[^a-z\d]/i.test(password.value)) score += 1
  if (password.value.length >= 12) score += 1
  return score
})

const passwordStrengthLabel = computed(() => {
  return ['بسیار ضعیف', 'ضعیف', 'متوسط', 'خوب', 'قوی'][passwordScore.value]
})

async function submitRegister() {
  submitted.value = true
  touched.terms = true
  formError.value = ''

  if (mobileError.value || passwordError.value || confirmationError.value || termsError.value) return

  loading.value = true
  try {
    await auth.register({
      mobile: mobile.value,
      password: password.value,
      passwordConfirmation: passwordConfirmation.value,
      referralCode: referralCode.value || undefined,
      acceptedTerms: acceptedTerms.value,
      termsVersion: LEGAL_DOCUMENTS.terms.version,
      privacyVersion: LEGAL_DOCUMENTS.privacy.version,
      acceptedAt: new Date().toISOString(),
    })
    await router.push({
      path: '/auth/verify',
      query: { purpose: 'register' },
    })
  } catch (error) {
    formError.value = error instanceof Error ? error.message : 'ساخت حساب انجام نشد. لطفاً چند لحظه دیگر دوباره تلاش کنید.'
  } finally {
    loading.value = false
  }
}
</script>

<template>
  <AppCard padding="lg" class="auth-view register-card">
    <div class="auth-intro">
      <span class="auth-kicker">شروع سریع با روشا</span>
      <h1 class="auth-title">ساخت حساب جدید</h1>
      <p class="auth-description">فعلاً فقط اطلاعات ضروری را می‌گیریم؛ تکمیل حساب بعد از ورود انجام می‌شود.</p>
    </div>

    <form class="auth-form" novalidate @submit.prevent="submitRegister">
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
        @blur="touched.mobile = true"
      />

      <AppInput
        v-model="password"
        label="رمز عبور"
        placeholder="حداقل ۸ نویسه"
        type="password"
        autocomplete="new-password"
        name="password"
        icon="lock"
        ltr
        :error="passwordError"
        @blur="touched.password = true"
      />

      <div v-if="password" class="password-strength">
        <div
          class="password-strength__track"
          role="progressbar"
          aria-label="قدرت رمز عبور"
          :aria-valuenow="passwordScore"
          aria-valuemin="0"
          aria-valuemax="4"
        >
          <span v-for="step in 4" :key="step" :class="{ active: passwordScore >= step }" />
        </div>
        <span>قدرت رمز: <strong>{{ passwordStrengthLabel }}</strong></span>
      </div>

      <AppInput
        v-model="passwordConfirmation"
        label="تکرار رمز عبور"
        placeholder="رمز عبور را دوباره وارد کنید"
        type="password"
        autocomplete="new-password"
        name="password_confirmation"
        icon="lock"
        ltr
        :error="confirmationError"
        @blur="touched.confirmation = true"
      />

      <AppInput
        v-model="referralCode"
        label="کد دعوت (اختیاری)"
        placeholder="اگر کد دعوت دارید وارد کنید"
        autocomplete="off"
        name="referral_code"
        icon="sparkle"
        ltr
        hint="می‌توانید این بخش را خالی بگذارید."
      />

      <div class="terms-field">
        <label class="terms-control">
          <input v-model="acceptedTerms" type="checkbox" @blur="touched.terms = true">
          <span class="terms-control__box"><AppIcon name="check" :size="15" /></span>
          <span>اسناد حقوقی روشا را مطالعه کرده‌ام و نسخه فعلی آن‌ها را می‌پذیرم.</span>
        </label>
        <p class="terms-links">
          <RouterLink to="/legal/terms" target="_blank" rel="noopener">شرایط استفاده</RouterLink>
          <span aria-hidden="true">•</span>
          <RouterLink to="/legal/privacy" target="_blank" rel="noopener">سیاست حریم خصوصی</RouterLink>
        </p>
        <span v-if="termsError" class="terms-field__error" role="alert">{{ termsError }}</span>
      </div>

      <div v-if="formError" class="auth-alert" role="alert">
        <AppIcon name="warning" :size="18" />
        <span>{{ formError }}</span>
      </div>

      <AppButton type="submit" size="lg" block :loading="loading">
        ساخت حساب و دریافت کد
      </AppButton>

      <div class="auth-security-note">
        <AppIcon name="shield" :size="18" />
        <span>برای امنیت حساب، یک کد یک‌بارمصرف به همین شماره ارسال می‌شود.</span>
      </div>
    </form>

    <p class="auth-footer">
      قبلاً ثبت‌نام کرده‌اید؟
      <RouterLink class="auth-link" to="/auth/login">ورود به حساب</RouterLink>
    </p>
  </AppCard>
</template>

<style scoped>
.register-card { margin-block: var(--space-4); }

.password-strength {
  display: flex;
  align-items: center;
  gap: var(--space-3);
  margin-top: calc(var(--space-3) * -1);
  color: var(--color-text-muted);
  font-size: var(--font-size-xs);
}

.password-strength__track { display: grid; flex: 1; grid-template-columns: repeat(4, 1fr); gap: var(--space-1); }

.password-strength__track span {
  height: .22rem;
  border-radius: var(--radius-pill);
  background: var(--color-border);
  transition: background var(--transition-fast);
}

.password-strength__track span.active { background: var(--color-primary); }
.password-strength strong { color: var(--color-text-secondary); font-weight: 600; }

.terms-field { display: grid; gap: var(--space-1); }

.terms-control {
  position: relative;
  display: flex;
  min-height: 2.75rem;
  align-items: flex-start;
  gap: var(--space-3);
  color: var(--color-text-secondary);
  cursor: pointer;
  font-size: var(--font-size-xs);
  line-height: 1.9;
}

.terms-control input {
  position: absolute;
  width: 1px;
  height: 1px;
  overflow: hidden;
  opacity: 0;
}

.terms-control__box {
  display: grid;
  width: 1.25rem;
  height: 1.25rem;
  flex: 0 0 auto;
  margin-top: .25rem;
  border: 1px solid var(--color-border-hover);
  border-radius: .38rem;
  background: var(--color-surface-2);
  color: transparent;
  place-items: center;
  transition: border-color var(--transition-fast), background var(--transition-fast), color var(--transition-fast), box-shadow var(--transition-fast);
}

.terms-control input:checked + .terms-control__box { border-color: var(--color-primary); background: var(--color-primary); color: white; }
.terms-control input:focus-visible + .terms-control__box { box-shadow: var(--shadow-focus); }
.terms-field__error { color: var(--color-danger); font-size: var(--font-size-xs); }
.terms-links { display: flex; align-items: center; gap: var(--space-2); margin: 0 2rem 0 0; color: var(--color-text-muted); font-size: var(--font-size-xs); }
.terms-links a { color: var(--color-primary); font-weight: 600; text-decoration: underline; text-underline-offset: .18rem; }
</style>
