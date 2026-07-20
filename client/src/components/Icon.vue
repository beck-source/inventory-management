<script setup>
// Small inline-SVG icon set for the sidebar/header. Maps a `name` prop to a
// path so nav items and header actions don't need hand-drawn SVGs per use.
// Add new entries to ICONS as needed, matching the existing style: 24x24
// viewBox, stroke-based, currentColor, ~1.8 stroke width, rounded caps/joins.

const props = defineProps({
  name: { type: String, required: true },
  size: { type: [Number, String], default: 20 },
})

const ICONS = {
  home: 'M3 11.5 12 4l9 7.5M5 10v9a1 1 0 0 0 1 1h4v-6h4v6h4a1 1 0 0 0 1-1v-9',
  box: 'M3 8 12 4l9 4-9 4-9-4Zm0 0v8l9 4 9-4V8M12 12v8',
  cart: 'M4 4h2l1.5 10.5A2 2 0 0 0 9.5 16h7a2 2 0 0 0 2-1.7L20 7H6M9 20a1 1 0 1 0 0-2 1 1 0 0 0 0 2Zm8 0a1 1 0 1 0 0-2 1 1 0 0 0 0 2Z',
  chart: 'M4 20V10m6 10V4m6 16v-7m6 7V8',
  dollar: 'M12 3v18M8 7.5c0-1.4 1.6-2.5 4-2.5s4 1.1 4 2.5-1.6 2.3-4 2.9-4 1.6-4 3S9.6 15 12 15s4-1 4-2.5',
  users: 'M9 12a3.5 3.5 0 1 0 0-7 3.5 3.5 0 0 0 0 7Zm-6 8c0-3 2.7-5.5 6-5.5s6 2.5 6 5.5M17 8.2a3 3 0 1 1 0 5.8M20 20c0-2.6-2-4.7-4.6-5.3',
  trending: 'M4 16l5-5 4 4 7-8M14 7h6v6',
  list: 'M8 6h13M8 12h13M8 18h13M3 6h.01M3 12h.01M3 18h.01',
  layers: 'M12 3 3 8l9 5 9-5-9-5ZM3 13l9 5 9-5M3 18l9 5 9-5',
  settings: 'M12 15a3 3 0 1 0 0-6 3 3 0 0 0 0 6Zm7.4-3a7.4 7.4 0 0 0-.1-1.2l2-1.6-2-3.4-2.4 1a7.5 7.5 0 0 0-2-1.2L14.5 3h-4l-.4 2.6a7.5 7.5 0 0 0-2 1.2l-2.4-1-2 3.4 2 1.6a7.4 7.4 0 0 0 0 2.4l-2 1.6 2 3.4 2.4-1c.6.5 1.3.9 2 1.2l.4 2.6h4l.4-2.6c.7-.3 1.4-.7 2-1.2l2.4 1 2-3.4-2-1.6c.1-.4.1-.8.1-1.2Z',
  bell: 'M6 8a6 6 0 1 1 12 0c0 4 1.5 5.5 1.5 5.5H4.5S6 12 6 8ZM9.5 17a2.5 2.5 0 0 0 5 0',
  search: 'M11 19a8 8 0 1 0 0-16 8 8 0 0 0 0 16Zm9 2-4.3-4.3',
  menu: 'M4 6h16M4 12h16M4 18h16',
  'chevron-left': 'M15 5 8 12l7 7',
  'chevron-right': 'M9 5l7 7-7 7',
  logout: 'M9 21H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h4M16 17l5-5-5-5M21 12H9',
  help: 'M12 21a9 9 0 1 0 0-18 9 9 0 0 0 0 18Zm0-5.5v-.5c0-1.2 2-1.6 2-3.5a2 2 0 1 0-4 0M12 17h.01',
  folder: 'M3 7a2 2 0 0 1 2-2h4l2 2h8a2 2 0 0 1 2 2v9a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V7Z',
  grid: 'M4 4h7v7H4Zm9 0h7v7h-7Zm0 9h7v7h-7ZM4 13h7v7H4Z',
  circle: 'M12 21a9 9 0 1 0 0-18 9 9 0 0 0 0 18Z',
}
</script>

<template>
  <svg
    :width="size"
    :height="size"
    viewBox="0 0 24 24"
    fill="none"
    :stroke="'currentColor'"
    stroke-width="1.8"
    stroke-linecap="round"
    stroke-linejoin="round"
    aria-hidden="true"
  >
    <path :d="ICONS[name] || ICONS.circle" />
  </svg>
</template>
