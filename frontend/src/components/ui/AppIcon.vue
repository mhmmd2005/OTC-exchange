<script setup lang="ts">
import { computed } from 'vue'

const props = withDefaults(defineProps<{ name: string; size?: number; strokeWidth?: number }>(), {
  size: 22,
  strokeWidth: 1.8,
})

const icons: Record<string, string[]> = {
  dashboard: ['M4 4h6v6H4z', 'M14 4h6v9h-6z', 'M4 14h6v6H4z', 'M14 17h6v3h-6z'],
  trade: ['M7 7h12l-3-3', 'm19 7-3 3', 'M17 17H5l3 3', 'm5 17 3-3'],
  markets: ['M5 19V9', 'M12 19V5', 'M19 19v-7', 'M3 19h18'],
  wallet: ['M4 7.5A2.5 2.5 0 0 1 6.5 5H18a2 2 0 0 1 2 2v12H6a2 2 0 0 1-2-2z', 'M4 9h16', 'M16 14h2'],
  orders: ['M7 3h10v3h3v15H4V6h3z', 'M8 11h8', 'M8 15h5'],
  transactions: ['M4 7h11', 'm12 4 3 3-3 3', 'M20 17H9', 'm12 14-3 3 3 3'],
  profile: ['M12 13a4 4 0 1 0 0-8 4 4 0 0 0 0 8Z', 'M5 21a7 7 0 0 1 14 0'],
  verify: ['M12 3 5 6v5c0 5 3 8 7 10 4-2 7-5 7-10V6z', 'm9 12 2 2 4-5'],
  bank: ['m3 9 9-5 9 5', 'M5 10v8', 'M9 10v8', 'M15 10v8', 'M19 10v8', 'M3 20h18'],
  shield: ['M12 3 5 2v6c0 4-2 7-5 9-3-2-5-5-5-9V5z', 'M12 8v4', 'M12 16h.01'],
  bell: ['M18 9a6 6 0 0 0-12 0c0 7-3 7-3 8h18c0-1-3-1-3-8', 'M10 21h4'],
  help: ['M12 22a10 10 0 1 0 0-20 10 10 0 0 0 0 20Z', 'M9.5 9a2.6 2.6 0 1 1 4 2.2c-1 .7-1.5 1.1-1.5 2.3', 'M12 17h.01'],
  settings: ['M12 15.5a3.5 3.5 0 1 0 0-7 3.5 3.5 0 0 0 0 7Z', 'M19.4 15a1.7 1.7 0 0 0 .3 1.9l.1.1-2 3.4-.2-.1a1.7 1.7 0 0 0-2-.2l-.8.5a1.7 1.7 0 0 0-.8 1.5v.2h-4v-.2a1.7 1.7 0 0 0-.8-1.5l-.8-.5a1.7 1.7 0 0 0-2 .2l-.2.1-2-3.4.1-.1a1.7 1.7 0 0 0 .3-1.9l-.4-.9A1.7 1.7 0 0 0 2.7 13h-.2V9h.2a1.7 1.7 0 0 0 1.5-1.1l.4-.9a1.7 1.7 0 0 0-.3-1.9L4.2 5l2-3.4.2.1a1.7 1.7 0 0 0 2 .2l.8-.5A1.7 1.7 0 0 0 10 0h4a1.7 1.7 0 0 0 .8 1.4l.8.5a1.7 1.7 0 0 0 2-.2l.2-.1 2 3.4-.1.1a1.7 1.7 0 0 0-.3 1.9l.4.9A1.7 1.7 0 0 0 21.3 9h.2v4h-.2a1.7 1.7 0 0 0-1.5 1.1z'],
  home: ['m3 11 9-8 9 8', 'M5 10v11h14V10', 'M9 21v-7h6v7'],
  more: ['M5 12h.01', 'M12 12h.01', 'M19 12h.01'],
  menu: ['M4 6h16', 'M4 12h16', 'M4 18h16'],
  search: ['M11 19a8 8 0 1 0 0-16 8 8 0 0 0 0 16Z', 'm21 21-4.4-4.4'],
  eye: ['M2 12s3.5-6 10-6 10 6 10 6-3.5 6-10 6S2 12 2 12Z', 'M12 15a3 3 0 1 0 0-6 3 3 0 0 0 0 6Z'],
  'eye-off': ['m3 3 18 18', 'M10.6 6.2c.5-.1.9-.2 1.4-.2 6.5 0 10 6 10 6a15 15 0 0 1-2.1 2.8', 'M6.2 6.2A14 14 0 0 0 2 12s3.5 6 10 6c1.3 0 2.5-.2 3.5-.6', 'M10.6 10.6a2 2 0 0 0 2.8 2.8'],
  chevron: ['m9 18 6-6-6-6'],
  chevronRight: ['m9 18 6-6-6-6'],
  chevronLeft: ['m15 18-6-6 6-6'],
  chevronDown: ['m6 9 6 6 6-6'],
  chevronUp: ['m6 15 6-6 6 6'],
  down: ['m6 9 6 6 6-6'],
  plus: ['M12 5v14', 'M5 12h14'],
  minus: ['M5 12h14'],
  close: ['M6 6l12 12', 'M18 6 6 18'],
  check: ['m5 12 4 4L19 6'],
  copy: ['M8 8h11v12H8z', 'M16 8V4H4v12h4'],
  upload: ['M12 16V4', 'm7 9 5-5 5 5', 'M5 20h14'],
  download: ['M12 4v12', 'm7 11 5 5 5-5', 'M5 20h14'],
  arrowUp: ['M12 19V5', 'm7 10 5-5 5 5'],
  arrowDown: ['M12 5v14', 'm7 14 5 5 5-5'],
  arrowLeft: ['M19 12H5', 'm12 5-7 7 7 7'],
  swapVertical: ['M7 5v14', 'm3 15 4 4 4-4', 'M17 19V5', 'm13 9 4-4 4 4'],
  refresh: ['M20 7v5h-5', 'M4 17v-5h5', 'M6.1 8A7 7 0 0 1 18.5 7L20 12', 'M4 12l1.5 5A7 7 0 0 0 18 16'],
  filter: ['M4 5h16l-6 7v6l-4 2v-8z'],
  star: ['m12 3 2.8 5.7 6.2.9-4.5 4.4 1.1 6.2L12 18l-5.6 3 1.1-6.2L3 9.6l6.2-.9z'],
  info: ['M12 22a10 10 0 1 0 0-20 10 10 0 0 0 0 20Z', 'M12 11v6', 'M12 7h.01'],
  warning: ['m12 3 10 18H2z', 'M12 9v5', 'M12 18h.01'],
  lock: ['M6 10h12v11H6z', 'M8 10V7a4 4 0 0 1 8 0v3'],
  phone: ['M7 3h10v18H7z', 'M11 18h2'],
  mail: ['M3 5h18v14H3z', 'm3 7 9 6 9-6'],
  clock: ['M12 22a10 10 0 1 0 0-20 10 10 0 0 0 0 20Z', 'M12 6v6l4 2'],
  calendar: ['M4 5h16v16H4z', 'M8 3v4', 'M16 3v4', 'M4 10h16'],
  logout: ['M10 5H5v14h5', 'M14 8l4 4-4 4', 'M9 12h9'],
  login: ['M14 5h5v14h-5', 'm10 8-4 4 4 4', 'M6 12h12'],
  qr: ['M4 4h6v6H4z', 'M14 4h6v6h-6z', 'M4 14h6v6H4z', 'M15 14h2v2h-2z', 'M19 14h1v3h-3v3h-3v-2', 'M19 19h1v1h-1z'],
  edit: ['M4 20h4L20 8l-4-4L4 16z', 'm14 6 4 4'],
  trash: ['M5 7h14', 'M9 7V4h6v3', 'M7 7l1 14h8l1-14', 'M10 11v6', 'M14 11v6'],
  sparkle: ['M12 3l1.2 3.8L17 8l-3.8 1.2L12 13l-1.2-3.8L7 8l3.8-1.2z', 'M18 14l.8 2.2L21 17l-2.2.8L18 20l-.8-2.2L15 17l2.2-.8z'],
  sun: ['M12 4V2', 'M12 22v-2', 'm4.93 4.93-1.42-1.42', 'm20.49 20.49-1.42-1.42', 'M4 12H2', 'M22 12h-2', 'm4.93 19.07-1.42 1.42', 'm20.49 3.51-1.42 1.42', 'M12 17a5 5 0 1 0 0-10 5 5 0 0 0 0 10Z'],
  moon: ['M21 12.8A9 9 0 1 1 11.2 3a7 7 0 0 0 9.8 9.8Z'],
}

const paths = computed(() => icons[props.name] ?? icons.info)
</script>

<template>
  <svg
    :width="size"
    :height="size"
    viewBox="0 0 24 24"
    fill="none"
    stroke="currentColor"
    :stroke-width="strokeWidth"
    stroke-linecap="round"
    stroke-linejoin="round"
    aria-hidden="true"
    focusable="false"
  >
    <path v-for="path in paths" :key="path" :d="path" />
  </svg>
</template>
