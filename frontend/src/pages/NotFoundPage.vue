<script setup lang="ts">
import AppButton from '@/components/ui/AppButton.vue'
import AppIcon from '@/components/ui/AppIcon.vue'
</script>
<template><main class="not-found"><div class="not-found__mark"><AppIcon name="search" :size="38" /></div><span>۴۰۴</span><h1>این صفحه پیدا نشد</h1><p>ممکن است نشانی تغییر کرده باشد. از داشبورد دوباره مسیرتان را پیدا کنید.</p><AppButton to="/app/dashboard" size="lg">بازگشت به داشبورد</AppButton></main></template>
<style scoped>
.not-found { display: grid; min-height: 100dvh; align-content: center; justify-items: center; padding: var(--space-6); text-align: center; }.not-found__mark { display: grid; width: 5rem; height: 5rem; border-radius: 1.5rem; background: var(--color-primary-soft); color: var(--color-primary); place-items: center; }.not-found > span { margin-top: var(--space-5); color: var(--color-gold); font-size: var(--font-size-sm); font-weight: 700; letter-spacing: .2em; }.not-found h1 { margin: var(--space-2) 0; font-size: var(--font-size-3xl); }.not-found p { max-width: 30rem; margin-bottom: var(--space-6); color: var(--color-text-muted); }
</style>
