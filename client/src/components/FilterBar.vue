<template>
  <div class="filters-bar">
    <div class="filters-grid">
      <div class="filter-group">
        <label>{{ t('filters.timePeriod') }}</label>
        <select v-model="selectedPeriod" class="filter-select">
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
        <label>{{ t('filters.location') }}</label>
        <select v-model="selectedLocation" class="filter-select">
          <option value="all">{{ t('filters.all') }}</option>
          <option value="San Francisco">{{ t('warehouses.sanFrancisco') }}</option>
          <option value="London">{{ t('warehouses.london') }}</option>
          <option value="Tokyo">{{ t('warehouses.tokyo') }}</option>
        </select>
      </div>

      <div class="filter-group">
        <label>{{ t('filters.category') }}</label>
        <select v-model="selectedCategory" class="filter-select">
          <option value="all">{{ t('filters.all') }}</option>
          <option value="circuit boards">{{ t('categories.circuitBoards') }}</option>
          <option value="sensors">{{ t('categories.sensors') }}</option>
          <option value="actuators">{{ t('categories.actuators') }}</option>
          <option value="controllers">{{ t('categories.controllers') }}</option>
          <option value="power supplies">{{ t('categories.powerSupplies') }}</option>
        </select>
      </div>

      <div class="filter-group">
        <label>{{ t('filters.orderStatus') }}</label>
        <select v-model="selectedStatus" class="filter-select">
          <option value="all">{{ t('filters.all') }}</option>
          <option value="delivered">{{ t('status.delivered') }}</option>
          <option value="shipped">{{ t('status.shipped') }}</option>
          <option value="processing">{{ t('status.processing') }}</option>
          <option value="backordered">{{ t('status.backordered') }}</option>
        </select>
      </div>
    </div>

    <button
      class="reset-filters-btn"
      @click="resetFilters"
      :disabled="!hasActiveFilters"
      :title="t('filters.reset') || 'Reset filters'"
    >
      <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 20 20" fill="currentColor">
        <path fill-rule="evenodd" d="M4 2a1 1 0 011 1v2.101a7.002 7.002 0 0111.601 2.566 1 1 0 11-1.885.666A5.002 5.002 0 005.999 7H9a1 1 0 010 2H4a1 1 0 01-1-1V3a1 1 0 011-1zm.008 9.057a1 1 0 011.276.61A5.002 5.002 0 0014.001 13H11a1 1 0 110-2h5a1 1 0 011 1v5a1 1 0 11-2 0v-2.101a7.002 7.002 0 01-11.601-2.566 1 1 0 01.61-1.276z" clip-rule="evenodd" />
      </svg>
      <span class="reset-label">Reset</span>
    </button>
  </div>
</template>

<script>
import { useFilters } from '../composables/useFilters'
import { useI18n } from '../composables/useI18n'

export default {
  name: 'FilterBar',
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
.filters-bar {
  background: var(--color-surface);
  border: 1px solid var(--color-border);
  border-radius: var(--radius-lg);
  padding: 0.875rem 1rem;
  margin-bottom: var(--space-6);
  display: flex;
  align-items: flex-end;
  gap: 0.875rem;
  box-shadow: var(--shadow-xs);
  flex-wrap: wrap;
}

.filters-grid {
  display: flex;
  align-items: flex-end;
  gap: 0.875rem;
  flex: 1;
  flex-wrap: wrap;
}

.filter-group {
  display: flex;
  flex-direction: column;
  gap: 0.375rem;
  min-width: 0;
}

.filter-group label {
  font-size: 0.6875rem;
  font-weight: 600;
  color: var(--color-text-muted);
  text-transform: uppercase;
  letter-spacing: 0.06em;
}

.filter-select {
  padding: 0.4375rem 2rem 0.4375rem 0.75rem;
  border: 1px solid var(--color-border);
  border-radius: var(--radius-md);
  font-size: 0.8125rem;
  color: var(--color-text-primary);
  background-color: var(--color-surface);
  background-image: url("data:image/svg+xml;charset=UTF-8,%3csvg xmlns='http://www.w3.org/2000/svg' width='10' height='10' viewBox='0 0 16 16' fill='none'%3e%3cpath d='M4 6L8 10L12 6' stroke='%2364748b' stroke-width='1.8' stroke-linecap='round' stroke-linejoin='round'/%3e%3c/svg%3e");
  background-repeat: no-repeat;
  background-position: right 0.6875rem center;
  background-size: 10px;
  cursor: pointer;
  transition: all 0.15s ease;
  font-weight: 500;
  min-width: 160px;
  appearance: none;
  -webkit-appearance: none;
}

.filter-select:hover {
  border-color: var(--color-border-strong);
}

.filter-select:focus {
  outline: none;
  border-color: var(--color-primary);
  box-shadow: var(--shadow-focus);
}

.reset-filters-btn {
  display: inline-flex;
  align-items: center;
  gap: 0.375rem;
  padding: 0.4375rem 0.75rem;
  background: var(--color-surface);
  border: 1px solid var(--color-border);
  border-radius: var(--radius-md);
  color: var(--color-text-secondary);
  cursor: pointer;
  transition: all 0.15s ease;
  font-family: inherit;
  font-size: 0.8125rem;
  font-weight: 600;
  flex-shrink: 0;
  height: 34px;
}

.reset-filters-btn:hover:not(:disabled) {
  background: var(--color-surface-alt);
  border-color: var(--color-border-strong);
  color: var(--color-text-primary);
}

.reset-filters-btn:disabled {
  opacity: 0.4;
  cursor: not-allowed;
}

.reset-filters-btn svg {
  width: 14px;
  height: 14px;
}

@media (max-width: 768px) {
  .filter-select {
    min-width: 140px;
    flex: 1;
  }

  .reset-label {
    display: none;
  }
}
</style>
