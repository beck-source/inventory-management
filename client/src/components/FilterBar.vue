<template>
  <div class="filters-bar">
    <div class="filters-container">
      <div class="filters-heading">
        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.75" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">
          <path d="M3 5h18l-7 8v6l-4 2v-8L3 5z" />
        </svg>
        <span>{{ t('filters.title') }}</span>
      </div>

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
        class="reset-filters-btn"
        @click="resetFilters"
        :disabled="!hasActiveFilters"
        :title="t('filters.reset')"
        :aria-label="t('filters.reset')"
      >
        <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 20 20" fill="currentColor">
          <path fill-rule="evenodd" d="M4 2a1 1 0 011 1v2.101a7.002 7.002 0 0111.601 2.566 1 1 0 11-1.885.666A5.002 5.002 0 005.999 7H9a1 1 0 010 2H4a1 1 0 01-1-1V3a1 1 0 011-1zm.008 9.057a1 1 0 011.276.61A5.002 5.002 0 0014.001 13H11a1 1 0 110-2h5a1 1 0 011 1v5a1 1 0 11-2 0v-2.101a7.002 7.002 0 01-11.601-2.566 1 1 0 01.61-1.276z" clip-rule="evenodd" />
        </svg>
        <span class="reset-label">{{ t('filters.reset') }}</span>
      </button>
    </div>
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
  position: sticky;
  top: var(--topbar-height);
  z-index: 90;
  background: var(--surface);
  border-bottom: 1px solid var(--border);
}

.filters-container {
  max-width: var(--content-max-width);
  margin: 0 auto;
  padding: var(--space-3) var(--space-8);
  display: flex;
  align-items: center;
  flex-wrap: wrap;
  gap: var(--space-3) var(--space-5);
}

.filters-heading {
  display: flex;
  align-items: center;
  gap: var(--space-2);
  padding-right: var(--space-5);
  border-right: 1px solid var(--border);
  color: var(--text-muted);
  font-size: 0.688rem;
  font-weight: 700;
  letter-spacing: 0.08em;
  text-transform: uppercase;
  white-space: nowrap;
}

.filters-heading svg {
  width: 15px;
  height: 15px;
}

.filters-grid {
  display: flex;
  align-items: center;
  flex-wrap: wrap;
  gap: var(--space-3) var(--space-5);
  flex: 1;
}

.filter-group {
  display: flex;
  align-items: center;
  gap: var(--space-2);
}

.filter-group label {
  font-size: 0.75rem;
  font-weight: 600;
  color: var(--text-muted);
  white-space: nowrap;
}

.filter-select {
  height: 34px;
  padding: 0 var(--space-3);
  border: 1px solid var(--border-strong);
  border-radius: var(--radius-sm);
  font-family: inherit;
  font-size: 0.813rem;
  color: var(--text-primary);
  background: var(--surface);
  cursor: pointer;
  transition: border-color var(--transition), box-shadow var(--transition);
  font-weight: 500;
  min-width: 150px;
}

.filter-select:hover {
  border-color: #94a3b8;
}

.filter-select:focus {
  outline: none;
  border-color: var(--accent);
  box-shadow: 0 0 0 3px rgba(37, 99, 235, 0.12);
}

.reset-filters-btn {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: var(--space-2);
  height: 34px;
  padding: 0 var(--space-3);
  background: var(--surface);
  border: 1px solid var(--border);
  border-radius: var(--radius-sm);
  color: var(--text-muted);
  font-family: inherit;
  font-size: 0.813rem;
  font-weight: 600;
  cursor: pointer;
  transition: background var(--transition), border-color var(--transition), color var(--transition);
  flex-shrink: 0;
}

.reset-filters-btn:hover:not(:disabled) {
  background: var(--surface-muted);
  border-color: var(--border-strong);
  color: var(--text-primary);
}

.reset-filters-btn:focus-visible {
  outline: 2px solid var(--accent);
  outline-offset: 2px;
}

.reset-filters-btn:disabled {
  opacity: 0.45;
  cursor: not-allowed;
}

.reset-filters-btn svg {
  width: 16px;
  height: 16px;
}

@media (max-width: 1280px) {
  .reset-label {
    display: none;
  }

  .reset-filters-btn {
    width: 34px;
    padding: 0;
  }
}

@media (max-width: 768px) {
  .filters-container {
    padding: var(--space-3) var(--space-4);
  }

  .filters-heading {
    display: none;
  }

  .filter-select {
    min-width: 0;
    flex: 1;
  }

  .filter-group {
    flex: 1 1 200px;
  }
}
</style>
