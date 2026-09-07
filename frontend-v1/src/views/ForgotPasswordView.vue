<script setup>
import {ref} from 'vue'
import {useRouter} from 'vue-router'
import {ArrowLeft} from 'lucide-vue-next'
import {useAuthStore} from '../stores/auth'

const router = useRouter()
const auth = useAuthStore()
const phone = ref('')
const otp = ref('')
const step = ref('phone')
const error = ref('')

async function requestOtp() {
  error.value = ''

  const result = await auth.requestPasswordResetOtp(phone.value)

  if (!result?.ok) {
    error.value = auth.error || result?.message || 'ارسال کد انجام نشد.'
    return
  }

  step.value = 'otp'
}

async function verifyOtp() {
  error.value = ''

  if (otp.value.length !== 6) {
    error.value = 'کد تأیید باید ۶ رقمی باشد.'
    return
  }

  const result = await auth.verifyOtp(otp.value)

  if (!result?.ok) {
    error.value = auth.error || result?.message || 'کد تأیید صحیح نیست.'
    return
  }

  await router.push('/reset-password')
}
</script>

<template>
  <div class="auth-shell compact-shell">
    <div class="auth-card compact-card">
      <div class="auth-form-panel full-panel">
        <button class="text-action" type="button" @click="router.push('/login')">
          <ArrowLeft :size="16"/>
          بازگشت
        </button>

        <div v-if="step === 'phone'" class="auth-header">
          <h2>بازیابی رمز عبور</h2>
          <p>شماره موبایل خود را وارد کنید.</p>
        </div>

        <form v-if="step === 'phone'" class="auth-form" @submit.prevent="requestOtp">
          <div class="field">
            <label>شماره موبایل</label>
            <input v-model="phone" class="input" type="tel" dir="ltr" inputmode="numeric" placeholder="09123456780"/>
          </div>

          <p v-if="error" class="form-error">{{ error }}</p>

          <button class="primary-btn large" type="submit" :disabled="auth.loading">
            {{ auth.loading ? 'در حال ارسال...' : 'ارسال کد تأیید' }}
          </button>
        </form>

        <div v-else-if="step === 'otp'">
          <div class="auth-header">
            <h2>تأیید شماره</h2>
            <p>کد ارسال‌شده به {{ auth.phone }} را وارد کنید.</p>
          </div>

          <form class="auth-form" @submit.prevent="verifyOtp">
            <div class="field">
              <label>کد تأیید</label>
              <input v-model="otp" class="input" type="text" inputmode="numeric" maxlength="6" dir="ltr"
                     placeholder="123456"/>
            </div>

            <p v-if="error" class="form-error">{{ error }}</p>

            <button class="primary-btn large" type="submit" :disabled="auth.loading || otp.length !== 6">
              {{ auth.loading ? 'در حال بررسی...' : 'تأیید کد' }}
            </button>
          </form>
        </div>
      </div>
    </div>
  </div>
</template>