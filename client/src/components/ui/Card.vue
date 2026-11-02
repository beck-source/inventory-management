<template>
  <div class="card">
    <div v-if="title || $slots.title" class="card-title-row">
      <slot name="title">
        <h3 class="card-title">{{ title }}</h3>
      </slot>
    </div>
    <slot />
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
.card {
  background: var(--surface-card);
  border: 1px solid var(--line);
  border-radius: var(--r-md);
  padding: var(--sp-6);
}

.card-title-row {
  margin-bottom: var(--sp-4);
}

.card-title {
  font-size: 14px;
  font-weight: 600;
  color: var(--ink-muted);
  margin: 0;
  line-height: 1.5;
}
</style>
