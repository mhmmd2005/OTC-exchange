<script setup lang="ts">
import { computed } from 'vue'
import { useRoute } from 'vue-router'
import AppButton from '@/components/ui/AppButton.vue'
import AppCard from '@/components/ui/AppCard.vue'
import AppIcon from '@/components/ui/AppIcon.vue'
import { safeAppRedirect } from './auth.utils'

const route = useRoute()
const loginRoute = computed(() => ({
  name: 'login',
  query: { redirect: safeAppRedirect(route.query.redirect) },
}))
</script>

<template>
  <AppCard padding="lg" class="auth-view auth-result">
    <div class="auth-result__symbol" aria-hidden="true">
      <AppIcon name="clock" :size="29" />
    </div>

    <div class="auth-intro auth-result__intro">
      <span class="auth-kicker">حفاظت از حساب</span>
      <h1 class="auth-title">نشست شما منقضی شده است</h1>
      <p class="auth-description">
        برای ادامه کار، دوباره وارد حساب شوید. پس از ورود به مسیر قبلی بازمی‌گردید.
      </p>
    </div>

    <AppButton :to="loginRoute" size="lg" block icon="login">
      ورود مجدد
    </AppButton>

    <div class="auth-security-note auth-result__note">
      <AppIcon name="shield" :size="18" />
      <span>این خروج خودکار برای محافظت از اطلاعات مالی شما انجام شده است.</span>
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
  border: 1px solid rgba(221, 183, 110, .28);
  border-radius: 1.35rem;
  background: var(--color-gold-soft);
  color: var(--color-gold);
  box-shadow: 0 0 0 .45rem rgba(221, 183, 110, .045);
  place-items: center;
}

.auth-result__intro { margin-inline: auto; }
.auth-result__note { margin-top: var(--space-5); text-align: right; }
</style>
