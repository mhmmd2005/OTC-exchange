<script setup>
import { computed, ref } from 'vue'
import { useRouter } from 'vue-router'
import { ArrowLeft, CheckCircle2, Eye, EyeOff, ShieldCheck } from 'lucide-vue-next'

const router = useRouter()
const form = ref({ username: '', email: '', password: '', confirmPassword: '', agree: false })
const step = ref('form')
const showPassword = ref(false)
const showConfirm = ref(false)

function goLogin() { router.push('/login') }
function validate() {
  if (!form.value.username || !form.value.email || !form.value.password || !form.value.confirmPassword) return false
  return form.value.password === form.value.confirmPassword && form.value.agree
}

function submit() {
  if (!validate()) return
  step.value = 'success'
}

const strength = computed(() => {
  const length = form.value.password.length
  if (length >= 10) return 'قوی'
  if (length >= 7) return 'متوسط'
  return 'ضعیف'
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
        <div class="visual-badge">Premium OTC</div>
        <h1>ثبت‌نام در صرافی</h1>
        <p>برای ورود به بازار رمزارز و معاملات OTC حرفه‌ای، حساب خود را ایجاد کنید.</p>
        <ul class="bullet-list">
          <li><ShieldCheck :size="16" /> مسدودسازی پیشرفته</li>
          <li><ShieldCheck :size="16" /> احراز هویت سطح ۲</li>
          <li><ShieldCheck :size="16" /> تسویه سریع و امن</li>
        </ul>
      </div>

      <div class="auth-form-panel">
        <button class="text-action" type="button" @click="router.push('/')">
          <ArrowLeft :size="16" /> بازگشت
        </button>

        <div v-if="step === 'form'">
          <div class="auth-header">
            <h2>ایجاد حساب</h2>
            <p>حساب خود را با اطلاعات پایه بسازید.</p>
          </div>

          <form class="auth-form" @submit.prevent="submit">
            <div class="field">
              <label>نام کاربری</label>
              <input v-model="form.username" class="input" type="text" placeholder="مثلاً mahdi_otc" />
            </div>
            <div class="field">
              <label>ایمیل</label>
              <input v-model="form.email" class="input" type="email" placeholder="you@example.com" />
            </div>
            <div class="field">
              <label>رمز عبور</label>
              <div class="password-wrap">
                <input v-model="form.password" :type="showPassword ? 'text' : 'password'" class="input" placeholder="حداقل 8 کاراکتر" />
                <button type="button" class="password-toggle" @click="showPassword = !showPassword">
                  <Eye v-if="!showPassword" :size="16" />
                  <EyeOff v-else :size="16" />
                </button>
              </div>
              <div class="strength-row"><span>سطح امنیتی</span><strong>{{ strength }}</strong></div>
            </div>
            <div class="field">
              <label>تکرار رمز عبور</label>
              <div class="password-wrap">
                <input v-model="form.confirmPassword" :type="showConfirm ? 'text' : 'password'" class="input" placeholder="تکرار رمز عبور" />
                <button type="button" class="password-toggle" @click="showConfirm = !showConfirm">
                  <Eye v-if="!showConfirm" :size="16" />
                  <EyeOff v-else :size="16" />
                </button>
              </div>
            </div>
            <label class="checkbox-row">
              <input v-model="form.agree" type="checkbox" />
              <span>شرایط و قوانین را مطالعه کرده‌ام و می‌پذیرم.</span>
            </label>
            <button class="primary-btn large" type="submit">ایجاد حساب</button>
            <div class="auth-switch">
              <span>قبلاً حساب دارید؟</span>
              <button type="button" class="text-link" @click="goLogin">ورود</button>
            </div>
          </form>
        </div>

        <div v-else class="success-box">
          <CheckCircle2 :size="40" />
          <h3>ثبت‌نام با موفقیت انجام شد</h3>
          <p>لینک فعال‌سازی به ایمیل شما ارسال شد. لطفاً ایمیل خود را بررسی کنید.</p>
          <button class="primary-btn large" type="button" @click="goLogin">ورود به حساب</button>
        </div>
      </div>
    </div>
  </div>
</template>
