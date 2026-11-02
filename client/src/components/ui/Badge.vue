<template>
  <span class="badge" :class="`badge-${variant}`">
    <slot />
  </span>
</template>

<script setup>
defineProps({
  variant: {
    type: String,
    default: 'neutral',
    validator: (v) => ['success', 'accent', 'warn', 'danger', 'neutral'].includes(v)
  }
})
</script>

<style scoped>
.badge {
  display: inline-block;
  font-size: 11px;
  font-weight: 600;
  padding: 4px 12px;
  border-radius: 999px;
  line-height: 1.5;
  white-space: nowrap;
}

.badge-success {
  background: rgba(16, 185, 129, 0.12);
  color: var(--success);
}

.badge-accent {
  background: rgba(59, 130, 246, 0.12);
  color: var(--accent);
}

.badge-warn {
  background: rgba(245, 158, 11, 0.12);
  color: var(--warn);
}

.badge-danger {
  background: rgba(239, 68, 68, 0.12);
  color: var(--danger);
}

.badge-neutral {
  background: var(--surface-muted);
  color: var(--ink-muted);
}
</style>
