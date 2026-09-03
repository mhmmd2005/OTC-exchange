<script setup>
import {computed, onMounted, ref} from 'vue'
import {useRoute, useRouter} from 'vue-router'
import {useAuthStore} from '../stores/auth'
import {useNotificationStore} from '../stores/notification'
import {ArrowLeft, Eye, EyeOff, ShieldCheck} from 'lucide-vue-next'
import OtpInput from '../components/OtpInput.vue'
import {getPasswordRequirements, validatePassword} from '../utils/passwordValidation'
import {isValidIranianMobile, normalizePhone} from '../utils/phone'

const router = useRouter()
const route = useRoute()
const auth = useAuthStore()
const notification = useNotificationStore()

const phone = ref(auth.phone || '')
const otp = ref('')
const password = ref('')
const confirmPassword = ref('')
const showPassword = ref(false)
const showConfirmPassword = ref(false)
const resendSeconds = ref(0)
let resendTimer = null

const step = computed(() => auth.authStep || 'phone')
const stepIndex = computed(() => {
  if (step.value === 'phone') return 0
  if (step.value === 'otp') return 1
  return 2
})

const maskedPhone = computed(() => {
  const raw = phone.value.replace(/\D/g, '')
  if (raw.length <= 4) return raw
  if (raw.length <= 11) return `${raw.slice(0, 4)} **** ${raw.slice(-4)}`
  return `${raw.slice(0, 6)} **** ${raw.slice(-4)}`
})

const passwordRequirements = computed(() => getPasswordRequirements(password.value))

function clearResendTimer() {
  if (resendTimer) {
    clearInterval(resendTimer)
    resendTimer = null
  }
}

function startResendTimer() {
  clearResendTimer()
  resendSeconds.value = 87
  resendTimer = setInterval(() => {
    resendSeconds.value -= 1
    if (resendSeconds.value <= 0) clearResendTimer()
  }, 1000)
}

async function handlePhoneSubmit() {
  const normalized = normalizePhone(phone.value)

  if (!isValidIranianMobile(normalized)) {
    notification.addToast({title: 'خطا', text: 'شماره موبایل معتبر نیست.', type: 'error'})
    return
  }

  phone.value = normalized
  auth.phone = normalized

  const result = await auth.requestRegistrationOtp(normalized)

  if (!result.ok) {
    notification.addToast({title: 'خطا', text: result.message || 'ارسال کد تأیید انجام نشد.', type: 'error'})
    return
  }

  if (result.alreadyRegistered) {
    notification.addToast({
      title: 'حساب از قبل وجود دارد',
      text: result.message || 'این شماره قبلاً ثبت شده است. وارد حساب خود شوید.',
      type: 'warning',
    })
    await router.push('/login')
    return
  }

  startResendTimer()
}

async function handleOtpSubmit() {
  if (otp.value.length !== 6) {
    notification.addToast({title: 'خطا', text: 'کد تأیید باید ۶ رقمی باشد.', type: 'error'})
    return
  }

  const result = await auth.verifyOtp(otp.value)

  if (!result.ok) {
    notification.addToast({title: 'خطا', text: result.message || 'کد تأیید صحیح نیست.', type: 'error'})
    return
  }

  otp.value = ''
}

async function handlePasswordSubmit() {
  if (!validatePassword(password.value)) {
    notification.addToast({title: 'خطا', text: 'رمز عبور شرایط لازم را ندارد.', type: 'error'})
    return
  }

  if (password.value !== confirmPassword.value) {
    notification.addToast({title: 'خطا', text: 'رمزهای عبور یکسان نیستند.', type: 'error'})
    return
  }

  const result = await auth.registerWithPassword(password.value, confirmPassword.value)

  if (!result.ok) {
    notification.addToast({title: 'خطا', text: result.message || 'ایجاد حساب انجام نشد.', type: 'error'})
    return
  }

  notification.addToast({title: 'ثبت‌نام موفق', text: 'حساب شما با موفقیت ایجاد شد.', type: 'success'})
  await router.push('/dashboard')
}

async function resendOtp() {
  if (resendSeconds.value > 0 || !phone.value) return

  const result = await auth.requestRegistrationOtp(phone.value)

  if (!result.ok) {
    notification.addToast({title: 'خطا', text: result.message || 'ارسال مجدد کد انجام نشد.', type: 'error'})
    return
  }

  startResendTimer()
}

function goBack() {
  if (step.value === 'password') {
    password.value = ''
    confirmPassword.value = ''
    auth.authStep = 'otp'
    return
  }

  if (step.value === 'otp') {
    otp.value = ''
    auth.resetAuthFlow({keepPhone: false})
    phone.value = ''
    return
  }

  router.push('/')
}

onMounted(async () => {
  const prefilledPhone = route.query.phone ? String(route.query.phone) : ''

  if (prefilledPhone) {
    const normalized = normalizePhone(prefilledPhone)
    phone.value = normalized
    auth.phone = normalized
    auth.authMode = 'register'
    auth.authStep = 'otp'
    await handlePhoneSubmit()
  }
})
</script>

