<script setup>
import { computed, onMounted, ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useAuthStore } from '../stores/auth'
import { useNotificationStore } from '../stores/notification'
import { ArrowLeft, Eye, EyeOff, ShieldCheck } from 'lucide-vue-next'
import OtpInput from '../components/OtpInput.vue'
import { isValidIranianMobile, normalizePhone } from '../utils/phone'

const router = useRouter()
const route = useRoute()
const auth = useAuthStore()
const notification = useNotificationStore()

const phone = ref(auth.phone || '')
const otp = ref('')
const password = ref('')
const showPassword = ref(false)
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
    if (resendSeconds.value <= 0) {
      clearResendTimer()
    }
  }, 1000)
}

async function handlePhoneSubmit() {
  const normalized = normalizePhone(phone.value)
  if (!isValidIranianMobile(normalized)) {
    notification.addToast({ title: 'خطا', text: 'شماره موبایل معتبر نیست.', type: 'error' })
    return
  }

  phone.value = normalized
  auth.phone = normalized
  const result = await auth.requestLoginOtp(normalized)

  if (!result.ok) {
    notification.addToast({ title: 'خطا', text: result.message || 'درخواست کد ناموفق بود.', type: 'error' })
    return
  }

  if (result.needsRegistration) {
    notification.addToast({
      title: 'حسابی پیدا نشد',
      text: 'برای همین شماره، فرم ثبت‌نام را ادامه می‌دهیم.',
      type: 'info',
    })
    await router.push({ path: '/register', query: { phone: normalized } })
    return
  }

  startResendTimer()
}

async function handleOtpSubmit() {
  if (!otp.value || otp.value.length !== 6) {
    notification.addToast({ title: 'خطا', text: 'کد تأیید باید ۶ رقمی باشد.', type: 'error' })
    return
  }

  const result = await auth.verifyOtp(otp.value)
  if (!result.ok) {
    notification.addToast({ title: 'خطا', text: result.message || 'کد تایید صحیح نیست.', type: 'error' })
    return
  }

  otp.value = ''
}

async function handlePasswordSubmit() {
  if (!password.value) {
    notification.addToast({ title: 'خطا', text: 'رمز عبور را وارد کنید.', type: 'error' })
    return
  }

  const result = await auth.verifyLoginPassword(password.value)
  if (!result.ok) {
    notification.addToast({ title: 'خطا', text: result.message || 'رمز عبور صحیح نیست.', type: 'error' })
    return
  }

  notification.addToast({ title: 'ورود موفق', text: 'به داشبورد خوش آمدید.', type: 'success' })
  await router.push('/dashboard')
}

async function resendOtp() {
  if (resendSeconds.value > 0 || !phone.value) return

  const result = await auth.requestLoginOtp(phone.value)
  if (!result.ok) {
    notification.addToast({ title: 'خطا', text: result.message || 'ارسال مجدد کد ناموفق بود.', type: 'error' })
    return
  }

  startResendTimer()
}

function goBack() {
  if (step.value === 'password') {
    password.value = ''
    auth.authStep = 'otp'
    return
  }

  if (step.value === 'otp') {
    otp.value = ''
    auth.resetAuthFlow({ keepPhone: false })
    phone.value = ''
    return
  }

  router.push('/')
}

onMounted(() => {
  if (route.query.phone) {
    const normalized = normalizePhone(route.query.phone)
    phone.value = normalized
    auth.phone = normalized
    auth.authMode = 'login'
    auth.authStep = 'otp'
    auth.requestLoginOtp(normalized)
  }
})
</script>

<template>
  <div class="auth-shell">
    <div class="auth-card premium-auth">
      <div class="auth-visual-panel">
        <div class="auth-brand">
          <div class="brand-mark"><span>OT</span></div>
          <div class="brand-copy small"><span class="brand-name">OTC</span><small>Desk</small></div>
        </div>

        <div class="visual-badge">Institutional Access</div>
        <h1>به بازار خصوصی خود وارد شوید.</h1>
        <p>برای کنترل دارایی، بررسی سفارش‌ها و اجرای معاملات بزرگ، وارد حساب خود شوید.</p>

        <ul class="bullet-list">
          <li><ShieldCheck :size="16" /> معاملات امن و مستقیم</li>
          <li><ShieldCheck :size="16" /> پشتیبانی اختصاصی ۲۴/۷</li>
          <li><ShieldCheck :size="16" /> تسویه و ریسک تحت کنترل</li>
        </ul>

        <div class="mini-quote">
          <span>بازار فعال</span>
          <strong>BTC / USDT</strong>
          <small>$68,420 • +2.8%</small>
        </div>
      </div>

      <div class="auth-form-panel">
        <button class="text-action" type="button" @click="goBack">
          <ArrowLeft :size="16" /> {{ step === 'phone' ? 'بازگشت' : 'بازگشت' }}
        </button>

        <div class="auth-step-indicator" aria-label="مراحل ورود">
          <span :class="['step-pill', { active: stepIndex === 0, done: stepIndex > 0 }]">01</span>
          <span :class="['step-pill', { active: stepIndex === 1, done: stepIndex > 1 }]">02</span>
          <span :class="['step-pill', { active: stepIndex === 2, done: stepIndex > 2 }]">03</span>
        </div>

        <div class="auth-header">
          <h2 v-if="step === 'phone'">ورود به حساب</h2>
          <h2 v-else-if="step === 'otp'">تأیید شماره موبایل</h2>
          <h2 v-else>ورود به حساب</h2>

          <p v-if="step === 'phone'">شماره موبایل خود را وارد کنید.</p>
          <p v-else-if="step === 'otp'">کد ۶ رقمی به شماره زیر ارسال شد.</p>
          <p v-else>رمز عبور خود را وارد کنید.</p>
        </div>

        <form v-if="step === 'phone'" class="auth-form" @submit.prevent="handlePhoneSubmit">
          <div class="field">
            <label>شماره موبایل</label>
            <input v-model="phone" type="tel" class="input" inputmode="numeric" placeholder="09123456789" />
          </div>

          <button class="primary-btn large" type="submit" :disabled="auth.loading">
            {{ auth.loading ? 'در حال ارسال...' : 'ادامه' }}
          </button>

          <div class="auth-switch">
            <span>حساب ندارید؟</span>
            <button type="button" class="text-link" @click="router.push('/register')">ثبت نام</button>
          </div>
        </form>

        <form v-else-if="step === 'otp'" class="auth-form" @submit.prevent="handleOtpSubmit">
          <div class="otp-summary" aria-live="polite">
            <span>شماره:</span>
            <strong>{{ maskedPhone }}</strong>
          </div>

          <OtpInput v-model="otp" :length="6" :disabled="auth.loading" />

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
              <input v-model="password" :type="showPassword ? 'text' : 'password'" class="input" placeholder="رمز عبور" />
              <button type="button" class="password-toggle" @click="showPassword = !showPassword" aria-label="نمایش یا مخفی کردن رمز عبور">
                <Eye v-if="!showPassword" :size="16" />
                <EyeOff v-else :size="16" />
              </button>
            </div>
          </div>

          <div class="auth-row-between">
            <button type="button" class="text-link" @click="auth.authStep = 'otp'">بازگشت</button>
            <button type="button" class="text-link" @click="router.push('/forgot-password')">فراموشی رمز عبور</button>
          </div>

          <button class="primary-btn large" type="submit" :disabled="auth.loading || !password">
            {{ auth.loading ? 'در حال ورود...' : 'ورود به حساب' }}
          </button>
        </form>
      </div>
    </div>
  </div>
</template>
