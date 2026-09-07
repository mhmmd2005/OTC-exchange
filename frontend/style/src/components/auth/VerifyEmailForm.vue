<script setup lang="ts">
import { ref } from 'vue';
import { useAuthStore } from '@/stores/auth';

const auth = useAuthStore();
const code = ref('');
const loading = ref(false);
const error = ref<string | null>(null);

const submit = async () => {
  error.value = null;
  loading.value = true;
  try {
    await auth.verifyEmail(code.value);
  } catch (e: any) {
    error.value = e.toString();
  } finally {
    loading.value = false;
  }
};
</script>

<template>
  <div class="mt-sm-13 mt-8">
    <v-label class="text-subtitle-1 font-weight-medium pb-2 text-lightText">
      Enter the 6-digit code from your email
    </v-label>
    <div class="d-flex justify-space-between gap-3 mb-2 verification">
      <VTextField v-model="code" maxlength="6" counter="6" />
    </div>
    <v-btn color="primary" size="large" rounded="pill" block flat @click="submit" :loading="loading">
      Verify Email
    </v-btn>
    <div v-if="error" class="text-error mt-3">{{ error }}</div>
  </div>
</template>
