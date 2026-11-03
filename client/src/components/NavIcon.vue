<template>
  <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor"
       stroke-width="1.75" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">
    <template v-if="name === 'overview'">
      <rect x="3" y="3" width="7" height="9" rx="1.5" /><rect x="14" y="3" width="7" height="5" rx="1.5" />
      <rect x="14" y="12" width="7" height="9" rx="1.5" /><rect x="3" y="16" width="7" height="5" rx="1.5" />
    </template>
    <template v-else-if="name === 'inventory'">
      <path d="M21 8l-9-5-9 5 9 5 9-5z" /><path d="M3 8v8l9 5 9-5V8" /><path d="M12 13v8" />
    </template>
    <template v-else-if="name === 'orders'">
      <path d="M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2" />
      <rect x="9" y="3" width="6" height="4" rx="1" /><path d="M9 12h6M9 16h4" />
    </template>
    <template v-else-if="name === 'finance'">
      <path d="M3 3v18h18" /><path d="M7 15l4-4 3 3 5-6" />
    </template>
    <template v-else-if="name === 'demand'">
      <path d="M3 17l6-6 4 4 8-8" /><path d="M15 7h6v6" />
    </template>
    <template v-else-if="name === 'restocking'">
      <path d="M20 12a8 8 0 01-14 5.3M4 12a8 8 0 0114-5.3" /><path d="M18 3v4h-4M6 21v-4h4" />
    </template>
    <template v-else-if="name === 'reports'">
      <path d="M14 3H7a2 2 0 00-2 2v14a2 2 0 002 2h10a2 2 0 002-2V8l-5-5z" /><path d="M14 3v5h5M9 13h6M9 17h6" />
    </template>
    <template v-else-if="name === 'collapse'">
      <rect x="3" y="4" width="18" height="16" rx="2" /><path d="M9 4v16" /><path d="M15 10l-2 2 2 2" />
    </template>
    <template v-else-if="name === 'menu'">
      <path d="M4 6h16M4 12h16M4 18h16" />
    </template>
  </svg>
</template>

<script setup>
defineProps({ name: { type: String, required: true } })
</script>
