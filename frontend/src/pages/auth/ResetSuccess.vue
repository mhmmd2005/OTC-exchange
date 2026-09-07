<script setup lang="ts">
import AppButton from '@/components/ui/AppButton.vue'
import AppCard from '@/components/ui/AppCard.vue'
import AppIcon from '@/components/ui/AppIcon.vue'
</script>

<template>
  <AppCard padding="lg" class="auth-view auth-result">
    <div class="auth-result__symbol auth-result__symbol--success" aria-hidden="true">
      <AppIcon name="check" :size="30" />
    </div>

    <div class="auth-intro auth-result__intro">
      <span class="auth-kicker">بازیابی با موفقیت انجام شد</span>
      <h1 class="auth-title">رمز عبور شما تغییر کرد</h1>
      <p class="auth-description">
        از این پس با رمز عبور جدید وارد حساب شوید. برای امنیت بیشتر، رمز قبلی دیگر قابل استفاده نیست.
      </p>
    </div>

    <AppButton to="/auth/login" size="lg" block icon="login">
      ورود به حساب
    </AppButton>

    <div class="auth-security-note auth-result__note">
      <AppIcon name="shield" :size="18" />
      <span>اگر این تغییر را شما انجام نداده‌اید، پیش از ورود با پشتیبانی روشا تماس بگیرید.</span>
    </div>
  </AppCard>
</template>

<style scoped>
.auth-result { text-align: center; }

.auth-result__symbol {
  display: grid;
  width: 4.25rem;
  height: 4.25rem;
  margin: 0 auto var(--space-5);
  border: 1px solid rgba(53, 201, 149, .28);
  border-radius: 1.35rem;
  background: var(--color-success-soft);
  color: var(--color-success);
  box-shadow: 0 0 0 .45rem rgba(53, 201, 149, .045);
  place-items: center;
}

.auth-result__intro { margin-inline: auto; }
.auth-result__note { margin-top: var(--space-5); text-align: right; }
</style>
