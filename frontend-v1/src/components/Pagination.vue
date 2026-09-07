<script setup>
const props = defineProps({ page: { type: Number, default: 1 }, total: { type: Number, default: 3 } })
const pages = Array.from({ length: props.total }, (_, index) => index + 1)
</script>

<template>
  <div class="pagination">
    <button class="page-btn" v-for="item in pages" :key="item" :class="{ active: item === page }">{{ item }}</button>
  </div>
</template>
