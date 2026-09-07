<script setup lang="ts">
import TextBannerCard from '@/components/frontpages/Shared/TextBannerCard.vue';
import DefaultLayout from '@/views/pages/front-pages/Layout.vue';
import Details from '@/components/frontpages/Blog/details/BlogDetails.vue';
import PurchaseTemplate from '@/components/frontpages/Homepage/PurchaseTemplate.vue';
</script>

<template>
     <DefaultLayout>
      <TextBannerCard title="Our most recent articles" caption="Blog Details" />
      <Details />
      <PurchaseTemplate />
     </DefaultLayout>
</template>
