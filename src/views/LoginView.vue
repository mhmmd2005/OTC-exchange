<script setup>
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import { useAuthStore } from '../stores/auth'
import { useNotificationStore } from '../stores/notification'
import { ArrowLeft, Eye, EyeOff, ShieldCheck } from 'lucide-vue-next'

const router = useRouter()
const auth = useAuthStore()
const notification = useNotificationStore()
const username = ref('demo')
const password = ref('123456')
const showPassword = ref(false)

async function handleLogin() {
  const ok = await auth.login({ username: username.value, password: password.value })
  if (ok) {
    notification.addToast({ title: 'ورود موفق', text: 'به داشبورد خوش آمدید.', type: 'success' })
    router.push('/dashboard')
  } else {
    notification.addToast({ title: 'خطا', text: auth.error || 'ورود ناموفق بود.', type: 'error' })
  }
}
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
        <button class="text-action" type="button" @click="router.push('/')">
          <ArrowLeft :size="16" /> بازگشت
        </button>

        <div class="auth-header">
          <h2>ورود به حساب</h2>
          <p>برای نمونه: demo / 123456</p>
        </div>

        <form class="auth-form" @submit.prevent="handleLogin">
          <div class="field">
            <label>نام کاربری</label>
            <input v-model="username" type="text" class="input" placeholder="نام کاربری" />
          </div>

          <div class="field">
            <label>رمز عبور</label>
            <div class="password-wrap">
              <input v-model="password" :type="showPassword ? 'text' : 'password'" class="input" placeholder="رمز عبور" />
              <button type="button" class="password-toggle" @click="showPassword = !showPassword">
                <Eye v-if="!showPassword" :size="16" />
                <EyeOff v-else :size="16" />
              </button>
            </div>
          </div>

          <div class="auth-row-between">
            <label class="checkbox-row compact">
              <input type="checkbox" />
              <span>مرا به خاطر بسپار</span>
            </label>
            <button type="button" class="text-link" @click="router.push('/forgot-password')">فراموشی رمز عبور</button>
          </div>

          <button class="primary-btn large" type="submit" :disabled="auth.loading">
            {{ auth.loading ? 'در حال ورود...' : 'ورود به حساب' }}
          </button>

          <div class="auth-switch">
            <span>حساب ندارید؟</span>
            <button type="button" class="text-link" @click="router.push('/register')">ثبت نام</button>
          </div>
        </form>
      </div>
    </div>
  </div>
</template>
