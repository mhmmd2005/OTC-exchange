<script setup>
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import { ArrowLeft, CheckCircle2, Mail } from 'lucide-vue-next'

const router = useRouter()
const email = ref('')
const sent = ref(false)

function submit() {
  if (!email.value) return
  sent.value = true
}
</script>

<template>
  <div class="auth-shell compact-shell">
    <div class="auth-card compact-card">
      <div class="auth-form-panel full-panel">
        <button class="text-action" type="button" @click="router.push('/login')">
          <ArrowLeft :size="16" /> بازگشت
        </button>

        <div v-if="!sent" class="auth-header">
          <h2>بازیابی رمز عبور</h2>
          <p>ایمیل یا نام کاربری خود را وارد کنید تا لینک بازیابی ارسال شود.</p>
        </div>

        <form v-if="!sent" class="auth-form" @submit.prevent="submit">
          <div class="field">
            <label>ایمیل</label>
            <div class="input-icon-wrap">
              <Mail :size="16" />
              <input v-model="email" class="input" type="email" placeholder="you@example.com" />
            </div>
          </div>
          <button class="primary-btn large" type="submit">ارسال لینک بازیابی</button>
        </form>

        <div v-else class="success-box">
          <CheckCircle2 :size="40" />
          <h3>لینک بازیابی ارسال شد</h3>
          <p>ایمیل با لینک بازیابی برای شما ارسال شد. لطفاً صندوق ورودی را بررسی کنید.</p>
          <button class="primary-btn large" type="button" @click="router.push('/reset-password')">تغییر رمز عبور</button>
        </div>
      </div>
    </div>
  </div>
</template>
