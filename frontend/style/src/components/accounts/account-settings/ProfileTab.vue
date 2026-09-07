<script setup lang="ts">
import { onMounted, ref, computed } from 'vue';
import { Form, Field } from 'vee-validate';
import * as yup from 'yup';
import { useAuthStore } from '@/stores/auth';
import COUNTRIES from '@/utils/countries';

const BUSINESS_CATEGORIES = [
  'Automotive','Communications and Media','Cryptocurrencies','E-commerce','Education',
  'Financial Services','Gambling/Casino','Government','Healthcare','Individual','Insurance',
  'IT Services and IT Consulting','Manufacturing and Natural Resources','Nonprofit',
  'Professional and Technical Services','Reseller','Retail','Technology, Information and Internet',
  'Transportation and Logistics','Utilities','Video Gaming','VPN',
];
const ORGANIZATION_SIZES = ['0-1','1-50','50-100','100-500','500-1000','1000-10000','10000+'];
const INTEREST_CATEGORIES = [
  'AI/ML','Wordpress','Full-Stack Web Development','Software Development',
  'Database Management','Game Development','Networking Engineering','Devops Engineering',
];

const auth = useAuthStore();

const initial = ref<Record<string, any>>({});
const loading = ref(false);
const saving = ref(false);

const snack = ref<{ open: boolean; text: string; color: 'success' | 'error' }>({
  open: false, text: '', color: 'success',
});

const LOCK_ONCE_FIELDS = new Set(['first_name', 'last_name', 'phone']);
const isLocked = (name: string) => {
  if (!LOCK_ONCE_FIELDS.has(name)) return false;
  const v = initial.value?.[name];
  return !!(typeof v === 'string' ? v.trim() : v);
};

const COUNTRY_CODES = computed(() => COUNTRIES.map(c => String(c.code).toUpperCase()));
const countryItems = computed(() =>
  COUNTRIES.map(c => ({ title: `${c.name} (${String(c.code).toUpperCase()})`, value: String(c.code).toUpperCase() }))
);

const schema = yup.object({
  first_name: yup.string().trim()
    .matches(/^[a-zA-Z\s\-]+$/, 'Only letters, spaces, and hyphens are allowed')
    .max(100).required('First name is required'),
  last_name: yup.string().trim()
    .matches(/^[a-zA-Z\s\-]+$/, 'Only letters, spaces, and hyphens are allowed')
    .max(100).required('Last name is required'),
  phone: yup.string().trim()
    .matches(/^\+?\d{7,20}$/, 'Invalid phone number').required('Phone is required'),
  address: yup.string().trim().max(200).required('Address is required'),
  address2: yup.string().trim().max(200).nullable(),
  country: yup.string()
    .transform(v => (v ? String(v).toUpperCase() : v))
    .oneOf(COUNTRY_CODES.value, 'Invalid country')
    .required('Country is required'),
  city: yup.string().trim().max(100).required('City is required'),
  zip_code: yup.string().trim()
    .matches(/^[a-zA-Z0-9]+$/, 'ZIP must be alphanumeric')
    .max(20).required('ZIP is required'),
  company_name: yup.string().trim().min(2, 'Must be at least 2 characters')
    .max(200).required('Company name is required'),
  vat_id: yup.string().trim().max(100).nullable(),
  company_url: yup.string().trim().url('Invalid URL').nullable()
    .transform(v => v === '' ? null : v),
  business_category: yup.string().oneOf(BUSINESS_CATEGORIES).required('Business category is required'),
  organization_size: yup.string().oneOf(ORGANIZATION_SIZES).required('Organization size is required'),
  interest_category: yup.string().oneOf(INTEREST_CATEGORIES).required('Interest category is required'),
});

async function load() {
  loading.value = true;
  try {
    const data = await auth.getProfile();
    initial.value = {
      first_name: data.first_name ?? '',
      last_name: data.last_name ?? '',
      phone: data.phone ?? '',
      address: data.address ?? '',
      address2: data.address2 ?? '',
      country: String(data.country || '').toUpperCase(),
      city: data.city ?? '',
      zip_code: String(data.zip_code || '').toUpperCase(),
      company_name: data.company_name ?? '',
      vat_id: data.vat_id ?? '',
      company_url: data.company_url ?? '',
      business_category: data.business_category ?? '',
      organization_size: data.organization_size ?? '',
      interest_category: data.interest_category ?? '',
      email: auth.user?.email || '',
    };
  } finally {
    loading.value = false;
  }
}

function onlyEditable(values: Record<string, any>) {
  const clone: Record<string, any> = { ...values };
  for (const key of LOCK_ONCE_FIELDS) {
    if (isLocked(key)) delete clone[key];
  }
  delete clone.email;
  if (clone.country) clone.country = String(clone.country).toUpperCase();
  if (clone.zip_code) clone.zip_code = String(clone.zip_code).toUpperCase();
  return clone;
}

