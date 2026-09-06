<script setup>
import { ref, computed } from 'vue'
import { getApiMode, setApiMode, isDevelopment } from '../services/mode'
import { Radio, Server, Zap } from 'lucide-vue-next'

const currentMode = ref(getApiMode())

const isDevMode = computed(() => isDevelopment())

const modes = [
  {
    value: 'real',
    label: 'Real Backend',
    icon: Server,
    description: 'Connect to Django backend',
  },
  {
    value: 'mock',
    label: 'Mock Mode',
    icon: Zap,
    description: 'Use local mock data',
  },
]

function handleModeChange(mode) {
  if (!isDevMode.value) return
  
  currentMode.value = mode
  setApiMode(mode)
  window.location.reload()
}
</script>

<template>
  <div v-if="isDevMode" class="api-mode-switch">
    <div class="mode-label">
      <Radio :size="14" />
      API Mode
    </div>
    <div class="mode-options">
      <button
        v-for="mode in modes"
        :key="mode.value"
        :class="['mode-btn', { active: currentMode === mode.value }]"
        @click="handleModeChange(mode.value)"
        :title="`Switch to ${mode.label}`"
      >
        <component :is="mode.icon" :size="14" />
        <span>{{ mode.label }}</span>
      </button>
    </div>
  </div>
</template>

<style scoped>
.api-mode-switch {
  border-top: 1px solid #e0e0e0;
  padding: 12px 16px;
  margin-top: 12px;
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.mode-label {
  display: flex;
  align-items: center;
  gap: 6px;
  font-size: 0.75rem;
  color: #888;
  text-transform: uppercase;
  letter-spacing: 0.5px;
  font-weight: 600;
}

.mode-options {
  display: flex;
  flex-direction: column;
  gap: 6px;
}

.mode-btn {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 8px 10px;
  border: 1px solid #ddd;
  border-radius: 6px;
  background: #f9f9f9;
  color: #666;
  font-size: 0.875rem;
  cursor: pointer;
  transition: all 0.2s;
}

.mode-btn:hover {
  background: #f0f0f0;
  border-color: #999;
}

.mode-btn.active {
  background: #0284c7;
  border-color: #0284c7;
  color: white;
}

.mode-btn svg {
  flex-shrink: 0;
}
</style>
