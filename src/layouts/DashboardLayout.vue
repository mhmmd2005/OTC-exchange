<script setup>
import { ref } from 'vue'
import AppSidebar from '../components/AppSidebar.vue'
import AppHeader from '../components/AppHeader.vue'

const sidebarOpen = ref(false)
const sidebarCollapsed = ref(false)
</script>

<template>
  <div class="layout-shell">
    <AppSidebar
      :open="sidebarOpen"
      :collapsed="sidebarCollapsed"
      @close="sidebarOpen = false"
      @toggle-collapse="sidebarCollapsed = !sidebarCollapsed"
    />
    <div class="main-panel">
      <AppHeader
        @toggle-sidebar="sidebarOpen = !sidebarOpen"
        @toggle-collapse="sidebarCollapsed = !sidebarCollapsed"
      />
      <main class="page-content">
        <RouterView />
      </main>
    </div>
  </div>
</template>
