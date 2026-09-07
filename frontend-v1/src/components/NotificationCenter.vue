<script setup>
import { computed, ref } from 'vue'
import { useNotificationsStore } from '../stores/notifications'

const notifications = useNotificationsStore()
const open = ref(false)
const unreadCount = computed(() => notifications.list.filter((item) => item.status === 'unread').length)
</script>

<template>
  <div class="notification-wrapper">
    <button class="icon-btn" @click="open = !open" aria-label="اعلان‌ها">
      🔔
      <span v-if="unreadCount" class="notification-count">{{ unreadCount }}</span>
    </button>

    <div v-if="open" class="notification-panel">
      <div class="notification-header">
        <strong>اعلان‌ها</strong>
        <span class="muted-small">{{ unreadCount }} جدید</span>
      </div>
      <div v-if="notifications.list.length" class="notification-list">
        <div v-for="item in notifications.list.slice(0, 5)" :key="item.id" class="notification-item">
          <div class="notification-dot" :class="item.status" />
          <div class="notification-copy">
            <div class="notification-title">{{ item.title }}</div>
            <div class="notification-message">{{ item.message }}</div>
            <div class="notification-time">{{ item.time }}</div>
          </div>
        </div>
      </div>
      <div v-else class="empty-state compact">
        <p>اعلان جدیدی وجود ندارد.</p>
      </div>
    </div>
  </div>
</template>
