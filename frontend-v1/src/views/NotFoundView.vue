<script setup>
import { useRouter } from 'vue-router'
const router = useRouter()
</script>

<template>
  <div class="auth-shell compact-shell">
    <div class="auth-card compact-card">
      <div class="auth-form-panel full-panel not-found-box">
        <div class="not-found-code">404</div>
        <h2>صفحه پیدا نشد</h2>
        <p>مسیر درخواستی موجود نیست یا حذف شده است.</p>
        <button class="primary-btn large" type="button" @click="router.push('/')">بازگشت به خانه</button>
      </div>
    </div>
  </div>
</template>