async function onSubmit(values: any) {
  saving.value = true;
  try {
    const payload = onlyEditable(values);
    const updated = await auth.updateProfile(payload);
    if (updated.country) updated.country = String(updated.country).toUpperCase();
    if (updated.zip_code) updated.zip_code = String(updated.zip_code).toUpperCase();
    initial.value = { ...initial.value, ...updated };
    snack.value = { open: true, text: 'Profile updated successfully.', color: 'success' };
  } catch (e: any) {
    const msg = typeof e === 'string' ? e : (e?.detail || e?.message || 'Failed to update profile');
    snack.value = { open: true, text: msg, color: 'error' };
  } finally {
    saving.value = false;
  }
}

onMounted(load);
const disableSave = computed(() => loading.value || saving.value);
</script>

<template>
  <v-card elevation="10">
    <v-card-item>
      <h5 class="text-h5">Profile</h5>
      <div class="text-subtitle-1 text-grey100 mt-2">Update your personal and company information.</div>
    </v-card-item>

    <v-divider />

    <v-card-text>
      <div v-if="loading" class="py-10 text-center">
        <v-progress-circular indeterminate />
      </div>

      <Form v-else as="form" :validation-schema="schema" :initial-values="initial" @submit="onSubmit">
        <v-row>
          <v-col cols="12" md="6">
            <v-label class="mb-2 font-weight-medium">Email (locked)</v-label>
            <v-text-field :model-value="initial.email" readonly disabled tabindex="-1" variant="outlined" append-inner-icon="mdi-lock" />
          </v-col>

          <v-col cols="12" md="6">
            <v-label class="mb-2 font-weight-medium">Phone</v-label>
            <Field name="phone" v-slot="{ field, errors, handleChange, handleBlur }">
              <v-text-field
                :name="field.name"
                :model-value="field.value"
                @update:modelValue="val => handleChange(val)"
                @blur="handleBlur"
                :readonly="isLocked('phone')"
                :disabled="isLocked('phone')"
                :append-inner-icon="isLocked('phone') ? 'mdi-lock' : undefined"
                :tabindex="isLocked('phone') ? -1 : 0"
                variant="outlined"
                :error-messages="errors"
              />
            </Field>
          </v-col>

          <v-col cols="12" md="6">
            <v-label class="mb-2 font-weight-medium">First Name</v-label>
            <Field name="first_name" v-slot="{ field, errors, handleChange, handleBlur }">
              <v-text-field
                :name="field.name"
                :model-value="field.value"
                @update:modelValue="val => handleChange(val)"
                @blur="handleBlur"
                :readonly="isLocked('first_name')"
                :disabled="isLocked('first_name')"
                :append-inner-icon="isLocked('first_name') ? 'mdi-lock' : undefined"
                :tabindex="isLocked('first_name') ? -1 : 0"
                variant="outlined"
                :error-messages="errors"
              />
            </Field>
          </v-col>

          <v-col cols="12" md="6">
            <v-label class="mb-2 font-weight-medium">Last Name</v-label>
            <Field name="last_name" v-slot="{ field, errors, handleChange, handleBlur }">
              <v-text-field
                :name="field.name"
                :model-value="field.value"
                @update:modelValue="val => handleChange(val)"
                @blur="handleBlur"
                :readonly="isLocked('last_name')"
                :disabled="isLocked('last_name')"
                :append-inner-icon="isLocked('last_name') ? 'mdi-lock' : undefined"
                :tabindex="isLocked('last_name') ? -1 : 0"
                variant="outlined"
                :error-messages="errors"
              />
            </Field>
          </v-col>

          <v-col cols="12" md="4">
            <v-label class="mb-2 font-weight-medium">Country</v-label>
            <Field name="country" v-slot="{ field, errors, handleChange, handleBlur }">
              <v-autocomplete
                :name="field.name"
                :items="countryItems"
                item-title="title"
                item-value="value"
                :model-value="(field.value || '').toString().toUpperCase()"
                @update:modelValue="val => handleChange((val || '').toString().toUpperCase())"
                @blur="handleBlur"
                placeholder="Select a country"
                variant="outlined"
                :error-messages="errors"
                :return-object="false"
                clearable
              />
            </Field>
          </v-col>

          <v-col cols="12" md="4">
            <v-label class="mb-2 font-weight-medium">City</v-label>
            <Field name="city" v-slot="{ field, errors, handleChange, handleBlur }">
              <v-text-field
                :name="field.name"
                :model-value="field.value"
                @update:modelValue="val => handleChange(val)"
                @blur="handleBlur"
                variant="outlined"
                :error-messages="errors"
              />
            </Field>
          </v-col>

          <v-col cols="12" md="4">
            <v-label class="mb-2 font-weight-medium">ZIP Code</v-label>
            <Field name="zip_code" v-slot="{ field, errors, handleChange, handleBlur }">
              <v-text-field
                :name="field.name"
                :model-value="field.value"
                @update:modelValue="val => handleChange(val?.toString().toUpperCase())"
                @blur="handleBlur"
                variant="outlined"
                :error-messages="errors"
              />
            </Field>
          </v-col>

          <v-col cols="12">
            <v-label class="mb-2 font-weight-medium">Address</v-label>
            <Field name="address" v-slot="{ field, errors, handleChange, handleBlur }">
              <v-text-field
                :name="field.name"
                :model-value="field.value"
                @update:modelValue="val => handleChange(val)"
                @blur="handleBlur"
                variant="outlined"
                :error-messages="errors"
              />
            </Field>
          </v-col>

          <v-col cols="12">
            <v-label class="mb-2 font-weight-medium">Address 2</v-label>
            <Field name="address2" v-slot="{ field, errors, handleChange, handleBlur }">
              <v-text-field
                :name="field.name"
                :model-value="field.value"
                @update:modelValue="val => handleChange(val)"
                @blur="handleBlur"
                variant="outlined"
                :error-messages="errors"
              />
            </Field>
          </v-col>

          <v-col cols="12" md="6">
            <v-label class="mb-2 font-weight-medium">Company Name</v-label>
            <Field name="company_name" v-slot="{ field, errors, handleChange, handleBlur }">
              <v-text-field
                :name="field.name"
                :model-value="field.value"
                @update:modelValue="val => handleChange(val)"
                @blur="handleBlur"
                variant="outlined"
                :error-messages="errors"
              />
            </Field>
          </v-col>

          <v-col cols="12" md="6">
            <v-label class="mb-2 font-weight-medium">VAT ID</v-label>
            <Field name="vat_id" v-slot="{ field, errors, handleChange, handleBlur }">
              <v-text-field
                :name="field.name"
                :model-value="field.value"
                @update:modelValue="val => handleChange(val)"
                @blur="handleBlur"
                variant="outlined"
                :error-messages="errors"
              />
            </Field>
          </v-col>

          <v-col cols="12" md="6">
            <v-label class="mb-2 font-weight-medium">Company URL</v-label>
            <Field name="company_url" v-slot="{ field, errors, handleChange, handleBlur }">
              <v-text-field
                :name="field.name"
                :model-value="field.value"
                @update:modelValue="val => handleChange(val)"
                @blur="handleBlur"
                placeholder="https://example.com"
                variant="outlined"
                :error-messages="errors"
              />
            </Field>
          </v-col>

          <v-col cols="12" md="4">
            <v-label class="mb-2 font-weight-medium">Business Category</v-label>
            <Field name="business_category" v-slot="{ field, errors, handleChange, handleBlur }">
              <v-select
                :name="field.name"
                :items="BUSINESS_CATEGORIES"
                :model-value="field.value"
                @update:modelValue="val => handleChange(val)"
                @blur="handleBlur"
                variant="outlined"
                :error-messages="errors"
                clearable
              />
            </Field>
          </v-col>

          <v-col cols="12" md="4">
            <v-label class="mb-2 font-weight-medium">Organization Size</v-label>
            <Field name="organization_size" v-slot="{ field, errors, handleChange, handleBlur }">
              <v-select
                :name="field.name"
                :items="ORGANIZATION_SIZES"
                :model-value="field.value"
                @update:modelValue="val => handleChange(val)"
                @blur="handleBlur"
                variant="outlined"
                :error-messages="errors"
                clearable
              />
            </Field>
          </v-col>

          <v-col cols="12" md="4">
            <v-label class="mb-2 font-weight-medium">Interest Category</v-label>
            <Field name="interest_category" v-slot="{ field, errors, handleChange, handleBlur }">
              <v-select
                :name="field.name"
                :items="INTEREST_CATEGORIES"
                :model-value="field.value"
                @update:modelValue="val => handleChange(val)"
                @blur="handleBlur"
                variant="outlined"
                :error-messages="errors"
                clearable
              />
            </Field>
          </v-col>
        </v-row>

        <div class="d-flex justify-end mt-6">
          <v-btn size="large" color="primary" rounded="pill" class="mr-3" type="submit" :loading="saving" :disabled="disableSave">
            Save
          </v-btn>
          <v-btn size="large" class="bg-lighterror text-error" rounded="pill" @click="load" :disabled="loading || saving">
            Reset
          </v-btn>
        </div>
      </Form>

      <v-snackbar v-model="snack.open" :timeout="3000" :color="snack.color" location="bottom" variant="elevated">
        {{ snack.text }}
      </v-snackbar>

      <div class="text-caption text-grey600 mt-4">
        Identity fields lock after first save. Contact support to request changes.
      </div>
    </v-card-text>
  </v-card>
</template>
