<script setup>
// Native <select> (keeps keyboard/a11y behavior) with a custom chevron.
// Single root element, so class/id/aria-*/disabled etc. fall through to the <select>.
defineProps({
  // 'md' = compact filter control, 'lg' = form field (used in modals)
  size: { type: String, default: 'md', validator: (v) => ['md', 'lg'].includes(v) },
})

const model = defineModel()
</script>

<template>
  <select v-model="model" class="base-select" :class="`base-select--${size}`">
    <slot />
  </select>
</template>

<style scoped>
.base-select {
  /* Drop the native arrow: browsers pin it ~4px from the border, which looks cramped */
  appearance: none;
  -webkit-appearance: none;
  -moz-appearance: none;
  /* Chevron is drawn as a background so it can sit 0.75rem from the right border */
  background-color: var(--surface);
  background-image: url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 16 16' fill='none' stroke='%2364748b' stroke-width='1.5' stroke-linecap='round' stroke-linejoin='round'%3E%3Cpath d='M4 6l4 4 4-4'/%3E%3C/svg%3E");
  background-repeat: no-repeat;
  background-position: right 0.75rem center;
  background-size: 1rem 1rem;
  /* Right padding reserves room for the chevron (0.75rem offset + 1rem icon + gap) so text never overlaps it */
  padding-right: 2.25rem;
  color: var(--text);
  cursor: pointer;
  font-family: inherit;
}

/* Legacy Edge/IE native arrow */
.base-select::-ms-expand {
  display: none;
}

.base-select:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.base-select--md {
  height: var(--control-height);
  padding-left: var(--space-3);
  border: 1px solid var(--border-strong);
  border-radius: var(--radius-md);
  font-size: var(--text-sm);
  font-weight: 500;
  transition: border-color var(--duration) var(--ease);
}
.base-select--md:hover:not(:disabled) {
  border-color: var(--text-subtle);
}
.base-select--md:focus-visible {
  outline: none;
  border-color: var(--accent);
  box-shadow: var(--focus-ring);
}

.base-select--lg {
  padding-top: var(--space-3);
  padding-bottom: var(--space-3);
  padding-left: var(--space-3);
  border: 2px solid var(--border);
  border-radius: var(--radius-lg);
  font-size: var(--text-md);
  transition: border-color var(--duration) var(--ease);
}
.base-select--lg:focus {
  outline: none;
  border-color: var(--accent);
}
</style>
