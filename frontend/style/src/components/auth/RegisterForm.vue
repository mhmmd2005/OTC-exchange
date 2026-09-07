<script setup lang="ts">
import { ref } from 'vue';
import { useRouter } from 'vue-router';
import Turnstile from '@/components/auth/Turnstile.vue';

const router = useRouter();

const email = ref('');
const password = ref('');
const password2 = ref('');
const captcha = ref<string | null>(null);
const captchaRef = ref<InstanceType<typeof Turnstile> | null>(null);
const loading = ref(false);

// field-level error buckets
const emailErrors = ref<string[]>([]);
const passwordErrors = ref<string[]>([]);
const password2Errors = ref<string[]>([]);
const captchaErrors = ref<string[]>([]);

// global (non-field) errors
const globalErrors = ref<string[]>([]);

const siteKey = (import.meta.env.VITE_TURNSTILE_SITE_KEY as string) || '';

/** Convert various API error shapes into ordered lists */
async function normalizeApiErrors(res: Response): Promise<{
  field: Record<string, string[]>;
  global: string[];
}> {
  const out = { field: {} as Record<string, string[]>, global: [] as string[] };

  // Try to parse JSON; fall back to text if not JSON
  let data: any;
  try {
    const clone = res.clone();
    data = await res.json().catch(async () => {
      const t = await clone.text();
      return t ? { detail: t } : {};
    });
  } catch {
    data = {};
  }

  // If it's a plain string, treat as global error
  if (typeof data === 'string') {
    out.global.push(data);
    return out;
  }

  // Common keys from DRF and custom handlers
  const order = [
    'detail',
    'non_field_errors',
    'email',
    'password',
    'password2',
    'turnstile_token',
    'captcha',
    'message',
    'error'
  ];

  const pushVals = (arr: unknown, into: string[]) => {
    if (Array.isArray(arr)) {
      arr.forEach(v => pushVals(v, into));
    } else if (arr && typeof arr === 'object') {
      // flatten nested objects
      Object.values(arr as Record<string, unknown>).forEach(v => pushVals(v, into));
    } else if (arr != null) {
      into.push(String(arr));
    }
  };

  // First ordered keys
  for (const key of order) {
    if (Object.prototype.hasOwnProperty.call(data, key)) {
      const val = (data as any)[key];
      if (['email','password','password2','turnstile_token','captcha'].includes(key)) {
        const bucket = (out.field[key] ||= []);
        pushVals(val, bucket);
      } else {
        pushVals(val, out.global);
      }
    }
  }

  // Then any remaining keys (sorted) to keep deterministic output
  for (const key of Object.keys(data).sort()) {
    if (order.includes(key)) continue;
    const val = (data as any)[key];
    if (typeof val === 'string' || Array.isArray(val) || (val && typeof val === 'object')) {
      const isFieldish = ['username','first_name','last_name','profile'].some(k => key.includes(k));
      if (isFieldish) {
        const bucket = (out.field[key] ||= []);
        pushVals(val, bucket);
      } else {
        // prefix with key so it's understandable
        const tmp: string[] = [];
        pushVals(val, tmp);
        tmp.forEach(msg => out.global.push(`${key}: ${msg}`));
      }
    }
  }

  // Fallback messages
  if (!out.global.length && !Object.keys(out.field).length) {
    out.global.push(`Request failed (${res.status})`);
  }

  return out;
}

function clearErrors() {
  emailErrors.value = [];
  passwordErrors.value = [];
  password2Errors.value = [];
  captchaErrors.value = [];
  globalErrors.value = [];
}

async function register() {
  loading.value = true;
  clearErrors();

  try {
    const res = await fetch(`${import.meta.env.VITE_API_URL}/accounts/register/`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        email: email.value,
        password: password.value,
        password2: password2.value,
        turnstile_token: captcha.value || '',
      }),
      credentials: 'include',
    });

    if (!res.ok) {
      const norm = await normalizeApiErrors(res);
      emailErrors.value = norm.field.email ?? [];
      passwordErrors.value = norm.field.password ?? [];
      password2Errors.value = norm.field.password2 ?? [];
      // Map both server keys to the captcha field
      captchaErrors.value = norm.field.turnstile_token ?? norm.field.captcha ?? [];
      globalErrors.value = norm.global;

      // Reset captcha on failure to force a fresh token
      captchaRef.value?.reset?.();
      captcha.value = null;
      return;
    }

    // success → go to login with verify notice
    router.push({ path: '/login', query: { notice: 'verify-email' } });
  } catch (err: any) {
    globalErrors.value = [err?.message || 'Registration failed'];
  } finally {
    loading.value = false;
  }
}
</script>

<template>
  <v-form @submit.prevent="register">
    <v-label class="text-subtitle-1 font-weight-medium pb-2">Email</v-label>
    <VTextField v-model="email" type="email" required :error-messages="emailErrors" />

    <v-label class="text-subtitle-1 font-weight-medium pb-2">Password</v-label>
    <VTextField v-model="password" type="password" required :error-messages="passwordErrors" />

    <v-label class="text-subtitle-1 font-weight-medium pb-2">Confirm Password</v-label>
    <VTextField v-model="password2" type="password" required :error-messages="password2Errors" />

    <div class="mt-3 mb-2">
      <Turnstile ref="captchaRef" v-model:token="captcha" :site-key="siteKey" />
      <div v-if="captchaErrors.length" class="mt-2">
        <v-alert type="error" border="start" density="compact" variant="tonal">
          <ul class="ma-0 pl-4">
            <li v-for="(e, i) in captchaErrors" :key="'cap-' + i">{{ e }}</li>
          </ul>
        </v-alert>
      </div>
    </div>

    <v-btn
      size="large"
      class="mt-2"
      color="primary"
      :disabled="loading"
      :loading="loading"
      block
      rounded="pill"
      type="submit"
    >
      Sign Up
    </v-btn>

    <div v-if="globalErrors.length" class="mt-3">
      <v-alert type="error" border="start" prominent>
        <ul class="ma-0 pl-6">
          <li v-for="(e, i) in globalErrors" :key="'g-' + i">{{ e }}</li>
        </ul>
      </v-alert>
    </div>
  </v-form>
</template>
