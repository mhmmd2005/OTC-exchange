<script setup>
import StatusBadge from './StatusBadge.vue'
defineProps({ items: { type: Array, default: () => [] } })
</script>

<template>
  <div class="table-wrap">
    <table class="data-table">
      <thead>
        <tr>
          <th>نوع تراکنش</th>
          <th>ارز</th>
          <th>مقدار</th>
          <th>وضعیت</th>
          <th>شناسه</th>
          <th>تاریخ</th>
        </tr>
      </thead>
      <tbody>
        <tr v-for="item in items" :key="item.id">
          <td>{{ item.type }}</td>
          <td>{{ item.asset }}</td>
          <td>{{ item.amount }}</td>
          <td><StatusBadge :status="item.status" /></td>
          <td>{{ item.id }}</td>
          <td>{{ item.date }}</td>
        </tr>
      </tbody>
    </table>
  </div>
</template>
