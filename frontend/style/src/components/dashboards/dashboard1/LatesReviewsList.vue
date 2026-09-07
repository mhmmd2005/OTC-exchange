<script setup lang="ts">
import { ref, computed, onMounted } from 'vue';
import { useEcomStore } from '@/stores/apps/eCommerce';
import type { Header, Item } from 'vue3-easy-data-table';
import 'vue3-easy-data-table/dist/style.css';
import { format } from 'date-fns';

const store = useEcomStore();
onMounted(() => {
    store.fetchProducts();
});

const getProducts = computed(() => {
    return store.products;
});

const searchField = ref('name');
const searchValue = ref('');

const headers: Header[] = [
    { text: 'Product', value: 'image' },
    { text: 'Title', value: 'name', sortable: true },
    { text: 'Created', value: 'created', sortable: true },
    { text: 'Price', value: 'offerPrice', sortable: true },
    { text: 'Sale-Price', value: 'salePrice', sortable: true },
    { text: 'Status', value: 'isStock' },
    { text: 'Action', value: 'operation' }
];
const items = ref(getProducts);
const themeColor = ref('rgb(var(--v-theme-primary))');

const itemsSelected = ref<Item[]>([]);
</script>

<template>
    <v-row>
        <v-col cols="12" md="12">
            <VCard elevation="10">
                <v-card-text>
                    <div class="d-sm-flex d-block justify-space-between d-block align-center mb-4 list-search">
                        <div>
                            <h5 class="text-h5 mb-1 font-weight-semibold">
                                Latest reviews
                            </h5>
                            <div class="text-subtitle-1 text-grey100 pb-1 font-weight-medium">Reviewd received across all
                                channels
                            </div>
                        </div>
                        <div>
                            <v-text-field type="text" variant="outlined" placeholder="Search Product" v-model="searchValue"
                                density="compact" hide-details prepend-inner-icon="mdi-magnify"  style="min-width: 230px;"/>
                        </div>
                    </div>
                    <EasyDataTable :headers="headers" :items="items" table-class-name="customize-table"
                        :theme-color="themeColor" :search-field="searchField" :search-value="searchValue" :rows-per-page="5"
                        v-model:items-selected="itemsSelected">
                        <template #item-image="{ image }">
                            <div class="player-wrapper">
                                <img alt="product" width="60" class="rounded-md" :src="image" />
                            </div>
                        </template>
                        <template #item-name="{ name }">
                            <div class="player-wrapper">
                                <h5 class="text-h6">{{ name }}</h5>
                            </div>
                        </template>
                        <template #item-created="{ date }">
                            <div class="player-wrapper">
                                {{ format(new Date(date), 'E, MMM d') }}
                            </div>
                        </template>
                        <template #item-offerPrice="{ offerPrice }">
                            <div class="player-wrapper">
                                <h5 class="text-h6">${{ offerPrice }}</h5>
                            </div>
                        </template>
                        <template #item-salePrice="{ salePrice }">
                            <div class="player-wrapper">
                                <h5 class="text-h6">${{ salePrice }}</h5>
                            </div>
                        </template>
                        <template #item-isStock="{ isStock }">
                            <div class="player-wrapper">
                                <v-chip color="success" v-if="isStock" size="small"> In Stock </v-chip>
                                <v-chip color="error" v-else size="small"> Out of Stock </v-chip>
                            </div>
                        </template>

                        <template #item-operation="item">
                            <div class="operation-wrapper">
                                <v-btn icon variant="text">
                                    <DotsIcon size="18" />
                                </v-btn>
                            </div>
                        </template>
                    </EasyDataTable>
                </v-card-text>
            </VCard>
        </v-col>
    </v-row>
</template>
