<script setup lang="ts">
import {computed, reactive, ref} from 'vue'
import {RouterLink, useRoute, useRouter} from 'vue-router'
import {useAuthStore} from '@/stores/auth'
import AppButton from '@/components/ui/AppButton.vue'
import AppCard from '@/components/ui/AppCard.vue'
import AppIcon from '@/components/ui/AppIcon.vue'
import AppInput from '@/components/ui/AppInput.vue'
import {isValidMobile, normalizeMobile, safeAppRedirect} from './auth.utils'

const route = useRoute()
const router = useRouter()
const auth = useAuthStore()

const rawMobile = ref('')
const password = ref('')
const remember = ref(true)
const loading = ref(false)
const submitted = ref(false)
const formError = ref('')

const touched = reactive({
  mobile: false,
  password: false,
})

const mobile = computed({
  get: () => rawMobile.value,
  set: (value: string) => {
    rawMobile.value = normalizeMobile(value)
  },
})

const mobileError = computed(() => {
  if (!submitted.value && !touched.mobile) return ''
  if (!mobile.value) return 'شماره موبایل را وارد کنید.'
  return isValidMobile(mobile.value)
      ? ''
      : 'شماره موبایل معتبر نیست؛ مانند ۰۹۱۲۱۲۳۴۵۶۷ وارد کنید.'
})

const passwordError = computed(() => {
  if (!submitted.value && !touched.password) return ''
  if (!password.value) return 'رمز عبور را وارد کنید.'
  return password.value.length >= 8 ? '' : 'رمز عبور باید حداقل ۸ نویسه باشد.'
})

const resetWasSuccessful = computed(() => route.query.reset === '1')
const sessionExpired = computed(() => route.query.expired === '1')

async function submitLogin() {
  if (loading.value) return

  submitted.value = true
  formError.value = ''

  if (mobileError.value || passwordError.value) return

  loading.value = true

  try {
    await auth.login({
      mobile: mobile.value,
      password: password.value,
      remember: remember.value,
    })

    const targetRedirect = safeAppRedirect(route.query.redirect)

    await router.push({
      path: '/auth/verify',
      query: {
        purpose: 'login',
        returnTo: targetRedirect,
      },
    })
  } catch (error: unknown) {
    if (error instanceof Error) {
      formError.value = error.message
    } else if (typeof error === 'object' && error !== null && 'response' in error) {
      const apiError = error as { response?: { data?: { detail?: string; message?: string } } }
      formError.value =
          apiError.response?.data?.detail ||
          apiError.response?.data?.message ||
          'ارسال کد ورود انجام نشد. لطفاً دوباره تلاش کنید.'
    } else {
      formError.value = 'ارسال کد ورود انجام نشد. لطفاً دوباره تلاش کنید.'
    }
  } finally {
    loading.value = false
  }
}
</script>

<template>
  <AppCard padding="lg" class="auth-view">
    <div class="auth-intro">
      <span class="auth-kicker">حساب کاربری روشا</span>
      <h1 class="auth-title">خوش آمدید</h1>
      <p class="auth-description">
        برای ورود به پنل، شماره موبایل و رمز عبور خود را وارد کنید.
      </p>
    </div>

    <!-- هشدارهای وضعیت نشست و بازنشانی -->
    <div
        v-if="resetWasSuccessful"
        class="auth-alert auth-alert--success"
        role="status"
    >
      <AppIcon name="check" :size="18"/>
      <span>رمز عبور شما با موفقیت تغییر کرد. اکنون وارد حساب شوید.</span>
    </div>
    <div v-else-if="sessionExpired" class="auth-alert" role="status">
      <AppIcon name="lock" :size="18"/>
      <span>نشست شما منقضی شده است. برای ادامه دوباره وارد شوید.</span>
    </div>

    <!-- فرم اصلی ورود -->
    <form class="auth-form" novalidate @submit.prevent="submitLogin">
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
          placeholder="رمز عبور خود را وارد کنید"
          type="password"
          autocomplete="current-password"
          name="password"
          icon="lock"
          ltr
          :error="passwordError"
          @blur="touched.password = true"
      />

      <div class="auth-form__meta">
        <label class="remember-control">
          <input
              v-model="remember"
              type="checkbox"
              aria-label="مرا به خاطر بسپار"
          />
          <span class="remember-control__box">
            <AppIcon name="check" :size="14"/>
          </span>
          <span class="remember-control__label">مرا به خاطر بسپار</span>
        </label>
        <RouterLink class="auth-link" to="/auth/forgot-password">
          رمز عبور را فراموش کرده‌ام
        </RouterLink>
      </div>

      <div v-if="formError" class="auth-alert auth-alert--error" role="alert">
        <AppIcon name="warning" :size="18"/>
        <span>{{ formError }}</span>
      </div>

      <AppButton
          type="submit"
          size="lg"
          block
          :loading="loading"
          :disabled="loading"
      >
        ورود به حساب
      </AppButton>
    </form>

    <p class="auth-footer">
      هنوز حساب ندارید؟
      <RouterLink class="auth-link" to="/auth/register">
        ساخت حساب جدید
      </RouterLink>
    </p>
  </AppCard>
