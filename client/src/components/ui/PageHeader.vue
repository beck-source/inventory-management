<template>
  <div class="page-header">
    <div class="page-header-title">
      <slot name="title">
        <h1 class="page-title">{{ title }}</h1>
      </slot>
    </div>
    <div class="page-header-actions" v-if="$slots.actions">
      <slot name="actions" />
    </div>
  </div>
</template>

<script setup>
defineProps({
  title: {
    type: String,
    default: ''
  }
})
</script>

<style scoped>
.page-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 0 0 var(--sp-6);
  border-bottom: 1px solid var(--line);
  margin-bottom: var(--sp-6);
}

.page-title {
  font-size: 24px;
  font-weight: 600;
  color: var(--ink-primary);
  line-height: 1.25;
  margin: 0;
}

.page-header-actions {
  display: flex;
  align-items: center;
  gap: var(--sp-2);
}
</style>
