<!-- src/pages/billing/BillingIndex.vue -->
<script setup lang="ts">
import { ref } from 'vue';
import BaseBreadcrumb from '@/components/shared/BaseBreadcrumb.vue';
import { CurrencyBitcoinIcon, ReceiptIcon, WalletIcon } from 'vue-tabler-icons';
import BillingOverviewTab from '@/components/accounts/billing/BillingOverviewTab.vue';
import BillingMakePaymentTab from '@/components/accounts/billing/BillingMakePaymentTab.vue';
import BillingHistoryTab from '@/components/accounts/billing/BillingHistoryTab.vue';

const tab = ref<'Overview'|'MakePayment'|'History'>('Overview');
const page = ref({ title: 'Billing' });
const breadcrumbs = ref([{ text: 'Home', disabled: false, href: '#' }, { text: 'Billing', disabled: true, href: '#' }]);
</script>

<template>
  <BaseBreadcrumb :title="page.title" :breadcrumbs="breadcrumbs" />
  <v-row class="justify-center">
    <v-col cols="12">
      <v-card elevation="10">
        <v-tabs v-model="tab" bg-color="transparent" height="70" color="primary">
          <v-tab value="Overview"><WalletIcon class="mr-2" size="20" />Overview</v-tab>
          <v-tab value="MakePayment"><CurrencyBitcoinIcon class="mr-2" size="20" />Make a Payment</v-tab>
          <v-tab value="History"><ReceiptIcon class="mr-2" size="20" />History</v-tab>
        </v-tabs>

        <v-divider />

        <v-card-text class="pa-sm-6 pa-3">
          <v-window v-model="tab">
            <v-window-item value="Overview"><BillingOverviewTab /></v-window-item>
            <v-window-item value="MakePayment"><BillingMakePaymentTab /></v-window-item>
            <v-window-item value="History"><BillingHistoryTab /></v-window-item>
          </v-window>
        </v-card-text>
      </v-card>
    </v-col>
  </v-row>
</template>
