<script setup>
import StatusBadge from './StatusBadge.vue'
defineProps({ items: { type: Array, default: () => [] } })
</script>

<template>
  <div class="table-wrap">
    <table class="data-table">
      <thead>
        <tr>
          <th>شناسه سفارش</th>
          <th>نوع</th>
          <th>ارز</th>
          <th>مقدار</th>
          <th>قیمت</th>
          <th>مبلغ کل</th>
          <th>وضعیت</th>
          <th>تاریخ</th>
        </tr>
      </thead>
      <tbody>
        <tr v-for="item in items" :key="item.id">
          <td>{{ item.id }}</td>
          <td>{{ item.type }}</td>
          <td>{{ item.asset }}</td>
          <td>{{ item.amount }}</td>
          <td>{{ Number(item.price).toLocaleString('fa-IR') }}</td>
          <td>{{ Number(item.total).toLocaleString('fa-IR') }}</td>
          <td><StatusBadge :status="item.status" /></td>
          <td>{{ item.time }}</td>
        </tr>
      </tbody>
    </table>
  </div>
</template>
