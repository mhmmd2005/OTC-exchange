<script setup lang="ts">
import { onMounted, ref, computed } from 'vue';
import { Form, Field } from 'vee-validate';
import * as yup from 'yup';
import { useAuthStore } from '@/stores/auth';
import {
  ShieldCheckIcon,
  RefreshIcon,
  CopyIcon,
  EyeIcon,
  EyeOffIcon,
  TrashIcon,
  KeyIcon,
  CheckIcon,
} from 'vue-tabler-icons';

const auth = useAuthStore();

/* Change Password */
const pwdLoading = ref(false);
const pwdSuccess = ref(false);
const pwdError = ref<string | null>(null);

const pwdSchema = yup.object({
  old_password: yup.string().required('Current password is required'),
  new_password: yup
    .string()
    .required('New password is required')
    .min(8, 'Min length is 8')
    .matches(/[A-Z]/, 'Must include an uppercase letter')
    .matches(/[a-z]/, 'Must include a lowercase letter')
    .matches(/\d/, 'Must include a digit')
    .matches(/[^A-Za-z0-9]/, 'Must include a symbol'),
  new_password2: yup
    .string()
    .oneOf([yup.ref('new_password')], 'Passwords must match')
    .required('Please confirm the new password'),
});

async function submitPassword(values: any) {
  pwdLoading.value = true;
  pwdError.value = null;
  pwdSuccess.value = false;
  try {
    await auth.changePassword({
      old_password: values.old_password,
      new_password: values.new_password,
      new_password2: values.new_password2,
    });
    pwdSuccess.value = true;
  } catch (e: any) {
    pwdError.value = typeof e === 'string' ? e : e?.detail || e?.message || 'Password change failed';
  } finally {
    pwdLoading.value = false;
  }
}

/* 2FA (TOTP) */
const twoFA = ref<{ is_enabled: boolean; has_recovery: boolean } | null>(null);
const twofaLoading = ref(false);
const twofaError = ref<string | null>(null);
const twofaSuccess = ref<string | null>(null);

const setupInProgress = ref(false);
const otpauthUri = ref<string | null>(null);
const tempSecret = ref<string | null>(null);
const confirmCode = ref<string>('');
const confirmLoading = ref(false);

const disableLoading = ref(false);
const disablePassword = ref('');
const disableCode = ref('');

const backupCodes = ref<string[] | null>(null);
const showBackupCodes = ref(false);

const qrSrc = computed(() => {
  if (!otpauthUri.value) return null;
  const encoded = encodeURIComponent(otpauthUri.value);
  return `https://api.qrserver.com/v1/create-qr-code/?size=220x220&data=${encoded}`;
});

function copyText(txt: string) {
  navigator.clipboard?.writeText(txt).catch(() => {});
}
function copyAllCodes() {
  if (!backupCodes.value?.length) return;
  copyText(backupCodes.value.join('\n'));
}

async function loadTwoFAStatus() {
  twofaLoading.value = true;
  twofaError.value = null;
  twofaSuccess.value = null;
  try {
    const s = await auth.twoFAStatus();
    twoFA.value = s;
  } catch (e: any) {
    twofaError.value = typeof e === 'string' ? e : e?.detail || e?.message || 'Failed to load 2FA status';
  } finally {
    twofaLoading.value = false;
  }
}

async function startSetup() {
  twofaError.value = null;
  twofaSuccess.value = null;
  try {
    const res = await auth.twoFASetupStart();
    otpauthUri.value = res?.otpauth_uri || null;
    tempSecret.value = res?.secret || null;
    setupInProgress.value = true;
  } catch (e: any) {
    twofaError.value = typeof e === 'string' ? e : e?.detail || e?.message || 'Failed to start 2FA setup';
  }
}

