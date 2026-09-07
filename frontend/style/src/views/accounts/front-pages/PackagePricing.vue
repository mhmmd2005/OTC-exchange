<script setup lang="ts">
import Packages from '@/components/frontpages/Homepage/Packages.vue';
import PurchaseTemplate from '@/components/frontpages/Homepage/PurchaseTemplate.vue';
import SecurePayment from '@/components/frontpages/Homepage/SecurePayment.vue';
import TextBannerCard from '@/components/frontpages/Shared/TextBannerCard.vue';
import DefaultLayout from '@/views/pages/front-pages/Layout.vue';
</script>

<template>
    <DefaultLayout>
        <TextBannerCard title="Choose Your Plan" caption="Pricing Page" />
        <Packages />
        <div class="sm:pb-14 pb-8">
            <SecurePayment />
        </div>
        <PurchaseTemplate />
    </DefaultLayout>
</template>
