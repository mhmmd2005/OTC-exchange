<!-- src/components/accounts/billing/BillingMakePaymentTab.vue -->
<script setup lang="ts">
import { ref, onMounted, computed } from 'vue'
import { useBillingStore } from '@/stores/billing'
import AmountPicker from './AmountPicker.vue'

type SubTab = 'card' | 'paypal' | 'crypto'
const billing = useBillingStore()
const subTab = ref<SubTab>('crypto')

const baseCurrency = ref('USD')
const amount = ref<number>(15)
const min = 15
const max = 1000

const loading = ref(false)
const errorMsg = ref('')
const successMsg = ref('')
const invoiceUrl = ref('')

const canSubmit = computed(
  () => !loading.value && !!amount.value && amount.value >= min && amount.value <= max
)

async function loadInit() {
  try {
    const o = await billing.getOverview()
    baseCurrency.value = o?.currency || 'USD'
  } catch {}
}

async function createCrypto() {
  errorMsg.value = ''
  successMsg.value = ''
  invoiceUrl.value = ''

  if (!amount.value || amount.value < min || amount.value > max) {
    errorMsg.value = `Amount must be between ${min} and ${max}`
    return
  }

  loading.value = true
  try {
    const resp = await billing.topupCrypto({ amount: String(amount.value) } as any)

    const url = (resp as any)?.payment_url || ''
    invoiceUrl.value = url

    if (url) {
      successMsg.value = 'Redirecting to payment...'
      window.location.href = url
    } else {
      errorMsg.value = 'Failed to create invoice.'
    }
  } catch (e: any) {
    errorMsg.value = typeof e === 'string' ? e : e?.detail || e?.message || e?.error || 'Top-up failed'
  } finally {
    loading.value = false
  }
}

onMounted(loadInit)
</script>

<template>
  <v-card class="rounded-xl">
    <v-card-text class="pt-6">
      <!-- Method tabs -->
      <v-tabs v-model="subTab" class="mb-2" grow>
        <v-tab value="card" :disabled="true">
          <v-icon size="18" icon="mdi-credit-card-outline" class="mr-1" />
          Card
          <v-chip size="x-small" class="ml-2" color="grey" variant="tonal">Soon</v-chip>
        </v-tab>

        <v-tab value="paypal" :disabled="true">
          <v-icon size="18" icon="mdi-paypal" class="mr-1" />
          PayPal
          <v-chip size="x-small" class="ml-2" color="grey" variant="tonal">Soon</v-chip>
        </v-tab>

        <v-tab value="crypto">
          <v-icon size="18" icon="mdi-bitcoin" class="mr-1" />
          Crypto
        </v-tab>
      </v-tabs>

      <v-divider class="mb-4" />

      <v-window v-model="subTab">
        <!-- Card -->
        <v-window-item value="card">
          <v-alert type="info" variant="tonal" class="rounded-lg">
            Card payments will be available soon.
          </v-alert>
        </v-window-item>

        <!-- PayPal -->
        <v-window-item value="paypal">
          <v-alert type="info" variant="tonal" class="rounded-lg">
            PayPal payments will be available soon.
          </v-alert>
        </v-window-item>

        <!-- Crypto -->
        <v-window-item value="crypto">
          <v-row>
            <!-- Left: amount -->
            <v-col cols="12" md="7">
              <v-card variant="outlined" class="rounded-xl pa-4">
                <div class="d-flex align-center mb-3">
                  <v-icon icon="mdi-cash-plus" class="mr-2" />
                  <div class="text-subtitle-1 font-weight-medium">Amount</div>
                  <v-spacer />
                  <v-chip size="small" color="primary" variant="tonal">
                    Base: {{ baseCurrency }}
                  </v-chip>
                </div>

                <AmountPicker
                  v-model="amount"
                  :min="min"
                  :max="max"
                  :currency="baseCurrency"
                />

                <v-alert type="info" class="mt-4 rounded-lg" variant="tonal">
                  You’ll choose the crypto/network on the payment gateway.
                </v-alert>

                <v-alert
                  v-if="errorMsg"
                  type="error"
                  class="mt-4 rounded-lg"
                  variant="tonal"
                >
                  <v-icon icon="mdi-alert-circle" class="mr-2" />
                  {{ errorMsg }}
                </v-alert>

                <v-alert
                  v-if="successMsg"
                  type="success"
                  class="mt-2 rounded-lg"
                  variant="tonal"
                >
                  <v-icon icon="mdi-check-circle" class="mr-2" />
                  {{ successMsg }}
                  <template v-if="invoiceUrl">
                    — <a :href="invoiceUrl" target="_blank" rel="noopener">Open payment page</a>
                  </template>
                </v-alert>
              </v-card>
            </v-col>

            <!-- Right: summary + CTA -->
            <v-col cols="12" md="5">
              <v-card class="rounded-xl pa-4" elevation="2">
                <div class="d-flex align-center mb-3">
                  <v-icon icon="mdi-receipt-text" class="mr-2" />
                  <div class="text-subtitle-1 font-weight-medium">Payment Summary</div>
                </div>

                <v-list density="compact" lines="one">
                  <v-list-item>
                    <template #prepend><v-icon icon="mdi-cash" /></template>
                    <v-list-item-title>Top-up Amount</v-list-item-title>
                    <v-list-item-subtitle>
                      {{ amount?.toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 }) }}
                      {{ baseCurrency }}
                    </v-list-item-subtitle>
                  </v-list-item>

                  <v-list-item>
                    <template #prepend><v-icon icon="mdi-swap-horizontal" /></template>
                    <v-list-item-title>Pay With</v-list-item-title>
                    <v-list-item-subtitle>Choose on gateway</v-list-item-subtitle>
                  </v-list-item>

                  <v-list-item>
                    <template #prepend><v-icon icon="mdi-timer-sand" /></template>
                    <v-list-item-title>Invoice Expiration</v-list-item-title>
                    <v-list-item-subtitle>Expires shortly after creation</v-list-item-subtitle>
                  </v-list-item>
                </v-list>

                <v-divider class="my-3" />

                <v-btn
                  color="primary"
                  size="large"
                  class="rounded-pill"
                  :loading="loading"
                  :disabled="!canSubmit"
                  prepend-icon="mdi-bitcoin"
                  block
                  @click="createCrypto"
                  aria-label="Create crypto invoice"
                >
                  Create Crypto Invoice
                </v-btn>

                <div class="text-caption mt-3 text-medium-emphasis">
                  Your crypto invoice may expire soon after it’s created. If redirect is blocked, use the link above.
                </div>
              </v-card>
            </v-col>
          </v-row>
        </v-window-item>
      </v-window>
    </v-card-text>
  </v-card>
</template>
