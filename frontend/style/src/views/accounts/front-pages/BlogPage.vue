<script setup lang="ts">
import BlogPagesPosts from '@/components/frontpages/Blog/BlogPagesPosts.vue';
import PurchaseTemplate from '@/components/frontpages/Homepage/PurchaseTemplate.vue';
import TextBannerCard from '@/components/frontpages/Shared/TextBannerCard.vue';
import DefaultLayout from '@/views/pages/front-pages/Layout.vue';
</script>

<template>
    <DefaultLayout>
        <TextBannerCard title="Latest blog & news" caption="Blog Page" />
        <div class="bg-background">
            <BlogPagesPosts />
        </div>
        <PurchaseTemplate />
    </DefaultLayout>
</template>
