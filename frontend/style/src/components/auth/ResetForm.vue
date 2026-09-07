<script setup lang="ts">
import { ref } from 'vue';
import { useAuthStore } from '@/stores/auth';
import Logo from '@/layouts/full/logo/Logo.vue';

const auth = useAuthStore();

const valid = ref(true);
const email = ref('');
const loading = ref(false);

// unified feedback state
const notice = ref<{ type: 'success' | 'error'; text: string } | null>(null);

const emailRules = [
  (v: string) => !!v || 'E-mail is required',
  (v: string) => /.+@.+\..+/.test(v) || 'E-mail must be valid',
];

const submit = async () => {
  if (!email.value) return;
  loading.value = true;
  notice.value = null;
  try {
    await auth.forgotPassword(email.value);
    notice.value = {
      type: 'success',
      text: 'If the email exists, a reset link has been sent.',
    };
  } catch (err: any) {
    notice.value = {
      type: 'error',
      text: err?.toString?.() || 'Something went wrong',
    };
  } finally {
    loading.value = false;
  }
};
</script>

<template>
  <v-form
    ref="form"
    v-model="valid"
    lazy-validation
    @submit.prevent="submit"
    class="mt-sm-13 mt-8"
  >
    <Logo class="mb-5" />

    <v-label class="text-subtitle-1 font-weight-medium pb-2 text-lightText">
      Email Address
    </v-label>
    <v-text-field
      v-model="email"
      :rules="emailRules"
      type="email"
      required
      class="mb-6"
    />

    <v-btn
      size="large"
      color="primary"
      block
      type="submit"
      :loading="loading"
      :disabled="loading || !valid"
      rounded="pill"
    >
      Forgot Password
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
      >
        <template #title>
          {{ notice.type === 'success' ? 'Check your email' : 'Oops' }}
        </template>
        {{ notice.text }}
      </v-alert>
    </v-expand-transition>
  </v-form>
</template>