async function confirmSetup() {
  if (!confirmCode.value) return;
  confirmLoading.value = true;
  twofaError.value = null;
  twofaSuccess.value = null;
  try {
    const res = await auth.twoFASetupConfirm(confirmCode.value);
    backupCodes.value = Array.isArray(res?.backup_codes) ? res.backup_codes : null;
    showBackupCodes.value = false;
    twofaSuccess.value = 'Two-factor authentication enabled successfully.';
    setupInProgress.value = false;
    confirmCode.value = '';
    await loadTwoFAStatus();
  } catch (e: any) {
    twofaError.value = typeof e === 'string' ? e : e?.detail || e?.message || 'Invalid TOTP code';
  } finally {
    confirmLoading.value = false;
  }
}

async function disableTwoFA() {
  if (!disablePassword.value || !disableCode.value) {
    twofaError.value = 'Password and 6-digit code are required.';
    return;
  }
  disableLoading.value = true;
  twofaError.value = null;
  twofaSuccess.value = null;
  try {
    await auth.twoFADisable({
      password: disablePassword.value,
      code: disableCode.value,
    });
    twofaSuccess.value = 'Two-factor authentication disabled.';
    disablePassword.value = '';
    disableCode.value = '';
    backupCodes.value = null;
    await loadTwoFAStatus();
  } catch (e: any) {
    twofaError.value = typeof e === 'string' ? e : e?.detail || e?.message || 'Failed to disable 2FA';
  } finally {
    disableLoading.value = false;
  }
}

/* Regenerate backup codes (dialog-local errors) */
const regenDialog = ref(false);
const regenPassword = ref('');
const regenCode = ref('');
const regenLoading = ref(false);
const regenError = ref<string | null>(null);
const canRegen = computed(() => !!regenPassword.value && /^\d{6}$/.test(regenCode.value));

function openRegenDialog() {
  regenDialog.value = true;
  regenPassword.value = '';
  regenCode.value = '';
  regenError.value = null;
}

async function doRegenerate() {
  if (!canRegen.value) {
    regenError.value = 'Enter your password and a valid 6-digit code.';
    return;
  }
  regenLoading.value = true;
  regenError.value = null;
  try {
    const res = await auth.regen2FABackupCodes({
      password: regenPassword.value,
      code: regenCode.value,
    });
    backupCodes.value = Array.isArray(res?.backup_codes) ? res.backup_codes : null;
    showBackupCodes.value = false;
    twofaSuccess.value = 'Backup codes regenerated.';
    regenDialog.value = false;
  } catch (e: any) {
    regenError.value = typeof e === 'string' ? e : e?.message || 'Failed to regenerate backup codes';
  } finally {
    regenLoading.value = false;
  }
}

onMounted(async () => {
  await loadTwoFAStatus();
});
</script>

