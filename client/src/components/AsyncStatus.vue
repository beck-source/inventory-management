<script setup>
import { useI18n } from '../composables/useI18n'

// Wraps a view's content with first-load / error / reload states.
// First load (not loaded yet): full-page loading or error + Retry.
// Later loads: content stays mounted, dimmed with an "Updating" label; errors show as a banner.
defineProps({
  loading: { type: Boolean, default: false },
  error: { default: null },
  loaded: { type: Boolean, default: false },
  loadingText: { type: String, default: '' },
})
defineEmits(['retry'])

const { t } = useI18n()
</script>

<template>
  <div v-if="!loaded && loading" class="loading">{{ loadingText || t('common.loading') }}</div>
  <div v-else-if="!loaded && error" class="error" role="alert">
    <p>{{ t('common.loadError') }}</p>
    <button type="button" class="retry-btn" @click="$emit('retry')">{{ t('common.retry') }}</button>
  </div>
  <div v-else>
    <div v-if="error" class="error-banner" role="alert">
      <span>{{ t('common.loadError') }}</span>
      <button type="button" class="retry-btn" @click="$emit('retry')">{{ t('common.retry') }}</button>
    </div>
    <div v-if="loading" class="updating" role="status">{{ t('common.updating') }}</div>
    <div :class="{ refreshing: loading }">
      <slot />
    </div>
  </div>
</template>

<style scoped>
.loading,
.error {
  padding: var(--space-8);
  text-align: center;
  color: var(--text-muted);
}

.error {
  color: var(--danger);
}

.error p {
  margin: 0 0 var(--space-3);
}

.error-banner {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: var(--space-3);
  margin-bottom: var(--space-4);
  padding: var(--space-3) var(--space-4);
  background: var(--danger-soft);
  border: 1px solid var(--danger-border);
  border-radius: var(--radius-md);
  color: var(--danger-ink);
  font-size: var(--text-base);
}

.retry-btn {
  padding: var(--space-1) var(--space-3);
  background: var(--surface);
  color: var(--text);
  border: 1px solid var(--border-strong);
  border-radius: var(--radius-md);
  font: inherit;
  font-size: var(--text-sm);
  cursor: pointer;
}

.retry-btn:hover {
  background: var(--surface-muted);
}

.updating {
  margin-bottom: var(--space-2);
  color: var(--text-muted);
  font-size: var(--text-xs);
  text-align: right;
}

/* Subtle reload indicator; pointer-events stay on so open details remain usable */
.refreshing {
  opacity: 0.6;
  transition: opacity 0.15s;
}
</style>