<template>
  <div class="auth-shell">
    <div class="auth-card register-card">
      <div class="auth-visual-panel">
        <div class="auth-brand">
          <div class="brand-mark"><span>OT</span></div>
          <div class="brand-copy small"><span class="brand-name">OTC</span><small>Exchange</small></div>
        </div>

        <div class="visual-badge">ایجاد حساب</div>
        <h1>حساب خود را ایجاد کنید.</h1>
        <p>برای استفاده از خدمات صرافی، حساب خود را ایجاد کنید.</p>

        <ul class="bullet-list">
          <li>
            <ShieldCheck :size="16"/>
            امنیت حساب
          </li>
          <li>
            <ShieldCheck :size="16"/>
            مدیریت دارایی
          </li>
          <li>
            <ShieldCheck :size="16"/>
            خرید و فروش آسان
          </li>
        </ul>
      </div>

      <div class="auth-form-panel">
        <button class="text-action" type="button" @click="goBack">
          <ArrowLeft :size="16"/>
          بازگشت
        </button>

        <div class="auth-step-indicator" aria-label="مراحل ثبت‌نام">
          <span :class="['step-pill', { active: stepIndex === 0, done: stepIndex > 0 }]">01</span>
          <span :class="['step-pill', { active: stepIndex === 1, done: stepIndex > 1 }]">02</span>
          <span :class="['step-pill', { active: stepIndex === 2, done: stepIndex > 2 }]">03</span>
        </div>

        <div class="auth-header">
          <h2 v-if="step === 'phone'">ایجاد حساب</h2>
          <h2 v-else-if="step === 'otp'">تأیید شماره موبایل</h2>
          <h2 v-else>تنظیم رمز عبور</h2>

          <p v-if="step === 'phone'">شماره موبایل خود را وارد کنید.</p>
          <p v-else-if="step === 'otp'">کد تأیید ارسال‌شده را وارد کنید.</p>
          <p v-else>رمز عبور خود را انتخاب کنید.</p>
        </div>

        <form v-if="step === 'phone'" class="auth-form" @submit.prevent="handlePhoneSubmit">
          <div class="field">
            <label>شماره موبایل</label>
            <input v-model="phone" type="tel" class="input" inputmode="numeric" placeholder="09123456789"/>
          </div>

          <button class="primary-btn large" type="submit" :disabled="auth.loading">
            {{ auth.loading ? 'در حال ارسال کد...' : 'ادامه' }}
          </button>

          <div class="auth-switch">
            <span>قبلاً حساب دارید؟</span>
            <button type="button" class="text-link" @click="router.push('/login')">ورود به حساب</button>
          </div>
        </form>

        <form v-else-if="step === 'otp'" class="auth-form" @submit.prevent="handleOtpSubmit">
          <div class="otp-summary" aria-live="polite">
            <span>شماره موبایل:</span>
            <strong>{{ maskedPhone }}</strong>
          </div>

          <OtpInput v-model="otp" :length="6" :disabled="auth.loading"/>

          <div class="otp-actions">
            <button type="button" class="text-link" :disabled="resendSeconds > 0" @click="resendOtp">
              {{ resendSeconds > 0 ? `ارسال مجدد در ${resendSeconds} ثانیه` : 'ارسال مجدد کد' }}
            </button>
            <button type="button" class="text-link" @click="goBack">تغییر شماره</button>
          </div>

          <button class="primary-btn large" type="submit" :disabled="auth.loading || otp.length !== 6">
            {{ auth.loading ? 'در حال تأیید...' : 'تأیید کد' }}
          </button>
        </form>

        <form v-else class="auth-form" @submit.prevent="handlePasswordSubmit">
          <div class="field">
            <label>رمز عبور</label>
            <div class="password-wrap">
              <input v-model="password" :type="showPassword ? 'text' : 'password'" class="input"
                     placeholder="رمز عبور"/>
              <button type="button" class="password-toggle" @click="showPassword = !showPassword"
                      aria-label="نمایش یا مخفی کردن رمز عبور">
                <Eye v-if="!showPassword" :size="16"/>
                <EyeOff v-else :size="16"/>
              </button>
            </div>
          </div>

          <div class="field">
            <label>تکرار رمز عبور</label>
            <div class="password-wrap">
              <input v-model="confirmPassword" :type="showConfirmPassword ? 'text' : 'password'" class="input"
                     placeholder="تکرار رمز عبور"/>
              <button type="button" class="password-toggle" @click="showConfirmPassword = !showConfirmPassword"
                      aria-label="نمایش یا مخفی کردن تکرار رمز عبور">
                <Eye v-if="!showConfirmPassword" :size="16"/>
                <EyeOff v-else :size="16"/>
              </button>
            </div>
          </div>

          <div class="password-requirements" aria-live="polite">
            <div v-for="item in passwordRequirements" :key="item.key"
                 :class="['password-check', { valid: item.valid }]">
              <span>{{ item.valid ? '✓' : '•' }}</span>
              <small>{{ item.label }}</small>
            </div>
          </div>

          <button class="primary-btn large" type="submit" :disabled="auth.loading || !password || !confirmPassword">
            {{ auth.loading ? 'در حال ایجاد حساب...' : 'ایجاد حساب' }}
          </button>
        </form>
      </div>
    </div>
  </div>
</template>