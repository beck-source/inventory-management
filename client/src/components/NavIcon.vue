<template>
  <svg width="20" height="20" viewBox="0 0 20 20" fill="none">
    <template v-if="name === 'overview'">
      <rect x="2.5" y="2.5" width="6" height="6" rx="1" stroke="currentColor" stroke-width="1.5"/>
      <rect x="11.5" y="2.5" width="6" height="6" rx="1" stroke="currentColor" stroke-width="1.5"/>
      <rect x="2.5" y="11.5" width="6" height="6" rx="1" stroke="currentColor" stroke-width="1.5"/>
      <rect x="11.5" y="11.5" width="6" height="6" rx="1" stroke="currentColor" stroke-width="1.5"/>
    </template>

    <template v-else-if="name === 'inventory'">
      <path d="M3 6.5L10 3L17 6.5V13.5L10 17L3 13.5V6.5Z" stroke="currentColor" stroke-width="1.5" stroke-linejoin="round"/>
      <path d="M3 6.5L10 10L17 6.5" stroke="currentColor" stroke-width="1.5" stroke-linejoin="round"/>
      <path d="M10 10V17" stroke="currentColor" stroke-width="1.5"/>
    </template>

    <template v-else-if="name === 'orders'">
      <rect x="4" y="3" width="12" height="14.5" rx="1.5" stroke="currentColor" stroke-width="1.5"/>
      <path d="M7.5 3V2.5C7.5 2 7.9 1.5 8.5 1.5H11.5C12.1 1.5 12.5 2 12.5 2.5V3" stroke="currentColor" stroke-width="1.5"/>
      <path d="M7 9H13M7 12H13M7 15H10.5" stroke="currentColor" stroke-width="1.5" stroke-linecap="round"/>
    </template>

    <template v-else-if="name === 'finance'">
      <circle cx="10" cy="10" r="7.5" stroke="currentColor" stroke-width="1.5"/>
      <path d="M10 5.5V14.5" stroke="currentColor" stroke-width="1.5" stroke-linecap="round"/>
      <path d="M12.5 7.5C12.5 6.5 11.4 6 10 6C8.6 6 7.5 6.7 7.5 7.7C7.5 8.7 8.4 9.1 10 9.5C11.7 9.9 12.5 10.3 12.5 11.3C12.5 12.3 11.4 13 10 13C8.6 13 7.5 12.5 7.5 11.5" stroke="currentColor" stroke-width="1.5" stroke-linecap="round"/>
    </template>

    <template v-else-if="name === 'demand'">
      <path d="M3 14.5L8 9.5L11 12.5L17 6" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"/>
      <path d="M13 6H17V10" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"/>
    </template>

    <template v-else-if="name === 'reports'">
      <rect x="4" y="2" width="12" height="16" rx="1.5" stroke="currentColor" stroke-width="1.5"/>
      <path d="M7 11.5V14.5M10 8.5V14.5M13 10V14.5" stroke="currentColor" stroke-width="1.5" stroke-linecap="round"/>
    </template>

    <circle v-else cx="10" cy="10" r="3" fill="currentColor"/>
  </svg>
</template>

<script setup>
defineProps({
  name: {
    type: String,
    default: null
  }
})
</script>
