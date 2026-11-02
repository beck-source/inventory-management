<template>
  <div class="empty-state">
    <div v-if="$slots.icon" class="empty-icon">
      <slot name="icon" />
    </div>
    <div class="empty-title">
      <slot name="title" />
    </div>
    <div class="empty-description" v-if="$slots.description">
      <slot name="description" />
    </div>
    <div class="empty-action" v-if="$slots.action">
      <slot name="action" />
    </div>
  </div>
</template>

<script setup>
</script>

<style scoped>
.empty-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: var(--sp-9) var(--sp-6);
  text-align: center;
  gap: var(--sp-3);
  line-height: 1.5;
}

.empty-icon {
  color: var(--ink-muted);
  margin-bottom: var(--sp-1);
}

.empty-title {
  font-size: 14px;
  font-weight: 600;
  color: var(--ink-secondary);
}

.empty-description {
  font-size: 13px;
  color: var(--ink-muted);
  max-width: 100%;
}

.empty-action {
  margin-top: var(--sp-2);
}
</style>
