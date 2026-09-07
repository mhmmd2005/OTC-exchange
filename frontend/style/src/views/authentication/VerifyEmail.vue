<script setup lang="ts">
import { useRoute, useRouter } from 'vue-router';
import { ref, onMounted } from 'vue';
import Logo from '@/layouts/full/logo/Logo.vue';

const route = useRoute();
const router = useRouter();

const status = ref<'loading' | 'success' | 'error'>('loading');
const message = ref('Verifying your email, please wait...');

onMounted(async () => {
  const token = route.params.token as string | undefined;
  if (!token) {
    status.value = 'error';
    message.value = 'Missing token.';
    return;
  }

  try {
    const res = await fetch(`${import.meta.env.VITE_API_URL}/accounts/verify-email/${token}/`, {
      method: 'GET',
      headers: { 'Content-Type': 'application/json' },
    });
    const data = await res.json().catch(() => ({}));

    if (res.ok) {
      status.value = 'success';
      message.value = data.message || 'Your email has been verified successfully!';
      setTimeout(() => router.push('/login'), 2000);
    } else {
      status.value = 'error';
      message.value = data.error || data.detail || 'Email verification failed.';
    }
  } catch {
    status.value = 'error';
    message.value = 'Network error.';
  }
});
</script>

<template>
  <div class="login-app-wrapper">
    <div class="auth-login position-relative d-flex align-center justify-content-center px-lg-16 px-sm-8 px-3 rounded-xl">
      <div class="auth-login-wrapper position-relative rounded-xl mx-lg-16 mx-4 mx-auto w-100">
        <v-card elevation="0" class="overflow-hidden px-sm-3 position-relative z-index-2">
          <v-card-item class="px-sm-8 px-3">
            <Logo />
            <div class="mt-8 text-center">
              <h2 class="text-h4 font-weight-bold mb-4">Email Verification</h2>
              <div :class="['text-subtitle-1', status==='success' ? 'text-success' : status==='error' ? 'text-error' : '']">
                {{ message }}
              </div>
            </div>
          </v-card-item>
        </v-card>
      </div>
    </div>
  </div>
</template>
