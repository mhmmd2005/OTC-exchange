<script setup lang="ts">
import { ref } from 'vue';
import { useAuthStore } from '@/stores/auth';
import { Form } from 'vee-validate';
import Turnstile from '@/components/auth/Turnstile.vue';

const password = ref('');
const username = ref('');
const captcha = ref<string | null>(null);
const captchaRef = ref<InstanceType<typeof Turnstile> | null>(null);
const siteKey = (import.meta.env.VITE_TURNSTILE_SITE_KEY as string) || '';

const notice = ref<{ type: 'success' | 'info' | 'warning' | 'error'; title: string; text: string } | null>(null);

const passwordRules = [
  (v: string) => !!v || 'Password is required',
  (v: string) => (v && v.length >= 10) || 'Password must be at least 10 characters',
];
const emailRules = [
  (v: string) => !!v || 'E-mail is required',
  (v: string) => /.+@.+\..+/.test(v) || 'E-mail must be valid',
];

function cleanErrorText(err: unknown): string {
  const s = String(err ?? '');
  // strip common prefixes
  return s.replace(/^Error:\s*/i, '').trim();
}

async function validate(_values: any) {
  const authStore = useAuthStore();
  notice.value = null;

  if (!captcha.value) {
    notice.value = {
      type: 'warning',
      title: 'Complete the captcha',
      text: 'Please complete the captcha challenge to continue.',
    };
    return;
  }

  try {
    await authStore.login({
      email: username.value,
      password: password.value,
      turnstile_token: captcha.value,
    });
  } catch (error: any) {
    notice.value = {
      type: 'error',
      title: 'Sign-in failed',
      text: cleanErrorText(error),
    };
  } finally {
    // Turnstile tokens are single-use; reset after each attempt
    captchaRef.value?.reset();
    captcha.value = null;
  }
}
</script>

<template>
  <Form @submit="validate" v-slot="{ isSubmitting }" class="mt-5">
    <v-label class="text-subtitle-1 font-weight-semibold pb-2 text-grey200">Username</v-label>
    <VTextField
      v-model="username"
      :rules="emailRules"
      class="mb-6"
      required
      hide-details="auto"
    />

    <v-label class="text-subtitle-1 font-weight-semibold pb-2 text-grey200">Password</v-label>
    <VTextField
      v-model="password"
      :rules="passwordRules"
      required
      hide-details="auto"
      type="password"
      class="pwdInput mb-4"
    />

    <div class="mt-2 mb-2">
      <Turnstile ref="captchaRef" v-model:token="captcha" :site-key="siteKey" />
    </div>

    <div class="d-flex flex-wrap align-center my-3 ml-n2">
      <div class="ml-sm-auto">
        <RouterLink
          to="/forgot-password"
          class="text-primary text-decoration-none text-body-1 opacity-1 font-weight-medium"
        >
          Forgot Password ?
        </RouterLink>
      </div>
    </div>

    <v-btn
      size="large"
      rounded="pill"
      :loading="isSubmitting"
      color="primary"
      :disabled="isSubmitting"
      block
      type="submit"
      flat
    >
      Sign In
    </v-btn>

    <v-expand-transition>
      <v-alert
        v-if="notice"
        :type="notice.type"
        variant="tonal"
        border="start"
        class="mt-4"
        density="comfortable"
        prominent
        closable
      >
        <template #title>
          {{ notice.title }}
        </template>
        {{ notice.text }}
      </v-alert>
    </v-expand-transition>
  </Form>
</template>
