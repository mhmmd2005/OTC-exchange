<script setup lang="ts">
import AppIcon from './AppIcon.vue'

defineProps<{ context: 'otp' | 'withdrawal' | 'two-factor' }>()
</script>

<template>
  <p v-if="context === 'two-factor'" class="demo-hint demo-hint--two-factor">
    در نسخه نمایشی، پس از افزودن حساب کد <bdi dir="ltr">۱۲۳۴۵۶</bdi> را وارد کنید.
  </p>
  <p v-else class="demo-hint">
    <AppIcon name="info" :size="16" />
    {{ context === 'withdrawal' ? 'در نسخه نمایشی کد' : 'کد نسخه نمایشی' }}
    <bdi dir="ltr">۱۲۳۴۵۶</bdi>
    {{ context === 'withdrawal' ? 'را وارد کنید.' : 'است.' }}
  </p>
</template>

