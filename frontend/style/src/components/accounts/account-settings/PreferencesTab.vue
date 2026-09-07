<script setup lang="ts">
import { onMounted, ref, computed } from 'vue';
import { Form, Field } from 'vee-validate';
import * as yup from 'yup';
import { useAuthStore } from '@/stores/auth';
import { DeviceFloppyIcon, RefreshIcon } from 'vue-tabler-icons';

const auth = useAuthStore();

const loading = ref(false);
const saving = ref(false);
const errorMsg = ref<string | null>(null);
const success = ref(false);

const timezones = ref<string[]>([]);
const dateFormatOptions = [
  { label: 'YYYY-MM-DD', value: '0' },
  { label: 'MM-DD-YYYY', value: '1' },
  { label: 'DD-MM-YYYY', value: '2' },
];


const initial = ref<{ timezone: string; date_format: string }>({ timezone: 'UTC', date_format: 'YYYY-MM-DD' });

const schema = yup.object({
  timezone: yup.string().required('Timezone is required'),
    date_format: yup
    .string()
    .oneOf(['0','1','2'], 'Invalid date format')
    .required('Date format is required'),

});

function loadTimezones() {
  try {
    // Use browser's IANA list if available
    // @ts-expect-error TS may not know supportedValuesOf
    const supported = typeof Intl.supportedValuesOf === 'function' ? Intl.supportedValuesOf('timeZone') : [];
    if (Array.isArray(supported) && supported.length) {
      timezones.value = supported.slice().sort((a, b) => a.localeCompare(b));
      return;
    }
  } catch {}
  // Fallback minimal list
  timezones.value = [
    'UTC',
    'Europe/London',
    'Europe/Paris',
    'Europe/Berlin',
    'Europe/Madrid',
    'Europe/Rome',
    'Asia/Tehran',
    'Asia/Dubai',
    'Asia/Tokyo',
    'Asia/Shanghai',
    'Asia/Singapore',
    'America/New_York',
    'America/Los_Angeles',
    'America/Chicago',
    'America/Sao_Paulo',
    'America/Santo_Domingo',
    'Africa/Cairo',
    'Africa/Johannesburg',
    'Australia/Sydney',
    'Pacific/Auckland',
  ].sort((a, b) => a.localeCompare(b));
}

async function load() {
  loading.value = true;
  errorMsg.value = null;
  success.value = false;
  try {
    const data = await auth.getTimePrefs();
    initial.value = {
      timezone: data.timezone ?? 'UTC',
      date_format: data.date_format ?? 'YYYY-MM-DD',
    };
  } catch (e: any) {
    errorMsg.value = typeof e === 'string' ? e : (e?.detail || e?.message || 'Failed to load preferences');
  } finally {
    loading.value = false;
  }
}

async function onSubmit(values: any) {
  saving.value = true;
  errorMsg.value = null;
  success.value = false;
  try {
    const payload = {
      timezone: values.timezone,
      date_format: values.date_format,
    };
    const saved = await auth.updateTimePrefs(payload);
    initial.value = { timezone: saved.timezone, date_format: saved.date_format };
    success.value = true;
  } catch (e: any) {
    errorMsg.value = typeof e === 'string' ? e : (e?.detail || e?.message || 'Failed to save preferences');
  } finally {
    saving.value = false;
  }
}

onMounted(() => {
  loadTimezones();
  load();
});

const disableSave = computed(() => loading.value || saving.value);
</script>

<template>
  <v-card elevation="10">
    <v-card-item>
      <h5 class="text-h5">Preferences</h5>
      <div class="text-subtitle-1 text-grey100 mt-2">Timezone and date format for your account.</div>
    </v-card-item>

    <v-divider />

    <v-card-text>
      <v-alert v-if="errorMsg" type="error" class="mb-4" variant="tonal">{{ errorMsg }}</v-alert>
      <v-alert v-if="success" type="success" class="mb-4" variant="tonal">Preferences updated successfully.</v-alert>

      <div v-if="loading" class="py-10 text-center"><v-progress-circular indeterminate /></div>

      <Form v-else as="form" :validation-schema="schema" :initial-values="initial" @submit="onSubmit">
        <v-row>
          <v-col cols="12" md="6">
            <v-label class="mb-2 font-weight-medium">Timezone</v-label>
            <Field name="timezone" v-slot="{ field, errors }">
              <v-select
                :name="field.name"
                :items="timezones"
                :model-value="field.value"
                @update:modelValue="field.onChange"
                @blur="field.onBlur"
                variant="outlined"
                :error-messages="errors"
                placeholder="Select timezone"
                density="comfortable"
              />
            </Field>
          </v-col>

          <v-col cols="12" md="6">
            <v-label class="mb-2 font-weight-medium">Date format</v-label>
            <Field name="date_format" v-slot="{ field, errors }">
              <v-select
                :name="field.name"
                :items="dateFormatOptions"
                item-title="label"
                item-value="value"
                :model-value="field.value"
                @update:modelValue="field.onChange"
                @blur="field.onBlur"
                variant="outlined"
                :error-messages="errors"
                placeholder="Select date format"
                density="comfortable"
              />
            </Field>
          </v-col>
        </v-row>

        <div class="d-flex justify-end mt-6">
          <v-btn
            size="large"
            class="bg-lighterror text-error mr-3"
            rounded="pill"
            :disabled="loading || saving"
            @click="load"
          >
            <RefreshIcon size="18" class="mr-1" /> Reset
          </v-btn>
          <v-btn
            size="large"
            color="primary"
            rounded="pill"
            type="submit"
            :loading="saving"
            :disabled="disableSave"
          >
            <DeviceFloppyIcon size="18" class="mr-1" /> Save
          </v-btn>
        </div>
      </Form>
    </v-card-text>
  </v-card>
</template>