</template>

<style scoped>
.auth-view {
  width: 100%;
  max-width: 440px;
  margin: 0 auto;
}

.auth-alert {
  display: flex;
  align-items: center;
  gap: var(--space-3, 0.75rem);
  padding: var(--space-3, 0.75rem) var(--space-4, 1rem);
  border-radius: var(--radius-md, 8px);
  margin-bottom: var(--space-5, 1.25rem);
  font-size: 0.875rem;
  background-color: var(--color-danger-subtle, rgba(239, 68, 68, 0.1));
  color: var(--color-danger, #ef4444);
  border: 1px solid var(--color-danger-border, rgba(239, 68, 68, 0.2));
}

.auth-alert--success {
  background-color: var(--color-success-subtle, rgba(16, 185, 129, 0.1));
  color: var(--color-success, #10b981);
  border-color: var(--color-success-border, rgba(16, 185, 129, 0.2));
}

.auth-form {
  display: flex;
  flex-direction: column;
  gap: var(--space-4, 1rem);
}

.auth-form__meta {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: var(--space-3, 0.75rem);
  margin-top: calc(var(--space-1, 0.25rem) * -1);
}

.remember-control {
  position: relative;
  display: inline-flex;
  min-height: 2.25rem;
  align-items: center;
  gap: var(--space-2, 0.5rem);
  cursor: pointer;
  user-select: none;
  font-size: 0.875rem;
  color: var(--color-text-muted, #6b7280);
  transition: color var(--transition-fast, 0.15s ease);
}

.remember-control:hover {
  color: var(--color-text, #111827);
}

/* Visually Hidden Native Input for A11y */
.remember-control input {
  position: absolute;
  width: 1px;
  height: 1px;
  padding: 0;
  margin: -1px;
  overflow: hidden;
  clip: rect(0, 0, 0, 0);
  white-space: nowrap;
  border: 0;
}

/* Checkbox Visual Box with Soft UI Styling (8px Radius System) */
.remember-control__box {
  display: grid;
  width: 1.25rem;
  height: 1.25rem;
  border: 1.5px solid var(--color-border, #d1d5db);
  border-radius: var(--radius-sm, 6px);
  background: var(--color-surface, #ffffff);
  color: transparent;
  place-items: center;
  transition: border-color var(--transition-fast, 0.15s ease),
  background-color var(--transition-fast, 0.15s ease),
  color var(--transition-fast, 0.15s ease),
  box-shadow var(--transition-fast, 0.15s ease);
}

.remember-control:hover .remember-control__box {
  border-color: var(--color-border-hover, #9ca3af);
}

.remember-control input:checked + .remember-control__box {
  border-color: var(--color-primary, #3b82f6);
  background-color: var(--color-primary, #3b82f6);
  color: #ffffff;
}

.remember-control input:focus-visible + .remember-control__box {
  outline: 2px solid var(--color-primary, #3b82f6);
  outline-offset: 2px;
  box-shadow: var(--shadow-focus, 0 0 0 3px rgba(59, 130, 246, 0.3));
}

.auth-link {
  font-size: 0.875rem;
  font-weight: 5rem;
  color: var(--color-primary, #3b82f6);
  text-decoration: none;
  transition: color var(--transition-fast, 0.15s ease);
}

.auth-link:hover {
  text-decoration: underline;
}

.auth-footer {
  margin-top: var(--space-6, 1.5rem);
  text-align: center;
  font-size: 0.875rem;
  color: var(--color-text-muted, #6b7280);
}

@media (max-width: 420px) {
  .auth-form__meta {
    align-items: flex-start;
    flex-direction: column;
    gap: var(--space-2, 0.5rem);
  }
}
</style>