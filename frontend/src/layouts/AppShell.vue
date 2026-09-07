<script setup lang="ts">
import { computed, onMounted, ref, watch } from 'vue'
import { RouterView, useRoute } from 'vue-router'
import { usePreferencesStore } from '@/stores/preferences'
import AppHeader from '@/components/layout/AppHeader.vue'
import DesktopSidebar from '@/components/layout/DesktopSidebar.vue'
import MobileBottomNav from '@/components/layout/MobileBottomNav.vue'
import MobileMoreMenu from '@/components/layout/MobileMoreMenu.vue'

const collapsed = ref(localStorage.getItem('rosha-sidebar-collapsed') === 'true')
const moreOpen = ref(false)
const preferences = usePreferencesStore()
const route = useRoute()
const contextualMobileHeader = computed(() => route.meta.mobileHeader === 'contextual')
const toggleSidebar = () => {
  collapsed.value = !collapsed.value
  localStorage.setItem('rosha-sidebar-collapsed', String(collapsed.value))
}

function focusRouteHeading(element: Element): void {
  const heading = element.querySelector<HTMLElement>('h1')
  if (!heading) return
  heading.tabIndex = -1
  heading.focus({ preventScroll: true })
}

onMounted(() => preferences.hydrate())
watch(() => route.fullPath, () => { moreOpen.value = false })
</script>

<template>
  <div class="app-shell" :class="{ 'sidebar-collapsed': collapsed, 'mobile-context-route': contextualMobileHeader }">
    <a class="skip-link" href="#main-content">پرش به محتوای اصلی</a>
    <DesktopSidebar :collapsed="collapsed" @toggle="toggleSidebar" />
    <div class="app-shell__content">
      <AppHeader />
      <main id="main-content">
        <RouterView v-slot="{ Component, route }">
          <Transition name="page" mode="out-in" @after-enter="focusRouteHeading">
            <component :is="Component" :key="route.path" />
          </Transition>
        </RouterView>
      </main>
    </div>
    <MobileBottomNav v-model:more-open="moreOpen" />
    <MobileMoreMenu v-model="moreOpen" />
  </div>
</template>

<style scoped>
.app-shell { min-height: 100dvh; }
.app-shell__content { min-width: 0; margin-inline-start: var(--sidebar-width); transition: margin var(--transition-base); }
.sidebar-collapsed .app-shell__content { margin-inline-start: var(--sidebar-collapsed); }
.page-enter-active, .page-leave-active { transition: opacity var(--transition-fast), transform var(--transition-fast); }
.page-enter-from { opacity: 0; transform: translateY(.3rem); }
.page-leave-to { opacity: 0; }
@media (max-width: 1199px) { .app-shell__content, .sidebar-collapsed .app-shell__content { margin-inline-start: 0; } }
@media (max-width: 1199px) { .mobile-context-route :deep(.app-header) { display: none; } }
</style>
