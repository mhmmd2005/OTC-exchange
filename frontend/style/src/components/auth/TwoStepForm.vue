<script setup lang="ts">
import { ref, watch, onMounted } from 'vue';
import { useAuthStore } from '@/stores/auth';

const auth = useAuthStore();

const codeDigits = ref<string[]>(['', '', '', '', '', '']);
const loading = ref(false);
const errorMessage = ref<string | null>(null);
const inputs = ref<NodeListOf<HTMLInputElement> | null>(null);

onMounted(() => {
  inputs.value = document.querySelectorAll<HTMLInputElement>('.verification input');
  inputs.value?.[0]?.focus();
});

function focusIndex(i: number) {
  inputs.value = document.querySelectorAll<HTMLInputElement>('.verification input');
  inputs.value?.[i]?.focus();
}

function handleInput(event: Event, index: number) {
  const input = event.target as HTMLInputElement;
  const val = input.value.replace(/\D/g, '');
  codeDigits.value[index] = val.slice(-1);
  input.value = codeDigits.value[index];
  if (codeDigits.value[index] && index < 5) focusIndex(index + 1);
}

function handleKeydown(event: KeyboardEvent, index: number) {
  const key = event.key;
  if (key === 'Backspace') {
    if (codeDigits.value[index]) {
      codeDigits.value[index] = '';
      return;
    }
    if (index > 0) {
      focusIndex(index - 1);
      event.preventDefault();
    }
  } else if (key === 'ArrowLeft') {
    if (index > 0) { focusIndex(index - 1); event.preventDefault(); }
  } else if (key === 'ArrowRight') {
    if (index < 5) { focusIndex(index + 1); event.preventDefault(); }
  } else if (key === 'Enter') {
    autoSubmit();
  }
}

function handlePaste(e: ClipboardEvent) {
  const text = (e.clipboardData?.getData('text') || '').replace(/\D/g, '').slice(0, 6);
  if (!text) return;
  e.preventDefault();
  for (let i = 0; i < 6; i++) codeDigits.value[i] = text[i] || '';
  const lastFilled = Math.min(text.length, 6) - 1;
  if (lastFilled >= 0) focusIndex(Math.min(lastFilled + 1, 5));
}

async function autoSubmit() {
  const code = codeDigits.value.join('');
  if (loading.value) return;
  if (code.length !== 6 || codeDigits.value.some(d => !d)) return;

  loading.value = true;
  errorMessage.value = null;
  try {
    await auth.verify2FA(code);
  } catch (err: any) {
    errorMessage.value = err?.message || String(err);
    codeDigits.value = Array(6).fill('');
    focusIndex(0);
  } finally {
    loading.value = false;
  }
}

// Auto-submit on any change once 6 digits are filled
watch(codeDigits, autoSubmit, { deep: true });
</script>

<template>
  <div class="mt-sm-13 mt-8">
    <v-label class="text-subtitle-1 font-weight-medium pb-2 text-lightText">
      Type your 6 digits security code
    </v-label>

    <div class="d-flex justify-space-between gap-3 mb-2 verification" @paste="handlePaste">
      <VTextField
        v-for="(_, i) in codeDigits"
        :key="i"
        v-model="codeDigits[i]"
        maxlength="1"
        inputmode="numeric"
        pattern="[0-9]*"
        type="tel"
        class="text-center"
        :autofocus="i === 0"
        :disabled="loading"
        @input="handleInput($event, i)"
        @keydown="handleKeydown($event, i)"
        hide-details
      />
    </div>

    <!-- Optional fallback button (kept for accessibility) -->
    <v-btn
      color="primary"
      size="large"
      rounded="pill"
      block
      flat
      :loading="loading"
      @click="autoSubmit"
    >
      Verify My Account
    </v-btn>

    <div v-if="errorMessage" class="mt-3">
      <v-alert type="error" dense>{{ errorMessage }}</v-alert>
    </div>
  </div>
</template>
