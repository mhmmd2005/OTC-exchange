<script setup lang="ts">
import { ref, onMounted, computed } from 'vue';
import { useRoute, useRouter } from 'vue-router';
import Logo from '@/layouts/full/logo/Logo.vue';
import { useAuthStore } from '@/stores/auth';

const route = useRoute();
const router = useRouter();
const auth = useAuthStore();

const token = ref<string>('');
const checking = ref(true);
const loading = ref(false);
const status = ref<'idle' | 'success' | 'error'>('idle');
const message = ref<string>('');

const password = ref('');
const confirmPassword = ref('');

const showForm = computed(() => !checking.value && status.value === 'idle');

const passwordRules = [
  (v: string) => !!v || 'Password is required',
  (v: string) => v.length >= 8 || 'Min 8 characters',
];

onMounted(async () => {
  token.value = (route.params.token as string) || '';
  if (!token.value) {
    status.value = 'error';
    message.value = 'Missing token in URL.';
    checking.value = false;
    return;
  }

  try {
    const res = await fetch(
      `${import.meta.env.VITE_API_URL}/accounts/reset-password-confirm/?token=${encodeURIComponent(token.value)}`
    );
    const data = await res.json().catch(() => ({}));
    if (!res.ok) {
      status.value = 'error';
      message.value = data.detail || 'Token is invalid or expired';
    } else {
      status.value = 'idle';
      message.value = '';
    }
  } catch {
    status.value = 'error';
    message.value = 'Network error.';
  } finally {
    checking.value = false;
  }
});

const submit = async () => {
  if (!showForm.value) return;

  if (password.value !== confirmPassword.value) {
    status.value = 'error';
    message.value = 'Passwords do not match.';
    return;
  }

  loading.value = true;
  status.value = 'idle';
  message.value = '';

  try {
    const res = await auth.resetPasswordConfirm(token.value, password.value, confirmPassword.value);
    status.value = 'success';
    message.value = (res?.detail as string) || 'Password has been reset. You can login now.';
    setTimeout(() => router.push('/login'), 2000);
  } catch (e: any) {
    status.value = 'error';
    message.value = e?.toString?.() || 'Password reset failed.';
  } finally {
    loading.value = false;
  }
};
</script>

<template>
  <div class="login-app-wrapper">
    <div class="auth-login position-relative d-flex align-center justify-content-center px-lg-16 px-sm-8 px-3 rounded-xl">
      <div class="auth-login-wrapper position-relative rounded-xl mx-lg-16 mx-4 mx-auto w-100" style="max-width: 980px">
        <v-card elevation="0" class="overflow-hidden px-sm-3 position-relative z-index-2">
          <v-card-item class="px-sm-8 px-3">
            <Logo />
            <v-row class="justify-md-space-around align-center py-md-8">
              <v-col cols="12" lg="5" md="6" class="d-md-flex d-none">
                <img src="@/assets/images/backgrounds/login-security.png" class="w-100" alt="reset-background" />
              </v-col>

              <v-col cols="12" lg="5" md="6">
                <div class="mt-xl-0 mt-5 mw-100">
                  <h2 class="text-h4 font-weight-bold mb-2">Reset your password</h2>
                  <div class="text-14 mb-6 font-weight-medium mt-3">
                    Please enter your new password below.
                  </div>

                  <v-alert v-if="checking" type="info" variant="tonal" border="start" prominent class="mb-4">
                    Validating link...
                  </v-alert>

                  <v-alert
                    v-if="!checking && status !== 'idle'"
                    class="mb-4"
                    :type="status === 'success' ? 'success' : 'error'"
                    variant="tonal"
                    border="start"
                    prominent
                  >
                    {{ message }}
                  </v-alert>

                  <v-form v-if="showForm" @submit.prevent="submit">
                    <v-label class="text-subtitle-1 font-weight-medium pb-2 text-lightText">New Password</v-label>
                    <v-text-field
                      v-model="password"
                      :rules="passwordRules"
                      type="password"
                      autocomplete="new-password"
                      required
                    />

                    <v-label class="text-subtitle-1 font-weight-medium pb-2 text-lightText">Confirm Password</v-label>
                    <v-text-field
                      v-model="confirmPassword"
                      type="password"
                      autocomplete="new-password"
                      required
                    />

                    <v-btn size="large" color="primary" block type="submit" :loading="loading" rounded="pill">
                      Reset Password
                    </v-btn>
                  </v-form>

                  <div v-if="!checking && status==='error'" class="d-flex justify-center mt-3">
                    <v-btn variant="text" color="primary" @click="$router.push('/forgot-password')">
                      Request a new reset link
                    </v-btn>
                  </div>
                </div>
              </v-col>
            </v-row>
          </v-card-item>
        </v-card>
      </div>
    </div>
  </div>
</template>
