<script setup>
defineProps({ title: { type: String, default: 'داده‌ای وجود ندارد' }, message: { type: String, default: 'برای شروع، داده‌های جدید را اضافه کنید.' } })
</script>

<template>
  <div class="empty-state">
    <h3>{{ title }}</h3>
    <p>{{ message }}</p>
  </div>
</template>