<template>
  <v-card elevation="10">
    <v-row class="ma-sm-n2 ma-n1">
      <v-col cols="12" md="7">
        <v-card elevation="10">
          <v-card-item>
            <div class="d-flex align-center">
              <ShieldCheckIcon class="mr-2" />
              <h4 class="text-h4">Two-factor Authentication</h4>
            </div>

            <v-alert v-if="twofaError" class="mt-4" type="error" variant="tonal">{{ twofaError }}</v-alert>
            <v-alert v-if="twofaSuccess" class="mt-4" type="success" variant="tonal">{{ twofaSuccess }}</v-alert>

            <div class="d-flex align-center justify-space-between mt-6 mb-4">
              <div class="text-subtitle-1 text-grey100">
                Add a one-time code from an authenticator app to sign in.
              </div>
              <div>
                <v-btn
                  v-if="!twoFA?.is_enabled"
                  color="primary"
                  :loading="twofaLoading"
                  @click="startSetup"
                  rounded="pill"
                >
                  Enable
                </v-btn>
                <v-chip v-else color="success" variant="tonal">Enabled</v-chip>
              </div>
            </div>

            <v-divider />

            <div v-if="setupInProgress" class="mt-6">
              <div class="d-flex flex-column flex-sm-row ga-6">
                <div v-if="qrSrc" class="pa-3 mx-auto mx-sm-0">
                  <v-sheet rounded="lg" class="pa-3">
                    <img :src="qrSrc" alt="TOTP QR" width="220" height="220" />
                  </v-sheet>
                </div>
                <div class="flex-grow-1">
                  <v-row>
                    <v-col cols="12">
                      <div class="d-flex align-center justify-space-between">
                        <div class="text-subtitle-1">Authenticator secret</div>
                        <v-btn variant="text" density="comfortable" @click="tempSecret && copyText(tempSecret)">
                          <CopyIcon size="18" class="mr-1" /> Copy
                        </v-btn>
                      </div>
                      <v-sheet class="pa-3 mt-2" color="surface-variant" rounded="lg">
                        <code v-if="tempSecret">{{ tempSecret }}</code>
                        <span v-else>—</span>
                      </v-sheet>
                    </v-col>
                    <v-col cols="12" md="6">
                      <v-text-field
                        label="6-digit code"
                        v-model="confirmCode"
                        variant="outlined"
                        placeholder="123456"
                        maxlength="6"
                        inputmode="numeric"
                      />
                    </v-col>
                    <v-col cols="12" md="6" class="d-flex align-end ga-3">
                      <v-btn color="primary" :loading="confirmLoading" @click="confirmSetup" rounded="pill">
                        Confirm
                      </v-btn>
                      <v-btn variant="text" @click="setupInProgress=false" rounded="pill">Cancel</v-btn>
                    </v-col>
                  </v-row>
                </div>
              </div>
            </div>

            <div v-if="twoFA?.is_enabled && !setupInProgress" class="mt-6">
              <div class="d-flex align-center justify-space-between mb-2">
                <h6 class="text-h6">Backup codes</h6>
                <div class="d-flex ga-2">
                  <v-btn variant="tonal" color="primary" @click="openRegenDialog" rounded="pill">
                    <RefreshIcon size="18" class="mr-1" /> Regenerate
                  </v-btn>
                  <v-btn
                    variant="text"
                    :disabled="!backupCodes?.length"
                    @click="showBackupCodes = !showBackupCodes"
                    rounded="pill"
                  >
                    <component :is="showBackupCodes ? EyeOffIcon : EyeIcon" size="18" class="mr-1" />
                    {{ showBackupCodes ? 'Hide' : 'Reveal' }}
                  </v-btn>
                  <v-btn
                    variant="text"
                    :disabled="!backupCodes?.length"
                    @click="copyAllCodes"
                    rounded="pill"
                  >
                    <CopyIcon size="18" class="mr-1" /> Copy All
                  </v-btn>
                </div>
              </div>
<v-sheet class="pa-3" color="surface-variant" rounded="lg">
  <div v-if="backupCodes?.length" class="d-flex flex-wrap ga-3">
    <v-chip
      v-for="code in backupCodes"
      :key="code"
      class="mb-1"
      size="large"
      variant="flat"
    >
      {{ showBackupCodes ? code : '••••••••' }}
    </v-chip>
  </div>
  <div v-else class="text-body-2 text-grey100">
    Backup codes will be shown here after enabling 2FA or regenerating.
  </div>
