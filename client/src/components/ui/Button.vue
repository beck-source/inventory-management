<template>
  <button
    :type="type"
    class="btn"
    :class="[`btn-${variant}`, `btn-${size}`]"
    :disabled="disabled"
    @click="$emit('click', $event)"
  >
    <slot />
  </button>
</template>

<script setup>
defineProps({
  variant: {
    type: String,
    default: 'primary',
    validator: (v) => ['primary', 'secondary', 'ghost', 'danger'].includes(v)
  },
  size: {
    type: String,
    default: 'md',
    validator: (v) => ['sm', 'md'].includes(v)
  },
  type: {
    type: String,
    default: 'button'
  },
  disabled: {
    type: Boolean,
    default: false
  }
})

defineEmits(['click'])
</script>

<style scoped>
.btn {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  gap: var(--sp-2);
  border-radius: var(--r-sm);
  font-family: inherit;
  font-weight: 500;
  cursor: pointer;
  transition: background 0.15s ease, border-color 0.15s ease, color 0.15s ease;
  white-space: nowrap;
  border: 1px solid transparent;
  line-height: 1;
}

.btn:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.btn-sm {
  height: 28px;
  padding: 0 var(--sp-3);
  font-size: 12px;
}

.btn-md {
  height: 36px;
  padding: 0 var(--sp-4);
  font-size: 14px;
}

.btn-primary {
  background: var(--accent);
  color: var(--ink-inverse);
  border-color: var(--accent);
}

.btn-primary:hover:not(:disabled) {
  background: var(--accent-2);
  border-color: var(--accent-2);
}

.btn-secondary {
  background: var(--surface-muted);
  color: var(--ink-secondary);
  border-color: var(--line);
}

.btn-secondary:hover:not(:disabled) {
  background: var(--line);
  border-color: var(--line-strong);
}

.btn-ghost {
  background: transparent;
  color: var(--ink-muted);
  border-color: transparent;
}

.btn-ghost:hover:not(:disabled) {
  background: var(--surface-muted);
  color: var(--ink-primary);
}

.btn-danger {
  background: var(--danger);
  color: var(--ink-inverse);
  border-color: var(--danger);
}

.btn-danger:hover:not(:disabled) {
  background: rgba(239, 68, 68, 0.8);
  border-color: rgba(239, 68, 68, 0.8);
}
</style>
