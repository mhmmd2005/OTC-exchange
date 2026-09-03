<script setup>
import { computed, ref } from 'vue'
import { useRouter } from 'vue-router'
import { ArrowLeft, CheckCircle2, Eye, EyeOff } from 'lucide-vue-next'

const router = useRouter()
const form = ref({ password: '', confirm: '' })
const changed = ref(false)
const show1 = ref(false)
const show2 = ref(false)

const strength = computed(() => {
  const len = form.value.password.length
  if (len >= 10) return 'قوی'
  if (len >= 7) return 'متوسط'
  return 'ضعیف'
})

function submit() {
  if (form.value.password.length < 6 || form.value.password !== form.value.confirm) return
  changed.value = true
}
</script>

<template>
  <div class="auth-shell compact-shell">
    <div class="auth-card compact-card">
      <div class="auth-form-panel full-panel">
        <button class="text-action" type="button" @click="router.push('/login')">
          <ArrowLeft :size="16" /> بازگشت
        </button>

        <div v-if="!changed" class="auth-header">
          <h2>تغییر رمز عبور</h2>
          <p>رمز جدید خود را وارد کنید و آن را تأیید نمایید.</p>
        </div>

        <form v-if="!changed" class="auth-form" @submit.prevent="submit">
          <div class="field">
            <label>رمز جدید</label>
            <div class="password-wrap">
              <input v-model="form.password" :type="show1 ? 'text' : 'password'" class="input" placeholder="رمز جدید" />
              <button type="button" class="password-toggle" @click="show1 = !show1">
                <Eye v-if="!show1" :size="16" />
                <EyeOff v-else :size="16" />
              </button>
            </div>
            <div class="strength-row"><span>سطح امنیتی</span><strong>{{ strength }}</strong></div>
          </div>

          <div class="field">
            <label>تکرار رمز جدید</label>
            <div class="password-wrap">
              <input v-model="form.confirm" :type="show2 ? 'text' : 'password'" class="input" placeholder="تکرار رمز جدید" />
              <button type="button" class="password-toggle" @click="show2 = !show2">
                <Eye v-if="!show2" :size="16" />
                <EyeOff v-else :size="16" />
              </button>
            </div>
          </div>

          <button class="primary-btn large" type="submit">تغییر رمز عبور</button>
        </form>

        <div v-else class="success-box">
          <CheckCircle2 :size="40" />
          <h3>رمز عبور با موفقیت تغییر کرد</h3>
          <p>اکنون می‌توانید با رمز جدید وارد حساب خود شوید.</p>
          <button class="primary-btn large" type="button" @click="router.push('/login')">ورود</button>
        </div>
      </div>
    </div>
  </div>
</template>
