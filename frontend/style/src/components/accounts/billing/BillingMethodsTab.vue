<template>
  <v-card>
    <v-card-text>
      <v-tabs v-model="subTab" grow>
        <v-tab value="card" :disabled="true">Card</v-tab>
        <v-tab value="paypal" :disabled="true">PayPal</v-tab>
        <v-tab value="crypto">Crypto</v-tab>
      </v-tabs>

      <v-window v-model="subTab" class="mt-4">
        <v-window-item value="card">
          <v-alert type="info" variant="tonal">Card payments coming soon.</v-alert>
        </v-window-item>

        <v-window-item value="paypal">
          <v-alert type="info" variant="tonal">PayPal payments coming soon.</v-alert>
        </v-window-item>

        <v-window-item value="crypto">
          <v-form @submit.prevent="createCrypto">
            <v-row>
              <v-col cols="12" md="4">
                <v-text-field
                  v-model.number="amount"
                  type="number"
                  label="Amount (USD)"
                  :min="min"
                  :max="max"
                  :step="1"
                  required
                />
              </v-col>
              <v-col cols="12" md="4">
                <v-select
                  v-model="currency"
                  :items="currencies"
                  item-title="label"
                  item-value="code"
                  label="Pay Currency"
                  required
                />
              </v-col>
              <v-col cols="12" md="4" class="d-flex align-center">
                <v-btn type="submit" color="primary" :loading="loading">Create Invoice</v-btn>
              </v-col>
            </v-row>
          </v-form>

          <v-alert v-if="invoiceUrl" type="success" class="mt-4">
            Invoice created. <a :href="invoiceUrl" target="_blank">Open payment page</a>
          </v-alert>
        </v-window-item>
      </v-window>
    </v-card-text>
  </v-card>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue';
import { useAuthStore } from '@/stores/auth';

const store = useAuthStore();
const subTab = ref('crypto');

const currencies = ref<{code:string; label:string}[]>([]);
const amount = ref<number>(50);
const currency = ref<string>('');
const invoiceUrl = ref<string>('');
const loading = ref(false);

const min = 15;
const max = 1000;

async function loadCurrencies() {
  currencies.value = await store.getCryptoCurrencies();
  if (!currency.value && currencies.value.length) currency.value = currencies.value[0].code;
}

async function createCrypto() {
  loading.value = true;
  invoiceUrl.value = '';
  try {
    const idempotency_key = crypto.randomUUID();
    const resp = await store.createFundingCrypto({
      amount: amount.value,
      pay_currency: currency.value,
      idempotency_key,
    });
    invoiceUrl.value = resp.payment_url;
  } catch (e:any) {
    console.error(e);
  } finally {
    loading.value = false;
  }
}

onMounted(loadCurrencies);
</script>