</v-sheet>


              <v-divider class="my-6" />

              <h6 class="text-h6 mb-2">Disable 2FA</h6>
              <div class="text-body-2 mb-4">
                Enter your account password and a current 6-digit code to disable.
              </div>
              <v-row>
                <v-col cols="12" md="6">
                  <v-text-field
                    label="Password"
                    v-model="disablePassword"
                    type="password"
                    variant="outlined"
                    prepend-inner-icon="mdi-lock-outline"
                  />
                </v-col>
                <v-col cols="12" md="6">
                  <v-text-field
                    label="6-digit code"
                    v-model="disableCode"
                    variant="outlined"
                    maxlength="6"
                    inputmode="numeric"
                    prepend-inner-icon="mdi-shield-key-outline"
                  />
                </v-col>
              </v-row>
              <v-btn color="error" :loading="disableLoading" @click="disableTwoFA" rounded="pill">
                <TrashIcon size="18" class="mr-1" /> Disable
              </v-btn>
            </div>
          </v-card-item>
        </v-card>
      </v-col>

      <v-col cols="12" md="5">
        <v-card elevation="10">
          <v-card-item>
            <div class="d-flex align-center">
              <KeyIcon class="mr-2" />
              <h4 class="text-h4">Change Password</h4>
            </div>

            <v-alert v-if="pwdError" type="error" class="mt-4" variant="tonal">{{ pwdError }}</v-alert>
            <v-alert v-if="pwdSuccess" type="success" class="mt-4" variant="tonal">Password changed successfully.</v-alert>

            <Form as="form" class="mt-6" :validation-schema="pwdSchema" @submit="submitPassword">
              <Field name="old_password" v-slot="{ field, errors, handleChange, handleBlur }">
                <v-text-field
                  :model-value="field.value ?? ''"
                  @update:modelValue="val => handleChange(val)"
                  @blur="handleBlur"
                  :error-messages="errors"
                  label="Current password"
                  type="password"
                  variant="outlined"
                  autocomplete="current-password"
                  autocapitalize="off"
                  autocorrect="off"
                  spellcheck="false"
                  class="mb-3"
                  prepend-inner-icon="mdi-lock-outline"
                />
              </Field>

              <Field name="new_password" v-slot="{ field, errors, handleChange, handleBlur }">
                <v-text-field
                  :model-value="field.value ?? ''"
                  @update:modelValue="val => handleChange(val)"
                  @blur="handleBlur"
                  :error-messages="errors"
                  label="New password"
                  type="password"
                  variant="outlined"
                  autocomplete="new-password"
                  autocapitalize="off"
                  autocorrect="off"
                  spellcheck="false"
                  class="mb-3"
                  prepend-inner-icon="mdi-lock-check-outline"
                />
              </Field>

              <Field name="new_password2" v-slot="{ field, errors, handleChange, handleBlur }">
                <v-text-field
                  :model-value="field.value ?? ''"
                  @update:modelValue="val => handleChange(val)"
                  @blur="handleBlur"
                  :error-messages="errors"
                  label="Confirm new password"
                  type="password"
                  variant="outlined"
                  autocomplete="new-password"
                  autocapitalize="off"
                  autocorrect="off"
                  spellcheck="false"
                  class="mb-6"
                  prepend-inner-icon="mdi-lock-check-outline"
                />
              </Field>

              <v-btn color="primary" type="submit" :loading="pwdLoading" rounded="pill">
                <CheckIcon size="18" class="mr-1" /> Update Password
              </v-btn>
            </Form>
          </v-card-item>
        </v-card>
      </v-col>
    </v-row>

    <v-dialog v-model="regenDialog" max-width="520">
      <v-card>
        <v-card-title class="d-flex align-center">
          <RefreshIcon class="mr-2" /> Regenerate Backup Codes
        </v-card-title>
        <v-card-text>
          <div class="text-body-2">
            For security, confirm your password and a current 6-digit code from your authenticator.
          </div>

          <v-alert
            v-if="regenError"
            type="error"
            variant="tonal"
            class="mt-3"
          >
            {{ regenError }}
          </v-alert>

          <v-row class="mt-4">
            <v-col cols="12">
              <v-text-field
                label="Password"
                v-model="regenPassword"
                type="password"
                variant="outlined"
                prepend-inner-icon="mdi-lock-outline"
                @input="regenError=null"
                required
              />
            </v-col>
            <v-col cols="12">
              <v-text-field
                label="6-digit code"
                v-model="regenCode"
                variant="outlined"
                maxlength="6"
                inputmode="numeric"
                prepend-inner-icon="mdi-shield-key-outline"
                @input="regenError=null"
                required
              />
            </v-col>
          </v-row>
        </v-card-text>
        <v-card-actions class="justify-end">
          <v-btn variant="text" @click="regenDialog=false">Cancel</v-btn>
          <v-btn
            color="primary"
            :loading="regenLoading"
            :disabled="!canRegen || regenLoading"
            @click="doRegenerate"
          >
            Regenerate
          </v-btn>
        </v-card-actions>
      </v-card>
    </v-dialog>
  </v-card>
</template>
