<template>
  <div class="sidebar-filters">
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

    <button
      class="reset-filters-btn"
      @click="resetFilters"
      :disabled="!hasActiveFilters"
      :title="t('filters.reset') || 'Reset all filters'"
    >
      <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 20 20" fill="currentColor">
        <path fill-rule="evenodd" d="M4 2a1 1 0 011 1v2.101a7.002 7.002 0 0111.601 2.566 1 1 0 11-1.885.666A5.002 5.002 0 005.999 7H9a1 1 0 010 2H4a1 1 0 01-1-1V3a1 1 0 011-1zm.008 9.057a1 1 0 011.276.61A5.002 5.002 0 0014.001 13H11a1 1 0 110-2h5a1 1 0 011 1v5a1 1 0 11-2 0v-2.101a7.002 7.002 0 01-11.601-2.566 1 1 0 01.61-1.276z" clip-rule="evenodd" />
      </svg>
      <span>Reset</span>
    </button>
  </div>
</template>

<script setup>
import { useFilters } from '../composables/useFilters'
import { useI18n } from '../composables/useI18n'

const {
  selectedPeriod,
  selectedLocation,
  selectedCategory,
  selectedStatus,
  hasActiveFilters,
  resetFilters
} = useFilters()

const { t } = useI18n()
</script>

<style scoped>
.sidebar-filters {
  display: flex;
  flex-direction: column;
  gap: 1rem;
}

.filter-group {
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
}

.filter-group label {
  color: var(--sidebar-text-muted);
  font-size: 0.75rem;
  text-transform: uppercase;
  letter-spacing: 0.05em;
  font-weight: 600;
}

.filter-select {
  background: rgba(255, 255, 255, 0.05);
  border: 1px solid var(--sidebar-border);
  color: var(--sidebar-text);
  border-radius: 6px;
  padding: 0.5rem 0.75rem;
  width: 100%;
  font-size: 0.813rem;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.2s;
  font-family: inherit;
}

.filter-select:hover {
  background: rgba(255, 255, 255, 0.08);
  border-color: rgba(255, 255, 255, 0.15);
}

.filter-select:focus {
  outline: none;
  border-color: var(--accent-primary);
  box-shadow: 0 0 0 3px rgba(59, 130, 246, 0.1);
}

.filter-select option {
  background: #1e293b;
  color: #e2e8f0;
}

.reset-filters-btn {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 0.5rem;
  padding: 0.5rem 0.75rem;
  background: rgba(255, 255, 255, 0.05);
  border: 1px solid var(--sidebar-border);
  border-radius: 6px;
  color: var(--sidebar-text);
  cursor: pointer;
  transition: all 0.2s;
  font-family: inherit;
  font-size: 0.813rem;
  font-weight: 500;
  margin-top: 0.5rem;
}

.reset-filters-btn:hover:not(:disabled) {
  background: rgba(255, 255, 255, 0.08);
  border-color: rgba(255, 255, 255, 0.15);
}

.reset-filters-btn:disabled {
  opacity: 0.3;
  cursor: not-allowed;
}

.reset-filters-btn svg {
  width: 16px;
  height: 16px;
  flex-shrink: 0;
}
</style>
