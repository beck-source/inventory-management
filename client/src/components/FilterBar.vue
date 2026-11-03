<template>
  <div class="filters-bar" role="group" :aria-label="t('filters.toolbarLabel')">
    <div class="filters-container">
      <div class="filters-grid">
        <div class="filter-group">
          <label for="filter-period">{{ t('filters.timePeriod') }}</label>
          <select id="filter-period" v-model="selectedPeriod" class="filter-select">
            <option value="all">{{ t('filters.allMonths') }}</option>
            <option value="2025-01">{{ t('months.january') }}</option>
            <option value="2025-02">{{ t('months.february') }}</option>
            <option value="2025-03">{{ t('months.march') }}</option>
            <option value="2025-04">{{ t('months.april') }}</option>
            <option value="2025-05">{{ t('months.may') }}</option>
            <option value="2025-06">{{ t('months.june') }}</option>
            <option value="2025-07">{{ t('months.july') }}</option>
            <option value="2025-08">{{ t('months.august') }}</option>
            <option value="2025-09">{{ t('months.september') }}</option>
            <option value="2025-10">{{ t('months.october') }}</option>
            <option value="2025-11">{{ t('months.november') }}</option>
            <option value="2025-12">{{ t('months.december') }}</option>
          </select>
        </div>

        <div class="filter-group">
          <label for="filter-location">{{ t('filters.location') }}</label>
          <select id="filter-location" v-model="selectedLocation" class="filter-select">
            <option value="all">{{ t('filters.all') }}</option>
            <option value="San Francisco">{{ t('warehouses.sanFrancisco') }}</option>
            <option value="London">{{ t('warehouses.london') }}</option>
            <option value="Tokyo">{{ t('warehouses.tokyo') }}</option>
          </select>
        </div>

        <div class="filter-group">
          <label for="filter-category">{{ t('filters.category') }}</label>
          <select id="filter-category" v-model="selectedCategory" class="filter-select">
            <option value="all">{{ t('filters.all') }}</option>
            <option value="circuit boards">{{ t('categories.circuitBoards') }}</option>
            <option value="sensors">{{ t('categories.sensors') }}</option>
            <option value="actuators">{{ t('categories.actuators') }}</option>
            <option value="controllers">{{ t('categories.controllers') }}</option>
            <option value="power supplies">{{ t('categories.powerSupplies') }}</option>
          </select>
        </div>

        <div class="filter-group">
          <label for="filter-status">{{ t('filters.orderStatus') }}</label>
          <select id="filter-status" v-model="selectedStatus" class="filter-select">
            <option value="all">{{ t('filters.all') }}</option>
            <option value="delivered">{{ t('status.delivered') }}</option>
            <option value="shipped">{{ t('status.shipped') }}</option>
            <option value="processing">{{ t('status.processing') }}</option>
            <option value="backordered">{{ t('status.backordered') }}</option>
          </select>
        </div>
      </div>

      <button
        type="button"
        class="reset-filters-btn"
        @click="resetFilters"
        :disabled="!hasActiveFilters"
        :title="t('filters.reset')"
        :aria-label="t('filters.reset')"
      >
        <AppIcon name="refresh" :size="16" />
      </button>
    </div>
  </div>
</template>

<script>
import { useFilters } from '../composables/useFilters'
import { useI18n } from '../composables/useI18n'
import AppIcon from './AppIcon.vue'

export default {
  name: 'FilterBar',
  components: { AppIcon },
  setup() {
    const {
      selectedPeriod,
      selectedLocation,
      selectedCategory,
      selectedStatus,
      hasActiveFilters,
      resetFilters
    } = useFilters()

    const { t } = useI18n()

    return {
      t,
      selectedPeriod,
      selectedLocation,
      selectedCategory,
      selectedStatus,
      hasActiveFilters,
      resetFilters
    }
  }
}
</script>

<style scoped>
/* Page toolbar between the top bar and the content. Not sticky: it scrolls away so
   it doesn't compete with the top bar for vertical space. */
.filters-bar {
  background: var(--color-bg);
  border-bottom: 1px solid var(--color-border);
  padding: var(--space-4) var(--content-padding);
}

.filters-container {
  max-width: var(--content-max-width);
  margin: 0 auto;
  display: flex;
  align-items: flex-end;
  gap: var(--space-3);
}

.filters-grid {
  display: flex;
  flex-wrap: wrap;
  align-items: flex-end;
  gap: var(--space-3) var(--space-4);
  flex: 1;
  min-width: 0;
}

.filter-group {
  display: flex;
  flex-direction: column;
  gap: var(--space-1);
  min-width: 0;
}

.filter-group label {
  font-size: var(--text-xs);
  font-weight: var(--weight-medium);
  color: var(--color-text-muted);
  white-space: nowrap;
}

.filter-select {
  height: 36px;
  min-width: 160px;
  padding: 0 var(--space-3);
  border: 1px solid var(--color-border-strong);
  border-radius: var(--radius-md);
  font: inherit;
  font-size: var(--text-sm);
  font-weight: var(--weight-medium);
  color: var(--color-text);
  background: var(--color-surface);
  cursor: pointer;
  transition: border-color var(--duration-fast) var(--ease), box-shadow var(--duration-fast) var(--ease);
}

.filter-select:hover {
  border-color: var(--color-text-subtle);
}

.filter-select:focus,
.filter-select:focus-visible {
  outline: none;
  border-color: var(--color-accent);
  box-shadow: var(--focus-ring);
  border-radius: var(--radius-md);
}

.reset-filters-btn {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 36px;
  height: 36px;
  padding: 0;
  background: var(--color-surface);
  border: 1px solid var(--color-border-strong);
  border-radius: var(--radius-md);
  color: var(--color-text-muted);
  cursor: pointer;
  transition: background var(--duration-fast) var(--ease), color var(--duration-fast) var(--ease);
  flex-shrink: 0;
}

.reset-filters-btn:focus-visible {
  border-radius: var(--radius-md);
}

.reset-filters-btn:hover:not(:disabled) {
  background: var(--color-surface-hover);
  color: var(--color-text);
}

.reset-filters-btn:disabled {
  opacity: 0.4;
  cursor: not-allowed;
}

@media (max-width: 1023px) {
  .filters-bar { padding: var(--space-3) var(--space-4); }
}

/* Phones: two selects per row, each stretching to fill its half. */
@media (max-width: 639px) {
  .filters-grid {
    display: grid;
    grid-template-columns: repeat(2, minmax(0, 1fr));
  }
  .filter-select { width: 100%; min-width: 0; }
}
</style>
