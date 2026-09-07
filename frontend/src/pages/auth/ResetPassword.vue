<script setup lang="ts">
import { computed, onMounted, reactive, ref } from 'vue'
import { useRouter } from 'vue-router'
import { useAuthStore } from '@/stores/auth'
import AppButton from '@/components/ui/AppButton.vue'
import AppCard from '@/components/ui/AppCard.vue'
import AppIcon from '@/components/ui/AppIcon.vue'
import AppInput from '@/components/ui/AppInput.vue'
import { maskMobile, passwordValidation } from './auth.utils'

const router = useRouter()
const auth = useAuthStore()
const password = ref('')
const passwordConfirmation = ref('')
const loading = ref(false)
const submitted = ref(false)
const formError = ref('')
const touched = reactive({ password: false, confirmation: false })

const mobile = computed(() => auth.passwordResetProof?.mobile || '')
const maskedMobile = computed(() => maskMobile(mobile.value))

const passwordError = computed(() => {
  if (!submitted.value && !touched.password) return ''
  return passwordValidation(password.value)
})

const confirmationError = computed(() => {
  if (!submitted.value && !touched.confirmation) return ''
  if (!passwordConfirmation.value) return 'تکرار رمز عبور را وارد کنید.'
  return passwordConfirmation.value === password.value ? '' : 'تکرار رمز عبور یکسان نیست.'
})

const passwordChecks = computed(() => [
  { label: 'حداقل ۸ نویسه', passed: password.value.length >= 8 },
])

async function resetPassword() {
  submitted.value = true
  formError.value = ''
  if (passwordError.value || confirmationError.value) return

  loading.value = true
  try {
    await auth.resetPassword({ password: password.value, passwordConfirmation: passwordConfirmation.value })
    await router.replace('/auth/reset-success')
  } catch (error) {
    formError.value = error instanceof Error ? error.message : 'تغییر رمز عبور انجام نشد. لطفاً دوباره تلاش کنید.'
    if (!auth.passwordResetProof) {
      await router.replace({ name: 'forgot-password', query: { proof: 'expired' } })
    }
  } finally {
    loading.value = false
  }
}

onMounted(() => {
  if (!auth.passwordResetProof) void router.replace('/auth/forgot-password')
})
</script>

<template>
  <AppCard padding="lg" class="auth-view">
    <div class="auth-intro">
      <span class="auth-kicker">آخرین مرحله بازیابی</span>
      <h1 class="auth-title">یک رمز عبور جدید بسازید</h1>
      <p class="auth-description">
        رمز جدید برای حساب <strong dir="ltr">{{ maskedMobile }}</strong> ثبت می‌شود.
      </p>
    </div>

    <ol class="reset-steps" aria-label="مراحل بازیابی رمز عبور">
      <li class="done"><span><AppIcon name="check" :size="15" /></span><small>شماره موبایل</small></li>
      <li class="done"><span><AppIcon name="check" :size="15" /></span><small>تأیید کد</small></li>
      <li class="active"><span>۳</span><small>رمز جدید</small></li>
    </ol>

    <form class="auth-form" novalidate @submit.prevent="resetPassword">
      <AppInput
        v-model="password"
        label="رمز عبور جدید"
        placeholder="رمز جدید را وارد کنید"
        type="password"
        autocomplete="new-password"
        name="password"
        icon="lock"
        ltr
        :error="passwordError"
        @blur="touched.password = true"
      />

      <ul class="password-checks" aria-label="شرایط رمز عبور">
        <li v-for="item in passwordChecks" :key="item.label" :class="{ passed: item.passed }">
          <span><AppIcon :name="item.passed ? 'check' : 'minus'" :size="13" /></span>
          {{ item.label }}
        </li>
      </ul>

      <AppInput
        v-model="passwordConfirmation"
        label="تکرار رمز عبور جدید"
        placeholder="رمز جدید را دوباره وارد کنید"
        type="password"
        autocomplete="new-password"
        name="password_confirmation"
        icon="lock"
        ltr
        :error="confirmationError"
        @blur="touched.confirmation = true"
      />

      <div v-if="formError" class="auth-alert" role="alert">
        <AppIcon name="warning" :size="18" />
        <span>{{ formError }}</span>
      </div>

      <AppButton type="submit" size="lg" block :loading="loading">
        ذخیره رمز عبور جدید
      </AppButton>

      <div class="auth-security-note">
        <AppIcon name="shield" :size="18" />
        <span>پس از تغییر رمز، برای امنیت بیشتر نشست‌های قبلی حساب بسته می‌شوند.</span>
      </div>
    </form>
  </AppCard>
</template>

<style scoped>
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
  background: linear-gradient(to left, var(--color-success) 0 76%, var(--color-border) 76%);
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
.reset-steps .done { color: var(--color-success); }
.reset-steps .done span { border-color: rgba(53, 201, 149, .38); background: var(--color-success-soft); }
.reset-steps .active { color: var(--color-primary); }
.reset-steps .active span { border-color: var(--color-primary); background: var(--color-primary-soft); }

.password-checks {
  display: flex;
  flex-wrap: wrap;
  gap: var(--space-2) var(--space-3);
  margin: calc(var(--space-3) * -1) 0 0;
  padding: 0;
  list-style: none;
}

.password-checks li {
  display: inline-flex;
  align-items: center;
  gap: var(--space-1);
  color: var(--color-text-muted);
  font-size: .68rem;
  transition: color var(--transition-fast);
}

.password-checks li span {
  display: grid;
  width: 1rem;
  height: 1rem;
  border-radius: 50%;
  background: var(--color-surface-3);
  place-items: center;
}

.password-checks li.passed { color: var(--color-success); }
.password-checks li.passed span { background: var(--color-success-soft); }
</style>
