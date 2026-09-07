<script setup lang="ts">
import { computed, reactive, ref } from 'vue'
import { RouterLink, useRoute, useRouter } from 'vue-router'
import { useAuthStore } from '@/stores/auth'
import AppButton from '@/components/ui/AppButton.vue'
import AppCard from '@/components/ui/AppCard.vue'
import AppIcon from '@/components/ui/AppIcon.vue'
import AppInput from '@/components/ui/AppInput.vue'
import { isValidMobile, normalizeMobile, safeAppRedirect } from './auth.utils'

const route = useRoute()
const router = useRouter()
const auth = useAuthStore()
const rawMobile = ref('')
const password = ref('')
const remember = ref(true)
const loading = ref(false)
const submitted = ref(false)
const formError = ref('')
const touched = reactive({ mobile: false, password: false })

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
  if (!password.value) return 'رمز عبور را وارد کنید.'
  return password.value.length >= 8 ? '' : 'رمز عبور باید حداقل ۸ نویسه باشد.'
})

const resetWasSuccessful = computed(() => route.query.reset === '1')
const sessionExpired = computed(() => route.query.expired === '1')

async function submitLogin() {
  submitted.value = true
  formError.value = ''
  if (mobileError.value || passwordError.value) return

  loading.value = true
  try {
    await auth.login({ mobile: mobile.value, password: password.value, remember: remember.value })
    await router.push(safeAppRedirect(route.query.redirect))
  } catch (error) {
    formError.value = error instanceof Error ? error.message : 'ورود انجام نشد. اتصال اینترنت خود را بررسی و دوباره تلاش کنید.'
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
      <p class="auth-description">برای ورود به پنل، شماره موبایل و رمز عبور خود را وارد کنید.</p>
    </div>

    <div v-if="resetWasSuccessful" class="auth-alert auth-alert--success" role="status">
      <AppIcon name="check" :size="18" />
      <span>رمز عبور شما با موفقیت تغییر کرد. اکنون وارد حساب شوید.</span>
    </div>
    <div v-else-if="sessionExpired" class="auth-alert" role="status">
      <AppIcon name="lock" :size="18" />
      <span>نشست شما منقضی شده است. برای ادامه دوباره وارد شوید.</span>
    </div>

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
          <input v-model="remember" type="checkbox">
          <span class="remember-control__box"><AppIcon name="check" :size="15" /></span>
          <span>مرا به خاطر بسپار</span>
        </label>
        <RouterLink class="auth-link" to="/auth/forgot-password">رمز عبور را فراموش کرده‌ام</RouterLink>
      </div>

      <div v-if="formError" class="auth-alert" role="alert">
        <AppIcon name="warning" :size="18" />
        <span>{{ formError }}</span>
      </div>

      <AppButton type="submit" size="lg" block :loading="loading">
        ورود به حساب
      </AppButton>
    </form>

    <p class="auth-footer">
      هنوز حساب ندارید؟
      <RouterLink class="auth-link" to="/auth/register">ساخت حساب جدید</RouterLink>
    </p>
  </AppCard>
</template>

<style scoped>
.auth-alert { margin-bottom: var(--space-5); }

.remember-control {
  position: relative;
  display: inline-flex;
  min-height: 2.75rem;
  align-items: center;
  gap: var(--space-2);
  cursor: pointer;
  user-select: none;
}

.remember-control input {
  position: absolute;
  width: 1px;
  height: 1px;
  overflow: hidden;
  opacity: 0;
}

.remember-control__box {
  display: grid;
  width: 1.25rem;
  height: 1.25rem;
  border: 1px solid var(--color-border-hover);
  border-radius: .38rem;
  background: var(--color-surface-2);
  color: transparent;
  place-items: center;
  transition: border-color var(--transition-fast), background var(--transition-fast), color var(--transition-fast), box-shadow var(--transition-fast);
}

.remember-control input:checked + .remember-control__box {
  border-color: var(--color-primary);
  background: var(--color-primary);
  color: white;
}

.remember-control input:focus-visible + .remember-control__box { box-shadow: var(--shadow-focus); }

@media (max-width: 420px) {
  .auth-form__meta { align-items: flex-start; flex-direction: column; }
}
</style>
