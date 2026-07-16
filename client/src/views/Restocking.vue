<script setup>
import { useI18n } from '../composables/useI18n'

const { t } = useI18n()
</script>

<template>
  <div class="view-container">
    <div class="page-header">
      <h2>{{ t('nav.restocking') }}</h2>
      <p>{{ t('restocking.description') }}</p>
    </div>

    <div class="card empty-state">
      <p>{{ t('restocking.comingSoon') }}</p>
    </div>
  </div>
</template>

<style scoped>
.view-container {
  padding: 0;
}

.empty-state {
  text-align: center;
  padding: 3rem 1.5rem;
  color: var(--color-text-muted);
}
</style>
